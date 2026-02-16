from typing import Optional, Dict, List
from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.inventory_loss import InventoryLoss
from app.models.goods import Goods

class InventoryLossRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, data: Dict) -> int:
        obj = InventoryLoss(**data)
        self.db.add(obj)
        self.db.flush()
        self.db.refresh(obj)
        return obj.id
    
    def get_by_id(self, loss_id: int) -> Optional[Dict]:
        obj = self.db.query(InventoryLoss).filter(
            InventoryLoss.id == loss_id,
            InventoryLoss.is_deleted == False
        ).first()
        return self._to_dict(obj) if obj else None
    
    def soft_delete(self, loss_id: int) -> None:
        self.db.query(InventoryLoss).filter(InventoryLoss.id == loss_id).update({
            InventoryLoss.is_deleted: True
        })
        self.db.flush()
    
    def count_by_conditions(self, id: Optional[int],
                           product_name: Optional[str],
                           start_date: Optional[datetime],
                           end_date: Optional[datetime]) -> int:
        query = self.db.query(func.count(InventoryLoss.id)).join(
            Goods, InventoryLoss.goods_id == Goods.id
        ).filter(InventoryLoss.is_deleted == False)

        if id:
            query = query.filter(InventoryLoss.id == id)
        if product_name:
            query = query.filter(Goods.goods_name.like(f"%{product_name}%"))
        if start_date:
            query = query.filter(InventoryLoss.loss_date >= start_date)
        if end_date:
            query = query.filter(InventoryLoss.loss_date <= end_date)
        return query.scalar()

    def list_by_conditions(self, id: Optional[int],
                           product_name: Optional[str],
                           start_date: Optional[datetime],
                           end_date: Optional[datetime],
                           offset: int, limit: int) -> List[Dict]:
        query = self.db.query(InventoryLoss, Goods.goods_name, Goods.product_spec).join(
            Goods, InventoryLoss.goods_id == Goods.id
        ).filter(InventoryLoss.is_deleted == False)

        if id:
            query = query.filter(InventoryLoss.id == id)
        if product_name:
            query = query.filter(Goods.goods_name.like(f"%{product_name}%"))
        if start_date:
            query = query.filter(InventoryLoss.loss_date >= start_date)
        if end_date:
            query = query.filter(InventoryLoss.loss_date <= end_date)
        
        results = query.order_by(InventoryLoss.loss_date.desc()).offset(offset).limit(limit).all()
        items = []
        for obj, goods_name, product_spec in results:
            d = self._to_dict(obj)
            d["goods_name"] = goods_name
            d["product_spec"] = product_spec
            items.append(d)
        return items
    
    def _to_dict(self, obj: InventoryLoss) -> Dict:
        return {
            "id": obj.id,
            "goods_id": obj.goods_id,
            "loss_num": obj.loss_num,
            "loss_unit_cost": obj.loss_unit_cost,
            "loss_total_cost": obj.loss_total_cost,
            "loss_date": obj.loss_date,
            "loss_reason": obj.loss_reason,
            "remark": obj.remark,
            "is_deleted": obj.is_deleted,
            "create_time": obj.create_time,
            "update_time": obj.update_time
        }