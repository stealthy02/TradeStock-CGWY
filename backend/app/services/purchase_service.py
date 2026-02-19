from typing import Optional, Dict, Any, List
from datetime import datetime

from app.repositories.purchase_info_repo import PurchaseInfoRepository
from app.repositories.purchase_statement_repo import PurchaseStatementRepository
from app.repositories.purchase_payment_repo import PurchasePaymentRepository
from app.repositories.goods_repo import GoodsRepository
from app.repositories.supplier_repo import SupplierRepository
from app.repositories.inventory_flow_repo import InventoryFlowRepository
from app.database import get_db
# 导入项目统一自定义异常（和其他服务层路径完全一致）
from app.utils.exceptions import CustomAPIException, NotFoundException, ParamErrorException


# ==================== 采购信息录入 ====================
async def add_purchase(data) -> Dict[str, Any]:
    """
    3.1.1 新增采购信息
    - 自动创建商品（如果不存在）
    - 计算加权平均成本并更新库存
    - 生成库存流动记录（入库）
    - 自动生成/更新采购对账单
    """
    # 使用 SessionLocal 直接创建数据库会话，避免使用生成器在异步函数中的问题
    from app.database import SessionLocal
    db = SessionLocal()
    
    try:
        purchase_repo = PurchaseInfoRepository(db)
        goods_repo = GoodsRepository(db)
        supplier_repo = SupplierRepository(db)
        inventory_flow_repo = InventoryFlowRepository(db)
        statement_repo = PurchaseStatementRepository(db)

        supplier_name = data.supplier_name
        product_name = data.product_name
        product_spec = data.product_spec
        purchase_num = data.purchase_num
        unit_price = data.purchase_price
        if unit_price <= 0:
            raise ParamErrorException(message="采购单价必须大于0")
        if purchase_num <= 0:
            raise ParamErrorException(message="采购数量必须大于0")  
        # 补充采购日期格式校验
        try:
            purchase_date = datetime.strptime(data.purchase_date, "%Y-%m-%d")
        except ValueError:
            raise ParamErrorException(message="采购日期格式错误，要求%Y-%m-%d")
        # 直接使用整数类型的规格值
        spec_value = float(product_spec)
        total_price = unit_price * spec_value * purchase_num
        
        # 校验供货商存在 → 抛出404异常
        supplier = supplier_repo.get_by_name(supplier_name)
        if not supplier or supplier.get("is_deleted"):
            raise NotFoundException(message="供货商不存在")
        supplier_id = supplier["id"]
        
        # 检查采购日期是否在当前对账单开始日期之前
        # 获取该供货商当前未结束的对账单（end_date为null）
        current_statement = statement_repo.get_by_supplier(supplier_id)
        if current_statement:
            start_date = current_statement.get("start_date")
            if start_date:
                # 确保日期类型一致
                if hasattr(start_date, "date"):
                    start_date_to_check = start_date.date()
                else:
                    start_date_to_check = start_date
                if hasattr(purchase_date, "date"):
                    purchase_date_to_check = purchase_date.date()
                else:
                    purchase_date_to_check = purchase_date
                # 如果采购日期小于等于对账单开始日期，禁止添加
                if purchase_date_to_check <= start_date_to_check:
                    raise CustomAPIException(code=603, message="采购日期早于当前对账单开始日期，禁止添加新记录")
        
        # 获取或创建商品（按名称和规格组合）
        goods = goods_repo.get_by_name_and_spec(product_name, product_spec)
        if not goods:
            # 自动创建新商品，初始库存为0
            goods_id = goods_repo.create({
                "goods_name": product_name,
                "product_spec": product_spec,
                "current_stock_num": 0,
                "stock_unit_cost": 0.00,
                "stock_total_value": 0.00
            })
            current_stock = 0
            current_cost = 0.00
        else:
            goods_id = goods["id"]
            current_stock = int(goods["current_stock_num"])
            current_cost = float(goods["stock_unit_cost"])
        
        # 自动生成或更新采购对账单
        await _ensure_purchase_statement(db, statement_repo, supplier_id, total_price)
        
        # 获取最新的对账单ID
        latest_statement = statement_repo.get_by_supplier(supplier_id)
        if not latest_statement:
            raise ParamErrorException(message="无法获取对账单，请联系管理员")
        
        # 插入采购记录
        purchase_data = {
            "supplier_id": supplier_id,
            "goods_id": goods_id,
            "product_spec": product_spec,
            "purchase_num": purchase_num,
            "purchase_unit_price": unit_price,
            "purchase_total_price": total_price,
            "purchase_date": purchase_date,
            "statement_id": latest_statement["id"],
            "remark": data.remark if hasattr(data, "remark") else None
        }
        purchase_id = purchase_repo.create(purchase_data)
        
        # 计算新的加权平均成本（单位成本不包含规格）
        spec_value = float(product_spec)
        old_total_value = current_stock * current_cost * spec_value
        new_stock = current_stock + purchase_num
        new_total_value = old_total_value + total_price
        new_cost = new_total_value / (new_stock * spec_value) if new_stock > 0 else unit_price
        new_total_value = new_cost * new_stock * spec_value
        
        # 更新商品库存
        goods_repo.update_stock_and_cost(
            goods_id=goods_id,
            new_stock=new_stock,
            new_cost=round(new_cost, 2),
            new_value=round(new_total_value, 2)
        )
        
        # 库存流动数据变动更改处
        # 生成库存流动记录（oper_type=1 采购入库）
        inventory_flow_repo.create({
            "goods_id": goods_id,
            "oper_type": 1,
            "biz_id": purchase_id,
            "change_num": purchase_num,
            "stock_before": current_stock,
            "stock_after": new_stock,
            "oper_time": purchase_date,
            "oper_source": f"采购-{supplier_name}"
        })

        db.commit()
        
        return {
            "id": purchase_id,
            "total_price": total_price
        }
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()


