"""
配置管理模块

该模块负责加载环境变量和管理应用配置，特别是数据库连接配置。
支持开发环境和 Electron 打包环境的适配。
"""

import os
import sys
from functools import lru_cache
from dotenv import load_dotenv
from pathlib import Path


def get_base_dir():
    """
    获取基础目录
    
    Returns:
        Path: 基础目录路径
    """
    # 如果在打包环境中，使用 sys._MEIPASS 获取打包后的资源目录
    if hasattr(sys, '_MEIPASS'):
        return Path(sys._MEIPASS)
    # 否则使用文件所在目录的上级目录
    return Path(__file__).parent.parent


# 获取基础目录
base_dir = get_base_dir()

# 加载 .env 文件
env_path = base_dir / ".env"
load_dotenv(dotenv_path=env_path)


class Settings:
    """
    应用配置类
    
    管理应用的所有配置项，包括数据库连接配置等。
    """
    # SQLite 配置
    DB_NAME = os.getenv("DB_NAME", "easy_stock_db")
    
    # SQLite 数据库文件路径
    # 在打包环境中，将数据库文件放在可执行文件同级目录
    if hasattr(sys, '_MEIPASS'):
        # 获取可执行文件所在目录
        if os.name == 'nt':  # Windows
            # 获取可执行文件路径
            exe_path = Path(sys.executable)
            # 数据库文件放在可执行文件同级目录
            db_path = exe_path.parent / f"{DB_NAME}.db"
        else:
            # 其他系统类似处理
            exe_path = Path(sys.executable)
            db_path = exe_path.parent / f"{DB_NAME}.db"
        
        # 数据库文件路径
        DATABASE_URL = f"sqlite:///{db_path}"
    else:
        # 开发环境使用相对路径
        DATABASE_URL = f"sqlite:///./{DB_NAME}.db"
    
    # SQLite 不需要连接池配置


@lru_cache()
def get_settings():
    """
    获取配置实例（使用缓存提高性能）
    
    Returns:
        Settings: 配置实例
    """
    return Settings()


# 配置实例
settings = get_settings()