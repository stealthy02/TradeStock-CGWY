"""
服务器启动脚本

该脚本负责启动 FastAPI 服务器，处理端口冲突自动重试，并挂载前端静态文件。
支持开发环境和 Electron 打包环境的适配。
"""

import uvicorn
import socket
import sys
from pathlib import Path
from fastapi.staticfiles import StaticFiles

from app.main import app


def get_base_dir():
    """
    获取基础目录
    
    Returns:
        Path: 基础目录路径
    """
    # 如果在打包环境中，使用 sys._MEIPASS 获取打包后的资源目录
    if hasattr(sys, '_MEIPASS'):
        return Path(sys._MEIPASS)
    # 否则使用文件所在目录
    return Path(__file__).parent


def get_static_dir():
    """
    获取前端静态文件目录（适配开发/打包/Electron环境）
    
    Returns:
        Path: 前端静态文件目录路径
    """
    base_dir = get_base_dir()
    
    # 打包环境（Electron）：静态文件在可执行文件同级的 dist 目录
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller 打包后，sys._MEIPASS 是临时解压目录
        # 实际静态文件会被 Electron 放到 resources 目录下
        static_dir = Path(sys._MEIPASS).parent.parent / "dist"
    else:
        # 开发环境：指向 Vue 项目打包后的 dist 目录
        # 假设当前文件在 backend/ 目录，Vue 目录在 ../frontend/
        static_dir = base_dir.parent / "frontend" / "dist"
    
    return static_dir.resolve()


def is_port_available(host: str, port: int) -> bool:
    """
    检查指定端口是否可用
    
    Args:
        host (str): 主机地址
        port (int): 端口号
    
    Returns:
        bool: True 表示端口可用，False 表示已被占用
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        # 设置超时时间，避免阻塞
        sock.settimeout(1)
        # 尝试连接端口，如果连接成功说明端口已被占用
        result = sock.connect_ex((host, port))
        # 返回 True 表示端口可用，False 表示已被占用
        return result != 0


def run_server_with_port_fallback(host: str, start_port: int, max_retries: int = 5):
    """
    启动服务器，若端口被占用则自动重试后续端口
    挂载前端静态文件
    
    Args:
        host (str): 主机地址
        start_port (int): 起始端口号
        max_retries (int): 最大重试次数
    
    Raises:
        RuntimeError: 当所有端口都被占用时
    """
    # 挂载 Vue 静态文件
    try:
        static_dir = get_static_dir()
        if static_dir.exists():
            # 挂载静态文件，支持 SPA 路由（html=True）
            app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
            print(f"[成功] 挂载前端静态文件：{static_dir}")
            
            # 移除根路径的 API 路由，确保静态文件优先响应
            for route in app.routes:
                if hasattr(route, "path") and route.path == "/":
                    app.routes.remove(route)
                    print("[成功] 已移除根路径 API 路由，确保静态文件优先响应")
                    break
        else:
            print(f"[警告] 前端静态文件目录不存在：{static_dir}，仅启动 API 服务")
    except Exception as e:
        print(f"[警告] 挂载静态文件失败：{e}")

    current_port = start_port
    retries = 0
    
    while retries < max_retries:
        if is_port_available(host, current_port):
            # 端口可用，直接启动服务
            print(f"[成功] 端口 {current_port} 可用，启动 FastAPI 服务...")
            
            uvicorn.run(
                app,
                host=host,
                port=current_port,
                log_level="info",
                # 打包后建议关闭 reload
                reload=False
            )
            return
        else:
            # 端口被占用，提示并尝试下一个端口
            print(f"[错误] 端口 {current_port} 已被占用，尝试下一个端口...")
            current_port += 1
            retries += 1
    
    # 所有重试端口都被占用，抛出异常
    raise RuntimeError(
        f"[错误] 端口 {start_port} 到 {current_port-1} 均被占用，无法启动服务！\n"
        "请手动释放端口，或修改起始端口后重试。"
    )


if __name__ == "__main__":
    # 推荐将 host 改为 127.0.0.1（仅本地访问），避免局域网内其他设备占用
    # 如果需要局域网访问，保留 0.0.0.0 即可
    HOST = "127.0.0.1"  # 或 "0.0.0.0"
    START_PORT = 8000
    
    try:
        run_server_with_port_fallback(HOST, START_PORT)
    except RuntimeError as e:
        print(e)
        # 可选：手动指定一个备用端口（比如 8080）
        # uvicorn.run(app, host=HOST, port=8080)