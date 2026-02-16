from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Index, UniqueConstraint
from app.database import Base
from app.models.base import SoftDeleteMixin, TimestampMixin

class GoodsCustomerName(Base, SoftDeleteMixin, TimestampMixin):
    __tablename__ = "t_goods_customer_name"
    
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    goods_id = Column(Integer, ForeignKey("t_goods.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False)
    purchaser_id = Column(Integer, ForeignKey("t_purchaser.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False)
    customer_goods_name = Column(String(50), nullable=False, comment="客户侧商品名")
    
    __table_args__ = (
        UniqueConstraint('goods_id', 'purchaser_id', name='uk_goods_purchaser'),
        Index('idx_goods_customer_purchaser_id', 'purchaser_id'),
        Index('idx_goods_customer_is_deleted', 'is_deleted'),
        {'comment': '客户侧商品名映射表'}
    )