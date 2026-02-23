from typing import Optional, Dict, Any
from datetime import datetime

from app.database import get_db
from app.repositories.goods_repo import GoodsRepository
from app.repositories.inventory_flow_repo import InventoryFlowRepository
from app.repositories.inventory_loss_repo import InventoryLossRepository
# 导入项目统一自定义异常（和其他服务层路径完全一致）
from app.utils.exceptions import CustomAPIException, NotFoundException


# ==================== 库存信息查询 ====================
async def list_inventory(
    product: Optional[str],
    min_num: Optional[int],
    max_num: Optional[int],
    sort_field: Optional[str],
    sort_order: Optional[str],
    page_num: int,
    page_size: int
) -> Dict[str, Any]:
    """
    5.1.1 查询当前库存列表
    - 支持商品名称模糊搜索
    - 支持库存数量范围筛选
    - 支持字段排序（inventory_num/inventory_value）
    - 返回最后采购/销售日期（需关联采购/销售记录）
    """
    # 处理排序字段映射（驼峰转下划线）
    sort_mapping = {
        "inventory_num": "current_stock_num",
        "inventory_value": "stock_total_value",
        "inventory_cost": "stock_unit_cost"
    }
    db_sort_field = sort_mapping.get(sort_field, "create_time")
    db_sort_order = sort_order if sort_order in ["asc", "desc"] else "desc"

    db = next(get_db())
    goods_repo = GoodsRepository(db)

    # 统计总数
    total = goods_repo.count_by_inventory_conditions(
        name=product,
        min_num=min_num,
        max_num=max_num
    )

    pages = (total + page_size - 1) // page_size if total > 0 else 0

    # 查询列表
    list_data = goods_repo.list_by_inventory_conditions(
        name=product,
        min_num=min_num,
        max_num=max_num,
        sort_field=db_sort_field,
        sort_order=db_sort_order,
        offset=(page_num - 1) * page_size,
        limit=page_size
    )

    # 补充最后采购/销售日期
    enriched_list = []
    for item in list_data:
        last_purchase = goods_repo.get_last_purchase_date(item["id"])
        last_sale = goods_repo.get_last_sale_date(item["id"])

        enriched_list.append({
            "product_name": item["goods_name"],
            "product_spec": item["product_spec"],
            "inventory_num": int(item["current_stock_num"]),
            "inventory_cost": float(item["stock_unit_cost"]),
            "inventory_value": float(item["stock_total_value"]),
            "last_purchase_date": last_purchase.strftime("%Y-%m-%d") if last_purchase else None,
            "last_sale_date": last_sale.strftime("%Y-%m-%d") if last_sale else None
        })

    return {
        "total": total,
        "pages": pages,
        "list": enriched_list
    }


async def get_inventory_detail(
    product: str,
    product_spec: int,
    page_num: int,
    page_size: int
) -> Dict[str, Any]:
    """
    5.1.2 单个商品库存详情
    - 查询商品当前库存信息
    - 查询库存变动记录（采购入库/销售出库）
    """
    db = next(get_db())
    goods_repo = GoodsRepository(db)
    inventory_flow_repo = InventoryFlowRepository(db)

    # 查询商品信息（按名称和规格组合），抛出404统一异常
    goods = goods_repo.get_by_name_and_spec(product, product_spec)
    if not goods or goods.get("is_deleted"):
        raise NotFoundException(message="商品不存在")

    # 统计变动记录总数
    total = inventory_flow_repo.count_by_goods_and_date(
        goods_id=goods["id"]
    )

    pages = (total + page_size - 1) // page_size if total > 0 else 0

    # 查询变动记录
    flow_list = inventory_flow_repo.list_by_goods_and_date(
        goods_id=goods["id"],
        offset=(page_num - 1) * page_size,
        limit=page_size
    )

    # 格式化变动记录
    formatted_flow = []
    for flow in flow_list:
        change_type = "采购入库" if flow["oper_type"] == 1 else "销售出库" if flow["oper_type"] == 2 else "库存报损" if flow["oper_type"] == 3 else "库存初始化"
        formatted_flow.append({
            "id": flow["id"],
            "change_type": change_type,
            "change_num": flow["change_num"],
            "change_date": flow["oper_time"].strftime("%Y-%m-%d %H:%M:%S"),
            "related_id": flow["biz_id"],
            "operator": None,  # 系统生成，无操作人
            "remark": flow["oper_source"],
            "stock_before": flow["stock_before"],
            "stock_after": flow["stock_after"]
        })

    return {
        "inventory_info": {
            "product_name": goods["goods_name"],
            "product_spec": goods["product_spec"],
            "inventory_num": int(goods["current_stock_num"]),
            "inventory_cost": float(goods["stock_unit_cost"]),
            "inventory_value": float(goods["stock_total_value"]),
            "total_purchase_num": goods_repo.get_total_purchase_num(goods["id"]),
            "total_sale_num": goods_repo.get_total_sale_num(goods["id"])
        },
        "change_record": {
            "total": total,
            "pages": pages,
            "list": formatted_flow
        }
    }


