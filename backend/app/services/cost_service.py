from typing import Optional, Dict, Any, List
from datetime import datetime

from app.repositories.operating_expense_repo import OperatingExpenseRepository
from app.database import get_db
# 替换废弃异常：导入项目统一自定义异常（和其他服务层路径一致）
from app.utils.exceptions import CustomAPIException, NotFoundException


# ==================== 运营杂费管理 ====================
async def add_operating_expense(data) -> Dict[str, int]:
    """
    新增运营杂费
    - 校验费用日期格式
    - 校验费用金额大于0
    - 插入数据库
    - 返回新增ID
    """
    # 获取db会话（调用周期服务需要传db）
    db = next(get_db())
    # 解析费用日期并做格式校验
    try:
        fee_date = datetime.strptime(data.fee_date, "%Y-%m-%d")
    except ValueError:
        raise CustomAPIException(code=400, message="费用日期格式错误，要求%Y-%m-%d")
    
    if data.fee_amount <= 0:
        raise CustomAPIException(code=400, message="费用金额必须大于0")
    # 构建存储数据（驼峰转下划线）
    repo_data = {
        "expense_desc": data.fee_desc,
        "expense_type": data.fee_type,
        "expense_amount": data.fee_amount,
        "expense_date": fee_date,
        "remark": data.remark if hasattr(data, "remark") else None
    }
    
    # 初始化仓库并执行新增
    expense_repo = OperatingExpenseRepository(db)
    expense_id = expense_repo.create(repo_data)
    db.commit()
    return {"id": expense_id}


async def list_operating_expenses(
    desc: Optional[str],
    type: Optional[str],
    start_date: Optional[str],
    end_date: Optional[str],
    page_num: int,
    page_size: int
) -> Dict[str, Any]:
    """
    查询运营杂费列表
    - 支持费用描述模糊搜索、类型筛选、日期范围筛选
    - 只返回未删除数据，按费用日期倒序排列
    - 分页参数：page_num（页码）、page_size（页大小）
    """
    # 转换日期字符串为datetime对象，增加格式校验
    start_date = None
    end_date = None
    try:
        if start_date:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
        if end_date:
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        raise CustomAPIException(code=400, message="查询日期格式错误，要求%Y-%m-%d")
    
    # 初始化仓库执行查询
    db = next(get_db())
    expense_repo = OperatingExpenseRepository(db)
    
    # 统计总数
    total = expense_repo.count_by_conditions(
        desc=desc,
        expense_type=type,
        start_date=start_date,
        end_date=end_date
    )
    
    pages = (total + page_size - 1) // page_size if total > 0 else 0
    
    # 查询分页列表
    list_data = expense_repo.list_by_conditions(
        desc=desc,
        expense_type=type,
        start_date=start_date,
        end_date=end_date,
        offset=(page_num - 1) * page_size,
        limit=page_size
    )
    
    return {
        "total": total,
        "pages": pages,
        "list": list_data
    }


async def update_operating_expense(data) -> None:
    """
    修改运营杂费信息
    - 校验ID存在（404）
    - 若修改费用日期，自动重新计算所属结算周期
    - 仅更新传入的非空字段，执行数据库更新
    """
    expense_id = data.id
    if not expense_id:
        raise CustomAPIException(code=400, message="杂费记录ID不能为空")
    
    # 初始化仓库
    db = next(get_db())
    expense_repo = OperatingExpenseRepository(db)
    
    # 检查记录是否存在且未被删除：抛出项目统一404异常
    existing = expense_repo.get_by_id(expense_id)
    if not existing or existing.get("is_deleted"):
        raise NotFoundException(message="杂费记录不存在")
    
    # 构建更新数据（仅处理传入的字段）
    repo_data = {}
    if hasattr(data, "fee_desc") and data.fee_desc:
        repo_data["expense_desc"] = data.fee_desc
    if hasattr(data, "fee_type") and data.fee_type:
        repo_data["expense_type"] = data.fee_type
    if hasattr(data, "fee_amount") and data.fee_amount:
        repo_data["expense_amount"] = data.fee_amount
    if hasattr(data, "remark") is not None:
        repo_data["remark"] = data.remark
    
    # 若修改费用日期，更新日期
    if hasattr(data, "fee_date") and data.fee_date:
        try:
            fee_date = datetime.strptime(data.fee_date, "%Y-%m-%d")
        except ValueError:
            raise CustomAPIException(code=400, message="费用日期格式错误，要求%Y-%m-%d")
        repo_data["expense_date"] = fee_date
    
    # 存在更新数据时执行更新并提交
    if repo_data:
        expense_repo.update(expense_id, repo_data)
        db.commit()


async def delete_operating_expense(id: int) -> None:
    """
    软删除运营杂费记录
    - 校验ID存在且未被删除（404）
    - 执行软删除（更新is_deleted字段）
    """
    # 初始化仓库
    db = next(get_db())
    expense_repo = OperatingExpenseRepository(db)
    
    # 检查记录是否存在且未被删除：抛出项目统一404异常
    existing = expense_repo.get_by_id(id)
    if not existing or existing.get("is_deleted"):
        raise NotFoundException(message="杂费记录不存在")
    
    expense_repo.soft_delete(id)
    db.commit()