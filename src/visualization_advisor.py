"""专业可视化选择、数据准备与咨询风格渲染。"""

import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

_mpl_cache = Path(tempfile.gettempdir()) / "datapilot-matplotlib"
_mpl_cache.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(_mpl_cache))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np
import pandas as pd


TIME_KEYWORDS = ("date", "time", "datetime", "month", "quarter", "year", "日期", "时间")
PRIMARY = "#17365D"
SECONDARY = "#5B7C99"
ACCENT = "#A9BCD0"
GRID = "#D9E1E8"


def _configure_font() -> None:
    available = {font.name for font in font_manager.fontManager.ttflist}
    for candidate in ("PingFang SC", "Arial Unicode MS", "Microsoft YaHei", "SimHei"):
        if candidate in available:
            plt.rcParams["font.sans-serif"] = [candidate, "DejaVu Sans"]
            break
    plt.rcParams["axes.unicode_minus"] = False


_configure_font()


def _find(columns: Sequence[str], keywords: Sequence[str]) -> Optional[str]:
    for column in columns:
        if any(keyword in column.lower() for keyword in keywords):
            return column
    return None


def find_datetime_column(df: pd.DataFrame) -> Optional[str]:
    """识别可可靠转换的时间字段。"""
    for column in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[column]):
            return str(column)
    for column in df.columns:
        name = str(column)
        if any(keyword in name.lower() for keyword in TIME_KEYWORDS):
            converted = pd.to_datetime(df[column], errors="coerce")
            if converted.notna().mean() >= 0.6:
                return name
    return None


def apply_mckinsey_style(ax: Any, title: str) -> None:
    """统一白底、深蓝、弱网格的克制图表风格。"""
    ax.set_title(title, loc="left", fontsize=14, fontweight="bold", color="#111111", pad=12)
    ax.set_facecolor("white")
    ax.grid(axis="y", color=GRID, linewidth=0.8, alpha=0.7)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors="#4A4A4A", labelsize=9)
    ax.set_xlabel(ax.get_xlabel(), color="#4A4A4A")
    ax.set_ylabel(ax.get_ylabel(), color="#4A4A4A")


def _chart(
    chart_type: str,
    title: str,
    insight: str,
    data: pd.DataFrame,
    x: Optional[str] = None,
    y: Optional[str] = None,
    columns: Optional[List[str]] = None,
) -> Dict[str, Any]:
    return {
        "type": chart_type,
        "title": title,
        "insight": insight,
        "data": data,
        "x": x,
        "y": y,
        "columns": columns or [],
    }


def _time_trend(
    df: pd.DataFrame,
    time_col: str,
    value_columns: List[str],
    title: str,
    insight: str,
) -> Optional[Dict[str, Any]]:
    frame = df[[time_col, *value_columns]].copy()
    frame[time_col] = pd.to_datetime(frame[time_col], errors="coerce")
    frame = frame.dropna(subset=[time_col])
    if frame.empty:
        return None
    for column in value_columns:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    trend = frame.set_index(time_col)[value_columns].resample("D").sum(min_count=1)
    trend = trend.dropna(how="all")
    if trend.empty:
        return None
    return _chart("line", title, insight, trend, columns=value_columns)


def _record_trend(df: pd.DataFrame, time_col: str) -> Optional[Dict[str, Any]]:
    dates = pd.to_datetime(df[time_col], errors="coerce").dropna()
    if dates.empty:
        return None
    trend = dates.dt.floor("D").value_counts().sort_index().rename("Record Count").to_frame()
    return _chart(
        "line",
        "Record Volume Trend",
        "该图用于判断业务量是否存在明显增长、下滑或周期性波动。",
        trend,
        columns=["Record Count"],
    )


def _top_contribution(
    df: pd.DataFrame,
    category: str,
    value: Optional[str],
    insight: str,
) -> Optional[Dict[str, Any]]:
    if value:
        frame = df[[category, value]].copy()
        frame[value] = pd.to_numeric(frame[value], errors="coerce")
        result = frame.groupby(category, dropna=False)[value].sum().nlargest(10).sort_values()
        label = f"Sum of {value}"
    else:
        result = df[category].fillna("Missing").astype(str).value_counts().head(10).sort_values()
        label = "Record Count"
    if result.empty:
        return None
    data = result.rename(label).to_frame()
    return _chart("barh", f"Top 10 by {category}", insight, data, columns=[label])