# ==================== 库存报损 ====================
async def add_inventory_loss(data) -> Dict[str, Any]:
    """
    5.2.1 新增库存报损
    - 校验商品存在
    - 校验库存充足（601错误）
    - 记录报损时单位成本快照
    - 扣减库存
    - 生成库存流动记录
    - 自动归属结算周期
    """
    # Pydantic模型属性访问
    product_name = data.product_name
    product_spec = data.product_spec
    loss_num = data.loss_num
    # 日期格式校验
    try:
        loss_date = datetime.strptime(data.loss_date, "%Y-%m-%d")
    except ValueError:
        raise CustomAPIException(code=400, message="报损日期格式错误，要求%Y-%m-%d")

    db = next(get_db())
    goods_repo = GoodsRepository(db)
    inventory_loss_repo = InventoryLossRepository(db)
    inventory_flow_repo = InventoryFlowRepository(db)

    # 查询商品（按名称和规格组合），抛出404统一异常
    goods = goods_repo.get_by_name_and_spec(product_name, product_spec)
    if not goods or goods.get("is_deleted"):
        raise NotFoundException(message="商品不存在")

    current_stock = int(goods["current_stock_num"])

    # 校验库存充足（601 自定义业务错误）
    if loss_num > current_stock:
        raise CustomAPIException(code=604, message="报损数量超过当前库存")

    # 获取当前成本快照
    unit_cost = float(goods["stock_unit_cost"])
    spec_value = float(product_spec)
    total_cost = unit_cost * spec_value * loss_num

    # 创建报损记录
    loss_data = {
        "goods_id": goods["id"],
        "loss_num": loss_num,
        "loss_unit_cost": unit_cost,
        "loss_total_cost": total_cost,
        "loss_date": loss_date,
        "loss_reason": data.loss_reason if hasattr(data, "loss_reason") else "其他",
        "remark": data.remark if hasattr(data, "remark") else None
    }
    loss_id = inventory_loss_repo.create(loss_data)

    # 扣减库存
    new_stock = current_stock - loss_num
    new_value = unit_cost * new_stock * spec_value if new_stock > 0 else 0
    goods_repo.update_stock_and_cost(
        goods_id=goods["id"],
        new_stock=new_stock,
        new_cost=unit_cost,
        new_value=new_value
    )

    # 库存流动数据变动更改处
    # 生成库存流动记录（oper_type=3 报损）
    loss_reason = data.loss_reason if hasattr(data, "loss_reason") else "其他"
    inventory_flow_repo.create({
        "goods_id": goods["id"],
        "oper_type": 3,  # 报损
        "biz_id": loss_id,
        "change_num": -loss_num,
        "stock_before": current_stock,
        "stock_after": new_stock,
        "oper_time": loss_date,
        "oper_source": f"报损-{loss_reason}"
    })

    db.commit()
    
    # 触发成本重算
    from app.services.cost_recalc_service import recalculate_cost_for_goods
    await recalculate_cost_for_goods(goods["id"])
    
    return {
        "id": loss_id,
        "loss_cost": total_cost
    }


