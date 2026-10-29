# README

# AI / 数据类岗位数据分析看板

个人学习项目（进行中）。基于 Streamlit + Pandas + Plotly 的交互式数据分析看板，
对 1800 条 AI / 数据类岗位的模拟数据做探索性分析、指标监控与异常归因。

> ⚠️ 数据说明：`jobs.csv`（项目根目录，程序也兼容放在 `data/jobs.csv`）为**模拟生成的演示数据**（用于练习完整分析流程，
> 含人为注入的波动点用于演示异常监控），不代表真实招聘市场行情。

## 功能与设计

| 模块 | 内容 | 对应能力 |
| --- | --- | --- |
| 📊 看板总览 | 多条件筛选、核心指标卡、薪资分布/结构图表、明细表 | 数据可视化看板搭建 |
| 🚨 指标监控与异常归因 | 日均薪资趋势、Z-Score 异常点检测、按城市下钻定位波动来源 | 数据异常监控与归因分析 |
| 📖 数据字典与指标口径 | 字段含义说明表、KPI 计算口径定义 | 数据治理、指标体系建设 |

## 技术栈

Python · Pandas（读取/筛选/groupby 聚合/时序处理）· Plotly（可视化）· Streamlit（Web 界面）

## 本地运行

```bash
pip install -r requirements.txt
streamlit run app.py
```

启动后浏览器访问 http://localhost:8501 。数据文件路径基于 `app.py` 所在目录解析，因此在任意工作目录下启动均可正常读取。

## 学习路线（配合开源项目）

- 数据处理部分：参考 [Datawhale《Joyful-Pandas》](https://github.com/datawhalechina/joyful-pandas)
- 深度学习原理：参考 [Datawhale《南瓜书》](https://github.com/datawhalechina/leedl-tutorial)

## TODO

- [ ] 接入真实招聘数据（爬虫采集 + 清洗）
- [ ] 增加薪资预测模块（线性回归）
