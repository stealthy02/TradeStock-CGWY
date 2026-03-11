from typing import Optional
from typing import Dict, List
from datetime import datetime
from decimal import Decimal
from sqlalchemy import func, desc, or_, and_
from sqlalchemy.orm import Session
from app.models.inventory_flow import InventoryFlow

class InventoryFlowRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, data: Dict) -> int:
        """创建库存流动记录，支持非顺序录入

        逻辑：
        1. 筛选该商品的所有库存流动记录
        2. 找到该时间点之前的最后一条记录（包括时间相同但ID更小的），取其变动后数量作为新记录的变动前数量
        3. 如果没有历史记录，则查找该时间点之后的最早记录，取其变动前数量
        4. 根据变动量计算新记录的变动后数量
        5. 更新所有时间点比新创建记录靠后的数据（包括时间相同但ID更大的），调整它们的变动前和变动后数量
        """
        goods_id = data['goods_id']
        oper_time = data['oper_time']
        change_num = Decimal(str(data['change_num']))

        # 先插入新记录获取ID，用于后续比较
        temp_data = data.copy()
        temp_data['stock_before'] = 0
        temp_data['stock_after'] = 0
        temp_obj = InventoryFlow(**temp_data)
        self.db.add(temp_obj)
        self.db.flush()
        self.db.refresh(temp_obj)
        new_id = temp_obj.id

        # 1. 查找该时间点之前的最后一条记录（时间 < 新记录时间，或者时间相同但ID < 新记录ID）
        prev_record = self.db.query(InventoryFlow).filter(
            InventoryFlow.goods_id == goods_id,
            InventoryFlow.id != new_id,
            or_(
                InventoryFlow.oper_time < oper_time,
                and_(
                    InventoryFlow.oper_time == oper_time,
                    InventoryFlow.id < new_id
                )
            )
        ).order_by(desc(InventoryFlow.oper_time), desc(InventoryFlow.id)).first()

        if prev_record:
            stock_before = prev_record.stock_after
        else:
            # 2. 如果没有历史记录，查找该时间点之后的最早记录
            next_record = self.db.query(InventoryFlow).filter(
                InventoryFlow.goods_id == goods_id,
                InventoryFlow.id != new_id,
                or_(
                    InventoryFlow.oper_time > oper_time,
                    and_(
                        InventoryFlow.oper_time == oper_time,
                        InventoryFlow.id > new_id
                    )
                )
            ).order_by(InventoryFlow.oper_time, InventoryFlow.id).first()

            if next_record:
                stock_before = next_record.stock_before
            else:
                stock_before = data.get('stock_before', 0)

        # 3. 找到所有时间点比新创建记录靠后的记录
        future_records = self.db.query(InventoryFlow).filter(
            InventoryFlow.goods_id == goods_id,
            InventoryFlow.id != new_id,
            or_(
                InventoryFlow.oper_time > oper_time,
                and_(
                    InventoryFlow.oper_time == oper_time,
                    InventoryFlow.id > new_id
                )
            )
        ).order_by(InventoryFlow.oper_time, InventoryFlow.id).all()

        stock_after = stock_before + change_num

        # 更新新记录的stock_before和stock_after
        temp_obj.stock_before = stock_before
        temp_obj.stock_after = stock_after
        self.db.flush()

        # 更新所有时间点比新创建记录靠后的数据
        for record in future_records:
            record.stock_before += change_num
            record.stock_after += change_num

        self.db.flush()
        return new_id
    
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

        # 定义业务类型优先级映射：采购(1) > 报损(3) > 销售(2)
        from sqlalchemy import case
        priority_case = case(
            (InventoryFlow.oper_type == 1, 1),  # 采购优先级最高
            (InventoryFlow.oper_type == 3, 2),  # 报损次之
            (InventoryFlow.oper_type == 2, 3),  # 销售最低
            else_=4  # 其他类型
        )

        objs = query.order_by(desc(InventoryFlow.oper_time), priority_case.desc(), desc(InventoryFlow.id)).offset(offset).limit(limit).all()
        return [self._to_dict(obj) for obj in objs]
    
    def delete_by_biz(self, oper_type: int, biz_id: int) -> None:
        """删除库存流动记录，支持非顺序操作
        
        逻辑：
        1. 找到要删除的记录
        2. 获取记录的goods_id、oper_time和change_num
        3. 找到所有日期大于该记录日期的记录（包括时间相同但ID更大的）
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
            record_id = record.id
            
            # 找到所有日期大于该记录日期的记录（包括时间相同但ID更大的）
            future_records = self.db.query(InventoryFlow).filter(
                InventoryFlow.goods_id == goods_id,
                InventoryFlow.id != record_id,
                or_(
                    InventoryFlow.oper_time > oper_time,
                    and_(
                        InventoryFlow.oper_time == oper_time,
                        InventoryFlow.id > record_id
                    )
                )
            ).order_by(InventoryFlow.oper_time, InventoryFlow.id).all()
            
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

        # 定义业务类型优先级映射：采购(1) > 报损(3) > 销售(2)
        from sqlalchemy import case
        priority_case = case(
            (InventoryFlow.oper_type == 1, 1),  # 采购优先级最高
            (InventoryFlow.oper_type == 3, 2),  # 报损次之
            (InventoryFlow.oper_type == 2, 3),  # 销售最低
            else_=4  # 其他类型
        )

        objs = query.order_by(desc(InventoryFlow.oper_time), priority_case.desc(), desc(InventoryFlow.id)).offset(offset).limit(limit).all()
        return [self._to_dict(obj) for obj in objs]
    
    def get_stock_state_at_date(self, goods_id: int, target_date: datetime) -> Optional[Dict]:
        """
        获取指定日期点的库存状态
        
        逻辑：
        1. 查询该商品日期小于等于target_date的记录
        2. 取日期最靠后的一条记录
        3. 返回该记录的操作后库存和当时的单位成本
        
        Args:
            goods_id: 商品ID
            target_date: 目标日期
            
        Returns:
            Optional[Dict]: 包含stock_num和unit_cost的字典，如果没有记录则返回None
        """
        record = self.db.query(InventoryFlow).filter(
            InventoryFlow.goods_id == goods_id,
            InventoryFlow.oper_time < target_date
        ).order_by(desc(InventoryFlow.oper_time), desc(InventoryFlow.id)).first()
        
        if record:
            return {
                "stock_num": record.stock_after,
                "unit_cost": float(record.stock_unit_cost) if record.stock_unit_cost else 0.00
            }
        return None
    
    def list_after_date(self, goods_id: int, start_date: datetime) -> List[InventoryFlow]:
        """
        获取指定日期之后的所有库存流动记录
        
        Args:
            goods_id: 商品ID
            start_date: 开始日期（不包含该日期）
            
        Returns:
            List[InventoryFlow]: 按时间升序排列的记录列表，日期相同时按业务类型优先级排序（采购 > 报损 > 销售）
        """
        # 定义业务类型优先级映射：采购(1) > 报损(3) > 销售(2)
        # 使用case语句实现优先级排序
        from sqlalchemy import case
        priority_case = case(
            (InventoryFlow.oper_type == 1, 1),  # 采购优先级最高
            (InventoryFlow.oper_type == 3, 2),  # 报损次之
            (InventoryFlow.oper_type == 2, 3),  # 销售最低
            else_=4  # 其他类型
        )
        
        return self.db.query(InventoryFlow).filter(
            InventoryFlow.goods_id == goods_id,
            InventoryFlow.oper_time >= start_date
        ).order_by(InventoryFlow.oper_time, priority_case, InventoryFlow.id).all()
    
    def update_stock_unit_cost(self, flow_id: int, unit_cost: float) -> None:
        """更新库存流动记录的单位成本"""
        self.db.query(InventoryFlow).filter(
            InventoryFlow.id == flow_id
        ).update({
            "stock_unit_cost": unit_cost
        })
        self.db.flush()

    def _to_dict(self, obj: InventoryFlow) -> Dict:
        return {
            "id": obj.id,
            "goods_id": obj.goods_id,
            "oper_type": obj.oper_type,
            "biz_id": obj.biz_id,
            "change_num": obj.change_num,
            "stock_before": obj.stock_before,
            "stock_after": obj.stock_after,
            "stock_unit_cost": float(obj.stock_unit_cost) if obj.stock_unit_cost else 0.00,
            "oper_time": obj.oper_time,
            "oper_source": obj.oper_source
        }
