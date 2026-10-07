@echo off
title LangchainRAG 系统（关掉本窗口 = 停止系统）
cd /d "%~dp0"
call "%~dp0环境配置.bat"

if not exist "%VENV_PY%" (
  echo [错误] 还没安装环境，请先双击 1-首次安装.bat
  pause
  exit /b 1
)
if not exist "%PROJECT_DIR%\frontend\dist\index.html" (
  echo [提示] 前端界面还没构建，请先双击 3-构建前端.bat
  pause
  exit /b 1
)

netstat -ano | findstr ":%SERVICE_PORT%" | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 (
  echo [提示] 端口 %SERVICE_PORT% 已被占用：
  echo        如果系统本来就在运行，直接打开 http://127.0.0.1:%SERVICE_PORT% 即可
  echo        如果不是，请关闭占用该端口的程序后重试
  pause
  exit /b 1
)

cd /d "%PROJECT_DIR%\backend"

echo.
echo ============================================
echo   正在启动知识库问答系统...
echo   浏览器稍后自动打开 http://127.0.0.1:%SERVICE_PORT%
echo.
echo   ★ 保持本窗口开着 = 系统运行中
echo   ★ 关掉本窗口   = 停止系统
echo ============================================
echo.

rem 等服务起来后再打开浏览器（等 5 秒）
start "" cmd /c "timeout /t 5 >nul & start http://127.0.0.1:%SERVICE_PORT%"

"%VENV_PY%" -m uvicorn app.main:app --host %SERVICE_HOST% --port %SERVICE_PORT%
pause
