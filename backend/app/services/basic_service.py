from typing import Optional, List, Dict, Any
from fastapi import status

from app.repositories.supplier_repo import SupplierRepository
from app.repositories.purchaser_repo import PurchaserRepository
from app.database import get_db
from app.utils.exceptions import CustomAPIException, NotFoundException

# ==================== 供货商相关 ====================
async def add_supplier(data) -> Dict[str, int]:
    """
    新增供货商（优化软删逻辑）
    - 校验名称唯一性：未删同名→409冲突；软删同名→恢复并更新信息
    - 无同名→插入数据库；有软删同名→恢复+更新
    - 返回新增/恢复的ID
    """
    db = next(get_db())
    supplier_repo = SupplierRepository(db)
    
    # 关键：查询【所有状态】的同名供货商（含软删，突破原仅查未删的限制）
    # 这里用repo新增方法，也可以直接查，推荐封装到repo层更优雅
    existing_supplier = supplier_repo.get_by_name_include_deleted(data.supplier_name)
    
    if existing_supplier:
        # 情况1：存在未软删的同名供货商→抛409冲突（原逻辑不变）
        if not existing_supplier.is_deleted:
            raise CustomAPIException(
                code=409,
                message="供货商名称已存在"
            )
        # 情况2：存在软删的同名供货商→恢复（取消软删）+ 更新新信息
        supplier_id = existing_supplier.id
        # 1. 先解除软删标记（update方法过滤了is_deleted=False，必须先单独改）
        supplier_repo.undo_soft_delete(supplier_id)
        # 2. 把新提交的信息转成字典，更新到该条数据（复用现有update方法）
        update_data = {
            "contact_person": data.contact_person,
            "contact_phone": data.contact_phone,
            "company_address": data.company_address,
            "bank_name": data.bank_name,
            "bank_account": data.bank_account,
            "tax_no": data.tax_no,
            "avatar_url": data.avatar_url,
            "remark": data.remark
        }
        supplier_repo.update(supplier_id, update_data)
    else:
        # 情况3：无同名数据→全新插入（原逻辑不变）
        supplier_id = supplier_repo.create(data)
    
    # 统一提交事务（新增/恢复+更新 都走这一个commit，保证原子性）
    db.commit()
    return {"id": supplier_id}


async def list_suppliers(
    supplier_name: Optional[str],  # 适配路由的参数名
    contact_phone: Optional[str],  # 适配路由的参数名
    page_num: int,                 # 替换原page → 适配路由page_num
    page_size: int                 # 替换原size → 适配路由page_size
) -> Dict[str, Any]:
    """
    分页查询供货商列表
    - 支持名称/电话模糊搜索
    - 只返回未删除的数据
    - 适配路由：page_num（页码）、page_size（页大小）
    """
    db = next(get_db())
    supplier_repo = SupplierRepository(db)
    
    total = supplier_repo.count_by_conditions(supplier_name, contact_phone)
    pages = (total + page_size - 1) // page_size if total > 0 else 0
    
    list_data = supplier_repo.list_by_conditions(
        name=supplier_name,
        phone=contact_phone,
        offset=(page_num - 1) * page_size,  # 适配page_num计算偏移量
        limit=page_size
    )
    return {
        "total": total,
        "pages": pages,
        "list": list_data
    }


async def update_supplier(data) -> None:
    """
    修改供货商信息
    - 校验ID存在（404）
    - 校验名称唯一性（排除自身，409冲突）
    - 执行数据库更新
    """
    db = next(get_db())
    supplier_repo = SupplierRepository(db)
    
    supplier_id = data.id
    
    # 检查供货商是否存在，使用封装的404异常子类，简化代码
    existing = supplier_repo.get_by_id(supplier_id)
    if not existing or existing.get("is_deleted"):
        raise NotFoundException(message="供货商不存在")
    
    # 名称修改时校验唯一性（排除自身ID）
    if hasattr(data, "supplier_name") and data.supplier_name:
        name_existing = supplier_repo.get_by_name(data.supplier_name)
        if name_existing and name_existing["id"] != supplier_id:
            raise CustomAPIException(
                code=409,
                message="供货商名称已存在"
            )
    
    supplier_repo.update(supplier_id, data)
    db.commit()


async def delete_supplier(id: int) -> None:
    """
    软删除供货商
    - 校验ID存在（404）
    - 检查关联采购记录（603，无法删除）
    - 执行删除（物理删除）
    """
    db = next(get_db())
    supplier_repo = SupplierRepository(db)
    
    # 检查供货商是否存在
    existing = supplier_repo.get_by_id(id)
    if not existing or existing.get("is_deleted"):
        raise NotFoundException(message="供货商不存在")
    
    # 检查关联采购记录，自定义业务码603
    if supplier_repo.has_purchase_records(id):
        raise CustomAPIException(
            code=603,
            message="存在关联采购记录，无法删除"  # 修正原msg→message
        )
    
    supplier_repo.soft_delete(id)
    db.commit()


async def select_suppliers(keyword: Optional[str], limit: int = 5) -> List[str]:
    """
    供货商下拉联想查询
    - 关键词模糊匹配名称
    - 返回不重复的结果
    - 格式：["供货商1", "供货商2"]
    """
    db = next(get_db())
    supplier_repo = SupplierRepository(db)
    suppliers = supplier_repo.select_by_keyword(keyword, limit=limit)
    return [supplier["supplier_name"] for supplier in suppliers]


