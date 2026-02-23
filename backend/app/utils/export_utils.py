from typing import Dict, Any, Optional
from .dynamic_exporter import dynamic_export, get_available_exporters


import sys
from pathlib import Path
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


def auto_export(data: Dict[str, Any], bill_type: str = "purchase") -> bytes:
    """
    自动选择脚本导出数据
    
    逻辑：
    1. 根据供应商/采购商名称查找对应脚本
    2. 如果有，使用该脚本
    3. 如果没有，根据是采购还是销售，选择对应的通用脚本
    
    Args:
        data: 导出数据
        bill_type: 对账单类型，"purchase"或"sale"
    
    Returns:
        xlsx文件的字节流
    """
    log("=== auto_export 开始 ===")
    log(f"账单类型: {bill_type}")
    
    # 获取所有可用脚本
    log("开始获取可用脚本")
    available_scripts = get_available_exporters()
    log(f"可用脚本: {available_scripts}")
    
    # 确定名称键
    if bill_type == "purchase":
        name_key = "supplier_name"
        generic_script = "通用采购导出"
    else:
        name_key = "purchaser_name"
        generic_script = "通用销售导出"
    log(f"名称键: {name_key}, 通用脚本: {generic_script}")
    
    # 获取实体名称
    entity_name = data["bill_info"].get(name_key, "")
    log(f"实体名称: {entity_name}")
    
    # 先尝试查找与实体名称匹配的脚本
    if entity_name:
        # 精确匹配
        log(f"尝试精确匹配: {entity_name}")
        if entity_name in available_scripts:
            log(f"找到精确匹配脚本: {entity_name}")
            result = dynamic_export(data, entity_name)
            if result:
                log("精确匹配脚本执行成功")
                return result
        
        # 模糊匹配：脚本名包含实体名称
        log("尝试模糊匹配")
        for script in available_scripts:
            if entity_name in script:
                log(f"找到模糊匹配脚本: {script}")
                result = dynamic_export(data, script)
                if result:
                    log("模糊匹配脚本执行成功")
                    return result
        
        # 批量匹配：脚本名包含多个名称（如 name1-name2-name3_导出.py）
        log("尝试批量匹配")
        for script in available_scripts:
            # 分割脚本名中的多个名称
            # 移除后缀如 "_导出"
            script_base = script
            if "_导出" in script_base:
                script_base = script_base.replace("_导出", "")
            # 按 - 分割
            script_names = script_base.split("-")
            # 检查是否有任何一个名称与实体名称匹配
            for name in script_names:
                if entity_name == name.strip():
                    log(f"找到批量匹配脚本: {script}")
                    result = dynamic_export(data, script)
                    if result:
                        log("批量匹配脚本执行成功")
                        return result
    
    # 如果没有找到专用脚本，使用通用脚本
    log(f"使用通用脚本: {generic_script}")
    result = dynamic_export(data, generic_script)
    if result:
        log("通用脚本执行成功")
        return result
    
    # 如果通用脚本也失败了，返回空字节流
    log("所有脚本执行失败，返回空字节流")
    log("=== auto_export 结束 ===")
    return b""
