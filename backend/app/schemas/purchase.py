from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# 统一响应模型
class ResponseModel(BaseModel):
    code: int
    message: str
    data: Optional[dict] = None


# 采购信息相关
class PurchaseCreate(BaseModel):
    supplier_id: int = Field(..., description="供货商ID")
    product_name: str = Field(..., min_length=1, max_length=50, description="商品名称")
    purchase_num: int = Field(..., gt=0, description="采购数量")
    purchase_price: float = Field(..., gt=0, description="采购单价")
    purchase_date: str = Field(..., description="采购日期(YYYY-MM-DD)")
    remark: Optional[str] = Field(None, max_length=200, description="备注")


class PurchaseUpdate(PurchaseCreate):
    id: int = Field(..., description="采购记录ID")


class PurchaseOut(BaseModel):
    id: int
    supplier_id: int
    supplier_name: str
    product_name: str
    purchase_num: int
    purchase_price: float
    total_price: float
    inventory_cost: float
    purchase_date: str
    cycle: str
    remark: str
    create_time: str
    
    class Config:
        from_attributes = True


class PurchaseListResponse(BaseModel):
    total: int
    pages: int
    list: List[PurchaseOut]


class ProductSelectItem(BaseModel):
    product_name: str


class LastPriceResponse(BaseModel):
    purchase_price: Optional[float]


# 对账单相关
class PaymentCreate(BaseModel):
    bill_id: int = Field(..., description="对账单ID")
    pay_date: str = Field(..., description="付款日期(YYYY-MM-DD)")
    pay_amount: float = Field(..., gt=0, description="付款金额")
    pay_method: str = Field(..., description="付款方式")
    remark: Optional[str] = Field(None, max_length=200)


class InvoiceUpdate(BaseModel):
    bill_id: int = Field(..., description="对账单ID")
    invoice_status: int = Field(..., ge=0, le=1, description="开票状态(0/1)")


class StatementOut(BaseModel):
    id: int
    supplier_id: int
    supplier_name: str
    cycle: str
    bill_amount: float
    received_amount: float
    unreceived_amount: float
    pay_status: int
    pay_status_text: str
    invoice_status: int
    invoice_status_text: str


class StatementListResponse(BaseModel):
    total: int
    pages: int
    list: List[StatementOut]


class PurchaseDetail(BaseModel):
    id: int
    product_name: str
    purchase_num: int
    total_price: float
    purchase_date: str
    remark: str


class PaymentRecord(BaseModel):
    id: int
    pay_date: str
    pay_amount: float
    pay_method: str
    remark: str


class StatementDetailResponse(BaseModel):
    bill_info: dict
    purchase_list: dict
    pay_record_list: dict