from pathlib import Path
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px

from src.analyzer import analyze_dataset
from src.cleaner import build_cleaning_plan, clean_dataset
from src.recommender import generate_recommendations
from src.ml_analyzer import detect_target, infer_task, target_candidates, run_supervised, run_clustering, run_anomaly_detection, log_experiment, run_research_benchmark, reference_label_columns
from src.research_suite import run_suite
from src.advanced_ml import run_advanced_predictive, run_forecast, ml_guided_recommendations, generate_natural_language_insights

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

st.title("📊 RetailIQ V1.0")
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


def choose_metric(columns, df=None, target=None):
    """Select a semantically meaningful measure; never use an arbitrary feature as a KPI."""
    priority = ["sales", "revenue", "profit", "amount", "value", "total", "net_sales", "quantity", "demand"]
    lower = {str(c).lower(): c for c in columns}
    for key in priority:
        if key in lower:
            c = lower[key]
            if df is None or df[c].nunique(dropna=True) > 1:
                return c
    # For scientific/feature-only datasets, return no business metric rather than
    # labeling an arbitrary feature as Total X.
    return None


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
metric = choose_metric(num_cols, df=df)
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
    label = metric.replace('_',' ').title()
    k2.metric(f"Total {label}", fmt_num(df[metric].sum()))
    k3.metric(f"Average {label}", fmt_num(df[metric].mean()))
else:
    k2.metric("Numeric Features", f"{len(num_cols):,}")
    k3.metric("Categorical Dimensions", f"{len(clean_profile['categorical_columns']):,}")
k4.metric("Reference Labels", f"{len(reference_label_columns(df)):,}")
missing = int(df.isna().sum().sum())
quality_pct = max(0, 100 - (missing / max(df.size, 1) * 100))
k5.metric("Data Quality", f"{quality_pct:.1f}%")

