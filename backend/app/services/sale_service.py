from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal

from app.repositories.sale_info_repo import SaleInfoRepository
from app.repositories.sale_statement_repo import SaleStatementRepository
from app.repositories.sale_receipt_repo import SaleReceiptRepository
from app.repositories.goods_repo import GoodsRepository
from app.repositories.purchaser_repo import PurchaserRepository
from app.repositories.goods_customer_name_repo import GoodsCustomerNameRepository
from app.repositories.inventory_flow_repo import InventoryFlowRepository
from app.database import get_db

from app.utils.exceptions import CustomAPIException, NotFoundException, ParamErrorException


# ==================== 销售信息录入 ====================
async def add_sale(data) -> Dict[str, Any]:
    """
    4.1.1 新增销售信息
    - 校验库存充足（601错误）
    - 快照当前库存成本
    - 计算利润（单价-成本）*数量
    - 扣减库存
    - 生成库存流动记录（出库）
    - 自动生成/更新销售对账单
    - 保存客户侧商品名（如果提供）
    """
    # 每次请求独立获取DB会话，保证线程安全
    db = next(get_db())
    repo = _get_repositories(db)

    purchaser_name = data.purchaser_name
    product_name = data.product_name
    product_spec = data.product_spec
    customer_product_name = data.customer_product_name if hasattr(data, "customer_product_name") and data.customer_product_name else product_name
    sale_num = data.sale_num
    sale_price = data.sale_price
    unit_price = sale_price
    if unit_price <= 0:
        raise ParamErrorException(message="销售单价必须大于0")
    if sale_num <= 0:
        raise ParamErrorException(message="销售数量必须大于0")
    # 增加日期格式校验，避免框架500报错
    try:
        sale_date = datetime.strptime(data.sale_date, "%Y-%m-%d")
    except ValueError:
        raise ParamErrorException(message="销售日期格式错误，要求%Y-%m-%d")
    # 直接使用整数类型的规格值
    spec_value = float(product_spec)
    total_price = unit_price * spec_value * sale_num

    # 1. 校验采购商存在 → 抛出404统一异常
    purchaser = repo.purchaser.get_by_name(purchaser_name)
    if not purchaser or purchaser.get("is_deleted"):
        raise NotFoundException(message="采购商不存在")
    purchaser_id = purchaser["id"]

    # 2. 查询商品（按名称和规格组合）→ 抛出404统一异常
    goods = repo.goods.get_by_name_and_spec(product_name, product_spec)
    if not goods or goods.get("is_deleted"):
        raise NotFoundException(message="商品不存在")

    goods_id = goods["id"]
    current_stock = int(goods["current_stock_num"])
    unit_cost = float(goods["stock_unit_cost"])  # 快照成本

    # 3. 库存校验（自定义业务码601）
    if sale_num > current_stock:
        raise CustomAPIException(code=601, message="库存不足：销售数量超过当前商品库存，禁止提交销售信息")

    # 4. 检查销售日期是否在当前对账单开始日期之前
    # 获取该采购商当前未结束的对账单（end_date为null）
    from app.repositories.sale_statement_repo import SaleStatementRepository
    statement_repo = SaleStatementRepository(db)
    current_statement = statement_repo.get_by_purchaser(purchaser_id)
    if current_statement:
        start_date = current_statement.get("start_date")
        if start_date:
            # 确保日期类型一致
            if hasattr(start_date, "date"):
                start_date_to_check = start_date.date()
            else:
                start_date_to_check = start_date
            if hasattr(sale_date, "date"):
                sale_date_to_check = sale_date.date()
            else:
                sale_date_to_check = sale_date
            # 如果销售日期小于等于对账单开始日期，禁止添加
            if sale_date_to_check <= start_date_to_check:
                raise CustomAPIException(code=603, message="销售日期早于当前对账单开始日期，禁止添加新记录")

    # 5. 计算利润（快照）
    unit_profit = unit_price - unit_cost
    total_profit = unit_profit * sale_num * spec_value

    # 10. 自动生成/更新销售对账单（含利润聚合）
    await _ensure_sale_statement(db, purchaser_id, total_price, total_profit, sale_num * unit_cost)

    # 6. 插入销售记录
    # 获取最新的对账单ID
    sale_statement_repo = SaleStatementRepository(db)
    latest_statement = sale_statement_repo.get_by_purchaser(purchaser_id)
    if not latest_statement:
        raise ParamErrorException(message="无法获取对账单，请联系管理员")
    
    sale_data = {
        "purchaser_id": purchaser_id,
        "goods_id": goods_id,
        "product_spec": product_spec,
        "sale_num": sale_num,
        "sale_unit_price": unit_price,
        "sale_total_price": total_price,
        "trade_unit_cost": unit_cost,
        "unit_profit": unit_profit,
        "total_profit": total_profit,
        "sale_date": sale_date,
        "statement_id": latest_statement["id"],
        "remark": data.remark if hasattr(data, "remark") else None
    }
    sale_id = repo.sale_info.create(sale_data)

    # 7. 保存客户侧商品名（如果提供）
    if customer_product_name:
        repo.goods_customer_name.save_or_update(
            goods_id=goods_id,
            purchaser_id=purchaser_id,
            customer_name=customer_product_name
        )

    # 8. 扣减库存
    new_stock = current_stock - sale_num
    new_value = unit_cost * new_stock * spec_value
    repo.goods.update_stock_and_cost(
        goods_id=goods_id,
        new_stock=new_stock,
        new_cost=unit_cost,
        new_value=new_value
    )

    # 库存流动数据变动更改处
    # 9. 生成库存流动记录（oper_type=2 销售出库）
    repo.inventory_flow.create({
        "goods_id": goods_id,
        "oper_type": 2,
        "biz_id": sale_id,
        "change_num": -sale_num,
        "stock_before": current_stock,
        "stock_after": new_stock,
        "oper_time": sale_date,
        "oper_source": f"销售-{purchaser_name}"
    })

    db.commit()

    return {
        "id": sale_id,
        "total_price": total_price,
        "unit_profit": round(unit_profit, 2),
        "total_profit": round(total_profit, 2)
    }


