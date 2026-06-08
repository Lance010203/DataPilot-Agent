# DataPilot Agent

DataPilot Agent 是一个面向业务数据分析前期流程的轻量级数据分析工作流工具。

用户上传 CSV 或 Excel 文件后，系统可以自动完成数据预览、字段识别、数据质量检查、业务场景判断、关键指标提取、专业可视化、基础清洗和 Markdown 报告生成。

该项目的目标不是替代完整的数据分析流程，而是帮助用户在拿到一份陌生业务数据时，快速完成初步理解、质量检查和分析方向判断。项目默认基于本地规则运行，不依赖付费 API。

## 功能特性

- CSV / Excel 文件上传与读取
- UTF-8、GBK 等常见 CSV 编码兼容
- 内置示例数据快速体验
- 数据预览与基础概览
- 字段类型识别
- 缺失值、重复值和潜在异常值检查
- 业务场景判断与置信度提示
- 支持用户手动确认或修正业务场景
- 关键业务指标自动提取
- 根据不同业务场景生成可视化图表
- Human-in-the-loop 基础清洗流程
- 清洗后数据下载
- SQL / Python 分析模板生成
- Markdown 数据分析报告生成与下载

## 业务场景识别

系统会根据字段名称、字段组合、数据类型和数据特征，对上传数据进行业务场景判断。当前支持的场景包括：

- 订单 / 交易数据
- 配送 / 履约数据
- 营销 / 增长数据
- 风控 / 信用 / 预测数据
- 财务 / 经营分析数据
- 宏观经济 / 金融市场数据
- 用户行为 / 产品分析数据
- 通用业务数据

页面会展示判断依据、置信度和备选场景。当自动判断置信度较低时，系统会提示用户进行人工确认，避免后续指标、图表和分析方向出现偏差。

## 可视化分析

DataPilot Agent 会根据字段结构和业务场景选择合适的图表，而不是简单堆叠图表。目前支持的可视化类型包括：

- 时间趋势图
- Top N 横向条形图
- 数值分布图
- 数值字段关系散点图
- 相关性分析
- 业务指标对比图
- 缺失值可视化

页面最多展示 6 张主要图表。每张图表会附带简短说明，用于解释图表可以回答的业务问题。缺少合适字段时，系统会给出提示，不会中断整体分析流程。

## Human-in-the-loop 清洗流程

数据清洗不会默认自动执行。用户可以根据需要手动选择是否进行以下操作：

- 删除完全重复行
- 将字段名标准化为小写下划线格式
- 自动识别并转换日期或时间字段
- 查看缺失率较高的字段提示
- 下载清洗后的数据文件

高缺失字段只进行提示，不会被自动删除。页面会对比清洗前后的行数和列数，并记录实际执行的操作。原始 DataFrame 在分析过程中保持不变。

## 技术栈

- Python
- Pandas
- NumPy
- Streamlit
- Matplotlib
- OpenPyXL

项目使用模块化的规则驱动 Workflow 组织数据加载、质量检查、场景识别、指标计算、建议生成和报告输出。`prompts/` 目录保留了可用于后续接入大模型的 Prompt 模板，但当前版本默认不调用外部模型服务。

## 项目结构

```text
DataPilot-Agent/
├── app.py
├── requirements.txt
├── README.md
├── data/
│   ├── README.md
│   └── sample_orders.csv
├── reports/
│   └── sample_report.md
├── screenshots/
│   └── README.md
├── prompts/
│   ├── data_analysis_agent_prompt.md
│   └── cleaning_advisor_prompt.md
├── src/
│   ├── __init__.py
│   ├── init.py
│   ├── data_loader.py
│   ├── data_profile.py
│   ├── business_scene_infer.py
│   ├── scenario_detector.py
│   ├── kpi_advisor.py
│   ├── visualization_advisor.py
│   ├── cleaning_advisor.py
│   ├── data_cleaner.py
│   ├── analysis_advisor.py
│   ├── sql_template_generator.py
│   └── report_generator.py
└── tests/
    ├── __init__.py
    ├── test_v02_workflow.py
    └── test_v03_professional.py
```

## 运行方式

建议使用 Python 3.10 或更高版本。

1. 克隆项目：

```bash
git clone https://github.com/Lance010203/DataPilot-Agent.git
cd DataPilot-Agent
```

2. 创建并激活虚拟环境：

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows 环境使用：

```powershell
.venv\Scripts\activate
```

3. 安装依赖：

```bash
python3 -m pip install -r requirements.txt
```

4. 启动应用：

```bash
python3 -m streamlit run app.py
```

5. 在浏览器中打开：

```text
http://localhost:8501
```

进入页面后，可以上传 CSV / XLSX 文件，也可以使用内置订单示例运行完整流程。

运行测试：

```bash
python3 -m unittest discover -s tests -v
```

## 分析输出

完成数据加载后，系统会按顺序生成：

1. 数据预览与字段概览
2. 缺失值、重复值和 IQR 潜在异常值检查
3. 业务场景、置信度、判断依据和备选场景
4. 当前字段可支持的关键业务指标
5. 与业务场景匹配的图表及简要说明
6. 数据清洗建议和可选清洗操作
7. 后续分析方向
8. SQL 与 Python / Pandas 分析模板
9. 可下载的 Markdown 初步分析报告

仓库内提供了一份基于示例订单数据生成的报告：[reports/sample_report.md](reports/sample_report.md)。

## 版本更新

### v0.3

- 优化页面模块结构，从数据上传开始形成完整分析流程
- 升级业务场景判断逻辑，引入置信度、匹配依据、备选场景和人工确认机制
- 新增关键业务指标模块
- 扩展订单、履约、营销、风控、财务、宏观金融和产品行为场景
- 优化可视化模块，根据业务场景和字段组合选择图表
- 为图表增加业务问题说明
- 同时生成 SQL 与 Python / Pandas 分析模板
- 优化 Markdown 报告结构，使输出更接近初步数据分析报告

### v0.2

- 新增自动可视化模块
- 新增基础清洗与清洗后数据下载功能
- 增强商业分析建议模块
- 优化 Streamlit 页面结构
- 更新 Markdown 报告生成内容
- 增加核心 Workflow 自动化测试

### v0.1

- 实现 CSV / Excel 上传
- 实现基础数据预览
- 实现字段识别、数据质量检查和业务场景推断
- 实现清洗建议与分析建议
- 实现 SQL 模板和 Markdown 报告初版输出

## 后续计划

- 接入可选的大模型 API，用于增强自然语言分析和报告生成
- 增加更多业务场景和字段识别规则
- 支持用户配置指标口径和自定义业务指标
- 支持更多图表类型与报告导出格式
- 增加更多测试用例和示例数据集
- 优化报告排版与可视化导出
- 增加场景规则和指标规则的配置化管理

## License

This project is for learning and demonstration purposes.
