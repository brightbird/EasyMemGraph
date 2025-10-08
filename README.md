# 忆语 (YiYu) - 智能对话记忆系统

> 忆语 - 让每句话都有记忆

基于 LangGraph、本地 Qdrant 向量数据库、Mem0、本地嵌入模型和 LangSmith 的智能对话记忆系统，具备跨会话记忆功能和完整的对话流程追踪。

## ✨ 特性

- 🧠 **跨会话记忆**: 使用 Mem0 管理用户对话历史和偏好
- 🔍 **本地嵌入**: 基于 M3E-Base 中文向量模型的语义搜索
- 🤖 **魔搭模型**: 集成魔搭社区 DeepSeek-V3.1 模型
- 📊 **本地存储**: 使用 Qdrant 本地向量数据库 (768维)
- 🔄 **状态管理**: 基于 LangGraph 的流式对话
- 👥 **智能用户管理**: 自动从数据库加载已有用户，支持用户分类和统计
- 🔐 **用户隔离**: 支持多用户独立记忆空间
- 📈 **对话追踪**: 集成 LangSmith 实现完整的对话流程追踪和调试
- 🌐 **Web界面**: 基于 Streamlit 的现代化Web交互界面
- 💬 **会话管理**: 支持多会话创建、保存、切换和删除
- 📋 **记忆引用**: 可展开查看对话中的记忆引用详情
- 🐛 **调试工具**: 提供强大的调试和性能分析工具
- 🚀 **无降级处理**: 严格按照要求实现，无备用方案

## 🏗️ 技术架构

### 核心对话架构
```
LangGraph (对话状态管理)
    ↓
Mem0 (记忆管理)
    ↓
HuggingFace M3E-Base (本地嵌入模型)
    ↓
Qdrant (本地向量数据库)
    ↓
ModelScope DeepSeek-V3.1 (LLM对话)
    ↓
LangSmith (对话流程追踪和调试)
```

### 用户管理架构
```
应用启动
    ↓
扫描 Qdrant 向量数据库
    ↓
提取已有用户ID列表
    ↓
分类用户 (数据库用户/本地用户)
    ↓
加载到 Streamlit Session State
    ↓
提供用户界面管理
    ↓
动态创建/删除用户
```

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <your-repo-url>
cd 忆语-YiYu  # 或 EasyMemGraph

# 创建 Python 3.11 虚拟环境
python3.11 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填入您的配置
# 必须配置 MODELSCOPE_API_KEY 和 LANGCHAIN_API_KEY
```

**关键配置项**:
```bash
# 必须配置的参数
MODELSCOPE_API_KEY=your-modelscope-api-key-here
LANGCHAIN_API_KEY=your-langsmith-api-key-here

# 其他推荐配置
EMBEDDING_MODEL=moka-ai/m3e-base  # 本地嵌入模型
EMBEDDING_DIMS=768               # 向量维度
LANGCHAIN_PROJECT=YiYu   # LangSmith 项目名称
```

### 3. 启动 Qdrant 服务

```bash
# 自动设置 Qdrant (推荐)
python setup_qdrant.py

# 或手动启动 Docker 容器
docker run -d --name qdrant-memory-agent \
  -p 6333:6333 -p 6334:6334 \
  -v $(pwd)/qdrant_storage:/qdrant/storage \
  qdrant/qdrant:latest
```

### 4. 创建 LangSmith 项目（可选）

```bash
# 自动创建 YiYu 项目
python create_project.py

# 或使用交互式设置工具
python setup_langsmith_project.py
```

### 5. 启动对话机器人

您可以选择使用命令行界面或Web界面：

#### 选项1: 命令行界面
```bash
python memory_agent.py
```

#### 选项2: Web界面 (推荐)
```bash
streamlit run app.py
```

忆语 Web界面将在浏览器中打开，默认地址为 `http://localhost:8501`

## 📁 项目结构

