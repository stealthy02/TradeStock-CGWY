from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from typing import Optional, List
from decimal import Decimal
from urllib.parse import quote
from app.schemas.common import ResponseModel, PageModel
from app.schemas.sale import SaleAdd, SaleUpdate, SaleReceipt, SaleInvoiceStatusUpdate, SaleStatementConfirm
from app.services import sale_service

router = APIRouter()

# ==================== 销售信息录入 ====================

@router.post("/info/add", response_model=ResponseModel[dict])
async def add_sale(data: SaleAdd):
    """
    4.1.1 新增销售信息
    """
    result = await sale_service.add_sale(data)
    return ResponseModel(data=result)

@router.get("/info/list", response_model=ResponseModel[PageModel[dict]])
async def list_sale_info(
    id: Optional[int] = Query(None),
    purchaser_name: Optional[str] = Query(None),
    product_name: Optional[str] = Query(None),
    sort_field: Optional[str] = Query(None),
    sort_order: Optional[str] = Query(None),
    page_num: int = Query(1),
    page_size: int = Query(10)
):
    """
    4.1.2 查询销售信息列表
    """
    result = await sale_service.list_sale_info(
        id, purchaser_name, product_name,
        sort_field, sort_order, page_num, page_size
    )
    return ResponseModel(data=result)

@router.put("/info/update", response_model=ResponseModel[None])
async def update_sale(data: SaleUpdate):
    """
    4.1.3 修改销售信息
    """
    await sale_service.update_sale(data)
    return ResponseModel(message="修改销售信息成功")

@router.delete("/info/delete", response_model=ResponseModel[None])
async def delete_sale(id: int = Query(...)):
    """
    4.1.4 删除销售信息
    """
    await sale_service.delete_sale(id)
    return ResponseModel(message="删除销售信息成功")

@router.get("/info/product_select", response_model=ResponseModel[List[str]])
async def select_sale_products(keyword: Optional[str] = Query(None), limit: int = Query(5, ge=1, le=50)):
    """
    4.1.5 销售商品下拉联想（仅显示有库存商品）
    """
    result = await sale_service.select_sale_products(keyword, limit=limit)
    return ResponseModel(data=result)

@router.get("/info/last_record", response_model=ResponseModel[Optional[dict]])
async def get_last_sale_record(
    purchaser_name: str = Query(...),
    product_name: str = Query(...)
):
    """
    4.1.6 获取上一次销售记录
    """
    result = await sale_service.get_last_sale_record(purchaser_name, product_name)
    return ResponseModel(data=result)

# ==================== 销售对账单 ====================

@router.get("/bill/list", response_model=ResponseModel[PageModel[dict]])
async def list_sale_bills(
    purchaser_name: Optional[str] = Query(None),
    receive_status: Optional[int] = Query(None, pattern=r"^(\d+|)$"),
    invoice_status: Optional[int] = Query(None, pattern=r"^(\d+|)$"),
    min_amount: Optional[float] = Query(None),
    max_amount: Optional[float] = Query(None),
    page_num: int = Query(1),
    page_size: int = Query(10)
):
    """
    4.2.1 查询销售对账单列表
    """
    result = await sale_service.list_sale_bills(
        purchaser_name, receive_status, invoice_status, min_amount, max_amount, page_num, page_size
    )
    return ResponseModel(data=result)

@router.get("/bill/detail", response_model=ResponseModel[dict])
async def get_sale_bill_detail(bill_id: int = Query(...), end_date: Optional[str] = Query(None)):
    """
    4.2.2 查看销售对账单细则
    """
    result = await sale_service.get_sale_bill_detail(bill_id, end_date)
    return ResponseModel(data=result)


@router.get("/bill/export")
async def export_sale_bill(bill_id: int = Query(...), end_date: Optional[str] = Query(None)):
    """
    导出销售对账单
    """
    result = await sale_service.export_sale_bill(bill_id, end_date)
    
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



@router.post("/bill/receive", response_model=ResponseModel[dict])
async def add_sale_receipt(data: SaleReceipt):
    """
    4.2.3 录入销售收款记录
    """
    result = await sale_service.add_sale_receipt(data)
    return ResponseModel(data=result)



