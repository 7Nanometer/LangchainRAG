@echo off
chcp 65001 >nul
title 下载 AI 模型
cd /d "%~dp0"
call "环境配置.bat"

echo.
echo ============================================
echo   下载本地 AI 模型（共约 3.5GB，国内源加速）
echo   包括：向量模型（约1.3GB）+ 精排模型（约2.2GB）
echo   支持断点续传，中断后重新运行即可接着下
echo ============================================
echo.

if not exist "%VENV_PY%" (
  echo [错误] 还没安装环境，请先双击 1-首次安装.bat
  pause
  exit /b 1
)

set "HF_HOME=%DATA_DIR%\hf_cache"
"%VENV_PY%" "%PROJECT_DIR%\backend\scripts\download_models.py"

echo.
pause
