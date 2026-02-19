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
        """创建库存流动记录，支持非顺序录入
        
        逻辑：
        1. 筛选该商品的所有库存流动记录
        2. 找到所有日期大于新创建记录日期的记录
        3. 在这些记录中，找到离新创建日期最近的记录的变动前数量，作为新记录的变动前数量
        4. 根据变动量计算新记录的变动后数量
        5. 更新所有日期比新创建日期靠后的数据，调整它们的变动前和变动后数量
        """
        goods_id = data['goods_id']
        oper_time = data['oper_time']
        change_num = data['change_num']
        
        # 找到所有日期大于新创建记录日期的记录
        future_records = self.db.query(InventoryFlow).filter(
            InventoryFlow.goods_id == goods_id,
            InventoryFlow.oper_time > oper_time
        ).order_by(InventoryFlow.oper_time).all()
        
        # 计算新记录的stock_before和stock_after
        if future_records:
            # 找到离新创建日期最近的记录的变动前数量
            nearest_record = future_records[0]
            stock_before = nearest_record.stock_before
        else:
            # 如果没有未来记录，使用传入的stock_before
            stock_before = data.get('stock_before', 0)
        
        stock_after = stock_before + change_num
        
        # 创建新记录
        new_data = data.copy()
        new_data['stock_before'] = stock_before
        new_data['stock_after'] = stock_after
        
        obj = InventoryFlow(**new_data)
        self.db.add(obj)
        self.db.flush()
        self.db.refresh(obj)
        
        # 更新所有日期比新创建日期靠后的数据
        for record in future_records:
            record.stock_before += change_num
            record.stock_after += change_num
        
        self.db.flush()
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
        objs = query.order_by(desc(InventoryFlow.oper_time), desc(InventoryFlow.id)).offset(offset).limit(limit).all()
        return [self._to_dict(obj) for obj in objs]
    
    def delete_by_biz(self, oper_type: int, biz_id: int) -> None:
        """删除库存流动记录，支持非顺序操作
        
        逻辑：
        1. 找到要删除的记录
        2. 获取记录的goods_id、oper_time和change_num
        3. 找到所有日期大于该记录日期的记录
        4. 对这些记录的stock_before和stock_after进行逆向变动（即减去change_num）
        5. 删除原记录
        """
        # 先找到要删除的记录，获取相关信息
        records_to_delete = self.db.query(InventoryFlow).filter(
            InventoryFlow.oper_type == oper_type,
            InventoryFlow.biz_id == biz_id
        ).all()
        
        for record in records_to_delete:
            goods_id = record.goods_id
            oper_time = record.oper_time
            change_num = record.change_num
            
            # 找到所有日期大于该记录日期的记录
            future_records = self.db.query(InventoryFlow).filter(
                InventoryFlow.goods_id == goods_id,
                InventoryFlow.oper_time > oper_time
            ).all()
            
            # 对这些记录的stock_before和stock_after进行逆向变动
            for future_record in future_records:
                future_record.stock_before -= change_num
                future_record.stock_after -= change_num
        
        # 删除原记录
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
        
        objs = query.order_by(desc(InventoryFlow.oper_time), desc(InventoryFlow.id)).offset(offset).limit(limit).all()
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