async def list_sale_info(
    id: Optional[int],
    purchaser_name: Optional[str],
    product_name: Optional[str],
    sort_field: Optional[str],
    sort_order: Optional[str],
    page_num: int,
    page_size: int
) -> Dict[str, Any]:
    """
    4.1.2 查询销售信息列表
    - 多条件筛选
    - 返回客户侧商品名（如果有）
    - 返回利润快照字段
    """
    db = next(get_db())
    repo = _get_repositories(db)

    # 解析采购商ID
    purchaser_id = None
    if purchaser_name:
        purchaser = repo.purchaser.get_by_name(purchaser_name)
        if purchaser:
            purchaser_id = purchaser["id"]

    # 排序映射
    sort_mapping = {
        "sale_date": "sale_date",
        "sale_num": "sale_num",
        "sale_price": "sale_unit_price",
        "total_profit": "total_profit"
    }
    db_sort_field = sort_mapping.get(sort_field, "sale_date")
    db_sort_order = sort_order if sort_order in ["asc", "desc"] else "desc"

    # 统计总数
    total = repo.sale_info.count_by_conditions(
        id=id,
        purchaser_id=purchaser_id,
        product_name=product_name
    )
    pages = (total + page_size - 1) // page_size if total > 0 else 0

    # 查询列表
    list_data = repo.sale_info.list_by_conditions(
        id=id,
        purchaser_id=purchaser_id,
        product_name=product_name,
        sort_field=db_sort_field,
        sort_order=db_sort_order,
        offset=(page_num - 1) * page_size,
        limit=page_size
    )

    formatted_list = []
    for item in list_data:
        # 查询客户侧商品名
        customer_name = repo.goods_customer_name.get_customer_name(
            goods_id=item["goods_id"],
            purchaser_id=item["purchaser_id"]
        )
        formatted_list.append({
            "id": item["id"],
            "purchaser_id": item["purchaser_id"],
            "purchaser_name": item["purchaser_name"],
            "product_name": item["goods_name"],
            "product_spec": item["product_spec"],
            "customer_product_name": customer_name,
            "sale_num": int(item["sale_num"]),
            "sale_price": float(item["sale_unit_price"]),
            "total_price": float(item["sale_total_price"]),
            "unit_profit": float(item["unit_profit"]),
            "total_profit": float(item["total_profit"]),
            "sale_date": item["sale_date"].strftime("%Y-%m-%d"),
            "remark": item["remark"],
            "create_time": item["create_time"].strftime("%Y-%m-%d %H:%M:%S")
        })

    return {
        "total": total,
        "pages": pages,
        "list": formatted_list
    }


