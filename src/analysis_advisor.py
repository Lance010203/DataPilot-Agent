"""根据确认场景、数据质量、KPI 和图表生成专业分析建议。"""

from typing import Any, Dict, List, Sequence

import pandas as pd


SCENARIO_PLANS: Dict[str, Dict[str, List[str]]] = {
    "订单/交易数据": {
        "questions": [
            "GMV 的变化来自订单量还是客单价？",
            "城市、品类、渠道和用户群体的贡献结构如何？",
            "支付失败、取消和复购不足发生在哪些环节？",
        ],
        "priorities": [
            "先拆解 GMV = 订单量 × 客单价，建立规模与效率指标基线。",
            "再按城市、品类、商品和渠道分析贡献、增长与集中度。",
            "最后定位支付转化和用户复购问题，并形成可执行分群。",
        ],
        "deliverables": ["经营指标看板", "品类/城市贡献分析", "用户分层与转化诊断"],
    },
    "配送/履约数据": {
        "questions": [
            "平均配送时长和超时率是否达到履约目标？",
            "距离、时段、城市、商户或骑手如何影响时效？",
            "哪些订单具备可提前识别的超时风险？",
        ],
        "priorities": [
            "先建立平均时长、P50/P90 和超时率基线。",
            "再按距离、时段、城市、商户和骑手拆解履约差异。",
            "最后组合距离、时长和状态字段构建高风险订单规则。",
        ],
        "deliverables": ["履约效率看板", "超时归因分析", "高风险订单识别清单"],
    },
    "营销/增长数据": {
        "questions": [
            "哪些渠道、活动或素材带来更高 CTR、CVR 和 ROI？",
            "曝光到点击、再到转化的主要损失发生在哪里？",
            "增加投放成本是否带来成比例的增量转化？",
        ],
        "priorities": [
            "先统一曝光、点击、转化、成本和收入的指标口径。",
            "再按渠道、活动和素材比较漏斗效率与 ROI。",
            "最后识别低效花费和可追加预算的高潜组合。",
        ],
        "deliverables": ["渠道效果看板", "转化漏斗诊断", "投放预算优化建议"],
    },
    "风控/信用/预测数据": {
        "questions": [
            "目标标签是否不平衡或存在定义风险？",
            "哪些特征与违约、逾期或风险评分相关？",
            "模型应使用哪些指标和阈值进行业务评估？",
        ],
        "priorities": [
            "先确认标签定义、观察窗口和样本分布。",
            "再比较关键特征在不同标签下的分布与相关性。",
            "最后建立可解释基线，并使用 Recall、AUC、KS 等指标评估。",
        ],
        "deliverables": ["样本质量报告", "特征探索报告", "模型基线与阈值建议"],
    },
    "财务/经营分析数据": {
        "questions": [
            "收入、成本、利润和毛利率如何变化？",
            "预算偏差来自哪些部门、业务线或时间周期？",
            "经营增长是否以利润和现金流为代价？",
        ],
        "priorities": [
            "先建立收入、成本、利润、毛利率和预算完成率基线。",
            "再按月份、季度、部门和业务线拆解贡献与偏差。",
            "最后定位利润压力和预算异常，形成经营改进清单。",
        ],
        "deliverables": ["经营分析月报", "预算偏差分析", "部门贡献与利润诊断"],
    },
    "宏观经济/金融市场数据": {
        "questions": [
            "CPI、GDP、利率或指数的趋势和拐点是什么？",
            "不同指标之间是否存在同步、背离或领先滞后？",
            "最新一期水平相较历史均值处于什么区间？",
        ],
        "priorities": [
            "先统一时间频率并分析核心指标趋势、环比和波动区间。",
            "再观察不同宏观指标或市场指标之间的相关性与阶段性背离。",
            "最后结合政策事件、地区和市场指数解释关键拐点。",
        ],
        "deliverables": ["宏观指标监测简报", "多指标趋势对比", "阶段性波动与事件清单"],
    },
    "用户行为/产品分析数据": {
        "questions": [
            "活跃用户、事件量和会话时长如何变化？",
            "哪些事件、页面或功能构成核心使用路径？",
            "留存和流失是否与设备、版本或行为模式相关？",
        ],
        "priorities": [
            "先建立活跃用户、事件量和会话时长基线。",
            "再识别高频事件、关键路径和主要流失节点。",
            "最后按设备、版本和用户群体拆解留存差异。",
        ],
        "deliverables": ["产品活跃看板", "用户路径分析", "留存与流失诊断"],
    },
    "通用业务数据": {
        "questions": ["核心指标和主要维度是什么？", "哪些分组存在明显差异？", "趋势和异常样本是否值得进一步回查？"],
        "priorities": ["先完成描述性统计和字段口径确认。", "再进行分组、趋势和相关性分析。", "最后回查缺失、重复和异常样本。"],
        "deliverables": ["数据质量简报", "基础探索分析", "后续数据需求清单"],
    },
}


