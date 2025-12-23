# AMPRD Web UI 使用指南

## 🎯 概述

AMPRD Web UI 是一个精美的Web界面，用于快速生成和管理PRD文档。它提供了直观的用户界面，让用户无需命令行即可使用AMPRD系统。

## ✨ 功能特性

### 1. PRD生成
- ✅ **自然语言输入**：直接输入产品需求描述，系统自动解析
- ✅ **结构化Brief输入**：使用JSON格式的Brief文件
- ✅ **模板选择**：支持选择不同的PRD模板
- ✅ **实时进度显示**：实时查看生成进度和当前步骤
- ✅ **后台任务处理**：生成任务在后台异步执行

### 2. 结果管理
- ✅ **PRD列表浏览**：查看所有已生成的PRD
- ✅ **PRD内容预览**：快速预览PRD内容
- ✅ **多格式导出**：支持导出为JSON、DOCX、Markdown格式
- ✅ **质量指标展示**：查看PRD的质量评估指标

### 3. 任务监控
- ✅ **任务状态查询**：通过任务ID查询生成状态
- ✅ **系统健康检查**：查看系统运行状态
- ✅ **任务历史记录**：查看所有任务的执行历史

## 🚀 快速开始

### 方式1：使用启动脚本（推荐）

#### Windows
```bash
cd webui
start.bat
```

#### Linux/Mac
```bash
cd webui
chmod +x start.sh
./start.sh
```

### 方式2：手动启动

#### 1. 安装依赖
```bash
pip install fastapi uvicorn python-multipart
```

#### 2. 启动服务
```bash
cd webui
python app.py
```

或者使用uvicorn：
```bash
cd webui
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

#### 3. 访问Web界面
打开浏览器访问：http://localhost:8000

## 📖 使用教程

### 步骤1：生成PRD

#### 方法A：自然语言输入（推荐）

1. 在"生成PRD"标签页，选择"自然语言描述"
2. 在文本框中输入产品需求描述，例如：
   ```
   我们要做一个智能客服系统，目标是提升客户服务效率和用户体验。
   主要功能包括：
   - 自动回复常见问题
   - 智能路由客户咨询
   - 多语言支持
   ```
3. （可选）输入模板ID
4. 点击"开始生成PRD"按钮

#### 方法B：结构化Brief输入

1. 在"生成PRD"标签页，选择"结构化Brief JSON"
2. 在文本框中输入Brief JSON，例如：
   ```json
   {
     "title": "智能客服系统",
     "domain": "customer_service",
     "goal": "提升客户服务效率和用户体验",
     "target_users": [
       {"persona": "客服人员"},
       {"persona": "终端用户"}
     ],
     "key_constraints": [
       {"type": "技术约束", "description": "必须支持多语言"}
     ],
     "business_metrics": [
       {"name": "响应时间", "target": "< 2秒"}
     ]
   }
   ```
3. 点击"开始生成PRD"按钮

### 步骤2：查看生成进度

生成开始后，页面会自动显示：
- **进度条**：显示生成进度（0-100%）
- **状态消息**：显示当前执行步骤
- **任务ID**：用于后续查询

### 步骤3：下载结果

生成完成后，页面会显示：
- ✅ 成功消息
- 🔗 下载链接（JSON、DOCX、Markdown格式）

点击相应的下载链接即可下载PRD文件。

### 步骤4：查看PRD列表

1. 点击"PRD列表"标签页
2. 点击"刷新列表"按钮
3. 查看所有已生成的PRD
4. 点击"查看"按钮预览PRD内容
5. 点击"JSON"、"DOCX"按钮下载对应格式

### 步骤5：查询任务状态

1. 点击"任务状态"标签页
2. 输入任务ID
3. 点击"查询状态"按钮
4. 查看任务状态、进度、错误信息等

## 🔌 API文档

启动服务后，可以访问以下地址查看完整的API文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 主要API端点

#### 1. 生成PRD
```
POST /api/generate
Content-Type: application/json

