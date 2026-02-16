"""
路由模块初始化文件

该文件导出所有路由模块，方便在主应用中统一注册。
"""

from app.routers import home, basic, purchase, sale, inventory, cost


__all__ = ["home", "basic", "purchase", "sale", "inventory", "cost"]