async def list_purchase_info(
    id: Optional[int],
    supplier_name: Optional[str],
    product_name: Optional[str],
    sort_field: Optional[str],
    sort_order: Optional[str],
    page_num: int,
    page_size: int
) -> Dict[str, Any]:
    """
    3.1.2 查询采购信息列表
    - 多条件筛选（id、供货商、商品）
    - 支持排序
    - 关联查询供货商名称、商品名称、库存成本
    """
    from app.database import SessionLocal
    db = SessionLocal()
    
    try:
        purchase_repo = PurchaseInfoRepository(db)
        goods_repo = GoodsRepository(db)
        from app.repositories.supplier_repo import SupplierRepository
        supplier_repo = SupplierRepository(db)
    
        # 解析供货商ID
        supplier_id = None
        if supplier_name:
            supplier = supplier_repo.get_by_name(supplier_name)
            if supplier:
                supplier_id = supplier["id"]
        
        # 排序字段映射
        sort_mapping = {
            "purchase_date": "purchase_date",
            "purchase_num": "purchase_num",
            "purchase_price": "purchase_unit_price"
        }
        db_sort_field = sort_mapping.get(sort_field, "purchase_date")
        db_sort_order = sort_order if sort_order in ["asc", "desc"] else "desc"
        
        # 统计总数
        total = purchase_repo.count_by_conditions(
            id=id,
            supplier_id=supplier_id,
            product_name=product_name
        )
        
        pages = (total + page_size - 1) // page_size if total > 0 else 0
        
        # 查询列表
        list_data = purchase_repo.list_by_conditions(
            id=id,
            supplier_id=supplier_id,
            product_name=product_name,
            sort_field=db_sort_field,
            sort_order=db_sort_order,
            offset=(page_num - 1) * page_size,
            limit=page_size
        )
        
        # 格式化（关联查询名称和当前库存成本）
        formatted_list = []
        for item in list_data:
            goods = goods_repo.get_by_id(item["goods_id"])
            formatted_list.append({
                "id": item["id"],
                "supplier_id": item["supplier_id"],
                "supplier_name": item["supplier_name"],
                "product_name": item["goods_name"],
                "product_spec": item["product_spec"],
                "purchase_num": int(item["purchase_num"]),
                "purchase_price": float(item["purchase_unit_price"]),
                "total_price": float(item["purchase_total_price"]),
                "inventory_cost": float(goods["stock_unit_cost"]) if goods else 0.00,
                "purchase_date": item["purchase_date"].strftime("%Y-%m-%d"),
                "remark": item["remark"],
                "create_time": item["create_time"].strftime("%Y-%m-%d %H:%M:%S")
            })
        
        return {
            "total": total,
            "pages": pages,
            "list": formatted_list
        }
    except Exception as e:
        raise
    finally:
        db.close()


