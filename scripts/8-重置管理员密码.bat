@echo off
title 重置管理员密码
cd /d "%~dp0"
call "%~dp0环境配置.bat"

echo.
echo ============================================
echo   重置管理员密码（忘记密码时使用）
echo ============================================
echo.

if not exist "%VENV_PY%" (
  echo [错误] 还没安装环境，请先双击 1-首次安装.bat
  pause
  exit /b 1
)

"%VENV_PY%" "%PROJECT_DIR%\backend\scripts\reset_admin.py"
pause
