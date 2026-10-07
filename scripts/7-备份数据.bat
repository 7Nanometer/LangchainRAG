@echo off
title 备份数据
cd /d "%~dp0"
call "%~dp0环境配置.bat"

echo.
echo ============================================
echo   备份数据（账号、聊天记录、知识库、上传的文件）
echo   建议先关闭系统窗口再备份，数据更完整
echo ============================================
echo.

if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"
if not exist "%PROJECT_DIR%\backend\data" (
  echo [提示] 还没有任何数据，无需备份
  pause
  exit /b 0
)

powershell -NoProfile -Command "$ts = Get-Date -Format 'yyyyMMdd-HHmm'; Compress-Archive -Path '%PROJECT_DIR%\backend\data\*' -DestinationPath '%BACKUP_DIR%\data-$ts.zip' -Force; Write-Host ('备份完成：' + '%BACKUP_DIR%\data-' + $ts + '.zip')"

echo.
pause
