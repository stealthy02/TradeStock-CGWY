from fastapi import APIRouter, Query, Path
from typing import Optional, List
from pydantic import BaseModel
from app.schemas.common import ResponseModel, PageModel
from app.services import basic_service

router = APIRouter()

# ==================== 供货商相关 ====================

class SupplierAdd(BaseModel):
    supplier_name: str
    contact_person: str
    contact_phone: str
    company_address: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    tax_no: Optional[str] = None
    remark: Optional[str] = None
    avatar_url: Optional[str] = None

class SupplierUpdate(SupplierAdd):
    id: int

@router.post("/supplier/add", response_model=ResponseModel[dict])
async def add_supplier(data: SupplierAdd):
    """
    2.1.1 新增供货商
    """
    result = await basic_service.add_supplier(data)
    return ResponseModel(data=result)

@router.get("/supplier/list", response_model=ResponseModel[PageModel[dict]])
async def list_suppliers(
    supplier_name: Optional[str] = Query(None),
    contact_phone: Optional[str] = Query(None),
    page_num: int = Query(1),
    page_size: int = Query(10)
):
    """
    2.1.2 查询供货商列表
    """
    result = await basic_service.list_suppliers(supplier_name, contact_phone, page_num, page_size)
    return ResponseModel(data=result)

@router.put("/supplier/update", response_model=ResponseModel[None])
async def update_supplier(data: SupplierUpdate):
    """
    2.1.3 修改供货商
    """
    await basic_service.update_supplier(data)
    return ResponseModel(message="修改供货商成功")

@router.delete("/supplier/delete", response_model=ResponseModel[None])
async def delete_supplier(id: int = Query(...)):
    """
    2.1.4 删除供货商
    """
    await basic_service.delete_supplier(id)
    return ResponseModel(message="删除供货商成功")

@router.get("/supplier/select", response_model=ResponseModel[List[str]])
async def select_suppliers(keyword: Optional[str] = Query(None), limit: int = Query(5, ge=1, le=50)):
    """
    2.1.5 供货商下拉联想
    """
    result = await basic_service.select_suppliers(keyword, limit=limit)
    return ResponseModel(data=result)

# ==================== 采购商相关 ====================

class PurchaserAdd(BaseModel):
    purchaser_name: str
    contact_person: str
    contact_phone: str
    company_address: Optional[str] = None
    receive_address: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    tax_no: Optional[str] = None
    remark: Optional[str] = None
    avatar_url: Optional[str] = None

class PurchaserUpdate(PurchaserAdd):
    id: int

@router.post("/purchaser/add", response_model=ResponseModel[dict])
async def add_purchaser(data: PurchaserAdd):
    """
    2.2.1 新增采购商（对应2.1.1）
    """
    result = await basic_service.add_purchaser(data)
    return ResponseModel(data=result)

@router.get("/purchaser/list", response_model=ResponseModel[PageModel[dict]])
async def list_purchasers(
    purchaser_name: Optional[str] = Query(None),
    contact_phone: Optional[str] = Query(None),
    page_num: int = Query(1),
    page_size: int = Query(10)
):
    """
    2.2.2 查询采购商列表
    """
    result = await basic_service.list_purchasers(purchaser_name, contact_phone, page_num, page_size)
    return ResponseModel(data=result)

@router.put("/purchaser/update", response_model=ResponseModel[None])
async def update_purchaser(data: PurchaserUpdate):
    """
    2.2.3 修改采购商
    """
    await basic_service.update_purchaser(data)
    return ResponseModel(message="修改采购商成功")

@router.delete("/purchaser/delete", response_model=ResponseModel[None])
async def delete_purchaser(id: int = Query(...)):
    """
    2.2.4 删除采购商
    """
    await basic_service.delete_purchaser(id)
    return ResponseModel(message="删除采购商成功")

@router.get("/purchaser/select", response_model=ResponseModel[List[str]])
async def select_purchasers(keyword: Optional[str] = Query(None), limit: int = Query(5, ge=1, le=50)):
    """
    2.2.5 采购商下拉联想
    """
    result = await basic_service.select_purchasers(keyword, limit=limit)
    return ResponseModel(data=result)