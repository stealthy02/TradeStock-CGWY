from sqlalchemy import Column, Integer, Numeric, Boolean, ForeignKey, Index, Date
from app.database import Base
from app.models.base import SoftDeleteMixin, TimestampMixin


class PurchaseStatement(Base, SoftDeleteMixin, TimestampMixin):
    __tablename__ = "t_purchase_statement"
    
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    supplier_id = Column(Integer, ForeignKey("t_supplier.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False)
    start_date = Column(Date, nullable=True, comment="对账开始日期")
    end_date = Column(Date, nullable=True, comment="对账结束日期")
    statement_amount = Column(Numeric(10,2), default=0.00, nullable=False, comment="对账金额")
    received_amount = Column(Numeric(10,2), default=0.00, nullable=False, comment="已付金额")
    unreceived_amount = Column(Numeric(10,2), default=0.00, nullable=False, comment="未付金额")
    pay_status = Column(Boolean, default=False, nullable=False, comment="结款状态：0-未结清，1-已结清")
    invoice_status = Column(Boolean, default=False, nullable=False, comment="开票状态：0-未开票，1-已开票") 
    
    __table_args__ = (
        Index('idx_supplier_id', 'supplier_id'),
        Index('idx_purchase_statement_start_date', 'start_date'),
        Index('idx_purchase_statement_end_date', 'end_date'),
        Index('idx_pay_status', 'pay_status'),
        Index('idx_purchase_statement_invoice_status', 'invoice_status'),
        Index('idx_purchase_statement_is_deleted', 'is_deleted'),
        {'comment': '采购对账单表'}
    )