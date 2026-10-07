@echo off
title 导入示例商品数据
cd /d "%~dp0"
call "%~dp0环境配置.bat"

echo.
echo ============================================
echo   导入示例商品资料（用于演示和验收）
echo   将生成 5 份商品文档并走真实入库流程
echo ============================================
echo.

if not exist "%VENV_PY%" (
  echo [错误] 还没安装环境，请先双击 1-首次安装.bat
  pause
  exit /b 1
)
if not exist "%PROJECT_DIR%\backend\scripts\seed_demo.py" (
  echo [提示] 示例数据脚本尚未就绪（将在 M2 里程碑提供）
  pause
  exit /b 0
)

cd /d "%PROJECT_DIR%\backend"
"%VENV_PY%" "%PROJECT_DIR%\backend\scripts\seed_demo.py"
pause
