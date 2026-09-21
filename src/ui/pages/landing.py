"""RetailIQ landing / upload experience — shown when no dataset is loaded."""

import streamlit as st

from .theme import logo_svg, get_theme


def render_landing(mode: str):
    """Render the polished landing page with upload zone."""
    t = get_theme(mode)
    logo = logo_svg(64, 64)

    st.markdown(
        f"""
        <div style="text-align:center;padding:40px 0 32px 0;" class="riq-fade-in">
            <div style="display:flex;justify-content:center;margin-bottom:20px;">{logo}</div>
            <h1 style="font-size:2.5rem;font-weight:800;letter-spacing:-0.03em;color:{t['text']};margin-bottom:8px;">
                RetailIQ
            </h1>
            <p style="font-size:1.1rem;color:{t['muted']};max-width:560px;margin:0 auto;line-height:1.6;">
                Adaptive data analytics & business insight system. Upload your dataset to instantly
                get executive dashboards, breakdown analysis, ML modeling, and actionable recommendations.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Feature highlights
    col1, col2, col3, col4 = st.columns(4)
    features = [
        ("Ingest", "CSV, XLSX, XLS", "primary"),
        ("Profile", "Auto-detect types", "cyan"),
        ("Analyze", "ML + statistics", "orange"),
        ("Explore", "Interactive charts", "green"),
    ]
    for col, (title, desc, accent) in zip([col1, col2, col3, col4], features):
        color = t[accent]
        with col:
            st.markdown(
                f'<div class="riq-card" style="text-align:center;">'
                f'<div style="font-size:1.2rem;font-weight:700;color:{color};">{title}</div>'
                f'<div style="font-size:0.82rem;color:{t["muted"]};margin-top:4px;">{desc}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown("")

    # Upload zone
    st.markdown(
        f"""
        <div class="riq-upload-zone">
            <div style="font-size:2.5rem;opacity:0.4;margin-bottom:12px;">📁</div>
            <div style="font-size:1.15rem;font-weight:600;color:{t['text']};margin-bottom:6px;">
                Upload your dataset to begin
            </div>
            <div style="font-size:0.88rem;color:{t['muted']};">
                Supported formats: CSV, XLSX, XLS — use the file uploader in the sidebar
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f'<div style="text-align:center;padding:16px 0;">'
        f'<span class="riq-badge riq-badge-primary">CSV</span> &nbsp; '
        f'<span class="riq-badge riq-badge-cyan">XLSX</span> &nbsp; '
        f'<span class="riq-badge riq-badge-orange">XLS</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.markdown(
        f'<div style="text-align:center;color:{t["muted"]};font-size:0.82rem;">'
        f'RetailIQ V1.0 — Adaptive Analytics & Business Insight System'
        f'</div>',
        unsafe_allow_html=True,
    )
