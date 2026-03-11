import asyncio
import time
from typing import Optional, Dict, List, Any
from datetime import datetime, date, timedelta
from decimal import Decimal
from app.repositories.goods_repo import GoodsRepository
from app.repositories.purchase_statement_repo import PurchaseStatementRepository
from app.repositories.sale_statement_repo import SaleStatementRepository
from app.repositories.operating_expense_repo import OperatingExpenseRepository
from app.repositories.sale_info_repo import SaleInfoRepository
from app.repositories.purchase_info_repo import PurchaseInfoRepository
from app.repositories.inventory_loss_repo import InventoryLossRepository
from app.database import SessionLocal
from app.utils.exceptions import CustomAPIException, ParamErrorException


def get_month_period(target_date: date) -> tuple[date, date]:
    """
    获取指定日期所属的业务月度期间
    业务月度：从上个月26日开始至本月25日结束
    
    例如：
    - 2024-01-15 属于 2023-12-26 至 2024-01-25 的月度
    - 2024-01-26 属于 2024-01-26 至 2024-02-25 的月度
    """
    if target_date.day >= 26:
        # 本月26日及之后，属于下个月度周期
        start_date = date(target_date.year, target_date.month, 26)
        if target_date.month == 12:
            end_date = date(target_date.year + 1, 1, 25)
        else:
            end_date = date(target_date.year, target_date.month + 1, 25)
    else:
        # 本月25日及之前，属于当前月度周期
        if target_date.month == 1:
            start_date = date(target_date.year - 1, 12, 26)
        else:
            start_date = date(target_date.year, target_date.month - 1, 26)
        end_date = date(target_date.year, target_date.month, 25)
    
    return start_date, end_date


def get_year_period(target_year: int) -> tuple[date, date]:
    """
    获取指定年份的业务年度期间
    业务年度：从前一年12月26日开始至本年12月25日结束
    
    例如：
    - 2024年度：2023-12-26 至 2024-12-25
    """
    start_date = date(target_year - 1, 12, 26)
    end_date = date(target_year, 12, 25)
    return start_date, end_date


def get_current_month_period() -> tuple[date, date]:
    """获取当前业务月度期间"""
    today = date.today()
    return get_month_period(today)


def get_last_month_period() -> tuple[date, date]:
    """
    获取上月业务月度期间
    例如：今天是2026-02-27，当前周期是2026-02-26~2026-03-25（3月周期）
    上月周期就是2026-01-26~2026-02-25（2月周期）
    """
    today = date.today()
    current_start, current_end = get_month_period(today)
    
    # 上月周期的结束日期是当前周期的开始日期减1天
    last_month_end = current_start - timedelta(days=1)
    # 上月周期的开始日期是上月周期结束日期往前推一个月
    if last_month_end.day == 25:
        # 上月周期是上个月26日到本月25日
        if last_month_end.month == 1:
            last_month_start = date(last_month_end.year - 1, 12, 26)
        else:
            last_month_start = date(last_month_end.year, last_month_end.month - 1, 26)
    else:
        # 兜底逻辑，正常情况下不会出现
        last_month_start = last_month_end - timedelta(days=30)
    
    return last_month_start, last_month_end


def get_current_year_period() -> tuple[date, date]:
    """获取当前业务年度期间"""
    today = date.today()
    return get_year_period(today.year)


