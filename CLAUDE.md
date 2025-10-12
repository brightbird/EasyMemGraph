# 忆语 (YiYu) 开发指南

## 🚨 核心开发原则

1. **始终在基于 Python 3.11 的虚拟环境下执行代码**
   ```bash
   # 激活虚拟环境
   source venv/bin/activate

   # 验证 Python 版本
   python --version  # 应显示 Python 3.11.x
   ```

2. **严禁使用任何降级处理方式，严格按要求的方案实现**
   - 不可使用 API 备用方案
   - 不可有错误处理的降级逻辑
   - 必须确保所有组件按配置正常工作

## 🏗️ 项目架构概览

### 系统架构图
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Streamlit     │    │   LangGraph      │    │    ModelScope   │
│   Web界面       │───▶│   对话状态管理   │───▶│   LLM API服务   │
│   (app.py)      │    │ (memory_agent.py)│    │ DeepSeek-V3.1   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌──────────────────┐              │
         └──────────────▶│      Mem0        │◀─────────────┘
                        │   记忆管理系统   │
                        └──────────────────┘
                                 │
                        ┌──────────────────┐
                        │     Qdrant       │
                        │   本地向量数据库  │
                        │  (M3E-Base 768维) │
                        └──────────────────┘
                                 │
                        ┌──────────────────┐
                        │    LangSmith     │
                        │   对话流程追踪   │
                        └──────────────────┘
```

### 核心模块结构
- **app.py**: Streamlit Web应用主文件，智能用户管理
- **memory_agent.py**: 主对话代理，集成LangSmith追踪
- **config.py**: 统一配置管理，环境变量处理
- **setup_qdrant.py**: Qdrant向量数据库初始化
- **langsmith_debug.py**: LangSmith调试和监控工具
- **setup_langsmith_project.py**: LangSmith项目设置

## 🛠️ 开发环境配置

### 虚拟环境管理
```bash
# 创建新的 Python 3.11 虚拟环境
python3.11 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# 升级pip
pip install --upgrade pip

# 安装项目依赖
pip install -r requirements.txt

# 验证安装
python -c "import langgraph, mem0, qdrant_client, streamlit; print('✅ 所有依赖安装成功')"
```

### 环境变量配置
```bash
# 复制环境变量模板
cp .env.example .env

# 必须配置的关键参数
MODELSCOPE_API_KEY=your-modelscope-api-key-here
LANGCHAIN_API_KEY=your-langsmith-api-key-here

# 推荐配置参数
EMBEDDING_MODEL=moka-ai/m3e-base
EMBEDDING_DIMS=768
MODEL_NAME=deepseek-ai/DeepSeek-V3.1
QDRANT_URL=http://localhost:6333
LANGCHAIN_PROJECT=YiYu
```

## 📦 技术栈详解

### 核心框架 (2025年最新版本)
- **LangGraph (>=0.2.0)**: 对话状态管理和流程控制
- **LangChain (>=0.3.0)**: LLM集成和工具链
- **Mem0 (>=0.1.8)**: 智能记忆管理系统
- **Qdrant-client (>=1.9.0)**: 高性能向量数据库客户端

### 模型和嵌入
- **ModelScope (>=1.17.0)**: 魔搭社区模型服务
- **Transformers (>=4.40.0)**: HuggingFace模型库
- **Torch (>=2.2.0)**: PyTorch深度学习框架
- **M3E-Base**: 中文嵌入模型 (768维向量)

### Web界面和工具
- **Streamlit (>=1.28.0)**: 现代化Web应用框架
- **Rich (>=13.7.0)**: 终端美化和日志输出
- **LangSmith (>=0.1.0)**: 对话流程追踪和调试

### 模型配置详情
- **LLM**: ModelScope DeepSeek-V3.1 (高性能对话模型)
- **嵌入**: 本地 M3E-Base (中文优化，768维)
- **向量存储**: 本地 Qdrant (Cosine 距离算法)
- **记忆管理**: Mem0智能记忆系统

## 🧪 测试与验证

### 完整测试流程
```bash
# 1. 基础环境测试
python -c "import langgraph, mem0, qdrant_client, streamlit; print('✅ 所有依赖安装成功')"

# 2. Qdrant 连接测试
python -c "from qdrant_client import QdrantClient; client = QdrantClient('http://localhost:6333'); print('✅ Qdrant连接成功')"

# 3. 嵌入模型测试
python -c "from sentence_transformers import SentenceTransformer; model = SentenceTransformer('moka-ai/m3e-base'); print('✅ M3E-Base模型加载成功')"

