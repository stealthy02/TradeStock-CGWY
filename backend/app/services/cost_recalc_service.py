from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal

from app.database import get_db
from app.repositories.goods_repo import GoodsRepository
from app.repositories.purchase_info_repo import PurchaseInfoRepository
from app.repositories.sale_info_repo import SaleInfoRepository
from app.repositories.inventory_loss_repo import InventoryLossRepository
from app.repositories.sale_statement_repo import SaleStatementRepository
from app.models.purchase_info import PurchaseInfo
from app.models.sale_info import SaleInfo
from app.models.inventory_loss import InventoryLoss
from sqlalchemy import and_, or_


async def recalculate_cost_for_goods(goods_id: int) -> None:
    """
    按时间顺序重新计算指定商品的成本、库存和销售利润
    
    逻辑：
    1. 获取该商品的所有采购、销售、报损记录，按时间排序
    2. 按时间顺序遍历，重新计算加权平均成本
    3. 更新销售记录的成本快照
    4. 更新商品的当前库存和成本
    5. 更新销售对账单的总成本和总利润
    """
    from app.database import SessionLocal
    db = SessionLocal()
    
    try:
        goods_repo = GoodsRepository(db)
        purchase_repo = PurchaseInfoRepository(db)
        sale_repo = SaleInfoRepository(db)
        loss_repo = InventoryLossRepository(db)
        statement_repo = SaleStatementRepository(db)
        
        # 获取商品信息
        goods = goods_repo.get_by_id(goods_id)
        if not goods:
            return
        
        product_spec = float(goods.get("product_spec", 1))
        
        # 1. 获取所有相关记录，按时间排序
        all_events = []
        
        # 获取采购记录
        purchases = db.query(PurchaseInfo).filter(
            PurchaseInfo.goods_id == goods_id,
            PurchaseInfo.is_deleted == False
        ).order_by(PurchaseInfo.purchase_date, PurchaseInfo.id).all()
        
        for p in purchases:
            all_events.append({
                "type": "purchase",
                "date": p.purchase_date,
                "id": p.id,
                "num": p.purchase_num,
                "unit_price": float(p.purchase_unit_price),
                "total_price": float(p.purchase_total_price),
                "obj": p
            })
        
        # 获取销售记录
        sales = db.query(SaleInfo).filter(
            SaleInfo.goods_id == goods_id,
            SaleInfo.is_deleted == False
        ).order_by(SaleInfo.sale_date, SaleInfo.id).all()
        
        for s in sales:
            all_events.append({
                "type": "sale",
                "date": s.sale_date,
                "id": s.id,
                "num": s.sale_num,
                "unit_price": float(s.sale_unit_price),
                "total_price": float(s.sale_total_price),
                "obj": s
            })
        
        # 获取报损记录
        losses = db.query(InventoryLoss).filter(
            InventoryLoss.goods_id == goods_id,
            InventoryLoss.is_deleted == False
        ).order_by(InventoryLoss.loss_date, InventoryLoss.id).all()
        
        for l in losses:
            all_events.append({
                "type": "loss",
                "date": l.loss_date,
                "id": l.id,
                "num": l.loss_num,
                "obj": l
            })
        
        # 按日期和类型排序（同一日期，采购先于销售，销售先于报损）
        def sort_key(event):
            type_priority = {"purchase": 0, "sale": 1, "loss": 2}
            return (event["date"], type_priority[event["type"]], event["id"])
        
        all_events.sort(key=sort_key)
        
        # 2. 按时间顺序遍历，重新计算
        current_stock = 0
        current_cost = 0.0
        current_total_value = 0.0
        
        # 用于跟踪需要更新的销售对账单
        statements_to_update = {}
        
        for event in all_events:
            if event["type"] == "purchase":
                # 采购：增加库存，计算新加权平均成本
                purchase_num = event["num"]
                purchase_total = event["total_price"]
                
                old_total_value = current_stock * current_cost * product_spec
                new_stock = current_stock + purchase_num
                new_total_value = old_total_value + purchase_total
                
                if new_stock > 0:
                    new_cost = new_total_value / (new_stock * product_spec)
                else:
                    new_cost = event["unit_price"]
                
                new_total_value = new_cost * new_stock * product_spec
                
                current_stock = new_stock
                current_cost = new_cost
                current_total_value = new_total_value
            
            elif event["type"] == "sale":
                # 销售：减少库存，记录成本快照
                sale_num = event["num"]
                sale_unit_price = event["unit_price"]
                sale_total_price = event["total_price"]
                sale_obj = event["obj"]
                
                # 计算成本和利润
                unit_cost = current_cost
                total_cost = unit_cost * sale_num * product_spec
                unit_profit = sale_unit_price - unit_cost
                total_profit = unit_profit * sale_num * product_spec
                
                # 更新销售记录
                sale_obj.trade_unit_cost = Decimal(str(round(unit_cost, 2)))
                sale_obj.unit_profit = Decimal(str(round(unit_profit, 2)))
                sale_obj.total_profit = Decimal(str(round(total_profit, 2)))
                
                # 跟踪需要更新的对账单
                statement_id = sale_obj.statement_id
                if statement_id not in statements_to_update:
                    statements_to_update[statement_id] = {
                        "total_amount": 0.0,
                        "total_cost": 0.0,
                        "total_profit": 0.0
                    }
                statements_to_update[statement_id]["total_amount"] += sale_total_price
                statements_to_update[statement_id]["total_cost"] += total_cost
                statements_to_update[statement_id]["total_profit"] += total_profit
                
                # 更新库存
                current_stock = current_stock - sale_num
                current_total_value = current_cost * current_stock * product_spec
            
            elif event["type"] == "loss":
                # 报损：减少库存
                loss_num = event["num"]
                loss_obj = event["obj"]
                
                # 更新报损记录的成本快照
                loss_obj.loss_unit_cost = Decimal(str(round(current_cost, 2)))
                loss_obj.loss_total_cost = Decimal(str(round(current_cost * loss_num * product_spec, 2)))
                
                # 更新库存
                current_stock = current_stock - loss_num
                current_total_value = current_cost * current_stock * product_spec
        
        # 3. 更新商品当前库存和成本
        goods_repo.update_stock_and_cost(
            goods_id=goods_id,
            new_stock=current_stock,
            new_cost=Decimal(str(round(current_cost, 2))),
            new_value=Decimal(str(round(current_total_value, 2)))
        )
        
        # 4. 更新销售对账单
        for statement_id, data in statements_to_update.items():
            statement = statement_repo.get_by_id(statement_id)
            if statement:
                # 获取该对账单的所有销售记录重新计算（确保准确）
                sales_in_statement = db.query(SaleInfo).filter(
                    SaleInfo.statement_id == statement_id,
                    SaleInfo.is_deleted == False
                ).all()
                
                total_amount = 0.0
                total_cost = 0.0
                total_profit = 0.0
                
                for s in sales_in_statement:
                    total_amount += float(s.sale_total_price)
                    total_cost += float(s.trade_unit_cost) * int(s.sale_num) * product_spec
                    total_profit += float(s.total_profit)
                
                statement_repo.update_amount_and_profit(
                    statement_id=statement_id,
                    statement_amount=Decimal(str(round(total_amount, 2))),
                    total_profit=Decimal(str(round(total_profit, 2))),
                    total_cost=Decimal(str(round(total_cost, 2))),
                    unreceived_amount=Decimal(str(round(total_amount - float(statement.get("received_amount", 0)), 2))),
                    receive_status=(total_amount - float(statement.get("received_amount", 0))) <= 0
                )
        
        db.commit()
        
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()


async def recalculate_all_costs() -> None:
    """重新计算所有商品的成本"""
    from app.database import SessionLocal
    from app.models.goods import Goods
    
    db = SessionLocal()
    
    try:
        # 获取所有未删除的商品
        goods_list = db.query(Goods).filter(Goods.is_deleted == False).all()
        
        for goods in goods_list:
            await recalculate_cost_for_goods(goods.id)
            
    finally:
        db.close()