async def get_statistic_card_data() -> Dict[str, Any]:
    """
    获取数字卡片数据
    说明：返回固定的统计数据
    优化点：
    1. 所有查询并行执行，避免顺序等待
    2. 四个时间周期的统计数据一次性获取，避免重复查询
    """
    # 获取当前业务月度、上月业务月度和业务年度的时间范围
    current_month_start, current_month_end = get_current_month_period()
    last_month_start, last_month_end = get_last_month_period()
    current_year_start, current_year_end = get_current_year_period()
    
    all_time_start = date(2020, 1, 1)
    all_time_end = date(2050, 1, 1)
    
    # 并行查询前三个基础数据
    inventory_value, purchase_unreceived, sale_unreceived = await asyncio.gather(
        asyncio.to_thread(_get_total_inventory_value),
        asyncio.to_thread(_get_total_purchase_unreceived),
        asyncio.to_thread(_get_total_sale_unreceived),
    )
    
    # 并行查询三个时间周期的统计数据(每个周期内部也并行查询5个指标)
    month_stats, last_month_stats, total_stats = await asyncio.gather(
        asyncio.to_thread(_get_cycle_statistics_sync, current_month_start, current_month_end),
        asyncio.to_thread(_get_cycle_statistics_sync, last_month_start, last_month_end),
        asyncio.to_thread(_get_cycle_statistics_sync, all_time_start, all_time_end),
    )
    
    # 数据兜底处理
    month_stats = month_stats or {}
    last_month_stats = last_month_stats or {}
    total_stats = total_stats or {}

    # 组装响应数据
    return {
        "inventory_value": float(inventory_value or 0),
        "purchase_unreceived": float(purchase_unreceived or 0),
        "sale_unreceived": float(sale_unreceived or 0),
        "month_profit": float(month_stats.get("profit", 0)),
        "last_month_profit": float(last_month_stats.get("profit", 0)),
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
        start_date, end_date
    )
    
    # 数据兜底处理
    trend_data = trend_data or {}

    # 组装响应数据
    return {
        "xAxis": trend_data.get("xAxis", []),
        "revenue_data": trend_data.get("revenue", []),
        "expend_data": trend_data.get("expend", [])
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
    repo = SaleInfoRepository(db)
    try:
        return repo.get_purchaser_profit_distribution(start_date, end_date)
    finally:
        db.close()


def _get_product_profit_distribution(start_date, end_date):
    db = SessionLocal()
    repo = SaleInfoRepository(db)
    try:
        return repo.get_product_profit_distribution(start_date, end_date)
    finally:
        db.close()


async def _resolve_date_range(
    time_type: str,
    start_date: Optional[str],
    end_date: Optional[str]
) -> tuple[date, date]:
    """解析查询类型对应的时间范围，返回(start_date, end_date)"""
    if time_type == "month":
        # 使用业务月度：从前一月26日至本月25日
        start_date, end_date = get_current_month_period()
        return start_date, end_date
    elif time_type == "year":
        # 使用业务年度：从前一年12月26日至本年12月25日
        today = datetime.now().date()
        start_date, end_date = get_year_period(today.year)
        return start_date, end_date
    elif time_type == "all":
        # 全部数据：从2020年1月1日到未来
        return date(2020, 1, 1), date(2050, 1, 1)
    elif time_type == "custom":
        # 自定义时间范围，仅趋势图支持
        if not start_date or not end_date:
            raise ParamErrorException(message="自定义时间范围必须提供start和end参数")
        # 增加日期格式校验
        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            raise ParamErrorException(message="时间格式错误，要求%Y-%m-%d")
        return start_date, end_date
    
    else:
        # 不支持的time_type
        raise ParamErrorException(message=f"不支持的time_type参数：{time_type}")


def _get_cycle_statistics_sync(
    start_date: date,
    end_date: date,
) -> Dict[str, float]:
    """
    获取指定时间范围的经营统计数据(同步版本，用于在线程池中执行)
    - revenue: 销售收入（基于sale_date的销售数据）
    - profit: 经营毛利（销售利润 - 运营杂费 - 报损成本）
    - expend: 总支出（采购支出 + 运营杂费）
    优化：使用线程池并行执行4个数据库查询
    """
    import concurrent.futures
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        # 提交所有任务到线程池
        future_revenue = executor.submit(_get_sale_revenue_by_date, start_date, end_date)
        future_profit = executor.submit(_get_sale_profit_by_date, start_date, end_date)
        future_purchase = executor.submit(_get_purchase_expend_by_date, start_date, end_date)
        future_operating = executor.submit(_get_operating_expend_by_date, start_date, end_date)
        future_loss = executor.submit(_get_loss_cost_by_date, start_date, end_date)
        
        # 获取结果
        sale_revenue = future_revenue.result()
        sale_profit = future_profit.result()
        purchase_expend = future_purchase.result()
        operating_expend = future_operating.result()
        loss_cost = future_loss.result()
    
    # 计算统计指标，空值默认0（逻辑不变）
    revenue = float(sale_revenue or 0)
    profit = float(sale_profit or 0) - float(operating_expend or 0) - float(loss_cost or 0)
    expend = float(purchase_expend or 0) + float(operating_expend or 0)
    
    return {"revenue": revenue, "profit": profit, "expend": expend}


# 周期统计的独立线程方法
def _get_sale_revenue_by_date(start_date, end_date):
    max_retries = 3
    retry_delay = 0.5
    
    for attempt in range(max_retries):
        db = SessionLocal()
        repo = SaleInfoRepository(db)
        try:
            return repo.get_total_revenue_by_date(start_date, end_date)
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            else:
                return Decimal("0.00")
        finally:
            db.close()


def _get_sale_profit_by_date(start_date, end_date):
    max_retries = 3
    retry_delay = 0.5
    
    for attempt in range(max_retries):
        db = SessionLocal()
        repo = SaleInfoRepository(db)
        try:
            return repo.get_total_profit_by_date(start_date, end_date)
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            else:
                return Decimal("0.00")
        finally:
            db.close()


def _get_purchase_expend_by_date(start_date, end_date):
    max_retries = 3
    retry_delay = 0.5
    
    for attempt in range(max_retries):
        db = SessionLocal()
        repo = PurchaseInfoRepository(db)
        try:
            return repo.get_total_expend_by_date(start_date, end_date)
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            else:
                return Decimal("0.00")
        finally:
            db.close()


def _get_operating_expend_by_date(start_date, end_date):
    max_retries = 3
    retry_delay = 0.5
    
    for attempt in range(max_retries):
        db = SessionLocal()
        repo = OperatingExpenseRepository(db)
        try:
            return repo.get_total_amount_by_date(start_date, end_date)
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            else:
                return Decimal("0.00")
        finally:
            db.close()


def _get_loss_cost_by_date(start_date, end_date):
    """获取指定日期范围内的报损总成本"""
    max_retries = 3
    retry_delay = 0.5
    
    for attempt in range(max_retries):
        db = SessionLocal()
        repo = InventoryLossRepository(db)
        try:
            return repo.get_total_loss_cost_by_date(start_date, end_date)
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            else:
                return Decimal("0.00")
        finally:
            db.close()


async def _get_trend_chart_data_by_range(
    current_start: date,
    current_end: date,
) -> Dict[str, List]:
    """
    获取趋势图数据
    - custom类型：按业务月度聚合营收/支出数据
    """
    # 按业务月度聚合获取趋势数据，独立线程执行
    def _get_monthly_data():
        db = SessionLocal()
        sale_repo = SaleInfoRepository(db)
        purchase_repo = PurchaseInfoRepository(db)
        expense_repo = OperatingExpenseRepository(db)
        try:
            return _get_monthly_revenue_expend_sync(
                sale_repo, purchase_repo, expense_repo, current_start, current_end
            )
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


def _get_monthly_revenue_expend_sync(
    sale_repo: SaleInfoRepository,
    purchase_repo: PurchaseInfoRepository,
    expense_repo: OperatingExpenseRepository,
    start_date: date,
    end_date: date
) -> List[Dict]:
    """
    获取指定时间范围内的月度营收支出数据（基于业务月度）
    业务月度：每月26日至次月25日
    月度标签以周期结束日期的月份为准
    例如：2026-01-26 ~ 2026-02-25 属于 "2026-02" 月度
    """
    from dateutil.relativedelta import relativedelta
    
    # 生成业务月度周期列表
    monthly_periods = []
    
    # 找到第一个包含start_date的月度周期
    period_start, period_end = get_month_period(start_date)
    
    while period_start <= end_date:
        if period_end >= start_date:
            # 计算实际查询范围（与请求范围的交集）
            query_start = max(period_start, start_date)
            query_end = min(period_end, end_date)
            
            # 月度标签以周期结束日期的月份为准
            # 例如：2026-01-26 ~ 2026-02-25 属于 "2026-02" 月度
            monthly_periods.append({
                "label": f"{period_end.year}-{period_end.month:02d}",
                "start": query_start,
                "end": query_end
            })
        
        # 移动到下一个月度周期
        if period_start.month == 12:
            period_start = date(period_start.year + 1, 1, 26)
        else:
            period_start = date(period_start.year, period_start.month + 1, 26)
        
        if period_start.month == 12:
            period_end = date(period_start.year + 1, 1, 25)
        else:
            period_end = date(period_start.year, period_start.month + 1, 25)
    
    # 查询每个月度周期的数据
    monthly_data = []
    for period in monthly_periods:
        # 查询销售收入
        revenue = sale_repo.get_total_revenue_by_date(period["start"], period["end"]) or Decimal("0.00")
        
        # 查询采购支出
        purchase_expend = purchase_repo.get_total_expend_by_date(period["start"], period["end"]) or Decimal("0.00")
        
        # 查询运营杂费
        operating_expend = expense_repo.get_total_amount_by_date(period["start"], period["end"]) or Decimal("0.00")
        
        total_expend = float(purchase_expend) + float(operating_expend)
        
        monthly_data.append({
            "month": period["label"],
            "revenue": float(revenue),
            "expend": total_expend
        })
    
    return monthly_data


def _format_pie_data(data_list: List[Dict]) -> List[Dict[str, Any]]:
    """
    格式化饼图数据，计算各维度占比
    :param data_list: 原始数据 [{"name": "xxx", "value": 5000}, ...]
    :return: 带占比的饼图数据 [{"name": "", "value": 0.0, "proportion": 0.0}, ...]
    """
    if not data_list:
        return []
    
    # 合并含有"压痕线"的商品
    merged_data = {}
    for item in data_list:
        name = item["name"]
        value = item["value"]
        
        if "压痕线" in name or "反压线" in name:
            # 合并到"压痕线"项
            if "压痕线" not in merged_data and "反压线" not in merged_data:
                merged_data["压痕线"] = 0
            merged_data["压痕线"] += value
        else:
            # 其他商品保持原样
            if name not in merged_data:
                merged_data[name] = 0
            merged_data[name] += value
    
    # 合并客户利润分布数据
    # 汇源系客户：汇源, 马鞍山, 新马鞍山, 武强, 塞北 -> 合并成"汇源"
    huiyuan_customers = ["汇源", "马鞍山", "新马鞍山", "武强", "塞北"]
    # 玖龙系客户：玖龙, 重庆, 太仓, 成都, 泉州, 镇江 -> 合并成"玖龙"
    jiulong_customers = ["玖龙", "重庆", "太仓", "成都", "泉州", "镇江"]
    
    final_merged_data = {}
    huiyuan_total = 0
    jiulong_total = 0
    
    for name, value in merged_data.items():
        # 检查是否是汇源系客户
        is_huiyuan = any(customer in name for customer in huiyuan_customers)
        # 检查是否是玖龙系客户
        is_jiulong = any(customer in name for customer in jiulong_customers)
        
        if is_huiyuan:
            huiyuan_total += value
        elif is_jiulong:
            jiulong_total += value
        else:
            # 其他客户保持原样
            final_merged_data[name] = value
    
    # 添加合并后的汇源和玖龙数据
    if huiyuan_total > 0:
        final_merged_data["汇源"] = huiyuan_total
    if jiulong_total > 0:
        final_merged_data["玖龙"] = jiulong_total
    
    # 转换回列表格式
    processed_data = [
        {"name": name, "value": value}
        for name, value in final_merged_data.items()
    ]
    
    total = sum(item["value"] for item in processed_data)
    # 总价值为0时，占比默认0，避免除零错误
    if total == 0:
        return [
            {"name": item["name"], "value": float(item["value"]), "proportion": 0.0}
            for item in processed_data
        ]
    
    return [
        {
            "name": item["name"],
            "value": float(item["value"]),
            "proportion": round(item["value"] / total * 100, 2)
        }
        for item in processed_data
    ]
