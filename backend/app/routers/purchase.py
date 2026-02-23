from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from typing import Optional, List
from pydantic import BaseModel
from urllib.parse import quote
from app.schemas.common import ResponseModel, PageModel
from app.services import purchase_service

router = APIRouter()

# ==================== 采购信息录入 ====================

class PurchaseAdd(BaseModel):
    supplier_name: str
    product_name: str
    product_spec: str
    purchase_num: int
    purchase_price: float
    purchase_date: str
    remark: Optional[str] = None

class PurchaseUpdate(PurchaseAdd):
    id: int

@router.post("/info/add", response_model=ResponseModel[dict])
async def add_purchase(data: PurchaseAdd):
    """
    3.1.1 新增采购信息
    """
    result = await purchase_service.add_purchase(data)
    return ResponseModel(data=result)

@router.get("/info/list", response_model=ResponseModel[PageModel[dict]])
async def list_purchase_info(
    id: Optional[int] = Query(None),
    supplier_name: Optional[str] = Query(None),
    product_name: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    sort_field: Optional[str] = Query(None),
    sort_order: Optional[str] = Query(None),
    page_num: int = Query(1),
    page_size: int = Query(10)
):
    """
    3.1.2 查询采购信息列表
    """
    result = await purchase_service.list_purchase_info(
        id, supplier_name, product_name, start_date, end_date,
        sort_field, sort_order, page_num, page_size
    )
    return ResponseModel(data=result)

@router.put("/info/update", response_model=ResponseModel[None])
async def update_purchase(data: PurchaseUpdate):
    """
    3.1.3 修改采购信息
    """
    await purchase_service.update_purchase(data)
    return ResponseModel(message="修改采购信息成功，已同步更新对账单和库存")

@router.delete("/info/delete", response_model=ResponseModel[None])
async def delete_purchase(id: int = Query(...)):
    """
    3.1.4 删除采购信息
    """
    await purchase_service.delete_purchase(id)
    return ResponseModel(message="删除采购信息成功，已同步更新对账单和库存")

@router.get("/info/product_select", response_model=ResponseModel[List[str]])
async def select_purchase_products(keyword: Optional[str] = Query(None), limit: int = Query(5, ge=1, le=50)):
    """
    3.1.5 采购商品下拉联想
    """
    result = await purchase_service.select_purchase_products(keyword, limit=limit)
    return ResponseModel(data=result)

@router.get("/info/last_record", response_model=ResponseModel[Optional[dict]])
async def get_last_purchase_record(
    supplier_name: str = Query(...),
    product_name: str = Query(...)
):
    """
    3.1.6 获取上一次采购记录
    """
    result = await purchase_service.get_last_purchase_record(supplier_name, product_name)
    return ResponseModel(data=result)

# ==================== 采购对账单 ====================

@router.get("/bill/list", response_model=ResponseModel[PageModel[dict]])
async def list_purchase_bills(
    supplier_name: Optional[str] = Query(None),
    pay_status: Optional[str] = Query(None, pattern="^(\\d+|)$"),
    invoice_status: Optional[str] = Query(None, pattern="^(\\d+|)$"),
    min_amount: Optional[float] = Query(None),
    max_amount: Optional[float] = Query(None),
    page_num: int = Query(1),
    page_size: int = Query(10)
):
    """
    3.2.1 查询采购对账单列表
    """
    # 处理空字符串情况
    pay_status_int = int(pay_status) if pay_status and pay_status.strip() else None
    invoice_status_int = int(invoice_status) if invoice_status and invoice_status.strip() else None
    
    result = await purchase_service.list_purchase_bills(
        supplier_name, pay_status_int, invoice_status_int, min_amount, max_amount, page_num, page_size
    )
    return ResponseModel(data=result)

@router.get("/bill/detail", response_model=ResponseModel[dict])
async def get_purchase_bill_detail(bill_id: int = Query(...), supplier_id: Optional[int] = Query(None), end_date: Optional[str] = Query(None)):
    """
    3.2.2 查看采购对账单细则
    """
    result = await purchase_service.get_purchase_bill_detail(bill_id, end_date)
    return ResponseModel(data=result)


@router.get("/bill/export")
async def export_purchase_bill(bill_id: int = Query(...), end_date: Optional[str] = Query(None)):
    """
    导出采购对账单
    """
    result = await purchase_service.export_purchase_bill(bill_id, end_date)
    
    def iterfile():
        yield result["xlsx_bytes"]
    
    encoded_filename = quote(result["filename"])
    return StreamingResponse(
        iterfile(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename*=UTF-8\'\'{encoded_filename}'
        }
    )

class PurchasePayment(BaseModel):
    bill_id: int
    pay_date: str
    pay_amount: float
    pay_method: str
    remark: Optional[str] = None