# ---------- Main dashboard ----------
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["📈 Overview", "📊 Breakdown", "🔎 Relationships", "🧹 Data Quality", "🤖 ML Analysis", "📋 Data", "🔬 Research Evaluation"])

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
            st.info("No semantic business measure was detected for the headline KPI view. Use the Breakdown, Relationships and ML Analysis tabs for feature-level exploration.")

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
    st.markdown("### Breakdown Controls")
    breakdown_dims = []
    for c in cat_cols:
        n = df[c].nunique(dropna=True)
        ratio = n / max(len(df), 1)
        if n >= 2 and ratio < 0.8:
            breakdown_dims.append(c)
    if not breakdown_dims:
        st.info("A categorical dimension with at least two meaningful categories is required for breakdown analysis.")
    elif not num_cols:
        st.info("A numeric measure is required for breakdown analysis.")
    else:
        default_dim = dimension if dimension in breakdown_dims else breakdown_dims[0]
        default_metric = metric if metric in num_cols else num_cols[0]
        d1, d2, d3 = st.columns(3)
        with d1:
            selected_dimension = st.selectbox(
                "Dimension",
                breakdown_dims,
                index=breakdown_dims.index(default_dim),
                format_func=lambda x: x.replace("_", " ").title(),
                key="breakdown_dimension",
            )
        with d2:
            selected_metric = st.selectbox(
                "Measure",
                num_cols,
                index=num_cols.index(default_metric),
                format_func=lambda x: x.replace("_", " ").title(),
                key="breakdown_metric",
            )

        unique_count = int(df[selected_dimension].nunique(dropna=True))
        recommended_graph = "Bar Chart"
        if unique_count <= 6:
            recommendation_reason = "Best default for comparing category values; a donut chart is also available for small category counts."
        else:
            recommendation_reason = "Recommended for comparing multiple categories without relying on area or angle perception."

        graph_options = [
            f"⭐ Recommended: {recommended_graph}",
            "Bar Chart",
            "Horizontal Bar Chart",
            "Line Chart",
            "Area Chart",
            "Pie Chart",
            "Donut Chart",
        ]
        with d3:
            graph_choice = st.selectbox("Graph Type", graph_options, key="breakdown_graph_type")

        if graph_choice.startswith("⭐ Recommended"):
            graph_type = recommended_graph
        else:
            graph_type = graph_choice

        st.caption(
            f"Recommended graph: **{recommended_graph}** — {recommendation_reason} "
            "You can override the recommendation from the Graph Type dropdown."
        )

        temp = (
            df[[selected_dimension, selected_metric]]
            .dropna()
            .groupby(selected_dimension, as_index=False)[selected_metric]
            .sum()
            .sort_values(selected_metric, ascending=False)
            .head(15)
        )
        display_name = selected_dimension.replace("_", " ").title()
        measure_name = selected_metric.replace("_", " ").title()
        chart_title = f"{measure_name} by {display_name}"

        if temp.empty:
            st.warning("No usable rows remain for the selected dimension and measure.")
        elif graph_type == "Bar Chart":
            fig = px.bar(
                temp.sort_values(selected_metric),
                x=selected_metric, y=selected_dimension, orientation="h",
                text_auto=".2s", title=chart_title,
            )
            st.plotly_chart(make_chart(fig), use_container_width=True)
        elif graph_type == "Horizontal Bar Chart":
            fig = px.bar(
                temp.sort_values(selected_metric),
                x=selected_metric, y=selected_dimension, orientation="h",
                text_auto=".2s", title=chart_title,
            )
            st.plotly_chart(make_chart(fig), use_container_width=True)
        elif graph_type == "Line Chart":
            fig = px.line(temp, x=selected_dimension, y=selected_metric, markers=True, title=chart_title)
            st.plotly_chart(make_chart(fig), use_container_width=True)
        elif graph_type == "Area Chart":
            fig = px.area(temp, x=selected_dimension, y=selected_metric, title=chart_title)
            st.plotly_chart(make_chart(fig), use_container_width=True)
        elif graph_type == "Pie Chart":
            pie_data = temp.head(10)
            fig = px.pie(pie_data, names=selected_dimension, values=selected_metric, title=f"Share of {measure_name}")
            st.plotly_chart(make_chart(fig), use_container_width=True)
        elif graph_type == "Donut Chart":
            pie_data = temp.head(10)
            fig = px.pie(pie_data, names=selected_dimension, values=selected_metric, hole=.55, title=f"Share of {measure_name}")
            st.plotly_chart(make_chart(fig), use_container_width=True)

        st.markdown(f"**Aggregation: {measure_name} by {display_name}**")
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
    if len(raw_df) != len(cleaned_df) or raw_df.shape[1] != cleaned_df.shape[1]:
        st.caption(f"Cleaning changed the dataset from {len(raw_df):,} rows × {raw_df.shape[1]:,} columns to {len(cleaned_df):,} rows × {cleaned_df.shape[1]:,} columns.")
    if cleaning_log:
        st.markdown("### Cleaning actions applied")
        st.dataframe(pd.DataFrame(cleaning_log), use_container_width=True, hide_index=True)

