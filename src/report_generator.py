"""将分析 Workflow 的结果组装为 Markdown 报告。"""

from typing import Any, Dict, List

import pandas as pd


def _format_number(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def _sample_to_markdown(df: pd.DataFrame) -> str:
    """不依赖 tabulate，将少量数据样例转换为 Markdown 表格。"""
    sample = df.head(5).fillna("")
    columns = [str(column) for column in sample.columns]
    header = "| " + " | ".join(columns) + " |"
    separator = "|" + "|".join("---" for _ in columns) + "|"
    rows = []
    for row in sample.astype(str).itertuples(index=False, name=None):
        safe_values = [value.replace("|", "\\|").replace("\n", " ") for value in row]
        rows.append("| " + " | ".join(safe_values) + " |")
    return "\n".join([header, separator, *rows])


def generate_markdown_report(
    df: pd.DataFrame,
    profile: Dict[str, Any],
    scene_info: Dict[str, Any],
    cleaning_suggestions: List[str],
    analysis_suggestions: List[str],
    sql_templates: List[Dict[str, str]],
) -> str:
    """生成一份可下载的数据分析初步报告。"""
    lines = [
        "# DataPilot Agent 数据分析初步报告",
        "",
        "> 本报告由规则驱动的 DataPilot Agent Workflow 自动生成，结论需结合业务口径复核。",
        "",
        "## 1. 数据概览",
        "",
        f"- 数据行数：{profile['shape']['rows']}",
        f"- 数据列数：{profile['shape']['columns']}",
        f"- 重复行数：{profile['duplicate_count']}",
        "",
        "数据样例：",
        "",
        _sample_to_markdown(df),
        "",
        "## 2. 字段信息",
        "",
        "| 字段 | 类型 | 缺失数 | 缺失率 |",
        "|---|---|---:|---:|",
    ]

    for column in profile["columns"]:
        lines.append(
            f"| {column} | {profile['dtypes'][column]} | "
            f"{profile['missing_count'][column]} | "
            f"{profile['missing_rate'][column]:.2f}% |"
        )

    lines.extend(
        [
            "",
            "## 3. 数据质量检查",
            "",
            f"- 完全重复行：{profile['duplicate_count']} 行",
            f"- 存在缺失值的字段："
            f"{sum(count > 0 for count in profile['missing_count'].values())} 个",
            "",
            "### 数值字段统计",
            "",
            "| 字段 | 均值 | 最小值 | 最大值 | 中位数 | 标准差 | 潜在异常值数 |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )

    if profile["numeric_summary"]:
        for column, summary in profile["numeric_summary"].items():
            lines.append(
                f"| {column} | {_format_number(summary['mean'])} | "
                f"{_format_number(summary['min'])} | {_format_number(summary['max'])} | "
                f"{_format_number(summary['median'])} | {_format_number(summary['std'])} | "
                f"{profile['possible_outliers'][column]['count']} |"
            )
    else:
        lines.append("| - | - | - | - | - | - | - |")

    lines.extend(
        [
            "",
            "## 4. 业务场景推断",
            "",
            f"- 推断场景：**{scene_info['scene_name']}**",
            f"- 判断依据：{scene_info['reason']}",
            "",
            "可进一步关注的业务问题：",
            "",
        ]
    )
    lines.extend(f"- {question}" for question in scene_info["possible_business_questions"])

    lines.extend(["", "## 5. 清洗建议", ""])
    lines.extend(f"{index}. {item}" for index, item in enumerate(cleaning_suggestions, 1))

    lines.extend(["", "## 6. 后续分析建议", ""])
    lines.extend(f"{index}. {item}" for index, item in enumerate(analysis_suggestions, 1))

    lines.extend(["", "## 7. SQL 分析模板", ""])
    for template in sql_templates:
        lines.extend(
            [
                f"### {template['title']}",
                "",
                template["description"],
                "",
                "```sql",
                template["sql"],
                "```",
                "",
            ]
        )

    lines.extend(
        [
            "## 8. 总结",
            "",
            f"当前数据被初步识别为 **{scene_info['scene_name']}**。"
            "建议先处理缺失、重复和潜在异常值，再围绕核心业务指标开展分组、趋势和关联分析。"
            "本报告用于快速形成分析起点，不替代业务口径确认和人工判断。",
            "",
        ]
    )
    return "\n".join(lines)
