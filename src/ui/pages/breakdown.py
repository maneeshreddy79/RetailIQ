"""RetailIQ Breakdown page — preserves existing working logic, improves UI."""

import streamlit as st
import plotly.express as px

from ..theme import get_theme, make_chart
from ..components import page_header, choose_metric, choose_dimension, empty_state


def render_breakdown(df, profile, mode, metric, dimension):
    """Render the Breakdown page with dimension/measure/graph-type controls."""
    t = get_theme(mode)

    page_header(
        "Breakdown Analysis",
        "Compare a numeric measure across categorical dimensions. Choose a dimension, measure, and chart type.",
        "primary",
        mode,
    )

    cat_cols = profile["categorical_columns"]
    num_cols = profile["numeric_columns"]

    breakdown_dims = []
    for c in cat_cols:
        n = df[c].nunique(dropna=True)
        ratio = n / max(len(df), 1)
        if n >= 2 and ratio < 0.8:
            breakdown_dims.append(c)

    if not breakdown_dims:
        empty_state("📊", "A categorical dimension with at least two meaningful categories is required for breakdown analysis.", mode)
        return
    if not num_cols:
        empty_state("📊", "A numeric measure is required for breakdown analysis.", mode)
        return

    default_dim = dimension if dimension in breakdown_dims else breakdown_dims[0]
    default_metric = metric if metric in num_cols else num_cols[0]

    # Control card
    st.markdown('<div class="riq-card">', unsafe_allow_html=True)
    st.markdown('<div class="riq-section-header">Controls</div>', unsafe_allow_html=True)

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
        f"Recommended: {recommended_graph}",
        "Bar Chart",
        "Horizontal Bar Chart",
        "Line Chart",
        "Area Chart",
        "Pie Chart",
        "Donut Chart",
    ]
    with d3:
        graph_choice = st.selectbox("Graph Type", graph_options, key="breakdown_graph_type")

    if graph_choice.startswith("Recommended"):
        graph_type = recommended_graph
    else:
        graph_type = graph_choice

    st.caption(
        f"Recommended graph: **{recommended_graph}** — {recommendation_reason} "
        "You can override the recommendation from the Graph Type dropdown."
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # Aggregation
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
        return

    # Chart card
    st.markdown('<div class="riq-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="riq-section-header">{chart_title}</div>', unsafe_allow_html=True)

    if graph_type == "Bar Chart":
        fig = px.bar(temp.sort_values(selected_metric), x=selected_metric, y=selected_dimension,
                     orientation="h", text_auto=".2s", title=chart_title)
        st.plotly_chart(make_chart(fig, mode, height=420), use_container_width=True)
    elif graph_type == "Horizontal Bar Chart":
        fig = px.bar(temp.sort_values(selected_metric), x=selected_metric, y=selected_dimension,
                     orientation="h", text_auto=".2s", title=chart_title)
        st.plotly_chart(make_chart(fig, mode, height=420), use_container_width=True)
    elif graph_type == "Line Chart":
        fig = px.line(temp, x=selected_dimension, y=selected_metric, markers=True, title=chart_title)
        st.plotly_chart(make_chart(fig, mode, height=420), use_container_width=True)
    elif graph_type == "Area Chart":
        fig = px.area(temp, x=selected_dimension, y=selected_metric, title=chart_title)
        st.plotly_chart(make_chart(fig, mode, height=420), use_container_width=True)
    elif graph_type == "Pie Chart":
        pie_data = temp.head(10)
        fig = px.pie(pie_data, names=selected_dimension, values=selected_metric, title=f"Share of {measure_name}")
        st.plotly_chart(make_chart(fig, mode, height=420), use_container_width=True)
    elif graph_type == "Donut Chart":
        pie_data = temp.head(10)
        fig = px.pie(pie_data, names=selected_dimension, values=selected_metric, hole=.55, title=f"Share of {measure_name}")
        st.plotly_chart(make_chart(fig, mode, height=420), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Aggregation table card
    st.markdown('<div class="riq-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="riq-section-header">Aggregation: {measure_name} by {display_name}</div>', unsafe_allow_html=True)
    st.dataframe(temp, use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)
