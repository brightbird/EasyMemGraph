import os
import logging
from typing import Annotated, List, Dict, Any, TypedDict, Union
from dotenv import load_dotenv

# LangGraph imports
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

# LangChain imports
from langchain_openai import ChatOpenAI

# LangSmith imports
from langsmith import traceable, Client
from langsmith import utils as langsmith_utils

# Mem0 imports
from mem0 import Memory

# Local imports
from config import Config

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set environment variables for LangChain/OpenAI compatibility
env_vars = Config.get_env_variables()
langsmith_config = Config.get_langsmith_config()
has_langsmith_key = bool(langsmith_config.get("LANGCHAIN_API_KEY"))

for key, value in env_vars.items():
    # Only set LangSmith environment variables if API key is provided
    if key.startswith("LANGCHAIN_") and not has_langsmith_key:
        # Disable LangSmith tracing completely
        if key == "LANGCHAIN_TRACING_V2":
            os.environ[key] = "false"
        continue
    if value:
        os.environ[key] = value

# Initialize LLM
try:
    llm = ChatOpenAI(
        model=os.getenv("MODEL_NAME", "deepseek-ai/DeepSeek-V3.1"),
        temperature=float(os.getenv("MODEL_TEMPERATURE", "0.2")),
        max_tokens=int(os.getenv("MODEL_MAX_TOKENS", "2000"))
    )
    logger.info("LLM initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize LLM: {e}")
    raise

# Initialize Memory with Qdrant
try:
    mem0_config = Config.get_mem0_config()
    memory = Memory.from_config(mem0_config)
    logger.info("Memory system initialized with Qdrant")
except Exception as e:
    logger.error(f"Failed to initialize Memory: {e}")
    raise

# Initialize LangSmith Client (only if API key is provided)
langsmith_client = None
langsmith_enabled = False
langsmith_config = Config.get_langsmith_config()
if langsmith_config.get("LANGCHAIN_API_KEY"):
    try:
        langsmith_client = Client(
            api_url=langsmith_config["LANGCHAIN_ENDPOINT"],
            api_key=langsmith_config["LANGCHAIN_API_KEY"]
        )
        langsmith_enabled = True
        logger.info("LangSmith client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize LangSmith client: {e}")
        langsmith_client = None
else:
    logger.info("LangSmith API key not provided, running without tracing")

# Conditional traceable decorator
def conditional_traceable(name=None):
    """Apply traceable decorator only if LangSmith is enabled"""
    def decorator(func):
        if langsmith_enabled:
            return traceable(name=name or func.__name__)(func)
        else:
            return func
    return decorator

# Define conversation state
class State(TypedDict):
    """Conversation state for LangGraph."""
    messages: Annotated[List[Union[HumanMessage, AIMessage]], add_messages]
    mem0_user_id: str

@conditional_traceable(name="memory_search")
def search_memories(query: str, user_id: str, limit: int = 5) -> Dict[str, Any]:
    """
    Search for relevant memories with LangSmith tracing.

    Args:
        query: Search query
        user_id: User identifier
        limit: Maximum number of memories to return

    Returns:
        Dictionary containing search results
    """
    logger.info(f"Searching memories for user {user_id} with query: {query[:50]}...")

    # Perform memory search
    memories = memory.search(
        query,
        user_id=user_id,
        limit=limit
    )

    # Process results for tracking
    memory_count = len(memories.get('results', [])) if memories and 'results' in memories else 0
    memory_texts = []

    if memories and 'results' in memories:
        for i, mem in enumerate(memories['results']):
            memory_texts.append({
                "index": i + 1,
                "memory": mem.get('memory', ''),
                "score": mem.get('score', 0)
            })

    logger.info(f"Found {memory_count} relevant memories")

    return memories

@conditional_traceable(name="memory_storage")
def store_interaction(interaction: List[Dict[str, str]], user_id: str) -> Dict[str, Any]:
    """
    Store interaction in memory with smart logic to reduce API calls.

    Args:
        interaction: List of message dictionaries
        user_id: User identifier

    Returns:
        Dictionary containing storage results
    """
    logger.info(f"Storing interaction for user {user_id}")

    # Smart memory storage logic to reduce API calls
    try:
        # Check if this interaction is worth storing
        user_message = interaction[0]["content"] if interaction else ""
        assistant_message = interaction[1]["content"] if len(interaction) > 1 else ""

        # Skip storing for very short or simple interactions
        if len(user_message.strip()) < 5 or len(assistant_message.strip()) < 10:
            logger.info("Skipping memory storage for very short interaction")
            return {"results": [], "message": "Skipped: interaction too short"}

        # Skip storing for simple greetings that don't contain meaningful information
        simple_greetings = ["你好", "hello", "hi", "嗨", "在吗", "在不在", "哈喽", "早上好", "晚上好", "嘿", "嗨嗨"]
        if user_message.strip().lower() in simple_greetings and len(assistant_message.strip()) < 30:
            logger.info("Skipping memory storage for simple greeting")
            return {"results": [], "message": "Skipped: simple greeting"}

        # But DO store interactions with important personal information
        important_keywords = ["我叫", "我是", "我的名字", "我来自", "我喜欢", "我不喜欢", "我的职业", "我工作", "我学习", "我住"]
        if any(keyword in user_message for keyword in important_keywords):
            logger.info("Force storing memory due to important personal information")
            # Proceed with memory storage without length checks
        elif len(user_message.strip()) < 8 and len(assistant_message.strip()) < 25:
            logger.info("Skipping memory storage for short interaction without important info")
            return {"results": [], "message": "Skipped: short and unimportant"}

        # Proceed with memory storage
        memory_result = memory.add(interaction, user_id=user_id)
        memories_added = len(memory_result.get('results', []))
        logger.info(f"Successfully stored {memories_added} memories")

        return memory_result

    except Exception as e:
        logger.error(f"Error in memory storage: {e}")
        # Return empty result instead of crashing
        return {"results": [], "error": str(e)}

