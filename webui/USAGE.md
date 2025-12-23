# AMPRD Web UI 使用指南

## ✅ 服务已启动

服务运行在：**http://localhost:8000**

## 🚀 快速使用

### 1. 访问Web界面

打开浏览器，访问：http://localhost:8000

### 2. 生成PRD

#### 方式A：自然语言输入（最简单）

1. 点击"生成PRD"标签页
2. 选择"自然语言描述"
3. 在文本框中输入产品需求，例如：
   ```
   我们要做一个智能客服系统，目标是提升客户服务效率和用户体验。
   主要功能包括：
   - 自动回复常见问题
   - 智能路由客户咨询
   - 多语言支持
   - 客服工作台
   ```
4. （可选）输入模板ID（如 `figma`、`jira` 等）
5. 点击"开始生成PRD"按钮

#### 方式B：结构化Brief JSON

1. 点击"生成PRD"标签页
2. 选择"结构化Brief JSON"
3. 在文本框中输入JSON格式的Brief，例如：
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
       {"name": "响应时间", "target": "< 2秒"},
       {"name": "满意度", "target": "> 90%"}
     ]
   }
   ```
4. 点击"开始生成PRD"按钮

### 3. 查看生成进度

生成开始后，页面会自动显示：
- **进度条**：实时显示生成进度（0-100%）
- **状态消息**：显示当前执行步骤
- **任务ID**：用于后续查询

生成过程通常需要 **10-20分钟**，请耐心等待。

### 4. 下载结果

生成完成后，页面会显示：
- ✅ 成功消息
- 🔗 下载链接（JSON、DOCX、Markdown格式）

点击相应的下载链接即可下载PRD文件。

### 5. 查看PRD列表

1. 点击"PRD列表"标签页
2. 点击"刷新列表"按钮
3. 查看所有已生成的PRD
4. 点击"查看"按钮预览PRD内容
5. 点击"JSON"、"DOCX"按钮下载对应格式

### 6. 查询任务状态

1. 点击"任务状态"标签页
2. 输入任务ID（从生成页面获取）
3. 点击"查询状态"按钮
4. 查看任务状态、进度、错误信息等

## 🔌 API接口

### 查看API文档

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 主要API端点

#### 1. 生成PRD
```bash
POST /api/generate
Content-Type: application/json

{
  "brief_text": "产品需求描述...",
  "template_id": "模板ID（可选）"
}
```

#### 2. 查询任务状态
```bash
GET /api/status/{task_id}
```

#### 3. 下载PRD
```bash
GET /api/download/{task_id}?format=json|docx|markdown
```

#### 4. 列出所有PRD
```bash
GET /api/prds?limit=50&offset=0
```

#### 5. 健康检查
```bash
GET /health
```

## 📝 注意事项

1. **生成时间**：PRD生成通常需要10-20分钟，请耐心等待
2. **网络稳定性**：确保网络连接稳定，避免生成中断
3. **API密钥**：确保已配置 `QWEN_API_KEY` 环境变量
4. **文件存储**：生成的PRD文件保存在 `artifacts/` 目录下

## 🐛 故障排除

### 生成失败

1. 查看任务状态中的错误信息
2. 检查API密钥是否正确配置
3. 检查网络连接
4. 查看后端日志

### 服务无法访问

1. 确认服务已启动（看到"Application startup complete"）
2. 确认端口8000未被占用
3. 尝试访问 http://127.0.0.1:8000

### API密钥问题

1. 检查 `.env` 文件中是否配置了 `QWEN_API_KEY`
2. 确认API密钥有效
3. 查看错误日志

## 💡 提示

- 首次使用建议先用简单的需求测试
- 生成完成后建议先预览内容再下载
- 可以同时生成多个PRD（使用不同的浏览器标签页）
- 所有生成的PRD都会保存在 `artifacts/` 目录下

## 📚 更多信息

- [详细使用指南](../docs/webui_guide.md)
- [快速启动指南](QUICKSTART.md)
- [API文档](http://localhost:8000/docs)

