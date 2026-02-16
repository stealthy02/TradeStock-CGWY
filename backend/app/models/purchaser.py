from sqlalchemy import Column, Integer, String, Boolean, Index, UniqueConstraint
from app.database import Base
from app.models.base import SoftDeleteMixin, TimestampMixin  # 确保导入

class Purchaser(Base, SoftDeleteMixin, TimestampMixin):  # 确保继承
    __tablename__ = "t_purchaser"
    
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    purchaser_name = Column(String(50), nullable=False, unique=True, comment="采购商名称(唯一)")
    contact_person = Column(String(20), comment="联系人")
    contact_phone = Column(String(20), comment="联系电话")
    company_address = Column(String(200), comment="公司地址")
    receive_address = Column(String(200), comment="收货地址")
    bank_name = Column(String(50), comment="开户行")
    bank_account = Column(String(50), comment="银行账号")
    tax_no = Column(String(50), comment="税号")
    avatar_url = Column(String(255), comment="头像地址")
    remark = Column(String(200), comment="备注")
    
    __table_args__ = (
        Index('idx_purchaser_contact_phone', 'contact_phone'),
        Index('idx_purchaser_is_deleted', 'is_deleted'),
        {'comment': '采购商信息表'}
    )