async def list_inventory_loss(
    id: Optional[int],
    product: Optional[str],
    start_date: Optional[str],
    end_date: Optional[str],
    page_num: int,
    page_size: int
) -> Dict[str, Any]:
    """
    5.2.2 查询库存报损列表
    - 支持商品名称模糊搜索
    - 支持日期范围筛选
    - 关联商品表显示名称
    """
    # 解析日期范围，增加格式校验
    parsed_start_date = None
    parsed_end_date = None
    try:
        if start_date:
            parsed_start_date = datetime.strptime(start_date, "%Y-%m-%d")
        if end_date:
            parsed_end_date = datetime.strptime(end_date, "%Y-%m-%d")
            parsed_end_date = parsed_end_date.replace(hour=23, minute=59, second=59)
    except ValueError:
        raise CustomAPIException(code=400, message="查询日期格式错误，要求%Y-%m-%d")

    db = next(get_db())
    inventory_loss_repo = InventoryLossRepository(db)

    # 统计总数
    total = inventory_loss_repo.count_by_conditions(
        id=id,
        product_name=product,
        start_date=parsed_start_date,
        end_date=parsed_end_date
    )

    pages = (total + page_size - 1) // page_size if total > 0 else 0

    # 查询列表
    list_data = inventory_loss_repo.list_by_conditions(
        id=id,
        product_name=product,
        start_date=parsed_start_date,
        end_date=parsed_end_date,
        offset=(page_num - 1) * page_size,
        limit=page_size
    )

    # 格式化返回
    formatted_list = []
    for item in list_data:
        formatted_list.append({
            "id": item["id"],
            "product_name": item["goods_name"],
            "product_spec": item.get("product_spec", ""),
            "loss_num": int(item["loss_num"]),
            "lossUnitCost": float(item["loss_unit_cost"]),
            "losstotal_cost": float(item["loss_total_cost"]),
            "loss_date": item["loss_date"].strftime("%Y-%m-%d"),
            "loss_reason": item["loss_reason"],
            "remark": item["remark"]
        })

    return {
        "total": total,
        "pages": pages,
        "list": formatted_list
    }


async def delete_inventory_loss(id: int) -> None:
    """
    5.2.3 删除报损记录（恢复库存）
    - 校验记录存在
    - 恢复库存数量（加回）
    - 更新库存总价值
    - 删除库存流动记录或标记失效（文档要求恢复库存）
    - 软删除报损记录
    """
    db = next(get_db())
    inventory_loss_repo = InventoryLossRepository(db)
    goods_repo = GoodsRepository(db)

    # 查询报损记录，抛出404统一异常
    loss = inventory_loss_repo.get_by_id(id)
    if not loss or loss.get("is_deleted"):
        raise NotFoundException(message="报损记录不存在")

    goods_id = loss["goods_id"]
    loss_num = int(loss["loss_num"])

    # 查询当前库存
    goods = goods_repo.get_by_id(goods_id)
    current_stock = int(goods["current_stock_num"])

    # 恢复库存
    new_stock = current_stock + loss_num
    new_value = float(goods["stock_unit_cost"]) * new_stock
    new_cost = goods["stock_unit_cost"]
    goods_repo.update_stock_and_cost(goods_id, new_stock, new_cost,new_value)

    # 软删除报损记录
    inventory_loss_repo.soft_delete(id)

    db.commit()
    
    # 触发成本重算
    from app.services.cost_recalc_service import recalculate_cost_for_goods
    await recalculate_cost_for_goods(goods_id)


# ==================== 库存预警/盘点 ====================
async def list_inventory_warning(
    warning_line: int,
    page_num: int,
    page_size: int
) -> Dict[str, Any]:
    """
    5.3.1 查询库存预警列表
    - 查询库存数量 <= warning_line 的商品
    - 返回最后采购日期
    - 返回主要供货商（可选，从最后采购记录获取）
    """
    db = next(get_db())
    goods_repo = GoodsRepository(db)

    # 统计总数
    total = goods_repo.count_by_warning_line(warning_line)
    pages = (total + page_size - 1) // page_size if total > 0 else 0

    # 查询列表
    list_data = goods_repo.list_by_warning_line(
        warning_line=warning_line,
        offset=(page_num - 1) * page_size,
        limit=page_size
    )

    formatted_list = []
    for item in list_data:
        # 获取最后采购信息
        last_purchase = goods_repo.get_last_purchase_info(item["id"])

        formatted_list.append({
            "product_name": item["goods_name"],
            "product_spec": item["product_spec"],
            "inventory_num": int(item["current_stock_num"]),
            "warning_line": warning_line,
            "last_purchase_date": last_purchase["purchase_date"] if last_purchase else None,
            "supplier_name": last_purchase["supplier_name"] if last_purchase else None
        })

    return {
        "total": total,
        "pages": pages,
        "list": formatted_list
    }