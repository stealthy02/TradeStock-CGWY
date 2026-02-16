from typing import Optional, Dict, List
from decimal import Decimal
from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.operating_expense import OperatingExpense

class OperatingExpenseRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, data: Dict) -> int:
        obj = OperatingExpense(**data)
        self.db.add(obj)
        self.db.flush()
        self.db.refresh(obj)
        return obj.id
    
    def get_by_id(self, expense_id: int) -> Optional[Dict]:
        obj = self.db.query(OperatingExpense).filter(
            OperatingExpense.id == expense_id,
            OperatingExpense.is_deleted == False
        ).first()
        return self._to_dict(obj) if obj else None
    
    def update(self, expense_id: int, data: Dict) -> None:
        self.db.query(OperatingExpense).filter(
            OperatingExpense.id == expense_id,
            OperatingExpense.is_deleted == False
        ).update(data)
        self.db.flush()
    
    def soft_delete(self, expense_id: int) -> None:
        self.db.query(OperatingExpense).filter(OperatingExpense.id == expense_id).update({
            OperatingExpense.is_deleted: True
        })
        self.db.flush()
    
    def count_by_conditions(self, desc: Optional[str], expense_type: Optional[str],
                           start_date: Optional[datetime], end_date: Optional[datetime]) -> int:
        query = self.db.query(func.count(OperatingExpense.id)).filter(
            OperatingExpense.is_deleted == False
        )
        if desc:
            query = query.filter(OperatingExpense.expense_desc.like(f"%{desc}%"))
        if expense_type:
            query = query.filter(OperatingExpense.expense_type == expense_type)
        if start_date:
            query = query.filter(OperatingExpense.expense_date >= start_date)
        if end_date:
            query = query.filter(OperatingExpense.expense_date <= end_date)
        return query.scalar()
    
    def list_by_conditions(self, desc: Optional[str], expense_type: Optional[str],
                          start_date: Optional[datetime], end_date: Optional[datetime],
                          offset: int, limit: int) -> List[Dict]:
        query = self.db.query(OperatingExpense).filter(OperatingExpense.is_deleted == False)
        
        if desc:
            query = query.filter(OperatingExpense.expense_desc.like(f"%{desc}%"))
        if expense_type:
            query = query.filter(OperatingExpense.expense_type == expense_type)
        if start_date:
            query = query.filter(OperatingExpense.expense_date >= start_date)
        if end_date:
            query = query.filter(OperatingExpense.expense_date <= end_date)
        
        results = query.order_by(OperatingExpense.expense_date.desc()).offset(offset).limit(limit).all()
        items = []
        for obj in results:
            d = self._to_dict(obj)
            items.append(d)
        return items
    
    def get_total_amount_by_date(self, start_date: datetime, end_date: datetime) -> Decimal:
        result = self.db.query(func.sum(OperatingExpense.expense_amount)).filter(
            OperatingExpense.is_deleted == False,
            OperatingExpense.expense_date >= start_date,
            OperatingExpense.expense_date <= end_date
        ).scalar()
        return Decimal(str(result)) if result is not None else Decimal("0.00")
    
    def _to_dict(self, obj: OperatingExpense) -> Dict:
        return {
            "id": obj.id,
            "expense_desc": obj.expense_desc,
            "expense_type": obj.expense_type,
            "expense_amount": obj.expense_amount,
            "expense_date": obj.expense_date,
            "remark": obj.remark,
            "is_deleted": obj.is_deleted,
            "create_time": obj.create_time,
            "update_time": obj.update_time
        }