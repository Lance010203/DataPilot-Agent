"""根据确认后的业务场景计算关键业务指标。"""

from typing import Any, Dict, List, Optional, Sequence

import numpy as np
import pandas as pd


def _find(columns: Sequence[str], keywords: Sequence[str]) -> Optional[str]:
    for column in columns:
        if any(keyword in column.lower() for keyword in keywords):
            return column
    return None


def _metric(name: str, value: Any, note: str, available: bool = True) -> Dict[str, Any]:
    return {"name": name, "value": value, "note": note, "available": available}


def _format_number(value: float, currency: bool = False, percent: bool = False) -> str:
    if percent:
        return f"{value:.1f}%"
    if currency:
        return f"¥{value:,.2f}"
    return f"{value:,.2f}" if isinstance(value, float) else f"{value:,}"


def _numeric_sum(df: pd.DataFrame, column: Optional[str]) -> Optional[float]:
    if not column:
        return None
    values = pd.to_numeric(df[column], errors="coerce")
    return float(values.sum()) if values.notna().any() else None


def generate_kpis(df: pd.DataFrame, scenario: str) -> List[Dict[str, Any]]:
    """只计算字段存在且逻辑合理的指标，并返回缺失提示。"""
    columns = [str(column) for column in df.columns]
    result: List[Dict[str, Any]] = []

    if scenario == "订单/交易数据":
        order = _find(columns, ("order_id", "order_no", "transaction_id", "订单"))
        user = _find(columns, ("user_id", "customer_id", "用户", "客户"))
        amount = _find(columns, ("amount", "gmv", "revenue", "订单金额", "收入"))
        price = _find(columns, ("price", "单价", "价格"))
        quantity = _find(columns, ("quantity", "qty", "数量"))
        status = _find(columns, ("payment_status", "pay_status", "支付状态"))

        orders = int(df[order].nunique()) if order else len(df)
        result.append(_metric("总订单量", _format_number(orders), f"基于 `{order}` 去重" if order else "按数据行数估算"))
        gmv = _numeric_sum(df, amount)
        if gmv is None and price and quantity:
            gmv = float(
                (
                    pd.to_numeric(df[price], errors="coerce")
                    * pd.to_numeric(df[quantity], errors="coerce")
                ).sum()
            )
        result.append(
            _metric("总 GMV / 收入", _format_number(gmv, currency=True), "金额字段汇总" if gmv is not None else "当前数据缺少金额或价格×数量字段", gmv is not None)
        )
        result.append(
            _metric("平均客单价", _format_number(gmv / orders, currency=True), "GMV ÷ 订单量" if gmv is not None and orders else "当前数据缺少计算客单价所需字段", gmv is not None and orders > 0)
        )
        if status:
            normalized = df[status].astype(str).str.lower()
            success = normalized.str.contains("paid|success|支付成功|已支付", regex=True)
            result.append(_metric("支付成功率", _format_number(float(success.mean() * 100), percent=True), f"基于 `{status}`"))
        else:
            result.append(_metric("支付成功率", "-", "当前数据缺少支付状态字段", False))
        if user:
            result.append(_metric("用户数", _format_number(int(df[user].nunique())), f"基于 `{user}` 去重"))

    elif scenario == "配送/履约数据":
        duration = _find(columns, ("delivery_minutes", "duration", "delivery_time", "配送时长"))
        distance = _find(columns, ("distance", "距离"))
        timeout = _find(columns, ("timeout", "late", "超时"))
        if duration:
            values = pd.to_numeric(df[duration], errors="coerce")
            result.append(_metric("平均配送时长", f"{values.mean():.1f} 分钟", f"基于 `{duration}`"))
        else:
            result.append(_metric("平均配送时长", "-", "当前数据缺少配送时长字段", False))
        if timeout:
            values = df[timeout].astype(str).str.lower()
            rate = values.isin({"1", "true", "yes", "timeout", "late", "超时"}).mean() * 100
            result.append(_metric("超时率", _format_number(float(rate), percent=True), f"基于 `{timeout}`"))
        else:
            result.append(_metric("超时率", "-", "当前数据缺少超时标记字段", False))
        if distance:
            result.append(_metric("平均距离", f"{pd.to_numeric(df[distance], errors='coerce').mean():.2f}", f"基于 `{distance}`"))

    elif scenario == "营销/增长数据":
        impression = _find(columns, ("impression", "曝光"))
        click = _find(columns, ("click", "点击"))
        conversion = _find(columns, ("conversion", "转化"))
        cost = _find(columns, ("cost", "spend", "花费", "成本"))
        revenue = _find(columns, ("revenue", "收入"))
        sums = {key: _numeric_sum(df, col) for key, col in {
            "impression": impression, "click": click, "conversion": conversion,
            "cost": cost, "revenue": revenue,
        }.items()}
        for name, key in (("曝光量", "impression"), ("点击量", "click"), ("转化数", "conversion"), ("花费", "cost")):
            value = sums[key]
            result.append(_metric(name, _format_number(value or 0, currency=name == "花费") if value is not None else "-", f"基于 `{locals().get(key)}`" if value is not None else f"当前数据缺少{name}字段", value is not None))
        ctr = sums["click"] / sums["impression"] * 100 if sums["click"] is not None and sums["impression"] else None
        cvr = sums["conversion"] / sums["click"] * 100 if sums["conversion"] is not None and sums["click"] else None
        roi = sums["revenue"] / sums["cost"] if sums["revenue"] is not None and sums["cost"] else None
        result.extend([
            _metric("CTR", _format_number(ctr, percent=True) if ctr is not None else "-", "点击量 ÷ 曝光量" if ctr is not None else "当前数据缺少曝光或点击字段", ctr is not None),
            _metric("CVR", _format_number(cvr, percent=True) if cvr is not None else "-", "转化数 ÷ 点击量" if cvr is not None else "当前数据缺少点击或转化字段", cvr is not None),
            _metric("ROI", f"{roi:.2f}" if roi is not None else "-", "收入 ÷ 花费" if roi is not None else "当前数据缺少收入或花费字段", roi is not None),
        ])

    elif scenario == "财务/经营分析数据":
        revenue = _find(columns, ("revenue", "income", "sales", "收入", "营收"))
        cost = _find(columns, ("cost", "expense", "成本", "费用"))
        budget = _find(columns, ("budget", "预算"))
        actual = _find(columns, ("actual", "实际"))
        revenue_value, cost_value = _numeric_sum(df, revenue), _numeric_sum(df, cost)
        result.append(_metric("总收入", _format_number(revenue_value, currency=True) if revenue_value is not None else "-", f"基于 `{revenue}`" if revenue else "当前数据缺少收入字段", revenue_value is not None))
        result.append(_metric("总成本", _format_number(cost_value, currency=True) if cost_value is not None else "-", f"基于 `{cost}`" if cost else "当前数据缺少成本字段", cost_value is not None))
        gross = revenue_value - cost_value if revenue_value is not None and cost_value is not None else None
        result.append(_metric("毛利", _format_number(gross, currency=True) if gross is not None else "-", "收入 - 成本" if gross is not None else "当前数据缺少收入或成本字段", gross is not None))
        margin = gross / revenue_value * 100 if gross is not None and revenue_value else None
        result.append(_metric("毛利率", _format_number(margin, percent=True) if margin is not None else "-", "毛利 ÷ 收入" if margin is not None else "当前数据缺少计算毛利率所需字段", margin is not None))
        budget_value, actual_value = _numeric_sum(df, budget), _numeric_sum(df, actual)
        completion = actual_value / budget_value * 100 if actual_value is not None and budget_value else None
        result.append(_metric("预算完成率", _format_number(completion, percent=True) if completion is not None else "-", "实际 ÷ 预算" if completion is not None else "当前数据缺少预算或实际字段", completion is not None))

    elif scenario == "宏观经济/金融市场数据":
        time_col = _find(columns, ("date", "month", "quarter", "year", "日期", "时间"))
        numeric = list(df.select_dtypes(include=np.number).columns)
        if time_col:
            dates = pd.to_datetime(df[time_col], errors="coerce").dropna()
            result.append(_metric("时间范围", f"{dates.min().date()} 至 {dates.max().date()}" if not dates.empty else "-", f"基于 `{time_col}`", not dates.empty))
        for column in numeric[:3]:
            values = pd.to_numeric(df[column], errors="coerce").dropna()
            if not values.empty:
                result.append(_metric(f"{column} 最新值", _format_number(float(values.iloc[-1])), f"历史均值 {_format_number(float(values.mean()))}"))

    elif scenario == "用户行为/产品分析数据":
        user = _find(columns, ("user_id", "用户"))
        event = _find(columns, ("event", "事件"))
        duration = _find(columns, ("session_duration", "duration", "会话时长"))
        result.append(_metric("活跃用户数", _format_number(int(df[user].nunique())) if user else "-", f"基于 `{user}` 去重" if user else "当前数据缺少用户字段", user is not None))
        result.append(_metric("事件量", _format_number(len(df)), "按行为记录数统计"))
        if duration:
            avg = pd.to_numeric(df[duration], errors="coerce").mean()
            result.append(_metric("平均会话时长", _format_number(float(avg)), f"基于 `{duration}`"))
        if event:
            result.append(_metric("事件类型数", _format_number(int(df[event].nunique())), f"基于 `{event}`"))

    else:
        result.extend([
            _metric("记录数", _format_number(len(df)), "数据总行数"),
            _metric("字段数", _format_number(len(df.columns)), "数据总列数"),
            _metric("缺失单元格", _format_number(int(df.isna().sum().sum())), "全部字段缺失值合计"),
        ])
    return result
