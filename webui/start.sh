#!/bin/bash
# AMPRD Web UI 启动脚本

echo "🚀 启动 AMPRD Web UI..."

# 检查Python环境
if ! command -v python &> /dev/null; then
    echo "❌ Python未安装，请先安装Python 3.8+"
    exit 1
fi

# 检查依赖
echo "📦 检查依赖..."
pip install fastapi uvicorn python-multipart -q

# 切换到webui目录
cd "$(dirname "$0")"

# 启动服务
echo "✅ 启动服务中..."
python app.py

