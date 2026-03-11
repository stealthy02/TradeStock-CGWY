"""
FastAPI 应用主文件

该文件负责创建和配置 FastAPI 应用实例，包括：
- 数据库初始化
- 异常处理器注册
- 跨域中间件配置
- 路由注册
- 静态文件服务配置
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from starlette.staticfiles import StaticFiles as StarletteStaticFiles
from starlette.responses import Response
from pydantic import ValidationError
from sqlalchemy.orm import sessionmaker
import os
import time

from app.database import engine, Base
from app.models import *
from app import routers
from app.utils.exceptions import CustomAPIException
from app.schemas.common import ResponseModel


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理：数据库初始化
    
    Args:
        app (FastAPI): FastAPI 应用实例
    """
    print("正在初始化数据库...")
    try:
        # SQLite 自动创建数据库文件，直接创建数据表
        Base.metadata.create_all(bind=engine)
        print("所有数据表检查/创建完成")
        
    except Exception as e:
        print(f"数据库初始化失败: {e}")
        raise
    
    yield
    
    print("应用关闭")


# 创建 app 实例
app = FastAPI(
    title="商贸库存结算管理系统",
    description="基于FastAPI+sqlLite，实现商贸库存结算管理，包括采购、销售、结算周期管理等功能。",
    version="1.0.0",
    lifespan=lifespan
)


# -------------------------- 全局异常处理器 --------------------------

