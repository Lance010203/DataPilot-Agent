# DataPilot Agent｜数据处理与分析工作流助手

> 一个面向业务数据分析场景的轻量级 **AI Agent / Workflow Demo**：上传 CSV 或 Excel 后，自动完成字段识别、数据质量检查、业务场景推断、数据清洗建议、分析方向建议、SQL 模板和 Markdown 报告生成。

## 项目背景

业务分析的第一步通常不是建模，而是反复确认字段、检查数据质量、理解业务口径并整理分析思路。这些步骤高度重复，也很适合被拆解成可解释的 Agent Workflow。

DataPilot Agent 使用 **Python + Pandas + Streamlit** 实现一条轻量级自动分析流程。第一版默认不依赖付费 API，通过规则逻辑和 Prompt Engineering 模板模拟 AI Agent 的“理解、检查、建议、生成”过程，优先保证项目能运行、能展示、能讲清楚。

## 核心功能

- 上传并读取 UTF-8 / GBK CSV 和 XLSX 文件；
- 支持一键加载内置订单样例，快速体验完整流程；
- 展示数据样例、行列数、字段名与字段类型；
- 统计每列缺失数量、缺失率和完全重复行；
- 输出数值字段描述性统计和类别字段摘要；
- 使用 IQR 方法识别潜在异常值；
- 根据字段关键词完成业务场景推断；
- 自动生成数据清洗建议和后续分析建议；
- 根据实际字段生成 SQL 分析模板；
- 生成可展示、可下载的 Markdown 初步分析报告；
- 提供数据分析 Agent 和清洗建议 Agent 的 Prompt 模板。

## Workflow

```text
上传 CSV / Excel
        ↓
数据读取与编码兼容
        ↓
字段识别与基础画像
        ↓
缺失 / 重复 / 异常值检查
        ↓
业务场景推断
        ↓
清洗建议 + 分析建议
        ↓
SQL 模板 + Markdown 报告
```

## 技术栈

- **应用界面**：Streamlit
- **数据处理**：Python、Pandas、NumPy
- **文件支持**：CSV、Excel、OpenPyXL
- **分析能力**：描述性统计、数据质量检查、IQR 异常值识别
- **Agent 设计**：规则驱动 Workflow、Prompt Engineering、模块化任务编排
- **分析输出**：SQL 模板、Markdown 报告

## 项目结构

```text
DataPilot-Agent/
├── README.md
├── app.py
├── requirements.txt
├── .gitignore
├── data/
│   ├── README.md
│   └── sample_orders.csv
├── prompts/
│   ├── data_analysis_agent_prompt.md
│   └── cleaning_advisor_prompt.md
├── reports/
│   └── sample_report.md
├── screenshots/
│   └── README.md
└── src/
    ├── __init__.py
    ├── init.py
    ├── data_loader.py
    ├── data_profile.py
    ├── business_scene_infer.py
    ├── cleaning_advisor.py
    ├── analysis_advisor.py
    ├── sql_template_generator.py
    └── report_generator.py
```

## 快速开始

建议使用 Python 3.10 或更高版本。

```bash
git clone https://github.com/your-name/DataPilot-Agent.git
cd DataPilot-Agent

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows 激活虚拟环境：

```powershell
.venv\Scripts\activate
```

## 运行方式

```bash
streamlit run app.py
```

浏览器通常会自动打开 `http://localhost:8501`。上传自己的 CSV / XLSX，或点击“使用内置示例数据”体验完整 Workflow。

## 示例输出

示例订单数据包含少量缺失值、重复记录和极端值。系统会自动输出：

- 场景判断：订单/交易数据；
- 数据质量结论：缺失字段、重复行、IQR 潜在异常值；
- 清洗建议：时间类型转换、缺失值处理、重复记录核验、异常值复核；
- 分析建议：订单趋势、用户分层、品类排行、支付状态分析；
- SQL 模板：总行数、NULL 统计、日期聚合、类别分组、金额汇总、用户统计；
- Markdown 数据分析初步报告。

仓库内提供示例报告：[reports/sample_report.md](reports/sample_report.md)。

## 项目亮点

1. **完整的 Agent Workflow**

   将数据读取、数据理解、质量检查、业务推断、建议生成和报告输出拆分为独立模块，体现 AI Agent 应用的任务编排思路。

2. **结果可解释**

   场景推断和清洗建议基于透明规则，能够说明触发关键词、缺失率和异常值数量，便于业务人员复核。

3. **不依赖付费 API**

   默认使用本地规则即可运行，降低 Demo 体验门槛；`prompts/` 中预留了接入大模型时可使用的系统提示词。

4. **面向真实业务分析流程**

   不只展示图表，而是覆盖字段识别、数据质量检查、SQL 分析模板和报告生成，更接近数据产品与分析 Workflow。

5. **模块清晰，便于扩展**

   各步骤均为独立 Python 函数，后续可接入 OpenAI 或本地大模型、数据库、可视化和任务历史管理。

## 后续优化方向

- 增加日期、金额、ID、标签字段的语义识别与置信度；
- 支持多个 Sheet、更多 CSV 编码和更大文件的分块读取；
- 增加字段口径确认和人工反馈闭环；
- 接入可选的大模型 API 或本地开源模型；
- 自动生成 Pandas 分析代码和图表；
- 支持数据库连接和 SQL 方言适配；
- 增加清洗前后质量评分与可追踪的处理日志；
- 增加单元测试、Docker 和在线 Demo 部署。

## 求职展示价值

该项目适合用于展示以下能力：

- 将模糊的业务需求拆解为可执行的 **AI Agent / Workflow**；
- 使用 **Prompt Engineering** 约束角色、输入、输出和风险边界；
- 使用 **Python、Pandas、SQL、Streamlit** 完成端到端产品 Demo；
- 理解字段识别、数据质量检查、业务场景推断和数据清洗建议；
- 将分析过程产品化，实现业务数据分析自动化；
- 在不依赖付费模型的情况下完成可运行 MVP，并为大模型接入预留扩展点。

## 说明

本项目输出的是自动化初步分析结果，不替代业务口径确认、数据治理流程或专业建模判断。示例数据为模拟数据，仅用于功能演示。
