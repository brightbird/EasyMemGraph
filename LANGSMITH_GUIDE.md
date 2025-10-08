# LangSmith 集成指南

EasyMemGraph 已成功集成 LangSmith，提供强大的对话流程追踪和调试功能。

## 🚀 快速开始

### 1. 配置环境变量

在 `.env` 文件中添加以下配置：

```bash
# LangSmith Configuration
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_API_KEY=your-langsmith-api-key-here
LANGCHAIN_PROJECT=EasyMemGraph
```

### 2. 安装依赖

```bash
source venv/bin/activate
pip install langsmith
```

### 3. 创建 LangSmith 项目

使用增强版的项目设置工具：

```bash
# 快速创建 EasyMemGraph 项目（推荐）
python setup_langsmith_project.py --quick

# 或指定自定义项目名称
python setup_langsmith_project.py --quick --project MyCustomProject

# 交互式模式（手动选择项目）
python setup_langsmith_project.py

# 列出所有现有项目
python setup_langsmith_project.py --list
```

### 4. 验证配置

运行测试脚本验证 LangSmith 集成：

```bash
python test_agent.py
```

## 📊 追踪功能

### 自动追踪的组件

1. **对话流程** (`conversation_turn`)
   - 完整的用户交互过程
   - 输入/输出信息
   - 执行时间和状态

2. **记忆检索** (`memory_search`)
   - 搜索查询和参数
   - 检索到的记忆数量
   - 详细的记忆内容

3. **记忆存储** (`memory_storage`)
   - 存储的交互内容
   - 存储结果和数量

4. **LLM 调用** (`chatbot_response`)
   - 系统消息和上下文
   - AI 生成过程
   - 响应内容

### 自定义 Span

实现了详细的记忆检索追踪，包括：
- 搜索开始状态
- 记忆匹配结果
- 每个记忆的分数和内容

## 🛠️ 调试工具

### 使用命令行工具

项目提供了强大的调试工具 `langsmith_debug.py`：

```bash
# 查看最近的运行记录
python langsmith_debug.py list --limit 10

# 查看特定运行的详细信息
python langsmith_debug.py details --run-id <run-id>

# 分析性能统计
python langsmith_debug.py performance --hours 24

# 运行测试对话
python langsmith_debug.py test --input "你好" --user-id test_user

# 实时监控运行
python langsmith_debug.py monitor --duration 5
```

### 项目管理工具

使用统一的项目设置工具 `setup_langsmith_project.py`：

```bash
# 快速设置（推荐新手使用）
python setup_langsmith_project.py --quick

# 高级用法
python setup_langsmith_project.py --quick --project MyProject
python setup_langsmith_project.py --list
python setup_langsmith_project.py  # 交互式模式
```

### 调试工具功能

1. **运行记录列表** - 查看最近的执行历史
2. **详细信息查看** - 分析特定运行的输入输出
3. **性能分析** - 统计成功率和执行时间
4. **测试对话** - 运行测试并自动追踪
5. **实时监控** - 实时查看新的运行记录

## 📈 LangSmith 控制台

访问 [LangSmith 控制台](https://smith.langchain.com) 查看：

- 📊 可视化的执行流程图
- 📝 详细的运行日志
- ⚡ 性能指标和统计
- 🔍 错误诊断和调试信息
- 📋 运行历史记录

## 🔧 开发调试

### 查看追踪数据

在开发过程中，可以实时查看追踪数据：

```python
# 在代码中添加自定义追踪
from langsmith import traceable

@traceable(name="custom_function")
def my_function(input_data):
    # 你的代码
    return result
```

### 性能优化建议

1. **监控执行时间** - 使用性能分析功能识别瓶颈
2. **检查错误率** - 定期查看失败的运行记录
3. **优化记忆检索** - 分析记忆搜索的准确性和效率
4. **LLM 调用优化** - 监控 token 使用和响应时间

## 🚨 故障排除

### 常见问题

1. **追踪数据未上传**
   - 检查网络连接
   - 验证 API Key 配置
   - 确认项目名称正确

2. **连接失败**
   ```bash
   # 测试连接
   python -c "from langsmith import Client; print('连接成功')"
   ```

3. **性能问题**
   - 检查执行时间统计
   - 分析记忆检索效率
   - 优化 LLM 调用参数

### 调试步骤

1. 检查环境变量配置
2. 运行测试脚本验证功能
3. 使用调试工具查看运行状态
4. 在 LangSmith 控制台分析详细数据

## 📚 最佳实践

1. **始终启用追踪** - 在开发和生产环境中都启用追踪
2. **使用有意义的名称** - 为追踪函数使用描述性的名称
3. **定期分析性能** - 使用性能分析功能优化代码
4. **监控错误** - 及时发现和修复问题
5. **版本控制** - 跟踪不同版本的运行表现

通过 LangSmith 集成，你可以深入了解 EasyMemGraph 的运行机制，快速诊断问题，并持续优化用户体验。