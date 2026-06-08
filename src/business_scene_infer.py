"""兼容旧接口的业务场景推断模块。"""

import pandas as pd

from src.scenario_detector import detect_business_scenario


def infer_business_scene(df: pd.DataFrame) -> dict:
    """返回旧页面和旧测试可继续使用的字段结构。"""
    result = detect_business_scenario(df)
    return {
        "scene_name": result["primary_scenario"],
        "reason": "；".join(result["matched_signals"]),
        "matched_keywords": result["matched_signals"],
        "possible_business_questions": result["suggested_questions"],
        **result,
    }