@router.post("/bill/pay", response_model=ResponseModel[dict])
async def add_purchase_payment(data: PurchasePayment):
    """
    3.2.3 录入采购付款记录
    """
    result = await purchase_service.add_purchase_payment(data)
    return ResponseModel(data=result)

class InvoiceStatusUpdate(BaseModel):
    bill_id: int
    invoice_status: int

@router.put("/bill/update_invoice_status", response_model=ResponseModel[None])
async def update_purchase_invoice_status(data: InvoiceStatusUpdate):
    """
    3.2.4 修改采购对账单开票状态
    """
    await purchase_service.update_purchase_invoice_status(data.bill_id, data.invoice_status)
    return ResponseModel(message="开票状态修改成功")


@router.delete("/bill/pay/delete", response_model=ResponseModel[dict])
async def delete_purchase_payment(payment_id: int = Query(...)):
    """
    删除付款记录
    """
    result = await purchase_service.delete_purchase_payment(payment_id)
    return ResponseModel(data=result, message="删除付款记录成功，已同步更新对账单")

# ==================== 采购对账单管理 ====================

class PurchaseStatementConfirm(BaseModel):
    statement_id: int
    end_date: str

@router.post("/statement/confirm", response_model=ResponseModel[None])
async def confirm_purchase_statement(data: PurchaseStatementConfirm):
    """
    确认采购对账单
    """
    from app.repositories.purchase_statement_repo import PurchaseStatementRepository
    from app.repositories.purchase_info_repo import PurchaseInfoRepository
    from app.database import get_db
    from datetime import datetime, timedelta
    
    db = next(get_db())
    statement_repo = PurchaseStatementRepository(db)
    purchase_info_repo = PurchaseInfoRepository(db)
    
    # 获取对账单信息
    statement = statement_repo.get_by_id(data.statement_id)
    if not statement:
        from app.utils.exceptions import NotFoundException
        raise NotFoundException(message="对账单不存在")
    
    # 解析结束日期
    end_date = datetime.strptime(data.end_date, "%Y-%m-%d").date()
    
    # 检查结束日期是否早于起始日期
    # 确保起始日期是date对象
    start_date = statement["start_date"]
    if start_date and hasattr(start_date, "date"):
        start_date = start_date.date()
        if end_date < start_date:
            from app.utils.exceptions import ParamErrorException
            raise ParamErrorException(message="结束日期不得早于起始日期")
    
    # 重新计算对账金额：筛选日期符合条件的所有采购信息
    purchase_list = purchase_info_repo.list_by_statement(
        supplier_id=statement["supplier_id"],
        statement_id=data.statement_id,
        start_date=start_date,
        end_date=end_date
    )
    
    # 计算总金额
    total_amount = 0.0
    for purchase in purchase_list:
        total_amount += float(purchase["purchase_total_price"])
    
    # 更新对账单结束日期和金额
    statement_repo.update_amount(
        statement_id=data.statement_id,
        statement_amount=total_amount,
        unreceived_amount=total_amount - float(statement["received_amount"]),
        pay_status=(total_amount - float(statement["received_amount"])) <= 0
    )
    
    # 更新对账单结束日期
    statement_repo.update_end_date(data.statement_id, end_date)
    
    # 自动创建新的对账单
    new_start_date = end_date + timedelta(days=1) if end_date else None
    new_statement_data = {
        "supplier_id": statement["supplier_id"],
        "start_date": new_start_date,
        "end_date": None,
        "statement_amount": 0.00,
        "received_amount": 0.00,
        "unreceived_amount": 0.00,
        "pay_status": False,
        "invoice_status": False
    }
    
    # 创建新对账单并获取其ID
    new_statement_id = statement_repo.create(new_statement_data)
    
    # 将采购日期大于对账单结束日期的记录转移到新对账单
    if end_date:
        # 获取所有属于当前对账单但采购日期大于结束日期的记录
        purchase_info_repo = PurchaseInfoRepository(db)
        # 首先获取这些记录
        future_purchases = purchase_info_repo.list_by_statement(
            supplier_id=statement["supplier_id"],
            statement_id=data.statement_id,
            start_date=end_date + timedelta(days=1)
        )
        
        # 计算这些记录的总金额
        future_total_amount = 0.0
        for purchase in future_purchases:
            future_total_amount += float(purchase["purchase_total_price"])
        
        # 如果有未来的采购记录
        if future_purchases:
            # 更新这些记录的statement_id
            purchase_info_repo.update_statement_id_for_purchases(
                statement_id=data.statement_id,
                new_statement_id=new_statement_id,
                start_date=end_date + timedelta(days=1)
            )
            
            # 更新新对账单的金额
            statement_repo.update_amount(
                statement_id=new_statement_id,
                statement_amount=future_total_amount,
                unreceived_amount=future_total_amount,
                pay_status=False
            )
            
            # 重新计算旧对账单的金额：只包含指定日期范围内的采购金额
            # 因为future_purchases的记录已经被转移到新对账单，所以不需要从total_amount中扣除
            # 直接使用total_amount作为旧对账单的最终金额
            statement_repo.update_amount(
                statement_id=data.statement_id,
                statement_amount=total_amount,
                unreceived_amount=total_amount - float(statement["received_amount"]),
                pay_status=(total_amount - float(statement["received_amount"])) <= 0
            )
    
    db.commit()
    
    return ResponseModel(message="对账单确认成功")

