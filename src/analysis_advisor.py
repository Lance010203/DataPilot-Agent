"""根据业务场景生成后续分析方向。"""

from typing import List

import pandas as pd


SCENE_SUGGESTIONS = {
    "订单/交易数据": [
        "按日或按周分析订单量、成交金额和客单价趋势。",
        "按用户累计消费金额进行分层，识别高价值用户。",
        "按商品或品类统计销量与销售额排行。",
        "对支付状态进行分组，分析支付成功率和失败原因。",
    ],
    "配送/履约数据": [
        "分析配送时长分布及 P50、P90 等分位数。",
        "分析配送距离与配送时长之间的关系。",
        "根据业务时效阈值识别超时订单。",
        "对比不同城市、区域或时间段的履约效率。",
    ],
    "营销/增长数据": [
        "对比不同渠道的 CTR、CVR 和 ROI。",
        "按广告素材或活动统计效果排行。",
        "构建曝光、点击、转化的用户漏斗。",
        "针对实验组与对照组开展 A/B 测试分析。",
    ],
    "风控/预测数据": [
        "检查目标标签分布和类别是否均衡。",
        "比较不同风险标签下关键数值字段的分布。",
        "分析字段相关性并排查潜在数据泄漏。",
        "建立可解释的分类或评分模型基线。",
    ],
    "通用业务数据": [
        "开展描述性统计，了解核心字段的分布与波动。",
        "按主要类别字段进行分组对比。",
        "对数值字段进行相关性分析。",
        "定位异常样本并回查业务原因。",
    ],
}


def generate_analysis_suggestions(scene_name: str, df: pd.DataFrame) -> List[str]:
    """返回场景化建议，并结合当前数据字段补充可执行方向。"""
    suggestions = list(
        SCENE_SUGGESTIONS.get(scene_name, SCENE_SUGGESTIONS["通用业务数据"])
    )
    columns = [str(column).lower() for column in df.columns]

    if any("city" in column or "城市" in column for column in columns):
        suggestions.append("按城市维度对比核心指标，识别区域差异。")
    if any(
        keyword in column
        for column in columns
        for keyword in ("date", "time", "日期", "时间")
    ):
        suggestions.append("将时间字段标准化后构建日、周、月趋势及环比指标。")

    return suggestions
