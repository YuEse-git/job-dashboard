# -*- coding: utf-8 -*-
"""岗位数据分析看板：Streamlit + Pandas + Plotly
覆盖：可视化看板 / 数据字典 / 指标口径 / 异常监控与波动归因
"""
from pathlib import Path

import pandas as pd
import numpy as np
import plotly.express as px
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent

st.set_page_config(page_title="AI/数据岗位分析看板", layout="wide")
st.title("AI / 数据类岗位数据分析看板")

# ---------- 1. 读取数据 ----------
def resolve_data_path() -> Path:
    """兼容 data/jobs.csv 与项目根目录 jobs.csv 两种存放方式。"""
    for rel in (Path("data") / "jobs.csv", Path("jobs.csv")):
        if (BASE_DIR / rel).is_file():
            return BASE_DIR / rel
    raise FileNotFoundError(
        f"未找到数据文件，请将 jobs.csv 放在 {BASE_DIR} 或其下的 data/ 目录中"
    )


@st.cache_data
def load_data():
    df = pd.read_csv(resolve_data_path(), encoding="utf-8")
    df["发布日期"] = pd.to_datetime(df["发布日期"])
    return df

df = load_data()

tab1, tab2, tab3 = st.tabs(["📊 看板总览", "🚨 指标监控与异常归因", "📖 数据字典与指标口径"])

# ================= Tab1 看板总览 =================
with tab1:
    st.sidebar.header("筛选条件")
    cities = st.sidebar.multiselect("城市", options=sorted(df["城市"].unique()), default=sorted(df["城市"].unique()))
    roles = st.sidebar.multiselect("岗位类别", options=sorted(df["岗位类别"].unique()), default=sorted(df["岗位类别"].unique()))
    exps = st.sidebar.multiselect("经验要求", options=sorted(df["经验要求"].unique()), default=sorted(df["经验要求"].unique()))

    dff = df[df["城市"].isin(cities) & df["岗位类别"].isin(roles) & df["经验要求"].isin(exps)]

    st.subheader(f"筛选后岗位数：{len(dff)} 条")
    if dff.empty:
        st.warning("当前筛选条件下没有数据，请调整筛选器。")
        st.stop()

    col1, col2, col3 = st.columns(3)
    col1.metric("平均月薪", f"{dff['月薪下限(元)'].mean():,.0f} 元")
    col2.metric("月薪中位数", f"{dff['月薪下限(元)'].median():,.0f} 元")
    col3.metric("最高月薪", f"{dff['月薪下限(元)'].max():,.0f} 元")

    left, right = st.columns(2)
    with left:
        st.subheader("各岗位类别平均薪资")
        avg = dff.groupby("岗位类别")["月薪下限(元)"].mean().sort_values()
        fig1 = px.bar(avg, orientation="h", labels={"value": "平均月薪(元)", "岗位类别": ""})
        st.plotly_chart(fig1, width="stretch")
    with right:
        st.subheader("城市 × 岗位 薪资分布")
        fig2 = px.box(dff, x="城市", y="月薪下限(元)", color="岗位类别")
        st.plotly_chart(fig2, width="stretch")

    st.subheader("经验要求与薪资的关系")
    fig3 = px.histogram(dff, x="经验要求", y="月薪下限(元)", color="岗位类别", histfunc="avg",
                        category_orders={"经验要求": ["应届/实习", "1-3年", "3-5年", "5年以上"]})
    st.plotly_chart(fig3, width="stretch")

    st.subheader("岗位明细")
    st.dataframe(dff, width="stretch")

