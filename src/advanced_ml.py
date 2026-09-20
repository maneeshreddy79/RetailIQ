"""Advanced ML/AI utilities for RetailIQ V1.0.

Adds the remaining planned analytics paths without introducing heavy external
ML dependencies: anomaly detection, lag-based forecasting, advanced gradient
boosting baselines, ML-guided recommendations, and deterministic natural-
language insight generation.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.metrics import (
    accuracy_score, f1_score, mean_absolute_error, mean_squared_error, r2_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.model_selection import train_test_split

from .ml_analyzer import RANDOM_STATE, _datetime_expand, _drop_unusable_features, run_anomaly_detection, _temporal_split_indices, reference_label_columns


def advanced_model_specs(task: str):
    if task == "classification":
        return {
            "Gradient Boosting": GradientBoostingClassifier(random_state=RANDOM_STATE),
        }
    return {
        "Gradient Boosting": GradientBoostingRegressor(random_state=RANDOM_STATE),
    }


def run_advanced_predictive(df: pd.DataFrame, target: str, task: str | None = None, test_size: float = 0.2) -> dict:
    """Evaluate a gradient-boosting model as an advanced predictive baseline."""
    from .ml_analyzer import infer_task
    if target not in df.columns:
        return {"ok": False, "error": "Target column not found."}
    work = df.dropna(subset=[target]).copy()
    task = task or infer_task(work[target])
    if task not in {"classification", "regression"}:
        return {"ok": False, "error": "Unsupported supervised task."}
    X_raw = work.drop(columns=[target])
    temporal_split = _temporal_split_indices(work, test_size=test_size)
    X, dropped = _drop_unusable_features(X_raw)
    refs = [c for c in reference_label_columns(X) if c != target]
    if refs:
        dropped.extend([c for c in refs if c in X.columns])
        X = X.drop(columns=[c for c in refs if c in X.columns])
    if X.shape[1] == 0 or len(work) < 30:
        return {"ok": False, "error": "At least 30 usable rows and one feature are required."}

    # Keep the advanced model conservative: numeric features after datetime expansion.
    Xn = X.select_dtypes(include=np.number).copy()
    if Xn.shape[1] == 0:
        return {"ok": False, "error": "Advanced predictive baseline currently requires numeric features."}
    Xn = pd.DataFrame(SimpleImputer(strategy="median").fit_transform(Xn), columns=Xn.columns, index=Xn.index)
    if temporal_split:
        train_idx, test_idx, temporal_date_col = temporal_split
        train_idx = Xn.index.intersection(train_idx); test_idx = Xn.index.intersection(test_idx)
        X_train, X_test = Xn.loc[train_idx], Xn.loc[test_idx]
        y_train, y_test = work[target].loc[train_idx], work[target].loc[test_idx]
        validation_strategy = "chronological holdout"
    else:
        stratify = work[target] if task == "classification" and work[target].value_counts().min() >= 2 else None
        X_train, X_test, y_train, y_test = train_test_split(
            Xn, work[target], test_size=test_size, random_state=RANDOM_STATE, stratify=stratify
        )
        temporal_date_col = None
        validation_strategy = "random holdout (stratified for classification when feasible)"
    model = list(advanced_model_specs(task).values())[0]
    pipe = Pipeline([("scale", StandardScaler()), ("model", model)])
    try:
        pipe.fit(X_train, y_train)
        pred = pipe.predict(X_test)
        if task == "classification":
            metrics = {
                "Accuracy": float(accuracy_score(y_test, pred)),
                "F1": float(f1_score(y_test, pred, average="weighted", zero_division=0)),
            }
            direction = "max"
            primary = metrics["F1"]
        else:
            metrics = {
                "MAE": float(mean_absolute_error(y_test, pred)),
                "RMSE": float(np.sqrt(mean_squared_error(y_test, pred))),
                "R2": float(r2_score(y_test, pred)),
            }
            direction = "min"
            primary = metrics["RMSE"]
        perm = permutation_importance(
            pipe, X_test, y_test,
            scoring="f1_weighted" if task == "classification" else "neg_root_mean_squared_error",
            n_repeats=5, random_state=RANDOM_STATE,
        )
        importance = pd.DataFrame({"Feature": X_test.columns, "Importance": perm.importances_mean}) \
            .sort_values("Importance", ascending=False).reset_index(drop=True)
        return {
            "ok": True, "task": task, "target": target, "model": "Gradient Boosting",
            "metrics": metrics, "primary_metric": primary, "primary_direction": direction,
            "predictions": pd.DataFrame({"Actual": y_test.values, "Predicted": pred}),
            "importance": importance, "dropped_features": dropped,
            "validation_strategy": validation_strategy,
            "temporal_date_column": temporal_date_col,
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def _choose_date_column(df: pd.DataFrame) -> str | None:
    candidates = []
    for col in df.columns:
        s = df[col]
        if pd.api.types.is_datetime64_any_dtype(s):
            candidates.append((col, 1.0))
        elif pd.api.types.is_object_dtype(s) or pd.api.types.is_string_dtype(s):
            sample = s.dropna().astype(str).head(200)
            if len(sample) >= 10:
                parsed = pd.to_datetime(sample, errors="coerce")
                ratio = parsed.notna().mean()
                if ratio >= 0.80:
                    candidates.append((col, ratio))
    if not candidates:
        return None
    # Prefer date/time semantic names when several candidates exist.
    candidates.sort(key=lambda x: (any(t in x[0].lower() for t in ("date", "time", "day", "month", "year")), x[1]), reverse=True)
    return candidates[0][0]


def _choose_numeric_target(df: pd.DataFrame, date_col: str) -> str | None:
    nums = [c for c in df.select_dtypes(include=np.number).columns if c != date_col and df[c].nunique(dropna=True) > 2]
    if not nums:
        return None
    keywords = ("sales", "revenue", "profit", "amount", "value", "demand", "quantity", "total")
    nums.sort(key=lambda c: (any(k in c.lower() for k in keywords), df[c].nunique()), reverse=True)
    return nums[0]


def _forecast_frequency(dates: pd.Series) -> str:
    unique = pd.Series(pd.to_datetime(dates, errors="coerce").dropna().sort_values().unique())
    if len(unique) < 3:
        return "D"
    deltas = unique.diff().dropna().dt.total_seconds() / 86400
    med = float(deltas.median())
    if med <= 1.5:
        return "D"
    if med <= 8:
        return "W"
    if med <= 32:
        return "MS"
    return "YS"


def run_forecast(df: pd.DataFrame, date_col: str | None = None, target: str | None = None, horizon: int = 7) -> dict:
    """Forecast a numeric time series with lag features and Ridge/GBR baselines."""
    date_col = date_col or _choose_date_column(df)
    if not date_col:
        return {"ok": False, "error": "No date-like column was detected."}
    target = target or _choose_numeric_target(df, date_col)
    if not target or target not in df.columns:
        return {"ok": False, "error": "No suitable numeric forecasting measure was detected."}
    work = pd.DataFrame({"date": pd.to_datetime(df[date_col], errors="coerce"), "value": pd.to_numeric(df[target], errors="coerce")}).dropna()
    if work["date"].nunique() < 15:
        return {"ok": False, "error": "At least 15 distinct dates are recommended for forecasting."}
    freq = _forecast_frequency(work["date"])
    agg = work.groupby(pd.Grouper(key="date", freq=freq))["value"].sum().dropna().reset_index()
    if len(agg) < 15:
        return {"ok": False, "error": "Too few time periods remain after aggregation."}
    for lag in (1, 2, 3, 7):
        if lag < len(agg):
            agg[f"lag_{lag}"] = agg["value"].shift(lag)
    agg["rolling_mean_3"] = agg["value"].shift(1).rolling(3).mean()
    model_df = agg.dropna().copy()
    if len(model_df) < 12:
        return {"ok": False, "error": "Too few complete lag observations for a stable forecast."}
    features = [c for c in model_df.columns if c.startswith("lag_") or c == "rolling_mean_3"]
    test_n = max(3, min(horizon, len(model_df) // 4))
    train, test = model_df.iloc[:-test_n], model_df.iloc[-test_n:]
    models = {
        "Ridge Lag Model": Ridge(alpha=1.0),
        "Gradient Boosting Lag Model": GradientBoostingRegressor(random_state=RANDOM_STATE),
    }
    rows = []
    fitted = {}
    for name, model in models.items():
        model.fit(train[features], train["value"])
        pred = model.predict(test[features])
        rows.append({"Model": name, "MAE": mean_absolute_error(test["value"], pred), "RMSE": np.sqrt(mean_squared_error(test["value"], pred)), "R2": r2_score(test["value"], pred)})
        fitted[name] = model
    # Recursive future forecast using the stronger RMSE model on the historical data.
    score_df = pd.DataFrame(rows)
    best_name = str(score_df.loc[score_df["RMSE"].idxmin(), "Model"])
    final_model = models[best_name]
    final_model.fit(model_df[features], model_df["value"])
    history = agg["value"].tolist()
    future_dates = pd.date_range(agg["date"].iloc[-1], periods=horizon + 1, freq=freq)[1:]
    future_values = []
    for _ in range(horizon):
        lags = {1: history[-1], 2: history[-2] if len(history) >= 2 else history[-1], 3: history[-3] if len(history) >= 3 else history[-1], 7: history[-7] if len(history) >= 7 else history[-1]}
        row = [[lags[1], lags[2], lags[3], lags[7], float(np.mean(history[-3:]))]]
        val = float(final_model.predict(pd.DataFrame(row, columns=features))[0])
        history.append(val); future_values.append(val)
    forecast = pd.DataFrame({"date": future_dates, "forecast": future_values})
    return {"ok": True, "date_column": date_col, "target": target, "frequency": freq, "aggregated": agg, "evaluation": score_df, "best_model": best_name, "forecast": forecast}


def ml_guided_recommendations(result: dict, baseline_result: dict | None = None,
                               anomaly_result: dict | None = None,
                               forecast_result: dict | None = None) -> list[dict[str, Any]]:
    """Generate evidence-based recommendations and never imply unsupported model superiority."""
    recs = []
    if result.get("ok"):
        task = result.get("task")
        model = result.get("model")
        metric_name = "F1" if task == "classification" else "RMSE"
        advanced_metric = result.get("metrics", {}).get(metric_name)
        baseline_metric = None
        baseline_model = None
        if baseline_result and baseline_result.get("ok"):
            rdf = baseline_result.get("results", pd.DataFrame())
            if not rdf.empty and metric_name in rdf.columns:
                valid = rdf.dropna(subset=[metric_name])
                if not valid.empty:
                    row = valid.loc[valid[metric_name].idxmax()] if task == "classification" else valid.loc[valid[metric_name].idxmin()]
                    baseline_metric = float(row[metric_name]); baseline_model = str(row["Model"])
        improved = None
        if advanced_metric is not None and baseline_metric is not None:
            improved = advanced_metric > baseline_metric if task == "classification" else advanced_metric < baseline_metric
        if improved is True:
            text = f"Gradient Boosting improved the best baseline on the current validation setup; retain it as an additional candidate."
            priority = "High"
        elif improved is False:
            text = f"Gradient Boosting did not improve the best baseline ({baseline_model}); retain it for comparison rather than treating it as superior."
            priority = "Low"
        else:
            text = "Evaluate Gradient Boosting as an additional predictive baseline and compare it using the same validation protocol."
            priority = "Medium"
        evidence = f"{metric_name}={advanced_metric:.4f}" if advanced_metric is not None else "Measured validation result"
        if baseline_metric is not None:
            evidence += f"; best baseline {baseline_model}={baseline_metric:.4f}"
        recs.append({"Source": "ML evaluation", "Priority": priority, "Recommendation": text, "Evidence": evidence})
        imp = result.get("importance")
        if isinstance(imp, pd.DataFrame) and not imp.empty:
            top = ", ".join(imp.head(3)["Feature"].astype(str))
            recs.append({"Source": "Feature importance", "Priority": "Medium", "Recommendation": "Review the most influential variables as predictive signals; do not interpret permutation importance as causation.", "Evidence": f"Top variables: {top}"})
    if anomaly_result and anomaly_result.get("ok"):
        n = anomaly_result.get("anomalies", 0)
        if anomaly_result.get("ground_truth_available"):
            gm = anomaly_result.get("ground_truth_metrics", {})
            recs.append({"Source": "Anomaly evaluation", "Priority": "High", "Recommendation": "Compare flagged observations with the available ground-truth anomaly label and investigate false positives/negatives.", "Evidence": f"Precision={gm.get('Precision',0):.3f}; Recall={gm.get('Recall',0):.3f}; F1={gm.get('F1',0):.3f}"})
        else:
            recs.append({"Source": "Anomaly detection", "Priority": "Medium" if n else "Low", "Recommendation": "Investigate model-flagged observations; no ground-truth anomaly label is available for accuracy validation.", "Evidence": f"{n} observations flagged ({anomaly_result.get('contamination',0.05):.0%} configured contamination)"})
    if forecast_result and forecast_result.get("ok"):
        fc = forecast_result["forecast"]["forecast"]
        if len(fc) >= 2:
            change = float(fc.iloc[-1] - fc.iloc[0])
            direction = "increase" if change > 0 else "decrease" if change < 0 else "stable level"
            recs.append({"Source": "Forecasting", "Priority": "Medium", "Recommendation": f"The selected forecasting model projects a {direction}; review the forecast alongside historical variability before using it for planning.", "Evidence": f"Model={forecast_result.get('best_model')}; horizon={len(fc)}; projected change={change:.2f}"})
    return recs


def generate_natural_language_insights(df: pd.DataFrame, profile: dict | None = None,
                                       anomaly_result: dict | None = None,
                                       forecast_result: dict | None = None) -> list[str]:
    """Generate deterministic, dataset-aware, non-causal insights."""
    insights = []
    refs = set(reference_label_columns(df))
    numeric = df.select_dtypes(include=np.number).drop(columns=[c for c in refs if c in df.columns], errors="ignore")
    if profile:
        if profile.get("date_columns"):
            insights.append(f"Temporal structure detected: {', '.join(map(str, profile['date_columns']))} can support time-based analysis.")
        if profile.get("categorical_columns") and numeric.shape[1]:
            insights.append(f"Mixed analytical structure detected with {len(profile['categorical_columns'])} categorical dimensions and {numeric.shape[1]} numeric features.")
        elif numeric.shape[1]:
            insights.append(f"Numeric analytical structure detected with {numeric.shape[1]} usable numeric features.")
        missing = int(profile.get("missing_cells", 0)); dup = int(profile.get("duplicate_rows", 0))
        if missing or dup:
            insights.append(f"Data quality signal: {missing:,} missing cells and {dup:,} duplicate rows were detected.")
    for col in numeric.columns[:5]:
        s = numeric[col].dropna()
        if len(s) >= 3 and s.nunique() > 1:
            insights.append(f"{col}: mean={s.mean():.2f}, median={s.median():.2f}, range={s.min():.2f} to {s.max():.2f}.")
    if refs:
        for col in refs:
            if col in df.columns:
                s=df[col].dropna()
                if len(s) and s.nunique() <= 10:
                    insights.append(f"Reference label detected in `{col}`; it is excluded from unsupervised model inputs and reserved for independent evaluation.")
    if anomaly_result and anomaly_result.get("ok"):
        if anomaly_result.get("ground_truth_available"):
            gm=anomaly_result.get("ground_truth_metrics",{})
            insights.append(f"Anomaly evaluation: Isolation Forest flagged {anomaly_result['anomalies']:,} observations; ground-truth comparison gives F1={gm.get('F1',0):.3f}.")
        else:
            insights.append(f"Anomaly signal: {anomaly_result['anomalies']:,} observations were flagged by Isolation Forest; no ground-truth anomaly label is available.")
    if forecast_result and forecast_result.get("ok"):
        fc = forecast_result["forecast"]["forecast"]
        if len(fc) >= 2:
            change = float(fc.iloc[-1] - fc.iloc[0])
            insights.append(f"Forecast signal: {forecast_result.get('best_model')} projects a {change:.2f} change over the next {len(fc)} periods.")
    return insights[:10]
