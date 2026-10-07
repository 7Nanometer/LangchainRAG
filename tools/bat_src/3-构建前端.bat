@echo off
title 构建前端界面
cd /d "%~dp0"
call "%~dp0环境配置.bat"

echo.
echo ============================================
echo   把网页界面打包成成品（约 1~3 分钟）
echo ============================================
echo.

cd /d "%PROJECT_DIR%\frontend"

if not exist node_modules (
  echo [提示] 首次构建前需要先安装前端依赖...
  call npm install --registry=https://registry.npmmirror.com --no-fund --no-audit
)

call npm run build
if errorlevel 1 (
  echo.
  echo [错误] 前端构建失败，请把窗口里的报错信息截图反馈
  pause
  exit /b 1
)

echo.
echo ============================================
echo   构建完成！现在可以双击 4-启动系统.bat 了
echo ============================================
pause
