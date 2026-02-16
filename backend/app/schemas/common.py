from typing import Optional, Generic, TypeVar
from pydantic import BaseModel

T = TypeVar('T')

class ResponseModel(BaseModel, Generic[T]):
    code: int = 200
    message: str = "操作成功"
    data: Optional[T] = None

class PageModel(BaseModel, Generic[T]):
    total: int
    pages: int
    list: list[T]

# -------------------------- 新增：通用响应常量（可选但推荐） --------------------------
# 与测试用例中的COMMON_ASSERT["param_error"]匹配，全项目统一参数错误响应
PARAM_ERROR_RESP = ResponseModel(code=400, message="请求参数错误", data=None)
# 服务器内部错误通用响应
SERVER_ERROR_RESP = ResponseModel(code=500, message="服务器内部错误", data=None)
# 资源不存在通用响应
NOT_FOUND_RESP = ResponseModel(code=404, message="请求的资源不存在", data=None)