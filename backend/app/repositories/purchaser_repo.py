from typing import Optional, Dict, List
from sqlalchemy import func
from sqlalchemy.orm import Session
# 新增：兼容Pydantic模型（核心修改）
from pydantic import BaseModel
from app.models.purchaser import Purchaser
from app.models.sale_info import SaleInfo

class PurchaserRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, purchaser_id: int) -> Optional[Dict]:
        obj = self.db.query(Purchaser).filter(
            Purchaser.id == purchaser_id,
            Purchaser.is_deleted == False
        ).first()
        return self._to_dict(obj) if obj else None
    
    def get_by_name(self, name: str) -> Optional[Dict]:
        obj = self.db.query(Purchaser).filter(
            Purchaser.purchaser_name == name,
            Purchaser.is_deleted == False
        ).first()
        return self._to_dict(obj) if obj else None
    
    # 核心修改：参数注解改为BaseModel（兼容Pydantic模型）+ 模型转字典
    def create(self, data: BaseModel) -> int:
        # Pydantic v2用model_dump()，v1用dict()，这里用主流的v2写法
        obj = Purchaser(**data.model_dump())
        self.db.add(obj)
        self.db.flush()
        self.db.refresh(obj)
        return obj.id
    
    def get_by_name_include_deleted(self, name: str) -> Optional[Purchaser]:
        return self.db.query(Purchaser).filter(
            Purchaser.purchaser_name == name
        ).first()

    # 新增方法2：解除软删标记（单独抽离，复用性强）
    def undo_soft_delete(self, purchaser_id: int) -> None:
        self.db.query(Purchaser).filter(
            Purchaser.id == purchaser_id
        ).update({"is_deleted": False})
        self.db.flush()

    # 【修复1】参数注解 Dict → BaseModel，与create保持一致，匹配实际传参（Pydantic模型）
    def update(self, purchaser_id: int, data: BaseModel) -> None:
        update_data = data.model_dump(exclude_unset=True) if isinstance(data, BaseModel) else data
        self.db.query(Purchaser).filter(
            Purchaser.id == purchaser_id,
            Purchaser.is_deleted == False
        ).update(update_data)  # 直接使用处理后的update_data
        self.db.flush()
    
    def soft_delete(self, purchaser_id: int) -> None:
        self.db.query(Purchaser).filter(
            Purchaser.id == purchaser_id
        ).update({"is_deleted": True})
        self.db.flush()
    
    def count_by_conditions(self, name: Optional[str], phone: Optional[str]) -> int:
        query = self.db.query(func.count(Purchaser.id)).filter(Purchaser.is_deleted == False)
        if name:
            query = query.filter(Purchaser.purchaser_name.like(f"%{name}%"))
        if phone:
            query = query.filter(Purchaser.contact_phone.like(f"%{phone}%"))
        return query.scalar()
    
    def list_by_conditions(self, name: Optional[str], phone: Optional[str], 
                          offset: int, limit: int) -> List[Dict]:
        query = self.db.query(Purchaser).filter(Purchaser.is_deleted == False)
        if name:
            query = query.filter(Purchaser.purchaser_name.like(f"%{name}%"))
        if phone:
            query = query.filter(Purchaser.contact_phone.like(f"%{phone}%"))
        
        objs = query.order_by(Purchaser.create_time.desc()).offset(offset).limit(limit).all()
        return [self._to_dict(obj) for obj in objs]
    
    def select_by_keyword(self, keyword: Optional[str], limit: int) -> List[Dict]:
        query = self.db.query(Purchaser.id, Purchaser.purchaser_name, Purchaser.create_time).distinct().filter(
            Purchaser.is_deleted == False
        )
        if keyword:
            query = query.filter(Purchaser.purchaser_name.like(f"%{keyword}%"))
        
        objs = query.order_by(Purchaser.create_time.desc()).limit(limit).all()
        return [{"id": obj.id, "purchaser_name": obj.purchaser_name} for obj in objs]
    
    def has_sale_records(self, purchaser_id: int) -> bool:
        count = self.db.query(func.count(SaleInfo.id)).filter(
            SaleInfo.purchaser_id == purchaser_id,
            SaleInfo.is_deleted == False
        ).scalar()
        return count > 0
    
    def _to_dict(self, obj: Purchaser) -> Dict:
        return {
            "id": obj.id,
            "purchaser_name": obj.purchaser_name,
            "contact_person": obj.contact_person,
            "contact_phone": obj.contact_phone,
            "company_address": obj.company_address,
            "receive_address": obj.receive_address,
            "bank_name": obj.bank_name,
            "bank_account": obj.bank_account,
            "tax_no": obj.tax_no,
            "avatar_url": obj.avatar_url,
            "remark": obj.remark,
            "is_deleted": obj.is_deleted,
            "create_time": obj.create_time,
            "update_time": obj.update_time
        }