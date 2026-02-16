from sqlalchemy import Column, Integer, String, Numeric, Date, Boolean, ForeignKey, Index
from app.database import Base
from app.models.base import SoftDeleteMixin, TimestampMixin

class PurchaseInfo(Base, SoftDeleteMixin, TimestampMixin):
    __tablename__ = "t_purchase_info"
    
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    supplier_id = Column(Integer, ForeignKey("t_supplier.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False)
    goods_id = Column(Integer, ForeignKey("t_goods.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False)
    product_spec = Column(String(20), nullable=False, comment="商品规格")
    purchase_num = Column(Integer, nullable=False, comment="采购数量")
    purchase_unit_price = Column(Numeric(10,2), nullable=False, comment="采购单价")
    purchase_total_price = Column(Numeric(10,2), nullable=False, comment="采购总价")
    purchase_date = Column(Date, nullable=False, comment="采购日期")
    statement_id = Column(Integer, ForeignKey("t_purchase_statement.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False)
    remark = Column(String(200), comment="备注")
    create_by = Column(Integer, comment="创建人ID")
    
    __table_args__ = (
        Index('idx_supplier_statement', 'supplier_id', 'statement_id'),
        Index('idx_purchase_info_goods_id', 'goods_id'),
        Index('idx_purchase_date', 'purchase_date'),
        Index('idx_purchase_info_is_deleted', 'is_deleted'),
        {'comment': '采购信息录入表'}   
    )