```
忆语 (YiYu)/
├── app.py                     # Streamlit Web应用主文件 (智能用户管理)
├── memory_agent.py            # 主对话代理 (带 LangSmith 追踪)
├── config.py                  # 统一配置管理
├── setup_qdrant.py            # Qdrant 向量数据库设置脚本
├── langsmith_debug.py         # LangSmith 调试和监控工具
├── setup_langsmith_project.py # LangSmith 项目设置工具
├── requirements.txt           # 依赖包列表 (含 streamlit)
├── .env.example              # 环境变量配置模板
├── README.md                 # 项目完整文档
├── CLAUDE.md                 # 开发环境指南
├── LANGSMITH_GUIDE.md        # LangSmith 详细使用指南
├── qdrant_storage/           # Qdrant 本地存储目录
└── venv/                     # Python 3.11 虚拟环境
```

## ⚙️ 配置说明

### 环境变量配置

| 变量名 | 说明 | 默认值 | 必填 |
|--------|------|--------|------|
| `MODELSCOPE_API_KEY` | 魔搭社区 API 密钥 | - | ✅ |
| `LANGCHAIN_API_KEY` | LangSmith API 密钥 | - | ✅ |
| `MODEL_NAME` | LLM 模型名称 | `deepseek-ai/DeepSeek-V3.1` | ❌ |
| `EMBEDDING_MODEL` | 本地嵌入模型 | `moka-ai/m3e-base` | ❌ |
| `EMBEDDING_DIMS` | 向量维度 | `768` | ❌ |
| `QDRANT_URL` | Qdrant 服务地址 | `http://localhost:6333` | ❌ |
| `QDRANT_COLLECTION_NAME` | 集合名称 | `conversation_memories` | ❌ |
| `LANGCHAIN_PROJECT` | LangSmith 项目名称 | `YiYu` | ❌ |
| `LANGCHAIN_TRACING_V2` | 启用 LangSmith 追踪 | `true` | ❌ |
| `LANGCHAIN_ENDPOINT` | LangSmith 服务地址 | `https://api.smith.langchain.com` | ❌ |

### 模型配置

**LLM 模型**: 魔搭社区 DeepSeek-V3.1
**嵌入模型**: 本地 M3E-Base 中文嵌入模型 (768维)
**向量数据库**: 本地 Qdrant (Cosine 距离)

## 🎯 使用示例

### Web界面使用 (推荐)

```bash
streamlit run app.py
```

Web界面功能特性：

1. **会话管理**: 左侧边栏可创建、切换、删除会话
2. **智能用户管理**: 自动加载和分类管理用户
3. **交互对话**: 主界面支持实时对话，消息按时间顺序显示
4. **记忆引用**: AI回复下方可点击"忆语引用"展开相关记忆详情
5. **响应式设计**: 适配不同屏幕尺寸，移动端友好

### 👥 智能用户管理功能

忆语支持强大的用户管理功能，自动识别和分类用户：

#### 🆔 用户类型
- **🗄️ 数据库用户**: 已有对话记忆的用户，从Qdrant向量数据库自动加载
- **👤 本地用户**: 新创建但暂无对话记忆的用户
- **🟢 当前用户**: 实时状态指示器显示当前活跃用户

#### 📊 用户统计信息
- **总用户数**: 显示系统中所有用户的总数
- **记忆数量**: 每个用户的对话记忆条数
- **最后活跃**: 用户最近的对话时间
- **用户分类**: 自动区分有数据/无数据用户

#### 🚀 用户操作
- **选择用户**: 从下拉菜单快速切换用户身份
- **创建用户**: 点击"+ ➕ 新建用户ID"创建新用户
- **删除用户**: 在用户管理面板中删除不需要的用户
- **自动保存**: 新用户自动添加到用户历史记录

**使用步骤**:
1. 启动Web应用后，系统自动扫描并加载所有已有用户
2. 在左侧"🆔 选择用户ID"下拉菜单中选择用户
3. 创建新用户：点击"+ ➕ 新建用户ID"，输入用户名并创建
4. 在"👥 用户管理"中查看详细的用户统计信息
5. 在底部输入框输入消息，点击发送或按Enter开始对话
6. 查看AI回复，点击"忆语引用"了解记忆详情
7. 可随时切换用户身份，每个用户拥有独立的记忆空间

### 命令行界面

```bash
python memory_agent.py
```

启动后，您可以：

1. 输入用户ID (可选，默认为 default_user)
2. 开始对话，系统会记住您的对话历史
3. 输入 `quit`、`exit` 或 `bye` 退出

### 程序化调用

