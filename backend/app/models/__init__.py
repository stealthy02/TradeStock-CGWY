"""
模型模块初始化文件

该文件导出所有模型类，让 SQLAlchemy 知道有哪些表要创建。
"""

from app.models.supplier import Supplier
from app.models.purchaser import Purchaser
from app.models.goods import Goods
from app.models.purchase_info import PurchaseInfo
from app.models.purchase_statement import PurchaseStatement
from app.models.purchase_payment import PurchasePayment
from app.models.sale_info import SaleInfo
from app.models.sale_statement import SaleStatement
from app.models.sale_receipt import SaleReceipt
from app.models.inventory_loss import InventoryLoss
from app.models.inventory_flow import InventoryFlow
from app.models.operating_expense import OperatingExpense


__all__ = [
    "Supplier", "Purchaser", "Goods", 
    "PurchaseInfo", "PurchaseStatement", 
    "PurchasePayment", "SaleInfo", "SaleStatement", "SaleReceipt",
    "InventoryLoss", "InventoryFlow", "OperatingExpense"
]