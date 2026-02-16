import asyncio
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
from decimal import Decimal
from app.repositories.goods_repo import GoodsRepository
from app.repositories.purchase_statement_repo import PurchaseStatementRepository
from app.repositories.sale_statement_repo import SaleStatementRepository
from app.repositories.operating_expense_repo import OperatingExpenseRepository
from app.database import SessionLocal  # 保留原有会话获取方法
# 替换废弃异常：导入项目统一自定义异常（和其他服务层路径完全一致）
from app.utils.exceptions import CustomAPIException, ParamErrorException


async def get_statistic_card_data(
    time_type: Optional[str],
    start_date: Optional[str],
    end_date: Optional[str]
) -> Dict[str, Any]:
    """
    获取数字卡片数据
    说明：返回固定的统计数据
    """
    # 获取当前月份和年度的时间范围
    today = datetime.now()
    current_month_start = datetime(today.year, today.month, 1)
    if today.month == 12:
        current_month_end = datetime(today.year, 12, 31, 23, 59, 59)
    else:
        current_month_end = datetime(today.year, today.month + 1, 1, 0, 0, 0) - timedelta(seconds=1)
    
    current_year_start = datetime(today.year, 1, 1)
    current_year_end = datetime(today.year, 12, 31, 23, 59, 59)
    
    all_time_start = datetime(2000, 1, 1)
    all_time_end = datetime.now().replace(hour=23, minute=59, second=59)
    
    # 并行查询数字卡片核心数据
    inventory_value, purchase_unreceived, sale_unreceived, month_stats, year_stats, total_stats = await asyncio.gather(
        asyncio.to_thread(_get_total_inventory_value),
        asyncio.to_thread(_get_total_purchase_unreceived),
        asyncio.to_thread(_get_total_sale_unreceived),
        _get_cycle_statistics(current_month_start, current_month_end),
        _get_cycle_statistics(current_year_start, current_year_end),
        _get_cycle_statistics(all_time_start, all_time_end)
    )
    
    # 数据兜底处理
    month_stats = month_stats or {}
    year_stats = year_stats or {}
    total_stats = total_stats or {}

    # 组装响应数据
    return {
        "inventory_value": float(inventory_value or 0),
        "purchase_unreceived": float(purchase_unreceived or 0),
        "sale_unreceived": float(sale_unreceived or 0),
        "month_profit": float(month_stats.get("profit", 0)),
        "year_profit": float(year_stats.get("profit", 0)),
        "total_profit": float(total_stats.get("profit", 0))
    }


async def get_pie_chart_data(
    time_type: str,
    start_date: Optional[str],
    end_date: Optional[str]
) -> Dict[str, Any]:
    """
    获取饼状图数据
    查询维度：
    - cycle: 指定结算周期
    - year: 本年数据
    - all: 全部数据
    - custom: 自定义时间范围
    """
    # 解析查询时间范围
    start_date, end_date = await _resolve_date_range(
        time_type, start_date, end_date
    )
    
    # 并行查询饼状图分布数据
    purchaser_profit, product_profit = await asyncio.gather(
        asyncio.to_thread(
            _get_purchaser_profit_distribution, start_date, end_date
        ),
        asyncio.to_thread(
            _get_product_profit_distribution, start_date, end_date
        )
    )
    
    # 数据兜底处理
    purchaser_profit = purchaser_profit or []
    product_profit = product_profit or []

    # 组装响应数据
    return {
        "purchaser_profit": _format_pie_data(purchaser_profit),
        "product_profit": _format_pie_data(product_profit)
    }


