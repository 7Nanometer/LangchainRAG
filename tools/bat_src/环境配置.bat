@echo off
rem =====================================================================
rem  环境配置 - 全项目所有路径集中在这一个文件里
rem  将来如果要换盘/换端口，只改这里一处，其他脚本自动跟着变
rem =====================================================================

rem 项目目录（代码和你的数据都在这里）
set "PROJECT_DIR=E:\Vibe Coding\LangchainRAG项目"

rem 重型组件目录（虚拟环境和 AI 模型约 12GB，放 F 盘）
set "DATA_DIR=F:\LangchainRAG-data"
set "VENV_DIR=%DATA_DIR%\venv"
set "VENV_PY=%VENV_DIR%\Scripts\python.exe"
set "MODELS_DIR=%DATA_DIR%\models"
set "BACKUP_DIR=%DATA_DIR%\backups"

rem 服务端口（浏览器访问 http://127.0.0.1:8000）
set "SERVICE_PORT=8000"

rem 服务监听地址：
rem   127.0.0.1 = 只有本机能用（默认，最安全）
rem   0.0.0.0   = 局域网内的手机/其他电脑也能访问（详见运维手册第五节）
set "SERVICE_HOST=127.0.0.1"
