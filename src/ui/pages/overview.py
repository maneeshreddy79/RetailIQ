"""RetailIQ Dashboard / Overview page."""

import streamlit as st
import pandas as pd
import plotly.express as px

from ..theme import make_chart
from ..components import page_header, kpi_row, fmt_num, choose_metric, choose_dimension, card, insight_card


def render_dashboard(df, profile, mode, metric, dimension, date_cols, num_cols, cat_cols, second_metric):
    """Render the executive dashboard."""
    t = __import__("src.ui.theme", fromlist=["get_theme"]).get_theme(mode)

    page_header(
        "Executive Dashboard",
        "Real-time overview of your dataset with key metrics, trends, and business insights.",
        "cyan",
        mode,
    )

    if len(df) == 0:
        st.warning("No rows match the current filters. Adjust the filters in the sidebar.")
        return

    # KPI Row
    from src.ml_analyzer import reference_label_columns
    ref_labels = reference_label_columns(df)
    missing = int(df.isna().sum().sum())
    quality_pct = max(0, 100 - (missing / max(df.size, 1) * 100))

    cards = [
        {"label": "Rows", "value": f"{len(df):,}", "accent": "cyan"},
    ]
    if metric:
        label = metric.replace("_", " ").title()
        cards.append({"label": f"Total {label}", "value": fmt_num(df[metric].sum()), "accent": "primary"})
        cards.append({"label": f"Average {label}", "value": fmt_num(df[metric].mean()), "accent": "primary"})
    else:
        cards.append({"label": "Numeric Features", "value": f"{len(num_cols):,}", "accent": "primary"})
        cards.append({"label": "Categorical Dimensions", "value": f"{len(cat_cols):,}", "accent": "primary"})
    cards.append({"label": "Reference Labels", "value": f"{len(ref_labels):,}", "accent": "orange"})
    cards.append({"label": "Data Quality", "value": f"{quality_pct:.1f}%", "accent": "green" if quality_pct >= 90 else "orange" if quality_pct >= 70 else "red"})

    kpi_row(cards, mode)

    # Main content
    left, right = st.columns([1.65, 1])

    with left:
        st.markdown('<div class="riq-section-header">Trend Visualization</div>', unsafe_allow_html=True)
        if date_cols and metric:
            dc = date_cols[0]
            temp = df[[dc, metric]].dropna().copy()
            temp[dc] = pd.to_datetime(temp[dc], errors="coerce")
            temp = temp.dropna(subset=[dc])
            if not temp.empty:
                span_days = max((temp[dc].max() - temp[dc].min()).days, 1)
                freq = "D" if span_days <= 60 else ("W" if span_days <= 365 else "ME")
                temp = temp.set_index(dc)[metric].resample(freq).sum().reset_index()
                fig = px.line(temp, x=dc, y=metric, markers=span_days <= 120,
                              title=f"{metric.replace('_',' ').title()} Trend")
                st.plotly_chart(make_chart(fig, mode), use_container_width=True)
            else:
                st.info("A usable date and numeric measure were not available for the trend view.")
        elif metric and dimension:
            temp = df[[dimension, metric]].dropna().groupby(dimension, as_index=False)[metric].sum().nlargest(15, metric)
            fig = px.bar(temp.sort_values(metric), x=metric, y=dimension, orientation="h",
                        title=f"Top {dimension.replace('_',' ').title()} by {metric.replace('_',' ').title()}")
            st.plotly_chart(make_chart(fig, mode), use_container_width=True)
        else:
            st.info("No semantic business measure was detected. Use Breakdown, Relationships and ML Studio for feature-level exploration.")

    with right:
        st.markdown('<div class="riq-section-header">Business Snapshot</div>', unsafe_allow_html=True)
        if metric:
            top_value = float(df[metric].max())
            median_value = float(df[metric].median())
            st.markdown(
                f'<div class="riq-card"><div class="small-muted" style="color:{t["muted"]};font-size:0.82rem;">Highest observed {metric.replace("_"," ").title()}</div>'
                f'<div style="font-size:1.8rem;font-weight:700;color:{t["text"]};margin-top:4px;">{fmt_num(top_value)}</div></div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div class="riq-card"><div class="small-muted" style="color:{t["muted"]};font-size:0.82rem;">Median {metric.replace("_"," ").title()}</div>'
                f'<div style="font-size:1.8rem;font-weight:700;color:{t["text"]};margin-top:4px;">{fmt_num(median_value)}</div></div>',
                unsafe_allow_html=True,
            )
        if dimension and metric:
            temp = df[[dimension, metric]].dropna().groupby(dimension, as_index=False)[metric].sum().sort_values(metric, ascending=False).head(5)
            st.markdown(f'<div class="riq-section-header">Top Segments</div>', unsafe_allow_html=True)
            for _, row in temp.iterrows():
                st.markdown(
                    f'<div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid {t["border"]};">'
                    f'<span style="font-weight:500;color:{t["text"]};">{row[dimension]}</span>'
                    f'<span style="color:{t["cyan"]};font-weight:600;">{fmt_num(row[metric])}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    # Recommendation preview
    st.markdown("---")
    st.markdown('<div class="riq-section-header">Recommendation Preview</div>', unsafe_allow_html=True)
    recommendations = st.session_state.get("recommendations", [])
    if recommendations:
        for rec in recommendations[:3]:
            card_body = f'<div style="font-size:0.9rem;color:{t["muted"]};">{rec.get("description","")}</div>'
            card(rec.get("title", ""), card_body, mode, glass=False)
        st.markdown(
            f'<div style="text-align:center;padding:8px;">'
            f'<span style="color:{t["muted"]};font-size:0.85rem;">See the Recommendations page for full details and routing</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
