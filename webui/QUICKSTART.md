# AMPRD Web UI 快速启动指南

## 🚀 5分钟快速启动

### 步骤1：安装依赖

```bash
pip install fastapi uvicorn python-multipart
```

或使用完整依赖：
```bash
pip install -r requirements.txt
```

### 步骤2：配置API密钥

确保 `.env` 文件中已配置：
```bash
QWEN_API_KEY=your-api-key-here
```

### 步骤3：启动服务

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

或手动启动：
```bash
cd webui
python app.py
```

### 步骤4：访问Web界面

打开浏览器访问：**http://localhost:8000**

## 📝 使用示例

### 示例1：自然语言输入生成PRD

1. 在"生成PRD"标签页，选择"自然语言描述"
2. 输入：
   ```
   我们要做一个智能客服系统，目标是提升客户服务效率和用户体验。
   主要功能包括自动回复、智能路由和多语言支持。
   ```
3. 点击"开始生成PRD"
4. 等待10-20分钟
5. 生成完成后下载PRD文件

### 示例2：查看已生成的PRD

1. 点击"PRD列表"标签页
2. 点击"刷新列表"
3. 查看所有已生成的PRD
4. 点击"查看"预览内容
5. 点击"下载"按钮获取文件

## 🔗 重要链接

- **Web界面**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

## ❓ 常见问题

### Q: 端口被占用怎么办？
A: 修改 `webui/app.py` 中的端口号（默认8000）

### Q: 生成失败怎么办？
A: 检查API密钥是否正确配置，查看任务状态中的错误信息

### Q: 如何批量生成PRD？
A: 使用API接口（见 http://localhost:8000/docs）

## 📚 更多信息

详细文档请查看：[Web UI使用指南](../docs/webui_guide.md)