async def update_purchase(data) -> None:
    """
    3.1.3 修改采购信息
    - 反向计算恢复旧库存（按旧记录扣减）
    - 更新采购记录
    - 重新计算加权平均成本
    - 更新对账单金额（先减后加）
    """
    from app.database import SessionLocal
    db = SessionLocal()
    
    try:
        purchase_repo = PurchaseInfoRepository(db)
        goods_repo = GoodsRepository(db)
        inventory_flow_repo = InventoryFlowRepository(db)
        statement_repo = PurchaseStatementRepository(db)

        purchase_id = data.id
        # 校验ID非空
        if not purchase_id:
            raise ParamErrorException(message="采购记录ID不能为空")
        
        # 查询原记录 → 抛出404异常
        old_record = purchase_repo.get_by_id(purchase_id)
        if not old_record or old_record.get("is_deleted"):
            raise NotFoundException(message="采购记录不存在")
        
        old_goods_id = old_record["goods_id"]
        old_num = int(old_record["purchase_num"])
        old_price = float(old_record["purchase_unit_price"])
        old_spec = old_record.get("product_spec", 1)
        # 直接使用整数类型的规格值
        old_spec_value = float(old_spec)
        old_total = old_price * old_spec_value * old_num
        old_supplier_id = old_record["supplier_id"]
        old_purchase_date = old_record["purchase_date"]
        
        # 检查原采购记录是否在已确认对账单期间内
        confirmed_statements = statement_repo.get_confirmed_statements(old_supplier_id)
        for stmt in confirmed_statements:
            start_date = stmt.get("start_date")
            end_date = stmt.get("end_date")
            if start_date and end_date:
                # 确保日期类型一致
                if hasattr(start_date, "date"):
                    start_date = start_date.date()
                if hasattr(end_date, "date"):
                    end_date = end_date.date()
                if hasattr(old_purchase_date, "date"):
                    old_purchase_date_to_check = old_purchase_date.date()
                else:
                    old_purchase_date_to_check = old_purchase_date
                if start_date <= old_purchase_date_to_check <= end_date:
                    raise CustomAPIException(code=604, message="该采购记录在已确认对账单期间内，禁止修改")
        
        # 反向恢复库存（先扣减旧采购的数量，恢复旧成本）
        goods = goods_repo.get_by_id(old_goods_id)
        current_stock = int(goods["current_stock_num"])
        current_cost = float(goods["stock_unit_cost"])
        
        restored_stock = current_stock - old_num
        if restored_stock < 0:
            restored_stock = 0
        restored_value = current_cost * restored_stock * old_spec_value
        
        goods_repo.update_stock_and_cost(
            goods_id=old_goods_id,
            new_stock=restored_stock,
            new_cost=current_cost,
            new_value=restored_value
        )
        
        # 更新对账单（扣除旧金额）
        await _adjust_purchase_statement(db, statement_repo, old_supplier_id, -old_total)
        
        # 准备新数据 → 补充新日期格式校验
        from app.repositories.supplier_repo import SupplierRepository
        supplier_repo = SupplierRepository(db)
        if hasattr(data, "supplier_name"):
            # 校验供货商存在
            supplier = supplier_repo.get_by_name(data.supplier_name)
            if not supplier or supplier.get("is_deleted"):
                raise NotFoundException(message="供货商不存在")
            new_supplier_id = supplier["id"]
        else:
            new_supplier_id = old_supplier_id
        new_product_name = data.product_name if hasattr(data, "product_name") else None
        new_product_spec = data.product_spec if hasattr(data, "product_spec") else old_spec
        new_num = data.purchase_num
        new_price = data.purchase_price
        try:
            new_date = datetime.strptime(data.purchase_date, "%Y-%m-%d")
        except ValueError:
            raise ParamErrorException(message="采购日期格式错误，要求%Y-%m-%d")
        
        # 直接使用整数类型的规格值
        new_spec_value = float(new_product_spec)
        
        # 如果商品变了，需要处理
        if new_product_name and new_product_name != goods["goods_name"]:
            # 获取或创建新商品（按名称和规格组合）
            new_goods = goods_repo.get_by_name_and_spec(new_product_name, new_product_spec)
            if not new_goods:
                new_goods_id = goods_repo.create({
                    "goods_name": new_product_name,
                    "product_spec": new_product_spec,
                    "current_stock_num": 0,
                    "stock_unit_cost": 0.00,
                    "stock_total_value": 0.00
                })
                new_current_stock = 0
                new_current_cost = 0.00
            else:
                new_goods_id = new_goods["id"]
                new_current_stock = int(new_goods["current_stock_num"])
                new_current_cost = float(new_goods["stock_unit_cost"])
        else:
            new_goods_id = old_goods_id
            new_current_stock = restored_stock
            new_current_cost = current_cost
        new_total = new_price * new_spec_value * new_num
        # 计算新的加权平均成本（单位成本不包含规格）
        old_value = new_current_stock * new_current_cost * new_spec_value
        final_stock = new_current_stock + new_num
        final_total_value = old_value + new_total
        final_cost = final_total_value / (final_stock * new_spec_value) if final_stock > 0 else new_price
        final_value = final_cost * final_stock * new_spec_value
        
        goods_repo.update_stock_and_cost(
            goods_id=new_goods_id,
            new_stock=final_stock,
            new_cost=round(final_cost, 2),
            new_value=round(final_value, 2)
        )
        
        # 更新采购记录
        update_data = {
            "supplier_id": new_supplier_id,
            "goods_id": new_goods_id,
            "product_spec": new_product_spec,
            "purchase_num": new_num,
            "purchase_unit_price": new_price,
            "purchase_total_price": new_total,
            "purchase_date": new_date,
            "remark": data.remark if hasattr(data, "remark") else old_record["remark"]
        }
        purchase_repo.update(purchase_id, update_data)
        
        # 库存流动数据变动更改处
        # 更新库存流动记录
        inventory_flow_repo.delete_by_biz(1, purchase_id)
        supplier_name = data.supplier_name if hasattr(data, "supplier_name") else supplier_repo.get_by_id(new_supplier_id)["supplier_name"]
        # 库存流动数据变动更改处
        inventory_flow_repo.create({
            "goods_id": new_goods_id,
            "oper_type": 1,
            "biz_id": purchase_id,
            "change_num": new_num,
            "stock_before": new_current_stock,
            "stock_after": final_stock,
            "oper_time": new_date,
            "oper_source": f"采购-修改-{supplier_name}"
        })
        
        # 更新新对账单
        await _ensure_purchase_statement(db, statement_repo, new_supplier_id, new_num * new_price)

        db.commit()
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()


