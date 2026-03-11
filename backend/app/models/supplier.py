# app/models/supplier.py
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Boolean, Index, UniqueConstraint
from app.database import Base
from app.models.base import SoftDeleteMixin, TimestampMixin  # 确保导入

class Supplier(Base, SoftDeleteMixin, TimestampMixin):  # 确保继承这两个类
    __tablename__ = "t_supplier"
    
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    supplier_name = Column(String(50), nullable=False, unique=True, comment="供货商名称(唯一)")
    contact_person = Column(String(20), comment="联系人")
    contact_phone = Column(String(20), comment="联系电话")
    company_address = Column(String(200), comment="公司地址")
    bank_name = Column(String(50), comment="开户行")
    bank_account = Column(String(50), comment="银行账号")
    tax_no = Column(String(50), comment="税号")
    avatar_url = Column(String(255), comment="头像地址")
    remark = Column(String(200), comment="备注")
    
    __table_args__ = (
        Index('idx_supplier_contact_phone', 'contact_phone'),
        Index('idx_supplier_is_deleted', 'is_deleted'),
        {'comment': '供货商信息表'}
    )


class SupplierSchema(BaseModel):
    id: int
    supplier_name: str
    contact_person: str | None = None
    phone: str | None = None
    company_address: str | None = None

    class Config:
        from_attributes = True  # Pydantic V2替代orm_mode，消除警告

# -------------------------- 分页返回模型（适配新的SupplierSchema） --------------------------
class SupplierListResponse(BaseModel):
    total: int
    list: list[SupplierSchema]  # 关联Pydantic序列化模型