@router.delete("/statement/delete", response_model=ResponseModel[None])
async def delete_purchase_statement(statement_id: int = Query(...)):
    """
    删除采购对账单
    """
    from app.repositories.purchase_statement_repo import PurchaseStatementRepository
    from app.database import get_db
    
    db = next(get_db())
    statement_repo = PurchaseStatementRepository(db)
    
    # 获取对账单信息
    statement = statement_repo.get_by_id(statement_id)
    if not statement:
        from app.utils.exceptions import NotFoundException
        raise NotFoundException(message="对账单不存在")
    
    # 软删除对账单
    statement_repo.soft_delete(statement_id)
    db.commit()
    
    return ResponseModel(message="对账单删除成功")


@router.post("/statement/unconfirm", response_model=ResponseModel[None])
async def unconfirm_purchase_statement(statement_id: int = Query(...)):
    """
    取消采购对账单确认
    """
    from app.repositories.purchase_statement_repo import PurchaseStatementRepository
    from app.repositories.purchase_info_repo import PurchaseInfoRepository
    from app.database import get_db
    from datetime import datetime, timedelta
    
    db = next(get_db())
    statement_repo = PurchaseStatementRepository(db)
    purchase_info_repo = PurchaseInfoRepository(db)
    
    # 获取对账单信息
    statement = statement_repo.get_by_id(statement_id)
    if not statement:
        from app.utils.exceptions import NotFoundException
        raise NotFoundException(message="对账单不存在")
    
    # 检查对账单是否已确认
    if not statement["end_date"]:
        from app.utils.exceptions import ParamErrorException
        raise ParamErrorException(message="对账单尚未确认，无需取消")
    
    # 获取供应商ID
    supplier_id = statement["supplier_id"]
    
    # 查找该供应商当前活跃的对账单（如果有）
    active_statement = statement_repo.get_by_supplier(supplier_id)
    
    # 如果存在活跃对账单，验证日期是否相接
    if active_statement:
        # 验证：要撤销的对账单的结束日期 + 1天 = 活跃对账单的开始日期
        expected_start_date = statement["end_date"] + timedelta(days=1)
        if active_statement["start_date"] != expected_start_date:
            from app.utils.exceptions import ParamErrorException
            raise ParamErrorException(
                message=f"只能撤销与活跃对账单相接的对账单。要撤销的对账单结束日期为 {statement['end_date']}，活跃对账单开始日期为 {active_statement['start_date']}，要求活跃对账单开始日期应为 {expected_start_date}"
            )
    
    # 将结束日期设为null
    statement_repo.update_end_date(statement_id, None)
    
    # 如果存在活跃对账单，将其采购记录重定向到要撤销的对账单
    if active_statement:
        # 获取活跃对账单的采购记录
        active_purchase_list = purchase_info_repo.list_by_statement(
            supplier_id=supplier_id,
            statement_id=active_statement["id"]
        )
        
        # 将活跃对账单的采购记录的 statement_id 改为要撤销的对账单的 statement_id
        for purchase in active_purchase_list:
            purchase_info_repo.update(purchase["id"], {"statement_id": statement_id})
    
    # 重新计算对账单金额（包含所有采购记录）
    purchase_list = purchase_info_repo.list_by_statement(
        supplier_id=supplier_id,
        statement_id=statement_id
    )
    
    # 计算总金额
    total_amount = 0.0
    for purchase in purchase_list:
        total_amount += float(purchase["purchase_total_price"])
    
    # 更新对账单金额
    statement_repo.update_amount(
        statement_id=statement_id,
        statement_amount=total_amount,
        unreceived_amount=total_amount - float(statement["received_amount"]),
        pay_status=(total_amount - float(statement["received_amount"])) <= 0
    )
    
    # 如果存在活跃对账单，删除它
    if active_statement:
        statement_repo.soft_delete(active_statement["id"])
    
    db.commit()
    
    return ResponseModel(message="对账单取消确认成功")