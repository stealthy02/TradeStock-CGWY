"""
首页路由模块

该模块定义了首页相关的 API 路由，包括核心数据、数字卡片、饼状图和趋势图等接口。
"""

from fastapi import APIRouter, Query
from typing import Optional

from app.schemas.common import ResponseModel
from app.services import home_service
from app.utils.exceptions import ParamErrorException


router = APIRouter()


@router.get("/home/data", response_model=ResponseModel[dict])
async def get_home_data(
    time_type: Optional[str] = Query("month", description="month/year/all/custom"),
    start_date: Optional[str] = Query(None, description="开始时间 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束时间 YYYY-MM-DD")
):
    """
    查询首页核心数据（数字卡片+趋势图+饼状图）
    
    Args:
        time_type (Optional[str]): 时间类型，可选值：month/year/all/custom
        start_date (Optional[str]): 开始时间，格式：YYYY-MM-DD
        end_date (Optional[str]): 结束时间，格式：YYYY-MM-DD
    
    Returns:
        ResponseModel[dict]: 首页核心数据
    
    Raises:
        ParamErrorException: 参数错误时抛出
    """
    # 参数逻辑校验
    if time_type == "custom":
        if not start_date or not end_date:
            raise ParamErrorException(message="自定义时间查询时，开始时间和结束时间必须同时传入")
        if start_date > end_date:
            raise ParamErrorException(message="开始时间不能晚于结束时间")
    
    result = await home_service.get_home_data(time_type, start_date, end_date)
    return ResponseModel(data=result)


@router.get("/home/statistic-card", response_model=ResponseModel[dict])
async def get_statistic_card(
    time_type: Optional[str] = Query(None, description="month/year/all/custom"),
    start_date: Optional[str] = Query(None, description="开始时间 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束时间 YYYY-MM-DD")
):
    """
    查询数字卡片数据
    
    Args:
        time_type (Optional[str]): 时间类型，可选值：month/year/all/custom
        start_date (Optional[str]): 开始时间，格式：YYYY-MM-DD
        end_date (Optional[str]): 结束时间，格式：YYYY-MM-DD
    
    Returns:
        ResponseModel[dict]: 数字卡片数据
    """
    result = await home_service.get_statistic_card_data(time_type, start_date, end_date)
    return ResponseModel(data=result)


@router.get("/home/pie-chart", response_model=ResponseModel[dict])
async def get_pie_chart(
    time_type: Optional[str] = Query("month", description="month/year/all/custom"),
    start_date: Optional[str] = Query(None, description="开始时间 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束时间 YYYY-MM-DD")
):
    """
    查询饼状图数据
    
    Args:
        time_type (Optional[str]): 时间类型，可选值：month/year/all/custom
        start_date (Optional[str]): 开始时间，格式：YYYY-MM-DD
        end_date (Optional[str]): 结束时间，格式：YYYY-MM-DD
    
    Returns:
        ResponseModel[dict]: 饼状图数据
    
    Raises:
        ParamErrorException: 参数错误时抛出
    """
    # 参数逻辑校验
    if time_type == "custom":
        if not start_date or not end_date:
            raise ParamErrorException(message="自定义时间查询时，开始时间和结束时间必须同时传入")
        if start_date > end_date:
            raise ParamErrorException(message="开始时间不能晚于结束时间")
    
    result = await home_service.get_pie_chart_data(time_type, start_date, end_date)
    return ResponseModel(data=result)


@router.get("/home/trend-chart", response_model=ResponseModel[dict])
async def get_trend_chart(
    time_type: Optional[str] = Query("all", description="month/year/all/custom"),
    start_date: Optional[str] = Query(None, description="开始时间 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束时间 YYYY-MM-DD")
):
    """
    查询趋势图数据
    
    Args:
        time_type (Optional[str]): 时间类型，可选值：month/year/all/custom
        start_date (Optional[str]): 开始时间，格式：YYYY-MM-DD
        end_date (Optional[str]): 结束时间，格式：YYYY-MM-DD
    
    Returns:
        ResponseModel[dict]: 趋势图数据
    
    Raises:
        ParamErrorException: 参数错误时抛出
    """
    # 参数逻辑校验
    if time_type == "custom":
        if not start_date or not end_date:
            raise ParamErrorException(message="自定义时间查询时，开始时间和结束时间必须同时传入")
        if start_date > end_date:
            raise ParamErrorException(message="开始时间不能晚于结束时间")
    
    result = await home_service.get_trend_chart_data(time_type, start_date, end_date)
    return ResponseModel(data=result)