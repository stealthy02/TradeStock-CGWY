"""
商品数据访问模块

该模块定义了商品数据访问对象（Repository），负责商品相关的数据库操作。
"""

from typing import Optional, Dict, List
from decimal import Decimal
from datetime import datetime
from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from app.models.goods import Goods
from app.models.purchase_info import PurchaseInfo
from app.models.sale_info import SaleInfo


class GoodsRepository:
    """
    商品数据访问类
    
    负责商品相关的数据库操作，包括商品信息的增删改查、库存管理等。
    """
    def __init__(self, db: Session):
        """
        初始化商品数据访问对象
        
        Args:
            db (Session): 数据库会话实例
        """
        self.db = db
    
    def get_by_id(self, goods_id: int) -> Optional[Dict]:
        """
        根据ID获取商品信息
        
        Args:
            goods_id (int): 商品ID
        
        Returns:
            Optional[Dict]: 商品信息字典，不存在返回None
        """
        obj = self.db.query(Goods).filter(
            Goods.id == goods_id,
            Goods.is_deleted == False
        ).first()
        return self._to_dict(obj) if obj else None
    
    def get_by_name(self, name: str) -> Optional[Dict]:
        """
        根据名称获取商品信息
        
        Args:
            name (str): 商品名称
        
        Returns:
            Optional[Dict]: 商品信息字典，不存在返回None
        """
        obj = self.db.query(Goods).filter(
            Goods.goods_name == name,
            Goods.is_deleted == False
        ).first()
        return self._to_dict(obj) if obj else None
    
    def get_by_name_and_spec(self, name: str, spec: int) -> Optional[Dict]:
        """
        根据名称和规格获取商品信息
        
        Args:
            name (str): 商品名称
            spec (int): 商品规格
        
        Returns:
            Optional[Dict]: 商品信息字典，不存在返回None
        """
        obj = self.db.query(Goods).filter(
            Goods.goods_name == name,
            Goods.product_spec == spec,
            Goods.is_deleted == False
        ).first()
        return self._to_dict(obj) if obj else None
    
    def create(self, data: Dict) -> int:
        """
        创建商品信息
        
        Args:
            data (Dict): 商品信息数据
        
        Returns:
            int: 创建的商品ID
        """
        obj = Goods(**data)
        self.db.add(obj)
        self.db.flush()
        self.db.refresh(obj)
        return obj.id
    
    def update_stock_and_cost(self, goods_id: int, new_stock: int, 
                             new_cost: Decimal, new_value: Decimal) -> None:
        """
        更新商品库存和成本信息
        
        Args:
            goods_id (int): 商品ID
            new_stock (int): 新的库存数量
            new_cost (Decimal): 新的单位成本
            new_value (Decimal): 新的库存总价值
        """
        self.db.query(Goods).filter(Goods.id == goods_id).update({
            "current_stock_num": new_stock,
            "stock_unit_cost": new_cost,
            "stock_total_value": new_value
        })
        self.db.flush()
    
    def select_by_keyword(self, keyword: Optional[str], limit: int) -> List[str]:
        """
        根据关键词查询商品名称
        
        Args:
            keyword (Optional[str]): 关键词
            limit (int): 限制数量
        
        Returns:
            List[str]: 商品名称列表
        """
        query = self.db.query(Goods.goods_name).distinct().filter(Goods.is_deleted == False)
        if keyword:
            query = query.filter(Goods.goods_name.like(f"%{keyword}%"))
        objs = query.limit(limit).all()
        return [obj.goods_name for obj in objs]
    
    def select_by_keyword_with_stock(self, keyword: Optional[str], limit: int) -> List[str]:
        """
        根据关键词查询有库存的商品名称
        
        Args:
            keyword (Optional[str]): 关键词
            limit (int): 限制数量
        
        Returns:
            List[str]: 商品名称列表
        """
        query = self.db.query(Goods.goods_name).distinct().filter(
            Goods.is_deleted == False,
            Goods.current_stock_num > 0
        )
        if keyword:
            query = query.filter(Goods.goods_name.like(f"%{keyword}%"))
        objs = query.limit(limit).all()
        return [obj.goods_name for obj in objs]
    
    def count_by_inventory_conditions(self, name: Optional[str], 
                                     min_num: Optional[int], max_num: Optional[int]) -> int:
        """
        根据库存条件统计商品数量
        
        Args:
            name (Optional[str]): 商品名称
            min_num (Optional[int]): 最小库存数量
            max_num (Optional[int]): 最大库存数量
        
        Returns:
            int: 商品数量
        """
        query = self.db.query(func.count(Goods.id)).filter(Goods.is_deleted == False)
        if name:
            query = query.filter(Goods.goods_name == name)
        if min_num is not None:
            query = query.filter(Goods.current_stock_num >= min_num)
        if max_num is not None:
            query = query.filter(Goods.current_stock_num <= max_num)
        return query.scalar()
    
    def list_by_inventory_conditions(self, name: Optional[str], min_num: Optional[int],
                                    max_num: Optional[int], sort_field: str, 
                                    sort_order: str, offset: int, limit: int) -> List[Dict]:
        """
        根据库存条件查询商品列表
        
        Args:
            name (Optional[str]): 商品名称
            min_num (Optional[int]): 最小库存数量
            max_num (Optional[int]): 最大库存数量
            sort_field (str): 排序字段
            sort_order (str): 排序顺序
            offset (int): 偏移量
            limit (int): 限制数量
        
        Returns:
            List[Dict]: 商品信息列表
        """
        query = self.db.query(Goods).filter(Goods.is_deleted == False)
        
        if name:
            query = query.filter(Goods.goods_name == name)
        if min_num is not None:
            query = query.filter(Goods.current_stock_num >= min_num)
        if max_num is not None:
            query = query.filter(Goods.current_stock_num <= max_num)
        
        # 排序
        order_column = getattr(Goods, sort_field, Goods.current_stock_num)
        if sort_order == "desc":
            query = query.order_by(desc(order_column))
        else:
            query = query.order_by(order_column)
        
        objs = query.offset(offset).limit(limit).all()
        return [self._to_dict(obj) for obj in objs]
    
    def count_by_warning_line(self, warning_line: int) -> int:
        """
        统计低于预警线的商品数量
        
        Args:
            warning_line (int): 库存预警线
        
        Returns:
            int: 低于预警线的商品数量
        """
        return self.db.query(func.count(Goods.id)).filter(
            Goods.is_deleted == False,
            Goods.current_stock_num < warning_line
        ).scalar()
    
    def list_by_warning_line(self, warning_line: int, offset: int, limit: int) -> List[Dict]:
        """
        查询低于预警线的商品列表
        
        Args:
            warning_line (int): 库存预警线
            offset (int): 偏移量
            limit (int): 限制数量
        
        Returns:
            List[Dict]: 低于预警线的商品信息列表
        """
        objs = self.db.query(Goods).filter(
            Goods.is_deleted == False,
            Goods.current_stock_num < warning_line
        ).order_by(Goods.current_stock_num.asc()).offset(offset).limit(limit).all()
        return [self._to_dict(obj) for obj in objs]
    
    def get_last_purchase_date(self, goods_id: int) -> Optional[datetime]:
        """
        获取商品最后采购日期
        
        Args:
            goods_id (int): 商品ID
        
        Returns:
            Optional[datetime]: 最后采购日期
        """
        result = self.db.query(func.max(PurchaseInfo.purchase_date)).filter(
            PurchaseInfo.goods_id == goods_id,
            PurchaseInfo.is_deleted == False
        ).scalar()
        return result
    
    def get_last_sale_date(self, goods_id: int) -> Optional[datetime]:
        """
        获取商品最后销售日期
        
        Args:
            goods_id (int): 商品ID
        
        Returns:
            Optional[datetime]: 最后销售日期
        """
        result = self.db.query(func.max(SaleInfo.sale_date)).filter(
            SaleInfo.goods_id == goods_id,
            SaleInfo.is_deleted == False
        ).scalar()
        return result
    
    def get_total_purchase_num(self, goods_id: int) -> int:
        """
        获取商品总采购数量
        
        Args:
            goods_id (int): 商品ID
        
        Returns:
            int: 总采购数量
        """
        result = self.db.query(func.sum(PurchaseInfo.purchase_num)).filter(
            PurchaseInfo.goods_id == goods_id,
            PurchaseInfo.is_deleted == False
        ).scalar()
        return result or 0
    
    def get_total_sale_num(self, goods_id: int) -> int:
        """
        获取商品总销售数量
        
        Args:
            goods_id (int): 商品ID
        
        Returns:
            int: 总销售数量
        """
        result = self.db.query(func.sum(SaleInfo.sale_num)).filter(
            SaleInfo.goods_id == goods_id,
            SaleInfo.is_deleted == False
        ).scalar()
        return result or 0
    
    def get_last_purchase_info(self, goods_id: int) -> Optional[Dict]:
        """
        获取商品最后采购信息
        
        Args:
            goods_id (int): 商品ID
        
        Returns:
            Optional[Dict]: 最后采购信息，包含采购日期和供货商名
        """
        # 最后采购信息包含供货商名
        from app.models.supplier import Supplier
        result = self.db.query(PurchaseInfo, Supplier.supplier_name).join(
            Supplier, PurchaseInfo.supplier_id == Supplier.id
        ).filter(
            PurchaseInfo.goods_id == goods_id,
            PurchaseInfo.is_deleted == False
        ).order_by(desc(PurchaseInfo.purchase_date)).first()
        
        if result:
            purchase_info, supplier_name = result
            return {
                "purchase_date": purchase_info.purchase_date,
                "supplier_name": supplier_name
            }
        return None
    
    def get_total_inventory_value(self) -> Decimal:
        """
        获取总库存价值
        
        Returns:
            Decimal: 总库存价值
        """
        result = self.db.query(func.sum(Goods.stock_total_value)).filter(
            Goods.is_deleted == False
        ).scalar()
        return result or Decimal("0.00")
    
    def _to_dict(self, obj: Goods) -> Dict:
        """
        将商品对象转换为字典
        
        Args:
            obj (Goods): 商品对象
        
        Returns:
            Dict: 商品信息字典
        """
        return {
            "id": obj.id,
            "goods_name": obj.goods_name,
            "product_spec": obj.product_spec,
            "current_stock_num": obj.current_stock_num,
            "stock_unit_cost": obj.stock_unit_cost,
            "stock_total_value": obj.stock_total_value,
            "is_deleted": obj.is_deleted,
            "create_time": obj.create_time,
            "update_time": obj.update_time
        }