from fastapi import APIRouter, Query
from typing import Optional
from pydantic import BaseModel
from app.schemas.common import ResponseModel, PageModel
from app.services import cost_service

router = APIRouter()

class OperatingExpenseAdd(BaseModel):
    fee_desc: str
    fee_amount: float
    fee_date: str
    fee_type: str
    remark: Optional[str] = None

class OperatingExpenseUpdate(OperatingExpenseAdd):
    id: int

@router.post("/fee/add", response_model=ResponseModel[dict])
async def add_operating_expense(data: OperatingExpenseAdd):
    """
    6.1.1 新增运营杂费
    """
    result = await cost_service.add_operating_expense(data)
    return ResponseModel(data=result)

@router.get("/fee/list", response_model=ResponseModel[PageModel[dict]])
async def list_operating_expenses(
    fee_desc: Optional[str] = Query(None),
    fee_type: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    page_num: int = Query(1),
    page_size: int = Query(10)
):
    """
    6.1.2 查询杂费列表
    """
    result = await cost_service.list_operating_expenses(
        fee_desc, fee_type, start_date, end_date, page_num, page_size
    )
    return ResponseModel(data=result)

@router.put("/fee/update", response_model=ResponseModel[None])
async def update_operating_expense(data: OperatingExpenseUpdate):
    """
    6.1.3 修改杂费信息
    """
    await cost_service.update_operating_expense(data)
    return ResponseModel(message="修改杂费信息成功")

@router.delete("/fee/delete", response_model=ResponseModel[None])
async def delete_operating_expense(id: int = Query(...)):
    """
    6.1.4 删除杂费记录
    """
    await cost_service.delete_operating_expense(id)
    return ResponseModel(message="删除杂费记录成功")