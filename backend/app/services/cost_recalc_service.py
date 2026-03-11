from typing import Optional, Dict, Any, List
from datetime import datetime, date
from decimal import Decimal

from app.database import get_db
from app.repositories.goods_repo import GoodsRepository
from app.repositories.purchase_info_repo import PurchaseInfoRepository
from app.repositories.sale_info_repo import SaleInfoRepository
from app.repositories.inventory_loss_repo import InventoryLossRepository
from app.repositories.sale_statement_repo import SaleStatementRepository
from app.repositories.inventory_flow_repo import InventoryFlowRepository
from app.models.purchase_info import PurchaseInfo
from app.models.sale_info import SaleInfo
from app.models.inventory_loss import InventoryLoss
from app.models.inventory_flow import InventoryFlow


async def recalculate_from_date(goods_id: int, start_date: date) -> None:
    """
    从指定日期开始增量重算成本
    
    重要：此函数只更新成本相关字段，不更新库存数量！
    库存数量由库存流动记录决定，商品表的库存应该在调用此函数之前已经更新。
    
    逻辑：
    1. 日期处理：以较早的日期作为基准日期
    2. 库存数据获取：根据基准日期获取库存流动记录，筛选日期早于基准日期，按日期降序排序
    3. 业务数据查询与排序：查询日期>=基准日期的全部销售、采购、报损记录，按时间顺序和业务类型优先级排序
    4. 库存流动记录处理：读取日期>=基准日期的库存流动记录，直接修改现有记录
    5. 成本计算与更新：按排序顺序逐条应用成本计算逻辑，更新相关记录
    6. 最终数据更新：更新商品表中的成本及相关字段
    
    Args:
        goods_id: 商品ID
        start_date: 开始重算的日期（从该日期点开始）
    """
    from app.database import SessionLocal
    db = SessionLocal()
    
    try:
        goods_repo = GoodsRepository(db)
        statement_repo = SaleStatementRepository(db)
        flow_repo = InventoryFlowRepository(db)
        goods = goods_repo.get_by_id(goods_id)
        if not goods:
            return
        product_spec = Decimal(str(goods.get("product_spec", 1)))
        
        # 1. 日期处理：以较早的日期作为基准日期
        start_date
        
        # 2. 库存数据获取：根据基准日期获取库存状态
        # 筛选条件：日期早于基准日期
        # 排序规则：按日期降序排列，日期相同则按ID降序排列
        # 获取排序后的第一条记录，记录此时的库存成本和变动后库存量数据
        stock_state = flow_repo.get_stock_state_at_date(goods_id, start_date)
        
        if stock_state:
            current_stock = Decimal(str(stock_state["stock_num"]))
            current_cost = Decimal(str(stock_state["unit_cost"]))
        else:
            current_stock = Decimal("0")
            current_cost = Decimal("0.0")
        
        current_total_value = current_stock * current_cost * product_spec
        
        # 3. 业务数据查询与排序
        future_flows = flow_repo.list_after_date(goods_id, start_date)
        
        # 4. 库存流动记录处理：读取该商品、型号下日期>=基准日期的库存流动记录
        # 处理方式：直接修改现有记录
        
        # 用于跟踪需要更新的销售对账单
        statements_to_update = set()
        
        # 5. 成本计算与更新：按排序顺序逐条应用成本计算逻辑
        for flow in future_flows:
            # 更新流动记录的前库存数量
            flow.stock_before = current_stock       
            if flow.oper_type == 1:  # 采购
                purchase = db.query(PurchaseInfo).filter(
                    PurchaseInfo.id == flow.biz_id,
                    PurchaseInfo.is_deleted == False
                ).first()
                
                if purchase:
                    purchase_num = Decimal(str(purchase.purchase_num))
                    purchase_total = Decimal(str(purchase.purchase_total_price))
                    
                    # 计算新的加权平均成本
                    old_total_value = current_stock * current_cost * product_spec
                    new_stock = current_stock + purchase_num
                    new_total_value = old_total_value + purchase_total
                    
                    if new_stock > 0:
                        new_cost = new_total_value / (new_stock * product_spec)
                    else:
                        new_cost = Decimal(str(purchase.purchase_unit_price))
                    
                    # 只更新成本计算用的变量，不直接更新商品表
                    current_stock = new_stock
                    current_cost = new_cost
                    current_total_value = new_cost * current_stock * product_spec
            
            elif flow.oper_type == 3:  # 报损
                loss = db.query(InventoryLoss).filter(
                    InventoryLoss.id == flow.biz_id,
                    InventoryLoss.is_deleted == False
                ).first()
                
                if loss:
                    loss_num = Decimal(str(loss.loss_num))
                    
                    # 更新报损记录的成本快照
                    loss.loss_unit_cost = Decimal(str(round(current_cost, 2)))
                    loss.loss_total_cost = Decimal(str(round(current_cost * loss_num * product_spec, 2)))
                    
                    # 只更新成本计算用的变量
                    current_stock = current_stock - loss_num
                    current_total_value = current_cost * current_stock * product_spec
            
            elif flow.oper_type == 2:  # 销售
                sale = db.query(SaleInfo).filter(
                    SaleInfo.id == flow.biz_id,
                    SaleInfo.is_deleted == False
                ).first()
                
                if sale:
                    sale_num = Decimal(str(sale.sale_num))
                    sale_unit_price = Decimal(str(sale.sale_unit_price))
                    
                    # 计算成本和利润
                    unit_cost = current_cost
                    total_cost = unit_cost * sale_num * product_spec
                    unit_profit = sale_unit_price - unit_cost
                    total_profit = unit_profit * sale_num * product_spec
                    
                    sale.trade_unit_cost = Decimal(str(round(unit_cost, 2)))
                    sale.unit_profit = Decimal(str(round(unit_profit, 2)))
                    sale.total_profit = Decimal(str(round(total_profit, 2)))

                    # 跟踪需要更新的对账单
                    statements_to_update.add(sale.statement_id)
                    
                    # 只更新成本计算用的变量
                    current_stock = current_stock - sale_num
                    current_total_value = current_cost * current_stock * product_spec
            
            # 更新流动记录的后库存数量和单位成本
            flow.stock_unit_cost = Decimal(str(round(current_cost, 2)))
            flow.stock_after = current_stock
        # 6. 最终数据更新：更新t_goods表中对应商品型号的成本及相关字段
        goods_repo.update_stock_and_cost(
            goods_id=goods_id,
            new_stock=current_stock,  # 这应该是正确的最终库存
            new_cost=Decimal(str(round(current_cost, 2))),
            new_value=Decimal(str(round(current_total_value, 2)))
        )
        
        # 更新销售对账单
        for statement_id in statements_to_update:
            statement = statement_repo.get_by_id(statement_id)
            if statement:
                # 获取该对账单的所有销售记录重新计算
                sales_in_statement = db.query(SaleInfo).filter(
                    SaleInfo.statement_id == statement_id,
                    SaleInfo.is_deleted == False
                ).all()
                
                total_amount = Decimal("0.0")
                total_cost = Decimal("0.0")
                total_profit = Decimal("0.0")
                
                for s in sales_in_statement:
                    total_amount += Decimal(str(s.sale_total_price))
                    total_cost += Decimal(str(s.trade_unit_cost)) * Decimal(str(s.sale_num)) * product_spec
                    total_profit += Decimal(str(s.total_profit))
                
                received_amount = Decimal(str(statement.get("received_amount", 0)))
                statement_repo.update_amount_and_profit(
                    statement_id=statement_id,
                    statement_amount=Decimal(str(round(total_amount, 2))),
                    total_profit=Decimal(str(round(total_profit, 2))),
                    total_cost=Decimal(str(round(total_cost, 2))),
                    unreceived_amount=Decimal(str(round(total_amount - received_amount, 2))),
                    receive_status=float(total_amount - received_amount) <= 0
                )
        
        db.commit()
        
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()
