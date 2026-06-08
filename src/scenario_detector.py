"""多信号业务场景规则引擎。"""

import re
from typing import Any, Dict, List, Sequence, Set, Tuple

import pandas as pd


SCENARIO_ORDER = [
    "订单/交易数据",
    "配送/履约数据",
    "营销/增长数据",
    "风控/信用/预测数据",
    "财务/经营分析数据",
    "宏观经济/金融市场数据",
    "用户行为/产品分析数据",
    "通用业务数据",
]

SCENARIO_RULES: Dict[str, Dict[str, Any]] = {
    "订单/交易数据": {
        "groups": {
            "订单标识": ("order_id", "order_no", "transaction_id", "订单", "交易"),
            "用户": ("user_id", "customer_id", "member_id", "用户", "客户"),
            "商品": ("product_id", "sku", "product", "category", "商品", "品类"),
            "金额数量": ("amount", "price", "quantity", "revenue", "gmv", "金额", "价格", "数量"),
            "时间状态": ("pay_time", "create_time", "order_time", "payment_status", "order_status", "支付", "状态"),
        },
        "min_groups": 3,
        "questions": [
            "GMV、订单量和客单价由哪些因素驱动？",
            "哪些城市、品类、商品或用户贡献最高？",
            "支付成功率和订单状态是否存在明显损失环节？",
        ],
    },
    "配送/履约数据": {
        "groups": {
            "履约标识": ("delivery_id", "waybill_id", "delivery", "waybill", "配送", "运单"),
            "骑手商户": ("rider_id", "courier_id", "merchant_id", "shop_id", "骑手", "商户"),
            "距离位置": ("distance", "longitude", "latitude", "lng", "lat", "距离", "经度", "纬度"),
            "履约时间": ("delivery_time", "pickup_time", "grab_time", "fetch_time", "arrive_time", "duration", "配送时长"),
            "超时状态": ("timeout", "late", "overdue", "超时", "迟到"),
        },
        "min_groups": 2,
        "questions": [
            "配送时长和超时率是否达到业务目标？",
            "距离、时段、骑手或商户是否影响履约效率？",
            "哪些订单具备较高超时风险？",
        ],
    },
    "营销/增长数据": {
        "groups": {
            "活动渠道": ("campaign", "channel", "ad_id", "creative_id", "活动", "渠道", "素材"),
            "曝光点击": ("impression", "click", "ctr", "曝光", "点击"),
            "转化": ("conversion", "cvr", "转化"),
            "成本": ("cost", "spend", "cac", "花费", "成本"),
            "收入回报": ("revenue", "roi", "收入", "回报"),
        },
        "min_groups": 2,
        "questions": [
            "不同渠道的 CTR、CVR 和 ROI 表现如何？",
            "曝光到点击、再到转化的主要流失发生在哪里？",
            "哪些活动或素材具备更高投入产出效率？",
        ],
    },
    "风控/信用/预测数据": {
        "groups": {
            "目标标签": ("label", "target", "default", "bad", "good", "y", "标签", "违约"),
            "风险信用": ("risk", "credit", "loan", "overdue", "风险", "信用", "贷款", "逾期"),
            "评分概率": ("risk_score", "credit_score", "probability", "prediction", "评分", "概率", "预测"),
            "特征": ("feature", "特征"),
        },
        "min_groups": 2,
        "questions": [
            "目标标签是否存在样本不平衡？",
            "哪些特征与违约或风险标签关系最强？",
            "高风险样本应使用什么阈值和评估指标识别？",
        ],
    },
    "财务/经营分析数据": {
        "groups": {
            "收入": ("revenue", "income", "sales", "收入", "营收"),
            "成本费用": ("cost", "expense", "成本", "费用"),
            "利润": ("profit", "gross_profit", "net_profit", "margin", "利润", "毛利"),
            "预算实际": ("budget", "actual", "预算", "实际"),
            "经营维度": ("month", "quarter", "department", "business_unit", "月份", "季度", "部门"),
            "资产现金": ("asset", "liability", "cash_flow", "资产", "负债", "现金流"),
        },
        "min_groups": 2,
        "questions": [
            "收入、成本和利润的趋势与结构如何？",
            "预算完成率及偏差主要来自哪些部门或业务线？",
            "毛利率和现金流是否出现阶段性压力？",
        ],
    },
    "宏观经济/金融市场数据": {
        "groups": {
            "宏观指标": ("gdp", "cpi", "ppi", "unemployment", "inflation", "失业", "通胀"),
            "利率汇率": ("interest_rate", "exchange_rate", "bond_yield", "利率", "汇率", "收益率"),
            "市场行情": ("stock_index", "close", "open", "high", "low", "volume", "指数", "收盘", "开盘"),
            "时间": ("date", "month", "quarter", "year", "日期", "月份", "季度", "年份"),
            "地区": ("region", "country", "province", "地区", "国家", "省份"),
        },
        "min_groups": 2,
        "questions": [
            "CPI、GDP、利率或市场指数是否存在阶段性趋势变化？",
            "不同宏观指标之间是否存在同步或领先滞后关系？",
            "最新一期水平相较历史均值处于什么位置？",
        ],
    },
    "用户行为/产品分析数据": {
        "groups": {
            "用户会话": ("user_id", "session_id", "用户", "会话"),
            "事件页面": ("event", "page", "view", "click", "事件", "页面", "浏览"),
            "活跃留存": ("retention", "churn", "active", "留存", "流失", "活跃"),
            "行为时间": ("login_time", "event_time", "duration", "登录时间", "行为时间", "时长"),
            "设备版本": ("device", "app_version", "os", "设备", "版本"),
        },
        "min_groups": 2,
        "questions": [
            "用户活跃、事件量和会话时长如何变化？",
            "哪些页面或事件是高频行为与关键路径？",
            "留存、流失是否与设备、版本或行为特征相关？",
        ],
    },
}


