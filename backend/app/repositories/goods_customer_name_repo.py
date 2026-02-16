from typing import Optional, Dict
from sqlalchemy.orm import Session
from app.models.goods_customer_name import GoodsCustomerName

class GoodsCustomerNameRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def save_or_update(self, goods_id: int, purchaser_id: int, customer_name: str) -> None:
        existing = self.db.query(GoodsCustomerName).filter(
            GoodsCustomerName.goods_id == goods_id,
            GoodsCustomerName.purchaser_id == purchaser_id,
            GoodsCustomerName.is_deleted == False
        ).first()
        
        if existing:
            existing.customer_goods_name = customer_name
        else:
            new_obj = GoodsCustomerName(
                goods_id=goods_id,
                purchaser_id=purchaser_id,
                customer_goods_name=customer_name
            )
            self.db.add(new_obj)
        self.db.flush()
    
    def get_customer_name(self, goods_id: int, purchaser_id: int) -> Optional[str]:
        obj = self.db.query(GoodsCustomerName).filter(
            GoodsCustomerName.goods_id == goods_id,
            GoodsCustomerName.purchaser_id == purchaser_id,
            GoodsCustomerName.is_deleted == False
        ).first()
        return obj.customer_goods_name if obj else None
    
    def get_by_goods_and_purchaser(self, goods_id: int, purchaser_id: int) -> Optional[Dict]:
        obj = self.db.query(GoodsCustomerName).filter(
            GoodsCustomerName.goods_id == goods_id,
            GoodsCustomerName.purchaser_id == purchaser_id,
            GoodsCustomerName.is_deleted == False
        ).first()
        
        if obj:
            return {
                "id": obj.id,
                "goods_id": obj.goods_id,
                "purchaser_id": obj.purchaser_id,
                "customer_goods_name": obj.customer_goods_name,
                "update_time": obj.update_time
            }
        return None