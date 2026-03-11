from sqlalchemy import Column, Integer, Numeric, Date, String, Boolean, ForeignKey, Index
from app.database import Base
from app.models.base import SoftDeleteMixin, TimestampMixin

class PurchasePayment(Base, SoftDeleteMixin, TimestampMixin):
    __tablename__ = "t_purchase_payment"
    
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    statement_id = Column(Integer, ForeignKey("t_purchase_statement.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False)
    payment_date = Column(Date, nullable=False, comment="付款日期")
    payment_amount = Column(Numeric(10,2), nullable=False, comment="付款金额")
    payment_method = Column(String(20), nullable=False, comment="付款方式")
    remark = Column(String(200), comment="付款备注")
    
    __table_args__ = (
        Index('idx_purchase_payment_statement_id', 'statement_id'),
        Index('idx_payment_date', 'payment_date'),
        Index('idx_purchase_payment_is_deleted', 'is_deleted'),
        {'comment': '采购付款记录表'}
    )