# 开发指南

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

## 🛠️ 开发环境配置

### 虚拟环境管理
```bash
# 创建新的 Python 3.11 虚拟环境
python3.11 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt
```

### 环境变量配置
```bash
# 复制环境变量模板
cp .env.example .env

# 必须配置的关键参数
MODELSCOPE_API_KEY=your-api-key-here
EMBEDDING_MODEL=moka-ai/m3e-base
EMBEDDING_DIMS=768
```

## 📦 技术栈要求

### 核心依赖
- **LangGraph**: 对话状态管理
- **Mem0**: 记忆管理系统
- **Qdrant**: 本地向量数据库
- **HuggingFace**: 本地嵌入模型支持
- **ModelScope**: LLM API 服务

### 模型配置
- **LLM**: ModelScope Qwen2.5-7B-Instruct
- **嵌入**: 本地 M3E-Base (768维)
- **向量存储**: 本地 Qdrant (Cosine 距离)

## 🧪 测试与验证

### 运行测试
```bash
# 完整功能测试
python test_agent.py

# 单次对话测试
python -c "from memory_agent import run_conversation; print(run_conversation('测试', 'test'))"
```

### 验证清单
- [ ] Python 3.11 虚拟环境激活
- [ ] 所有依赖安装成功
- [ ] Qdrant 服务正常运行
- [ ] 嵌入模型本地加载
- [ ] LLM API 调用成功
- [ ] 记忆功能正常工作
- [ ] 用户隔离有效

## 🔧 代码规范

### 配置管理
- 使用 `config.py` 统一管理所有配置
- 环境变量通过 `.env` 文件配置
- 不硬编码任何配置参数

### 错误处理
- **禁止**使用 try-except 进行降级处理
- **必须**在组件故障时直接报错
- **确保**所有依赖按预期工作

### 记忆系统
- 使用本地 M3E-Base 嵌入模型
- 通过 Qdrant 进行向量存储
- 实现严格的用户隔离

## 📝 开发流程

1. **环境准备**
   ```bash
   source venv/bin/activate
   ```

2. **代码修改**
   - 遵循既定的架构设计
   - 保持配置的统一管理
   - 确保无降级处理

3. **测试验证**
   ```bash
   python test_agent.py
   ```

4. **文档更新**
   - 更新 README.md
   - 更新相关注释

## ⚠️ 重要注意事项

- **本地优先**: 嵌入模型和向量存储必须本地部署
- **用户隔离**: 不同用户数据完全分离
- **无降级**: 任何组件故障都应直接报错
- **版本控制**: 严格使用 Python 3.11
- **配置统一**: 所有配置通过 config.py 管理

## 🐛 常见问题解决

### 虚拟环境问题
```bash
# 重建虚拟环境
rm -rf venv
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 模型下载问题
- 确保网络连接正常
- 检查磁盘空间充足
- 清理 HuggingFace 缓存：`rm -rf ~/.cache/huggingface`

### Qdrant 连接问题
```bash
# 重新设置 Qdrant
python setup_qdrant.py

# 检查服务状态
curl http://localhost:6333/collections
```