async def delete_purchase(id: int) -> None:
    """
    3.1.4 删除采购信息（软删除）
    - 恢复库存（扣减数量，反向计算成本）
    - 软删除采购记录
    - 更新对账单（扣除金额）
    - 删除或标记库存流动记录
    """
    from app.database import SessionLocal
    db = SessionLocal()
    
    try:
        purchase_repo = PurchaseInfoRepository(db)
        goods_repo = GoodsRepository(db)
        inventory_flow_repo = InventoryFlowRepository(db)
        statement_repo = PurchaseStatementRepository(db)

        # 查询记录 → 抛出404异常
        record = purchase_repo.get_by_id(id)
        if not record or record.get("is_deleted"):
            raise NotFoundException(message="采购记录不存在")
        
        goods_id = record["goods_id"]
        num = int(record["purchase_num"])
        total = float(record["purchase_total_price"])
        supplier_id = record["supplier_id"]
        purchase_date = record["purchase_date"]

        # 检查采购日期是否在当前对账单开始日期之前
        # 获取该供应商当前未结束的对账单（end_date为null）
        current_statement = statement_repo.get_by_supplier(supplier_id)
        if current_statement:
            start_date = current_statement.get("start_date")
            if start_date:
                # 确保日期类型一致
                if hasattr(start_date, "date"):
                    start_date_to_check = start_date.date()
                else:
                    start_date_to_check = start_date
                if hasattr(purchase_date, "date"):
                    purchase_date_to_check = purchase_date.date()
                else:
                    purchase_date_to_check = purchase_date
                # 如果采购日期小于等于对账单开始日期，禁止删除
                if purchase_date_to_check <= start_date_to_check:
                    raise CustomAPIException(code=604, message="该采购记录早于当前对账单开始日期，禁止删除")
        
        # 恢复库存（扣减数量，反向计算加权平均成本）
        goods = goods_repo.get_by_id(goods_id)
        current_stock = int(goods["current_stock_num"])
        current_cost = float(goods["stock_unit_cost"])
        current_value = float(goods["stock_total_value"])
        product_spec = float(record.get("product_spec", 1))
        
        new_stock = current_stock - num
        if new_stock < 0:
            new_stock = 0
        
        # 计算新的加权平均成本（反向操作）
        if new_stock > 0:
            # 计算扣除当前采购后的总价值和单位成本
            new_value = current_value - total
            new_cost = new_value / (new_stock * product_spec) if new_stock > 0 else 0.00
        else:
            # 库存为0时，成本和价值都设为0
            new_value = 0.00
            new_cost = 0.00
        
        goods_repo.update_stock_and_cost(
            goods_id=goods_id,
            new_stock=new_stock,
            new_cost=round(new_cost, 2),
            new_value=round(new_value, 2)
        )
        
        # 软删除采购记录
        purchase_repo.soft_delete(id)
        
        # 更新对账单（扣除金额）
        await _adjust_purchase_statement(db, statement_repo, supplier_id, -total)
        
        # 库存流动数据变动更改处
        # 删除库存流动记录
        inventory_flow_repo.delete_by_biz(1, id)

        db.commit()
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()


