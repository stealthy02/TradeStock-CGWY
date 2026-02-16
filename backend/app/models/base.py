"""
模型基础类模块

该模块定义了模型的基础混入类，包括软删除和时间戳功能。
"""

from sqlalchemy import Column, DateTime, Boolean, func

from app.database import Base


class SoftDeleteMixin:
    """
    软删除混入
    
    为模型添加软删除功能，通过 is_deleted 字段标记记录状态。
    """
    is_deleted = Column(Boolean, default=False, nullable=False, comment="软删除：0-未删，1-已删")


class TimestampMixin:
    """
    时间戳混入
    
    为模型添加创建时间和更新时间字段，自动记录数据的变更时间。
    """
    create_time = Column(DateTime, server_default=func.now(), nullable=False, comment="创建时间")
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False, comment="更新时间")