{
  "brief_text": "产品需求描述...",
  "template_id": "模板ID（可选）"
}
```

#### 2. 查询任务状态
```
GET /api/status/{task_id}
```

#### 3. 下载PRD
```
GET /api/download/{task_id}?format=json|docx|markdown
```

#### 4. 列出所有PRD
```
GET /api/prds?limit=50&offset=0
```

#### 5. 获取PRD内容
```
GET /api/prd/{prd_id}
```

#### 6. 获取质量指标
```
GET /api/metrics/{task_id}
```

#### 7. 健康检查
```
GET /health
```

## 🎨 界面预览

### 主界面
- **渐变背景**：紫色渐变背景，美观大方
- **卡片式设计**：内容以卡片形式展示，清晰易读
- **响应式布局**：适配不同屏幕尺寸

### 标签页
- **生成PRD**：输入产品需求，开始生成
- **PRD列表**：浏览已生成的PRD
- **任务状态**：查询任务执行状态

### 功能特点
- **实时进度**：进度条实时更新
- **状态提示**：不同状态用不同颜色提示（成功/失败/进行中）
- **一键下载**：支持多种格式一键下载

## 🔧 配置说明

### 环境变量

确保已配置以下环境变量（在`.env`文件中）：

```bash
# Qwen API配置
QWEN_API_KEY=your-api-key-here
QWEN_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1  # 可选
```

### 端口配置

默认端口：8000

修改端口：编辑 `webui/app.py` 文件，修改：
```python
uvicorn.run(
    "app:app",
    host="0.0.0.0",
    port=8000,  # 修改这里
    reload=True,
    log_level="info"
)
```

## 🐛 故障排除

### 1. 端口被占用
**错误**: `Address already in use`

**解决**:
- 修改端口号
- 或关闭占用8000端口的程序

### 2. API密钥未配置
**错误**: `QWEN_API_KEY not found`

**解决**:
- 检查`.env`文件是否存在
- 确认`QWEN_API_KEY`已正确配置

### 3. 依赖缺失
**错误**: `ModuleNotFoundError: No module named 'fastapi'`

**解决**:
```bash
pip install fastapi uvicorn python-multipart
```

### 4. 生成失败
**错误**: 任务状态显示"failed"

**解决**:
- 查看错误信息
- 检查网络连接
- 确认API密钥有效
- 查看后端日志

## 📝 注意事项

1. **首次使用**：确保已安装所有依赖并配置API密钥
2. **生成时间**：PRD生成通常需要10-20分钟，请耐心等待
3. **任务持久化**：任务信息存储在内存中，重启服务会丢失
4. **文件存储**：生成的PRD文件保存在`artifacts/`目录下

## 🚀 进阶使用

### 使用API进行批量生成

```python
import requests

API_BASE = "http://localhost:8000"

# 批量生成PRD
briefs = [
    {"brief_text": "产品需求1..."},
    {"brief_text": "产品需求2..."},
    # ...
]

task_ids = []
for brief in briefs:
    response = requests.post(f"{API_BASE}/api/generate", json=brief)
    task_ids.append(response.json()["task_id"])

# 查询所有任务状态
for task_id in task_ids:
    response = requests.get(f"{API_BASE}/api/status/{task_id}")
    print(response.json())
```

### 集成到其他系统

Web UI提供了完整的REST API，可以轻松集成到其他系统中：

```python
from amprd_webui_client import AMPRDClient

client = AMPRDClient("http://localhost:8000")

# 生成PRD
task = client.generate_prd(brief_text="产品需求...")

# 等待完成
result = client.wait_for_completion(task.task_id)

# 下载PRD
prd_json = client.download_prd(task.task_id, format="json")
```

## 📚 相关文档

- [系统架构文档](../docs/system_guide.md)
- [API参考文档](http://localhost:8000/docs)
- [实验报告](../docs/week3_full_system_complete_analysis.md)

## 🎉 总结

AMPRD Web UI提供了一个简单易用的界面来使用AMPRD系统。无论您是产品经理、开发者还是研究人员，都可以通过Web界面快速生成高质量的PRD文档。

如有问题，请查看API文档或提交Issue。

