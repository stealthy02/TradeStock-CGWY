from sqlalchemy import Column, Integer, Numeric, Date, String, Boolean, ForeignKey, Index
from app.database import Base
from app.models.base import SoftDeleteMixin, TimestampMixin

class InventoryLoss(Base, SoftDeleteMixin, TimestampMixin):
    __tablename__ = "t_inventory_loss"
    
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    goods_id = Column(Integer, ForeignKey("t_goods.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False)
    loss_num = Column(Integer, nullable=False, comment="报损数量")
    loss_unit_cost = Column(Numeric(10,2), nullable=False, comment="报损时单位成本(快照)")
    loss_total_cost = Column(Numeric(10,2), nullable=False, comment="报损总成本")
    loss_date = Column(Date, nullable=False, comment="报损日期")
    loss_reason = Column(String(50), comment="报损原因")
    remark = Column(String(200), comment="备注")
    
    __table_args__ = (
        Index('idx_inventory_loss_goods_id', 'goods_id'),
        Index('idx_loss_date', 'loss_date'),
        Index('idx_inventory_loss_is_deleted', 'is_deleted'),
        {'comment': '库存报损表'}
    )