async def select_purchase_products(keyword: Optional[str], limit: int = 5) -> List[str]:
    """
    3.1.5 采购商品下拉联想
    - 从商品表联想（所有商品，不限库存）
    - 只返回不重复的商品名称
    """
    from app.database import SessionLocal
    db = SessionLocal()
    
    try:
        goods_repo = GoodsRepository(db)
        return goods_repo.select_by_keyword(keyword, limit=limit)
    except Exception as e:
        raise
    finally:
        db.close()


async def get_last_purchase_record(supplier_name: str, product_name: str) -> Optional[Dict[str, Any]]:
    """
    3.1.6 获取上一次采购记录
    - 查询该供货商该商品的最后一条未删除采购记录
    """
    from app.database import SessionLocal
    db = SessionLocal()
    
    try:
        goods_repo = GoodsRepository(db)
        purchase_repo = PurchaseInfoRepository(db)
        from app.repositories.supplier_repo import SupplierRepository
        supplier_repo = SupplierRepository(db)

        # 校验供货商存在
        supplier = supplier_repo.get_by_name(supplier_name)
        if not supplier or supplier.get("is_deleted"):
            return None
        supplier_id = supplier["id"]

        goods = goods_repo.get_by_name(product_name)
        if not goods:
            return None
        
        last_record = purchase_repo.get_last_by_supplier_and_goods(
            supplier_id=supplier_id,
            goods_id=goods["id"]
        )
        
        if not last_record:
            return None
        
        return {
            "purchase_price": float(last_record["purchase_unit_price"]),
            "product_spec": last_record["product_spec"]
        }
    except Exception as e:
        raise
    finally:
        db.close()


# ==================== 采购对账单 ====================
async def list_purchase_bills(
    supplier_name: Optional[str],
    pay_status: Optional[int],
    invoice_status: Optional[int],
    min_amount: Optional[float],
    max_amount: Optional[float],
    page_num: int,
    page_size: int
) -> Dict[str, Any]:
    """
    3.2.1 查询采购对账单列表
    - 按供货商自动聚合所有未对账交易
    - 支持多条件筛选
    """
    db = next(get_db())
    statement_repo = PurchaseStatementRepository(db)
    purchase_repo = PurchaseInfoRepository(db)
    from app.repositories.supplier_repo import SupplierRepository
    supplier_repo = SupplierRepository(db)

    # 解析供货商ID
    supplier_id = None
    if supplier_name:
        supplier = supplier_repo.get_by_name(supplier_name)
        if supplier:
            supplier_id = supplier["id"]

    # 获取有对账单的数据
    total = statement_repo.count_by_conditions(
        supplier_id=supplier_id,
        pay_status=pay_status,
        invoice_status=invoice_status,
        min_amount=min_amount,
        max_amount=max_amount
    )

    pages = (total + page_size - 1) // page_size if total > 0 else 0

    list_data = statement_repo.list_by_conditions(
        supplier_id=supplier_id,
        pay_status=pay_status,
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
            "supplier_id": item["supplier_id"],
            "supplier_name": item["supplier_name"],
            "bill_amount": float(item["statement_amount"]),
            "received_amount": float(item["received_amount"]),
            "unreceived_amount": float(item["unreceived_amount"]),
            "pay_status": 1 if item["pay_status"] else 0,
            "pay_status_text": "已结清" if item["pay_status"] else "未结清",
            "invoice_status": 1 if item["invoice_status"] else 0,
            "invoice_status_text": "已开票" if item["invoice_status"] else "未开票",
            "has_statement": True,
            "start_date": start_date,
            "end_date": end_date
        })

    # 只返回有对账单的数据
    return {
        "total": total,
        "pages": max(pages, 1) if formatted_list else 0,
        "list": formatted_list
    }


