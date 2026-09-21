"""RetailIQ Classification page."""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from ..theme import get_theme, make_chart
from ..components import page_header, kpi_row, empty_state


def render_classification(df, profile, mode, selected_target, resolved_task):
    """Render the Classification page using existing supervised backend."""
    from src.ml_analyzer import detect_target, target_candidates, infer_task, run_supervised, log_experiment

    t = get_theme(mode)

    page_header(
        "Classification",
        "Train and compare classification models. Select a categorical target and run the benchmark.",
        "primary",
        mode,
    )

    auto_target = detect_target(df)
    candidates = target_candidates(df)
    usable_numeric = [c for c in df.select_dtypes(include=np.number).columns if df[c].nunique(dropna=True) > 1]
    usable_features = len(profile["numeric_columns"]) + len(profile["categorical_columns"]) + len(profile["date_columns"])

    # Info cards
    cards = [
        {"label": "ML Rows", "value": f"{len(df):,}", "accent": "cyan"},
        {"label": "Candidate Features", "value": f"{usable_features:,}", "accent": "primary"},
        {"label": "Numeric Signals", "value": f"{len(usable_numeric):,}", "accent": "orange"},
        {"label": "Auto Target", "value": str(auto_target) if auto_target else "None", "accent": "green" if auto_target else "red"},
    ]
    kpi_row(cards, mode)

    if auto_target:
        st.success(f"Adaptive routing: **{auto_target}** is a high-confidence target candidate.")
    else:
        st.info("No high-confidence target detected. Choose a target manually if your dataset has one.")

    if not candidates.empty:
        with st.expander("Target suggestions and confidence"):
            shown = candidates.copy()
            shown["Confidence"] = (shown["Confidence"] * 100).round(0).astype(int).astype(str) + "%"
            st.dataframe(shown, use_container_width=True, hide_index=True)

    # Target selection
    target_options = ["— No target / unsupervised —"] + list(df.columns)
    default_index = target_options.index(auto_target) if auto_target in target_options else 0
    selected_target = st.selectbox("Target column", target_options, index=default_index, key="ml_target")

    if selected_target == "— No target / unsupervised —":
        empty_state("🎯", "Select a supervised target above to enable classification analysis.", mode)
        return selected_target, None

    inferred = infer_task(df[selected_target])
    if inferred != "classification":
        st.warning(f"Detected task for `{selected_target}` is **{inferred}**, not classification. This target may be better suited for the Regression page.")
        return selected_target, inferred

    task_choice = st.selectbox("ML task", ["Auto", "classification", "regression"], index=0, key="ml_task")
    resolved_task = inferred if task_choice == "Auto" else task_choice
    st.info(f"Detected task: **{inferred}** · Selected task: **{resolved_task}**")

    test_size = st.slider("Test-set size", 0.15, 0.40, 0.20, 0.05, key="ml_test_size")

    if st.button("Run Classification Benchmark", type="primary", key="run_classification"):
        with st.spinner("Training baseline models and evaluating the hold-out test set..."):
            ml_result = run_supervised(df, selected_target, "classification", test_size=test_size)

        if not ml_result["ok"]:
            st.warning(ml_result["error"])
            return selected_target, resolved_task

        st.success(f"Benchmark completed using {ml_result['train_rows']:,} training rows and {ml_result['test_rows']:,} test rows.")
        st.caption(f"Features used: {ml_result['features_used']} · Dropped: {len(ml_result['dropped_features'])} · Seed: {ml_result['random_state']}")
        for note in ml_result.get("diagnostics", []):
            st.warning(note)

        # Results table
        st.markdown('<div class="riq-section-header">Model Comparison</div>', unsafe_allow_html=True)
        results = ml_result["results"].copy()
        metric_cols = [c for c in results.columns if c not in {"Model", "Error"}]
        for c in metric_cols:
            results[c] = pd.to_numeric(results[c], errors="coerce")
        st.dataframe(results, use_container_width=True, hide_index=True)

        # Best model
        valid = results.dropna(subset=[c for c in metric_cols if c in results.columns], how="all")
        if not valid.empty and "F1" in valid.columns:
            best_name = valid.loc[valid["F1"].idxmax(), "Model"]
            st.metric("Best baseline (weighted F1)", str(best_name))

        # Experiment log
        try:
            log_path = log_experiment(ml_result)
            st.caption(f"Experiment logged to `{log_path.as_posix()}`.")
        except Exception as exc:
            st.warning(f"Benchmark completed, but experiment logging failed: {exc}")

        # Feature importance
        st.markdown("---")
        st.markdown('<div class="riq-section-header">Feature Importance / Influence</div>', unsafe_allow_html=True)
        st.caption("Permutation importance measures how much model performance changes when each feature is shuffled.")
        model_names = list(ml_result["importances"].keys())
        if model_names:
            chosen_model = st.selectbox("Model explanation", model_names, key="ml_explain_model")
            imp = ml_result["importances"][chosen_model]
            if imp.empty:
                st.info("Permutation importance could not be computed for this model/dataset.")
            else:
                display_imp = imp.copy()
                display_imp["Importance"] = display_imp["Importance"].round(6)
                if "Std" in display_imp.columns:
                    display_imp["Std"] = display_imp["Std"].round(6)
                st.dataframe(display_imp, use_container_width=True, hide_index=True)
                fig = px.bar(display_imp.sort_values("Importance"), x="Importance", y="Feature",
                             orientation="h", title=f"Permutation importance — {chosen_model}")
                st.plotly_chart(make_chart(fig, mode), use_container_width=True)

    return selected_target, resolved_task
