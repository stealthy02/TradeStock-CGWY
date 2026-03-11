from typing import Optional, Dict, List
from sqlalchemy import func, or_
from sqlalchemy.orm import Session
# 新增：兼容Pydantic模型（核心修改）
from pydantic import BaseModel
from app.models.supplier import Supplier
from app.models.purchase_info import PurchaseInfo

class SupplierRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, supplier_id: int) -> Optional[Dict]:
        obj = self.db.query(Supplier).filter(
            Supplier.id == supplier_id,
            Supplier.is_deleted == False
        ).first()
        return self._to_dict(obj) if obj else None
    
    # 【规范1】统一返回注解风格：Supplier | None → Optional[Supplier]，兼容低版本Python
    def get_by_name_include_deleted(self, name: str) -> Optional[Supplier]:
        return self.db.query(Supplier).filter(
            Supplier.supplier_name == name
        ).first()

    # 新增方法2：解除软删标记（单独抽离，复用性强）
    def undo_soft_delete(self, supplier_id: int) -> None:
        self.db.query(Supplier).filter(
            Supplier.id == supplier_id
        ).update({"is_deleted": False})
        self.db.flush()

    def get_by_name(self, name: str) -> Optional[Dict]:
        obj = self.db.query(Supplier).filter(
            Supplier.supplier_name == name,
            Supplier.is_deleted == False
        ).first()
        return self._to_dict(obj) if obj else None
    
    # 【修复1】参数注解 Dict → BaseModel，兼容Pydantic模型（和采购商create保持一致）
    def create(self, data: BaseModel) -> int:
        # 【修复2】Pydantic模型转字典解包，否则直接传data会触发解包错误
        obj = Supplier(**data.model_dump())
        self.db.add(obj)
        self.db.flush()
        self.db.refresh(obj)
        return obj.id
    
    # 【修复3】参数注解 Dict → BaseModel，匹配实际传参（Pydantic的SupplierUpdate模型）
    def update(self, supplier_id: int, data: BaseModel) -> None:
        update_data = data.model_dump(exclude_unset=True) if isinstance(data, BaseModel) else data
        self.db.query(Supplier).filter(
            Supplier.id == supplier_id,
            Supplier.is_deleted == False
        # 【修复4】核心！模型转字典+exclude_unset=True，避免items()错误+误更新空字段
        ).update(update_data)
        self.db.flush()
    
    def soft_delete(self, supplier_id: int) -> None:
        self.db.query(Supplier).filter(
            Supplier.id == supplier_id
        ).update({"is_deleted": True})
        self.db.flush()
    
    def count_by_conditions(self, name: Optional[str], phone: Optional[str]) -> int:
        query = self.db.query(func.count(Supplier.id)).filter(Supplier.is_deleted == False)
        if name:
            query = query.filter(Supplier.supplier_name.like(f"%{name}%"))
        if phone:
            query = query.filter(Supplier.contact_phone.like(f"%{phone}%"))
        return query.scalar()
    
    def list_by_conditions(self, name: Optional[str], phone: Optional[str], 
                          offset: int, limit: int) -> List[Dict]:
        query = self.db.query(Supplier).filter(Supplier.is_deleted == False)
        if name:
            query = query.filter(Supplier.supplier_name.like(f"%{name}%"))
        if phone:
            query = query.filter(Supplier.contact_phone.like(f"%{phone}%"))
        
        objs = query.order_by(Supplier.create_time.desc()).offset(offset).limit(limit).all()
        return [self._to_dict(obj) for obj in objs]
    
    def select_by_keyword(self, keyword: Optional[str], limit: int) -> List[Dict]:
        query = self.db.query(Supplier.id, Supplier.supplier_name, Supplier.create_time).distinct().filter(
            Supplier.is_deleted == False
        )
        if keyword:
            query = query.filter(Supplier.supplier_name.like(f"%{keyword}%"))
        
        objs = query.order_by(Supplier.create_time.desc()).limit(limit).all()
        return [{"id": obj.id, "supplier_name": obj.supplier_name} for obj in objs]
    
    def has_purchase_records(self, supplier_id: int) -> bool:
        count = self.db.query(func.count(PurchaseInfo.id)).filter(
            PurchaseInfo.supplier_id == supplier_id,
            PurchaseInfo.is_deleted == False
        ).scalar()
        return count > 0
    
    def _to_dict(self, obj: Supplier) -> Dict:
        return {
            "id": obj.id,
            "supplier_name": obj.supplier_name,
            "contact_person": obj.contact_person,
            "contact_phone": obj.contact_phone,
            "company_address": obj.company_address,
            "bank_name": obj.bank_name,
            "bank_account": obj.bank_account,
            "tax_no": obj.tax_no,
            "avatar_url": obj.avatar_url,
            "remark": obj.remark,
            "is_deleted": obj.is_deleted,
            "create_time": obj.create_time,
            "update_time": obj.update_time
        }