# 4. 完整功能测试 (推荐)
python test_agent.py

# 5. 单次对话测试
python -c "from memory_agent import run_conversation; print(run_conversation('你好，请介绍一下自己', 'test_user'))"

# 6. LangSmith 追踪测试
python langsmith_debug.py test --input "测试消息" --user-id test_user
```

### 验证清单
- [ ] Python 3.11 虚拟环境激活
- [ ] 所有依赖安装成功
- [ ] 环境变量配置正确 (MODELSCOPE_API_KEY, LANGCHAIN_API_KEY)
- [ ] Qdrant 服务正常运行 (http://localhost:6333)
- [ ] 嵌入模型本地加载成功 (M3E-Base)
- [ ] LLM API 调用成功 (ModelScope DeepSeek-V3.1)
- [ ] 记忆功能正常工作 (Mem0)
- [ ] 用户隔离有效
- [ ] LangSmith 追踪正常
- [ ] Web界面可以正常启动

## 🔧 代码规范

### 配置管理
- 使用 `config.py` 统一管理所有配置
- 环境变量通过 `.env` 文件配置
- 不硬编码任何配置参数
- 敏感信息 (API keys) 仅通过环境变量传递

### 错误处理
- **禁止**使用 try-except 进行降级处理
- **必须**在组件故障时直接报错
- **确保**所有依赖按预期工作
- 使用 Rich 库美化错误输出

### 代码风格
- 遵循 PEP 8 Python 代码规范
- 使用类型提示 (Type Hints)
- 函数和类必须包含文档字符串
- 变量命名使用 snake_case

### 记忆系统规范
- 使用本地 M3E-Base 嵌入模型
- 通过 Qdrant 进行向量存储
- 实现严格的用户隔离
- 记忆数据自动去重和更新

## 📝 开发工作流程

### 1. 环境准备
```bash
# 激活虚拟环境
source venv/bin/activate

# 验证环境
python --version  # 确保是 Python 3.11.x
pip list | grep -E "(langgraph|mem0|qdrant|streamlit)"  # 验证关键依赖
```

### 2. 开发前检查
```bash
# 检查 Qdrant 服务
curl http://localhost:6333/collections

# 检查环境变量
python -c "import os; print('MODELSCOPE_API_KEY:', 'SET' if os.getenv('MODELSCOPE_API_KEY') else 'NOT SET')"
```

### 3. 代码修改流程
- 遵循既定的架构设计
- 保持配置的统一管理
- 确保无降级处理
- 先运行测试再修改代码
- 修改后立即测试验证

### 4. 测试验证
```bash
# 基础功能测试
python test_agent.py

# LangSmith 追踪测试
python langsmith_debug.py list --limit 5
```

### 5. 文档更新
- 更新 README.md
- 更新相关注释
- 更新 CLAUDE.md 开发指南

## 🚀 开发调试指南

### 本地开发调试
```bash
# 启动 Web 界面调试
streamlit run app.py --server.port 8501 --logger.level debug

# 启动命令行调试
python memory_agent.py

# 查看 LangSmith 追踪数据
python langsmith_debug.py monitor --duration 10
```

### 性能分析
```bash
# 分析对话性能
python langsmith_debug.py performance --hours 24

# 查看用户统计
python -c "
from app import get_user_statistics
print('用户统计:', get_user_statistics())
"
```

### 内存和资源监控
```bash
# 监控内存使用
python -c "
import psutil
import os
process = psutil.Process(os.getpid())
print(f'内存使用: {process.memory_info().rss / 1024 / 1024:.2f} MB')
"

# 监控 GPU 使用 (如果有)
nvidia-smi  # Linux/Windows with NVIDIA GPU
```

## ⚠️ 重要注意事项

### 开发原则
- **本地优先**: 嵌入模型和向量存储必须本地部署
- **用户隔离**: 不同用户数据完全分离
- **无降级**: 任何组件故障都应直接报错
- **版本控制**: 严格使用 Python 3.11
- **配置统一**: 所有配置通过 config.py 管理

### 安全考虑
- API 密钥不能提交到版本控制
- 用户数据完全隔离存储
- 本地数据库确保数据隐私
- 定期备份 Qdrant 数据

### 性能优化
- 合理设置记忆搜索限制 (limit=5)
- 使用流式输出提升用户体验
- 缓存常用配置和模型
- 监控内存使用情况

## 🐛 故障排除指南

### 虚拟环境问题
```bash
# 完全重建虚拟环境
rm -rf venv
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 模型下载问题
```bash
# 检查网络连接和磁盘空间
df -h  # 查看磁盘空间
ping huggingface.co  # 测试网络连接

# 清理 HuggingFace 缓存
rm -rf ~/.cache/huggingface
rm -rf ~/.cache/modelscope

# 重新下载模型
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('moka-ai/m3e-base')"
```

