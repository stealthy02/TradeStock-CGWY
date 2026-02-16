from fastapi import APIRouter, Query
from typing import Optional, List
from pydantic import BaseModel
from app.schemas.common import ResponseModel, PageModel
from app.services import inventory_service

router = APIRouter()

# ==================== 库存信息查询 ====================

@router.get("/list", response_model=ResponseModel[PageModel[dict]])
async def list_inventory(
    product_name: Optional[str] = Query(None),
    min_num: Optional[int] = Query(None),
    max_num: Optional[int] = Query(None),
    sort_field: Optional[str] = Query(None),
    sort_order: Optional[str] = Query(None),
    page_num: int = Query(1),
    page_size: int = Query(10)
):
    """
    5.1.1 查询当前库存列表
    """
    result = await inventory_service.list_inventory(
        product_name, min_num, max_num, sort_field, sort_order, page_num, page_size
    )
    return ResponseModel(data=result)

@router.get("/detail", response_model=ResponseModel[dict])
async def get_inventory_detail(
    product_name: str = Query(...),
    product_spec: str = Query(...),
    page_num: int = Query(1),
    page_size: int = Query(10)
):
    """
    5.1.2 单个商品库存详情（含变动记录）
    """
    result = await inventory_service.get_inventory_detail(
        product_name, product_spec, page_num, page_size
    )
    return ResponseModel(data=result)

# ==================== 库存报损 ====================

class InventoryLossAdd(BaseModel):
    product_name: str
    product_spec: str
    loss_num: int
    loss_date: str
    loss_reason: Optional[str] = None

@router.post("/loss/add", response_model=ResponseModel[dict])
async def add_inventory_loss(data: InventoryLossAdd):
    """
    5.2.1 新增库存报损
    """
    result = await inventory_service.add_inventory_loss(data)
    return ResponseModel(data=result)

@router.get("/loss/list", response_model=ResponseModel[PageModel[dict]])
async def list_inventory_loss(
    id: Optional[int] = Query(None),
    product_name: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    page_num: int = Query(1),
    page_size: int = Query(10)
):
    """
    5.2.2 查询库存报损列表
    """
    result = await inventory_service.list_inventory_loss(
        id, product_name, start_date, end_date, page_num, page_size
    )
    return ResponseModel(data=result)

@router.delete("/loss/delete", response_model=ResponseModel[None])
async def delete_inventory_loss(id: int = Query(...)):
    """
    5.2.3 删除报损记录（恢复库存）
    """
    await inventory_service.delete_inventory_loss(id)
    return ResponseModel(message="删除报损记录成功，已恢复库存")

# ==================== 库存预警/盘点 ====================

@router.get("/warning", response_model=ResponseModel[PageModel[dict]])
async def list_inventory_warning(
    warning_line: int = Query(5),
    page_num: int = Query(1),
    page_size: int = Query(10)
):
    """
    5.3.1 查询库存预警列表（低于预警线）
    """
    result = await inventory_service.list_inventory_warning(warning_line, page_num, page_size)
    return ResponseModel(data=result)

class CheckItem(BaseModel):
    product_name: str
    product_spec: int
    actualNum: int
    diffReason: Optional[str] = None

class InventoryCheck(BaseModel):
    checkDate: str
    remark: Optional[str] = None
    checkList: List[CheckItem]