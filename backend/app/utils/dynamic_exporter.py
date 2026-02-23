from typing import Dict, Any, Optional, Callable
import os
import sys
import importlib.util
from pathlib import Path


import os
from datetime import datetime, timedelta

def log(message: str):
    """
    写入调试日志
    使用相对路径，按日期命名，保留7天
    """
    try:
        # 获取日志目录
        if hasattr(sys, '_MEIPASS'):
            base_dir = Path(sys.executable).parent
        else:
            base_dir = Path(__file__).parent.parent.parent
        
        logs_dir = base_dir / "logs"
        logs_dir.mkdir(exist_ok=True)
        
        # 生成今天的日志文件名
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = logs_dir / f"{today}.log"
        
        # 写入日志
        with open(log_file, 'a', encoding='utf-8') as f:
            timestamp = datetime.now().strftime("%H:%M:%S")
            f.write(f"[{timestamp}] {message}\n")
        
        # 清理7天前的日志
        cleanup_old_logs(logs_dir)
    except Exception as e:
        pass

def cleanup_old_logs(logs_dir: Path):
    """
    清理7天前的日志文件
    """
    try:
        seven_days_ago = datetime.now() - timedelta(days=7)
        
        for file in logs_dir.iterdir():
            if file.suffix == '.log':
                try:
                    # 解析文件名中的日期
                    file_date = datetime.strptime(file.stem, "%Y-%m-%d")
                    if file_date < seven_days_ago:
                        file.unlink()
                except ValueError:
                    # 文件名格式不正确，跳过
                    pass
    except Exception:
        pass


def get_scripts_dir() -> Path:
    """
    获取脚本目录
    
    Returns:
        脚本目录路径
    """
    log("=== get_scripts_dir 开始 ===")
    
    if hasattr(sys, '_MEIPASS'):
        # 打包后，使用可执行文件所在目录的 scripts 文件夹
        log(f"检测到 _MEIPASS: {sys._MEIPASS}")
        log(f"可执行文件路径: {sys.executable}")
        base_dir = Path(sys.executable).parent
        log(f"可执行文件所在目录: {base_dir}")
    else:
        # 开发环境，使用项目根目录的 scripts 文件夹
        current_file = Path(__file__)
        log(f"当前文件路径: {current_file}")
        base_dir = current_file.parent.parent.parent
        log(f"项目根目录: {base_dir}")
    
    scripts_dir = base_dir / "scripts"
    log(f"脚本目录: {scripts_dir}")
    log(f"脚本目录是否存在: {scripts_dir.exists()}")
    
    try:
        scripts_dir.mkdir(exist_ok=True)
        log("脚本目录创建/存在成功")
    except Exception as e:
        log(f"创建脚本目录失败: {e}")
    
    log("=== get_scripts_dir 结束 ===")
    return scripts_dir


def load_exporter_script(script_name: str) -> Optional[Callable]:
    """
    动态加载导出脚本
    
    Args:
        script_name: 脚本名称（不含 .py 扩展名）
    
    Returns:
        导出函数，如果加载失败返回 None
    """
    log(f"=== load_exporter_script 开始: {script_name} ===")
    
    scripts_dir = get_scripts_dir()
    script_path = scripts_dir / f"{script_name}.py"
    log(f"脚本路径: {script_path}")
    log(f"脚本文件是否存在: {script_path.exists()}")
    
    if not script_path.exists():
        log("脚本文件不存在，返回 None")
        log("=== load_exporter_script 结束: 返回 None ===")
        return None
    
    try:
        # 动态加载模块
        log("开始加载模块")
        spec = importlib.util.spec_from_file_location(script_name, script_path)
        log(f"spec 是否创建成功: {spec is not None}")
        
        if spec and spec.loader:
            log("创建模块对象")
            module = importlib.util.module_from_spec(spec)
            log("执行模块")
            spec.loader.exec_module(module)
            log("模块执行完成")
            
            # 检查是否有 export 函数
            log(f"是否有 export 函数: {hasattr(module, 'export')}")
            if hasattr(module, 'export'):
                log(f"export 是否可调用: {callable(module.export)}")
                if callable(module.export):
                    log("=== load_exporter_script 结束: 返回 export 函数 ===")
                    return module.export
    except Exception as e:
        log(f"加载脚本失败: {e}")
    
    log("=== load_exporter_script 结束: 返回 None ===")
    return None


def get_available_exporters() -> list:
    """
    获取所有可用的导出脚本
    
    Returns:
        脚本名称列表
    """
    log("=== get_available_exporters 开始 ===")
    
    scripts_dir = get_scripts_dir()
    log(f"脚本目录: {scripts_dir}")
    log(f"脚本目录是否存在: {scripts_dir.exists()}")
    
    if not scripts_dir.exists():
        log("脚本目录不存在，返回空列表")
        log("=== get_available_exporters 结束: 返回空列表 ===")
        return []
    
    exporters = []
    try:
        files = list(scripts_dir.iterdir())
        log(f"目录中的文件数: {len(files)}")
        for file in files:
            log(f"文件: {file.name}, 后缀: {file.suffix}, 是否是文件: {file.is_file()}")
            if file.suffix == ".py" and file.is_file():
                exporters.append(file.stem)
                log(f"添加脚本: {file.stem}")
    except Exception as e:
        log(f"遍历目录失败: {e}")
    
    log(f"找到的脚本列表: {exporters}")
    log("=== get_available_exporters 结束 ===")
    return exporters


def dynamic_export(data: Dict[str, Any], script_name: str) -> Optional[bytes]:
    """
    使用动态脚本导出数据
    
    Args:
        data: 导出数据
        script_name: 脚本名称
    
    Returns:
        导出的字节流，如果失败返回 None
    """
    log(f"=== dynamic_export 开始: {script_name} ===")
    
    exporter = load_exporter_script(script_name)
    log(f"加载导出函数结果: {exporter is not None}")
    
    if exporter:
        try:
            log("开始执行导出函数")
            result = exporter(data)
            log(f"导出函数执行完成，返回值类型: {type(result)}")
            log(f"返回值是否为字节流: {isinstance(result, bytes)}")
            log("=== dynamic_export 结束: 成功 ===")
            return result
        except Exception as e:
            log(f"执行导出脚本失败: {e}")
    else:
        log("导出函数加载失败")
    
    log("=== dynamic_export 结束: 失败 ===")
    return None
