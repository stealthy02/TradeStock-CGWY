"""
商品模型模块

该模块定义了商品信息模型，包含商品的基本信息和库存状态。
"""

from sqlalchemy import Column, Integer, String, Numeric, Index, UniqueConstraint

from app.database import Base
from app.models.base import SoftDeleteMixin, TimestampMixin


class Goods(Base, SoftDeleteMixin, TimestampMixin):
    """
    商品信息表（实时库存）
    
    存储商品的基本信息和实时库存状态，包括商品名称、规格、库存数量和成本等。
    """
    __tablename__ = "t_goods"
    
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False, comment="商品ID")
    goods_name = Column(String(50), nullable=False, comment="商品名称")
    product_spec = Column(Integer, nullable=False, comment="商品规格")
    current_stock_num = Column(Integer, default=0, nullable=False, comment="当前库存数量")
    stock_unit_cost = Column(Numeric(10, 2), default=0.00, nullable=False, comment="库存单位成本(加权平均)")
    stock_total_value = Column(Numeric(10, 2), default=0.00, nullable=False, comment="库存总价值")
    
    __table_args__ = (
        UniqueConstraint('goods_name', 'product_spec', name='uix_goods_spec'),
        Index('idx_goods_current_stock_num', 'current_stock_num'),
        Index('idx_goods_is_deleted', 'is_deleted'),
        {'comment': '商品信息表（实时库存）'}
    )