@conditional_traceable(name="chatbot_response")
def chatbot(state: State) -> Dict[str, Any]:
    """
    Main chatbot function that processes user input with memory context.

    Args:
        state: Current conversation state with messages and user_id

    Returns:
        Dictionary with AI response message
    """
    messages = state["messages"]
    user_id = state["mem0_user_id"]

    logger.info(f"Processing message for user: {user_id}")

    # Get the latest user message
    latest_message = messages[-1]

    # Search for relevant memories with tracing
    memories = search_memories(latest_message.content, user_id, limit=5)

    # Extract memory context
    memory_context = ""
    if memories and 'results' in memories:
        memory_list = memories['results']
        if memory_list:
            memory_context = "Relevant information from previous conversations:\n"
            for i, mem in enumerate(memory_list, 1):
                memory_context += f"{i}. {mem.get('memory', '')}\n"
            logger.info(f"Found {len(memory_list)} relevant memories")

    # Create system message with memory context
    system_content = """你是忆语 (YiYu)，一个具有记忆功能的智能对话伙伴。请根据提供的上下文信息，为用户提供个性化的回应。

    指导原则：
    1. 利用记忆中的信息提供连贯的对话体验
    2. 记住用户的偏好和过去的交互
    3. 保持友好和专业的语调
    4. 如果没有相关记忆，就基于当前问题进行回答
    5. 用中文回答

    """ + memory_context

    system_message = SystemMessage(content=system_content)

    # Prepare full message sequence
    full_messages = [system_message] + messages

    logger.info("Generating AI response")
    response = llm.invoke(full_messages)

    # Store the interaction in memory with tracing
    interaction = [
        {
            "role": "user",
            "content": latest_message.content
        },
        {
            "role": "assistant",
            "content": response.content
        }
    ]

    memory_result = store_interaction(interaction, user_id)

    return {"messages": [response]}

# Build the conversation graph
graph = StateGraph(State)
graph.add_node("chatbot", chatbot)
graph.add_edge(START, "chatbot")
# Removed self-loop to prevent infinite requests
# The graph should end after chatbot response and wait for next user input

# Compile the graph
conversation_graph = graph.compile()
logger.info("Conversation graph compiled successfully")

@conditional_traceable(name="conversation_turn")
def run_conversation(user_input: str, user_id: str = "default_user") -> str:
    """
    Run a conversation turn with the memory agent.

    Args:
        user_input: User's message
        user_id: Unique identifier for the user

    Returns:
        AI response string
    """
    config = {"configurable": {"thread_id": user_id}}
    state = {
        "messages": [HumanMessage(content=user_input)],
        "mem0_user_id": user_id
    }

    logger.info(f"Starting conversation for user {user_id}")

    # Stream the response
    for event in conversation_graph.stream(state, config):
        for value in event.values():
            if value.get("messages"):
                response = value["messages"][-1].content
                print(f"AI助手: {response}")
                return response

def interactive_chat():
    """
    Interactive chat interface for command line usage.
    """
    print("🧠💬 忆语 (YiYu) - 智能对话记忆系统已启动！(输入 'quit', 'exit' 或 'bye' 退出)")
    print("=" * 50)

    # Get user ID (could be enhanced with actual user management)
    user_id = input("请输入您的用户ID (直接回车使用默认): ").strip()
    if not user_id:
        user_id = "default_user"

    print(f"你好！用户ID: {user_id}")
    print("=" * 50)

    while True:
        try:
            user_input = input("\n你: ").strip()

            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("\nAI助手: 谢谢使用！再见！👋")
                break

            if not user_input:
                continue

            run_conversation(user_input, user_id)

        except KeyboardInterrupt:
            print("\n\nAI助手: 再见！👋")
            break
        except Exception as e:
            logger.error(f"Error in interactive chat: {e}")
            print("AI助手: 抱歉，出现了错误。请重试。")

if __name__ == "__main__":
    interactive_chat()