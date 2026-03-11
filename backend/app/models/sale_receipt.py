from sqlalchemy import Column, Integer, Numeric, Date, String, Boolean, ForeignKey, Index
from app.database import Base
from app.models.base import SoftDeleteMixin, TimestampMixin

class SaleReceipt(Base, SoftDeleteMixin, TimestampMixin):
    __tablename__ = "t_sale_receipt"
    
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    statement_id = Column(Integer, ForeignKey("t_sale_statement.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False)
    receipt_date = Column(Date, nullable=False, comment="收款日期")
    receipt_amount = Column(Numeric(10,2), nullable=False, comment="收款金额")
    receipt_method = Column(String(20), nullable=False, comment="收款方式")
    remark = Column(String(200), comment="收款备注")
    
    __table_args__ = (
        Index('idx_sale_receipt_statement_id', 'statement_id'),
        Index('idx_receipt_date', 'receipt_date'),
        Index('idx_sale_receipt_is_deleted', 'is_deleted'),
        {'comment': '销售收款记录表'}
    )