async def update_sale(data) -> None:
    """
    4.1.3 修改销售信息
    - 恢复旧库存
    - 更新记录（重新计算利润快照）
    - 扣减新库存
    - 更新对账单（先减后加）
    """
    db = next(get_db())
    repo = _get_repositories(db)
    sale_id = data.id

    # 1. 查询原记录 → 抛出404统一异常
    old = repo.sale_info.get_by_id(sale_id)
    if not old or old.get("is_deleted"):
        raise NotFoundException(message="销售记录不存在")

    old_goods_id = old["goods_id"]
    old_num = int(old["sale_num"])
    old_price = float(old["sale_unit_price"])
    old_spec = old.get("product_spec", 1)
    # 直接使用整数类型的规格值
    old_spec_value = float(old_spec)
    old_total = float(old["sale_total_price"])
    old_profit = float(old["total_profit"])
    old_cost = float(old["trade_unit_cost"]) * old_num  # 总成本
    old_purchaser_id = old["purchaser_id"]

    # 2. 恢复旧库存（加回数量）
    goods = repo.goods.get_by_id(old_goods_id)
    restored_stock = int(goods["current_stock_num"]) + old_num
    unit_cost = float(goods["stock_unit_cost"])
    restored_value = unit_cost * restored_stock * old_spec_value
    repo.goods.update_stock_and_cost(
        goods_id=old_goods_id,
        new_stock=restored_stock,
        new_cost=unit_cost,
        new_value=restored_value
    )

    # 3. 更新对账单（扣除旧数据）
    await _adjust_sale_statement(db, old_purchaser_id, -old_total, -old_profit, -old_cost)

    # 4. 准备新数据
    if hasattr(data, "purchaser_name"):
        # 校验采购商存在
        purchaser = repo.purchaser.get_by_name(data.purchaser_name)
        if not purchaser or purchaser.get("is_deleted"):
            raise NotFoundException(message="采购商不存在")
        new_purchaser_id = purchaser["id"]
    else:
        new_purchaser_id = old_purchaser_id
    new_num = data.sale_num
    new_price = data.sale_price
    new_product_spec = data.product_spec if hasattr(data, "product_spec") else old_spec
    # 直接使用整数类型的规格值
    new_spec_value = float(new_product_spec)
    new_total = new_price * new_spec_value * new_num
    # 增加日期格式校验
    try:
        new_date = datetime.strptime(data.sale_date, "%Y-%m-%d")
    except ValueError:
        raise ParamErrorException(message="销售日期格式错误，要求%Y-%m-%d")

    # 检查商品是否变更
    new_goods_id = old_goods_id
    new_current_stock = restored_stock
    new_unit_cost = unit_cost
    if hasattr(data, "product_name") and data.product_name:
        new_goods = repo.goods.get_by_name_and_spec(data.product_name, new_product_spec)
        if not new_goods:
            raise NotFoundException(message="新商品不存在")
        new_goods_id = new_goods["id"]
        new_current_stock = int(new_goods["current_stock_num"])
        new_unit_cost = float(new_goods["stock_unit_cost"])

    # 5. 库存检查（自定义业务码601）
    if new_num > new_current_stock:
        raise CustomAPIException(code=601, message="库存不足：销售数量超过当前商品库存，禁止提交销售信息")

    # 6. 计算新利润快照
    new_unit_profit = new_price - new_unit_cost
    new_total_profit = new_unit_profit * new_num
    new_total_cost = new_unit_cost * new_num

    # 7. 扣减新库存
    final_stock = new_current_stock - new_num
    final_value = new_unit_cost * final_stock * new_spec_value
    repo.goods.update_stock_and_cost(
        goods_id=new_goods_id,
        new_stock=final_stock,
        new_cost=new_unit_cost,
        new_value=final_value
    )

    # 8. 更新销售记录
    update_data = {
        "purchaser_id": new_purchaser_id,
        "goods_id": new_goods_id,
        "product_spec": new_product_spec,
        "sale_num": new_num,
        "sale_unit_price": new_price,
        "sale_total_price": new_total,
        "trade_unit_cost": new_unit_cost,
        "unit_profit": new_unit_profit,
        "total_profit": new_total_profit,
        "sale_date": new_date,
        "remark": data.remark if hasattr(data, "remark") else old["remark"]
    }
    repo.sale_info.update(sale_id, update_data)

    # 库存流动数据变动更改处
    # 9. 更新库存流动记录
    repo.inventory_flow.delete_by_biz(2, sale_id)  # 2=销售
    purchaser_name = data.purchaser_name if hasattr(data, "purchaser_name") else repo.purchaser.get_by_id(new_purchaser_id)["purchaser_name"]
    # 库存流动数据变动更改处
    repo.inventory_flow.create({
        "goods_id": new_goods_id,
        "oper_type": 2,
        "biz_id": sale_id,
        "change_num": -new_num,
        "stock_before": new_current_stock,
        "stock_after": final_stock,
        "oper_time": new_date,
        "oper_source": f"销售-修改-{purchaser_name}"
    })

    # 10. 更新客户侧商品名
    if hasattr(data, "customer_product_name"):
        customer_name = data.customer_product_name if data.customer_product_name else data.product_name
        repo.goods_customer_name.save_or_update(
            goods_id=new_goods_id,
            purchaser_id=new_purchaser_id,
            customer_name=customer_name
        )

    # 11. 更新新对账单
    await _ensure_sale_statement(db, new_purchaser_id, new_total, new_total_profit, new_total_cost)
    db.commit()


