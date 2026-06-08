"""DataPilot Agent v0.3 Streamlit 应用入口。"""

from pathlib import Path

import pandas as pd
import streamlit as st

from src.analysis_advisor import generate_analysis_plan
from src.cleaning_advisor import generate_cleaning_suggestions
from src.data_cleaner import clean_dataframe, dataframe_to_csv_bytes
from src.data_loader import load_csv_or_excel
from src.data_profile import get_basic_profile
from src.kpi_advisor import generate_kpis
from src.report_generator import generate_markdown_report
from src.scenario_detector import SCENARIO_ORDER, detect_business_scenario
from src.sql_template_generator import generate_python_templates, generate_sql_templates
from src.visualization_advisor import build_professional_visualizations, render_chart


st.set_page_config(page_title="DataPilot Agent v0.3", layout="wide")


def show_section(title: str, description: str = "") -> None:
    st.divider()
    st.subheader(title)
    if description:
        st.caption(description)


def build_field_info(profile: dict) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "字段名": profile["columns"],
            "字段类型": [profile["dtypes"][column] for column in profile["columns"]],
            "缺失值数量": [profile["missing_count"][column] for column in profile["columns"]],
            "缺失率(%)": [profile["missing_rate"][column] for column in profile["columns"]],
        }
    )


st.title("DataPilot Agent｜数据处理与分析工作流助手")
st.markdown("**面向业务数据分析前期流程的轻量级 AI Agent / Workflow Demo。**")
st.caption("v0.3 Professional · 场景判断、关键指标、专业可视化与初步商业分析报告")

# 1. 数据上传
show_section("1. 数据上传", "支持 UTF-8 / GBK CSV 与 XLSX；原始文件不会被自动修改。")
uploaded_file = st.file_uploader("上传业务数据文件", type=["csv", "xlsx"])
if st.button("使用内置示例数据", width="stretch"):
    st.session_state["use_sample_data"] = True

if uploaded_file is None and not st.session_state.get("use_sample_data", False):
    st.info("请上传 CSV / XLSX，或使用内置订单样例体验完整工作流。")
    st.stop()

try:
    source = uploaded_file or Path(__file__).parent / "data" / "sample_orders.csv"
    dataframe = load_csv_or_excel(source)
except Exception as error:
    st.error(f"文件读取失败：{error}")
    st.stop()
if dataframe.empty:
    st.warning("文件读取成功，但数据为空。")
    st.stop()

with st.spinner("正在理解数据结构并生成专业分析工作流..."):
    profile = get_basic_profile(dataframe)
    scenario_result = detect_business_scenario(dataframe)
    cleaning_suggestions = generate_cleaning_suggestions(profile)

st.success("数据加载成功，已完成字段识别与初步场景判断。")

# 2. 数据预览
show_section("2. 数据预览", "快速核对字段、样例值和数据粒度。")
st.dataframe(dataframe.head(), width="stretch", hide_index=True)

# 3. 数据概览
show_section("3. 数据概览")
overview_columns = st.columns(4)
overview_columns[0].metric("记录数", profile["shape"]["rows"])
overview_columns[1].metric("字段数", profile["shape"]["columns"])
overview_columns[2].metric("重复记录", profile["duplicate_count"])
overview_columns[3].metric(
    "潜在异常值",
    sum(item["count"] for item in profile["possible_outliers"].values()),
)
st.dataframe(build_field_info(profile), width="stretch", hide_index=True)

# 4. 数据质量检查
show_section("4. 数据质量检查", "聚焦缺失、重复、字段类型和 IQR 潜在异常值。")
quality_left, quality_right = st.columns(2)
with quality_left:
    st.markdown("#### 数值字段统计")
    if profile["numeric_summary"]:
        numeric_summary = pd.DataFrame(profile["numeric_summary"]).T.reset_index()
        numeric_summary = numeric_summary.rename(
            columns={
                "index": "字段",
                "mean": "均值",
                "min": "最小值",
                "max": "最大值",
                "median": "中位数",
                "std": "标准差",
            }
        )
        st.dataframe(numeric_summary, width="stretch", hide_index=True)
    else:
        st.info("当前数据没有可统计的数值字段。")