def _distribution(df: pd.DataFrame, column: str, insight: str) -> Optional[Dict[str, Any]]:
    values = pd.to_numeric(df[column], errors="coerce").dropna()
    if values.nunique() < 2:
        return None
    return _chart(
        "hist",
        f"Distribution of {column}",
        insight,
        values.rename(column).to_frame(),
        x=column,
    )


def _scatter(df: pd.DataFrame, x: str, y: str, insight: str) -> Optional[Dict[str, Any]]:
    frame = df[[x, y]].apply(pd.to_numeric, errors="coerce").dropna()
    if len(frame) < 3 or frame[x].nunique() < 2 or frame[y].nunique() < 2:
        return None
    return _chart("scatter", f"{y} vs {x}", insight, frame, x=x, y=y)


def _correlation(df: pd.DataFrame) -> Optional[Dict[str, Any]]:
    numeric = df.select_dtypes(include=np.number)
    if numeric.shape[1] < 3 or numeric.shape[1] > 8:
        return None
    corr = numeric.corr()
    return _chart(
        "heatmap",
        "Numeric Correlation Overview",
        "该图用于识别指标之间的同步变化关系，为后续归因分析和特征筛选提供线索。",
        corr,
        columns=list(corr.columns),
    )


def _missing_chart(df: pd.DataFrame) -> Optional[Dict[str, Any]]:
    missing = df.isna().sum()
    missing = missing[missing > 0].sort_values()
    if missing.empty:
        return None
    return _chart(
        "barh",
        "Missing Values by Field",
        "该图用于定位数据质量治理优先级，缺失较多的字段需要先确认业务口径和可用性。",
        missing.rename("Missing Count").to_frame(),
        columns=["Missing Count"],
    )