async def delete_sale(id: int) -> None:
    """
    4.1.4 删除销售信息（软删除）
    - 恢复库存
    - 扣减对账单金额和利润
    - 软删除记录
    """
    db = next(get_db())
    repo = _get_repositories(db)

    # 查询记录 → 抛出404统一异常
    record = repo.sale_info.get_by_id(id)
    if not record or record.get("is_deleted"):
        raise NotFoundException(message="销售记录不存在")

    goods_id = record["goods_id"]
    num = int(record["sale_num"])
    total = float(record["sale_total_price"])
    profit = float(record["total_profit"])
    cost = float(record["trade_unit_cost"]) * num
    purchaser_id = record["purchaser_id"]
    sale_date = record["sale_date"]

    # 检查销售日期是否在当前对账单开始日期之前
    # 获取该采购商当前未结束的对账单（end_date为null）
    from app.repositories.sale_statement_repo import SaleStatementRepository
    statement_repo = SaleStatementRepository(db)
    current_statement = statement_repo.get_by_purchaser(purchaser_id)
    if current_statement:
        start_date = current_statement.get("start_date")
        if start_date:
            # 确保日期类型一致
            if hasattr(start_date, "date"):
                start_date_to_check = start_date.date()
            else:
                start_date_to_check = start_date
            if hasattr(sale_date, "date"):
                sale_date_to_check = sale_date.date()
            else:
                sale_date_to_check = sale_date
            # 如果销售日期小于等于对账单开始日期，禁止删除
            if sale_date_to_check <= start_date_to_check:
                raise CustomAPIException(code=604, message="该销售记录早于当前对账单开始日期，禁止删除")

    # 恢复库存
    goods = repo.goods.get_by_id(goods_id)
    new_stock = int(goods["current_stock_num"]) + num
    unit_cost = float(goods["stock_unit_cost"])
    repo.goods.update_stock_and_cost(
        goods_id=goods_id,
        new_stock=new_stock,
        new_cost=unit_cost,
        new_value=unit_cost * new_stock
    )

    # 软删除
    repo.sale_info.soft_delete(id)

    # 更新对账单（扣减）
    await _adjust_sale_statement(db, purchaser_id, -total, -profit, -cost)

    # 库存流动数据变动更改处
    # 删除流动记录
    repo.inventory_flow.delete_by_biz(2, id)
    db.commit()


async def select_sale_products(keyword: Optional[str], limit: int = 5) -> List[str]:
    """
    4.1.5 销售商品下拉联想
    - 只显示有库存的商品（current_stock_num > 0）
    - 只返回不重复的商品名称
    """
    db = next(get_db())
    repo = _get_repositories(db)
    return repo.goods.select_by_keyword_with_stock(keyword, limit=limit)


async def get_last_sale_record(purchaser_name: str, product_name: str) -> Optional[Dict[str, Any]]:
    """
    4.1.6 获取上一次销售记录
    - 同时返回客户侧商品名（如果有）
    """
    db = next(get_db())
    repo = _get_repositories(db)

    # 校验采购商存在
    purchaser = repo.purchaser.get_by_name(purchaser_name)
    if not purchaser or purchaser.get("is_deleted"):
        return None
    purchaser_id = purchaser["id"]

    goods = repo.goods.get_by_name(product_name)
    if not goods:
        return None

    last_record = repo.sale_info.get_last_by_purchaser_and_goods(
        purchaser_id=purchaser_id,
        goods_id=goods["id"]
    )
    if not last_record:
        return None

    # 查询客户侧商品名
    customer_name = repo.goods_customer_name.get_customer_name(
        goods_id=goods["id"],
        purchaser_id=purchaser_id
    )

    return {
        "sale_price": float(last_record["sale_unit_price"]),
        "customer_product_name": customer_name,
        "product_spec": last_record["product_spec"]
    }