async def get_purchase_bill_detail(bill_id: int,  end_date: Optional[str] = None) -> Dict[str, Any]:
    """
    3.2.2 查看采购对账单细则
    - 对账单基本信息
    - 采购明细列表（按名称日期合并）
    - 付款记录列表
    """
    db = next(get_db())
    statement_repo = PurchaseStatementRepository(db)
    purchase_repo = PurchaseInfoRepository(db)
    payment_repo = PurchasePaymentRepository(db)

    # 处理有对账单的情况
    bill = statement_repo.get_by_id(bill_id)
    if not bill:
        raise NotFoundException(message="对账单不存在")

    # 检查 bill 对象的字段
    if "supplier_id" not in bill:
        raise Exception(f"Bill object missing supplier_id: {bill.keys()}")
    if "start_date" not in bill:
        raise Exception(f"Bill object missing start_date: {bill.keys()}")

    # 如果对账单的 end_date 为空，则使用传入的 end_date
    bill_end_date = bill.get("end_date")
    if not bill_end_date and end_date:
        from datetime import datetime
        bill_end_date = datetime.strptime(end_date, "%Y-%m-%d")

    # 采购明细
    purchase_list = purchase_repo.list_by_statement(
        supplier_id=bill["supplier_id"],
        statement_id=bill_id,
        start_date=bill["start_date"],
        end_date=bill_end_date
    )

    # 按名称和日期合并采购记录
    merged_purchases = {}
    total_amount = 0.0
    for p in purchase_list:
        # 检查可用字段
        if "goods_name" in p:
            product_name = p["goods_name"]
        elif "product_name" in p:
            product_name = p["product_name"]
        else:
            product_name = "未知商品"
        
        key = (product_name, p["purchase_date"].strftime("%Y-%m-%d"))
        if key not in merged_purchases:
            # 直接使用整数类型的规格值
            spec_value = float(p.get("product_spec", 1))
            purchase_num = int(p["purchase_num"])
            merged_purchases[key] = {
                "product_name": product_name,
                "purchase_date": p["purchase_date"].strftime("%Y-%m-%d"),
                "total_num": purchase_num,
                "total_kg": purchase_num * spec_value,
                "total_price": float(p["purchase_total_price"]),
                "product_spec": p.get("product_spec", ""),
                "remark": p["remark"]
            }
            total_amount += float(p["purchase_total_price"])
        else:
            # 直接使用整数类型的规格值
            spec_value = float(p.get("product_spec", 1))
            purchase_num = int(p["purchase_num"])
            merged_purchases[key]["total_num"] += purchase_num
            merged_purchases[key]["total_kg"] += purchase_num * spec_value
            merged_purchases[key]["total_price"] += float(p["purchase_total_price"])
            total_amount += float(p["purchase_total_price"])
    
    # 计算单价并格式化
    formatted_purchases = []
    for key, purchase in merged_purchases.items():
        # 计算单价：总价格 / 总公斤数
        if purchase["total_kg"] > 0:
            unit_price = purchase["total_price"] / purchase["total_kg"]
        else:
            unit_price = 0.0
        # 添加单价字段
        purchase["unit_price"] = unit_price
        formatted_purchases.append(purchase)

    # 付款记录
    payment_list = payment_repo.list_by_statement(bill_id)
    formatted_payments = [{
        "id": p["id"],
        "pay_date": p["payment_date"].strftime("%Y-%m-%d"),
        "pay_amount": float(p["payment_amount"]),
        "pay_method": p["payment_method"],
        "remark": p["remark"]
    } for p in payment_list]

    # 计算已付金额
    received_amount = sum(float(p["payment_amount"]) for p in payment_list)
    unreceived_amount = total_amount - received_amount
    pay_status = unreceived_amount <= 0

    # 获取起始日期和结束日期
    start_date = bill["start_date"].strftime("%Y-%m-%d") if hasattr(bill["start_date"], "strftime") else bill["start_date"]
    end_date = None
    if bill.get("end_date"):
        end_date = bill["end_date"].strftime("%Y-%m-%d") if hasattr(bill["end_date"], "strftime") else bill["end_date"]
    elif end_date:  # 如果对账单没有 end_date，但传入了 end_date
        end_date = end_date
    
    return {
        "bill_info": {
            "id": bill["id"],
            "supplier_name": bill["supplier_name"],
            "start_date": start_date,
            "end_date": end_date,
            "bill_amount": total_amount,
            "received_amount": received_amount,
            "unreceived_amount": unreceived_amount,
            "pay_status": 1 if pay_status else 0,
            "pay_status_text": "已结清" if pay_status else "未结清",
            "invoice_status": bill["invoice_status"],
            "invoice_status_text": "已开票" if bill["invoice_status"] else "未开票"
        },
        "purchase_list": {
            "total": len(formatted_purchases),
            "pages": 1,
            "list": formatted_purchases
        },
        "pay_record_list": {
            "total": len(formatted_payments),
            "pages": 1,
            "list": formatted_payments
        }
    }


