from typing import Dict, List, Optional
from decimal import Decimal
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.purchase_payment import PurchasePayment

class PurchasePaymentRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, data: Dict) -> int:
        obj = PurchasePayment(**data)
        self.db.add(obj)
        self.db.flush()
        self.db.refresh(obj)
        return obj.id
    
    def list_by_statement(self, statement_id: int) -> List[Dict]:
        objs = self.db.query(PurchasePayment).filter(
            PurchasePayment.statement_id == statement_id,
            PurchasePayment.is_deleted == False
        ).order_by(PurchasePayment.payment_date.desc()).all()
        return [self._to_dict(obj) for obj in objs]
    
    def get_total_received_by_statement(self, statement_id: int) -> Decimal:
        result = self.db.query(func.sum(PurchasePayment.payment_amount)).filter(
            PurchasePayment.statement_id == statement_id,
            PurchasePayment.is_deleted == False
        ).scalar()
        return result or Decimal("0.00")
    
    def _to_dict(self, obj: PurchasePayment) -> Dict:
        return {
            "id": obj.id,
            "statement_id": obj.statement_id,
            "payment_date": obj.payment_date,
            "payment_amount": obj.payment_amount,
            "payment_method": obj.payment_method,
            "remark": obj.remark,
            "is_deleted": obj.is_deleted,
            "create_time": obj.create_time,
            "update_time": obj.update_time
        }
    
    def soft_delete(self, payment_id: int) -> bool:
        """
        软删除付款记录
        """
        result = self.db.query(PurchasePayment).filter(
            PurchasePayment.id == payment_id,
            PurchasePayment.is_deleted == False
        ).update({"is_deleted": True})
        self.db.flush()
        return result > 0
    
    def get_by_id(self, payment_id: int) -> Optional[PurchasePayment]:
        """
        根据ID获取付款记录
        """
        return self.db.query(PurchasePayment).filter(
            PurchasePayment.id == payment_id,
            PurchasePayment.is_deleted == False
        ).first()