with tab5:
    st.markdown("### 🤖 Adaptive Machine Learning")
    st.caption("RetailIQ conservatively routes datasets to supervised or unsupervised analysis. Models are reproducible baselines—not automatic claims of best performance.")

    auto_target = detect_target(df)
    candidates = target_candidates(df)
    usable_numeric = [c for c in df.select_dtypes(include=np.number).columns if df[c].nunique(dropna=True) > 1]
    usable_features = len(clean_profile["numeric_columns"]) + len(clean_profile["categorical_columns"]) + len(clean_profile["date_columns"])

    r1, r2, r3, r4 = st.columns(4)
    r1.metric("ML Rows", f"{len(df):,}")
    r2.metric("Candidate Features", f"{usable_features:,}")
    r3.metric("Numeric Signals", f"{len(usable_numeric):,}")
    r4.metric("Auto Target", str(auto_target) if auto_target else "None detected")

    if auto_target:
        st.success(f"Adaptive routing: **{auto_target}** is a high-confidence target candidate, so supervised learning is available by default.")
    else:
        st.info("Adaptive routing: **No high-confidence target detected.** Unsupervised learning is recommended. You can still choose a target manually if your dataset has one that RetailIQ cannot infer from its name.")

    if not candidates.empty:
        with st.expander("Target suggestions and confidence", expanded=False):
            shown = candidates.copy()
            shown["Confidence"] = (shown["Confidence"] * 100).round(0).astype(int).astype(str) + "%"
            st.dataframe(shown, use_container_width=True, hide_index=True)

    st.markdown("#### 1. Supervised Learning")
    target_options = ["— No target / unsupervised —"] + list(df.columns)
    default_index = target_options.index(auto_target) if auto_target in target_options else 0
    selected_target = st.selectbox("Target column", target_options, index=default_index, key="ml_target")

    if selected_target != "— No target / unsupervised —":
        inferred = infer_task(df[selected_target])
        task_options = ["Auto", "classification", "regression"]
        task_choice = st.selectbox("ML task", task_options, index=0, key="ml_task")
        resolved_task = inferred if task_choice == "Auto" else task_choice
        st.info(f"Detected task: **{inferred}** · Selected task: **{resolved_task}**")

        test_size = st.slider("Test-set size", 0.15, 0.40, 0.20, 0.05, key="ml_test_size")
        run_ml = st.button("🚀 Run ML Benchmark", type="primary", key="run_ml")
        if run_ml:
            with st.spinner("Training baseline models and evaluating the hold-out test set..."):
                ml_result = run_supervised(df, selected_target, resolved_task, test_size=test_size)
            if not ml_result["ok"]:
                st.warning(ml_result["error"])
            else:
                st.success(f"Benchmark completed using {ml_result['train_rows']:,} training rows and {ml_result['test_rows']:,} test rows.")
                st.caption(f"Features used: {ml_result['features_used']} · Automatically removed identifier-like/constant fields: {len(ml_result['dropped_features'])} · Random seed: {ml_result['random_state']}")
                for note in ml_result.get("diagnostics", []):
                    st.warning(note)

                results = ml_result["results"].copy()
                metric_cols = [c for c in results.columns if c not in {"Model", "Error"}]
                for c in metric_cols:
                    results[c] = pd.to_numeric(results[c], errors="coerce")
                st.dataframe(results, use_container_width=True, hide_index=True)

                valid = results.dropna(subset=[c for c in metric_cols if c in results.columns], how="all")
                if not valid.empty:
                    if resolved_task == "classification" and "F1" in valid.columns:
                        best_name = valid.loc[valid["F1"].idxmax(), "Model"]
                        st.metric("Best baseline (weighted F1)", str(best_name))
                    elif resolved_task == "regression" and "RMSE" in valid.columns:
                        best_name = valid.loc[valid["RMSE"].idxmin(), "Model"]
                        st.metric("Best baseline (lowest RMSE)", str(best_name))

                # Research reproducibility: keep a compact experiment record.
                try:
                    log_path = log_experiment(ml_result)
                    st.caption(f"Experiment logged to `{log_path.as_posix()}` for reproducibility.")
                except Exception as exc:
                    st.warning(f"Benchmark completed, but experiment logging failed: {exc}")

                st.markdown("#### Feature importance / influence")
                st.caption("Permutation importance measures how much model performance changes when each original input feature is shuffled. This avoids comparing raw coefficients across differently scaled variables and keeps categorical fields grouped by their original column.")
                model_names = list(ml_result["importances"].keys())
                if model_names:
                    chosen_model = st.selectbox("Model explanation", model_names, key="ml_explain_model")
                    imp = ml_result["importances"][chosen_model]
                    if imp.empty:
                        st.info("Permutation importance could not be computed for this model/dataset.")
                    else:
                        display_imp = imp.copy()
                        display_imp["Importance"] = display_imp["Importance"].round(6)
                        display_imp["Std"] = display_imp["Std"].round(6)
                        st.dataframe(display_imp, use_container_width=True, hide_index=True)
                        fig = px.bar(display_imp.sort_values("Importance"), x="Importance", y="Feature", orientation="h", title=f"Permutation importance — {chosen_model}")
                        st.plotly_chart(make_chart(fig), use_container_width=True)
    else:
        st.info("No supervised target is selected. Continue with the unsupervised analyses below.")

    st.markdown("#### 2. Unsupervised Learning")
    c1, c2 = st.columns(2)
    with c1:
        n_clusters = st.slider("Number of clusters (K-Means)", 2, 8, 3, key="ml_k")
        if st.button("Run K-Means", key="run_kmeans"):
            result = run_clustering(df, n_clusters, exclude_columns=[selected_target] if selected_target != "— No target / unsupervised —" else None)
            if not result["ok"]:
                st.warning(result["error"])
            else:
                st.success(f"K-Means completed. Silhouette score: {result['silhouette']:.3f}")
                sizes = ", ".join(f"Cluster {k}: {v}" for k, v in result["cluster_sizes"].items())
                st.caption(f"Cluster sizes — {sizes} · Random seed: {result['random_state']}")
                st.dataframe(result["assignments"].head(500), use_container_width=True, hide_index=True)
    with c2:
        contamination = st.slider("Expected anomaly proportion", 0.01, 0.20, 0.05, 0.01, key="ml_contamination")
        if st.button("Run Anomaly Detection", key="run_anomaly"):
            result = run_anomaly_detection(df, contamination, exclude_columns=[selected_target] if selected_target != "— No target / unsupervised —" else None)
            if not result["ok"]:
                st.warning(result["error"])
            else:
                st.success(f"Isolation Forest flagged {result['anomalies']:,} anomalous rows out of {len(df):,} ({result['anomalies']/len(df)*100:.1f}%).")
                st.caption(f"Contamination setting: {result['contamination']:.2f} · Random seed: {result['random_state']}")
                st.dataframe(result["data"].head(500), use_container_width=True, hide_index=True)

    st.markdown("#### 3. Advanced Predictive Analytics")
    st.caption("Adds a gradient-boosting baseline to the existing linear/tree/forest models. This is an additional predictive path, not a claim of universal superiority.")
    if selected_target != "— No target / unsupervised —":
        if st.button("Run Advanced Predictive Model", key="run_advanced_predictive"):
            with st.spinner("Training Gradient Boosting and computing validation metrics..."):
                adv = run_advanced_predictive(df, selected_target, resolved_task)
            if not adv["ok"]:
                st.warning(adv["error"])
            else:
                st.success(f"Gradient Boosting completed for {adv['task']} on target `{adv['target']}`.")
                st.dataframe(pd.DataFrame([adv["metrics"]]), use_container_width=True, hide_index=True)
                if not adv["importance"].empty:
                    st.markdown("**Top influential numeric features**")
                    st.dataframe(adv["importance"].head(10), use_container_width=True, hide_index=True)
    else:
        st.info("Select a supervised target above to run the advanced predictive baseline.")

    st.markdown("#### 4. Time-Series Forecasting")
    st.caption("When a date-like column and numeric measure are available, RetailIQ creates lag features and compares Ridge and Gradient Boosting forecasting baselines without requiring Prophet.")
    if date_cols and num_cols:
        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            forecast_date = st.selectbox("Forecast date column", date_cols, key="forecast_date")
        with fc2:
            forecast_target = st.selectbox("Forecast measure", num_cols, index=num_cols.index(metric) if metric in num_cols else 0, key="forecast_target")
        with fc3:
            forecast_horizon = st.slider("Forecast horizon", 3, 30, 7, key="forecast_horizon")
        if st.button("Run Forecasting", key="run_forecast"):
            with st.spinner("Building lag features and evaluating forecasting baselines..."):
                fc = run_forecast(df, forecast_date, forecast_target, forecast_horizon)
            if not fc["ok"]:
                st.warning(fc["error"])
            else:
                st.success(f"Forecast completed using {fc['best_model']} at {fc['frequency']} frequency.")
                st.dataframe(fc["evaluation"].round(4), use_container_width=True, hide_index=True)
                hist = fc["aggregated"][["date", "value"]].tail(60).copy(); hist["Series"] = "Historical"; hist.rename(columns={"value": forecast_target}, inplace=True)
                pred = fc["forecast"][["date", "forecast"]].copy(); pred["Series"] = "Forecast"; pred.rename(columns={"forecast": forecast_target}, inplace=True)
                chart = pd.concat([hist, pred], ignore_index=True)
                fig = px.line(chart, x="date", y=forecast_target, color="Series", markers=True, title=f"Forecast — {forecast_target.replace('_',' ').title()}")
                st.plotly_chart(make_chart(fig), use_container_width=True)
    else:
        st.info("Forecasting requires at least one date-like column and one numeric measure.")

    st.markdown("#### 5. ML-Guided Recommendations")
    st.caption("Recommendations are derived from measured model, anomaly and forecast signals; they are transparent rule-based outputs rather than unexplained model decisions.")
    rec_ml_target = selected_target if selected_target != "— No target / unsupervised —" else None
    rec_task = resolved_task if rec_ml_target else None
    if st.button("Generate ML-Guided Recommendations", key="run_ml_recs"):
        adv_for_rec = run_advanced_predictive(df, rec_ml_target, rec_task) if rec_ml_target else {}
        anomaly_for_rec = run_anomaly_detection(df, 0.05, exclude_columns=[rec_ml_target] if rec_ml_target else None)
        forecast_for_rec = run_forecast(df, date_cols[0], metric, 7) if date_cols and metric else {}
        baseline_for_rec = run_supervised(df, rec_ml_target, rec_task, test_size=0.20) if rec_ml_target else {}
        recs_ml = ml_guided_recommendations(adv_for_rec, baseline_for_rec, anomaly_for_rec, forecast_for_rec)
        if recs_ml:
            st.dataframe(pd.DataFrame(recs_ml), use_container_width=True, hide_index=True)
        else:
            st.info("No ML-guided recommendations could be generated from the current dataset.")

    st.markdown("#### 6. Natural-Language Insight Generation")
    st.caption("RetailIQ generates deterministic, data-grounded narrative insights from the observed dataset. This does not require an external LLM and does not invent unsupported facts.")
    if st.button("Generate Automated Insights", key="run_nl_insights"):
        anomaly_for_nl = run_anomaly_detection(df, 0.05, exclude_columns=[selected_target] if selected_target != "— No target / unsupervised —" else None)
        forecast_for_nl = run_forecast(df, date_cols[0], metric, 7) if date_cols and metric else {}
        insights = generate_natural_language_insights(df, clean_profile, anomaly_for_nl, forecast_for_nl)
        if insights:
            for i, insight in enumerate(insights, 1):
                st.write(f"**{i}.** {insight}")
        else:
            st.info("No sufficiently strong signals were available for automated narrative generation.")

    st.markdown("#### ML interpretation")
    if selected_target != "— No target / unsupervised —":
        st.write(f"This dataset supports supervised {resolved_task} analysis on `{selected_target}`. Anomaly detection excludes the selected target from model inputs. Forecasting is available only when a date-like field and numeric measure are present.")
    elif date_cols and num_cols:
        st.write(f"This dataset supports temporal analysis using `{date_cols[0]}` and its numeric measures. No supervised target was selected; forecasting uses chronological evaluation.")
    elif len(num_cols) >= 2:
        st.write(f"This dataset supports unsupervised clustering and anomaly analysis across {len(num_cols)} varying numeric features. Reference labels, when present, are excluded from model inputs.")
    else:
        st.write("The detected structure supports descriptive analysis and only those ML paths for which the dataset provides sufficient evidence.")

