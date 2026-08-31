from pathlib import Path
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px

from src.analyzer import analyze_dataset
from src.cleaner import build_cleaning_plan, clean_dataset
from src.recommender import generate_recommendations

st.set_page_config(page_title="RetailIQ", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

# ---------- Styling ----------
st.markdown("""
<style>
.block-container {padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1500px;}
[data-testid="stMetric"] {background: #171a21; border: 1px solid #2a2f3a; padding: 14px 16px; border-radius: 12px;}
[data-testid="stMetricLabel"] {color: #9ca3af;}
[data-testid="stMetricValue"] {font-size: 1.55rem;}
.dashboard-card {background:#171a21;border:1px solid #2a2f3a;border-radius:14px;padding:16px 18px;margin-bottom:12px;}
.small-muted {color:#9ca3af;font-size:.86rem;}
.kpi-good {color:#22c55e;font-weight:700;}
.kpi-warn {color:#f59e0b;font-weight:700;}
</style>
""", unsafe_allow_html=True)

st.title("📊 RetailIQ")
st.caption("Adaptive Data Analytics & Business Insight System · Power BI–style interactive analytics")

# ---------- Helpers ----------
def fmt_num(x):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "—"
    x = float(x)
    ax = abs(x)
    if ax >= 1_000_000_000:
        return f"{x/1_000_000_000:.2f}B"
    if ax >= 1_000_000:
        return f"{x/1_000_000:.2f}M"
    if ax >= 1_000:
        return f"{x/1_000:.1f}K"
    return f"{x:,.0f}" if x.is_integer() else f"{x:,.2f}"


def choose_metric(columns):
    priority = ["sales", "revenue", "profit", "amount", "value", "total", "net_sales", "quantity"]
    lower = {str(c).lower(): c for c in columns}
    for key in priority:
        if key in lower:
            return lower[key]
    return columns[0] if columns else None


def choose_dimension(df, exclude=None):
    exclude = set(exclude or [])
    cats = [c for c in df.select_dtypes(include=["object", "string", "category", "bool"]).columns if c not in exclude]
    # Prefer dimensions with enough variation but not almost-unique IDs.
    ranked = []
    for c in cats:
        n = df[c].nunique(dropna=True)
        ratio = n / max(len(df), 1)
        if n >= 2 and ratio < 0.8:
            ranked.append((0 if n <= 30 else 1, n, c))
    if ranked:
        ranked.sort()
        return ranked[0][2]
    return cats[0] if cats else None


def make_chart(fig):
    fig.update_layout(
        template="plotly_dark", height=380, margin=dict(l=10, r=10, t=55, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        legend_title_text=""
    )
    return fig

# ---------- Upload ----------
with st.sidebar:
    st.header("RetailIQ Controls")
    uploaded = st.file_uploader("Upload CSV / Excel", type=["csv", "xlsx", "xls"])
    st.divider()
    st.caption("The dashboard is generated from the uploaded data. Original files are never overwritten.")

if uploaded is None:
    st.info("👆 Upload a CSV or Excel dataset to build the dashboard.")
    a, b, c, d = st.columns(4)
    a.metric("01", "Ingest")
    b.metric("02", "Profile")
    c.metric("03", "Analyze")
    d.metric("04", "Explore")
    st.markdown("### What this version adds")
    st.write("Power BI–style KPI cards, slicer-like filters, trend analysis, category rankings, metric relationships, data-quality monitoring, and an exportable filtered dataset.")
    st.stop()

try:
    if uploaded.name.lower().endswith(".csv"):
        raw_df = pd.read_csv(uploaded)
    else:
        raw_df = pd.read_excel(uploaded)
except Exception as exc:
    st.error(f"Could not read the dataset: {exc}")
    st.stop()

if raw_df.empty:
    st.error("The uploaded dataset is empty.")
    st.stop()

profile = analyze_dataset(raw_df)
plan = build_cleaning_plan(raw_df)
cleaned_df, cleaning_log = clean_dataset(raw_df, plan)

# Re-profile AFTER cleaning so visualizations use actual cleaned column names.
clean_profile = analyze_dataset(cleaned_df)
recommendations = generate_recommendations(clean_profile, cleaned_df)

# ---------- Sidebar filters ----------
df = cleaned_df.copy()
with st.sidebar:
    st.success(f"Loaded {uploaded.name}")
    date_cols = clean_profile["date_columns"]
    num_cols = clean_profile["numeric_columns"]
    cat_cols = clean_profile["categorical_columns"]

    st.subheader("Dashboard Filters")
    selected = {}
    for col in cat_cols[:4]:
        vals = sorted(df[col].dropna().astype(str).unique().tolist())
        if 1 < len(vals) <= 100:
            selected[col] = st.multiselect(col.replace("_", " ").title(), vals, default=vals)

    if date_cols:
        dc = date_cols[0]
        df[dc] = pd.to_datetime(df[dc], errors="coerce")
        valid_dates = df[dc].dropna()
        if not valid_dates.empty:
            start, end = valid_dates.min().date(), valid_dates.max().date()
            date_range = st.date_input("Date range", value=(start, end), min_value=start, max_value=end)
            if isinstance(date_range, tuple) and len(date_range) == 2:
                df = df[df[dc].dt.date.between(date_range[0], date_range[1])]

    if selected:
        for col, vals in selected.items():
            if vals:
                df = df[df[col].astype(str).isin(vals)]

    st.divider()
    st.caption(f"Showing {len(df):,} of {len(cleaned_df):,} cleaned rows")

# ---------- Semantic selections ----------
metric = choose_metric(num_cols)
dimension = choose_dimension(df)
other_num = [c for c in num_cols if c != metric]
second_metric = other_num[0] if other_num else None

# ---------- Header KPIs ----------
st.markdown("## Executive Overview")
if len(df) == 0:
    st.warning("No rows match the current filters. Adjust the filters in the sidebar.")
    st.stop()

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Rows", f"{len(df):,}")
if metric:
    k2.metric(f"Total {metric.replace('_',' ').title()}", fmt_num(df[metric].sum()))
    k3.metric(f"Average {metric.replace('_',' ').title()}", fmt_num(df[metric].mean()))
else:
    k2.metric("Numeric Measures", f"{len(num_cols):,}")
    k3.metric("Average", "—")
k4.metric("Dimensions", f"{len(clean_profile['categorical_columns']):,}")
missing = int(df.isna().sum().sum())
quality_pct = max(0, 100 - (missing / max(df.size, 1) * 100))
k5.metric("Data Quality", f"{quality_pct:.1f}%")

# ---------- Main dashboard ----------
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 Overview", "📊 Breakdown", "🔎 Relationships", "🧹 Data Quality", "📋 Data"])

with tab1:
    left, right = st.columns([1.65, 1])
    with left:
        if date_cols and metric:
            dc = date_cols[0]
            temp = df[[dc, metric]].dropna().copy()
            temp[dc] = pd.to_datetime(temp[dc], errors="coerce")
            temp = temp.dropna(subset=[dc])
            if not temp.empty:
                # Adaptive granularity keeps charts readable.
                span_days = max((temp[dc].max() - temp[dc].min()).days, 1)
                freq = "D" if span_days <= 60 else ("W" if span_days <= 365 else "ME")
                temp = temp.set_index(dc)[metric].resample(freq).sum().reset_index()
                fig = px.line(temp, x=dc, y=metric, markers=span_days <= 120, title=f"{metric.replace('_',' ').title()} Trend")
                st.plotly_chart(make_chart(fig), use_container_width=True)
            else:
                st.info("A usable date and numeric measure were not available for the trend view.")
        elif metric and dimension:
            temp = df[[dimension, metric]].dropna().groupby(dimension, as_index=False)[metric].sum().nlargest(15, metric)
            fig = px.bar(temp.sort_values(metric), x=metric, y=dimension, orientation="h", title=f"Top {dimension.replace('_',' ').title()} by {metric.replace('_',' ').title()}")
            st.plotly_chart(make_chart(fig), use_container_width=True)
        else:
            st.info("Upload data containing at least one numeric measure to unlock KPI visualizations.")

    with right:
        st.markdown("### Business Snapshot")
        if metric:
            top_value = float(df[metric].max())
            median_value = float(df[metric].median())
            st.markdown(f"<div class='dashboard-card'><div class='small-muted'>Highest observed {metric}</div><h2>{fmt_num(top_value)}</h2></div>", unsafe_allow_html=True)
            st.markdown(f"<div class='dashboard-card'><div class='small-muted'>Median {metric}</div><h2>{fmt_num(median_value)}</h2></div>", unsafe_allow_html=True)
        if dimension and metric:
            temp = df[[dimension, metric]].dropna().groupby(dimension, as_index=False)[metric].sum().sort_values(metric, ascending=False).head(5)
            st.markdown("**Top segments**")
            for _, row in temp.iterrows():
                st.write(f"**{row[dimension]}** — {fmt_num(row[metric])}")

with tab2:
    if not (dimension and metric):
        st.info("A categorical dimension and numeric measure are required for breakdown analysis.")
    else:
        c1, c2 = st.columns(2)
        temp = df[[dimension, metric]].dropna().groupby(dimension, as_index=False)[metric].sum().sort_values(metric, ascending=False).head(15)
        with c1:
            fig = px.bar(temp.sort_values(metric), x=metric, y=dimension, orientation="h", text_auto=".2s", title=f"Top {dimension.replace('_',' ').title()}")
            st.plotly_chart(make_chart(fig), use_container_width=True)
        with c2:
            pie_data = temp.head(8)
            fig = px.pie(pie_data, names=dimension, values=metric, hole=.55, title=f"Share of {metric.replace('_',' ').title()}")
            st.plotly_chart(make_chart(fig), use_container_width=True)
        st.dataframe(temp, use_container_width=True, hide_index=True)

with tab3:
    if len(num_cols) >= 2:
        x = st.selectbox("X-axis", num_cols, index=0)
        y = st.selectbox("Y-axis", num_cols, index=1)
        color = st.selectbox("Color by", ["None"] + cat_cols, index=1 if cat_cols else 0)
        cols = [x, y] + ([] if color == "None" else [color])
        temp = df[cols].dropna().copy()
        fig = px.scatter(temp, x=x, y=y, color=None if color == "None" else color, hover_data=cols, title=f"{x.replace('_',' ').title()} vs {y.replace('_',' ').title()}")
        st.plotly_chart(make_chart(fig), use_container_width=True)
    elif metric:
        fig = px.histogram(df.dropna(subset=[metric]), x=metric, nbins=30, title=f"Distribution of {metric.replace('_',' ').title()}")
        st.plotly_chart(make_chart(fig), use_container_width=True)
    else:
        st.info("Not enough numeric measures for relationship analysis.")

with tab4:
    q1, q2, q3 = st.columns(3)
    q1.metric("Missing cells", f"{missing:,}")
    q2.metric("Duplicate rows", f"{int(df.duplicated().sum()):,}")
    q3.metric("Columns", f"{df.shape[1]:,}")
    if clean_profile["quality_table"].empty:
        st.success("No major data-quality issues detected in the cleaned dataset.")
    else:
        st.dataframe(clean_profile["quality_table"], use_container_width=True, hide_index=True)
    if cleaning_log:
        st.markdown("### Cleaning actions applied")
        st.dataframe(pd.DataFrame(cleaning_log), use_container_width=True, hide_index=True)

with tab5:
    st.markdown("### Filtered Dataset")
    st.dataframe(df.head(500), use_container_width=True, hide_index=True)
    st.download_button(
        "⬇️ Download Filtered CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name=f"RetailIQ_filtered_{Path(uploaded.name).stem}.csv",
        mime="text/csv",
    )

# ---------- Recommendations ----------
st.markdown("## Recommended Analytics")
for rec in recommendations[:4]:
    with st.container(border=True):
        st.markdown(f"### {rec['priority']} {rec['title']}")
        st.write(rec["description"])
        st.caption(f"Why: {rec['why']} · Business value: {rec['business_value']}")

st.caption(f"RetailIQ V0.5 — adaptive profiling, conservative cleaning, Power BI–style dashboarding, recommendations and export.")
