"""生成结论先行的 Markdown 初步商业分析报告。"""

from typing import Any, Dict, List, Optional

import pandas as pd


def _sample_to_markdown(df: pd.DataFrame) -> str:
    sample = df.head(5).fillna("")
    columns = [str(column) for column in sample.columns]
    rows = [
        "| " + " | ".join(value.replace("|", "\\|") for value in row) + " |"
        for row in sample.astype(str).itertuples(index=False, name=None)
    ]
    return "\n".join([
        "| " + " | ".join(columns) + " |",
        "|" + "|".join("---" for _ in columns) + "|",
        *rows,
    ])


def _scene_value(scene_info: Dict[str, Any], key: str, legacy: str, default: Any) -> Any:
    return scene_info.get(key, scene_info.get(legacy, default))


def generate_markdown_report(
    df: pd.DataFrame,
    profile: Dict[str, Any],
    scene_info: Dict[str, Any],
    cleaning_suggestions: List[str],
    analysis_suggestions: List[str],
    sql_templates: List[Dict[str, str]],
    kpis: Optional[List[Dict[str, Any]]] = None,
    visualizations: Optional[List[Dict[str, Any]]] = None,
    analysis_plan: Optional[Dict[str, List[str]]] = None,
    python_templates: Optional[List[Dict[str, str]]] = None,
    confirmed_scenario: Optional[str] = None,
) -> str:
    """生成接近咨询/商业分析交付物的 Markdown 报告。"""
    kpis = kpis or []
    visualizations = visualizations or []
    python_templates = python_templates or []
    automatic_primary = _scene_value(scene_info, "primary_scenario", "scene_name", "通用业务数据")
    primary = confirmed_scenario or automatic_primary
    confidence = float(scene_info.get("confidence", 0.5))
    signals = _scene_value(scene_info, "matched_signals", "matched_keywords", [])
    questions = _scene_value(scene_info, "suggested_questions", "possible_business_questions", [])
    plan = analysis_plan or {
        "questions": questions,
        "priority_directions": analysis_suggestions[:3],
        "missing_data": ["需根据业务目标补充外部或口径字段。"],
        "data_risks": cleaning_suggestions[:3],
        "deliverables": ["基础数据分析报告"],
        "visual_findings": [item.get("insight", "") for item in visualizations[:4]],
    }

    missing_fields = sum(value > 0 for value in profile["missing_count"].values())
    outlier_count = sum(item["count"] for item in profile["possible_outliers"].values())
    executive = (
        f"规则引擎自动判断为 **{automatic_primary}**，置信度为 **{confidence:.0%}**；"
        f"当前报告最终采用 **{primary}**。"
        f"数据共 {profile['shape']['rows']} 行、{profile['shape']['columns']} 列，"
        f"包含 {missing_fields} 个存在缺失的字段、{profile['duplicate_count']} 行重复记录"
        f"和 {outlier_count} 个 IQR 潜在异常值。"
    )

    lines = [
        "# DataPilot Agent 初步商业分析报告",
        "",
        "> 本报告由轻量级规则驱动 Agent Workflow 自动生成，关键口径与业务结论需人工确认。",
        "",
        "## 1. Executive Summary",
        "",
        executive,
        "",
        "建议优先开展以下工作：",
        "",
    ]
    lines.extend(f"{index}. {item}" for index, item in enumerate(plan["priority_directions"][:3], 1))

    lines.extend([
        "",
        "## 2. 数据基本信息",
        "",
        f"- 数据规模：{profile['shape']['rows']} 行 × {profile['shape']['columns']} 列",
        f"- 数值字段：{len(profile['numeric_summary'])} 个",
        f"- 类别字段：{len(profile['categorical_summary'])} 个",
        "",
        "### 数据样例",
        "",
        _sample_to_markdown(df),
        "",
        "### 字段类型概览",
        "",
        "| 字段 | 类型 | 缺失数 | 缺失率 |",
        "|---|---|---:|---:|",
    ])
    for column in profile["columns"]:
        lines.append(
            f"| {column} | {profile['dtypes'][column]} | "
            f"{profile['missing_count'][column]} | {profile['missing_rate'][column]:.2f}% |"
        )

    lines.extend([
        "",
        "## 3. 业务场景判断与置信度",
        "",
        f"- 自动判断场景：**{automatic_primary}**",
        f"- 自动判断置信度：**{confidence:.0%}**",
        f"- 人工最终采用场景：**{primary}**",
        "- 判断依据：",
    ])
    lines.extend(f"  - {signal}" for signal in signals)
    alternatives = scene_info.get("alternative_scenarios", [])
    if alternatives:
        lines.append("- 备选场景：" + "；".join(
            f"{item['scenario']}（{item['confidence']:.0%}）" for item in alternatives
        ))
    if scene_info.get("warning"):
        lines.append(f"- 人工确认提示：{scene_info['warning']}")

    lines.extend(["", "## 4. 关键指标概览", ""])
    if kpis:
        lines.extend(["| 指标 | 当前值 | 口径/提示 |", "|---|---:|---|"])
        for item in kpis:
            lines.append(f"| {item['name']} | {item['value']} | {item['note']} |")
    else:
        lines.append("当前报告未传入可计算 KPI，建议先确认指标字段和口径。")

    lines.extend([
        "",
        "## 5. 数据质量问题",
        "",
        f"- 完全重复记录：{profile['duplicate_count']} 行。",
        f"- 存在缺失值的字段：{missing_fields} 个。",
        f"- IQR 潜在异常值：{outlier_count} 个。",
    ])
    lines.extend(f"- {item}" for item in plan["data_risks"])
    lines.append("")
    lines.append("建议的清洗动作：")
    lines.extend(f"{index}. {item}" for index, item in enumerate(cleaning_suggestions, 1))

    lines.extend(["", "## 6. 主要可视化发现", ""])
    findings = plan.get("visual_findings", [])
    if findings:
        lines.extend(f"- {item}" for item in findings)
    else:
        lines.append("- 当前字段组合不足以形成稳定的可视化洞察。")

    lines.extend(["", "## 7. 初步商业洞察", ""])
    lines.extend(f"- {item}" for item in plan["questions"])

    lines.extend(["", "## 8. 后续分析建议", ""])
    lines.extend(f"{index}. {item}" for index, item in enumerate(plan["priority_directions"], 1))
    lines.append("")
    lines.append("建议补充的数据：")
    lines.extend(f"- {item}" for item in plan["missing_data"])
    lines.append("")
    lines.append("可形成的业务交付物：")
    lines.extend(f"- {item}" for item in plan["deliverables"])

    lines.extend(["", "## 9. 可执行下一步", ""])
    lines.extend([
        "1. 由业务人员确认场景、字段含义、主键和核心指标口径。",
        "2. 使用 Human-in-the-loop 清洗功能处理重复、类型和高缺失字段。",
        "3. 使用 SQL / Python 模板复核指标，补充维度拆解和异常回查。",
        "4. 将确认后的指标、图表和结论沉淀为正式分析报告或看板。",
        "",
        "### SQL 模板",
        "",
    ])
    for template in sql_templates:
        lines.extend([
            f"#### {template['title']}",
            template["description"],
            "```sql",
            template["sql"],
            "```",
            "",
        ])
    if python_templates:
        lines.extend(["### Python 模板", ""])
        for template in python_templates:
            lines.extend([
                f"#### {template['title']}",
                template["description"],
                "```python",
                template["python"],
                "```",
                "",
            ])
    return "\n".join(lines)