async def add_purchase_payment(data) -> Dict[str, Any]:
    """
    3.2.3 录入采购付款记录
    - 校验对账单存在
    - 校验付款金额 <= 未付金额（602自定义错误）
    - 插入付款记录
    - 更新对账单已付/未付金额和状态
    """
    db = next(get_db())
    payment_repo = PurchasePaymentRepository(db)
    statement_repo = PurchaseStatementRepository(db)

    bill_id = data.bill_id
    pay_amount = data.pay_amount
    # 补充付款日期格式校验
    try:
        pay_date = datetime.strptime(data.pay_date, "%Y-%m-%d")
    except ValueError:
        raise ParamErrorException(message="付款日期格式错误，要求%Y-%m-%d")
    
    # 查询对账单 → 抛出404异常
    bill = statement_repo.get_by_id(bill_id)
    if not bill:
        raise NotFoundException(message="对账单不存在")
    
    # 检查对账单是否已确认
    if not bill["end_date"]:
        raise CustomAPIException(code=605, message="对账单尚未确认，禁止输入付款金额")
    
    unreceived = float(bill["unreceived_amount"])
    
    # 校验金额 → 抛出自定义602异常（付款金额错误）
    if pay_amount <= 0:
        raise CustomAPIException(code=602, message="付款金额必须大于0")
    if pay_amount > unreceived:
        raise CustomAPIException(code=602, message="付款金额超过未付金额")
    
    # 插入付款记录
    pay_data = {
        "statement_id": bill_id,
        "payment_date": pay_date,
        "payment_amount": pay_amount,
        "payment_method": data.pay_method,
        "remark": data.remark if hasattr(data, "remark") else None
    }
    payment_id = payment_repo.create(pay_data)
    
    # 更新对账单
    new_received = float(bill["received_amount"]) + pay_amount
    new_unreceived = float(bill["statement_amount"]) - new_received
    new_status = new_unreceived <= 0
    
    statement_repo.update_payment(
        statement_id=bill_id,
        received_amount=new_received,
        unreceived_amount=new_unreceived,
        pay_status=new_status
    )

    db.commit()
    
    return {
        "pay_status": 1 if new_status else 0
    }


async def update_purchase_invoice_status(bill_id: int, status: int) -> None:
    """
    3.2.4 修改采购对账单开票状态
    - 0=未开票，1=已开票
    """
    db = next(get_db())
    statement_repo = PurchaseStatementRepository(db)

    # 校验状态参数 → 抛出400参数错误
    if status not in [0, 1]:
        raise ParamErrorException(message="状态参数错误，仅支持0（未开票）/1（已开票）")
    
    # 校验对账单存在 → 抛出404异常
    bill = statement_repo.get_by_id(bill_id)
    if not bill:
        raise NotFoundException(message="对账单不存在")
    
    # 检查对账单是否已确认
    if not bill["end_date"]:
        raise CustomAPIException(code=606, message="对账单尚未确认，禁止修改开票状态")
    
    statement_repo.update_invoice_status(bill_id, bool(status))
    db.commit()


