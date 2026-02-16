from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index, func  # 添加 func
from app.database import Base

class InventoryFlow(Base):
    __tablename__ = "t_inventory_flow"
    
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    goods_id = Column(Integer, ForeignKey("t_goods.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False)
    oper_type = Column(Integer, nullable=False, comment="操作类型：1-采购，2-销售，3-报损")
    biz_id = Column(Integer, nullable=False, comment="关联业务ID")
    change_num = Column(Integer, nullable=False, comment="变动数量")
    stock_before = Column(Integer, nullable=False, comment="操作前库存")
    stock_after = Column(Integer, nullable=False, comment="操作后库存")
    oper_time = Column(DateTime, nullable=False, comment="操作时间")
    oper_source = Column(String(100), nullable=False, comment="操作来源")
    
    __table_args__ = (
        Index('idx_goods_oper', 'goods_id', 'oper_type'),
        Index('idx_oper_time', 'oper_time'),
        Index('idx_biz_id', 'biz_id'),
        {'comment': '库存流动记录表'}
    )