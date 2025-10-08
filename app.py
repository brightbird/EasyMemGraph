import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Tuple
import streamlit as st
from streamlit_chat import message

# Local imports
from memory_agent import conversation_graph, search_memories, store_interaction
from config import Config

# Additional imports for user management
try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Filter, FieldCondition, MatchAny, models
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    logger.warning("Qdrant client not available, user scanning functionality disabled")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configure Streamlit page
st.set_page_config(
    page_title="忆语 (YiYu) - 智能对话，记忆永存",
    page_icon="🧠💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for YiYu branding
st.markdown("""
<style>
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }

    .user-message {
        background: linear-gradient(135deg, #E3F2FD 0%, #BBDEFB 100%);
        align-items: flex-end;
        border-left: 4px solid #2196F3;
    }

    .assistant-message {
        background: linear-gradient(135deg, #F3E5F5 0%, #E1BEE7 100%);
        align-items: flex-start;
        border-left: 4px solid #9C27B0;
    }

    .memory-ref {
        background: linear-gradient(135deg, #FFF3E0 0%, #FFE0B2 100%);
        padding: 0.75rem;
        border-radius: 0.5rem;
        margin-top: 0.75rem;
        border-left: 4px solid #FF6F00;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .session-item {
        padding: 0.75rem;
        margin: 0.25rem 0;
        border-radius: 0.5rem;
        cursor: pointer;
        transition: all 0.3s ease;
        border: 1px solid #E0E0E0;
    }

    .session-item:hover {
        background: linear-gradient(135deg, #F5F5F5 0%, #EEEEEE 100%);
        border-color: #9C27B0;
        transform: translateY(-1px);
    }

    .active-session {
        background: linear-gradient(135deg, #E8F5E8 0%, #C8E6C9 100%);
        border-left: 4px solid #4CAF50;
        border-color: #4CAF50;
    }

    /* YiYu branding elements */
    .yiyu-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }

    .yiyu-button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 0.25rem;
        cursor: pointer;
        transition: all 0.3s ease;
    }

    .yiyu-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(102, 126, 234, 0.3);
    }
</style>
""", unsafe_allow_html=True)

def get_user_statistics(user_id: str) -> Dict[str, Any]:
    """
    Get detailed statistics for a specific user.
    Returns information like memory count, last activity, etc.
    """
    try:
        # Get memory statistics
        memories = search_memories("", user_id, limit=100)  # Get up to 100 memories
        memory_count = len(memories.get('results', [])) if memories else 0

        # Try to get more detailed information from Qdrant
        last_activity = None
        conversation_count = 0

        if QDRANT_AVAILABLE:
            try:
                qdrant_config = Config.get_qdrant_config()
                qdrant_url = qdrant_config["config"]["url"]
                collection_name = qdrant_config["config"]["collection_name"]
                api_key = qdrant_config["config"]["api_key"]

                if api_key:
                    client = QdrantClient(url=qdrant_url, api_key=api_key)
                else:
                    client = QdrantClient(url=qdrant_url)

                # Search for user-specific records with timestamp information
                from qdrant_client.models import Filter, FieldCondition

                # Try to find records for this user
                user_filter = Filter(
                    must=[
                        FieldCondition(
                            key="user_id",
                            match={"value": user_id}
                        )
                    ]
                )

                # Get some records to estimate activity
                try:
                    records, _ = client.scroll(
                        collection_name=collection_name,
                        scroll_filter=user_filter,
                        limit=50,
                        with_payload=True
                    )

                    if records:
                        conversation_count = len(records)
                        # Extract timestamp information if available
                        timestamps = []
                        for record in records:
                            if record.payload:
                                # Look for timestamp in various possible locations
                                timestamp = None
                                if 'timestamp' in record.payload:
                                    timestamp = record.payload['timestamp']
                                elif 'metadata' in record.payload and 'timestamp' in record.payload['metadata']:
                                    timestamp = record.payload['metadata']['timestamp']
                                elif 'created_at' in record.payload:
                                    timestamp = record.payload['created_at']

                                if timestamp:
                                    timestamps.append(timestamp)

                        if timestamps:
                            # Get the most recent timestamp
                            last_activity = max(timestamps)

                except Exception as e:
                    logger.debug(f"Could not get detailed stats for user {user_id}: {e}")

            except Exception as e:
                logger.debug(f"Qdrant not available for user stats: {e}")

        return {
            'user_id': user_id,
            'memory_count': memory_count,
            'conversation_count': conversation_count,
            'last_activity': last_activity,
            'has_data': memory_count > 0 or conversation_count > 0
        }

    except Exception as e:
        logger.error(f"Error getting user statistics for {user_id}: {e}")
        return {
            'user_id': user_id,
            'memory_count': 0,
            'conversation_count': 0,
            'last_activity': None,
            'has_data': False
        }

def scan_existing_users() -> set:
    """
    Scan Qdrant vector database to find existing user IDs.
    Returns a set of unique user IDs found in the database.
    """
    if not QDRANT_AVAILABLE:
        logger.warning("Qdrant client not available, cannot scan existing users")
        return set()

    try:
        # Get Qdrant configuration
        qdrant_config = Config.get_qdrant_config()
        qdrant_url = qdrant_config["config"]["url"]
        collection_name = qdrant_config["config"]["collection_name"]
        api_key = qdrant_config["config"]["api_key"]

        # Initialize Qdrant client
        if api_key:
            client = QdrantClient(url=qdrant_url, api_key=api_key)
        else:
            client = QdrantClient(url=qdrant_url)

        # Check if collection exists
        try:
            collections = client.get_collections().collections
            collection_exists = any(collection.name == collection_name for collection in collections)
            if not collection_exists:
                logger.info(f"Collection '{collection_name}' does not exist, no existing users")
                return set()
        except Exception as e:
            logger.warning(f"Could not verify collection existence: {e}")
            return set()

        # Scroll through all points to extract user IDs
        logger.info(f"Scanning existing users from collection '{collection_name}'")

        all_users = set()
        offset = None
        limit = 100  # Process in batches

        while True:
            try:
                # Scroll through records
                records, next_page_offset = client.scroll(
                    collection_name=collection_name,
                    offset=offset,
                    limit=limit,
                    with_payload=True
                )

                # Extract user IDs from payloads
                for record in records:
                    if record.payload:
                        # Look for user_id in different possible payload structures
                        user_id = None

                        # Check direct user_id field
                        if 'user_id' in record.payload:
                            user_id = record.payload['user_id']

                        # Check nested structure (Mem0 might store it this way)
                        elif 'metadata' in record.payload and 'user_id' in record.payload['metadata']:
                            user_id = record.payload['metadata']['user_id']

                        # Check if user_id is in the payload as a string
                        if user_id and isinstance(user_id, str) and user_id.strip():
                            all_users.add(user_id.strip())

                # Check if there are more records
                if next_page_offset is None:
                    break

                offset = next_page_offset

            except Exception as e:
                logger.error(f"Error scanning batch of users: {e}")
                break

        logger.info(f"Found {len(all_users)} existing users in database")
        return all_users

    except Exception as e:
        logger.error(f"Failed to scan existing users from Qdrant: {e}")
        return set()

def init_session_state():
    """Initialize Streamlit session state variables."""
    if 'sessions' not in st.session_state:
        st.session_state.sessions = {}
    if 'current_session_id' not in st.session_state:
        st.session_state.current_session_id = None
    if 'user_id' not in st.session_state:
        st.session_state.user_id = "web_user"
    if 'show_memory_details' not in st.session_state:
        st.session_state.show_memory_details = {}
    if 'first_visit' not in st.session_state:
        st.session_state.first_visit = True
    if 'api_status' not in st.session_state:
        st.session_state.api_status = "unknown"
    if 'last_api_check' not in st.session_state:
        st.session_state.last_api_check = 0
    if 'user_history' not in st.session_state:
        st.session_state.user_history = set()
        # Load existing users from database on first initialization
        if 'existing_users_loaded' not in st.session_state:
            existing_users = scan_existing_users()
            st.session_state.user_history.update(existing_users)
            st.session_state.existing_users_loaded = True
            logger.info(f"Loaded {len(existing_users)} existing users from database")

        # Initialize with current user
        if st.session_state.user_id and st.session_state.user_id != "web_user":
            st.session_state.user_history.add(st.session_state.user_id)
    if 'ai_thinking' not in st.session_state:
        st.session_state.ai_thinking = False
    if 'pending_response' not in st.session_state:
        st.session_state.pending_response = None
    if 'show_suggestions' not in st.session_state:
        st.session_state.show_suggestions = True
    if 'selected_suggestion' not in st.session_state:
        st.session_state.selected_suggestion = None
    if 'suggestion_source' not in st.session_state:
        st.session_state.suggestion_source = None

    # Auto-create default session if no sessions exist
    if not st.session_state.sessions:
        create_new_session("默认对话")
        st.session_state.first_visit = True

def create_new_session(session_name: str = None) -> str:
    """Create a new conversation session."""
    if session_name is None:
        session_name = f"会话 {datetime.now().strftime('%Y-%m-%d %H:%M')}"

    session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    st.session_state.sessions[session_id] = {
        'name': session_name,
        'messages': [],
        'created_at': datetime.now().isoformat(),
        'last_updated': datetime.now().isoformat()
    }

    st.session_state.current_session_id = session_id
    logger.info(f"Created new session: {session_id}")
    return session_id

def delete_session(session_id: str):
    """Delete a conversation session."""
    if session_id in st.session_state.sessions:
        del st.session_state.sessions[session_id]
        if st.session_state.current_session_id == session_id:
            st.session_state.current_session_id = None
        logger.info(f"Deleted session: {session_id}")

def switch_session(session_id: str):
    """Switch to a different conversation session."""
    if session_id in st.session_state.sessions:
        st.session_state.current_session_id = session_id
        st.session_state.sessions[session_id]['last_updated'] = datetime.now().isoformat()
        logger.info(f"Switched to session: {session_id}")

def add_message_to_session(session_id: str, role: str, content: str, memories: List[Dict] = None):
    """Add a message to the current session."""
    if session_id not in st.session_state.sessions:
        return

    message_data = {
        'role': role,
        'content': content,
        'timestamp': datetime.now().isoformat(),
        'memories': memories or []
    }

    st.session_state.sessions[session_id]['messages'].append(message_data)
    st.session_state.sessions[session_id]['last_updated'] = datetime.now().isoformat()

def get_conversation_response(user_input: str, user_id: str) -> Tuple[str, List[Dict]]:
    """Get response from the conversation agent with retry mechanism."""
    import time

    # Import here to avoid circular imports
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

    max_retries = 3
    retry_delay = 2  # seconds

    for attempt in range(max_retries):
        try:
            # Search for relevant memories
            memories = search_memories(user_input, user_id, limit=5)
            memory_list = memories.get('results', []) if memories else []

            # Extract memory context
            memory_context = ""
            if memory_list:
                memory_context = "Relevant information from previous conversations:\n"
                for i, mem in enumerate(memory_list, 1):
                    memory_context += f"{i}. {mem.get('memory', '')}\n"

            # Create system message with memory context
            system_content = """你是忆语 (YiYu)，一个具有记忆功能的智能对话伙伴。请根据提供的上下文信息，为用户提供个性化的回应。

            指导原则：
            1. 利用记忆中的信息提供连贯的对话体验
            2. 记住用户的偏好和过去的交互
            3. 保持友好和专业的语调
            4. 如果没有相关记忆，就基于当前问题进行回答
            5. 用中文回答

            """ + memory_context

            # Get response from conversation graph
            config = {"configurable": {"thread_id": user_id}}
            state = {
                "messages": [HumanMessage(content=user_input)],
                "mem0_user_id": user_id
            }

            response_content = ""
            for event in conversation_graph.stream(state, config):
                for value in event.values():
                    if value.get("messages"):
                        response_content = value["messages"][-1].content
                        break

            # Store the interaction in memory
            interaction = [
                {
                    "role": "user",
                    "content": user_input
                },
                {
                    "role": "assistant",
                    "content": response_content
                }
            ]

            store_interaction(interaction, user_id)

            # Update API status on success
            st.session_state.api_status = "normal"
            st.session_state.last_api_check = time.time()

            return response_content, memory_list

        except Exception as e:
            logger.error(f"Error getting conversation response (attempt {attempt + 1}/{max_retries}): {e}")
            error_str = str(e).lower()

            # For rate limiting, wait and retry
            if "429" in error_str or "rate limit" in error_str or "request limit exceeded" in error_str:
                st.session_state.api_status = "rate_limited"
                if attempt < max_retries - 1:
                    logger.info(f"Rate limit hit, waiting {retry_delay} seconds before retry...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                else:
                    return """🚫 **API调用频率限制**

很抱歉，当前API调用频率过高，已达到使用限制。请稍后再试。

**建议解决方案：**
1. 等待2-3分钟后重试
2. 检查您的ModelScope API配额
3. 如需更高配额，请联系ModelScope升级服务

我仍然记得我们之前的对话内容，稍后您可以继续我们的交流。""", []

            # For network errors, wait and retry
            elif "connection" in error_str or "network" in error_str or "timeout" in error_str:
                st.session_state.api_status = "error"
                if attempt < max_retries - 1:
                    logger.info(f"Network error, waiting {retry_delay} seconds before retry...")
                    time.sleep(retry_delay)
                    retry_delay *= 1.5
                    continue
                else:
                    return """🔌 **网络连接问题**

很抱歉，无法连接到AI服务。请检查网络连接后重试。

**建议检查：**
1. 网络连接是否正常
2. 防火墙设置是否阻止连接
3. API服务是否可用

您的消息已保存，网络恢复后我可以继续对话。""", []

            # For authentication errors, don't retry
            elif "authentication" in error_str or "unauthorized" in error_str or "api key" in error_str:
                st.session_state.api_status = "error"
                return """🔑 **API认证错误**

很抱歉，API密钥验证失败。请检查配置文件。

**请检查：**
1. MODELSCOPE_API_KEY是否正确配置
2. API密钥是否有效
3. 是否有足够的API访问权限

请联系管理员更新API配置。""", []

            # For other errors, don't retry
            else:
                st.session_state.api_status = "error"
                return f"""❌ **系统错误**

很抱歉，我遇到了一个技术问题：{str(e)[:100]}...

请稍后重试，或联系技术支持。您的消息已保存，我不会忘记我们的对话内容。""", []

    # This should not be reached, but just in case
    return "抱歉，遇到了意外错误。请重试。", []

def process_ai_response():
    """Process AI response asynchronously."""
    if st.session_state.ai_thinking and st.session_state.pending_response:
        try:
            # Get AI response
            user_input, user_id = st.session_state.pending_response

            with st.spinner("🤖 正在思考..."):
                response, memories = get_conversation_response(user_input, user_id)

            # Add assistant response to session
            add_message_to_session(
                st.session_state.current_session_id,
                'assistant',
                response,
                memories
            )

            # Clear pending state
            st.session_state.ai_thinking = False
            st.session_state.pending_response = None

            # Rerun to show the response
            st.rerun()

        except Exception as e:
            logger.error(f"Error processing AI response: {e}")
            # Handle error gracefully
            error_response = "抱歉，处理您的请求时遇到了问题。请稍后重试。"

            add_message_to_session(
                st.session_state.current_session_id,
                'assistant',
                error_response,
                []
            )

            st.session_state.ai_thinking = False
            st.session_state.pending_response = None
            st.rerun()

def render_sidebar():
    """Render the sidebar with session management."""
    st.sidebar.title("🎛️ 控制面板")

    # Quick stats
    st.sidebar.markdown("### 📊 当前状态")
    current_session = st.session_state.sessions.get(st.session_state.current_session_id, {})
    message_count = len(current_session.get('messages', []))

    st.sidebar.metric("当前会话消息", message_count)
    st.sidebar.metric("总会话数", len(st.session_state.sessions))

    # Quick new session button
    st.sidebar.markdown("---")
    if st.sidebar.button("🚀 快速新建会话", use_container_width=True, help="创建一个新的对话会话"):
        create_new_session()
        st.rerun()

    # API Status indicator
    st.sidebar.markdown("### 📡 服务状态")
    if 'api_status' not in st.session_state:
        st.session_state.api_status = "unknown"

    if st.session_state.api_status == "rate_limited":
        st.sidebar.error("🚫 API频率限制")
        st.sidebar.caption("请稍后重试")
    elif st.session_state.api_status == "error":
        st.sidebar.warning("⚠️ API服务异常")
        st.sidebar.caption("正在尝试恢复...")
    else:
        st.sidebar.success("✅ API服务正常")
        st.sidebar.caption("随时可用")

    # User ID input
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 👤 用户设置")

    # Prepare user options with better organization
    db_users = set()
    local_users = set()

    # Separate users into database users and locally created users
    if st.session_state.user_history:
        for user in st.session_state.user_history:
            if user != "web_user":
                # Check if user is from database (heuristic: check if it has memories)
                try:
                    memories = search_memories("test", user, limit=1)
                    if memories and memories.get('results'):
                        db_users.add(user)
                    else:
                        local_users.add(user)
                except:
                    local_users.add(user)

    # Create organized user options
    user_options = ["web_user"]

    # Add database users with special indicator
    if db_users:
        user_options.extend([f"🗄️ {user}" for user in sorted(db_users)])

    # Add local users
    if local_users:
        user_options.extend([f"👤 {user}" for user in sorted(local_users)])

    user_options.append("+ ➕ 新建用户ID")

    # Find current user index
    current_index = 0
    for i, option in enumerate(user_options):
        # Strip prefixes for comparison
        if option.replace("🗄️ ", "").replace("👤 ", "") == st.session_state.user_id:
            current_index = i
            break

    # User selection dropdown with better formatting
    selected_user = st.sidebar.selectbox(
        "🆔 选择用户ID",
        options=user_options,
        index=current_index,
        help="🗄️ = 数据库用户(有记忆), 👤 = 本地用户, 不同用户拥有独立的记忆空间"
    )

    # Handle user selection
    if selected_user == "+ ➕ 新建用户ID":
        st.sidebar.markdown("**✨ 创建新用户**")
        new_user_id = st.sidebar.text_input(
            "新用户ID",
            value="",
            placeholder="输入新的用户ID",
            key="new_user_id_input"
        )
        col1, col2 = st.sidebar.columns([2, 1])
        with col1:
            if st.sidebar.button("🚀 创建", key="create_new_user", use_container_width=True):
                if new_user_id.strip() and new_user_id.strip() not in st.session_state.user_history:
                    st.session_state.user_history.add(new_user_id.strip())
                    st.session_state.user_id = new_user_id.strip()
                    st.sidebar.success(f"✅ 用户 '{new_user_id.strip()}' 创建成功！")
                    st.rerun()
                elif new_user_id.strip():
                    st.sidebar.warning("⚠️ 该用户ID已存在")
        with col2:
            if st.sidebar.button("❌ 取消", key="cancel_new_user", use_container_width=True):
                st.rerun()
    else:
        # Strip prefixes to get actual user ID
        actual_user_id = selected_user.replace("🗄️ ", "").replace("👤 ", "")

        if actual_user_id != st.session_state.user_id:
            st.session_state.user_id = actual_user_id
            # Add to history if it's not a default user
            if actual_user_id != "web_user":
                st.session_state.user_history.add(actual_user_id)
                # Show user type indicator
                if selected_user.startswith("🗄️"):
                    st.sidebar.success(f"✅ 切换到数据库用户: {actual_user_id}")
                else:
                    st.sidebar.info(f"ℹ️ 切换到本地用户: {actual_user_id}")
            st.rerun()

    # User management section with enhanced information
    with st.sidebar.expander("👥 用户管理", expanded=False):
        st.sidebar.markdown("#### 📊 用户统计")

        # User statistics
        total_users = len(st.session_state.user_history)
        current_user = st.session_state.user_id

        st.sidebar.metric("🔢 总用户数", total_users)
        st.sidebar.metric("🆔 当前用户", current_user)

        st.sidebar.markdown("#### 📋 用户详情")

        if st.session_state.user_history:
            # Categorize users
            db_users_list = []
            local_users_list = []

            for user in sorted(list(st.session_state.user_history)):
                try:
                    memories = search_memories("test", user, limit=1)
                    if memories and memories.get('results'):
                        db_users_list.append(user)
                    else:
                        local_users_list.append(user)
                except:
                    local_users_list.append(user)

            # Display database users with statistics
            if db_users_list:
                st.sidebar.markdown("**🗄️ 数据库用户 (有记忆):**")
                for user in db_users_list:
                    # Get user statistics
                    stats = get_user_statistics(user)

                    with st.sidebar.container():
                        col1, col2, col3, col4 = st.sidebar.columns([2, 1, 1, 1])
                        with col1:
                            is_current = "🟢" if user == current_user else "⚪"
                            st.sidebar.write(f"{is_current} **{user}**")
                        with col2:
                            st.sidebar.write(f"📚 {stats['memory_count']}")
                        with col3:
                            if stats['last_activity']:
                                try:
                                    from datetime import datetime
                                    if isinstance(stats['last_activity'], str):
                                        last_dt = datetime.fromisoformat(stats['last_activity'].replace('Z', '+00:00'))
                                    else:
                                        last_dt = datetime.fromtimestamp(stats['last_activity'])
                                    st.sidebar.write(f"🕒 {last_dt.strftime('%m/%d')}")
                                except:
                                    st.sidebar.write("🕒 最近")
                            else:
                                st.sidebar.write("🕒 未知")
                        with col4:
                            if st.sidebar.button("🗑️", key=f"delete_user_{user}", help="删除用户"):
                                if user in st.session_state.user_history:
                                    st.session_state.user_history.remove(user)
                                    if user == current_user:
                                        st.session_state.user_id = "web_user"
                                    st.rerun()

            # Display local users
            if local_users_list:
                st.sidebar.markdown("**👤 本地用户 (无记忆):**")
                for user in local_users_list:
                    with st.sidebar.container():
                        col1, col2, col3 = st.sidebar.columns([3, 1, 1])
                        with col1:
                            is_current = "🟢" if user == current_user else "⚪"
                            st.sidebar.write(f"{is_current} {user}")
                        with col2:
                            st.sidebar.write("🔧")
                        with col3:
                            if st.sidebar.button("🗑️", key=f"delete_local_user_{user}", help="删除用户"):
                                if user in st.session_state.user_history:
                                    st.session_state.user_history.remove(user)
                                    if user == current_user:
                                        st.session_state.user_id = "web_user"
                                    st.rerun()
        else:
            st.sidebar.info("📝 暂无历史用户")

    # Advanced session management section
    with st.sidebar.expander("🛠️ 会话管理 (高级)", expanded=False):
        st.sidebar.info("💡 **提示**: 您可以创建多个会话来组织不同主题的对话")

        # New session creation
        with st.sidebar.expander("➕ 新建会话", expanded=False):
            session_name = st.sidebar.text_input(
                "会话名称",
                value="",
                key="new_session_name",
                placeholder="留空使用默认名称"
            )
            col1, col2 = st.sidebar.columns(2)
            with col1:
                if st.sidebar.button("创建会话", use_container_width=True, key="create_custom_session"):
                    create_new_session(session_name if session_name.strip() else None)
                    st.rerun()
            with col2:
                if st.sidebar.button("快速创建", use_container_width=True, key="create_default_session"):
                    create_new_session()
                    st.rerun()

        # Session list
        st.sidebar.markdown("#### 📚 会话列表")

        if st.session_state.sessions:
            for session_id, session_data in st.session_state.sessions.items():
                with st.sidebar.container():
                    col1, col2 = st.columns([4, 1])

                    with col1:
                        session_name = session_data['name']
                        last_updated = datetime.fromisoformat(session_data['last_updated'])
                        time_str = last_updated.strftime("%m/%d %H:%M")
                        msg_count = len(session_data.get('messages', []))

                        # Show active indicator and message count
                        indicator = "🟢" if session_id == st.session_state.current_session_id else "⚪"

                        if st.button(
                            f"{indicator} **{session_name}**\n*{time_str}* | {msg_count}条消息",
                            key=f"session_{session_id}",
                            use_container_width=True,
                            help=f"点击切换到此会话 ({msg_count}条消息)"
                        ):
                            switch_session(session_id)
                            st.rerun()

                    with col2:
                        if st.button("🗑️", key=f"delete_{session_id}", help="删除会话"):
                            delete_session(session_id)
                            st.rerun()

        else:
            st.sidebar.info("暂无会话")

    # Memory management info
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🧠 记忆功能")
    st.sidebar.success("""
    ✅ **跨会话记忆已启用**
    - 自动保存对话历史
    - 智能上下文检索
    - 用户数据隔离
    """)

    # Help section
    with st.sidebar.expander("❓ 使用帮助", expanded=False):
        st.sidebar.markdown("""
        **基本操作:**
        - 直接在输入框聊天
        - 点击建议按钮快速开始

        **高级功能:**
        - 创建多个独立会话
        - 自定义用户ID隔离记忆
        - 查看AI回复的记忆引用

        **记忆功能:**
        - AI会自动记住重要信息
        - 跨会话保持连续对话
        - 支持个性化回应
        """)

def render_memory_details(memories: List[Dict], message_key: str):
    """Render memory details in an expandable section."""
    if not memories:
        return

    # Toggle button for memory details
    if st.button("🧠 忆语引用", key=f"memory_toggle_{message_key}"):
        st.session_state.show_memory_details[message_key] = not st.session_state.show_memory_details.get(message_key, False)

    # Show expanded memory details
    if st.session_state.show_memory_details.get(message_key, False):
        with st.expander("🧠 忆语记忆详情", expanded=True):
            for i, memory in enumerate(memories, 1):
                memory_text = memory.get('memory', '')
                score = memory.get('score', 0)

                st.markdown(f"""
                <div class="memory-ref">
                    <strong>忆语记忆 {i} (相似度: {score:.3f}):</strong><br>
                    {memory_text}
                </div>
                """, unsafe_allow_html=True)

def render_chat_interface():
    """Render the main chat interface."""
    st.title("🧠💬 忆语 (YiYu) - 智能对话，记忆永存")

    # Ensure we have an active session (should always be true now)
    if not st.session_state.current_session_id:
        st.error("❌ 会话错误，请刷新页面重试")
        return

    current_session = st.session_state.sessions[st.session_state.current_session_id]

    # Display session name with edit option
    if 'editing_session_name' not in st.session_state:
        st.session_state.editing_session_name = False

    col1, col2 = st.columns([4, 1])

    if not st.session_state.editing_session_name:
        with col1:
            st.markdown(f"### 📝 {current_session['name']}")
        with col2:
            if st.button("✏️", key="rename_session", help="重命名会话"):
                st.session_state.editing_session_name = True
                st.session_state.temp_session_name = current_session['name']
                st.rerun()
    else:
        with col1:
            new_name = st.text_input(
                "新会话名称",
                value=st.session_state.get('temp_session_name', current_session['name']),
                key="session_rename_input",
                label_visibility="collapsed"
            )
        with col2:
            col_save, col_cancel = st.columns(2)
            with col_save:
                if st.button("✅", key="confirm_rename", help="保存名称"):
                    if new_name.strip():
                        current_session['name'] = new_name.strip()
                        st.session_state.editing_session_name = False
                        if 'temp_session_name' in st.session_state:
                            del st.session_state.temp_session_name
                        st.rerun()
            with col_cancel:
                if st.button("❌", key="cancel_rename", help="取消编辑"):
                    st.session_state.editing_session_name = False
                    if 'temp_session_name' in st.session_state:
                        del st.session_state.temp_session_name
                    st.rerun()

    # Show welcome message for first-time users or empty sessions
    if st.session_state.first_visit and not current_session['messages']:
        st.markdown("""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white; padding: 1.5rem; border-radius: 1rem; margin-bottom: 1rem;'>
            <h3>👋 欢迎使用忆语 (YiYu)！</h3>
            <p>我是您的智能对话伙伴，具有跨会话记忆功能。忆语可以：</p>
            <ul>
                <li>🧠 记住我们的对话历史</li>
                <li>🎯 提供个性化的回应</li>
                <li>📚 支持多个独立会话</li>
            </ul>
            <p><strong>现在就开始对话吧！</strong> 🚀</p>
        </div>
        """, unsafe_allow_html=True)
        st.session_state.first_visit = False

    # Chat messages container
    chat_container = st.container()

    with chat_container:
        # Display conversation history
        messages = current_session['messages']

        for i, msg in enumerate(messages):
            if msg['role'] == 'user':
                message(msg['content'], is_user=True, key=f"user_{i}")
            else:
                message(msg['content'], is_user=False, key=f"assistant_{i}")

                # Show memory details for assistant messages
                if msg.get('memories'):
                    render_memory_details(msg['memories'], f"msg_{i}")

        # Show AI thinking indicator
        if st.session_state.ai_thinking:
            st.markdown("""
            <div style='text-align: center; padding: 1rem; color: #666;'>
                <div class="thinking-indicator">
                    🤖 正在思考中...
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Process AI response if pending
    if st.session_state.ai_thinking and st.session_state.pending_response:
        process_ai_response()

    # User input at the bottom
    st.markdown("---")

    # Enhanced input form
    with st.form(key="user_input_form", clear_on_submit=True):
        col1, col2 = st.columns([5, 1])

        with col1:
            # Get quick suggestion if available
            default_value = ""
            input_key = "user_message"

            if 'quick_suggestion' in st.session_state:
                default_value = st.session_state.quick_suggestion
                # 使用时间戳确保每次引导语变化时都创建新的输入框
                if 'suggestion_timestamp' not in st.session_state:
                    st.session_state.suggestion_timestamp = 0
                input_key = f"user_message_{st.session_state.suggestion_timestamp}"

            user_input = st.text_input(
                "💬 和我聊聊吧:",
                value=default_value,
                placeholder="输入您想说的话，比如：你好，我想了解一下你的功能...",
                key=input_key,
                label_visibility="collapsed"
            )

        with col2:
            submit_button = st.form_submit_button("发送 🚀", use_container_width=True)

    # Quick suggestions for new users
    if st.session_state.show_suggestions:
        st.markdown("**💡 试试这些问题：**")

        # 个人信息类问题
        st.markdown("**👤 个人信息设置**")
        personal_col1, personal_col2, personal_col3 = st.columns(3)
        with personal_col1:
            if st.button("📝 我的姓名是", key="suggestion_name", use_container_width=True):
                import time
                st.session_state.quick_suggestion = "我的姓名是"
                st.session_state.suggestion_timestamp = int(time.time() * 1000)
                st.session_state.show_suggestions = False
                st.rerun()
        with personal_col2:
            if st.button("✈️ 我喜欢去...旅行", key="suggestion_travel", use_container_width=True):
                import time
                st.session_state.quick_suggestion = "我喜欢去...旅行"
                st.session_state.suggestion_timestamp = int(time.time() * 1000)
                st.session_state.show_suggestions = False
                st.rerun()
        with personal_col3:
            if st.button("🍽️ 我喜欢品尝", key="suggestion_food", use_container_width=True):
                import time
                st.session_state.quick_suggestion = "我喜欢品尝"
                st.session_state.suggestion_timestamp = int(time.time() * 1000)
                st.session_state.show_suggestions = False
                st.rerun()

        personal_col4, personal_col5, personal_col6 = st.columns(3)
        with personal_col4:
            if st.button("⚠️ 我对...过敏", key="suggestion_allergy", use_container_width=True):
                import time
                st.session_state.quick_suggestion = "我对...过敏"
                st.session_state.suggestion_timestamp = int(time.time() * 1000)
                st.session_state.show_suggestions = False
                st.rerun()
        with personal_col5:
            if st.button("💼 我正在从事", key="suggestion_work", use_container_width=True):
                import time
                st.session_state.quick_suggestion = "我正在从事"
                st.session_state.suggestion_timestamp = int(time.time() * 1000)
                st.session_state.show_suggestions = False
                st.rerun()
        with personal_col6:
            if st.button("🎯 更多信息", key="suggestion_more_info", use_container_width=True):
                import time
                st.session_state.quick_suggestion = "我想添加更多个人信息"
                st.session_state.suggestion_timestamp = int(time.time() * 1000)
                st.session_state.show_suggestions = False
                st.rerun()

        st.markdown("---")  # 分隔线

        # 系统功能类问题
        st.markdown("**🤖 系统功能了解**")
        system_col1, system_col2, system_col3 = st.columns(3)
        with system_col1:
            if st.button("👋 自我介绍", key="suggestion_intro", use_container_width=True):
                import time
                st.session_state.quick_suggestion = "你好，请介绍一下你自己"
                st.session_state.suggestion_timestamp = int(time.time() * 1000)
                st.session_state.show_suggestions = False
                st.rerun()
        with system_col2:
            if st.button("🧠 记忆功能", key="suggestion_memory", use_container_width=True):
                import time
                st.session_state.quick_suggestion = "你的记忆功能是怎么工作的？"
                st.session_state.suggestion_timestamp = int(time.time() * 1000)
                st.session_state.show_suggestions = False
                st.rerun()
        with system_col3:
            if st.button("🎯 功能特色", key="suggestion_features", use_container_width=True):
                import time
                st.session_state.quick_suggestion = "你有什么特别的功能吗？"
                st.session_state.suggestion_timestamp = int(time.time() * 1000)
                st.session_state.show_suggestions = False
                st.rerun()

    # Show selected suggestion preview
    if st.session_state.selected_suggestion and st.session_state.suggestion_source == "button":
        st.markdown("---")
        st.markdown("### 📝 选中的引导语")

        # Display the selected suggestion in a nice container
        st.markdown(f"""
        <div style='background-color: #E3F2FD; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #2196F3;'>
            <strong>💡 建议问题:</strong><br>
            {st.session_state.selected_suggestion}
        </div>
        """, unsafe_allow_html=True)

        # Action buttons
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("🚀 发送这个问题", key="send_suggestion", use_container_width=True):
                # Directly process the suggestion as user input
                suggestion_text = st.session_state.selected_suggestion

                # Check for rate limiting cooldown
                import time
                current_time = time.time()

                if (st.session_state.api_status == "rate_limited" and
                    current_time - st.session_state.get('last_api_check', 0) < 120):
                    st.warning("⏰ API频率限制中，请等待2分钟后再试")
                    st.stop()

                # Hide suggestions and clear selected suggestion
                st.session_state.show_suggestions = False
                st.session_state.selected_suggestion = None
                st.session_state.suggestion_source = None

                # Add user message to session immediately
                add_message_to_session(
                    st.session_state.current_session_id,
                    'user',
                    suggestion_text
                )

                # Set AI processing state
                st.session_state.ai_thinking = True
                st.session_state.pending_response = (suggestion_text, st.session_state.user_id)

                # Rerun to show user message immediately
                st.rerun()

        with col2:
            if st.button("✏️ 修改问题", key="edit_suggestion", use_container_width=True):
                st.session_state.quick_suggestion = st.session_state.selected_suggestion
                st.session_state.selected_suggestion = None
                st.session_state.suggestion_source = None
                st.rerun()
        with col3:
            if st.button("❌ 取消", key="cancel_suggestion", use_container_width=True):
                st.session_state.selected_suggestion = None
                st.session_state.suggestion_source = None
                st.rerun()

        st.markdown("---")

    # Clear quick suggestion after it's been used
    if 'quick_suggestion' in st.session_state and submit_button:
        del st.session_state.quick_suggestion

    # Handle user input
    if submit_button and user_input.strip():
        # Check for rate limiting cooldown
        import time
        current_time = time.time()

        if (st.session_state.api_status == "rate_limited" and
            current_time - st.session_state.get('last_api_check', 0) < 120):
            st.warning("⏰ API频率限制中，请等待2分钟后再试")
            st.stop()

        # Hide suggestions and clear selected suggestion after first message
        st.session_state.show_suggestions = False
        st.session_state.selected_suggestion = None
        st.session_state.suggestion_source = None

        # Add user message to session immediately
        add_message_to_session(
            st.session_state.current_session_id,
            'user',
            user_input.strip()
        )

        # Set AI processing state
        st.session_state.ai_thinking = True
        st.session_state.pending_response = (user_input.strip(), st.session_state.user_id)

        # Rerun to show user message immediately
        st.rerun()

def main():
    """Main application entry point."""
    init_session_state()

    # Render sidebar
    render_sidebar()

    # Render main chat interface
    render_chat_interface()

    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666; font-size: 0.8em;'>
            忆语 (YiYu) - 基于LangGraph和Mem0的智能对话记忆系统 |
            支持跨会话记忆 | 本地向量数据库
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()