async def get_trend_chart_data(
    time_type: str,
    start_date: Optional[str],
    end_date: Optional[str]
) -> Dict[str, Any]:
    """
    获取趋势图数据
    查询维度：
    - all: 全部数据
    - custom: 自定义时间范围（按周期走）
    """
    # 解析查询时间范围
    start_date, end_date = await _resolve_date_range(
        time_type, start_date, end_date
    )
    
    # 获取趋势图数据
    trend_data = await _get_trend_chart_data_by_range(
        time_type, start_date, end_date
    )
    
    # 数据兜底处理
    trend_data = trend_data or {}

    # 组装响应数据
    return {
        "xAxis": trend_data.get("xAxis", []),
        "revenue_data": trend_data.get("revenue", []),
        "expend_data": trend_data.get("expend", [])
    }


async def get_home_data(
    time_type: str,
    start_date: Optional[str],
    end_date: Optional[str]
) -> Dict[str, Any]:
    """
    查询首页核心数据（数字卡片+趋势图+饼状图）
    查询维度：
    - month: 本月数据
    - year: 本年数据
    - all: 全部数据
    - custom: 自定义时间范围
    """
    # 解析查询时间范围
    start_date, end_date = await _resolve_date_range(
        time_type, start_date, end_date
    )
    
    # 获取当前月份和年度的时间范围
    today = datetime.now()
    current_month_start = datetime(today.year, today.month, 1)
    if today.month == 12:
        current_month_end = datetime(today.year, 12, 31, 23, 59, 59)
    else:
        current_month_end = datetime(today.year, today.month + 1, 1, 0, 0, 0) - timedelta(seconds=1)
    
    current_year_start = datetime(today.year, 1, 1)
    current_year_end = datetime(today.year, 12, 31, 23, 59, 59)
    
    all_time_start = datetime(2000, 1, 1)
    all_time_end = datetime.now().replace(hour=23, minute=59, second=59)
    
    # 并行查询数字卡片核心数据 - 每个线程独立创建会话+仓库，保证线程隔离
    inventory_value, purchase_unreceived, sale_unreceived, current_stats, month_stats, year_stats, total_stats = await asyncio.gather(
        # 库存总价值：独立线程+独立会话
        asyncio.to_thread(_get_total_inventory_value),
        # 采购未付款：独立线程+独立会话
        asyncio.to_thread(_get_total_purchase_unreceived),
        # 销售未收款：独立线程+独立会话
        asyncio.to_thread(_get_total_sale_unreceived),
        # 当前时间范围统计：内部已做线程隔离，直接调用
        _get_cycle_statistics(start_date, end_date),
        # 本月统计
        _get_cycle_statistics(current_month_start, current_month_end),
        # 本年统计
        _get_cycle_statistics(current_year_start, current_year_end),
        # 全部统计
        _get_cycle_statistics(all_time_start, all_time_end)
    )
    
    # 查询趋势图数据（单线程执行，内部并行已做隔离）
    trend_data = await _get_trend_chart_data_by_range(
        time_type, start_date, end_date
    )
    
    # 并行查询饼状图分布数据 - 每个线程独立创建会话+仓库
    purchaser_profit, product_profit = await asyncio.gather(
        asyncio.to_thread(
            _get_purchaser_profit_distribution, start_date, end_date
        ),
        asyncio.to_thread(
            _get_product_profit_distribution, start_date, end_date
        )
    )
    
    # ========== 核心修改：全层级兜底初始化，彻底解决None问题 ==========
    # 1. 对统计数据兜底：如果返回None则置为空字典
    current_stats = current_stats or {}
    month_stats = month_stats or {}
    year_stats = year_stats or {}
    total_stats = total_stats or {}
    # 2. 对trend_data兜底：如果返回None则置为空字典
    trend_data = trend_data or {}
    # 3. 对饼图数据兜底：避免_format_pie_data入参为None
    purchaser_profit = purchaser_profit or []
    product_profit = product_profit or []

    # 组装响应数据：所有字段均做兜底，保证非None
    return {
        # 数字卡片：保证是字典，所有值默认0.0
        "statistic_card": {
            "inventory_value": float(inventory_value or 0),
            "purchase_unreceived": float(purchase_unreceived or 0),
            "sale_unreceived": float(sale_unreceived or 0),
            "cycle_profit": float(current_stats.get("profit", 0)),  # 缺字段取0
            "cycle_revenue": float(current_stats.get("revenue", 0)), # 缺字段取0
            "cycle_expend": float(current_stats.get("expend", 0)),   # 测试代码要取的cycle_expend彻底兜底
            "month_profit": float(month_stats.get("profit", 0)),
            "year_profit": float(year_stats.get("profit", 0)),
            "total_profit": float(total_stats.get("profit", 0))
        },
        # 趋势图：保证是字典，xAxis/数据列表默认空列表
        "trend_chart": {
            "xAxis": trend_data.get("xAxis", []),  # 缺字段取空列表
            "revenue_data": trend_data.get("revenue", []),  # 缺字段取空列表
            "expend_data": trend_data.get("expend", [])     # 缺字段取空列表
        },
        # 饼状图：保证是字典，子字段由_format_pie_data返回（即使入参空列表也会返回合法格式）
        "pie_chart": {
            "purchaser_profit": _format_pie_data(purchaser_profit),
            "product_profit": _format_pie_data(product_profit)
        }
    }


