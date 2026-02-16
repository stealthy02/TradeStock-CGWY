from sqlalchemy import Column, Integer, Numeric, Boolean, ForeignKey, Index, Date
from app.database import Base
from app.models.base import SoftDeleteMixin, TimestampMixin

class SaleStatement(Base, SoftDeleteMixin, TimestampMixin):
    __tablename__ = "t_sale_statement"
    
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    purchaser_id = Column(Integer, ForeignKey("t_purchaser.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False)
    start_date = Column(Date, nullable=True, comment="对账开始日期")
    end_date = Column(Date, nullable=True, comment="对账结束日期")
    statement_amount = Column(Numeric(10,2), default=0.00, nullable=False, comment="对账金额")
    total_cost = Column(Numeric(10,2), default=0.00, nullable=False, comment="销售总成本")
    total_profit = Column(Numeric(10,2), default=0.00, nullable=False, comment="销售总利润")
    received_amount = Column(Numeric(10,2), default=0.00, nullable=False, comment="已收金额")
    unreceived_amount = Column(Numeric(10,2), default=0.00, nullable=False, comment="未收金额")
    receive_status = Column(Boolean, default=False, nullable=False, comment="结款状态")
    invoice_status = Column(Boolean, default=False, nullable=False, comment="开票状态")
    
    __table_args__ = (
        Index('idx_purchaser_id', 'purchaser_id'),
        Index('idx_sale_statement_start_date', 'start_date'),
        Index('idx_sale_statement_end_date', 'end_date'),
        Index('idx_receive_status', 'receive_status'),
        Index('idx_sale_statement_invoice_status', 'invoice_status'),
        Index('idx_total_profit', 'total_profit'),
        Index('idx_sale_statement_is_deleted', 'is_deleted'),
        {'comment': '销售对账单表'}
    )