# ==================== 销售对账单 ====================
async def list_sale_bills(
    purchaser_name: Optional[str],
    receive_status: Optional[int],
    invoice_status: Optional[int],
    min_amount: Optional[float],
    max_amount: Optional[float],
    page_num: int,
    page_size: int
) -> Dict[str, Any]:
    """
    4.2.1 查询销售对账单列表
    - 包含总利润字段（与采购对账单区别）
    - 按采购商自动聚合所有未对账交易
    """
    db = next(get_db())
    repo = _get_repositories(db)

    # 解析采购商ID
    purchaser_id = None
    if purchaser_name:
        purchaser = repo.purchaser.get_by_name(purchaser_name)
        if purchaser:
            purchaser_id = purchaser["id"]

    # 获取有对账单的数据
    # 统计总数
    total = repo.sale_statement.count_by_conditions(
        purchaser_id=purchaser_id,
        receive_status=receive_status,
        invoice_status=invoice_status,
        min_amount=min_amount,
        max_amount=max_amount
    )
    pages = (total + page_size - 1) // page_size if total > 0 else 0

    # 查询列表
    list_data = repo.sale_statement.list_by_conditions(
        purchaser_id=purchaser_id,
        receive_status=receive_status,
        invoice_status=invoice_status,
        min_amount=min_amount,
        max_amount=max_amount,
        offset=(page_num - 1) * page_size,
        limit=page_size
    )

    # 格式化有对账单的数据
    formatted_list = []
    for item in list_data:
        # 格式化日期
        start_date = item.get("start_date")
        end_date = item.get("end_date")
        if start_date and hasattr(start_date, "strftime"):
            start_date = start_date.strftime("%Y-%m-%d")
        if end_date and hasattr(end_date, "strftime"):
            end_date = end_date.strftime("%Y-%m-%d")
        
        formatted_list.append({
            "id": item["id"],
            "purchaser_id": item["purchaser_id"],
            "purchaser_name": item["purchaser_name"],
            "statement_amount": float(item["statement_amount"]),
            "total_cost": float(item["total_cost"]),
            "received_amount": float(item["received_amount"]),
            "unreceived_amount": float(item["unreceived_amount"]),
            "receive_status": 1 if item["receive_status"] else 0,
            "receive_status_text": "已结清" if item["receive_status"] else "未结清",
            "invoice_status": 1 if item["invoice_status"] else 0,
            "invoice_status_text": "已开票" if item["invoice_status"] else "未开票",
            "has_statement": True,
            "start_date": start_date,
            "end_date": end_date
        })

    # 获取无对账单的数据
    unstatemented_summary = repo.sale_info.get_unstatemented_summary_by_purchaser()
    unstatemented_list = []
    for purchaser_id, summary in unstatemented_summary.items():
        # 如果指定了采购商，只返回匹配的
        if purchaser_id and purchaser_id != summary["purchaser_id"]:
            continue
        
        unstatemented_list.append({
            "id": 0,  # 虚假对账单ID为0
            "purchaser_id": summary["purchaser_id"],
            "purchaser_name": summary["purchaser_name"],
            "statement_amount": summary["total_amount"],
            "total_cost": 0.0,  # 简化处理，不计算成本
            "received_amount": 0.0,
            "unreceived_amount": summary["total_amount"],
            "receive_status": 0,
            "receive_status_text": "未结清",
            "invoice_status": 0,
            "invoice_status_text": "未开票",
            "has_statement": False
        })

    # 合并数据
    all_list = formatted_list + unstatemented_list

    return {
        "total": total + len(unstatemented_list),
        "pages": max(pages, 1) if all_list else 0,
        "list": all_list
    }


