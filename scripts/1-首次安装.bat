@echo off
chcp 65001 >nul
title LangchainRAG 首次安装
cd /d "%~dp0"
call "环境配置.bat"

echo.
echo ============================================
echo   LangchainRAG 首次安装
echo   全程约 30~60 分钟（大部分时间在下载工具包）
echo   中途请不要关闭本窗口
echo ============================================
echo.

rem ---------- 检查 Python ----------
python --version >nul 2>&1
if errorlevel 1 (
  echo [错误] 没有找到 Python，请先安装 Python 3.13 后再运行本脚本
  pause
  exit /b 1
)

rem ---------- 准备 F 盘目录 ----------
if not exist "%DATA_DIR%" mkdir "%DATA_DIR%"
if not exist "%DATA_DIR%\logs" mkdir "%DATA_DIR%\logs"
if not exist "%DATA_DIR%\tmp" mkdir "%DATA_DIR%\tmp"
if not exist "%DATA_DIR%\pip_cache" mkdir "%DATA_DIR%\pip_cache"
if not exist "%DATA_DIR%\hf_cache" mkdir "%DATA_DIR%\hf_cache"
if not exist "%DATA_DIR%\backups" mkdir "%DATA_DIR%\backups"

rem ---------- 创建虚拟环境 ----------
if not exist "%VENV_PY%" (
  echo [1/5] 创建虚拟环境（F 盘，隔离本项目的工具间）...
  python -m venv "%VENV_DIR%"
  if errorlevel 1 (
    echo [错误] 虚拟环境创建失败
    pause
    exit /b 1
  )
) else (
  echo [1/5] 虚拟环境已存在，跳过
)

rem ---------- 安装缓存都指向 F 盘（防止撑爆 C 盘） ----------
set "PIP_CACHE_DIR=%DATA_DIR%\pip_cache"
set "TMP=%DATA_DIR%\tmp"
set "TEMP=%DATA_DIR%\tmp"
set "HF_HOME=%DATA_DIR%\hf_cache"

rem ---------- 安装 PyTorch（显卡加速版，约 2.8GB） ----------
echo.
echo [2/5] 安装 PyTorch 显卡加速版（约 2.8GB，最耗时的一步，请耐心等）...
"%VENV_PY%" -m pip install torch --index-url https://download.pytorch.org/whl/cu128 --disable-pip-version-check
if errorlevel 1 (
  echo.
  echo [警告] 显卡版 PyTorch 安装失败，自动改用普通版继续（功能不变，仅速度慢一些）
  "%VENV_PY%" -m pip install torch -i https://pypi.tuna.tsinghua.edu.cn/simple --disable-pip-version-check
)

rem ---------- 安装其余 Python 依赖 ----------
echo.
echo [3/5] 安装其余 Python 依赖（LangChain、FastAPI、Chroma 等）...
"%VENV_PY%" -m pip install -r "%PROJECT_DIR%\backend\requirements.txt" -i https://pypi.tuna.tsinghua.edu.cn/simple --disable-pip-version-check
if errorlevel 1 (
  echo [错误] Python 依赖安装失败，请检查网络后重新运行本脚本（已装好的不会重复下载）
  pause
  exit /b 1
)

rem ---------- 安装前端依赖 ----------
echo.
echo [4/5] 安装前端依赖包...
cd /d "%PROJECT_DIR%\frontend"
if not exist node_modules (
  call npm install --registry=https://registry.npmmirror.com --no-fund --no-audit
  if errorlevel 1 (
    echo [错误] 前端依赖安装失败
    pause
    exit /b 1
  )
) else (
  echo      前端依赖已存在，跳过
)

rem ---------- 生成配置文件 ----------
echo.
echo [5/5] 准备配置文件...
cd /d "%PROJECT_DIR%\backend"
if not exist ".env" (
  copy ".env.example" ".env" >nul
  echo      已生成 backend\.env （稍后把 DeepSeek 的 API Key 填进去）
) else (
  echo      backend\.env 已存在，跳过
)

echo.
echo ============================================
echo   安装完成！
echo.
echo   接下来请依次：
echo    1. 双击 2-下载模型.bat  （下载两个 AI 模型）
echo    2. 双击 3-构建前端.bat  （打包网页界面）
echo    3. 打开 backend\.env 文件：
echo       - 把 DeepSeek 的 API Key 填到 DEEPSEEK_API_KEY= 后面
echo       - 设置管理员密码 ADMIN_PASSWORD=（首次启动时生效）
echo    4. 双击 4-启动系统.bat  （日常启动用这个）
echo ============================================
pause
