"""RetailIQ Anomaly Detection page."""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from ..theme import get_theme, make_chart
from ..components import page_header, kpi_row, empty_state


def render_anomaly(df, profile, mode, selected_target):
    """Render the Anomaly Detection page using existing Isolation Forest backend."""
    from src.ml_analyzer import run_anomaly_detection, reference_label_columns

    t = get_theme(mode)

    page_header(
        "Anomaly Detection",
        "Detect unusual observations using Isolation Forest. Adjust the expected anomaly proportion and run.",
        "red",
        mode,
    )

    usable_numeric = [c for c in df.select_dtypes(include=np.number).columns if df[c].nunique(dropna=True) > 1]
    ref_cols = reference_label_columns(df)

    cards = [
        {"label": "ML Rows", "value": f"{len(df):,}", "accent": "red"},
        {"label": "Numeric Features", "value": f"{len(usable_numeric):,}", "accent": "primary"},
        {"label": "Reference Labels", "value": f"{len(ref_cols):,}", "accent": "orange"},
    ]
    kpi_row(cards, mode)

    # Controls
    st.markdown('<div class="riq-card">', unsafe_allow_html=True)
    st.markdown('<div class="riq-section-header">Configuration</div>', unsafe_allow_html=True)

    contamination = st.slider("Expected anomaly proportion", 0.01, 0.20, 0.05, 0.01, key="ml_contamination")

    exclude = [selected_target] if selected_target and selected_target != "— No target / unsupervised —" else None

    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("Run Anomaly Detection", type="primary", key="run_anomaly"):
        with st.spinner("Running Isolation Forest anomaly detection..."):
            result = run_anomaly_detection(df, contamination, exclude_columns=exclude)

        if not result["ok"]:
            st.warning(result["error"])
            return

        st.success(f"Isolation Forest flagged {result['anomalies']:,} anomalous rows out of {len(df):,} ({result['anomalies']/len(df)*100:.1f}%).")
        st.caption(f"Contamination: {result['contamination']:.2f} · Random seed: {result['random_state']}")

        # Summary cards
        cards = [
            {"label": "Anomalies Detected", "value": f"{result['anomalies']:,}", "accent": "red"},
            {"label": "Normal Rows", "value": f"{len(df) - result['anomalies']:,}", "accent": "green"},
            {"label": "Contamination", "value": f"{result['contamination']:.2f}", "accent": "orange"},
        ]

        # Ground truth evaluation
        if result.get("ground_truth_available"):
            gm = result["ground_truth_metrics"]
            cards.append({"label": "Ground-Truth F1", "value": f"{gm['F1']:.3f}", "accent": "primary"})

            st.markdown("---")
            st.markdown('<div class="riq-section-header">Reference Label Evaluation</div>', unsafe_allow_html=True)
            st.info(f"Reference label column: `{result.get('ground_truth_column', '')}` — excluded from model inputs.")

            gt_metrics = pd.DataFrame([gm])
            st.dataframe(gt_metrics, use_container_width=True, hide_index=True)
        else:
            cards.append({"label": "Ground Truth", "value": "Not available", "accent": "cyan"})

        kpi_row(cards, mode)

        # Distinguish model-detected vs reference labels
        st.markdown("---")
        st.markdown('<div class="riq-section-header">Model-Detected Anomalies</div>', unsafe_allow_html=True)
        st.caption("These are observations flagged by the Isolation Forest model. They are candidates for investigation, not confirmed anomalies.")

        anomaly_data = result["data"]
        st.dataframe(anomaly_data.head(500), use_container_width=True, hide_index=True)

        # Anomaly score distribution
        st.markdown('<div class="riq-section-header">Anomaly Score Distribution</div>', unsafe_allow_html=True)
        fig = px.histogram(anomaly_data, x="Anomaly_Score", color="ML_Anomaly",
                          title="Distribution of Anomaly Scores",
                          color_discrete_map={"Anomaly": t["red"], "Normal": t["green"]})
        st.plotly_chart(make_chart(fig, mode), use_container_width=True)

        if result.get("ground_truth_available"):
            st.markdown("---")
            st.markdown('<div class="riq-section-header">Reference Labels</div>', unsafe_allow_html=True)
            st.caption("These are the known anomaly labels from the dataset, shown for comparison. They were not used as model inputs.")
            ref_col = result.get("ground_truth_column", "")
            if ref_col and ref_col in anomaly_data.columns:
                ref_counts = anomaly_data[ref_col].value_counts().reset_index()
                ref_counts.columns = ["Label", "Count"]
                st.dataframe(ref_counts, use_container_width=True, hide_index=True)