# 抽离独立线程执行的方法 - 内部创建专属会话+仓库，避免会话共享
def _get_total_inventory_value():
    db = SessionLocal()
    repo = GoodsRepository(db)
    try:
        return repo.get_total_inventory_value()
    finally:
        db.close()

def _get_total_purchase_unreceived():
    db = SessionLocal()
    repo = PurchaseStatementRepository(db)
    try:
        return repo.get_total_unreceived_amount()
    finally:
        db.close()

def _get_total_sale_unreceived():
    db = SessionLocal()
    repo = SaleStatementRepository(db)
    try:
        return repo.get_total_unreceived_amount()
    finally:
        db.close()

def _get_purchaser_profit_distribution(start_date, end_date):
    db = SessionLocal()
    repo = SaleStatementRepository(db)
    try:
        return repo.get_purchaser_profit_distribution(start_date, end_date)
    finally:
        db.close()

def _get_product_profit_distribution(start_date, end_date):
    db = SessionLocal()
    repo = SaleStatementRepository(db)
    try:
        return repo.get_product_profit_distribution(start_date, end_date)
    finally:
        db.close()


async def _resolve_date_range(
    time_type: str,
    start_date: Optional[str],
    end_date: Optional[str]
) -> tuple[datetime, datetime]:
    """解析查询类型对应的时间范围，返回(start_date, end_date)"""
    if time_type == "month":
        # 当前月份
        today = datetime.now()
        start_date = datetime(today.year, today.month, 1)
        # 计算当月最后一天
        if today.month == 12:
            end_date = datetime(today.year, 12, 31, 23, 59, 59)
        else:
            end_date = datetime(today.year, today.month + 1, 1, 0, 0, 0) - timedelta(seconds=1)
        return start_date, end_date
    elif time_type == "year":
        # 使用标准的日历年度
        today = datetime.now()
        start_date = datetime(today.year, 1, 1)
        end_date = datetime(today.year, 12, 31, 23, 59, 59)
        return start_date, end_date
    elif time_type == "all":
        # 全部数据，返回最早和最晚的时间
        # 这里使用一个较早的日期作为起点
        start_date = datetime(2000, 1, 1)
        end_date = datetime.now().replace(hour=23, minute=59, second=59)
        return start_date, end_date
    elif time_type == "custom":
        # 自定义时间范围，校验参数完整性
        if not start_date or not end_date:
            raise ParamErrorException(message="自定义时间范围必须提供start和end参数")
        # 增加日期格式校验
        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise ParamErrorException(message="时间格式错误，要求%Y-%m-%d")
        # 调整结束时间至当日23:59:59，确保包含整天数据
        end_date = end_date.replace(hour=23, minute=59, second=59)
        return start_date, end_date
    
    else:
        # 不支持的time_type
        raise ParamErrorException(message=f"不支持的time_type参数：{time_type}")


