# -*- coding: utf-8 -*-
r"""
数据库连接 —— 管理 SQLite 数据库的"总开关"

SQLite 是一个"文件型数据库"：不需要安装任何软件，所有数据存在
backend\data\app.db 这一个文件里。

这里做了三件重要的性能优化（企业级标配）：
  1. WAL 模式：读写可以同时进行，不会互相堵车
  2. busy_timeout：数据库忙的时候先排队等 5 秒，而不是直接报错
  3. 外键约束：防止出现"孤儿数据"（比如删了用户但他的会话还留着）
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import DB_PATH

# 连接引擎：check_same_thread=False 是 SQLite 配合 Web 服务的标准写法。
# 连接池参数经过压力测试调优：高并发时默认的 5+10 个连接会被瞬间抽干，
# 导致 "QueuePool limit ... connection timed out" 错误（实测复现过）。
engine = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False, "timeout": 30},
    pool_size=20,          # 常备连接数
    max_overflow=40,       # 高峰期可临时超借到 60 个
    pool_timeout=30,       # 借不到连接的等待上限（秒）
    pool_recycle=3600,     # 连接用满 1 小时回收重建
    echo=False,
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, _connection_record):
    """每次建立数据库连接时，自动执行这些优化设置"""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")     # 开启 WAL 模式
    cursor.execute("PRAGMA foreign_keys=ON")      # 开启外键约束
    cursor.execute("PRAGMA busy_timeout=5000")    # 忙时等待 5 秒
    cursor.execute("PRAGMA synchronous=NORMAL")   # 兼顾安全与速度
    cursor.close()


class Base(DeclarativeBase):
    """所有数据库表的"父类"，表结构定义都继承它"""


# 会话工厂：每个请求从这里取一个数据库会话，用完归还
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db():
    """
    FastAPI 依赖项：每个接口请求自动获得一个数据库会话，
    请求结束时自动关闭（yield 之前相当于"打开"，之后相当于"关闭"）。
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