# ==================== 采购商相关 ====================

async def add_purchaser(data) -> Dict[str, int]:
    """
    新增采购商（优化软删逻辑）
    - 校验名称唯一性：未删同名→409冲突；软删同名→恢复并更新新信息
    - 无同名→插入数据库；有软删同名→恢复+更新
    - 返回新增/恢复的采购商ID
    """
    db = next(get_db())
    purchaser_repo = PurchaserRepository(db)
    
    # 关键：查询【所有状态】的同名采购商（含软删，用于判断是恢复还是抛错）
    existing_purchaser = purchaser_repo.get_by_name_include_deleted(data.purchaser_name)
    
    if existing_purchaser:
        # 情况1：存在未软删的同名采购商→抛409业务异常（原逻辑不变）
        if not existing_purchaser.is_deleted:
            raise CustomAPIException(
                code=409,
                message="采购商名称已存在"
            )
        # 情况2：存在软删的同名采购商→先恢复软删，再更新新提交的信息
        purchaser_id = existing_purchaser.id
        # 解除软删标记（必须先执行，否则update方法过滤不到数据）
        purchaser_repo.undo_soft_delete(purchaser_id)
        # 构造更新数据（适配采购商所有可编辑字段，排除名称：唯一且同名无需改）
        update_data = {
            "contact_person": data.contact_person,
            "contact_phone": data.contact_phone,
            "company_address": data.company_address,
            "receive_address": data.receive_address,  # 采购商专属收货地址字段
            "bank_name": data.bank_name,
            "bank_account": data.bank_account,
            "tax_no": data.tax_no,
            "avatar_url": data.avatar_url,
            "remark": data.remark
        }
        # 复用现有update方法更新新信息
        purchaser_repo.update(purchaser_id, update_data)
    else:
        # 情况3：无同名采购商→正常新增（原逻辑不变）
        purchaser_id = purchaser_repo.create(data)
    
    # 统一提交事务：新增/恢复+更新 都走这一个commit，保证原子性
    db.commit()
    return {"id": purchaser_id}


async def list_purchasers(
    purchaser_name: Optional[str],  # 适配路由的参数名
    contact_phone: Optional[str],  # 适配路由的参数名
    page_num: int,                 # 替换原page → 适配路由page_num
    page_size: int                 # 替换原size → 适配路由page_size
) -> Dict[str, Any]:
    """
    分页查询采购商列表
    - 支持名称/电话模糊搜索
    - 只返回未删除的数据
    - 适配路由：page_num（页码）、page_size（页大小）
    """
    db = next(get_db())
    purchaser_repo = PurchaserRepository(db)
    
    total = purchaser_repo.count_by_conditions(purchaser_name, contact_phone)
    pages = (total + page_size - 1) // page_size if total > 0 else 0
    
    list_data = purchaser_repo.list_by_conditions(
        name=purchaser_name,
        phone=contact_phone,
        offset=(page_num - 1) * page_size,  # 适配page_num计算偏移量
        limit=page_size
    )
    return {
        "total": total,
        "pages": pages,
        "list": list_data
    }


async def update_purchaser(data) -> None:
    """
    修改采购商信息
    - 校验ID存在（404）
    - 校验名称唯一性（排除自身，409冲突）
    - 执行数据库更新
    """
    db = next(get_db())
    purchaser_repo = PurchaserRepository(db)
    
    purchaser_id = data.id
    
    # 检查采购商是否存在
    existing = purchaser_repo.get_by_id(purchaser_id)
    if not existing or existing.get("is_deleted"):
        raise NotFoundException(message="采购商不存在")
    
    # 名称修改时校验唯一性（排除自身ID）
    if hasattr(data, "purchaser_name") and data.purchaser_name:
        name_existing = purchaser_repo.get_by_name(data.purchaser_name)
        if name_existing and name_existing["id"] != purchaser_id:
            raise CustomAPIException(
                code=409,
                message="采购商名称已存在"
            )
    
    purchaser_repo.update(purchaser_id, data)
    db.commit()


async def delete_purchaser(id: int) -> None:
    """
    软删除采购商
    - 校验ID存在（404）
    - 检查关联销售记录（603，无法删除）
    - 执行软删除（更新is_deleted）
    """
    db = next(get_db())
    purchaser_repo = PurchaserRepository(db)
    
    # 检查采购商是否存在
    existing = purchaser_repo.get_by_id(id)
    if not existing or existing.get("is_deleted"):
        raise NotFoundException(message="采购商不存在")
    
    # 检查关联销售记录，自定义业务码603
    if purchaser_repo.has_sale_records(id):
        raise CustomAPIException(
            code=603,
            message="存在关联销售记录，无法删除"
        )
    
    purchaser_repo.soft_delete(id)
    db.commit()


async def select_purchasers(keyword: Optional[str], limit: int = 5) -> List[str]:
    """
    采购商下拉联想查询
    - 关键词模糊匹配名称
    - 返回不重复的结果
    - 格式：["采购商1", "采购商2"]
    """
    db = next(get_db())
    purchaser_repo = PurchaserRepository(db)
    purchasers = purchaser_repo.select_by_keyword(keyword, limit=limit)
    return [purchaser["purchaser_name"] for purchaser in purchasers]