from typing import Dict, Any, List
from datetime import datetime
import os
import sys
import re
import csv
from openpyxl import load_workbook
from openpyxl.styles import Font, Border, Side, PatternFill, Alignment
from io import BytesIO
from pathlib import Path
import decimal


def get_base_dir():
    """获取正确的基础目录"""
    if hasattr(sys, '_MEIPASS'):
        return Path(sys._MEIPASS)
    # 开发环境：从脚本所在目录向上两级
    return Path(__file__).parent.parent


def _format_value(value, field_type: str = "text"):
    """
    格式化值，解决精度丢失问题，数值最多保留两位小数（实际有几位显示几位）
    
    Args:
        value: 要格式化的值
        field_type: 字段类型，可选 "text"（文本）、"numeric"（数值）
    Returns:
        格式化后的值
    """
    if value is None or value == "":
        return ""
    
    # 日期类型统一格式化
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d")
    
    # 只有数值类型字段才做小数处理
    if field_type == "numeric":
        try:
            # 使用decimal解决精度问题
            if isinstance(value, (int, float)):
                num = decimal.Decimal(str(value)).quantize(decimal.Decimal('0.00'), rounding=decimal.ROUND_HALF_UP)
            else:
                num = decimal.Decimal(str(value)).quantize(decimal.Decimal('0.00'), rounding=decimal.ROUND_HALF_UP)
            
            # 去除末尾无用的0，最多保留两位小数
            num_str = str(num).rstrip('0').rstrip('.') if '.' in str(num) else str(num)
            # 如果是空（比如0.00处理后变成空），返回0
            return num_str if num_str else "0"
        except (ValueError, TypeError, decimal.InvalidOperation):
            pass
    
    # 文本类型直接返回字符串，不做小数处理
    return str(value)


def load_product_units() -> Dict[str, str]:
    """
    加载商品单位映射
    从脚本同级目录的商品单位.csv文件读取
    
    Returns:
        商品名称到数量单位的映射字典
    """
    units_map = {}
    
    try:
        # 获取脚本所在目录
        script_dir = Path(__file__).parent
        csv_path = script_dir / "商品单位.csv"
        
        if csv_path.exists():
            with open(csv_path, 'r', encoding='gb2312') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    product_name = row.get("name", "").strip()
                    unit = row.get("unit", "").strip()
                    if product_name and unit:
                        units_map[product_name] = unit
    except Exception as e:
        print(f"加载商品单位失败: {e}")
    
    return units_map


def load_material_number_mapping() -> Dict[str, str]:
    """
    加载物料编号映射
    从脚本同级目录的物料编号对照表.csv文件读取
    
    Returns:
        customer_product_name到物料编号的映射字典
    """
    material_map = {}
    
    try:
        # 获取脚本所在目录
        script_dir = Path(__file__).parent
        csv_path = script_dir / "物料编号对照表.csv"
        
        if csv_path.exists():
            with open(csv_path, 'r', encoding='gb2312') as f:
                reader = csv.DictReader(f)
                # 检查csv列名是否正确
                header = reader.fieldnames
                if not header or "key" not in header or "value" not in header:
                    print("物料编号对照表.csv列名错误，需要包含key和value列")
                    return material_map
                    
                for row in reader:
                    key = row.get("key", "").strip()
                    value = row.get("value", "").strip()
                    if key and value:
                        material_map[key] = value
        else:
            print("物料编号对照表.csv文件不存在")
    except Exception as e:
        print(f"加载物料编号失败: {e}")
    
    return material_map


