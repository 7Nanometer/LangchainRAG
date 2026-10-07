@echo off
title 环境检查
cd /d "%~dp0"
call "%~dp0环境配置.bat"

echo.
echo ============================================
echo   电脑环境检查（装系统前先跑这个看看）
echo ============================================
echo.
echo [1/4] Python（后端程序的运行环境）
python --version 2>nul
if errorlevel 1 echo    [缺失] 没找到 Python，需要先安装 Python 3.13
echo.
echo [2/4] Node.js（前端界面的构建工具）
node --version 2>nul
if errorlevel 1 echo    [缺失] 没找到 Node.js，需要先安装
call npm --version 2>nul
echo.
echo [3/4] 显卡（本地 AI 模型靠它加速）
nvidia-smi --query-gpu=name,memory.total --format=csv 2>nul
if errorlevel 1 echo    [提示] 没检测到 NVIDIA 显卡，模型会改用 CPU 运行（慢一些但不影响功能）
echo.
echo [4/4] 磁盘空间（是否够装）
powershell -NoProfile -Command "Get-CimInstance Win32_LogicalDisk | Select-Object DeviceID,VolumeName,@{n='剩余GB';e={[math]::Round($_.FreeSpace/1GB,1)}} | Format-Table -AutoSize"
echo.
echo E 盘放代码和数据（约需 1GB）；F 盘放工具和模型（约需 12GB）
echo.
pause
