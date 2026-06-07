"""数据画像与数据质量检查。"""

from typing import Any, Dict

import numpy as np
import pandas as pd


def _to_python_value(value: Any) -> Any:
    """将 numpy/pandas 标量转换为便于展示和序列化的 Python 类型。"""
    if pd.isna(value):
        return None
    if isinstance(value, np.generic):
        return value.item()
    return value


def get_basic_profile(df: pd.DataFrame) -> Dict[str, Any]:
    """生成基础数据画像和轻量级质量检查结果。"""
    row_count = len(df)
    missing_count = df.isna().sum()
    missing_rate = missing_count.div(row_count).mul(100) if row_count else missing_count

    numeric_df = df.select_dtypes(include=np.number)
    numeric_summary: Dict[str, Dict[str, Any]] = {}
    possible_outliers: Dict[str, Dict[str, Any]] = {}

    for column in numeric_df.columns:
        series = numeric_df[column].dropna()
        numeric_summary[column] = {
            "mean": _to_python_value(series.mean()) if not series.empty else None,
            "min": _to_python_value(series.min()) if not series.empty else None,
            "max": _to_python_value(series.max()) if not series.empty else None,
            "median": _to_python_value(series.median()) if not series.empty else None,
            "std": _to_python_value(series.std()) if len(series) > 1 else None,
        }

        if series.empty:
            possible_outliers[column] = {
                "count": 0,
                "lower_bound": None,
                "upper_bound": None,
            }
            continue

        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        outlier_count = int(((series < lower_bound) | (series > upper_bound)).sum())
        possible_outliers[column] = {
            "count": outlier_count,
            "lower_bound": _to_python_value(lower_bound),
            "upper_bound": _to_python_value(upper_bound),
        }

    categorical_columns = df.select_dtypes(
        include=["object", "category", "bool"]
    ).columns
    categorical_summary: Dict[str, Dict[str, Any]] = {}
    for column in categorical_columns:
        series = df[column].dropna()
        value_counts = series.value_counts()
        categorical_summary[column] = {
            "unique_count": int(series.nunique()),
            "top": _to_python_value(value_counts.index[0]) if not value_counts.empty else None,
            "top_frequency": int(value_counts.iloc[0]) if not value_counts.empty else 0,
        }

    return {
        "shape": {"rows": int(df.shape[0]), "columns": int(df.shape[1])},
        "columns": [str(column) for column in df.columns],
        "dtypes": {str(column): str(dtype) for column, dtype in df.dtypes.items()},
        "missing_count": {str(column): int(value) for column, value in missing_count.items()},
        "missing_rate": {
            str(column): round(float(value), 2) for column, value in missing_rate.items()
        },
        "duplicate_count": int(df.duplicated().sum()),
        "numeric_summary": numeric_summary,
        "categorical_summary": categorical_summary,
        "possible_outliers": possible_outliers,
    }
