@echo off
title 备份数据
cd /d "%~dp0"
call "%~dp0环境配置.bat"

echo.
echo ============================================
echo   备份数据（账号、聊天记录、知识库、上传的文件）
echo ============================================
echo.

rem 先检查系统是否在运行：运行中数据文件被占用，无法完整备份
netstat -ano | findstr ":%SERVICE_PORT%" | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 (
  echo [提示] 系统正在运行，数据文件被占用，无法完整备份。
  echo        请先关闭「4-启动系统.bat」的黑色窗口，再重新运行本脚本。
  pause
  exit /b 1
)

if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"
if not exist "%PROJECT_DIR%\backend\data" (
  echo [提示] 还没有任何数据，无需备份
  pause
  exit /b 0
)

powershell -NoProfile -Command "$ts = Get-Date -Format 'yyyyMMdd-HHmm'; Compress-Archive -Path '%PROJECT_DIR%\backend\data\*' -DestinationPath '%BACKUP_DIR%\data-$ts.zip' -Force; Write-Host ('备份完成：' + '%BACKUP_DIR%\data-' + $ts + '.zip')"

echo.
pause
