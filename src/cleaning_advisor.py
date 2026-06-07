"""根据数据画像生成可解释的数据清洗建议。"""

import re
from typing import Any, Dict, List


def generate_cleaning_suggestions(profile: Dict[str, Any]) -> List[str]:
    """根据缺失、重复、类型和异常值规则生成清洗建议。"""
    suggestions: List[str] = []

    for column, rate in profile["missing_rate"].items():
        if rate >= 50:
            suggestions.append(
                f"字段 `{column}` 缺失率为 {rate:.2f}%，建议评估业务价值后删除，"
                "或使用可靠的业务规则填补。"
            )
        elif rate > 0:
            suggestions.append(
                f"字段 `{column}` 缺失率为 {rate:.2f}%，建议区分随机缺失和业务缺失，"
                "再选择中位数、众数或分组填补。"
            )

    duplicate_count = profile["duplicate_count"]
    if duplicate_count:
        suggestions.append(
            f"检测到 {duplicate_count} 行完全重复数据，建议结合主键检查后去重，"
            "避免重复统计。"
        )

    for column, dtype in profile["dtypes"].items():
        column_lower = column.lower()
        if dtype in {"object", "string"} and any(
            keyword in column_lower
            for keyword in ("date", "time", "日期", "时间")
        ):
            suggestions.append(
                f"字段 `{column}` 可能是时间字段，建议使用 `pd.to_datetime` 转换并检查解析失败值。"
            )

    for column, summary in profile["possible_outliers"].items():
        if summary["count"] > 0:
            suggestions.append(
                f"数值字段 `{column}` 发现 {summary['count']} 个 IQR 潜在异常值，"
                "建议结合业务阈值判断保留、缩尾或修正。"
            )

    categorical_columns = list(profile["categorical_summary"])
    if categorical_columns:
        suggestions.append(
            "类别字段建议去除首尾空格、统一大小写和同义值，重点检查："
            + "、".join(f"`{column}`" for column in categorical_columns)
            + "。"
        )

    non_standard_columns = [
        column
        for column in profile["columns"]
        if column != column.lower()
        or " " in column
        or not re.fullmatch(r"[a-z0-9_\u4e00-\u9fff]+", column.lower())
    ]
    if non_standard_columns:
        suggestions.append(
            "建议将字段名统一为小写下划线格式，便于 Python 和 SQL 使用："
            + "、".join(f"`{column}`" for column in non_standard_columns)
            + "。"
        )
    else:
        suggestions.append("当前字段命名较规范，建议继续保持小写下划线风格。")

    if not suggestions:
        suggestions.append("暂未发现明显数据质量问题，建议结合业务规则继续核验字段口径。")

    return suggestions