async def delete_purchase_payment(payment_id: int) -> Dict[str, Any]:
    """
    删除付款记录
    - 软删除付款记录
    - 重新计算对账单的已付金额
    - 更新对账单的付款状态
    """
    db = next(get_db())
    payment_repo = PurchasePaymentRepository(db)
    statement_repo = PurchaseStatementRepository(db)

    # 校验付款记录存在
    payment = payment_repo.get_by_id(payment_id)
    if not payment:
        raise NotFoundException(message="付款记录不存在")
    
    statement_id = payment.statement_id
    
    # 软删除付款记录
    deleted = payment_repo.soft_delete(payment_id)
    if not deleted:
        raise CustomAPIException(code=500, message="删除付款记录失败")
    
    # 重新计算对账单的已付金额
    new_received = payment_repo.get_total_received_by_statement(statement_id)
    
    # 获取对账单信息
    statement = statement_repo.get_by_id(statement_id)
    if not statement:
        raise NotFoundException(message="对账单不存在")
    
    # 计算新的未付金额和付款状态
    new_unreceived = float(statement["statement_amount"]) - float(new_received)
    new_status = new_unreceived <= 0
    
    # 更新对账单
    statement_repo.update_payment(
        statement_id=statement_id,
        received_amount=new_received,
        unreceived_amount=new_unreceived,
        pay_status=new_status
    )

    db.commit()
    
    return {
        "pay_status": 1 if new_status else 0
    }


# ==================== 内部辅助函数 ====================
async def _ensure_purchase_statement(db, statement_repo: PurchaseStatementRepository, supplier_id: int, amount: float):
    """
    确保对账单存在，并累加金额
    - 存在则累加，不存在则新建
    """
    from datetime import datetime, timedelta
    existing = statement_repo.get_by_supplier(supplier_id)
    if existing:
        # 累加金额
        new_amount = float(existing["statement_amount"]) + amount
        new_unreceived = new_amount - float(existing["received_amount"])
        new_status = new_unreceived <= 0
        statement_repo.update_amount(
            statement_id=existing["id"],
            statement_amount=new_amount,
            unreceived_amount=new_unreceived,
            pay_status=new_status
        )
    else:
        # 获取上一个已关闭的对账单，计算新对账单的起始日期
        last_statement = statement_repo.get_last_closed_statement(supplier_id)
        if last_statement and last_statement["end_date"]:
            last_end_date = last_statement["end_date"]
            start_date = last_end_date + timedelta(days=1)
        else:
            # 如果没有历史对账单，使用空值
            start_date = None
        
        # 新建对账单
        statement_repo.create({
            "supplier_id": supplier_id,
            "start_date": start_date,
            "end_date": None,
            "statement_amount": amount,
            "received_amount": 0.00,
            "unreceived_amount": amount,
            "pay_status": False,
            "invoice_status": False
        })


async def _adjust_purchase_statement(db, statement_repo: PurchaseStatementRepository, supplier_id: int, amount: float):
    """
    调整对账单金额（用于修改/删除时）
    - amount 可为负数，代表扣减金额
    """
    existing = statement_repo.get_by_supplier(supplier_id)
    if not existing:
        return
    
    new_amount = float(existing["statement_amount"]) + amount
    if new_amount < 0:
        new_amount = 0
    
    new_unreceived = new_amount - float(existing["received_amount"])
    if new_unreceived < 0:
        new_unreceived = 0
    
    new_status = new_unreceived <= 0
    
    statement_repo.update_amount(
        statement_id=existing["id"],
        statement_amount=new_amount,
        unreceived_amount=new_unreceived,
        pay_status=new_status
    )


async def export_purchase_bill(bill_id: int, end_date: Optional[str] = None) -> Dict[str, Any]:
    """
    导出采购对账单
    - 获取对账单数据（与bill/detail相同）
    - 转换为xlsx文件流
    """
    from app.utils.export_utils import convert_to_xlsx
    
    # 第一步：获取与bill/detail一样的数据
    data = await get_purchase_bill_detail(bill_id, end_date)
    
    # 第二步：将数据传给convert_to_xlsx函数（暂时pass）
    xlsx_bytes = convert_to_xlsx(data, bill_type="purchase")
    
    # 第三步：返回xlsx文件数据流
    return {
        "data": data,
        "xlsx_bytes": xlsx_bytes,
        "filename": f"采购对账单_{data['bill_info']['supplier_name']}_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
    }