async def _get_cycle_statistics(
    start_date: datetime,
    end_date: datetime,
) -> Dict[str, float]:
    """
    获取指定时间范围的经营统计数据
    - revenue: 销售收入（销售对账单金额）
    - profit: 经营毛利（销售利润 - 运营杂费）
    - expend: 总支出（采购支出 + 运营杂费）
    """
    # 内部并行查询，同样做线程隔离
    sale_revenue, sale_profit, purchase_expend, operating_expend = await asyncio.gather(
        asyncio.to_thread(_get_sale_revenue_by_date, start_date, end_date),
        asyncio.to_thread(_get_sale_profit_by_date, start_date, end_date),
        asyncio.to_thread(_get_purchase_expend_by_date, start_date, end_date),
        asyncio.to_thread(_get_operating_expend_by_date, start_date, end_date)
    )
    
    # 计算统计指标，空值默认0（逻辑不变）
    revenue = float(sale_revenue or 0)
    profit = float(sale_profit or 0) - float(operating_expend or 0)
    expend = float(purchase_expend or 0) + float(operating_expend or 0)
    
    return {"revenue": revenue, "profit": profit, "expend": expend}

# 周期统计的独立线程方法
def _get_sale_revenue_by_date(start_date, end_date):
    db = SessionLocal()
    repo = SaleStatementRepository(db)
    try:
        return repo.get_total_statement_amount_by_date(start_date, end_date)
    finally:
        db.close()

def _get_sale_profit_by_date(start_date, end_date):
    db = SessionLocal()
    repo = SaleStatementRepository(db)
    try:
        return repo.get_total_profit_by_date(start_date, end_date)
    finally:
        db.close()

def _get_purchase_expend_by_date(start_date, end_date):
    db = SessionLocal()
    repo = PurchaseStatementRepository(db)
    try:
        return repo.get_total_statement_amount_by_date(start_date, end_date)
    finally:
        db.close()

def _get_operating_expend_by_date(start_date, end_date):
    db = SessionLocal()
    repo = OperatingExpenseRepository(db)
    try:
        return repo.get_total_amount_by_date(start_date, end_date)
    finally:
        db.close()


async def _get_trend_chart_data_by_range(
    time_type: str,
    current_start: datetime,
    current_end: datetime,
) -> Dict[str, List]:
    """
    获取趋势图数据
    - all类型：按月份显示所有数据的营收/支出对比
    - custom类型：按月份聚合营收/支出数据
    """
    # 按月份聚合获取趋势数据，独立线程执行
    def _get_monthly_data():
        db = SessionLocal()
        repo = SaleStatementRepository(db)
        try:
            return repo.get_monthly_revenue_expend(current_start, current_end)
        finally:
            db.close()
    monthly_data = await asyncio.to_thread(_get_monthly_data)
    
    # 确保monthly_data是列表
    if not isinstance(monthly_data, list):
        monthly_data = []
    
    x_axis = [d["month"] for d in monthly_data]
    revenue = [float(d["revenue"]) for d in monthly_data]
    expend = [float(d["expend"]) for d in monthly_data]
    
    return {"xAxis": x_axis, "revenue": revenue, "expend": expend}


def _format_pie_data(data_list: List[Dict]) -> List[Dict[str, Any]]:
    """
    格式化饼图数据，计算各维度占比
    :param data_list: 原始数据 [{"name": "xxx", "value": 5000}, ...]
    :return: 带占比的饼图数据 [{"name": "", "value": 0.0, "proportion": 0.0}, ...]
    """
    if not data_list:
        return []
    
    total = sum(item["value"] for item in data_list)
    # 总价值为0时，占比默认0，避免除零错误
    if total == 0:
        return [
            {"name": item["name"], "value": float(item["value"]), "proportion": 0.0}
            for item in data_list
        ]
    
    return [
        {
            "name": item["name"],
            "value": float(item["value"]),
            "proportion": round(item["value"] / total * 100, 2)
        }
        for item in data_list
    ]