```python
from memory_agent import run_conversation

# 单次对话
response = run_conversation("你好，我想了解一下你的功能", "user123")

# 多轮对话 (跨会话记忆)
response1 = run_conversation("我叫张三，喜欢编程和AI", "user123")
response2 = run_conversation("你还记得我的名字和爱好吗？", "user123")  # 会记住之前的对话
```

### 测试项目

```bash
# 运行完整测试套件 (含 LangSmith 验证)
python test_agent.py

# 测试内容包括：
# - 基本自我介绍和记忆存储
# - 跨会话记忆检索
# - 用户隔离验证
# - 偏好记忆功能
# - LangSmith 追踪数据验证
# - 调试工具功能测试
```

## 🔧 开发指南

### 核心设计原则

1. **无降级处理**: 所有组件必须按配置正常工作，无备用方案
2. **本地优先**: 嵌入模型和向量数据库优先使用本地部署
3. **用户隔离**: 不同用户的记忆数据完全分离
4. **状态一致性**: 使用 LangGraph 确保对话状态的一致性
5. **智能用户管理**: 自动发现和管理用户，无需手动配置
6. **混合存储**: 结合数据库持久化和内存缓存，提升性能

### 用户管理系统架构

忆语采用混合用户管理方案，结合数据库扫描和内存缓存：

```python
# 用户扫描流程
def scan_existing_users() -> set:
    """从Qdrant扫描已有用户"""
    - 连接到Qdrant向量数据库
    - 批量扫描所有记录
    - 提取user_id字段
    - 返回唯一用户集合

# 用户统计流程
def get_user_statistics(user_id: str) -> Dict:
    """获取用户详细统计"""
    - 查询用户记忆数量
    - 获取最后活跃时间
    - 统计对话次数
    - 返回用户画像信息
```

**用户分类策略**:
- **数据库用户**: 通过Qdrant扫描发现的有历史数据的用户
- **本地用户**: 会话期间创建但尚未有对话数据的新用户
- **默认用户**: `web_user` 作为访客模式的默认标识

**缓存机制**:
- 首次启动时全量扫描数据库
- 用户信息存储在Session State中
- 避免重复扫描，提升性能
- 支持运行时动态添加新用户

### 记忆系统架构

```python
# 记忆存储格式
interaction = [
    {
        "role": "user",
        "content": "用户输入内容"
    },
    {
        "role": "assistant",
        "content": "AI回应内容"
    }
]

# 记忆检索配置
memories = memory.search(
    query=user_message,
    user_id=user_id,
    limit=5  # 返回最相关的5条记忆
)
```

## 🛠️ 故障排除

### 常见问题

1. **虚拟环境问题**
   ```bash
   # 确保使用 Python 3.11
   python3.11 --version

   # 重新创建虚拟环境
   rm -rf venv
   python3.11 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Qdrant 连接失败**
   ```bash
   # 检查 Qdrant 是否运行
   curl http://localhost:6333/collections

   # 重新设置 Qdrant
   python setup_qdrant.py
   ```

3. **嵌入模型问题**
   - M3E-Base 模型首次使用时会自动下载 (约 400MB)
   - 确保有足够的磁盘空间和网络连接
   - 模型下载后保存在 HuggingFace 缓存目录

4. **LLM API 调用失败**
   - 检查 `MODELSCOPE_API_KEY` 是否正确配置
   - 确认网络可以访问魔搭 API
   - 查看模型配额和使用限制

5. **LangSmith 追踪问题**
   - 检查 `LANGCHAIN_API_KEY` 是否正确配置
   - 确认 LangSmith 项目是否存在 (`python create_project.py`)
   - 验证网络可以访问 LangSmith API
   - 查看 LangSmith 控制台确认数据接收

6. **嵌入模型维度错误**
   - 确保 `EMBEDDING_MODEL` 和 `EMBEDDING_DIMS` 配置匹配
   - M3E-Base 使用 768 维，M3E-Large 使用 1024 维
   - 删除错误的 Qdrant 集合重新开始

### 日志查看

程序运行时会输出详细日志：
- 🔄 记忆搜索结果统计
- 💾 记忆存储操作记录
- 🤖 LLM 调用状态
- 📊 LangSmith 追踪信息
- ❌ 错误信息和调试信息

## 📝 API 参考

### Config 配置类

```python
from config import Config

