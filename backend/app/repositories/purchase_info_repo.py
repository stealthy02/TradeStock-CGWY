from typing import Optional, Dict, List
from datetime import datetime
from sqlalchemy import func, desc
from sqlalchemy.orm import Session
from app.models.purchase_info import PurchaseInfo
from app.models.supplier import Supplier
from app.models.goods import Goods

class PurchaseInfoRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, data: Dict) -> int:
        obj = PurchaseInfo(**data)
        self.db.add(obj)
        self.db.flush()
        self.db.refresh(obj)
        return obj.id
    
    def get_by_id(self, id: int) -> Optional[Dict]:
        result = self.db.query(
            PurchaseInfo, 
            Supplier.supplier_name,
            Goods.goods_name
        ).join(
            Supplier, PurchaseInfo.supplier_id == Supplier.id
        ).join(
            Goods, PurchaseInfo.goods_id == Goods.id
        ).filter(
            PurchaseInfo.id == id,
            PurchaseInfo.is_deleted == False
        ).first()
        
        if result:
            obj, s_name, g_name = result
            d = self._to_dict(obj)
            d["supplier_name"] = s_name
            d["goods_name"] = g_name
            return d
        return None
    
    def update(self, id: int, data: Dict) -> None:
        self.db.query(PurchaseInfo).filter(
            PurchaseInfo.id == id,
            PurchaseInfo.is_deleted == False
        ).update(data)
        self.db.flush()
    
    def soft_delete(self, id: int) -> None:
        self.db.query(PurchaseInfo).filter(PurchaseInfo.id == id).update({
            PurchaseInfo.is_deleted: True
        })
        self.db.flush()
    
    def count_by_conditions(self, id: Optional[int],
                           supplier_id: Optional[int], 
                           product_name: Optional[str]) -> int:
        query = self.db.query(func.count(PurchaseInfo.id)).join(
            Goods, PurchaseInfo.goods_id == Goods.id
        ).filter(PurchaseInfo.is_deleted == False)
        
        if id:
            query = query.filter(PurchaseInfo.id == id)
        if supplier_id:
            query = query.filter(PurchaseInfo.supplier_id == supplier_id)
        if product_name:
            query = query.filter(Goods.goods_name.like(f"%{product_name}%"))
        return query.scalar()
    
    def list_by_conditions(self, id: Optional[int],
                          supplier_id: Optional[int], 
                          product_name: Optional[str],
                          sort_field: Optional[str],
                          sort_order: Optional[str],
                          offset: int, limit: int) -> List[Dict]:
        query = self.db.query(
            PurchaseInfo,
            Supplier.supplier_name,
            Goods.goods_name
        ).join(
            Supplier, PurchaseInfo.supplier_id == Supplier.id
        ).join(
            Goods, PurchaseInfo.goods_id == Goods.id
        ).filter(PurchaseInfo.is_deleted == False)
        
        if id:
            query = query.filter(PurchaseInfo.id == id)
        if supplier_id:
            query = query.filter(PurchaseInfo.supplier_id == supplier_id)
        if product_name:
            query = query.filter(Goods.goods_name.like(f"%{product_name}%"))
        
        # 排序
        if sort_field and hasattr(PurchaseInfo, sort_field):
            column = getattr(PurchaseInfo, sort_field)
            if sort_order == "desc":
                query = query.order_by(desc(column))
            else:
                query = query.order_by(column)
        else:
            query = query.order_by(desc(PurchaseInfo.purchase_date))
        
        results = query.offset(offset).limit(limit).all()
        items = []
        for obj, s_name, g_name in results:
            d = self._to_dict(obj)
            d["supplier_name"] = s_name
            d["goods_name"] = g_name
            items.append(d)
        return items
    
    def get_last_by_supplier_and_goods(self, supplier_id: int, goods_id: int) -> Optional[Dict]:
        obj = self.db.query(PurchaseInfo).filter(
            PurchaseInfo.supplier_id == supplier_id,
            PurchaseInfo.goods_id == goods_id,
            PurchaseInfo.is_deleted == False
        ).order_by(desc(PurchaseInfo.purchase_date)).first()
        return self._to_dict(obj) if obj else None
    
    def list_by_statement(self, supplier_id: int, statement_id: int, start_date: Optional[datetime.date] = None, end_date: Optional[datetime.date] = None) -> List[Dict]:
        # 用于对账单细则查询 - 查询该供货商在指定对账单和日期范围内的采购记录
        query = self.db.query(
            PurchaseInfo,
            Goods.goods_name
        ).join(
            Goods, PurchaseInfo.goods_id == Goods.id
        ).filter(
            PurchaseInfo.supplier_id == supplier_id,
            PurchaseInfo.statement_id == statement_id,
            PurchaseInfo.is_deleted == False
        )
        
        # 添加日期范围过滤
        if start_date:
            query = query.filter(PurchaseInfo.purchase_date >= start_date)
        if end_date:
            query = query.filter(PurchaseInfo.purchase_date <= end_date)
        
        results = query.order_by(PurchaseInfo.purchase_date).all()
        
        items = []
        for obj, g_name in results:
            d = self._to_dict(obj)
            d["goods_name"] = g_name
            items.append(d)
        return items
    
    def has_records_by_supplier(self, supplier_id: int) -> bool:
        count = self.db.query(func.count(PurchaseInfo.id)).filter(
            PurchaseInfo.supplier_id == supplier_id,
            PurchaseInfo.is_deleted == False
        ).scalar()
        return count > 0
    
    def list_unstatemented(self, supplier_id: Optional[int] = None) -> List[Dict]:
        # 查询无对账单的采购记录
        query = self.db.query(
            PurchaseInfo,
            Goods.goods_name,
            Supplier.supplier_name
        ).join(
            Goods, PurchaseInfo.goods_id == Goods.id
        ).join(
            Supplier, PurchaseInfo.supplier_id == Supplier.id
        ).filter(
            PurchaseInfo.is_deleted == False,
            PurchaseInfo.statement_id == None
        )
        
        if supplier_id:
            query = query.filter(PurchaseInfo.supplier_id == supplier_id)
        
        results = query.order_by(PurchaseInfo.purchase_date).all()
        
        items = []
        for obj, g_name, s_name in results:
            d = self._to_dict(obj)
            d["goods_name"] = g_name
            d["supplier_name"] = s_name
            items.append(d)
        return items
    
    def get_unstatemented_summary_by_supplier(self) -> Dict[int, Dict]:
        # 按供货商分组统计无对账单的采购记录
        records = self.list_unstatemented()
        summary = {}
        
        for record in records:
            supplier_id = record["supplier_id"]
            if supplier_id not in summary:
                summary[supplier_id] = {
                    "supplier_id": supplier_id,
                    "supplier_name": record["supplier_name"],
                    "total_amount": 0.0,
                    "records": []
                }
            summary[supplier_id]["total_amount"] += float(record["purchase_total_price"])
            summary[supplier_id]["records"].append(record)
        
        return summary
    
    def _to_dict(self, obj: PurchaseInfo) -> Dict:
        return {
            "id": obj.id,
            "supplier_id": obj.supplier_id,
            "goods_id": obj.goods_id,
            "product_spec": obj.product_spec,
            "purchase_num": obj.purchase_num,
            "purchase_unit_price": obj.purchase_unit_price,
            "purchase_total_price": obj.purchase_total_price,
            "purchase_date": obj.purchase_date,
            "remark": obj.remark,
            "create_by": obj.create_by,
            "is_deleted": obj.is_deleted,
            "create_time": obj.create_time,
            "update_time": obj.update_time
        }
    
    def update_statement_id_for_purchases(self, statement_id: int, new_statement_id: int, start_date: datetime.date) -> None:
        """
        更新采购记录的对账单ID
        """
        self.db.query(PurchaseInfo).filter(
            PurchaseInfo.statement_id == statement_id,
            PurchaseInfo.purchase_date >= start_date,
            PurchaseInfo.is_deleted == False
        ).update({"statement_id": new_statement_id})
        self.db.flush()