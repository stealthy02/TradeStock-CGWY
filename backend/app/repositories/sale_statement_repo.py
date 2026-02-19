from typing import Optional, Dict, List
from decimal import Decimal
from datetime import datetime
from sqlalchemy import func, desc
from sqlalchemy.orm import Session
from app.models.sale_statement import SaleStatement
from app.models.purchaser import Purchaser
from app.models.sale_info import SaleInfo
from app.models.goods import Goods

class SaleStatementRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, data: Dict) -> int:
        obj = SaleStatement(**data)
        self.db.add(obj)
        self.db.flush()
        self.db.refresh(obj)
        return obj.id
    
    def get_by_id(self, id: int) -> Optional[Dict]:
        result = self.db.query(
            SaleStatement,
            Purchaser.purchaser_name
        ).join(
            Purchaser, SaleStatement.purchaser_id == Purchaser.id
        ).filter(
            SaleStatement.id == id,
            SaleStatement.is_deleted == False
        ).first()
        
        if result:
            obj, purchaser_name = result
            d = self._to_dict(obj)
            d["purchaser_name"] = purchaser_name
            return d
        return None
    
    def get_by_purchaser(self, purchaser_id: int) -> Optional[Dict]:
        obj = self.db.query(SaleStatement).filter(
            SaleStatement.purchaser_id == purchaser_id,
            SaleStatement.is_deleted == False,
            SaleStatement.end_date == None
        ).first()
        return self._to_dict(obj) if obj else None
    
    def get_last_closed_statement(self, purchaser_id: int) -> Optional[Dict]:
        obj = self.db.query(SaleStatement).filter(
            SaleStatement.purchaser_id == purchaser_id,
            SaleStatement.is_deleted == False,
            SaleStatement.end_date != None
        ).order_by(SaleStatement.end_date.desc()).first()
        return self._to_dict(obj) if obj else None
    
    def get_confirmed_statements(self, purchaser_id: int) -> List[Dict]:
        """
        获取该采购商的所有已确认对账单
        """
        objs = self.db.query(SaleStatement).filter(
            SaleStatement.purchaser_id == purchaser_id,
            SaleStatement.is_deleted == False,
            SaleStatement.end_date != None
        ).all()
        return [self._to_dict(obj) for obj in objs]
    
    def count_by_conditions(self, purchaser_id: Optional[int],
                           receive_status: Optional[int], invoice_status: Optional[int],
                           min_amount: Optional[Decimal], max_amount: Optional[Decimal]) -> int:
        query = self.db.query(func.count(SaleStatement.id)).filter(
            SaleStatement.is_deleted == False
        )
        if purchaser_id:
            query = query.filter(SaleStatement.purchaser_id == purchaser_id)
        if receive_status is not None:
            query = query.filter(SaleStatement.receive_status == receive_status)
        if invoice_status is not None:
            query = query.filter(SaleStatement.invoice_status == invoice_status)
        if min_amount is not None:
            query = query.filter(SaleStatement.statement_amount >= min_amount)
        if max_amount is not None:
            query = query.filter(SaleStatement.statement_amount <= max_amount)
        return query.scalar()
    
    def list_by_conditions(self, purchaser_id: Optional[int],
                          receive_status: Optional[int], invoice_status: Optional[int],
                          min_amount: Optional[Decimal], max_amount: Optional[Decimal],
                          offset: int, limit: int) -> List[Dict]:
        query = self.db.query(
            SaleStatement,
            Purchaser.purchaser_name
        ).join(
            Purchaser, SaleStatement.purchaser_id == Purchaser.id
        ).filter(SaleStatement.is_deleted == False)
        
        if purchaser_id:
            query = query.filter(SaleStatement.purchaser_id == purchaser_id)
        if receive_status is not None:
            query = query.filter(SaleStatement.receive_status == receive_status)
        if invoice_status is not None:
            query = query.filter(SaleStatement.invoice_status == invoice_status)
        if min_amount is not None:
            query = query.filter(SaleStatement.statement_amount >= min_amount)
        if max_amount is not None:
            query = query.filter(SaleStatement.statement_amount <= max_amount)
        
        results = query.order_by(SaleStatement.create_time.desc()).offset(offset).limit(limit).all()
        items = []
        for obj, purchaser_name in results:
            d = self._to_dict(obj)
            d["purchaser_name"] = purchaser_name
            d["receive_status_text"] = "已结清" if obj.receive_status else "未结清"
            d["invoice_status_text"] = "已开票" if obj.invoice_status else "未开票"
            items.append(d)
        return items
    
    def update_amount_and_profit(self, statement_id: int, statement_amount: Decimal,
                                total_profit: Decimal, total_cost: Decimal,
                                unreceived_amount: Decimal, receive_status: bool) -> None:
        self.db.query(SaleStatement).filter(
            SaleStatement.id == statement_id
        ).update({
            "statement_amount": statement_amount,
            "total_profit": total_profit,
            "total_cost": total_cost,
            "unreceived_amount": unreceived_amount,
            "receive_status": receive_status
        })
        self.db.flush()
    
    def update_receipt(self, statement_id: int, received_amount: Decimal,
                      unreceived_amount: Decimal, receive_status: bool) -> None:
        self.db.query(SaleStatement).filter(
            SaleStatement.id == statement_id
        ).update({
            "received_amount": received_amount,
            "unreceived_amount": unreceived_amount,
            "receive_status": receive_status
        })
        self.db.flush()
    
    def update_invoice_status(self, id: int, status: int) -> None:
        self.db.query(SaleStatement).filter(
            SaleStatement.id == id
        ).update({"invoice_status": bool(status)})
        self.db.flush()
    
    def get_total_unreceived_amount(self) -> Decimal:
        result = self.db.query(func.sum(SaleStatement.unreceived_amount)).filter(
            SaleStatement.is_deleted == False
        ).scalar()
        return result or Decimal("0.00")
    
    def _to_dict(self, obj: SaleStatement) -> Dict:
        return {
            "id": obj.id,
            "purchaser_id": obj.purchaser_id,
            "start_date": obj.start_date,
            "end_date": obj.end_date,
            "statement_amount": obj.statement_amount,
            "total_cost": obj.total_cost,
            "total_profit": obj.total_profit,
            "received_amount": obj.received_amount,
            "unreceived_amount": obj.unreceived_amount,
            "receive_status": obj.receive_status,
            "invoice_status": obj.invoice_status,
            "is_deleted": obj.is_deleted,
            "create_time": obj.create_time,
            "update_time": obj.update_time
        }
    
    def soft_delete(self, id: int) -> None:
        self.db.query(SaleStatement).filter(
            SaleStatement.id == id
        ).update({"is_deleted": True})
        self.db.flush()
    
    def update_end_date(self, id: int, end_date: datetime) -> None:
        self.db.query(SaleStatement).filter(
            SaleStatement.id == id
        ).update({"end_date": end_date})
        self.db.flush()
    
    def get_total_statement_amount_by_date(self, start_date: datetime, end_date: datetime) -> Decimal:
        """
        获取指定时间范围内的销售对账单总金额
        说明：end_date为空的记录视为本日
        """
        # 转换为date类型进行比较
        start_date_date = start_date.date()
        end_date_date = end_date.date()
        today_date = datetime.now().date()
        
        # 构建查询，处理end_date为空的情况
        from sqlalchemy import or_
        # 使用字符串格式化日期，确保SQLite能正确处理
        result = self.db.query(func.sum(SaleStatement.statement_amount)).filter(
            SaleStatement.is_deleted == False,
            or_(
                # end_date不为空且在时间范围内
                (SaleStatement.end_date.isnot(None)) & 
                (SaleStatement.end_date >= start_date_date) & 
                (SaleStatement.end_date <= end_date_date),
                # end_date为空且视为今天，今天在时间范围内
                (SaleStatement.end_date.is_(None)) & 
                (today_date >= start_date_date) & 
                (today_date <= end_date_date)
            )
        ).scalar()
        return Decimal(str(result)) if result is not None else Decimal("0.00")
    
    def get_total_profit_by_date(self, start_date: datetime, end_date: datetime) -> Decimal:
        """
        获取指定时间范围内的销售对账单总利润
        说明：end_date为空的记录视为本日
        """
        # 转换为date类型进行比较
        start_date_date = start_date.date()
        end_date_date = end_date.date()
        today_date = datetime.now().date()
        
        # 构建查询，处理end_date为空的情况
        from sqlalchemy import or_
        result = self.db.query(func.sum(SaleStatement.total_profit)).filter(
            SaleStatement.is_deleted == False,
            or_(
                # end_date不为空且在时间范围内
                (SaleStatement.end_date.isnot(None)) & 
                (SaleStatement.end_date >= start_date_date) & 
                (SaleStatement.end_date <= end_date_date),
                # end_date为空且视为今天，今天在时间范围内
                (SaleStatement.end_date.is_(None)) & 
                (today_date >= start_date_date) & 
                (today_date <= end_date_date)
            )
        ).scalar()
        return Decimal(str(result)) if result is not None else Decimal("0.00")
    
    def get_purchaser_profit_distribution(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """
        获取指定时间范围内的采购商利润分布
        说明：end_date为空的记录视为本日
        """
        # 转换为date类型进行比较
        start_date_date = start_date.date()
        end_date_date = end_date.date()
        today_date = datetime.now().date()
        
        # 构建查询，处理end_date为空的情况
        from sqlalchemy import or_
        results = self.db.query(
            Purchaser.purchaser_name,
            func.sum(SaleStatement.total_profit).label("profit")
        ).join(
            SaleStatement, SaleStatement.purchaser_id == Purchaser.id
        ).filter(
            SaleStatement.is_deleted == False,
            or_(
                # end_date不为空且在时间范围内
                (SaleStatement.end_date != None) & 
                (SaleStatement.end_date >= start_date_date) & 
                (SaleStatement.end_date <= end_date_date),
                # end_date为空且视为今天，今天在时间范围内
                (SaleStatement.end_date == None) & 
                (today_date >= start_date_date) & 
                (today_date <= end_date_date)
            )
        ).group_by(
            Purchaser.purchaser_name
        ).all()
        
        return [
            {"name": name, "value": float(profit or 0)}
            for name, profit in results
        ]
    
    def get_product_profit_distribution(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """
        获取指定时间范围内的商品利润分布
        说明：end_date为空的记录视为本日
        """
        from app.models.goods import Goods
        
        # 转换为date类型进行比较
        start_date_date = start_date.date()
        end_date_date = end_date.date()
        today_date = datetime.now().date()
        
        # 构建查询，处理end_date为空的情况
        from sqlalchemy import or_
        results = self.db.query(
            Goods.goods_name,
            func.sum(SaleInfo.total_profit).label("profit")
        ).join(
            Goods, SaleInfo.goods_id == Goods.id
        ).join(
            SaleStatement, SaleInfo.statement_id == SaleStatement.id
        ).filter(
            SaleInfo.is_deleted == False,
            SaleStatement.is_deleted == False,
            or_(
                # end_date不为空且在时间范围内
                (SaleStatement.end_date != None) & 
                (SaleStatement.end_date >= start_date_date) & 
                (SaleStatement.end_date <= end_date_date),
                # end_date为空且视为今天，今天在时间范围内
                (SaleStatement.end_date == None) & 
                (today_date >= start_date_date) & 
                (today_date <= end_date_date)
            )
        ).group_by(
            Goods.goods_name
        ).all()
        
        return [
            {"name": name, "value": float(profit or 0)}
            for name, profit in results
        ]
    
    def get_monthly_revenue_expend(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """
        获取指定时间范围内的月度营收支出数据
        说明：end_date为空的记录视为本日
        """
        # 转换为date类型进行比较
        start_date_date = start_date.date()
        end_date_date = end_date.date()
        today_date = datetime.now().date()
        
        # 构建查询，处理end_date为空的情况
        from sqlalchemy import or_, func as sql_func
        
        # 按月分组查询销售对账单金额（营收）
        sale_results = self.db.query(
            sql_func.strftime("%Y-%m", sql_func.coalesce(SaleStatement.end_date, today_date)).label("month"),
            sql_func.sum(SaleStatement.statement_amount).label("revenue")
        ).filter(
            SaleStatement.is_deleted == False,
            or_(
                # end_date不为空且在时间范围内
                (SaleStatement.end_date != None) & 
                (SaleStatement.end_date >= start_date_date) & 
                (SaleStatement.end_date <= end_date_date),
                # end_date为空且视为今天，今天在时间范围内
                (SaleStatement.end_date == None) & 
                (today_date >= start_date_date) & 
                (today_date <= end_date_date)
            )
        ).group_by(
            "month"
        ).all()
        
        # 将营收结果转换为字典
        sale_data = {item.month: float(item.revenue or 0) for item in sale_results}
        
        # 查询采购支出（按月份）
        from app.models.purchase_statement import PurchaseStatement
        purchase_results = self.db.query(
            sql_func.strftime("%Y-%m", sql_func.coalesce(PurchaseStatement.end_date, today_date)).label("month"),
            sql_func.sum(PurchaseStatement.statement_amount).label("expend")
        ).filter(
            PurchaseStatement.is_deleted == False,
            or_(
                # end_date不为空且在时间范围内
                (PurchaseStatement.end_date != None) & 
                (PurchaseStatement.end_date >= start_date_date) & 
                (PurchaseStatement.end_date <= end_date_date),
                # end_date为空且视为今天，今天在时间范围内
                (PurchaseStatement.end_date == None) & 
                (today_date >= start_date_date) & 
                (today_date <= end_date_date)
            )
        ).group_by(
            "month"
        ).all()
        
        # 查询运营杂费（按月份）
        from app.models.operating_expense import OperatingExpense
        expense_results = self.db.query(
            sql_func.strftime("%Y-%m", OperatingExpense.expense_date).label("month"),
            sql_func.sum(OperatingExpense.expense_amount).label("expend")
        ).filter(
            OperatingExpense.is_deleted == False,
            OperatingExpense.expense_date >= start_date_date,
            OperatingExpense.expense_date <= end_date_date
        ).group_by(
            "month"
        ).all()
        
        # 合并支出数据
        expend_data = {}
        for item in purchase_results:
            month = item.month
            expend_data[month] = expend_data.get(month, 0) + float(item.expend or 0)
        
        for item in expense_results:
            month = item.month
            expend_data[month] = expend_data.get(month, 0) + float(item.expend or 0)
        
        # 构建完整的月度数据列表
        from datetime import datetime as dt
        from dateutil.relativedelta import relativedelta
        
        monthly_data = []
        current_date = dt(start_date.year, start_date.month, 1)
        end_month = dt(end_date.year, end_date.month, 1)
        
        while current_date <= end_month:
            month_str = current_date.strftime("%Y-%m")
            monthly_data.append({
                "month": month_str,
                "revenue": sale_data.get(month_str, 0),
                "expend": expend_data.get(month_str, 0)  # 计算采购支出+运营杂费
            })
            current_date += relativedelta(months=1)
        
        return monthly_data