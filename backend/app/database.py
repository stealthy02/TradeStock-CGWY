"""
数据库配置模块

该模块负责配置数据库连接、会话管理和基础模型类。
使用 SQLAlchemy ORM 与 SQLite 数据库交互。
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy import event

from app.config import settings


# 主引擎（连接 SQLite 数据库）
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},  # 允许在同一线程中使用连接
    poolclass=StaticPool,  # SQLite 使用静态连接池
    echo=False  # 生产环境设为 False
)


# 启用 WAL 模式
@event.listens_for(engine, 'connect')
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute('PRAGMA journal_mode = WAL;')
    cursor.close()


# 会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# 基础模型类
Base = declarative_base()


def get_db():
    """
    数据库会话依赖注入函数
    
    Yields:
        Session: 数据库会话实例
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()