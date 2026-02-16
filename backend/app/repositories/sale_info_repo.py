from typing import Optional, Dict, List
from datetime import datetime
from sqlalchemy import func, desc
from sqlalchemy.orm import Session
from app.models.sale_info import SaleInfo
from app.models.purchaser import Purchaser
from app.models.goods import Goods

class SaleInfoRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, data: Dict) -> int:
        obj = SaleInfo(**data)
        self.db.add(obj)
        self.db.flush()
        self.db.refresh(obj)
        return obj.id
    
    def get_by_id(self, id: int) -> Optional[Dict]:
        result = self.db.query(
            SaleInfo,
            Purchaser.purchaser_name,
            Goods.goods_name
        ).join(
            Purchaser, SaleInfo.purchaser_id == Purchaser.id
        ).join(
            Goods, SaleInfo.goods_id == Goods.id
        ).filter(
            SaleInfo.id == id,
            SaleInfo.is_deleted == False
        ).first()
        
        if result:
            obj, p_name, g_name = result
            d = self._to_dict(obj)
            d["purchaser_name"] = p_name
            d["goods_name"] = g_name
            return d
        return None
    
    def update(self, id: int, data: Dict) -> None:
        self.db.query(SaleInfo).filter(
            SaleInfo.id == id,
            SaleInfo.is_deleted == False
        ).update(data)
        self.db.flush()
    
    def soft_delete(self, id: int) -> None:
        self.db.query(SaleInfo).filter(SaleInfo.id == id).update({
            SaleInfo.is_deleted: True
        })
        self.db.flush()
    
    def count_by_conditions(self, id: Optional[int],
                           purchaser_id: Optional[int], 
                           product_name: Optional[str]) -> int:
        query = self.db.query(func.count(SaleInfo.id)).join(
            Goods, SaleInfo.goods_id == Goods.id
        ).filter(SaleInfo.is_deleted == False)
        
        if id:
            query = query.filter(SaleInfo.id == id)
        if purchaser_id:
            query = query.filter(SaleInfo.purchaser_id == purchaser_id)
        if product_name:
            query = query.filter(Goods.goods_name.like(f"%{product_name}%"))
        return query.scalar()
    
    def list_by_conditions(self, id: Optional[int],
                         purchaser_id: Optional[int], 
                         product_name: Optional[str],
                         sort_field: Optional[str],
                         sort_order: Optional[str],
                         offset: int, limit: int) -> List[Dict]:
        query = self.db.query(
            SaleInfo,
            Purchaser.purchaser_name,
            Goods.goods_name
        ).join(
            Purchaser, SaleInfo.purchaser_id == Purchaser.id
        ).join(
            Goods, SaleInfo.goods_id == Goods.id
        ).filter(SaleInfo.is_deleted == False)
        
        if id:
            query = query.filter(SaleInfo.id == id)
        if purchaser_id:
            query = query.filter(SaleInfo.purchaser_id == purchaser_id)
        if product_name:
            query = query.filter(Goods.goods_name.like(f"%{product_name}%"))
        
        if sort_field and hasattr(SaleInfo, sort_field):
            column = getattr(SaleInfo, sort_field)
            if sort_order == "desc":
                query = query.order_by(desc(column))
            else:
                query = query.order_by(column)
        else:
            query = query.order_by(desc(SaleInfo.sale_date))
        
        results = query.offset(offset).limit(limit).all()
        items = []
        for obj, p_name, g_name in results:
            d = self._to_dict(obj)
            d["purchaser_name"] = p_name
            d["goods_name"] = g_name
            items.append(d)
        return items
    
    def get_last_by_purchaser_and_goods(self, purchaser_id: int, goods_id: int) -> Optional[Dict]:
        obj = self.db.query(SaleInfo).filter(
            SaleInfo.purchaser_id == purchaser_id,
            SaleInfo.goods_id == goods_id,
            SaleInfo.is_deleted == False
        ).order_by(desc(SaleInfo.sale_date)).first()
        return self._to_dict(obj) if obj else None
    
    def list_by_statement(self, purchaser_id: int, statement_id: int, start_date: Optional[datetime.date] = None, end_date: Optional[datetime.date] = None) -> List[Dict]:
        # 用于对账单细则查询 - 查询该采购商在指定对账单和日期范围内的销售记录
        query = self.db.query(
            SaleInfo,
            Goods.goods_name
        ).join(
            Goods, SaleInfo.goods_id == Goods.id
        ).filter(
            SaleInfo.purchaser_id == purchaser_id,
            SaleInfo.statement_id == statement_id,
            SaleInfo.is_deleted == False
        )
        
        # 添加日期范围过滤
        if start_date:
            query = query.filter(SaleInfo.sale_date >= start_date)
        if end_date:
            query = query.filter(SaleInfo.sale_date <= end_date)
        
        results = query.order_by(SaleInfo.sale_date).all()
        
        items = []
        for obj, g_name in results:
            d = self._to_dict(obj)
            d["goods_name"] = g_name
            items.append(d)
        return items
    
    def has_records_by_purchaser(self, purchaser_id: int) -> bool:
        count = self.db.query(func.count(SaleInfo.id)).filter(
            SaleInfo.purchaser_id == purchaser_id,
            SaleInfo.is_deleted == False
        ).scalar()
        return count > 0
    
    def list_unstatemented(self, purchaser_id: Optional[int] = None) -> List[Dict]:
        # 查询无对账单的销售记录
        query = self.db.query(
            SaleInfo,
            Goods.goods_name,
            Purchaser.purchaser_name
        ).join(
            Goods, SaleInfo.goods_id == Goods.id
        ).join(
            Purchaser, SaleInfo.purchaser_id == Purchaser.id
        ).filter(
            SaleInfo.is_deleted == False,
            SaleInfo.statement_id == None
        )
        
        if purchaser_id:
            query = query.filter(SaleInfo.purchaser_id == purchaser_id)
        
        results = query.order_by(SaleInfo.sale_date).all()
        
        items = []
        for obj, g_name, p_name in results:
            d = self._to_dict(obj)
            d["goods_name"] = g_name
            d["purchaser_name"] = p_name
            items.append(d)
        return items
    
    def get_unstatemented_summary_by_purchaser(self) -> Dict[int, Dict]:
        # 按采购商分组统计无对账单的销售记录
        records = self.list_unstatemented()
        summary = {}
        
        for record in records:
            purchaser_id = record["purchaser_id"]
            if purchaser_id not in summary:
                summary[purchaser_id] = {
                    "purchaser_id": purchaser_id,
                    "purchaser_name": record["purchaser_name"],
                    "total_amount": 0.0,
                    "total_profit": 0.0,
                    "records": []
                }
            summary[purchaser_id]["total_amount"] += float(record["sale_total_price"])
            summary[purchaser_id]["total_profit"] += float(record["total_profit"])
            summary[purchaser_id]["records"].append(record)
        
        return summary
    
    def _to_dict(self, obj: SaleInfo) -> Dict:
        return {
            "id": obj.id,
            "purchaser_id": obj.purchaser_id,
            "goods_id": obj.goods_id,
            "product_spec": obj.product_spec,
            "sale_num": obj.sale_num,
            "sale_unit_price": obj.sale_unit_price,
            "sale_total_price": obj.sale_total_price,
            "trade_unit_cost": obj.trade_unit_cost,
            "unit_profit": obj.unit_profit,
            "total_profit": obj.total_profit,
            "sale_date": obj.sale_date,
            "remark": obj.remark,
            "create_by": obj.create_by,
            "is_deleted": obj.is_deleted,
            "create_time": obj.create_time,
            "update_time": obj.update_time
        }
    
    def update_statement_id_for_sales(self, statement_id: int, new_statement_id: int, start_date: datetime.date) -> None:
        """
        更新销售记录的对账单ID
        """
        self.db.query(SaleInfo).filter(
            SaleInfo.statement_id == statement_id,
            SaleInfo.sale_date >= start_date,
            SaleInfo.is_deleted == False
        ).update({"statement_id": new_statement_id})
        self.db.flush()