def export(data: Dict[str, Any]) -> bytes:
    base_dir = get_base_dir()
    
    # 加载商品单位映射和物料编号映射
    product_units = load_product_units()
    material_number_map = load_material_number_mapping()
    
    # 优先检查 exe 所在目录是否有 public 文件夹
    exe_dir = None
    if hasattr(sys, 'executable') and sys.executable:
        exe_dir = Path(sys.executable).parent
        external_public = exe_dir / "public"
        if external_public.exists():
            base_dir = exe_dir
    
    template_base_dir = base_dir / "public" / "sale"
    
    entity_name = data["bill_info"].get("purchaser_name", "")
    
    template_files = []
    if template_base_dir.exists():
        template_files = [f.name for f in template_base_dir.iterdir() if f.suffix == ".xlsx"]
    
    template_path = None
    if entity_name:
        specific_template = f"{entity_name}_模板.xlsx"
        if specific_template in template_files:
            template_path = template_base_dir / specific_template
    
    if not template_path:
        generic_template = "通用模板.xlsx"
        if generic_template in template_files:
            template_path = template_base_dir / generic_template
    
    if not template_path:
        return b""
    
    wb = load_workbook(template_path)
    ws = wb.active
    
    bill_info = data["bill_info"]
    
    start_date = bill_info.get("start_date")
    end_date = bill_info.get("end_date")
    if not end_date or end_date == "":
        end_date = datetime.now().strftime("%Y-%m-%d")
    
    # 账单信息中的数值字段指定为 numeric 类型
    replace_mapping = {
        "{{supplier_name}}": _format_value(bill_info.get("supplier_name")),
        "{{purchaser_name}}": _format_value(bill_info.get("purchaser_name")),
        "{{start_date}}": _format_value(start_date),
        "{{end_date}}": _format_value(end_date),
        "{{bill_amount}}": _format_value(bill_info.get("statement_amount"), "numeric"),
        "{{statement_amount}}": _format_value(bill_info.get("statement_amount"), "numeric")
    }
    
    for row in ws.iter_rows():
        for cell in row:
            if cell.value:
                cell_value = str(cell.value)
                for placeholder, value in replace_mapping.items():
                    if placeholder in cell_value:
                        cell.value = cell_value.replace(placeholder, value)
            elif ws.merged_cells.ranges and any(cell.coordinate in r for r in ws.merged_cells.ranges):
                for merged_range in ws.merged_cells.ranges:
                    if cell.coordinate in merged_range:
                        top_left_cell = ws.cell(merged_range.min_row, merged_range.min_col)
                        if top_left_cell.value:
                            cell_value = str(top_left_cell.value)
                            for placeholder, value in replace_mapping.items():
                                if placeholder in cell_value:
                                    top_left_cell.value = cell_value.replace(placeholder, value)
                        break
    
    # 直接使用原始数据，不再合并压痕线
    list_data = data.get("sale_list", {}).get("list", [])
    
    if list_data:
        list_data_row = None
        fixed_rows = None
        for idx, row in enumerate(ws.iter_rows(), 1):
            for cell in row:
                if cell.value:
                    cell_value = str(cell.value)
                    match = re.search(r'<list_data(:\d+)?>', cell_value)
                    if match:
                        list_data_row = idx
                        if match.group(1):
                            fixed_rows = int(match.group(1)[1:])
                        cell.value = cell_value.replace(match.group(0), "")
                        break
            if list_data_row:
                break
        
        if list_data_row:
            if fixed_rows:
                needed_rows = max(fixed_rows, len(list_data))
            else:
                needed_rows = len(list_data)
            
            template_cells = {}
            for cell in ws[list_data_row]:
                template_cells[cell.column] = {
                    "value": cell.value,
                    "font": cell.font,
                    "border": cell.border,
                    "fill": cell.fill,
                    "alignment": cell.alignment,
                    "number_format": cell.number_format
                }
            
            for i in range(needed_rows - 1):
                ws.insert_rows(list_data_row + i + 1)
            
            for i in range(needed_rows):
                current_row = list_data_row + i
                
                if i < len(list_data):
                    row_data = list_data[i]
                else:
                    row_data = {}
                
                # 获取商品数量单位：包含"压痕线"的都按"压痕线"匹配
                product_name = row_data.get("product_name", "").strip()
                unit_key = "压痕线" if "压痕线" in product_name else product_name
                unit = product_units.get(unit_key, "")
                
                # 获取物料编号
                customer_product_name = row_data.get("customer_product_name", "").strip()
                material_number = material_number_map.get(customer_product_name, "")
                
                for col, template_info in template_cells.items():
                    target_cell = ws.cell(row=current_row, column=col)
                    
                    if template_info["font"]:
                        target_cell.font = template_info["font"].copy()
                    if template_info["border"]:
                        target_cell.border = template_info["border"].copy()
                    if template_info["fill"]:
                        target_cell.fill = template_info["fill"].copy()
                    if template_info["alignment"]:
                        target_cell.alignment = template_info["alignment"].copy()
                    if template_info["number_format"]:
                        target_cell.number_format = template_info["number_format"]
                    
                    if template_info["value"]:
                        cell_value = str(template_info["value"])
                        
                        # 明确区分文本字段和数值字段，新增物料编号字段
                        field_mapping = {
                            "{{product_name}}": _format_value(row_data.get("product_name")),
                            "{{customer_product_name}}": _format_value(row_data.get("customer_product_name")),
                            "{{sale_date}}": _format_value(row_data.get("sale_date")),
                            "{{total_num}}": _format_value(row_data.get("total_num"), "numeric"),
                            "{{total_kg}}": _format_value(row_data.get("total_kg"), "numeric"),
                            "{{total_price}}": _format_value(row_data.get("total_price"), "numeric"),
                            "{{product_spec}}": _format_value(row_data.get("product_spec")),
                            "{{remark}}": _format_value(row_data.get("remark")),
                            "{{unit_price}}": _format_value(row_data.get("unit_price"), "numeric"),
                            "{{unit}}": _format_value(unit),
                            "{{material_number}}": _format_value(material_number)  # 新增物料编号字段
                        }
                        
                        for placeholder, value in field_mapping.items():
                            if placeholder in cell_value:
                                cell_value = cell_value.replace(placeholder, value)
                        
                        target_cell.value = cell_value
                    else:
                        target_cell.value = None
    
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    return output.getvalue()