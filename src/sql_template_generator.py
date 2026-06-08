"""根据字段特征生成通用 SQL 分析模板。"""

from typing import Dict, List, Optional

import pandas as pd


def _find_column(columns: List[str], keywords: tuple[str, ...]) -> Optional[str]:
    for column in columns:
        if any(keyword in column.lower() for keyword in keywords):
            return column
    return None


def _quote(column: str) -> str:
    return f"`{column}`"


def _find_category_column(df: pd.DataFrame, date_column: Optional[str]) -> Optional[str]:
    """优先选择适合分组分析的类别字段，避免直接按 ID 分组。"""
    categorical_columns = [
        str(column)
        for column in df.select_dtypes(include=["object", "category", "bool"]).columns
        if str(column) != date_column
        and not str(column).lower().endswith("_id")
        and str(column).lower() != "id"
    ]
    preferred = _find_column(
        categorical_columns,
        ("category", "status", "city", "channel", "type", "品类", "状态", "城市", "渠道"),
    )
    return preferred or (categorical_columns[0] if categorical_columns else None)


def generate_sql_templates(
    df: pd.DataFrame,
    scene_name: str,
    table_name: str = "your_table",
) -> List[Dict[str, str]]:
    """依据已有字段生成可复制修改的 SQL 模板。"""
    columns = [str(column) for column in df.columns]
    date_column = _find_column(columns, ("date", "time", "日期", "时间"))
    amount_column = _find_column(
        columns, ("amount", "price", "revenue", "sales", "金额", "价格", "收入")
    )
    quantity_column = _find_column(columns, ("quantity", "qty", "count", "数量"))
    user_column = _find_column(
        columns, ("user_id", "customer_id", "member_id", "用户", "客户")
    )

    category_column = _find_category_column(df, date_column)

    templates: List[Dict[str, str]] = [
        {
            "title": "查看总行数",
            "description": f"快速确认 `{scene_name}` 数据规模。",
            "sql": f"SELECT COUNT(*) AS total_rows\nFROM {table_name};",
        },
        {
            "title": "查看缺失情况",
            "description": (
                "SQL 的缺失检查通常按字段统计 NULL。可将下方示例中的字段替换或扩展；"
                "空字符串还需增加 TRIM(column) = '' 条件。"
            ),
            "sql": "SELECT\n"
            + ",\n".join(
                f"    SUM(CASE WHEN {_quote(column)} IS NULL THEN 1 ELSE 0 END) "
                f"AS {_quote(column + '_null_count')}"
                for column in columns[:8]
            )
            + f"\nFROM {table_name};",
        },
    ]

    if date_column:
        templates.append(
            {
                "title": "按日期聚合",
                "description": f"使用 `{date_column}` 观察每日数据量趋势。",
                "sql": (
                    f"SELECT DATE({_quote(date_column)}) AS stat_date,\n"
                    "       COUNT(*) AS record_count\n"
                    f"FROM {table_name}\n"
                    "GROUP BY DATE("
                    f"{_quote(date_column)})\nORDER BY stat_date;"
                ),
            }
        )

    if category_column:
        templates.append(
            {
                "title": "按类别分组统计",
                "description": f"按 `{category_column}` 比较不同类别的数据量。",
                "sql": (
                    f"SELECT {_quote(category_column)}, COUNT(*) AS record_count\n"
                    f"FROM {table_name}\n"
                    f"GROUP BY {_quote(category_column)}\n"
                    "ORDER BY record_count DESC;"
                ),
            }
        )

    if amount_column:
        quantity_expression = (
            f",\n       SUM({_quote(quantity_column)}) AS total_quantity"
            if quantity_column
            else ""
        )
        templates.append(
            {
                "title": "金额与数量汇总",
                "description": f"汇总 `{amount_column}` 等核心交易指标。",
                "sql": (
                    "SELECT\n"
                    "       COUNT(*) AS record_count,\n"
                    f"       SUM({_quote(amount_column)}) AS total_amount,\n"
                    f"       AVG({_quote(amount_column)}) AS avg_amount"
                    f"{quantity_expression}\n"
                    f"FROM {table_name};"
                ),
            }
        )

    if user_column:
        templates.append(
            {
                "title": "用户维度统计",
                "description": f"按 `{user_column}` 统计用户活跃或贡献。",
                "sql": (
                    f"SELECT {_quote(user_column)},\n"
                    "       COUNT(*) AS record_count"
                    + (
                        f",\n       SUM({_quote(amount_column)}) AS total_amount"
                        if amount_column
                        else ""
                    )
                    + f"\nFROM {table_name}\n"
                    f"GROUP BY {_quote(user_column)}\n"
                    "ORDER BY record_count DESC;"
                ),
            }
        )

    return templates


def generate_python_templates(df: pd.DataFrame, scene_name: str) -> List[Dict[str, str]]:
    """根据字段生成简洁的 Pandas 分析模板。"""
    columns = [str(column) for column in df.columns]
    date_column = _find_column(columns, ("date", "time", "日期", "时间"))
    amount_column = _find_column(columns, ("amount", "price", "revenue", "gmv", "金额", "价格"))
    category_column = _find_category_column(df, date_column)
    templates = [
        {
            "title": "基础数据质量检查",
            "description": "复核数据规模、缺失和重复情况。",
            "python": "print(df.shape)\nprint(df.isna().sum().sort_values(ascending=False))\nprint(df.duplicated().sum())",
        }
    ]
    if date_column:
        templates.append(
            {
                "title": "时间趋势分析",
                "description": f"按 `{date_column}` 汇总每日记录量。",
                "python": (
                    f"df['{date_column}'] = pd.to_datetime(df['{date_column}'], errors='coerce')\n"
                    f"daily = df.groupby(df['{date_column}'].dt.date).size()\n"
                    "print(daily)"
                ),
            }
        )
    if category_column:
        value_expression = f"['{amount_column}'].sum()" if amount_column else ".size()"
        templates.append(
            {
                "title": "业务维度贡献分析",
                "description": f"按 `{category_column}` 计算贡献排名。",
                "python": (
                    f"ranking = df.groupby('{category_column}'){value_expression}\n"
                    "print(ranking.sort_values(ascending=False).head(10))"
                ),
            }
        )
    return templates
