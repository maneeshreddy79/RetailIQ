"""RetailIQ Research Evaluation page."""

import streamlit as st
import pandas as pd
import plotly.express as px

from ..theme import get_theme, make_chart
from ..components import page_header, empty_state


def render_research(df, profile, mode):
    """Render the Research Evaluation page with legacy and expanded suites."""
    from src.ml_analyzer import run_research_benchmark
    from src.research_suite import run_suite

    t = get_theme(mode)

    page_header(
        "Research Evaluation",
        "Reproducible evaluation layer for the research paper. Runs are button-triggered — no automatic execution.",
        "cyan",
        mode,
    )

    st.caption("The Expanded Research Suite is the primary V1.0 evidence source. The legacy 4-dataset benchmark is retained for diagnostics.")

    # Legacy benchmark
    st.markdown('<div class="riq-card">', unsafe_allow_html=True)
    st.markdown('<div class="riq-section-header">1. Legacy 4-Dataset Benchmark (Diagnostic)</div>', unsafe_allow_html=True)
    st.caption("Automatic routing evaluation on built-in sklearn datasets.")

    folds = st.selectbox("Cross-validation folds", [5, 10], index=0, key="research_folds")

    if st.button("Run Legacy Benchmark", type="secondary", key="run_research"):
        with st.spinner("Running routing, cross-validation, clustering, and statistical evaluation..."):
            research = run_research_benchmark("results", folds=folds)

        if not research["ok"]:
            st.error("Research benchmark failed.")
        else:
            routing = research["routing"]["results"].copy()
            st.success(f"Research benchmark completed. Automatic routing accuracy: {research['routing']['accuracy']*100:.1f}%")
            st.dataframe(routing, use_container_width=True, hide_index=True)

            st.markdown('<div class="riq-section-header">Leakage-safe Supervised Cross-Validation</div>', unsafe_allow_html=True)
            cv = research["cv_summary"].copy()
            if cv.empty:
                st.warning("No supervised CV results were produced.")
            else:
                st.dataframe(cv, use_container_width=True, hide_index=True)
                st.caption("Preprocessing is fitted separately within each fold.")

            st.markdown('<div class="riq-section-header">Unsupervised Evaluation</div>', unsafe_allow_html=True)
            cl = research["clustering"].get("results", pd.DataFrame())
            if not cl.empty:
                st.dataframe(cl, use_container_width=True, hide_index=True)
                fig = px.line(cl, x="K", y="Silhouette", markers=True,
                              title="K-Means Silhouette Score by K")
                st.plotly_chart(make_chart(fig, mode), use_container_width=True)

            st.markdown('<div class="riq-section-header">Statistical Comparison</div>', unsafe_allow_html=True)
            stats = research["statistics"]
            if stats.empty:
                st.info("No statistical comparison was generated for this run.")
            else:
                st.dataframe(stats, use_container_width=True, hide_index=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # Expanded suite
    st.markdown('<div class="riq-card">', unsafe_allow_html=True)
    st.markdown('<div class="riq-section-header">2. Expanded Research Dataset Suite</div>', unsafe_allow_html=True)
    st.caption("Primary V1.0 evidence: 5×5 repeated cross-validation, unsupervised clustering, ground-truth anomaly evaluation, temporal forecasting, and multiple-comparison-corrected statistical tests.")

    if st.button("Run Expanded Research Suite", type="primary", key="run_expanded_suite"):
        with st.spinner("Running expanded dataset suite (5 repeats × 5 folds)..."):
            expanded = run_suite(root="research_datasets", results_dir="results/research_suite", repeats=5, folds=5)

        st.success(f"Expanded suite completed across {int(expanded['run_summary'].iloc[0]['datasets'])} datasets. "
                   f"Routing accuracy: {expanded['run_summary'].iloc[0]['routing_accuracy']*100:.1f}%.")

        st.markdown('<div class="riq-section-header">Routing Evaluation</div>', unsafe_allow_html=True)
        st.dataframe(expanded["routing"], use_container_width=True, hide_index=True)

        st.markdown('<div class="riq-section-header">Supervised CV Summary</div>', unsafe_allow_html=True)
        st.dataframe(expanded["summary"], use_container_width=True, hide_index=True)

        st.markdown('<div class="riq-section-header">Unsupervised Metrics</div>', unsafe_allow_html=True)
        st.dataframe(expanded["clustering"], use_container_width=True, hide_index=True)

        st.markdown('<div class="riq-section-header">Statistical Tests</div>', unsafe_allow_html=True)
        st.dataframe(expanded["statistics"], use_container_width=True, hide_index=True)

        st.info("The expanded suite is the preferred source for the research paper; inspect the generated CSV artifacts before reporting any number.")

    st.markdown('</div>', unsafe_allow_html=True)

    # Saved artifacts
    st.markdown('<div class="riq-card">', unsafe_allow_html=True)
    st.markdown('<div class="riq-section-header">3. Saved V1.0 Evaluation Artifacts</div>', unsafe_allow_html=True)
    st.code(
        "results/research_suite/expanded_run_summary.csv\n"
        "results/research_suite/expanded_routing.csv\n"
        "results/research_suite/expanded_cv_summary.csv\n"
        "results/research_suite/expanded_cv_fold_results.csv\n"
        "results/research_suite/expanded_clustering_results.csv\n"
        "results/research_suite/expanded_anomaly_results.csv\n"
        "results/research_suite/expanded_forecasting_results.csv\n"
        "results/research_suite/expanded_statistical_tests.csv\n"
        "results/research_suite/expanded_advanced_predictive_results.csv"
    )
    st.info("These V1.0 evaluation artifacts are the primary saved outputs for the expanded 12-dataset benchmark.")
    st.markdown('</div>', unsafe_allow_html=True)