@router.put("/bill/update_invoice_status", response_model=ResponseModel[None])
async def update_sale_invoice_status(data: SaleInvoiceStatusUpdate):
    """
    4.2.4 修改销售对账单开票状态
    """
    await sale_service.update_sale_invoice_status(data.bill_id, data.invoice_status)
    return ResponseModel(message="开票状态修改成功")


@router.delete("/bill/receive/delete", response_model=ResponseModel[dict])
async def delete_sale_receipt(receive_id: int = Query(...)):
    """
    删除收款记录
    """
    result = await sale_service.delete_sale_receipt(receive_id)
    return ResponseModel(data=result, message="删除收款记录成功，已同步更新对账单")

# ==================== 销售对账单管理 ====================



@router.post("/statement/confirm", response_model=ResponseModel[None])
async def confirm_sale_statement(data: SaleStatementConfirm):
    """
    确认销售对账单
    """
    from app.repositories.sale_statement_repo import SaleStatementRepository
    from app.repositories.sale_info_repo import SaleInfoRepository
    from app.database import get_db
    from datetime import datetime, timedelta
    
    db = next(get_db())
    statement_repo = SaleStatementRepository(db)
    sale_info_repo = SaleInfoRepository(db)
    
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
    
    # 重新计算对账金额：筛选日期符合条件的所有销售信息
    sale_list = sale_info_repo.list_by_statement(
        purchaser_id=statement["purchaser_id"],
        statement_id=data.statement_id,
        start_date=start_date,
        end_date=end_date
    )
    
    # 计算总金额、总成本和总利润
    total_amount = 0.0
    total_cost = 0.0
    total_profit = 0.0
    for sale in sale_list:
        total_amount += float(sale["sale_total_price"])
        total_cost += float(sale["trade_unit_cost"]) * float(sale["sale_num"])
        total_profit += float(sale["total_profit"])
    
    # 转换为 Decimal 类型
    total_amount_decimal = Decimal(str(total_amount))
    total_cost_decimal = Decimal(str(total_cost))
    total_profit_decimal = Decimal(str(total_profit))
    received_amount_decimal = Decimal(str(statement["received_amount"]))
    unreceived_amount_decimal = total_amount_decimal - received_amount_decimal
    
    # 更新对账单结束日期和金额
    statement_repo.update_amount_and_profit(
        statement_id=data.statement_id,
        statement_amount=total_amount_decimal,
        total_profit=total_profit_decimal,
        total_cost=total_cost_decimal,
        unreceived_amount=unreceived_amount_decimal,
        receive_status=(unreceived_amount_decimal <= 0)
    )
    
    # 更新对账单结束日期
    statement_repo.update_end_date(data.statement_id, end_date)
    
    # 自动创建新的对账单
    new_start_date = end_date + timedelta(days=1) if end_date else None
    new_statement_data = {
        "purchaser_id": statement["purchaser_id"],
        "start_date": new_start_date,
        "end_date": None,
        "statement_amount": Decimal("0.00"),
        "total_cost": Decimal("0.00"),
        "total_profit": Decimal("0.00"),
        "received_amount": Decimal("0.00"),
        "unreceived_amount": Decimal("0.00"),
        "receive_status": False,
        "invoice_status": False
    }
    
    # 创建新对账单并获取其ID
    new_statement_id = statement_repo.create(new_statement_data)
    
    # 将销售日期大于对账单结束日期的记录转移到新对账单
    if end_date:
        # 获取所有属于当前对账单但销售日期大于结束日期的记录
        sale_info_repo = SaleInfoRepository(db)
        # 注意：这里需要在SaleInfoRepository中添加一个方法来更新记录的statement_id
        # 同时，我们需要更新新对账单的金额
        # 首先获取这些记录
        future_sales = sale_info_repo.list_by_statement(
            purchaser_id=statement["purchaser_id"],
            statement_id=data.statement_id,
            start_date=end_date + timedelta(days=1)
        )
        
        # 计算这些记录的总金额、总成本和总利润
        future_total_amount = 0.0
        future_total_cost = 0.0
        future_total_profit = 0.0
        for sale in future_sales:
            future_total_amount += float(sale["sale_total_price"])
            future_total_cost += float(sale["trade_unit_cost"]) * float(sale["sale_num"])
            future_total_profit += float(sale["total_profit"])
        
        # 如果有未来的销售记录
        if future_sales:
            # 转换为 Decimal 类型
            future_total_amount_decimal = Decimal(str(future_total_amount))
            future_total_cost_decimal = Decimal(str(future_total_cost))
            future_total_profit_decimal = Decimal(str(future_total_profit))
            
            # 更新这些记录的statement_id
            sale_info_repo.update_statement_id_for_sales(
                statement_id=data.statement_id,
                new_statement_id=new_statement_id,
                start_date=end_date + timedelta(days=1)
            )
            
            # 更新新对账单的金额
            statement_repo.update_amount_and_profit(
                statement_id=new_statement_id,
                statement_amount=future_total_amount_decimal,
                total_profit=future_total_profit_decimal,
                total_cost=future_total_cost_decimal,
                unreceived_amount=future_total_amount_decimal,
                receive_status=False
            )
            
            # 重新计算旧对账单的金额：只包含指定日期范围内的销售金额
            # 因为future_sales的记录已经被转移到新对账单，所以不需要从total_amount中扣除
            # 直接使用total_amount作为旧对账单的最终金额
            statement_repo.update_amount_and_profit(
                statement_id=data.statement_id,
                statement_amount=total_amount_decimal,
                total_profit=total_profit_decimal,
                total_cost=total_cost_decimal,
                unreceived_amount=unreceived_amount_decimal,
                receive_status=(unreceived_amount_decimal <= 0)
            )
    
    db.commit()
    
    return ResponseModel(message="对账单确认成功")

