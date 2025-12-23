# AMPRD Web UI

基于FastAPI和React的AMPRD Web用户界面。

## 🚀 快速开始

### 安装依赖

```bash
# 安装Python依赖（包括Web UI后端）
pip install -r requirements.txt
pip install fastapi uvicorn python-multipart

# 安装前端依赖（可选，如果有React构建）
cd webui/frontend
npm install
npm run build
```

### 启动后端服务

```bash
# 方式1：直接运行
cd webui
python app.py

# 方式2：使用uvicorn
uvicorn webui.app:app --host 0.0.0.0 --port 8000 --reload
```

### 访问Web界面

打开浏览器访问：http://localhost:8000

## 📋 功能特性

### 1. PRD生成
- ✅ 结构化Brief输入（JSON格式）
- ✅ 自然语言Brief输入（自动解析）
- ✅ 模板选择
- ✅ 实时进度显示
- ✅ 后台任务处理

### 2. 结果查看
- ✅ PRD列表浏览
- ✅ PRD内容预览
- ✅ 质量指标展示
- ✅ 多格式导出（JSON/DOCX/Markdown）

### 3. 系统监控
- ✅ 任务状态查询
- ✅ 系统健康检查
- ✅ 任务历史记录

## 🔌 API文档

启动服务后，访问以下地址查看API文档：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 📁 项目结构

```
webui/
├── app.py              # FastAPI后端主文件
├── static/             # 静态文件（如果使用纯HTML）
├── frontend/           # React前端（可选）
│   ├── src/
│   ├── public/
│   └── package.json
└── README.md
```

## 🔧 配置

确保已配置环境变量：
- `QWEN_API_KEY`: Qwen模型API密钥
- `QWEN_API_BASE`: API基础URL（可选）

## 📝 使用示例

### 1. 生成PRD（结构化Brief）

```bash
curl -X POST "http://localhost:8000/api/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "brief": {
      "title": "智能客服系统",
      "domain": "customer_service",
      "goal": "提升客户服务效率",
      "target_users": [{"persona": "客服人员"}]
    },
    "template_id": null
  }'
```

### 2. 生成PRD（自然语言）

```bash
curl -X POST "http://localhost:8000/api/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "brief_text": "我们要做一个智能客服系统，目标是提升客户服务效率..."
  }'
```

### 3. 查询任务状态

```bash
curl "http://localhost:8000/api/status/{task_id}"
```

### 4. 下载PRD

```bash
# JSON格式
curl "http://localhost:8000/api/download/{task_id}?format=json" -o prd.json

# DOCX格式
curl "http://localhost:8000/api/download/{task_id}?format=docx" -o prd.docx

# Markdown格式
curl "http://localhost:8000/api/download/{task_id}?format=markdown" -o prd.md
```

## 🎨 前端开发（可选）

如果要使用React前端：

```bash
cd webui/frontend
npm install
npm run dev  # 开发模式
npm run build  # 构建生产版本
```

前端构建产物会自动部署到 `webui/frontend/dist`，后端会自动服务该目录。

## 🐛 故障排除

1. **端口占用**：修改 `app.py` 中的端口号
2. **API密钥未配置**：检查 `.env` 文件
3. **依赖缺失**：运行 `pip install -r requirements.txt`

## 📄 许可证

与主项目相同（MIT License）

