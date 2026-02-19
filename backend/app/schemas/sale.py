# 销售相关的数据传输对象
from pydantic import BaseModel, Field
from typing import Optional


# ==================== 销售信息 ====================
class SaleAdd(BaseModel):
    purchaser_name: str
    product_name: str
    product_spec: str
    customer_product_name: Optional[str] = None
    sale_num: int
    sale_price: float
    sale_date: str
    total_price: float
    remark: Optional[str] = None


class SaleUpdate(SaleAdd):
    id: int


# ==================== 销售收款 ====================
class SaleReceipt(BaseModel):
    bill_id: int
    receive_date: str
    receive_amount: float
    receive_method: str
    remark: Optional[str] = None


# ==================== 销售开票状态 ====================
class SaleInvoiceStatusUpdate(BaseModel):
    bill_id: int
    invoice_status: int


# ==================== 销售对账单确认 ====================
class SaleStatementConfirm(BaseModel):
    statement_id: int
    end_date: str
