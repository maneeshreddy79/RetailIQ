"""RetailIQ Clustering page."""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from ..theme import get_theme, make_chart
from ..components import page_header, kpi_row, empty_state


def render_clustering(df, profile, mode, selected_target):
    """Render the Clustering page using existing K-Means backend."""
    from src.ml_analyzer import run_clustering, evaluate_clustering_k_range

    t = get_theme(mode)

    page_header(
        "Clustering",
        "Discover natural groupings in your data using K-Means clustering. Configure the number of clusters and run.",
        "pink",
        mode,
    )

    usable_numeric = [c for c in df.select_dtypes(include=np.number).columns if df[c].nunique(dropna=True) > 1]

    cards = [
        {"label": "ML Rows", "value": f"{len(df):,}", "accent": "pink"},
        {"label": "Numeric Features", "value": f"{len(usable_numeric):,}", "accent": "primary"},
    ]
    kpi_row(cards, mode)

    # Controls
    st.markdown('<div class="riq-card">', unsafe_allow_html=True)
    st.markdown('<div class="riq-section-header">Configuration</div>', unsafe_allow_html=True)

    n_clusters = st.slider("Number of clusters (K)", 2, 8, 3, key="ml_k")

    exclude = [selected_target] if selected_target and selected_target != "— No target / unsupervised —" else None

    col1, col2 = st.columns(2)
    with col1:
        run_btn = st.button("Run K-Means", type="primary", key="run_kmeans")
    with col2:
        eval_btn = st.button("Evaluate K Range", key="eval_k_range")

    st.markdown('</div>', unsafe_allow_html=True)

    if run_btn:
        with st.spinner("Running K-Means clustering..."):
            result = run_clustering(df, n_clusters, exclude_columns=exclude)

        if not result["ok"]:
            st.warning(result["error"])
            return

        st.success(f"K-Means completed. Silhouette score: {result['silhouette']:.3f}")
        sizes = ", ".join(f"Cluster {k}: {v}" for k, v in result["cluster_sizes"].items())
        st.caption(f"Cluster sizes — {sizes} · Random seed: {result['random_state']}")

        # Cluster sizes visualization
        st.markdown('<div class="riq-section-header">Cluster Sizes</div>', unsafe_allow_html=True)
        sizes_df = pd.DataFrame(list(result["cluster_sizes"].items()), columns=["Cluster", "Count"])
        fig = px.bar(sizes_df, x="Cluster", y="Count", title="Cluster Size Distribution")
        st.plotly_chart(make_chart(fig, mode), use_container_width=True)

        # Assignments table
        st.markdown('<div class="riq-section-header">Cluster Assignments</div>', unsafe_allow_html=True)
        st.dataframe(result["assignments"].head(500), use_container_width=True, hide_index=True)

    if eval_btn:
        with st.spinner("Evaluating cluster quality across K values..."):
            eval_result = evaluate_clustering_k_range(df)

        if not eval_result["ok"]:
            st.warning(eval_result["error"])
            return

        st.markdown('<div class="riq-section-header">Silhouette Score by K</div>', unsafe_allow_html=True)
        st.dataframe(eval_result["results"], use_container_width=True, hide_index=True)
        fig = px.line(eval_result["results"], x="K", y="Silhouette", markers=True,
                      title="K-Means Silhouette Score by K")
        st.plotly_chart(make_chart(fig, mode), use_container_width=True)