async def get_sale_bill_detail(bill_id: int, end_date: Optional[str] = None) -> Dict[str, Any]:
    """
    4.2.2 查看销售对账单细则
    - 包含利润信息
    - 包含客户侧商品名
    - 按名称日期合并销售记录
    """
    db = next(get_db())
    repo = _get_repositories(db)

    # 解析结束日期
    parsed_end_date = None
    if end_date:
        try:
            parsed_end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            raise ParamErrorException(message="结束日期格式错误，要求%Y-%m-%d")

    # 处理有对账单的情况
    # 查询对账单 → 抛出404统一异常
    bill = repo.sale_statement.get_by_id(bill_id)
    if not bill:
        raise NotFoundException(message="对账单不存在")

    # 销售明细（含利润）
    sale_list = repo.sale_info.list_by_statement(
        purchaser_id=bill["purchaser_id"],
        statement_id=bill_id,
        start_date=bill["start_date"],
        end_date=parsed_end_date or bill.get("end_date")
    )

    # 按名称和日期合并销售记录
    merged_sales = {}
    total_amount = 0.0
    total_cost = 0.0
    for s in sale_list:
        # 查询客户侧商品名
        customer_name = repo.goods_customer_name.get_customer_name(
            goods_id=s["goods_id"],
            purchaser_id=s["purchaser_id"]
        )
        key = (s["goods_name"], s["sale_date"].strftime("%Y-%m-%d"))
        if key not in merged_sales:
            # 直接使用整数类型的规格值
            spec_value = float(s.get("product_spec", 1))
            sale_num = int(s["sale_num"])
            merged_sales[key] = {
                "product_name": s["goods_name"],
                "customer_product_name": customer_name,
                "sale_date": s["sale_date"].strftime("%Y-%m-%d"),
                "total_num": sale_num,
                "total_kg": sale_num * spec_value,
                "total_price": float(s["sale_total_price"]),
                "product_spec": s.get("product_spec", ""),
                "remark": s["remark"]
            }
            total_amount += float(s["sale_total_price"])
            # 简化处理，不计算成本
            total_cost = 0.0
        else:
            # 直接使用整数类型的规格值
            spec_value = float(s.get("product_spec", 1))
            sale_num = int(s["sale_num"])
            merged_sales[key]["total_num"] += sale_num
            merged_sales[key]["total_kg"] += sale_num * spec_value
            merged_sales[key]["total_price"] += float(s["sale_total_price"])
            total_amount += float(s["sale_total_price"])
            # 简化处理，不计算成本
            total_cost = 0.0
    
    # 计算单价并格式化
    formatted_sales = []
    for key, sale in merged_sales.items():
        # 计算单价：总价格 / 总公斤数
        if sale["total_kg"] > 0:
            unit_price = sale["total_price"] / sale["total_kg"]
        else:
            unit_price = 0.0
        # 添加单价字段
        sale["unit_price"] = unit_price
        formatted_sales.append(sale)

    # 收款记录
    receipt_list = repo.sale_receipt.list_by_statement(bill_id)
    formatted_receipts = [{
        "id": r["id"],
        "receiptDate": r["receipt_date"].strftime("%Y-%m-%d"),
        "receiptAmount": float(r["receipt_amount"]),
        "receiptMethod": r["receipt_method"],
        "remark": r["remark"]
    } for r in receipt_list]

    # 计算已收金额和未收金额
    received_amount = sum(float(r["receipt_amount"]) for r in receipt_list)
    unreceived_amount = total_amount - received_amount
    receive_status = unreceived_amount <= 0

    # 获取起始日期和结束日期
    start_date = bill["start_date"].strftime("%Y-%m-%d") if bill["start_date"] else None
    end_date = None
    if bill.get("end_date"):
        end_date = bill["end_date"].strftime("%Y-%m-%d") if hasattr(bill["end_date"], "strftime") else bill["end_date"]
    
    return {
        "bill_info": {
            "id": bill["id"],
            "purchaser_name": bill["purchaser_name"],
            "statement_amount": total_amount,
            "total_cost": total_cost,
            "received_amount": received_amount,
            "unreceived_amount": unreceived_amount,
            "receive_status_text": "已结清" if receive_status else "未结清",
            "invoice_status_text": "已开票" if bill["invoice_status"] else "未开票",
            "start_date": start_date,
            "end_date": end_date
        },
        "sale_list": {
            "total": len(formatted_sales),
            "pages": 1,
            "list": formatted_sales
        },
        "receipt_list": {
            "total": len(formatted_receipts),
            "pages": 1,
            "list": formatted_receipts
        }
    }