### Qdrant 连接问题
```bash
# 检查服务状态
curl http://localhost:6333/collections
curl http://localhost:6333/health

# 重新设置 Qdrant
python setup_qdrant.py

# 手动启动 Docker (如果需要)
docker run -d --name qdrant-memory-agent \
  -p 6333:6333 -p 6334:6334 \
  -v $(pwd)/qdrant_storage:/qdrant/storage \
  qdrant/qdrant:latest
```

### API 调用问题
```bash
# 测试 ModelScope API
python -c "
import os
from modelscope import AutoModelForCausalLM, AutoTokenizer
print('ModelScope API Key:', 'SET' if os.getenv('MODELSCOPE_API_KEY') else 'NOT SET')
"

# 测试 LangSmith API
python -c "
import os
from langsmith import Client
print('LangSmith API Key:', 'SET' if os.getenv('LANGCHAIN_API_KEY') else 'NOT SET')
"
```

### 内存和性能问题
```bash
# 监控系统资源
htop  # Linux
top   # macOS/Linux
活动监视器  # macOS

# 清理 Python 缓存
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} +
```

## 🔧 高级配置

### 自定义嵌入模型
```python
# 在 config.py 中修改
EMBEDDING_MODEL = "your-custom-model"
EMBEDDING_DIMS = 1024  # 根据模型调整
```

### 调整记忆搜索参数
```python
# 在 memory_agent.py 中调整
memories = memory.search(
    query=user_message,
    user_id=user_id,
    limit=10,  # 增加搜索结果数量
    similarity_threshold=0.7  # 调整相似度阈值
)
```

### LangSmith 高级配置
```bash
# 设置采样率
LANGCHAIN_TRACING_SAMPLE_RATE=1.0

# 启用详细日志
LANGCHAIN_VERBOSE=true

# 设置项目标签
LANGCHAIN_TAGS="development,yiyu,memory-agent"
```

## 📊 监控和日志

### 应用监控
```bash
# 实时监控 LangSmith 追踪
python langsmith_debug.py monitor --duration 30

# 性能分析报告
python langsmith_debug.py performance --hours 24 --output report.json

# 错误日志分析
python langsmith_debug.py errors --hours 48
```

### 日志配置
```python
# 在代码中启用详细日志
import logging

# 设置日志级别
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 启用特定模块的调试日志
logging.getLogger("langgraph").setLevel(logging.DEBUG)
logging.getLogger("mem0").setLevel(logging.DEBUG)
```

### 系统资源监控
```bash
# CPU 和内存监控
python -c "
import psutil
import time
while True:
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    print(f'CPU: {cpu_percent}%, 内存: {memory.percent}%')
    time.sleep(5)
"

# 磁盘空间监控
df -h
du -sh qdrant_storage/
```

## 🚀 部署指南

### 本地部署
```bash
# 1. 环境准备
source venv/bin/activate
python setup_qdrant.py

# 2. 启动 Web 服务
streamlit run app.py --server.port 8501

# 3. 验证部署
curl http://localhost:8501
```

### Docker 部署
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8501 6333

# 启动脚本
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

```bash
# 构建和运行
docker build -t yiyu-memory-agent .
docker run -d --name yiyu \
  -p 8501:8501 -p 6333:6333 \
  -v $(pwd)/qdrant_storage:/app/qdrant_storage \
  --env-file .env \
  yiyu-memory-agent
```

### 生产环境配置
```bash
# 环境变量 (生产环境)
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
STREAMLIT_SERVER_ENABLE_CORS=false
STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=true

# 性能优化
PYTHONUNBUFFERED=1
TZ=Asia/Shanghai
```

## 🔄 数据备份和恢复

### Qdrant 数据备份
```bash
# 1. 停止 Qdrant 服务
docker stop qdrant-memory-agent

# 2. 备份数据目录
tar -czf qdrant_backup_$(date +%Y%m%d_%H%M%S).tar.gz qdrant_storage/

# 3. 恢复数据
tar -xzf qdrant_backup_YYYYMMDD_HHMMSS.tar.gz

# 4. 重启服务
docker start qdrant-memory-agent
```

