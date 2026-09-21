"""RetailIQ Relationships page — preserves existing scatter/histogram logic."""

import streamlit as st
import plotly.express as px

from ..theme import get_theme, make_chart
from ..components import page_header, empty_state


def render_relationships(df, profile, mode, metric):
    """Render the Relationships page with scatter plot or histogram fallback."""
    t = get_theme(mode)

    page_header(
        "Relationships",
        "Explore how numeric variables relate to each other using scatter plots and distributions.",
        "cyan",
        mode,
    )

    num_cols = profile["numeric_columns"]
    cat_cols = profile["categorical_columns"]

    if len(num_cols) >= 2:
        # Control card
        st.markdown('<div class="riq-card">', unsafe_allow_html=True)
        st.markdown('<div class="riq-section-header">Controls</div>', unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        with c1:
            x = st.selectbox("X-axis", num_cols, index=0, format_func=lambda v: v.replace("_", " ").title())
        with c2:
            y = st.selectbox("Y-axis", num_cols, index=1, format_func=lambda v: v.replace("_", " ").title())
        with c3:
            color = st.selectbox("Color by", ["None"] + cat_cols, index=0,
                                 format_func=lambda v: "None" if v == "None" else v.replace("_", " ").title())

        st.markdown('</div>', unsafe_allow_html=True)

        cols = [x, y] + ([] if color == "None" else [color])
        temp = df[cols].dropna().copy()

        if temp.empty:
            empty_state("📊", "No rows with valid values for the selected columns.", mode)
            return

        # Chart card
        st.markdown('<div class="riq-card">', unsafe_allow_html=True)
        title = f"{x.replace('_',' ').title()} vs {y.replace('_',' ').title()}"
        st.markdown(f'<div class="riq-section-header">{title}</div>', unsafe_allow_html=True)
        fig = px.scatter(temp, x=x, y=y, color=None if color == "None" else color,
                        hover_data=cols, title=title)
        st.plotly_chart(make_chart(fig, mode, height=450), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    elif metric:
        st.markdown('<div class="riq-card">', unsafe_allow_html=True)
        title = f"Distribution of {metric.replace('_',' ').title()}"
        st.markdown(f'<div class="riq-section-header">{title}</div>', unsafe_allow_html=True)
        fig = px.histogram(df.dropna(subset=[metric]), x=metric, nbins=30, title=title)
        st.plotly_chart(make_chart(fig, mode, height=450), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    else:
        empty_state("📊", "Not enough numeric measures for relationship analysis.", mode)
