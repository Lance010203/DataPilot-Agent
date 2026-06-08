"""Human-in-the-loop 基础数据清洗工具。"""

import re
from typing import Dict, List, Tuple

import pandas as pd


TIME_KEYWORDS = ("date", "time", "datetime", "日期", "时间")


def standardize_column_name(column: object) -> str:
    """将字段名转换为小写下划线格式，并保留中文字符。"""
    name = str(column).strip().lower()
    name = re.sub(r"[\s\-/]+", "_", name)
    name = re.sub(r"[^\w\u4e00-\u9fff]", "_", name)
    name = re.sub(r"_+", "_", name).strip("_")
    return name or "unnamed_column"


def standardize_column_names(columns: List[object]) -> Tuple[List[str], Dict[str, str]]:
    """标准化字段名，并为冲突字段增加数字后缀。"""
    normalized: List[str] = []
    mapping: Dict[str, str] = {}
    used: Dict[str, int] = {}

    for column in columns:
        original = str(column)
        base_name = standardize_column_name(column)
        used[base_name] = used.get(base_name, 0) + 1
        final_name = (
            base_name
            if used[base_name] == 1
            else f"{base_name}_{used[base_name]}"
        )
        normalized.append(final_name)
        mapping[original] = final_name

    return normalized, mapping


def find_time_columns(df: pd.DataFrame) -> List[str]:
    """根据字段类型和字段名识别候选时间字段。"""
    candidates: List[str] = []
    for column in df.columns:
        column_name = str(column)
        if pd.api.types.is_datetime64_any_dtype(df[column]) or any(
            keyword in column_name.lower() for keyword in TIME_KEYWORDS
        ):
            candidates.append(column_name)
    return candidates


def get_high_missing_columns(
    df: pd.DataFrame,
    threshold: float = 50.0,
) -> Dict[str, float]:
    """返回缺失率达到阈值的字段，不执行删除。"""
    if df.empty:
        return {}
    rates = df.isna().mean().mul(100)
    return {
        str(column): round(float(rate), 2)
        for column, rate in rates.items()
        if rate >= threshold
    }


def clean_dataframe(
    df: pd.DataFrame,
    remove_duplicates: bool = False,
    normalize_columns: bool = False,
    convert_datetime: bool = False,
    high_missing_threshold: float = 50.0,
) -> Tuple[pd.DataFrame, Dict[str, object]]:
    """按用户选择执行基础清洗，并返回清洗结果和操作日志。"""
    cleaned = df.copy()
    operations: List[str] = []
    column_mapping: Dict[str, str] = {}
    converted_time_columns: List[str] = []

    before_shape = {"rows": int(df.shape[0]), "columns": int(df.shape[1])}
    high_missing_columns = get_high_missing_columns(df, high_missing_threshold)

    if remove_duplicates:
        before_rows = len(cleaned)
        cleaned = cleaned.drop_duplicates().reset_index(drop=True)
        removed_count = before_rows - len(cleaned)
        operations.append(f"删除完全重复行：{removed_count} 行。")

    if normalize_columns:
        normalized_columns, column_mapping = standardize_column_names(
            list(cleaned.columns)
        )
        cleaned.columns = normalized_columns
        changed_count = sum(
            original != normalized
            for original, normalized in column_mapping.items()
        )
        operations.append(f"字段名标准化：调整 {changed_count} 个字段。")

    if convert_datetime:
        time_columns = find_time_columns(cleaned)
        for column in time_columns:
            if pd.api.types.is_datetime64_any_dtype(cleaned[column]):
                converted_time_columns.append(column)
                continue

            converted = pd.to_datetime(cleaned[column], errors="coerce")
            if converted.notna().mean() >= 0.6:
                cleaned[column] = converted
                converted_time_columns.append(column)

        if converted_time_columns:
            operations.append(
                "时间字段转换："
                + "、".join(f"`{column}`" for column in converted_time_columns)
                + "。"
            )
        else:
            operations.append("未发现可可靠转换的时间字段，数据保持不变。")

    if not operations:
        operations.append("未勾选清洗操作，当前数据保持原样。")

    log: Dict[str, object] = {
        "before_shape": before_shape,
        "after_shape": {
            "rows": int(cleaned.shape[0]),
            "columns": int(cleaned.shape[1]),
        },
        "operations": operations,
        "column_mapping": column_mapping,
        "converted_time_columns": converted_time_columns,
        "high_missing_columns": high_missing_columns,
    }
    return cleaned, log


def dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
    """将清洗后的数据转换为带 UTF-8 BOM 的 CSV，便于 Excel 打开中文。"""
    return df.to_csv(index=False).encode("utf-8-sig")