def build_professional_visualizations(
    df: pd.DataFrame,
    scenario: str,
    max_charts: int = 6,
) -> List[Dict[str, Any]]:
    """根据确认场景生成 4–6 张最有业务价值的图表规格。"""
    columns = [str(column) for column in df.columns]
    time_col = find_datetime_column(df)
    amount = _find(columns, ("amount", "revenue", "gmv", "price", "收入", "金额", "价格"))
    quantity = _find(columns, ("quantity", "qty", "数量"))
    category = _find(columns, ("category", "product", "city", "channel", "department", "品类", "城市", "渠道", "部门"))
    status = _find(columns, ("payment_status", "order_status", "status", "状态"))
    duration = _find(columns, ("delivery_minutes", "duration", "配送时长", "会话时长"))
    distance = _find(columns, ("distance", "距离"))
    charts: List[Dict[str, Any]] = []

    if scenario == "订单/交易数据":
        analysis_df = df
        chart_amount = amount
        if amount and quantity and "price" in amount.lower():
            analysis_df = df.copy()
            analysis_df["Calculated_GMV"] = (
                pd.to_numeric(analysis_df[amount], errors="coerce")
                * pd.to_numeric(analysis_df[quantity], errors="coerce")
            )
            chart_amount = "Calculated_GMV"

        if time_col and chart_amount:
            chart = _time_trend(
                analysis_df, time_col, [chart_amount], "Revenue / GMV Trend",
                "该图用于判断交易规模是否存在明显增长、下滑或异常波动。",
            )
            if chart:
                charts.append(chart)
        elif time_col:
            chart = _record_trend(df, time_col)
            if chart:
                charts.append(chart)
        if category:
            chart = _top_contribution(
                analysis_df, category, chart_amount,
                "该图用于识别贡献最高的品类、城市或渠道，可辅助资源配置与重点经营。",
            )
            if chart:
                charts.append(chart)
        if amount:
            chart = _distribution(
                df, amount,
                "该图用于观察订单金额或客单价的集中区间，并识别极端高价值订单。",
            )
            if chart:
                charts.append(chart)
        if status:
            chart = _top_contribution(
                df, status, None,
                "该图用于检查支付或订单状态结构，定位失败、取消或待处理占比。",
            )
            if chart:
                charts.append(chart)
        if quantity and amount:
            chart = _scatter(
                df, quantity, amount,
                "该图用于观察购买数量与金额是否同步变化，并识别高数量或高金额异常订单。",
            )
            if chart:
                charts.append(chart)

    elif scenario == "配送/履约数据":
        if duration:
            chart = _distribution(df, duration, "该图用于判断配送时长的主要区间和长尾超时风险。")
            if chart:
                charts.append(chart)
        if distance and duration:
            chart = _scatter(
                df, distance, duration,
                "该图用于观察配送距离与配送时长是否同步上升，辅助识别异常履约订单。",
            )
            if chart:
                charts.append(chart)
        if time_col:
            chart = _record_trend(df, time_col)
            if chart:
                charts.append(chart)
        if category:
            chart = _top_contribution(
                df, category, duration,
                "该图用于比较不同城市、商户或骑手维度的履约表现。",
            )
            if chart:
                charts.append(chart)

    elif scenario == "营销/增长数据":
        channel = _find(columns, ("channel", "campaign", "creative", "渠道", "活动", "素材"))
        roi = _find(columns, ("roi",))
        ctr = _find(columns, ("ctr",))
        cvr = _find(columns, ("cvr",))
        cost = _find(columns, ("cost", "spend", "花费"))
        conversion = _find(columns, ("conversion", "转化"))
        for value, insight in (
            (roi, "该图用于识别投入产出效率最高的渠道或活动。"),
            (ctr or cvr, "该图用于比较渠道点击或转化效率，定位表现差异。"),
        ):
            if channel and value:
                chart = _top_contribution(df, channel, value, insight)
                if chart:
                    charts.append(chart)
        if cost and conversion:
            chart = _scatter(
                df, cost, conversion,
                "该图用于判断增加花费是否带来同步转化增长，并识别低效投放。",
            )
            if chart:
                charts.append(chart)
        if time_col:
            chart = _record_trend(df, time_col)
            if chart:
                charts.append(chart)

    elif scenario == "财务/经营分析数据":
        finance_cols = [
            column for column in columns
            if any(key in column.lower() for key in ("revenue", "cost", "profit", "income", "收入", "成本", "利润"))
            and pd.api.types.is_numeric_dtype(df[column])
        ][:3]
        if time_col and finance_cols:
            chart = _time_trend(
                df, time_col, finance_cols, "Revenue / Cost / Profit Trend",
                "该图用于判断收入、成本和利润的变化是否同步，并定位经营拐点。",
            )
            if chart:
                charts.append(chart)
        if category and amount:
            chart = _top_contribution(df, category, amount, "该图用于识别部门或业务线的收入贡献结构。")
            if chart:
                charts.append(chart)

    elif scenario == "宏观经济/金融市场数据":
        macro_cols = [
            column for column in df.select_dtypes(include=np.number).columns
            if any(key in str(column).lower() for key in (
                "gdp", "cpi", "ppi", "rate", "yield", "index", "close", "inflation", "unemployment"
            ))
        ][:4]
        if time_col and macro_cols:
            chart = _time_trend(
                df, time_col, [str(col) for col in macro_cols], "Macro / Market Indicator Trend",
                "该图用于识别宏观指标或市场指数是否存在明显趋势、拐点和阶段性波动。",
            )
            if chart:
                charts.append(chart)
        for column in macro_cols[:2]:
            chart = _distribution(
                df, str(column),
                "该图用于比较指标当前波动区间与历史常态，识别极端时期。",
            )
            if chart:
                charts.append(chart)

    elif scenario == "用户行为/产品分析数据":
        event = _find(columns, ("event", "page", "事件", "页面"))
        device = _find(columns, ("device", "app_version", "设备", "版本"))
        if time_col:
            chart = _record_trend(df, time_col)
            if chart:
                chart["insight"] = "该图用于判断用户活跃或事件量是否存在增长、衰退和周期性变化。"
                charts.append(chart)
        for column, insight in (
            (event, "该图用于识别高频事件和核心产品使用路径。"),
            (device, "该图用于比较设备或版本结构，辅助定位兼容性与体验问题。"),
        ):
            if column:
                chart = _top_contribution(df, column, None, insight)
                if chart:
                    charts.append(chart)

    else:
        if time_col:
            chart = _record_trend(df, time_col)
            if chart:
                charts.append(chart)
        if category:
            chart = _top_contribution(df, category, amount, "该图用于识别主要业务维度的规模或贡献差异。")
            if chart:
                charts.append(chart)

    correlation = _correlation(df)
    if correlation and len(charts) < max_charts:
        charts.append(correlation)
    missing = _missing_chart(df)
    if missing and len(charts) < max_charts:
        charts.append(missing)

    if not charts:
        numeric = list(df.select_dtypes(include=np.number).columns)
        if numeric:
            chart = _distribution(df, str(numeric[0]), "该图用于了解核心数值字段的分布和异常区间。")
            if chart:
                charts.append(chart)

    return charts[:max_charts]