# 获取完整的 Mem0 配置
mem0_config = Config.get_mem0_config()

# 获取 LLM 配置 (魔搭 API)
llm_config = Config.get_model_config()

# 获取嵌入配置 (本地 M3E-Base)
embedding_config = Config.get_embedding_config()

# 获取 Qdrant 配置
qdrant_config = Config.get_qdrant_config()
```

### 对话代理

```python
from memory_agent import run_conversation

# 单次对话
response = run_conversation("你好", "user_id")

# 带记忆的多轮对话
response1 = run_conversation("我叫张三，是程序员", "user_id")
response2 = run_conversation("你还记得我的职业吗？", "user_id")
```

### 记忆管理

```python
from mem0 import Memory
from config import Config

# 初始化记忆系统
memory = Memory.from_config(Config.get_mem0_config())

# 搜索用户记忆
memories = memory.search("查询内容", user_id="user_id")

# 查看记忆结果
if memories and 'results' in memories:
    for mem in memories['results']:
        print(f"记忆: {mem['memory']}")
```

### LangSmith 调试工具

```bash
# 查看运行记录
python langsmith_debug.py list --limit 10

# 查看特定运行详情
python langsmith_debug.py details --run-id <run-id>

# 性能分析
python langsmith_debug.py performance --hours 24

# 测试对话并追踪
python langsmith_debug.py test --input "测试消息" --user-id test_user

# 实时监控运行
python langsmith_debug.py monitor --duration 5

# 创建或切换 LangSmith 项目
python create_project.py
```

## 🎯 性能特性

### 系统性能指标

- **嵌入模型**: M3E-Base (768维向量)
- **向量搜索**: Cosine 相似度，毫秒级响应
- **记忆存储**: 自动去重和更新
- **用户隔离**: 完全独立的记忆空间
- **并发支持**: 多用户同时对话
- **用户管理性能**: 启动时一次性扫描，运行时零延迟
- **用户统计**: 实时获取用户记忆数量和活跃状态
- **追踪性能**: LangSmith 实时追踪对话流程
- **调试效率**: 详细的性能分析和错误诊断

### 扩展性考虑

- 支持自定义嵌入模型
- 可配置的记忆搜索参数
- **智能用户管理**: 支持从多种数据源自动发现用户
- **用户统计扩展**: 可扩展的用户画像和行为分析
- 模块化的配置系统
- 可扩展的追踪功能
- 自定义调试工具集成

## 🔒 安全性

- API 密钥本地存储
- 用户数据隔离
- 本地向量数据库
- 无数据外传风险
- **用户隐私保护**: 用户ID和记忆数据完全隔离
- **内存缓存安全**: 用户信息仅在会话期间缓存
- **访问控制**: 用户间数据无法互相访问
- LangSmith 追踪数据加密传输
- 可配置的追踪隐私级别

## 🤝 贡献指南

### 开发要求

1. 使用 Python 3.11 虚拟环境
2. 遵循无降级处理原则
3. 保证测试用例通过 (含 LangSmith 验证)
4. 更新相关文档
5. 确保 LangSmith 追踪功能正常

### 提交流程

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 确保所有测试通过 (`python test_agent.py`)
4. 验证 LangSmith 功能 (`python langsmith_debug.py list`)
5. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
6. 推送到分支 (`git push origin feature/AmazingFeature`)
7. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [LangGraph](https://github.com/langchain-ai/langgraph) - 状态管理框架
- [Mem0](https://github.com/mem0ai/mem0) - 记忆管理系统
- [Qdrant](https://github.com/qdrant/qdrant) - 向量数据库
- [ModelScope](https://github.com/modelscope/modelscope) - 模型服务
- [LangSmith](https://smith.langchain.com) - 对话流程追踪和调试平台
- [M3E](https://huggingface.co/moka-ai/m3e-base) - 中文嵌入模型
- [HuggingFace](https://huggingface.co) - 模型托管和部署

## 🔗 相关链接

- [LangSmith 控制台](https://smith.langchain.com) - 查看对话追踪数据
- [LANGSMITH_GUIDE.md](./LANGSMITH_GUIDE.md) - 详细使用指南
- [魔搭社区](https://modelscope.cn) - LLM 模型服务