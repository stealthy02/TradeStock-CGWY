from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.models.sale_receipt import SaleReceipt

class SaleReceiptRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, data: Dict) -> int:
        obj = SaleReceipt(**data)
        self.db.add(obj)
        self.db.flush()
        self.db.refresh(obj)
        return obj.id
    
    def list_by_statement(self, statement_id: int) -> List[Dict]:
        objs = self.db.query(SaleReceipt).filter(
            SaleReceipt.statement_id == statement_id,
            SaleReceipt.is_deleted == False
        ).order_by(SaleReceipt.receipt_date.desc()).all()
        return [self._to_dict(obj) for obj in objs]
    
    def _to_dict(self, obj: SaleReceipt) -> Dict:
        return {
            "id": obj.id,
            "statement_id": obj.statement_id,
            "receipt_date": obj.receipt_date,
            "receipt_amount": obj.receipt_amount,
            "receipt_method": obj.receipt_method,
            "remark": obj.remark,
            "is_deleted": obj.is_deleted,
            "create_time": obj.create_time,
            "update_time": obj.update_time
        }
    
    def soft_delete(self, receipt_id: int) -> bool:
        """
        软删除收款记录
        """
        result = self.db.query(SaleReceipt).filter(
            SaleReceipt.id == receipt_id,
            SaleReceipt.is_deleted == False
        ).update({"is_deleted": True})
        self.db.flush()
        return result > 0
    
    def get_by_id(self, receipt_id: int) -> Optional[SaleReceipt]:
        """
        根据ID获取收款记录
        """
        return self.db.query(SaleReceipt).filter(
            SaleReceipt.id == receipt_id,
            SaleReceipt.is_deleted == False
        ).first()
    
    def get_total_received_by_statement(self, statement_id: int):
        """
        获取对账单的总收款金额
        """
        from sqlalchemy import func
        from decimal import Decimal
        result = self.db.query(func.sum(SaleReceipt.receipt_amount)).filter(
            SaleReceipt.statement_id == statement_id,
            SaleReceipt.is_deleted == False
        ).scalar()
        return result or Decimal("0.00")