def generate_analysis_plan(
    scenario: str,
    df: pd.DataFrame,
    profile: Dict[str, Any],
    kpis: List[Dict[str, Any]],
    visualizations: List[Dict[str, Any]],
) -> Dict[str, List[str]]:
    """生成接近商业分析交付物结构的建议。"""
    base = SCENARIO_PLANS.get(scenario, SCENARIO_PLANS["通用业务数据"])
    columns = {str(column).lower() for column in df.columns}
    missing_fields: List[str] = []

    expected = {
        "订单/交易数据": [("用户字段", ("user_id", "customer_id")), ("渠道字段", ("channel",)), ("订单金额字段", ("amount", "gmv", "revenue"))],
        "配送/履约数据": [("距离字段", ("distance",)), ("超时标记", ("timeout", "late")), ("骑手或商户字段", ("rider_id", "merchant_id"))],
        "营销/增长数据": [("曝光字段", ("impression",)), ("转化字段", ("conversion",)), ("成本和收入字段", ("cost", "spend", "revenue"))],
        "财务/经营分析数据": [("预算与实际字段", ("budget", "actual")), ("部门或业务线字段", ("department", "business_unit"))],
        "宏观经济/金融市场数据": [("政策事件字段", ("event", "policy")), ("地区字段", ("region", "country"))],
        "用户行为/产品分析数据": [("会话字段", ("session_id",)), ("留存或流失字段", ("retention", "churn"))],
    }.get(scenario, [])
    for label, candidates in expected:
        if not any(any(candidate in column for candidate in candidates) for column in columns):
            missing_fields.append(f"建议补充{label}，以支持更完整的归因分析。")

    risks: List[str] = []
    missing_columns = [column for column, rate in profile["missing_rate"].items() if rate > 0]
    if missing_columns:
        risks.append("存在缺失字段：" + "、".join(f"`{column}`" for column in missing_columns[:6]) + "，可能影响指标口径。")
    if profile["duplicate_count"]:
        risks.append(f"存在 {profile['duplicate_count']} 行完全重复记录，汇总前需确认是否去重。")
    outliers = [column for column, item in profile["possible_outliers"].items() if item["count"] > 0]
    if outliers:
        risks.append("以下字段存在统计异常值：" + "、".join(f"`{column}`" for column in outliers[:6]) + "，需要业务复核。")
    unavailable = [item["name"] for item in kpis if not item["available"]]
    if unavailable:
        risks.append("部分关键指标暂不可计算：" + "、".join(unavailable) + "。")

    findings = [spec["insight"] for spec in visualizations[:4]]
    return {
        "questions": list(base["questions"]),
        "priority_directions": list(base["priorities"])[:3],
        "missing_data": missing_fields or ["当前字段已覆盖基础分析，后续可根据业务目标补充外部数据。"],
        "data_risks": risks or ["暂未发现阻断分析的明显数据风险，仍需确认业务口径。"],
        "deliverables": list(base["deliverables"]),
        "visual_findings": findings or ["当前字段组合不足以生成高价值图表，建议补充时间、数值或业务维度字段。"],
    }


def generate_analysis_suggestions(scene_name: str, df: pd.DataFrame) -> List[str]:
    """兼容 v0.2 的扁平建议接口。"""
    return list(SCENARIO_PLANS.get(scene_name, SCENARIO_PLANS["通用业务数据"])["priorities"])
