"""v0.3 专业场景、KPI 与可视化测试。"""

import unittest
from pathlib import Path

import pandas as pd

from src.data_loader import load_csv_or_excel
from src.kpi_advisor import generate_kpis
from src.scenario_detector import detect_business_scenario
from src.visualization_advisor import build_professional_visualizations, render_chart


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class DataPilotV03ProfessionalTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.orders = load_csv_or_excel(PROJECT_ROOT / "data" / "sample_orders.csv")

    def test_single_lat_does_not_trigger_delivery(self) -> None:
        result = detect_business_scenario(
            pd.DataFrame({"lat": [31.2, 31.3], "name": ["A", "B"]})
        )
        self.assertEqual(result["primary_scenario"], "通用业务数据")
        self.assertLess(result["confidence"], 0.65)
        self.assertTrue(result["warning"])

    def test_macro_scenario_has_priority(self) -> None:
        result = detect_business_scenario(
            pd.DataFrame(
                {
                    "Date": ["2025-01-01", "2025-02-01"],
                    "CPI": [2.1, 2.3],
                    "InterestRate": [3.2, 3.1],
                    "Region": ["China", "China"],
                }
            )
        )
        self.assertEqual(result["primary_scenario"], "宏观经济/金融市场数据")
        self.assertGreaterEqual(result["confidence"], 0.65)

    def test_order_kpis(self) -> None:
        kpis = generate_kpis(self.orders, "订单/交易数据")
        values = {item["name"]: item["value"] for item in kpis}
        self.assertEqual(values["总订单量"], "29")
        self.assertIn("¥", values["总 GMV / 收入"])
        self.assertEqual(values["用户数"], "24")

    def test_professional_charts_are_limited_and_varied(self) -> None:
        charts = build_professional_visualizations(self.orders, "订单/交易数据")
        self.assertGreaterEqual(len(charts), 4)
        self.assertLessEqual(len(charts), 6)
        self.assertGreaterEqual(len({chart["type"] for chart in charts}), 3)
        for chart in charts:
            self.assertTrue(chart["insight"])
            self.assertIsNotNone(render_chart(chart))


if __name__ == "__main__":
    unittest.main()
