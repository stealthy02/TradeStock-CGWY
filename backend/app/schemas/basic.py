from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from app.schemas.common import ResponseModel 
# ==================== 供货商 Schemas ====================
class SupplierBase(BaseModel):
    supplier_name: str = Field(..., min_length=1, max_length=50, description="供货商名称")
    contact_person: Optional[str] = Field(None, max_length=20, description="联系人")
    contact_phone: Optional[str] = Field(None, max_length=20, description="联系电话")
    company_address: Optional[str] = Field(None, max_length=200, description="公司地址")
    bank_name: Optional[str] = Field(None, max_length=50, description="开户行")
    bank_account: Optional[str] = Field(None, max_length=50, description="银行账号")
    tax_no: Optional[str] = Field(None, max_length=50, description="税号")
    remark: Optional[str] = Field(None, max_length=200, description="备注")
    avatar_url: Optional[str] = Field(None, max_length=255, description="头像URL") 

class SupplierCreate(SupplierBase):
    pass

class SupplierUpdate(SupplierBase):
    id: int = Field(..., description="供货商ID")

class SupplierOut(BaseModel):
    id: int
    supplier_name: str
    contact_person: Optional[str]
    contact_phone: Optional[str]
    company_address: Optional[str]
    avatar_url: Optional[str]
    remark: Optional[str]
    create_time: datetime
    
    class Config:
        from_attributes = True

class SupplierListResponse(BaseModel):
    total: int
    pages: int
    list: List[SupplierOut]

class SupplierSelectItem(BaseModel):
    id: int
    supplier_name: str

# ==================== 采购商 Schemas（对称） ====================
class PurchaserBase(BaseModel):
    purchaser_name: str = Field(..., min_length=1, max_length=50)
    contact_person: Optional[str] = Field(None, max_length=20)
    contact_phone: Optional[str] = Field(None, max_length=20)
    company_address: Optional[str] = Field(None, max_length=200)
    receive_address: Optional[str] = Field(None, max_length=200, description="收货地址")  # 比供货商多这个
    bank_name: Optional[str] = Field(None, max_length=50)
    bank_account: Optional[str] = Field(None, max_length=50)
    tax_no: Optional[str] = Field(None, max_length=50)
    remark: Optional[str] = Field(None, max_length=200)
    avatar_url: Optional[str] = Field(None, max_length=255)

class PurchaserCreate(PurchaserBase):
    pass

class PurchaserUpdate(PurchaserBase):
    id: int

class PurchaserOut(BaseModel):
    id: int
    purchaser_name: str
    contact_person: Optional[str]
    contact_phone: Optional[str]
    company_address: Optional[str]
    receive_address: Optional[str]  # 多这个字段
    avatar_url: Optional[str]
    remark: Optional[str]
    create_time: datetime
    
    class Config:
        from_attributes = True

class PurchaserListResponse(BaseModel):
    total: int
    pages: int
    list: List[PurchaserOut]

class PurchaserSelectItem(BaseModel):
    id: int
    purchaser_name: str