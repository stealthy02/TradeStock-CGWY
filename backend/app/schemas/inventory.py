from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

# ==================== 商品基础 ====================
class GoodsBase(BaseModel):
    goods_name: str = Field(..., min_length=1, max_length=50, description="商品名称")

class GoodsCreate(GoodsBase):
    pass

class GoodsUpdate(GoodsBase):
    id: int = Field(..., description="商品ID")

class GoodsOut(BaseModel):
    id: int
    goods_name: str
    current_stock_num: int = Field(0, description="当前库存数量")
    stock_unit_cost: float = Field(0.00, description="库存单位成本(加权平均)")
    stock_total_value: float = Field(0.00, description="库存总价值")
    create_time: datetime
    
    class Config:
        from_attributes = True

class GoodsListResponse(BaseModel):
    total: int
    pages: int
    list: List[GoodsOut]

class GoodsSelectItem(BaseModel):
    goods_name: str

# ==================== 客户侧商品名映射 ====================
class CustomerGoodsNameCreate(BaseModel):
    goods_id: int
    purchaser_id: int
    customer_goods_name: str = Field(..., max_length=50)

class CustomerGoodsNameOut(BaseModel):
    id: int
    goods_name: str  # 系统商品名
    purchaser_name: str  # 采购商名
    customer_goods_name: str  # 客户侧名称
    update_time: datetime
    
    class Config:
        from_attributes = True