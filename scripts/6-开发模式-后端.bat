@echo off
title 开发模式 - 后端（改代码自动生效）
cd /d "%~dp0"
call "%~dp0环境配置.bat"

if not exist "%VENV_PY%" (
  echo [错误] 还没安装环境，请先双击 1-首次安装.bat
  pause
  exit /b 1
)

cd /d "%PROJECT_DIR%\backend"
echo 后端开发服务（修改代码后自动重启）：http://127.0.0.1:%SERVICE_PORT%
"%VENV_PY%" -m uvicorn app.main:app --host 127.0.0.1 --port %SERVICE_PORT% --reload
pause