with tab7:
    st.markdown("### 🔬 Research Evaluation")
    st.caption("Reproducible evaluation layer for the research paper. The Expanded Research Suite below is the primary V1.0 evidence source; the legacy 4-dataset benchmark is retained only for diagnostics.")
    st.markdown("#### 1. Automatic routing evaluation")
    st.write("RetailIQ V1.0 is evaluated on 12 datasets spanning classification, regression, unsupervised analysis, anomaly detection and forecasting. The Expanded Research Suite below is the primary source for paper results.")
    folds = st.selectbox("Cross-validation folds", [5, 10], index=0, key="research_folds")
    if st.button("🚀 Run Legacy 4-Dataset Benchmark (Diagnostic)", type="secondary", key="run_research"):
        with st.spinner("Running routing, cross-validation, clustering, and statistical evaluation..."):
            research = run_research_benchmark("results", folds=folds)
        if not research["ok"]:
            st.error("Research benchmark failed.")
        else:
            routing = research["routing"]["results"].copy()
            st.success(f"Research benchmark completed. Automatic routing accuracy: {research['routing']['accuracy']*100:.1f}%")
            st.dataframe(routing, use_container_width=True, hide_index=True)
            st.markdown("#### 2. Leakage-safe supervised cross-validation")
            cv = research["cv_summary"].copy()
            if cv.empty:
                st.warning("No supervised CV results were produced.")
            else:
                st.dataframe(cv, use_container_width=True, hide_index=True)
                st.caption("Preprocessing is fitted separately within each fold. Means and standard deviations are reported across folds.")
            st.markdown("#### 3. Unsupervised evaluation")
            cl = research["clustering"].get("results", pd.DataFrame())
            if not cl.empty:
                st.dataframe(cl, use_container_width=True, hide_index=True)
                fig = px.line(cl, x="K", y="Silhouette", markers=True, title="K-Means silhouette score by K")
                st.plotly_chart(make_chart(fig), use_container_width=True)
            st.markdown("#### 4. Statistical comparison")
            stats = research["statistics"]
            if stats.empty:
                st.info("No statistical comparison was generated for this run.")
            else:
                st.dataframe(stats, use_container_width=True, hide_index=True)
    st.markdown("#### 5. Expanded research dataset suite")
    st.caption("Primary V1.0 evidence: 5×5 repeated cross-validation for general supervised benchmarks, unsupervised clustering metrics, ground-truth anomaly evaluation, temporal forecasting evaluation, and multiple-comparison-corrected statistical tests. Public and synthetic datasets are labeled separately.")
    if st.button("🧪 Run Expanded Research Suite", key="run_expanded_suite"):
        with st.spinner("Running expanded dataset suite (5 repeats × 5 folds)..."):
            expanded = run_suite(root="research_datasets", results_dir="results/research_suite", repeats=5, folds=5)
        st.success(f"Expanded suite completed across {int(expanded['run_summary'].iloc[0]['datasets'])} datasets. Routing accuracy: {expanded['run_summary'].iloc[0]['routing_accuracy']*100:.1f}%.")
        st.markdown("**Routing evaluation**")
        st.dataframe(expanded["routing"], use_container_width=True, hide_index=True)
        st.markdown("**Supervised cross-validation summary**")
        st.dataframe(expanded["summary"], use_container_width=True, hide_index=True)
        st.markdown("**Unsupervised metrics**")
        st.dataframe(expanded["clustering"], use_container_width=True, hide_index=True)
        st.markdown("**Statistical tests**")
        st.dataframe(expanded["statistics"], use_container_width=True, hide_index=True)
        st.info("The expanded suite is the preferred source for the research paper; inspect the generated CSV artifacts before reporting any number.")

    st.markdown("#### 6. Saved V1.0 evaluation artifacts")
    st.code("results/research_suite/expanded_run_summary.csv\nresults/research_suite/expanded_routing.csv\nresults/research_suite/expanded_cv_summary.csv\nresults/research_suite/expanded_cv_fold_results.csv\nresults/research_suite/expanded_clustering_results.csv\nresults/research_suite/expanded_anomaly_results.csv\nresults/research_suite/expanded_forecasting_results.csv\nresults/research_suite/expanded_statistical_tests.csv\nresults/research_suite/expanded_advanced_predictive_results.csv")
    st.info("These V1.0 evaluation artifacts are the primary saved outputs for the expanded 12-dataset benchmark and its model, clustering, anomaly, forecasting, and statistical results.")

with tab6:
    st.markdown("### Filtered Dataset")
    st.dataframe(df.head(500), use_container_width=True, hide_index=True)
    st.download_button(
        "⬇️ Download Filtered CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name=f"RetailIQ_filtered_{Path(uploaded.name).stem}.csv",
        mime="text/csv",
    )

# ---------- Recommendations ----------
rec_context = {
    "target": selected_target if "selected_target" in locals() and selected_target != "— No target / unsupervised —" else None,
    "task": resolved_task if "resolved_task" in locals() and selected_target != "— No target / unsupervised —" else None,
}
recommendations = generate_recommendations(clean_profile, cleaned_df, rec_context)
st.markdown("## Recommended Analytics")
for rec in recommendations[:6]:
    with st.container(border=True):
        st.markdown(f"### {rec['priority']} — {rec['title']}")
        st.write(rec["description"])
        st.caption(f"Why: {rec['why']} · Business value: {rec['business_value']}")

st.caption("RetailIQ V1.0 — adaptive analytics, ML/AI extensions, research evaluation and reproducible experiment suite.")
