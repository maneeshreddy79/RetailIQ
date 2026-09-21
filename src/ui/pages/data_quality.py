"""RetailIQ Data Quality page."""

import streamlit as st
import pandas as pd

from ..theme import get_theme
from ..components import page_header, kpi_row, empty_state


def render_data_quality(df, profile, cleaning_log, raw_df, cleaned_df, mode):
    """Render the Data Quality page with quality cards, quality table, and cleaning log."""
    t = get_theme(mode)

    page_header(
        "Data Quality",
        "Monitor missing values, duplicates, and column-level quality issues. Cleaning rules are applied automatically.",
        "orange",
        mode,
    )

    missing = int(df.isna().sum().sum())
    duplicates = int(df.duplicated().sum())
    quality_pct = max(0, 100 - (missing / max(df.size, 1) * 100))

    cards = [
        {"label": "Overall Quality", "value": f"{quality_pct:.1f}%",
         "accent": "green" if quality_pct >= 90 else "orange" if quality_pct >= 70 else "red"},
        {"label": "Missing Cells", "value": f"{missing:,}", "accent": "orange"},
        {"label": "Duplicate Rows", "value": f"{duplicates:,}", "accent": "red"},
        {"label": "Columns", "value": f"{df.shape[1]:,}", "accent": "cyan"},
    ]
    kpi_row(cards, mode)

    st.markdown("---")

    # Quality table
    st.markdown('<div class="riq-section-header">Column Quality Issues</div>', unsafe_allow_html=True)
    if profile["quality_table"].empty:
        st.success("No major data-quality issues detected in the cleaned dataset.")
    else:
        st.dataframe(profile["quality_table"], use_container_width=True, hide_index=True)

    st.markdown("---")

    # Raw vs cleaned
    if len(raw_df) != len(cleaned_df) or raw_df.shape[1] != cleaned_df.shape[1]:
        st.markdown('<div class="riq-section-header">Raw vs Cleaned</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="riq-card">'
            f'<div style="font-size:0.9rem;color:{t["muted"]};">'
            f'Cleaning changed the dataset from <strong style="color:{t["text"]}">{len(raw_df):,} rows × {raw_df.shape[1]:,} columns</strong> '
            f'to <strong style="color:{t["text"]}">{len(cleaned_df):,} rows × {cleaned_df.shape[1]:,} columns</strong>.'
            f'</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Cleaning log
    st.markdown('<div class="riq-section-header">Cleaning Actions Applied</div>', unsafe_allow_html=True)
    if cleaning_log:
        st.dataframe(pd.DataFrame(cleaning_log), use_container_width=True, hide_index=True)
    else:
        empty_state("✓", "No cleaning actions were needed for this dataset.", mode)