with quality_right:
    st.markdown("#### 类别字段统计")
    if profile["categorical_summary"]:
        category_summary = pd.DataFrame(profile["categorical_summary"]).T.reset_index()
        category_summary = category_summary.rename(
            columns={
                "index": "字段",
                "unique_count": "唯一值数量",
                "top": "最高频值",
                "top_frequency": "最高频次数",
            }
        )
        st.dataframe(category_summary, width="stretch", hide_index=True)
    else:
        st.info("当前数据没有类别字段。")

outlier_frame = pd.DataFrame(profile["possible_outliers"]).T.reset_index()
if not outlier_frame.empty:
    st.markdown("#### 潜在异常值")
    st.dataframe(
        outlier_frame.rename(
            columns={"index": "字段", "count": "异常值数量", "lower_bound": "IQR 下界", "upper_bound": "IQR 上界"}
        ),
        width="stretch",
        hide_index=True,
    )

# 5. 业务场景判断
show_section("5. 业务场景判断", "综合字段组合、数据类型和值特征计算置信度，并由用户最终确认。")
scenario_metrics = st.columns(2)
scenario_metrics[0].metric("自动判断场景", scenario_result["primary_scenario"])
scenario_metrics[1].metric("判断置信度", f"{scenario_result['confidence']:.0%}")

st.markdown("#### 判断依据")
for signal in scenario_result["matched_signals"]:
    st.markdown(f"- {signal}")
if scenario_result["alternative_scenarios"]:
    alternatives = "；".join(
        f"{item['scenario']}（{item['confidence']:.0%}）"
        for item in scenario_result["alternative_scenarios"]
    )
    st.caption(f"备选场景：{alternatives}")
if scenario_result["warning"]:
    st.warning(scenario_result["warning"])

default_index = SCENARIO_ORDER.index(scenario_result["primary_scenario"])
confirmed_scenario = st.selectbox(
    "人工确认或覆盖业务场景",
    options=SCENARIO_ORDER,
    index=default_index,
    help="后续 KPI、可视化、分析建议和报告均以此处确认的场景为准。",
)
st.info(f"后续工作流采用场景：**{confirmed_scenario}**")

with st.spinner("正在基于确认场景计算 KPI、图表和分析建议..."):
    kpis = generate_kpis(dataframe, confirmed_scenario)
    visualizations = build_professional_visualizations(dataframe, confirmed_scenario)
    analysis_plan = generate_analysis_plan(
        confirmed_scenario, dataframe, profile, kpis, visualizations
    )
    sql_templates = generate_sql_templates(dataframe, confirmed_scenario)
    python_templates = generate_python_templates(dataframe, confirmed_scenario)
    markdown_report = generate_markdown_report(
        dataframe,
        profile,
        scenario_result,
        cleaning_suggestions,
        analysis_plan["priority_directions"],
        sql_templates,
        kpis=kpis,
        visualizations=visualizations,
        analysis_plan=analysis_plan,
        python_templates=python_templates,
        confirmed_scenario=confirmed_scenario,
    )

# 6. 关键业务指标
show_section("6. 关键业务指标", "仅计算字段存在且口径合理的指标；不可计算项会明确提示。")
available_kpis = [item for item in kpis if item["available"]]
unavailable_kpis = [item for item in kpis if not item["available"]]
if available_kpis:
    for start in range(0, len(available_kpis), 4):
        metric_columns = st.columns(min(4, len(available_kpis[start:start + 4])))
        for column, item in zip(metric_columns, available_kpis[start:start + 4]):
            column.metric(item["name"], item["value"], help=item["note"])
if unavailable_kpis:
    with st.expander("暂不可计算的指标"):
        for item in unavailable_kpis:
            st.markdown(f"- **{item['name']}**：{item['note']}")

# 7. 专业可视化分析
show_section("7. 专业可视化分析", "少而精地展示 4–6 张最有业务价值的图表，每张图附带业务 insight。")
if visualizations:
    for start in range(0, len(visualizations), 2):
        chart_columns = st.columns(2)
        for column, spec in zip(chart_columns, visualizations[start:start + 2]):
            with column:
                try:
                    figure = render_chart(spec)
                    st.pyplot(figure, width="stretch")
                    figure.clear()
                    st.markdown(f"**Insight：** {spec['insight']}")
                except Exception as error:
                    st.info(f"图表 `{spec['title']}` 暂无法生成：{error}")
