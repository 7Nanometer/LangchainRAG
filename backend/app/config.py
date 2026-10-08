# -*- coding: utf-8 -*-
r"""
配置中心 —— 全项目的"总控台"

所有可调的设置都集中在这里：
  - 读取 backend\.env 文件里的配置（比如 DeepSeek 的 API Key）
  - 定义各种文件路径（数据库、上传目录、日志等）
  - 定义检索、缓存等业务参数

想改任何设置：优先改 .env 文件；.env 里没有的项用本文件的默认值。
"""
import os
import secrets
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# ---------- 路径定义 ----------
# BASE_DIR 指向 backend 文件夹（本文件是 backend/app/config.py，往上两级）
BASE_DIR = Path(__file__).resolve().parent.parent
# 运行数据目录（数据库、向量库、上传的文件、日志都在这里面）
# 可用环境变量 RAG_DATA_DIR 覆盖 —— 用于测试隔离等场景
DATA_DIR = Path(os.environ.get("RAG_DATA_DIR") or (BASE_DIR / "data"))
UPLOAD_DIR = DATA_DIR / "uploads"       # 管理员上传的原始文档
CHROMA_DIR = DATA_DIR / "chroma"        # Chroma 向量库目录
LOG_DIR = DATA_DIR / "logs"             # 日志文件
DB_PATH = DATA_DIR / "app.db"           # SQLite 数据库文件
FRONTEND_DIST = BASE_DIR.parent / "frontend" / "dist"   # 前端打包后的成品（由后端托管）


def get_or_create_secret_key() -> str:
    r"""
    获取 JWT 加密密钥（相当于系统内部盖章用的私章）。

    首次启动时自动生成一串随机字符并保存到 data\.jwt_secret，
    之后每次启动都读同一个文件 —— 保证"重启后已登录用户不掉线"。
    """
    secret_file = DATA_DIR / ".jwt_secret"
    if secret_file.exists():
        return secret_file.read_text(encoding="utf-8").strip()
    secret = secrets.token_hex(32)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    secret_file.write_text(secret, encoding="utf-8")
    return secret


class Settings(BaseSettings):
    """全部配置项（括号里是 .env 文件中的变量名）"""

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ---- 服务端口 ----
    host: str = "127.0.0.1"
    port: int = 8000

    # ---- DeepSeek 大模型 ----
    deepseek_api_key: str = ""                              # 需要你填（.env 文件里）
    deepseek_model: str = "deepseek-flash"                  # 模型名（可在 .env 覆盖）
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_temperature: float = 0.3                       # 越低回答越稳定
    deepseek_max_tokens: int = 1024                         # 单次回答长度上限
    deepseek_timeout_s: int = 60                            # 请求超时（秒）

    # ---- 管理员账号（仅首次启动自动创建时使用）----
    # 安全设计：密码不写在代码里（防止代码仓库泄漏时连带泄漏密码），
    # 必须在 backend\.env 文件中配置 ADMIN_PASSWORD 才会创建管理员
    admin_username: str = "7Nanometer"
    admin_password: str = ""

    # ---- 登录通行证（JWT）----
    jwt_expire_hours: int = 72                              # 通行证有效期（小时）

    # ---- 本地 AI 模型（F 盘，由 2-下载模型.bat 下载）----
    embedding_model_path: str = r"F:\LangchainRAG-data\models\bge-large-zh-v1.5"
    reranker_model_path: str = r"F:\LangchainRAG-data\models\bge-reranker-v2-m3"
    model_device: str = "auto"                              # auto=自动选显卡或CPU / cuda / cpu

    # ---- 检索参数 ----
    vector_top_k: int = 20          # 向量检索粗召回条数
    bm25_top_k: int = 20            # 关键词检索粗召回条数
    rerank_top_n: int = 5           # 精排后最终采用条数
    # 精排相关度阈值（低于它视为不相关→兜底）。
    # 依据实测：bge-reranker 的分数以 0.5 为"零点"——无关片段≈0.500，
    # 相关片段 0.55~0.79。取 0.52 为分界线（留出安全余量）
    rerank_threshold: float = 0.52
    chunk_size: int = 500           # 文档分块大小（字符）
    chunk_overlap: int = 50         # 分块重叠（防止一句话被拦腰切断）

    # ---- 问答缓存 ----
    qa_cache_enabled: bool = True              # 是否启用语义缓存（压测等场景可关闭）
    cache_similarity_threshold: float = 0.92   # 相似度高于此值直接复用旧答案
    cache_max_entries: int = 5000              # 缓存条数上限

    # ---- 限流（防 API 费用失控）----
    rate_limit_per_minute: int = 20            # 每用户每分钟最多提问次数

    # ---- 上传 ----
    max_upload_mb: int = 50                    # 单个文件大小上限（MB）


settings = Settings()

# 确保运行数据目录存在（程序一启动就建好，免得到处判断）
for _d in (DATA_DIR, UPLOAD_DIR, CHROMA_DIR, LOG_DIR):
    _d.mkdir(parents=True, exist_ok=True)
