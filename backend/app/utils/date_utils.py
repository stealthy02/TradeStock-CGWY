"""
日期工具模块

该模块提供日期相关的工具函数，包括日期转换、结算周期计算等。
"""

from datetime import datetime, date, timedelta
from typing import Union, Tuple


def to_date_obj(target: Union[str, datetime, date], fmt: str = "%Y-%m-%d") -> date:
    """
    通用日期转换：将str/datetime统一转为date对象（排除时间部分）
    
    Args:
        target (Union[str, datetime, date]): 待转换的日期
        fmt (str): 字符串日期的格式，默认%Y-%m-%d
    
    Returns:
        date: 纯date对象
    """
    if isinstance(target, date):
        return target
    if isinstance(target, datetime):
        return target.date()
    if isinstance(target, str):
        return datetime.strptime(target, fmt).date()
    raise ValueError(f"不支持的日期类型：{type(target)}")