def render_chart(spec: Dict[str, Any]) -> Any:
    """将图表规格渲染为统一风格的 Matplotlib Figure。"""
    chart_type = spec["type"]
    data = spec["data"]
    fig, ax = plt.subplots(figsize=(9, 4.6), facecolor="white")

    if chart_type == "line":
        for index, column in enumerate(data.columns):
            ax.plot(data.index, data[column], color=PRIMARY if index == 0 else SECONDARY, linewidth=2.2, label=str(column))
        if len(data.columns) > 1:
            ax.legend(frameon=False, loc="best")
    elif chart_type == "barh":
        column = data.columns[0]
        ax.barh([str(value) for value in data.index], data[column], color=PRIMARY)
        ax.grid(axis="x", color=GRID, linewidth=0.8, alpha=0.7)
        ax.grid(axis="y", visible=False)
    elif chart_type == "hist":
        ax.hist(data[spec["x"]].dropna(), bins=12, color=PRIMARY, edgecolor="white")
        ax.set_xlabel(spec["x"])
        ax.set_ylabel("Frequency")
    elif chart_type == "scatter":
        ax.scatter(data[spec["x"]], data[spec["y"]], color=PRIMARY, alpha=0.7, edgecolors="white")
        ax.set_xlabel(spec["x"])
        ax.set_ylabel(spec["y"])
    elif chart_type == "heatmap":
        image = ax.imshow(data.values, cmap="Blues", vmin=-1, vmax=1)
        ax.set_xticks(range(len(data.columns)), data.columns, rotation=45, ha="right")
        ax.set_yticks(range(len(data.index)), data.index)
        fig.colorbar(image, ax=ax, fraction=0.03, pad=0.03)

    apply_mckinsey_style(ax, spec["title"])
    fig.tight_layout()
    return fig


# v0.2 兼容接口
def build_visualization_data(df: pd.DataFrame) -> Dict[str, Any]:
    """保留 v0.2 测试依赖的基础图表数据接口。"""
    missing = df.isna().sum().sort_values(ascending=False).rename("缺失值数量").to_frame()
    numeric: Dict[str, pd.DataFrame] = {}
    for column in list(df.select_dtypes(include=np.number).columns[:3]):
        values = df[column].dropna()
        if values.nunique() >= 2:
            counts, edges = np.histogram(values, bins=min(10, values.nunique()))
            numeric[str(column)] = pd.DataFrame(
                {"记录数": counts},
                index=[f"{edges[i]:.2f} ~ {edges[i + 1]:.2f}" for i in range(len(counts))],
            )
    categorical: Dict[str, pd.DataFrame] = {}
    for column in df.select_dtypes(include=["object", "category", "bool"]).columns:
        name = str(column)
        if name.lower().endswith("_id") or any(key in name.lower() for key in TIME_KEYWORDS):
            continue
        categorical[name] = df[column].fillna("缺失值").astype(str).value_counts().head(10).rename("记录数").to_frame()
        if len(categorical) == 3:
            break
    time_col = find_datetime_column(df)
    time_data = pd.DataFrame()
    if time_col:
        dates = pd.to_datetime(df[time_col], errors="coerce").dropna()
        time_data = dates.dt.floor("D").value_counts().sort_index().rename("记录数").to_frame()
    return {
        "missing": missing,
        "numeric": numeric,
        "categorical": categorical,
        "time_trend": {"column": time_col, "data": time_data},
    }
