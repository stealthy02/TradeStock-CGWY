from sqlalchemy import Column, Integer, Numeric, Date, String, Boolean, ForeignKey, Index
from app.database import Base
from app.models.base import SoftDeleteMixin, TimestampMixin

class OperatingExpense(Base, SoftDeleteMixin, TimestampMixin):
    __tablename__ = "t_operating_expense"
    
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    expense_desc = Column(String(50), nullable=False, comment="费用描述")
    expense_type = Column(String(20), nullable=False, comment="费用类型")
    expense_amount = Column(Numeric(10,2), nullable=False, comment="费用金额")
    expense_date = Column(Date, nullable=False, comment="费用日期")
    remark = Column(String(200), comment="备注")
    
    __table_args__ = (
        Index('idx_expense_type', 'expense_type'),
        Index('idx_expense_date', 'expense_date'),
        Index('idx_operating_expense_is_deleted', 'is_deleted'),
        {'comment': '运营杂费表'}
    )