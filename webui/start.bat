@echo off
REM AMPRD Web UI 启动脚本 (Windows)

echo 🚀 启动 AMPRD Web UI...

REM 检查Python环境
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python未安装，请先安装Python 3.8+
    pause
    exit /b 1
)

REM 检查依赖
echo 📦 检查依赖...
pip install fastapi uvicorn python-multipart -q

REM 切换到webui目录
cd /d "%~dp0"

REM 启动服务
echo ✅ 启动服务中...
python app.py

pause

