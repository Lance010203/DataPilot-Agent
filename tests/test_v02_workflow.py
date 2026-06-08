"""v0.2 核心 Workflow 回归测试。"""

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.analysis_advisor import generate_analysis_suggestions
from src.business_scene_infer import infer_business_scene
from src.cleaning_advisor import generate_cleaning_suggestions
from src.data_cleaner import clean_dataframe, dataframe_to_csv_bytes
from src.data_loader import load_csv_or_excel
from src.data_profile import get_basic_profile
from src.report_generator import generate_markdown_report
from src.sql_template_generator import generate_sql_templates
from src.visualization_advisor import build_visualization_data


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_DATA = PROJECT_ROOT / "data" / "sample_orders.csv"


class DataPilotV02WorkflowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.df = load_csv_or_excel(SAMPLE_DATA)

    def test_csv_and_excel_loader(self) -> None:
        self.assertEqual(self.df.shape, (30, 9))

        with tempfile.NamedTemporaryFile(suffix=".xlsx") as temp_file:
            self.df.head(3).to_excel(temp_file.name, index=False)
            excel_df = load_csv_or_excel(Path(temp_file.name))
        self.assertEqual(excel_df.shape, (3, 9))

    def test_visualization_data(self) -> None:
        charts = build_visualization_data(self.df)
        self.assertEqual(int(charts["missing"]["缺失值数量"].sum()), 5)
        self.assertTrue(charts["numeric"])
        self.assertIn("product_category", charts["categorical"])
        self.assertEqual(charts["time_trend"]["column"], "order_time")
        self.assertFalse(charts["time_trend"]["data"].empty)

    def test_human_in_the_loop_cleaning(self) -> None:
        unchanged, unchanged_log = clean_dataframe(self.df)
        self.assertTrue(unchanged.equals(self.df))
        self.assertEqual(
            unchanged_log["before_shape"],
            unchanged_log["after_shape"],
        )

        cleaned, log = clean_dataframe(
            self.df,
            remove_duplicates=True,
            normalize_columns=True,
            convert_datetime=True,
        )
        self.assertEqual(cleaned.shape, (29, 9))
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(cleaned["order_time"]))
        self.assertGreater(len(dataframe_to_csv_bytes(cleaned)), 100)
        self.assertEqual(len(log["operations"]), 3)

    def test_business_advice_and_report(self) -> None:
        profile = get_basic_profile(self.df)
        scene = infer_business_scene(self.df)
        cleaning = generate_cleaning_suggestions(profile)
        analysis = generate_analysis_suggestions(scene["scene_name"], self.df)
        sql_templates = generate_sql_templates(self.df, scene["scene_name"])
        report = generate_markdown_report(
            self.df,
            profile,
            scene,
            cleaning,
            analysis,
            sql_templates,
        )

        self.assertEqual(scene["scene_name"], "订单/交易数据")
        self.assertTrue(any("GMV" in suggestion for suggestion in analysis))
        for heading in (
            "## 1. Executive Summary",
            "## 2. 数据基本信息",
            "## 3. 业务场景判断与置信度",
            "## 4. 关键指标概览",
            "## 5. 数据质量问题",
            "## 6. 主要可视化发现",
            "## 7. 初步商业洞察",
            "## 8. 后续分析建议",
            "## 9. 可执行下一步",
        ):
            self.assertIn(heading, report)


if __name__ == "__main__":
    unittest.main()