else:
    st.info("当前字段不足以生成高价值图表，建议补充时间、业务维度或数值指标字段。")

# 8. Human-in-the-loop 清洗与下载
show_section("8. Human-in-the-loop 清洗与下载", "只有用户勾选的操作才执行，原始数据始终保留。")
clean_columns = st.columns(3)
with clean_columns[0]:
    remove_duplicates = st.checkbox("删除重复行")
with clean_columns[1]:
    normalize_columns = st.checkbox("字段名标准化")
with clean_columns[2]:
    convert_datetime = st.checkbox("转换时间字段")

cleaned_dataframe, cleaning_log = clean_dataframe(
    dataframe,
    remove_duplicates=remove_duplicates,
    normalize_columns=normalize_columns,
    convert_datetime=convert_datetime,
)
shape_columns = st.columns(2)
shape_columns[0].metric(
    "清洗前数据规模",
    f"{cleaning_log['before_shape']['rows']} 行 × {cleaning_log['before_shape']['columns']} 列",
)
shape_columns[1].metric(
    "清洗后数据规模",
    f"{cleaning_log['after_shape']['rows']} 行 × {cleaning_log['after_shape']['columns']} 列",
)
for operation in cleaning_log["operations"]:
    st.markdown(f"- {operation}")
if cleaning_log["high_missing_columns"]:
    text = "、".join(f"`{column}`（{rate:.1f}%）" for column, rate in cleaning_log["high_missing_columns"].items())
    st.warning(f"高缺失字段需要人工判断，系统不会默认删除：{text}")
with st.expander("预览清洗结果"):
    st.dataframe(cleaned_dataframe.head(), width="stretch", hide_index=True)
st.download_button(
    "下载清洗后的 CSV",
    dataframe_to_csv_bytes(cleaned_dataframe),
    file_name="cleaned_data.csv",
    mime="text/csv",
    width="stretch",
)

# 9. 分析建议
show_section("9. 分析建议", "以业务问题、优先方向、数据风险和交付物为核心组织建议。")
advice_left, advice_right = st.columns(2)
with advice_left:
    st.markdown("#### 当前数据适合回答的问题")
    for item in analysis_plan["questions"]:
        st.markdown(f"- {item}")
    st.markdown("#### 建议优先分析的 3 个方向")
    for index, item in enumerate(analysis_plan["priority_directions"], 1):
        st.markdown(f"{index}. {item}")
    st.markdown("#### 需要补充的数据字段")
    for item in analysis_plan["missing_data"]:
        st.markdown(f"- {item}")
with advice_right:
    st.markdown("#### 可能存在的数据风险")
    for item in analysis_plan["data_risks"]:
        st.markdown(f"- {item}")
    st.markdown("#### 可形成的业务交付物")
    for item in analysis_plan["deliverables"]:
        st.markdown(f"- {item}")
    st.markdown("#### 数据清洗建议")
    for item in cleaning_suggestions:
        st.markdown(f"- {item}")

# 10. SQL / Python 分析模板
show_section("10. SQL / Python 分析模板", "提供可复制修改的通用分析起点。")
template_tabs = st.tabs(["SQL 模板", "Python / Pandas 模板"])
with template_tabs[0]:
    for template in sql_templates:
        with st.expander(template["title"]):
            st.write(template["description"])
            st.code(template["sql"], language="sql")
with template_tabs[1]:
    for template in python_templates:
        with st.expander(template["title"]):
            st.write(template["description"])
            st.code(template["python"], language="python")

# 11. Markdown 报告生成
show_section("11. Markdown 报告生成", "输出结论先行的初步商业分析报告。")
with st.expander("查看完整报告"):
    st.markdown(markdown_report)
st.download_button(
    "下载 Markdown 报告",
    markdown_report.encode("utf-8"),
    file_name="datapilot_business_analysis_report.md",
    mime="text/markdown",
    width="stretch",
)
