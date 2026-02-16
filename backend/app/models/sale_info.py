from sqlalchemy import Column, Integer, Numeric, Date, String, Boolean, ForeignKey, Index
from app.database import Base
from app.models.base import SoftDeleteMixin, TimestampMixin


class SaleInfo(Base, SoftDeleteMixin, TimestampMixin):
    __tablename__ = "t_sale_info"
    
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    purchaser_id = Column(Integer, ForeignKey("t_purchaser.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False)
    goods_id = Column(Integer, ForeignKey("t_goods.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False)
    product_spec = Column(String(20), nullable=False, comment="商品规格")
    sale_num = Column(Integer, nullable=False, comment="销售数量")
    sale_unit_price = Column(Numeric(10,2), nullable=False, comment="销售单价")
    sale_total_price = Column(Numeric(10,2), nullable=False, comment="销售总价")
    trade_unit_cost = Column(Numeric(10,2), nullable=False, comment="交易时库存单位成本(快照)")
    unit_profit = Column(Numeric(10,2), nullable=False, comment="单位利润(快照)")
    total_profit = Column(Numeric(10,2), nullable=False, comment="总利润(快照)")
    sale_date = Column(Date, nullable=False, comment="销售日期")
    statement_id = Column(Integer, ForeignKey("t_sale_statement.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False)
    remark = Column(String(200), comment="备注")
    create_by = Column(Integer, comment="创建人ID")
    
    __table_args__ = (
        Index('idx_purchaser_statement', 'purchaser_id', 'statement_id'),
        Index('idx_sale_info_goods_id', 'goods_id'),
        Index('idx_sale_date', 'sale_date'),      
        Index('idx_sale_info_is_deleted', 'is_deleted'),
        {'comment': '销售信息录入表'}
    )