async def add_sale_receipt(data) -> Dict[str, Any]:
    """
    4.2.3 录入销售收款记录
    - 校验金额 <= 未收金额（602）
    """
    db = next(get_db())
    repo = _get_repositories(db)

    bill_id = data.bill_id
    amount = data.receive_amount
    # 增加日期格式校验
    try:
        receive_date = datetime.strptime(data.receive_date, "%Y-%m-%d")
    except ValueError:
        raise ParamErrorException(message="收款日期格式错误，要求%Y-%m-%d")

    # 校验对账单存在 → 抛出404统一异常
    bill = repo.sale_statement.get_by_id(bill_id)
    if not bill:
        raise NotFoundException(message="对账单不存在")

    # 检查对账单是否已确认
    if not bill["end_date"]:
        raise CustomAPIException(code=605, message="对账单尚未确认，禁止输入结款金额")

    unreceived = float(bill["unreceived_amount"])
    # 收款金额校验（自定义业务码602）
    if amount <= 0:
        raise CustomAPIException(code=602, message="收款金额必须大于0")
    if amount > unreceived:
        raise CustomAPIException(code=602, message="收款金额超过未收金额")

    # 新增收款记录
    receipt_id = repo.sale_receipt.create({
        "statement_id": bill_id,
        "receipt_date": receive_date,
        "receipt_amount": amount,
        "receipt_method": data.receive_method,
        "remark": data.remark if hasattr(data, "remark") else None
    })

    # 更新对账单收款状态
    new_received = float(bill["received_amount"]) + amount
    new_unreceived = float(bill["statement_amount"]) - new_received
    new_status = new_unreceived <= 0

    repo.sale_statement.update_receipt(
        statement_id=bill_id,
        received_amount=new_received,
        unreceived_amount=new_unreceived,
        receive_status=new_status
    )
    db.commit()

    return {
        "pay_status": 1 if new_status else 0
    }


async def update_sale_invoice_status(bill_id: int, status: int) -> None:
    """
    4.2.4 修改销售对账单开票状态
    """
    db = next(get_db())
    repo = _get_repositories(db)

    # 状态参数校验 → 抛出400统一异常
    if status not in [0, 1]:
        raise ParamErrorException(message="状态参数错误，仅支持0（未开票）/1（已开票）")

    # 校验对账单存在 → 抛出404统一异常
    bill = repo.sale_statement.get_by_id(bill_id)
    if not bill:
        raise NotFoundException(message="对账单不存在")

    # 检查对账单是否已确认
    if not bill["end_date"]:
        raise CustomAPIException(code=606, message="对账单尚未确认，禁止修改开票状态")

    repo.sale_statement.update_invoice_status(bill_id, bool(status))
    db.commit()


async def delete_sale_receipt(receipt_id: int) -> Dict[str, Any]:
    """
    删除收款记录
    - 软删除收款记录
    - 重新计算对账单的已收金额
    - 更新对账单的收款状态
    """
    db = next(get_db())
    repo = _get_repositories(db)

    # 校验收款记录存在
    receipt = repo.sale_receipt.get_by_id(receipt_id)
    if not receipt:
        raise NotFoundException(message="收款记录不存在")
    
    statement_id = receipt.statement_id
    
    # 软删除收款记录
    deleted = repo.sale_receipt.soft_delete(receipt_id)
    if not deleted:
        raise CustomAPIException(code=500, message="删除收款记录失败")
    
    # 重新计算对账单的已收金额
    new_received = repo.sale_receipt.get_total_received_by_statement(statement_id)
    
    # 获取对账单信息
    statement = repo.sale_statement.get_by_id(statement_id)
    if not statement:
        raise NotFoundException(message="对账单不存在")
    
    # 计算新的未收金额和收款状态
    new_unreceived = float(statement["statement_amount"]) - float(new_received)
    new_status = new_unreceived <= 0
    
    # 更新对账单
    repo.sale_statement.update_receipt(
        statement_id=statement_id,
        received_amount=new_received,
        unreceived_amount=new_unreceived,
        receive_status=new_status
    )

    db.commit()
    
    return {
        "pay_status": 1 if new_status else 0
    }


# ==================== 内部辅助函数 ====================
def _get_repositories(db):
    """仓库实例化辅助函数，避免重复代码，统一管理"""
    class Repos:
        def __init__(self, db_conn):
            self.sale_info = SaleInfoRepository(db_conn)
            self.sale_statement = SaleStatementRepository(db_conn)
            self.sale_receipt = SaleReceiptRepository(db_conn)
            self.goods = GoodsRepository(db_conn)
            self.purchaser = PurchaserRepository(db_conn)
            self.goods_customer_name = GoodsCustomerNameRepository(db_conn)
            self.inventory_flow = InventoryFlowRepository(db_conn)
    return Repos(db)


