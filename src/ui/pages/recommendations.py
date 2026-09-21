"""RetailIQ Recommendations page — with routing and NL insights."""

import streamlit as st
import pandas as pd

from ..theme import get_theme
from ..components import page_header, recommendation_card, insight_card, empty_state, badge


def render_recommendations(df, profile, mode, selected_target, resolved_task, date_cols, metric):
    """Render the Recommendations page with clickable routing and NL insights."""
    from src.recommender import generate_recommendations
    from src.advanced_ml import generate_natural_language_insights, run_anomaly_detection, run_forecast

    t = get_theme(mode)

    page_header(
        "Recommendations",
        "Dataset-aware analytical recommendations generated from your data's structure and measured signals.",
        "green",
        mode,
    )

    # Generate recommendations with context
    rec_context = {
        "target": selected_target if selected_target and selected_target != "— No target / unsupervised —" else None,
        "task": resolved_task,
    }
    recommendations = generate_recommendations(profile, df, rec_context)

    # Routing map: recommendation title keywords -> page id
    def route_for_rec(rec):
        title_lower = rec.get("title", "").lower()
        desc_lower = rec.get("description", "").lower()
        combined = title_lower + " " + desc_lower
        if "classification" in combined:
            return "classification"
        if "regression" in combined:
            return "regression"
        if "cluster" in combined:
            return "clustering"
        if "forecast" in combined:
            return "forecasting"
        if "anomaly" in combined:
            return "anomaly"
        if "breakdown" in combined or "segment" in combined or "categorical" in combined:
            return "breakdown"
        if "relationship" in combined or "correlation" in combined or "feature" in combined:
            return "relationships"
        if "data quality" in combined or "cleaning" in combined:
            return "data_quality"
        if "time-series" in combined or "trend" in combined:
            return "dashboard"
        return None

    st.markdown('<div class="riq-section-header">Analytical Recommendations</div>', unsafe_allow_html=True)

    if not recommendations:
        empty_state("💡", "No recommendations could be generated for this dataset.", mode)
    else:
        for i, rec in enumerate(recommendations):
            recommendation_card(rec, i, mode)
            route = route_for_rec(rec)
            if route:
                if st.button(f"Go to {route.replace('_',' ').title()}", key=f"rec_route_{i}", help=f"Navigate to {route}"):
                    st.session_state["current_page"] = route
                    st.rerun()

    # ML-guided recommendations
    st.markdown("---")
    st.markdown('<div class="riq-section-header">ML-Guided Recommendations</div>', unsafe_allow_html=True)
    st.caption("Recommendations derived from measured model, anomaly and forecast signals.")

    if st.button("Generate ML-Guided Recommendations", key="run_ml_recs"):
        from src.advanced_ml import ml_guided_recommendations, run_advanced_predictive
        from src.ml_analyzer import run_anomaly_detection as run_anom, run_supervised as run_sup

        rec_ml_target = selected_target if selected_target and selected_target != "— No target / unsupervised —" else None
        rec_task = resolved_task if rec_ml_target else None

        with st.spinner("Running ML models to generate evidence-based recommendations..."):
            adv_for_rec = run_advanced_predictive(df, rec_ml_target, rec_task) if rec_ml_target else {}
            anomaly_for_rec = run_anom(df, 0.05, exclude_columns=[rec_ml_target] if rec_ml_target else None)
            forecast_for_rec = run_forecast(df, date_cols[0], metric, 7) if date_cols and metric else {}
            baseline_for_rec = run_sup(df, rec_ml_target, rec_task, test_size=0.20) if rec_ml_target else {}
            recs_ml = ml_guided_recommendations(adv_for_rec, baseline_for_rec, anomaly_for_rec, forecast_for_rec)

        if recs_ml:
            st.dataframe(pd.DataFrame(recs_ml), use_container_width=True, hide_index=True)
        else:
            st.info("No ML-guided recommendations could be generated from the current dataset.")

    # Natural-language insights
    st.markdown("---")
    st.markdown('<div class="riq-section-header">Natural-Language Insights</div>', unsafe_allow_html=True)
    st.caption("Deterministic, data-grounded narrative insights. Does not require an external LLM and does not invent unsupported facts.")

    if st.button("Generate Automated Insights", key="run_nl_insights"):
        with st.spinner("Generating natural-language insights..."):
            anomaly_for_nl = run_anomaly_detection(df, 0.05,
                exclude_columns=[selected_target] if selected_target and selected_target != "— No target / unsupervised —" else None)
            forecast_for_nl = run_forecast(df, date_cols[0], metric, 7) if date_cols and metric else {}
            insights = generate_natural_language_insights(df, profile, anomaly_for_nl, forecast_for_nl)

        if insights:
            for i, insight in enumerate(insights, 1):
                insight_card(insight, mode)
        else:
            st.info("No sufficiently strong signals were available for automated narrative generation.")
