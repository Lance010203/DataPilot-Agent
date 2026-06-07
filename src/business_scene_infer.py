"""根据字段关键词推断数据对应的业务场景。"""

from typing import Any, Dict, List, Set

import pandas as pd


SCENE_RULES = {
    "订单/交易数据": {
        "keywords": {
            "order", "订单", "user", "用户", "customer", "客户", "amount",
            "金额", "price", "价格", "payment", "支付", "product", "商品",
        },
        "questions": [
            "用户消费金额分布如何？",
            "哪些商品或客户贡献更高？",
            "订单转化或支付情况如何？",
        ],
    },
    "配送/履约数据": {
        "keywords": {
            "delivery", "配送", "rider", "骑手", "distance", "距离",
            "duration", "时长", "fulfillment", "履约", "timeout", "超时",
        },
        "questions": [
            "配送时长是否存在异常？",
            "哪些区域或时间段效率较低？",
            "是否存在超时风险？",
        ],
    },
    "营销/增长数据": {
        "keywords": {
            "click", "点击", "view", "曝光", "conversion", "转化", "ctr",
            "cvr", "roi", "channel", "渠道", "campaign", "广告",
        },
        "questions": [
            "CTR、CVR、ROI 表现如何？",
            "哪些渠道或素材效果更好？",
            "用户转化路径是否存在流失？",
        ],
    },
    "风控/预测数据": {
        "keywords": {
            "score", "评分", "label", "标签", "default", "违约", "risk",
            "风险", "fraud", "欺诈", "target", "预测",
        },
        "questions": [
            "不同标签样本分布是否均衡？",
            "哪些字段可能与风险相关？",
            "是否适合构建分类或评分模型？",
        ],
    },
}


def _matched_keywords(columns: List[str], keywords: Set[str]) -> List[str]:
    normalized_columns = [column.lower() for column in columns]
    return sorted(
        keyword
        for keyword in keywords
        if any(keyword.lower() in column for column in normalized_columns)
    )


def infer_business_scene(df: pd.DataFrame) -> Dict[str, Any]:
    """根据字段名关键词得分推断最可能的业务场景。"""
    columns = [str(column) for column in df.columns]
    matches = {
        scene_name: _matched_keywords(columns, rule["keywords"])
        for scene_name, rule in SCENE_RULES.items()
    }
    scene_name = max(matches, key=lambda scene: len(matches[scene]))
    matched = matches[scene_name]

    if not matched:
        return {
            "scene_name": "通用业务数据",
            "reason": "未匹配到明确的业务关键词，因此按通用业务数据处理。",
            "matched_keywords": [],
            "possible_business_questions": [
                "数据的核心指标和分布特征是什么？",
                "不同类别或时间段之间是否存在明显差异？",
                "哪些字段之间可能存在相关关系？",
            ],
        }

    return {
        "scene_name": scene_name,
        "reason": f"字段名中匹配到关键词：{', '.join(matched)}。",
        "matched_keywords": matched,
        "possible_business_questions": SCENE_RULES[scene_name]["questions"],
    }
