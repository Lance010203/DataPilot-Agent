"""DataPilot Agent Streamlit 应用入口。"""

from pathlib import Path

import pandas as pd
import streamlit as st

from src.analysis_advisor import generate_analysis_suggestions
from src.business_scene_infer import infer_business_scene
from src.cleaning_advisor import generate_cleaning_suggestions
from src.data_loader import load_csv_or_excel
from src.data_profile import get_basic_profile
from src.report_generator import generate_markdown_report
from src.sql_template_generator import generate_sql_templates


st.set_page_config(
    page_title="DataPilot Agent",
    layout="wide",
)

st.title("DataPilot Agent｜数据处理与分析工作流助手")
st.caption(
    "上传 CSV 或 Excel，自动完成数据理解、质量检查、业务场景推断、"
    "清洗建议、分析建议、SQL 模板和 Markdown 报告生成。"
)

uploaded_file = st.file_uploader(
    "上传业务数据文件",
    type=["csv", "xlsx"],
    help="CSV 支持 UTF-8/GBK 编码，Excel 支持 XLSX。",
)

if st.button("使用内置示例数据", width="stretch"):
    st.session_state["use_sample_data"] = True

if uploaded_file is None and not st.session_state.get("use_sample_data", False):
    st.info("请上传一个 CSV 或 XLSX 文件，或点击上方按钮体验完整分析流程。")
    st.stop()

try:
    data_source = (
        uploaded_file
        if uploaded_file is not None
        else Path(__file__).parent / "data" / "sample_orders.csv"
    )
    dataframe = load_csv_or_excel(data_source)
except Exception as error:
    st.error(f"文件读取失败：{error}")
    st.stop()

if dataframe.empty:
    st.warning("文件读取成功，但数据为空。")
    st.stop()

with st.spinner("DataPilot Agent 正在执行分析 Workflow..."):
    profile = get_basic_profile(dataframe)
    scene_info = infer_business_scene(dataframe)
    cleaning_suggestions = generate_cleaning_suggestions(profile)
    analysis_suggestions = generate_analysis_suggestions(
        scene_info["scene_name"], dataframe
    )
    sql_templates = generate_sql_templates(dataframe, scene_info["scene_name"])
    markdown_report = generate_markdown_report(
        dataframe,
        profile,
        scene_info,
        cleaning_suggestions,
        analysis_suggestions,
        sql_templates,
    )

st.success(f"分析完成：初步识别为「{scene_info['scene_name']}」")

metric_columns = st.columns(4)
metric_columns[0].metric("数据行数", profile["shape"]["rows"])
metric_columns[1].metric("数据列数", profile["shape"]["columns"])
metric_columns[2].metric("重复行数", profile["duplicate_count"])
metric_columns[3].metric(
    "潜在异常值",
    sum(item["count"] for item in profile["possible_outliers"].values()),
)

overview_tab, quality_tab, advice_tab, sql_tab, report_tab = st.tabs(
    ["数据概览", "质量检查", "Agent 建议", "SQL 模板", "Markdown 报告"]
)

with overview_tab:
    st.subheader("数据前 5 行")
    st.dataframe(dataframe.head(), width="stretch")

    st.subheader("字段信息")
    field_info = pd.DataFrame(
        {
            "字段名": profile["columns"],
            "字段类型": [profile["dtypes"][column] for column in profile["columns"]],
            "缺失值数量": [
                profile["missing_count"][column] for column in profile["columns"]
            ],
            "缺失率(%)": [
                profile["missing_rate"][column] for column in profile["columns"]
            ],
        }
    )
    st.dataframe(field_info, width="stretch", hide_index=True)

    st.subheader("业务场景推断")
    st.markdown(f"**场景：{scene_info['scene_name']}**")
    st.write(scene_info["reason"])
    for question in scene_info["possible_business_questions"]:
        st.markdown(f"- {question}")

with quality_tab:
    st.subheader("数值型字段统计")
    if profile["numeric_summary"]:
        numeric_summary_df = pd.DataFrame(profile["numeric_summary"]).T.reset_index()
        numeric_summary_df = numeric_summary_df.rename(
            columns={
                "index": "字段",
                "mean": "均值",
                "min": "最小值",
                "max": "最大值",
                "median": "中位数",
                "std": "标准差",
            }
        )
        st.dataframe(numeric_summary_df, width="stretch", hide_index=True)
    else:
        st.info("当前数据没有可统计的数值型字段。")

    st.subheader("类别型字段统计")
    if profile["categorical_summary"]:
        categorical_summary_df = (
            pd.DataFrame(profile["categorical_summary"]).T.reset_index()
        )
        categorical_summary_df = categorical_summary_df.rename(
            columns={
                "index": "字段",
                "unique_count": "唯一值数量",
                "top": "最高频值",
                "top_frequency": "最高频次数",
            }
        )
        st.dataframe(
            categorical_summary_df, width="stretch", hide_index=True
        )
    else:
        st.info("当前数据没有类别型字段。")

    st.subheader("IQR 潜在异常值")
    outlier_df = pd.DataFrame(profile["possible_outliers"]).T.reset_index()
    if not outlier_df.empty:
        outlier_df = outlier_df.rename(
            columns={
                "index": "字段",
                "count": "异常值数量",
                "lower_bound": "下界",
                "upper_bound": "上界",
            }
        )
        st.dataframe(outlier_df, width="stretch", hide_index=True)
    else:
        st.info("当前数据没有可检查的数值型字段。")

with advice_tab:
    left_column, right_column = st.columns(2)
    with left_column:
        st.subheader("数据清洗建议")
        for index, suggestion in enumerate(cleaning_suggestions, 1):
            st.markdown(f"{index}. {suggestion}")
    with right_column:
        st.subheader("后续分析建议")
        for index, suggestion in enumerate(analysis_suggestions, 1):
            st.markdown(f"{index}. {suggestion}")

with sql_tab:
    st.caption("模板使用通用 SQL 语法，日期函数和字段引用方式可按数据库调整。")
    for template in sql_templates:
        st.subheader(template["title"])
        st.write(template["description"])
        st.code(template["sql"], language="sql")

with report_tab:
    st.markdown(markdown_report)
    st.download_button(
        "下载 Markdown 报告",
        data=markdown_report.encode("utf-8"),
        file_name="datapilot_analysis_report.md",
        mime="text/markdown",
        width="stretch",
    )
