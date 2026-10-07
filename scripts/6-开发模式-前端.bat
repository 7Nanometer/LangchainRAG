@echo off
chcp 65001 >nul
title 开发模式 - 前端（改界面即时预览）
cd /d "%~dp0"
call "环境配置.bat"

cd /d "%PROJECT_DIR%\frontend"
if not exist node_modules (
  echo [提示] 需要先安装前端依赖...
  call npm install --registry=https://registry.npmmirror.com --no-fund --no-audit
)
echo 前端开发服务：http://127.0.0.1:5173 （需同时运行 6-开发模式-后端.bat）
call npm run dev
pause