async def _ensure_sale_statement(db, purchaser_id: int, amount: float, profit: float, cost: float):
    """
    确保销售对账单存在，并累加金额、利润、成本
    """
    from datetime import datetime, timedelta
    sale_statement_repo = SaleStatementRepository(db)
    existing = sale_statement_repo.get_by_purchaser(purchaser_id)
    if existing:
        new_amount = float(existing["statement_amount"]) + amount
        new_profit = float(existing["total_profit"]) + profit
        new_cost = float(existing["total_cost"]) + cost
        new_unreceived = new_amount - float(existing["received_amount"])

        # 转换为 Decimal 类型
        new_amount_decimal = Decimal(str(new_amount))
        new_profit_decimal = Decimal(str(new_profit))
        new_cost_decimal = Decimal(str(new_cost))
        new_unreceived_decimal = Decimal(str(new_unreceived))

        sale_statement_repo.update_amount_and_profit(
            statement_id=existing["id"],
            statement_amount=new_amount_decimal,
            total_profit=new_profit_decimal,
            total_cost=new_cost_decimal,
            unreceived_amount=new_unreceived_decimal,
            receive_status = (new_unreceived_decimal == 0)
        )
    else:
        # 获取上一个已关闭的对账单，计算新对账单的起始日期
        last_statement = sale_statement_repo.get_last_closed_statement(purchaser_id)
        if last_statement and last_statement["end_date"]:
            last_end_date = last_statement["end_date"]
            start_date = last_end_date + timedelta(days=1)
        else:
            # 如果没有历史对账单，使用空值
            start_date = None
        
        # 转换为 Decimal 类型
        amount_decimal = Decimal(str(amount))
        cost_decimal = Decimal(str(cost))
        profit_decimal = Decimal(str(profit))

        sale_statement_repo.create({
            "purchaser_id": purchaser_id,
            "start_date": start_date,
            "end_date": None,
            "statement_amount": amount_decimal,
            "total_cost": cost_decimal,
            "total_profit": profit_decimal,
            "received_amount": Decimal("0.00"),
            "unreceived_amount": amount_decimal,
            "receive_status": False,
            "invoice_status": False
        })


async def _adjust_sale_statement(db, purchaser_id: int, amount: float, profit: float, cost: float):
    """
    调整销售对账单（修改/删除时用）
    amount/profit/cost 可为负数
    """
    sale_statement_repo = SaleStatementRepository(db)
    existing = sale_statement_repo.get_by_purchaser(purchaser_id)
    if not existing:
        return

    # 计算新值并做非负校验
    new_amount = max(0.0, float(existing["statement_amount"]) + amount)
    new_profit = max(0.0, float(existing["total_profit"]) + profit)
    new_cost = max(0.0, float(existing["total_cost"]) + cost)
    new_unreceived = max(0.0, new_amount - float(existing["received_amount"]))
    new_status = new_unreceived <= 0

    # 转换为 Decimal 类型
    new_amount_decimal = Decimal(str(new_amount))
    new_profit_decimal = Decimal(str(new_profit))
    new_cost_decimal = Decimal(str(new_cost))
    new_unreceived_decimal = Decimal(str(new_unreceived))

    sale_statement_repo.update_amount_and_profit(
        statement_id=existing["id"],
        statement_amount=new_amount_decimal,
        total_profit=new_profit_decimal,
        total_cost=new_cost_decimal,
        unreceived_amount=new_unreceived_decimal,
        receive_status=new_status
    )


async def export_sale_bill(bill_id: int, end_date: Optional[str] = None) -> Dict[str, Any]:
    """
    导出销售对账单
    - 获取对账单数据（与bill/detail相同）
    - 转换为xlsx文件流
    """
    from app.utils.export_utils import convert_to_xlsx
    
    # 第一步：获取与bill/detail一样的数据
    data = await get_sale_bill_detail(bill_id, end_date)
    
    # 第二步：将数据传给convert_to_xlsx函数（暂时pass）
    xlsx_bytes = convert_to_xlsx(data, bill_type="sale")
    
    # 第三步：返回xlsx文件数据流
    return {
        "data": data,
        "xlsx_bytes": xlsx_bytes,
        "filename": f"销售对账单_{data['bill_info']['purchaser_name']}_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
    }