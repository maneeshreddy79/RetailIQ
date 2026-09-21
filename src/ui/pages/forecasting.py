"""RetailIQ Forecasting page."""

import streamlit as st
import pandas as pd
import plotly.express as px

from ..theme import get_theme, make_chart
from ..components import page_header, kpi_row, empty_state


def render_forecasting(df, profile, mode, metric, date_cols, num_cols):
    """Render the Forecasting page using existing forecasting backend."""
    from src.advanced_ml import run_forecast

    t = get_theme(mode)

    page_header(
        "Forecasting",
        "Build time-series forecasts using lag features. Compare Ridge and Gradient Boosting baselines.",
        "orange",
        mode,
    )

    if not date_cols or not num_cols:
        empty_state("📅", "Forecasting requires at least one date-like column and one numeric measure.", mode)
        return

    # Controls
    st.markdown('<div class="riq-card">', unsafe_allow_html=True)
    st.markdown('<div class="riq-section-header">Forecast Configuration</div>', unsafe_allow_html=True)

    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        forecast_date = st.selectbox("Date column", date_cols, key="forecast_date",
                                      format_func=lambda v: v.replace("_", " ").title())
    with fc2:
        forecast_target = st.selectbox("Forecast measure", num_cols,
                                        index=num_cols.index(metric) if metric in num_cols else 0,
                                        key="forecast_target", format_func=lambda v: v.replace("_", " ").title())
    with fc3:
        forecast_horizon = st.slider("Forecast horizon (periods)", 3, 30, 7, key="forecast_horizon")

    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("Run Forecasting", type="primary", key="run_forecast"):
        with st.spinner("Building lag features and evaluating forecasting baselines..."):
            fc = run_forecast(df, forecast_date, forecast_target, forecast_horizon)

        if not fc["ok"]:
            st.warning(fc["error"])
            return

        st.success(f"Forecast completed using {fc['best_model']} at {fc['frequency']} frequency.")

        # Summary cards
        eval_df = fc["evaluation"].round(4)
        best_row = eval_df.loc[eval_df["RMSE"].idxmin()]
        cards = [
            {"label": "Best Model", "value": fc["best_model"], "accent": "orange"},
            {"label": "Frequency", "value": fc["frequency"], "accent": "cyan"},
            {"label": "Best RMSE", "value": f"{best_row['RMSE']:.4f}", "accent": "primary"},
            {"label": "Best R²", "value": f"{best_row['R2']:.4f}", "accent": "green"},
        ]
        kpi_row(cards, mode)

        # Model comparison
        st.markdown('<div class="riq-section-header">Model Comparison</div>', unsafe_allow_html=True)
        st.dataframe(eval_df, use_container_width=True, hide_index=True)

        # Forecast chart
        st.markdown('<div class="riq-section-header">Forecast Chart</div>', unsafe_allow_html=True)
        hist = fc["aggregated"][["date", "value"]].tail(60).copy()
        hist["Series"] = "Historical"
        hist.rename(columns={"value": forecast_target}, inplace=True)
        pred = fc["forecast"][["date", "forecast"]].copy()
        pred["Series"] = "Forecast"
        pred.rename(columns={"forecast": forecast_target}, inplace=True)
        chart = pd.concat([hist, pred], ignore_index=True)
        fig = px.line(chart, x="date", y=forecast_target, color="Series", markers=True,
                      title=f"Forecast — {forecast_target.replace('_',' ').title()}")
        st.plotly_chart(make_chart(fig, mode, height=450), use_container_width=True)

        # Projected change
        fc_vals = fc["forecast"]["forecast"]
        if len(fc_vals) >= 2:
            change = float(fc_vals.iloc[-1] - fc_vals.iloc[0])
            direction = "increase" if change > 0 else "decrease" if change < 0 else "stable level"
            st.info(
                f"Projected change: {direction} of {abs(change):.2f} over the next {len(fc_vals)} periods. "
                f"Review alongside historical variability before using for planning."
            )