# ================= Tab2 指标监控与异常归因 =================
with tab2:
    st.caption("口径说明：日均值 = 当日新发布岗位月薪下限的平均值；异常判定 = |Z-Score| > 2（Z-Score 基于全期日均值计算）")

    daily = df.groupby("发布日期")["月薪下限(元)"].mean().reset_index()
    daily["Z-Score"] = (daily["月薪下限(元)"] - daily["月薪下限(元)"].mean()) / daily["月薪下限(元)"].std()
    daily["是否异常"] = daily["Z-Score"].abs() > 2

    col1, col2 = st.columns(2)
    col1.metric("监控天数", f"{len(daily)} 天")
    col2.metric("异常天数", f"{int(daily['是否异常'].sum())} 天")

    fig = px.line(daily, x="发布日期", y="月薪下限(元)", markers=True, labels={"月薪下限(元)": "日均薪资(元)"})
    abnormal = daily[daily["是否异常"]]
    if not abnormal.empty:
        fig.add_scatter(x=abnormal["发布日期"], y=abnormal["月薪下限(元)"], mode="markers",
                        marker=dict(size=12, color="red", symbol="x"), name="异常点(|Z|>2)")
    st.plotly_chart(fig, width="stretch")

    st.subheader("异常日波动归因（下钻分析）")
    st.caption("思路：找到异常日后，按城市拆分对比各城市日均薪资与其全期均值的偏离度，定位波动的来源维度")
    if abnormal.empty:
        st.info("当前数据未检测到异常日，可调整数据或阈值演示。")
    else:
        day = abnormal.sort_values("Z-Score").iloc[0]["发布日期"]
        st.markdown(f"**选取消幅最大异常日：{day.date()}**")
        city_avg = df.groupby("城市")["月薪下限(元)"].mean().rename("全期均值")
        day_avg = df[df["发布日期"] == day].groupby("城市")["月薪下限(元)"].mean().rename("当日均值")
        compare = pd.concat([city_avg, day_avg], axis=1).dropna()
        compare["偏离度%"] = ((compare["当日均值"] - compare["全期均值"]) / compare["全期均值"] * 100).round(1)
        compare = compare.sort_values("偏离度%")
        st.dataframe(compare, width="stretch")
        worst = compare["偏离度%"].idxmin()
        st.error(f"归因结论：当日「{worst}」薪资偏离全期均值 {compare.loc[worst, '偏离度%']}%，是主要波动来源，建议进一步核对该城市当日岗位数据口径与来源。")

# ================= Tab3 数据字典与指标口径 =================
with tab3:
    st.subheader("数据字典")
    st.caption("记录每张表、每个字段的业务含义，保证分析口径统一")
    dict_tbl = pd.DataFrame({
        "字段名": ["城市", "岗位类别", "经验要求", "月薪下限(元)", "公司类型", "发布日期"],
        "类型": ["文本"] * 5 + ["日期"],
        "含义": [
            "岗位工作所在城市（8 个主要城市）",
            "岗位所属职能方向（6 类）",
            "岗位要求的工作经验档位（4 档）",
            "岗位公布的月薪下限，单位：元/月",
            "发布岗位的公司规模分类（3 类）",
            "岗位发布的自然日，格式 YYYY-MM-DD",
        ],
        "示例": ["深圳", "数据分析", "1-3年", "11000", "中型公司", "2026-10-01"],
    })
    st.dataframe(dict_tbl, width="stretch")

    st.subheader("指标口径定义")
    kpi_tbl = pd.DataFrame({
        "指标": ["平均月薪", "月薪中位数", "日均薪资", "偏离度%", "异常日"],
        "计算口径": [
            "筛选集内「月薪下限(元)」的算术平均值",
            "筛选集内「月薪下限(元)」的中位数（抗极端值）",
            "按发布日期分组后，「月薪下限(元)」的日平均值",
            "(当日均值 − 全期均值) / 全期均值 × 100%",
            "日均薪资的 Z-Score 绝对值 > 2 的自然日",
        ],
        "用途": ["整体水平参考", "排除极端值后的水平参考", "趋势监控", "定位波动来源维度", "触发波动归因分析"],
    })
    st.dataframe(kpi_tbl, width="stretch")
