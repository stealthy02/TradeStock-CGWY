"""
项目自定义异常类：全项目的业务异常都集中在此定义
"""
from fastapi import HTTPException


class CustomAPIException(Exception):
    """
    项目核心自定义API异常
    用于业务逻辑中主动抛出，配合全局处理器返回统一的code/message/data格式
    """
    def __init__(self, code: int, message: str, data: any = None):
        self.code = code
        self.message = message
        self.data = data


class NotFoundException(CustomAPIException):
    """资源不存在异常（通用404）"""
    def __init__(self, message: str = "请求的资源不存在", data: any = None):
        super().__init__(code=404, message=message, data=data)


class ParamErrorException(CustomAPIException):
    """参数错误异常（通用400，和你测试用例的param_error匹配）"""
    def __init__(self, message: str = "请求参数错误", data: any = None):
        super().__init__(code=400, message=message, data=data)


class ServerErrorException(CustomAPIException):
    """服务器内部错误（通用500）"""
    def __init__(self, message: str = "服务器内部错误，请联系管理员", data: any = None):
        super().__init__(code=500, message=message, data=data)