@router.delete("/statement/delete", response_model=ResponseModel[None])
async def delete_sale_statement(statement_id: int = Query(...)):
    """
    删除销售对账单
    """
    from app.repositories.sale_statement_repo import SaleStatementRepository
    from app.database import get_db
    
    db = next(get_db())
    statement_repo = SaleStatementRepository(db)
    
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
async def unconfirm_sale_statement(statement_id: int = Query(...)):
    """
    取消销售对账单确认
    """
    from app.repositories.sale_statement_repo import SaleStatementRepository
    from app.repositories.sale_info_repo import SaleInfoRepository
    from app.database import get_db
    from datetime import datetime, timedelta
    
    db = next(get_db())
    statement_repo = SaleStatementRepository(db)
    sale_info_repo = SaleInfoRepository(db)
    
    # 获取对账单信息
    statement = statement_repo.get_by_id(statement_id)
    if not statement:
        from app.utils.exceptions import NotFoundException
        raise NotFoundException(message="对账单不存在")
    
    # 检查对账单是否已确认
    if not statement["end_date"]:
        from app.utils.exceptions import ParamErrorException
        raise ParamErrorException(message="对账单尚未确认，无需取消")
    
    # 获取采购商ID
    purchaser_id = statement["purchaser_id"]
    
    # 查找该采购商当前活跃的对账单（如果有）
    active_statement = statement_repo.get_by_purchaser(purchaser_id)
    
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
    
    # 如果存在活跃对账单，将其销售记录重定向到要撤销的对账单
    if active_statement:
        # 获取活跃对账单的销售记录
        active_sale_list = sale_info_repo.list_by_statement(
            purchaser_id=purchaser_id,
            statement_id=active_statement["id"]
        )
        
        # 将活跃对账单的销售记录的 statement_id 改为要撤销的对账单的 statement_id
        for sale in active_sale_list:
            sale_info_repo.update(sale["id"], {"statement_id": statement_id})
    
    # 重新计算对账单金额（包含所有销售记录）
    sale_list = sale_info_repo.list_by_statement(
        purchaser_id=purchaser_id,
        statement_id=statement_id
    )
    
    # 计算总金额、总成本和总利润
    total_amount = 0.0
    total_cost = 0.0
    total_profit = 0.0
    for sale in sale_list:
        total_amount += float(sale["sale_total_price"])
        total_cost += float(sale["trade_unit_cost"]) * float(sale["sale_num"])
        total_profit += float(sale["total_profit"])
    
    # 更新对账单金额
    statement_repo.update_amount_and_profit(
        statement_id=statement_id,
        statement_amount=total_amount,
        total_profit=total_profit,
        total_cost=total_cost,
        unreceived_amount=total_amount - float(statement["received_amount"]),
        receive_status=(total_amount - float(statement["received_amount"])) <= 0
    )
    
    # 如果存在活跃对账单，删除它
    if active_statement:
        statement_repo.soft_delete(active_statement["id"])
    
    db.commit()
    
    return ResponseModel(message="对账单取消确认成功")