@app.exception_handler(CustomAPIException)
async def custom_api_exception_handler(request: Request, exc: CustomAPIException):
    """
    处理自定义API异常（业务中主动抛出的）
    
    Args:
        request (Request): 请求对象
        exc (CustomAPIException): 自定义异常实例
    
    Returns:
        JSONResponse: 统一格式的错误响应
    """
    return JSONResponse(
        status_code=200,  # HTTP统一200，业务code区分结果
        content=ResponseModel(
            code=exc.code,
            message=exc.message,
            data=exc.data
        ).model_dump()  # 复用项目统一响应模型
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    处理FastAPI/Pydantic默认参数校验异常
    
    Args:
        request (Request): 请求对象
        exc (RequestValidationError): 参数校验异常实例
    
    Returns:
        JSONResponse: 统一格式的错误响应
    """
    # 格式化默认校验错误信息，更友好
    error_msg = "; ".join([f"【{err['loc'][-1]}】{err['msg']}" for err in exc.errors()])
    return JSONResponse(
        status_code=200,
        content=ResponseModel(code=400, message=f"参数校验失败：{error_msg}").model_dump()
    )


@app.exception_handler(ValidationError)
async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
    """
    处理Pydantic兜底验证异常
    
    Args:
        request (Request): 请求对象
        exc (ValidationError): Pydantic验证异常实例
    
    Returns:
        JSONResponse: 统一格式的错误响应
    """
    error_msg = "; ".join([f"【{err['loc'][-1]}】{err['msg']}" for err in exc.errors()])
    return JSONResponse(
        status_code=200,
        content=ResponseModel(code=400, message=f"数据验证失败：{error_msg}").model_dump()
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    全局兜底异常（捕获所有未处理的异常）
    
    Args:
        request (Request): 请求对象
        exc (Exception): 异常实例
    
    Returns:
        JSONResponse: 统一格式的错误响应
    """
    # 打印异常日志，方便后端排查（生产环境建议用logging模块）
    print(f"⚠️  全局未捕获异常：{request.url} -> {exc}")
    return JSONResponse(
        status_code=200,
        content=ResponseModel(code=500, message="服务器内部错误，请联系管理员").model_dump()
    )


# -------------------------- 中间件配置 --------------------------

# 跨域中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------- 静态文件服务配置 --------------------------

# 确定静态文件目录路径
current_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
print(f"当前目录: {current_dir}")
print(f"当前工作目录: {os.getcwd()}")

# 静态文件目录
static_dir = None

# 开发环境路径 - 前端构建后的目录
dev_dist_path = os.path.join(os.path.dirname(current_dir), "frontend", "dist")
if os.path.exists(dev_dist_path) and os.path.isdir(dev_dist_path):
    index_path = os.path.join(dev_dist_path, "index.html")
    if os.path.exists(index_path):
        static_dir = dev_dist_path
        print(f"找到开发环境静态文件目录: {static_dir}")

# 如果没有找到开发环境静态文件目录，尝试其他可能的路径
if not static_dir:
    possible_paths = [
        os.path.join(current_dir, "dist"),
        os.path.join(os.path.dirname(current_dir), "dist"),
        os.path.join(current_dir, "frontend", "dist")
    ]
    
    for path in possible_paths:
        if os.path.exists(path) and os.path.isdir(path):
            index_path = os.path.join(path, "index.html")
            if os.path.exists(index_path):
                static_dir = path
                print(f"找到静态文件目录: {static_dir}")
                break

# 如果仍然没有找到静态文件目录，使用默认目录
if not static_dir:
    static_dir = os.path.join(current_dir, "static")
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
        print(f"创建默认静态文件目录: {static_dir}")
    else:
        print(f"使用默认静态文件目录: {static_dir}")
    
    # 在默认目录中创建一个简单的index.html文件
    index_path = os.path.join(static_dir, "index.html")
    if not os.path.exists(index_path):
        with open(index_path, "w", encoding="utf-8") as f:
            f.write("""
<!DOCTYPE html>
<html>
<head>
    <title>商贸库存结算管理系统</title>
    <meta charset="utf-8">
</head>
<body>
    <h1>商贸库存结算管理系统</h1>
    <p>前端文件`{index_path}`未找到，请检查打包配置。</p>
</body>
</html>
            """.format(index_path))
        print(f"在默认目录中创建index.html文件: {index_path}")


# -------------------------- 路由注册 --------------------------

# 注册所有路由（先注册API路由，确保优先级最高）
app.include_router(routers.home.router, prefix="/api", tags=["首页"])
app.include_router(routers.basic.router, prefix="/api/basic", tags=["基础信息"])
app.include_router(routers.purchase.router, prefix="/api/purchase", tags=["采购管理"])
app.include_router(routers.sale.router, prefix="/api/sale", tags=["销售管理"])
app.include_router(routers.inventory.router, prefix="/api/inventory", tags=["库存管理"])
app.include_router(routers.cost.router, prefix="/api/cost", tags=["成本费用"])


@app.get("/docs")
def read_docs():
    """
    API 文档路径
    
    Returns:
        dict: API 文档信息
    """
    return ResponseModel(data={"message": "商贸库存结算管理系统API", "docs": "/docs"}).model_dump()


# -------------------------- 静态文件挂载 --------------------------

class NoCacheStaticFiles(StaticFiles):
    """自定义静态文件类，添加禁用缓存的响应头"""
    async def get_response(self, path: str, scope):
        try:
            response = await super().get_response(path, scope)
        except Exception:
            # 如果文件不存在，返回 404 也要加缓存头
            from starlette.responses import Response
            response = Response(content="Not Found", status_code=404)
        
        # 为所有响应添加禁用缓存头（特别是 HTML 和 JS/CSS）
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        # 添加 Vary 头确保不同请求不会被缓存混淆
        response.headers["Vary"] = "*"
        return response

if static_dir:
    print(f"使用静态文件目录: {static_dir}")
    
    # 挂载静态资源（assets目录）- 使用无缓存版本
    assets_path = os.path.join(static_dir, "assets")
    if os.path.exists(assets_path):
        print(f"挂载assets目录: {assets_path}")
        app.mount("/assets", NoCacheStaticFiles(directory=assets_path), name="assets")
    else:
        print(f"assets目录不存在: {assets_path}")
    
    # 挂载静态文件目录，但不使用html=True，避免影响SPA路由
    print(f"挂载静态文件目录: {static_dir}")
    app.mount("/static", NoCacheStaticFiles(directory=static_dir), name="static")
    
    def add_no_cache_headers(response):
        """为响应添加禁用缓存的头部"""
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        response.headers["Vary"] = "*"
        return response
    
    # 服务器启动时间戳，用于缓存破坏
    SERVER_START_TIME = str(int(time.time()))
    
    def serve_index_html():
        """读取并返回 index.html，注入缓存破坏脚本"""
        index_path = os.path.join(static_dir, "index.html")
        if not os.path.exists(index_path):
            return None
        
        with open(index_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        timestamp = SERVER_START_TIME
        
        # 注入缓存破坏脚本：检测服务器重启并自动刷新
        cache_buster_script = f"""
        <script>
        (function() {{
            var serverVersion = "{timestamp}";
            var storedVersion = localStorage.getItem('app_server_version');
            var needsReload = false;
            
            // 检查是否是第一次访问或服务器已重启
            if (!storedVersion) {{
                console.log('首次访问，记录服务器版本...');
                localStorage.setItem('app_server_version', serverVersion);
            }} else if (storedVersion !== serverVersion) {{
                console.log('服务器已重启，需要刷新页面...');
                localStorage.setItem('app_server_version', serverVersion);
                needsReload = true;
            }}
            
            // 检测 JS 加载错误（404）
            window.addEventListener('error', function(e) {{
                if (e.target && e.target.tagName === 'SCRIPT') {{
                    var src = e.target.src || '';
                    if (src.includes('/assets/') && src.includes('.js')) {{
                        console.log('JS 文件加载失败:', src);
                        if (!sessionStorage.getItem('js_error_reloaded')) {{
                            sessionStorage.setItem('js_error_reloaded', '1');
                            location.reload(true);
                        }}
                    }}
                }}
            }}, true);
            
            // 如果需要刷新（服务器重启）
            if (needsReload) {{
                sessionStorage.removeItem('js_error_reloaded');
                location.reload(true);
            }}
        }})();
        </script>
        """
        
        # 在 </head> 前插入脚本
        content = content.replace("</head>", cache_buster_script + "</head>")
        
        response = HTMLResponse(content=content)
        return add_no_cache_headers(response)
    
    # 为SPA添加通配符路由，确保所有前端路由都返回index.html
    # 这个路由必须放在最后，确保API路由优先匹配
    @app.get("/{path:path}")
    async def serve_spa(path: str):
        """
        为SPA添加通配符路由，确保所有前端路由都返回index.html
        
        Args:
            path (str): 路径参数
        
        Returns:
            Response | dict: 文件响应或错误信息
        """
        # 先尝试直接返回静态文件（如果存在）
        file_path = os.path.join(static_dir, path) # type: ignore
        if os.path.exists(file_path) and os.path.isfile(file_path):
            response = FileResponse(file_path)
            # 为静态文件添加禁用缓存头
            return add_no_cache_headers(response)
        
        # 否则返回index.html，让前端路由处理
        response = serve_index_html()
        if response:
            return response
        
        return ResponseModel(data={"message": "页面未找到"}, code=404).model_dump()
    
    # 根路径处理
    @app.get("/")
    async def serve_root():
        """
        根路径返回index.html
        
        Returns:
            Response: index.html响应
        """
        response = serve_index_html()
        if response:
            return response
        return ResponseModel(data={"message": "页面未找到"}, code=404).model_dump()
else:
    print("警告: 未找到静态文件目录")
    
    # 如果找不到静态文件目录，仍然提供API服务
    @app.get("/")
    def read_root():
        """
        根路径处理
        
        Returns:
            FileResponse | dict: 文件响应或API信息
        """
        # 尝试在当前目录及其子目录中查找index.html文件
        def find_index_html(directory):
            for root, dirs, files in os.walk(directory):
                if "index.html" in files:
                    return os.path.join(root, "index.html")
            return None
        
        # 搜索index.html文件
        index_html_path = find_index_html(os.getcwd())
        if index_html_path:
            print(f"找到index.html文件: {index_html_path}")
            return FileResponse(index_html_path)
        
        # 如果仍然找不到index.html文件，返回API响应
        return ResponseModel(data={"message": "商贸库存结算管理系统API", "docs": "/docs"}).model_dump()
