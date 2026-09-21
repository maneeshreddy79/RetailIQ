"""RetailIQ Data page — professional data-grid experience."""

import streamlit as st
import pandas as pd
from pathlib import Path

from ..theme import get_theme
from ..components import page_header, kpi_row


def render_data(df, profile, mode, uploaded_name):
    """Render the Data page with dataset summary, table preview, and CSV download."""
    t = get_theme(mode)

    page_header(
        "Data Explorer",
        "Browse, filter, and export your dataset. All filtering happens in the sidebar.",
        "primary",
        mode,
    )

    # Summary KPIs
    cards = [
        {"label": "Total Rows", "value": f"{len(df):,}", "accent": "cyan"},
        {"label": "Total Columns", "value": f"{df.shape[1]:,}", "accent": "primary"},
        {"label": "Numeric Columns", "value": f"{len(profile['numeric_columns']):,}", "accent": "orange"},
        {"label": "Categorical Columns", "value": f"{len(profile['categorical_columns']):,}", "accent": "green"},
        {"label": "Date Columns", "value": f"{len(profile['date_columns']):,}", "accent": "pink"},
    ]
    kpi_row(cards, mode)

    st.markdown("---")

    # Column profile table
    st.markdown('<div class="riq-section-header">Column Profile</div>', unsafe_allow_html=True)
    st.dataframe(profile["column_profile"], use_container_width=True, hide_index=True)

    st.markdown("---")

    # Data preview
    st.markdown('<div class="riq-section-header">Data Preview (first 500 rows)</div>', unsafe_allow_html=True)
    st.dataframe(df.head(500), use_container_width=True, hide_index=True)

    st.markdown("---")

    # Download
    st.markdown('<div class="riq-section-header">Export</div>', unsafe_allow_html=True)
    csv_data = df.to_csv(index=False).encode("utf-8")
    file_stem = Path(uploaded_name).stem if uploaded_name else "dataset"
    st.download_button(
        "Download Filtered CSV",
        data=csv_data,
        file_name=f"RetailIQ_filtered_{file_stem}.csv",
        mime="text/csv",
        type="primary",
    )