def _matched_columns(columns: Sequence[str], keywords: Sequence[str]) -> List[str]:
    def normalize(value: str) -> str:
        return re.sub(r"[^a-z0-9\u4e00-\u9fff]", "", value.lower())

    return sorted(
        {
            column
            for column in columns
            if any(
                normalize(column) == normalize(keyword)
                if len(normalize(keyword)) <= 2
                else normalize(keyword) in normalize(column)
                for keyword in keywords
            )
        }
    )


def _value_signals(df: pd.DataFrame) -> Set[str]:
    signals: Set[str] = set()
    for column in df.select_dtypes(include=["object", "category", "bool"]).columns:
        values = set(df[column].dropna().astype(str).str.lower().head(200))
        if values & {"paid", "pending", "failed", "cancelled", "success"}:
            signals.add("支付/订单状态值")
        if values & {"click", "view", "login", "purchase", "page_view"}:
            signals.add("用户行为事件值")
        if values & {"default", "bad", "good", "overdue", "fraud"}:
            signals.add("风险标签值")
    return signals


def _score_scenario(
    df: pd.DataFrame,
    name: str,
    rule: Dict[str, Any],
) -> Tuple[float, List[str]]:
    columns = [str(column) for column in df.columns]
    group_hits: List[Tuple[str, List[str]]] = []
    for group_name, keywords in rule["groups"].items():
        matched = _matched_columns(columns, keywords)
        if matched:
            group_hits.append((group_name, matched))

    group_count = len(group_hits)
    coverage = group_count / len(rule["groups"])
    minimum_met = group_count >= rule["min_groups"]
    score = coverage * 0.72
    if minimum_met:
        score += 0.18
    if group_count >= rule["min_groups"] + 1:
        score += 0.05

    numeric_count = len(df.select_dtypes(include="number").columns)
    datetime_like = any(
        pd.api.types.is_datetime64_any_dtype(df[column])
        or any(token in str(column).lower() for token in ("date", "time", "month", "year", "日期", "时间"))
        for column in df.columns
    )
    if numeric_count >= 2:
        score += 0.02
    if datetime_like and name in {
        "订单/交易数据",
        "配送/履约数据",
        "财务/经营分析数据",
        "宏观经济/金融市场数据",
        "用户行为/产品分析数据",
    }:
        score += 0.03

    value_signals = _value_signals(df)
    if name == "订单/交易数据" and "支付/订单状态值" in value_signals:
        score += 0.05
    if name == "用户行为/产品分析数据" and "用户行为事件值" in value_signals:
        score += 0.05
    if name == "风控/信用/预测数据" and "风险标签值" in value_signals:
        score += 0.05

    if not minimum_met:
        score = min(score, 0.54)

    signals = [
        f"{group_name}：{', '.join(columns)}"
        for group_name, columns in group_hits
    ]
    return round(min(score, 0.98), 2), signals


def detect_business_scenario(df: pd.DataFrame) -> Dict[str, Any]:
    """综合字段组合、类型和值特征判断业务场景。"""
    scored = []
    for scenario, rule in SCENARIO_RULES.items():
        score, signals = _score_scenario(df, scenario, rule)
        scored.append({"scenario": scenario, "score": score, "signals": signals})
    scored.sort(key=lambda item: item["score"], reverse=True)

    best = scored[0]
    if best["score"] < 0.55:
        primary = "通用业务数据"
        confidence = round(max(0.35, best["score"]), 2)
        signals = best["signals"] or ["未形成足够的字段组合信号"]
        questions = [
            "数据的核心指标、时间范围和主要维度是什么？",
            "哪些分组之间存在显著差异？",
            "缺失、重复和异常样本是否影响分析结论？",
        ]
    else:
        primary = best["scenario"]
        confidence = best["score"]
        signals = best["signals"]
        questions = SCENARIO_RULES[primary]["questions"]

    alternatives = [
        {"scenario": item["scenario"], "confidence": item["score"]}
        for item in scored
        if item["scenario"] != primary and item["score"] >= 0.25
    ][:3]
    warning = (
        "当前场景判断置信度不高，建议人工确认后再生成分析建议。"
        if confidence < 0.65
        else ""
    )
    return {
        "primary_scenario": primary,
        "confidence": confidence,
        "matched_signals": signals,
        "alternative_scenarios": alternatives,
        "warning": warning,
        "suggested_questions": questions,
    }
