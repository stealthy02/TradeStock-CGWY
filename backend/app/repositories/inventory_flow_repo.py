from typing import Optional
from typing import Dict, List
from datetime import datetime
from sqlalchemy import func, desc
from sqlalchemy.orm import Session
from app.models.inventory_flow import InventoryFlow

class InventoryFlowRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, data: Dict) -> int:
        obj = InventoryFlow(**data)
        self.db.add(obj)
        self.db.flush()
        self.db.refresh(obj)
        return obj.id
    
    def count_by_goods_and_date(self, goods_id: int, start_date: datetime = None, end_date: datetime = None) -> int:
        query = self.db.query(func.count(InventoryFlow.id)).filter(
            InventoryFlow.goods_id == goods_id
        )
        if start_date:
            query = query.filter(InventoryFlow.oper_time >= start_date)
        if end_date:
            query = query.filter(InventoryFlow.oper_time <= end_date)
        return query.scalar()
    
    def list_by_goods_and_date(self, goods_id: int, start_date: datetime = None, 
                               end_date: datetime = None, offset: int = 0, limit: int = 10) -> List[Dict]:
        query = self.db.query(InventoryFlow).filter(
            InventoryFlow.goods_id == goods_id
        )
        if start_date:
            query = query.filter(InventoryFlow.oper_time >= start_date)
        if end_date:
            query = query.filter(InventoryFlow.oper_time <= end_date)
        objs = query.order_by(desc(InventoryFlow.oper_time)).offset(offset).limit(limit).all()
        return [self._to_dict(obj) for obj in objs]
    
    def delete_by_biz(self, oper_type: int, biz_id: int) -> None:
        """修改业务记录时删除旧流动记录"""
        self.db.query(InventoryFlow).filter(
            InventoryFlow.oper_type == oper_type,
            InventoryFlow.biz_id == biz_id
        ).delete()
        self.db.flush()
    
    def list_by_conditions(self, goods_id: Optional[int], oper_type: Optional[int],
                          start_date: datetime, end_date: datetime, 
                          offset: int, limit: int) -> List[Dict]:
        query = self.db.query(InventoryFlow)
        if goods_id:
            query = query.filter(InventoryFlow.goods_id == goods_id)
        if oper_type:
            query = query.filter(InventoryFlow.oper_type == oper_type)
        if start_date:
            query = query.filter(InventoryFlow.oper_time >= start_date)
        if end_date:
            query = query.filter(InventoryFlow.oper_time <= end_date)
        
        objs = query.order_by(desc(InventoryFlow.oper_time)).offset(offset).limit(limit).all()
        return [self._to_dict(obj) for obj in objs]
    
    def _to_dict(self, obj: InventoryFlow) -> Dict:
        return {
            "id": obj.id,
            "goods_id": obj.goods_id,
            "oper_type": obj.oper_type,
            "biz_id": obj.biz_id,
            "change_num": obj.change_num,
            "stock_before": obj.stock_before,
            "stock_after": obj.stock_after,
            "oper_time": obj.oper_time,
            "oper_source": obj.oper_source
        }