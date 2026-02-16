from typing import Optional, Dict, List
from decimal import Decimal
from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.purchase_statement import PurchaseStatement
from app.models.supplier import Supplier
from app.models.purchase_info import PurchaseInfo

class PurchaseStatementRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, data: Dict) -> int:
        obj = PurchaseStatement(**data)
        self.db.add(obj)
        self.db.flush()
        self.db.refresh(obj)
        return obj.id
    
    def get_by_id(self, id: int) -> Optional[Dict]:
        result = self.db.query(
            PurchaseStatement,
            Supplier.supplier_name
        ).join(
            Supplier, PurchaseStatement.supplier_id == Supplier.id
        ).filter(
            PurchaseStatement.id == id,
            PurchaseStatement.is_deleted == False
        ).first()
        
        if result:
            obj, supplier_name = result
            d = self._to_dict(obj)
            d["supplier_name"] = supplier_name
            return d
        return None
    
    def get_by_supplier(self, supplier_id: int) -> Optional[Dict]:
        obj = self.db.query(PurchaseStatement).filter(
            PurchaseStatement.supplier_id == supplier_id,
            PurchaseStatement.is_deleted == False,
            PurchaseStatement.end_date == None
        ).first()
        return self._to_dict(obj) if obj else None
    
    def get_last_closed_statement(self, supplier_id: int) -> Optional[Dict]:
        obj = self.db.query(PurchaseStatement).filter(
            PurchaseStatement.supplier_id == supplier_id,
            PurchaseStatement.is_deleted == False,
            PurchaseStatement.end_date != None
        ).order_by(PurchaseStatement.end_date.desc()).first()
        return self._to_dict(obj) if obj else None
    
    def get_confirmed_statements(self, supplier_id: int) -> List[Dict]:
        """
        获取该供应商的所有已确认对账单
        """
        objs = self.db.query(PurchaseStatement).filter(
            PurchaseStatement.supplier_id == supplier_id,
            PurchaseStatement.is_deleted == False,
            PurchaseStatement.end_date != None
        ).all()
        return [self._to_dict(obj) for obj in objs]
    
    def count_by_conditions(self, supplier_id: Optional[int],
                           pay_status: Optional[int], invoice_status: Optional[int],
                           min_amount: Optional[Decimal], max_amount: Optional[Decimal]) -> int:
        query = self.db.query(func.count(PurchaseStatement.id)).filter(
            PurchaseStatement.is_deleted == False
        )
        if supplier_id:
            query = query.filter(PurchaseStatement.supplier_id == supplier_id)
        if pay_status is not None:
            query = query.filter(PurchaseStatement.pay_status == pay_status)
        if invoice_status is not None:
            query = query.filter(PurchaseStatement.invoice_status == invoice_status)
        if min_amount is not None:
            query = query.filter(PurchaseStatement.statement_amount >= min_amount)
        if max_amount is not None:
            query = query.filter(PurchaseStatement.statement_amount <= max_amount)
        return query.scalar()
    
    def list_by_conditions(self, supplier_id: Optional[int],
                          pay_status: Optional[int], invoice_status: Optional[int],
                          min_amount: Optional[Decimal], max_amount: Optional[Decimal],
                          offset: int, limit: int) -> List[Dict]:
        query = self.db.query(
            PurchaseStatement,
            Supplier.supplier_name
        ).join(
            Supplier, PurchaseStatement.supplier_id == Supplier.id
        ).filter(PurchaseStatement.is_deleted == False)
        
        if supplier_id:
            query = query.filter(PurchaseStatement.supplier_id == supplier_id)
        if pay_status is not None:
            query = query.filter(PurchaseStatement.pay_status == pay_status)
        if invoice_status is not None:
            query = query.filter(PurchaseStatement.invoice_status == invoice_status)
        if min_amount is not None:
            query = query.filter(PurchaseStatement.statement_amount >= min_amount)
        if max_amount is not None:
            query = query.filter(PurchaseStatement.statement_amount <= max_amount)
        
        results = query.order_by(PurchaseStatement.create_time.desc()).offset(offset).limit(limit).all()
        items = []
        for obj, supplier_name in results:
            d = self._to_dict(obj)
            d["supplier_name"] = supplier_name
            d["pay_status_text"] = "已结清" if obj.pay_status else "未结清"
            d["invoice_status_text"] = "已开票" if obj.invoice_status else "未开票"
            items.append(d)
        return items
    
    def update_amount(self, statement_id: int, statement_amount: Decimal,
                     unreceived_amount: Decimal, pay_status: bool) -> None:
        self.db.query(PurchaseStatement).filter(
            PurchaseStatement.id == statement_id
        ).update({
            "statement_amount": statement_amount,
            "unreceived_amount": unreceived_amount,
            "pay_status": pay_status
        })
        self.db.flush()
    
    def update_payment(self, statement_id: int, received_amount: Decimal,
                      unreceived_amount: Decimal, pay_status: bool) -> None:
        self.db.query(PurchaseStatement).filter(
            PurchaseStatement.id == statement_id
        ).update({
            "received_amount": received_amount,
            "unreceived_amount": unreceived_amount,
            "pay_status": pay_status
        })
        self.db.flush()
    
    def update_invoice_status(self, id: int, status: int) -> None:
        self.db.query(PurchaseStatement).filter(
            PurchaseStatement.id == id
        ).update({"invoice_status": bool(status)})
        self.db.flush()
    
    def get_total_unreceived_amount(self) -> Decimal:
        result = self.db.query(func.sum(PurchaseStatement.unreceived_amount)).filter(
            PurchaseStatement.is_deleted == False
        ).scalar()
        return result or Decimal("0.00")
    
    def _to_dict(self, obj: PurchaseStatement) -> Dict:
        return {
            "id": obj.id,
            "supplier_id": obj.supplier_id,
            "start_date": obj.start_date,
            "end_date": obj.end_date,
            "statement_amount": obj.statement_amount,
            "received_amount": obj.received_amount,
            "unreceived_amount": obj.unreceived_amount,
            "pay_status": obj.pay_status,
            "invoice_status": obj.invoice_status,
            "is_deleted": obj.is_deleted,
            "create_time": obj.create_time,
            "update_time": obj.update_time
        }
    
    def soft_delete(self, id: int) -> None:
        self.db.query(PurchaseStatement).filter(
            PurchaseStatement.id == id
        ).update({"is_deleted": True})
        self.db.flush()
    
    def update_end_date(self, id: int, end_date: datetime) -> None:
        self.db.query(PurchaseStatement).filter(
            PurchaseStatement.id == id
        ).update({"end_date": end_date})
        self.db.flush()
    
    def get_total_statement_amount_by_date(self, start_date: datetime, end_date: datetime) -> Decimal:
        """
        获取指定时间范围内的采购对账单总金额
        说明：end_date为空的记录视为本日
        """
        # 转换为date类型进行比较
        start_date_date = start_date.date()
        end_date_date = end_date.date()
        today_date = datetime.now().date()
        
        # 构建查询，处理end_date为空的情况
        from sqlalchemy import or_
        result = self.db.query(func.sum(PurchaseStatement.statement_amount)).filter(
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
        ).scalar()
        return Decimal(str(result)) if result is not None else Decimal("0.00")