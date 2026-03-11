from fastapi import APIRouter
from app.routers import basic, purchase  # 添加purchase

api_router = APIRouter()

# 已注册的基础信息路由
api_router.include_router(basic.router, prefix="/api", tags=["基础信息"])

# 新增采购管理路由
api_router.include_router(purchase.router, prefix="/api", tags=["采购管理"])

# 后续还会添加：
# from app.routers import sale, inventory, cost, home
# api_router.include_router(sale.router, prefix="/api")
# api_router.include_router(inventory.router, prefix="/api")
# api_router.include_router(cost.router, prefix="/api")
# api_router.include_router(home.router, prefix="/api")