### 配置文件备份
```bash
# 备份关键配置
cp .env .env.backup
cp config.py config.py.backup

# 批量备份脚本
#!/bin/bash
BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

cp .env $BACKUP_DIR/
cp config.py $BACKUP_DIR/
cp -r qdrant_storage $BACKUP_DIR/
tar -czf $BACKUP_DIR.tar.gz $BACKUP_DIR/
rm -rf $BACKUP_DIR/

echo "备份完成: $BACKUP_DIR.tar.gz"
```

## 📈 性能优化建议

### 模型优化
```python
# 优化嵌入模型配置
from sentence_transformers import SentenceTransformer

# 使用 GPU 加速 (如果可用)
model = SentenceTransformer('moka-ai/m3e-base', device='cuda')

# 批量处理提升效率
texts = ["文本1", "文本2", "文本3"]
embeddings = model.encode(texts, batch_size=32, show_progress_bar=True)
```

### 数据库优化
```python
# Qdrant 连接优化
from qdrant_client import QdrantClient

# 使用连接池
client = QdrantClient(
    url="localhost",
    port=6333,
    timeout=30,
    prefer_grpc=True  # 使用 gRPC 提升性能
)

# 批量操作优化
def batch_search(client, queries, batch_size=10):
    results = []
    for i in range(0, len(queries), batch_size):
        batch = queries[i:i+batch_size]
        batch_results = client.search_batch(batch)
        results.extend(batch_results)
    return results
```

### 缓存策略
```python
# 使用 functools.lru_cache 缓存结果
from functools import lru_cache
import time

@lru_cache(maxsize=100)
def cached_embedding(text: str):
    """缓存嵌入计算结果"""
    # 实际的嵌入计算逻辑
    return compute_embedding(text)

# 定期清理缓存
def clear_cache_periodically():
    while True:
        time.sleep(3600)  # 每小时清理一次
        cached_embedding.cache_clear()
```

## 🎯 最佳实践

### 开发最佳实践
1. **版本控制**
   - 使用语义化版本号 (v1.0.0)
   - 每个功能使用独立分支开发
   - 提交信息使用约定式提交格式

2. **测试驱动开发**
   ```bash
   # 先写测试
   python test_agent.py

   # 再修改代码
   # 再次运行测试验证
   ```

3. **代码质量**
   - 使用 `black` 格式化代码
   - 使用 `flake8` 检查代码风格
   - 使用 `mypy` 进行类型检查

### 运维最佳实践
1. **监控告警**
   ```bash
   # 设置健康检查
   curl -f http://localhost:8501/_stcore/health || exit 1

   # 监控关键指标
   python -c "
   from langsmith import Client
   client = Client()
   # 检查最近的错误率
   "
   ```

2. **日志管理**
   - 使用结构化日志格式
   - 设置日志轮转策略
   - 关键操作添加审计日志

3. **安全实践**
   - 定期更新依赖包
   - 使用 `.env.example` 作为配置模板
   - API 密钥使用环境变量管理

### 扩展开发指南
1. **添加新的 LLM 提供商**
   ```python
   # 在 config.py 中添加新的配置
   class NewLLMConfig:
       api_key: str = os.getenv("NEW_LLM_API_KEY")
       model_name: str = "new-model-name"
       base_url: str = "https://api.newllm.com"
   ```

2. **自定义记忆策略**
   ```python
   # 扩展 Mem0 配置
   custom_memory_config = {
       "vector_store": {
           "provider": "qdrant",
           "config": {
               "collection_name": "custom_memories",
               "embedding_model": "custom-model"
           }
       }
   }
   ```

## 📚 参考资料

### 官方文档
- [LangGraph 官方文档](https://langchain-ai.github.io/langgraph/)
- [Mem0 文档](https://docs.mem0.ai/)
- [Qdrant 文档](https://qdrant.tech/documentation/)
- [Streamlit 文档](https://docs.streamlit.io/)
- [LangSmith 文档](https://docs.smith.langchain.com/)

### 社区资源
- [ModelScope 魔搭社区](https://modelscope.cn/)
- [HuggingFace 模型库](https://huggingface.co/)
- [M3E 模型仓库](https://huggingface.co/moka-ai/m3e-base)

### 相关工具
- [Rich 库](https://rich.readthedocs.io/) - 终端美化
- [Pydantic](https://pydantic-docs.helpmanual.io/) - 数据验证
- [Python-dotenv](https://github.com/theskumar/python-dotenv) - 环境变量管理

---

**📅 最后更新**: 2025年10月12日
**🔧 维护者**: 忆语 (YiYu) 开发团队
**📦 版本**: v2.0 (增强开发指南)

这份开发指南涵盖了忆语项目的完整开发流程，包括环境配置、开发调试、测试验证、部署运维等各个方面。请根据实际需求定期更新和完善。