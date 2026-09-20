def _add(recs, priority, title, description, why, business_value, tools, question):
    recs.append({"priority": priority, "title": title, "description": description,
                 "why": why, "business_value": business_value, "tools": tools, "question": question})


def generate_recommendations(profile, df, analysis_context=None):
    """Generate recommendations from detected dataset characteristics and measured results."""
    analysis_context = analysis_context or {}
    recs = []
    numeric = profile.get("numeric_columns", [])
    cats = profile.get("categorical_columns", [])
    dates = profile.get("date_columns", [])
    missing = profile.get("missing_cells", 0)
    duplicates = profile.get("duplicate_rows", 0)
    target = analysis_context.get("target")
    task = analysis_context.get("task")
    anomaly = analysis_context.get("anomaly")
    clustering = analysis_context.get("clustering")
    reference_cols = [c for c in df.columns if str(c).strip().lower() in {"is_anomaly","anomaly_label","ground_truth","outlier_label","reference_label"}]

    if missing or duplicates:
        _add(recs, "⚠️", "Resolve Data-Quality Issues",
             "Review missing values and duplicate records before relying on downstream analysis.",
             "The dataset contains quality signals that can distort measurements or model results.",
             "Improves reliability and reproducibility.", "Python, Pandas",
             "Which fields require cleaning or validation before reporting?")

    if dates and numeric:
        _add(recs, "1️⃣", "Perform Time-Series Analysis",
             "Analyze the selected numeric measures over the detected date field for trends, seasonality and unusual periods.",
             "A date-like field and numeric measures are available.",
             "Supports temporal monitoring and forecasting decisions.", "Python, Pandas, Plotly",
             "How does the key measure change over time?")
        _add(recs, "2️⃣", "Evaluate Forecasting",
             "Compare forecasting models using chronological validation before using predictions for planning.",
             "The dataset has temporal structure suitable for forecasting.",
             "Supports evidence-based forward planning.", "Python, scikit-learn",
             "What is the expected future trajectory of the key measure?")
    elif target and task:
        if task == "classification":
            _add(recs, "1️⃣", "Evaluate Classification Performance",
                 "Compare class-aware metrics and inspect class balance and influential predictors.",
                 "A supervised classification target was detected.",
                 "Supports defensible predictive classification.", "scikit-learn, Python",
                 "Which predictors and models perform reliably across classes?")
        elif task == "regression":
            _add(recs, "1️⃣", "Evaluate Regression Performance",
                 "Compare MAE, RMSE and R² across multiple baselines using a consistent validation design.",
                 "A continuous supervised target was detected.",
                 "Supports evidence-based prediction.", "scikit-learn, Python",
                 "Which model gives the most reliable prediction error?")
    elif len(numeric) >= 2:
        _add(recs, "1️⃣", "Evaluate Cluster Structure",
             "Compare cluster configurations and inspect feature separation before interpreting segments.",
             "Multiple varying numeric features are available without a supervised target.",
             "Reveals potential latent groups without requiring labels.", "Python, scikit-learn",
             "Do the observations form meaningful clusters?")
        _add(recs, "2️⃣", "Analyze Feature Relationships",
             "Inspect correlations, distributions and pairwise relationships among numeric variables.",
             "The dataset contains multiple measurable features.",
             "Reveals redundancy, associations and unusual observations.", "Pandas, Plotly",
             "Which variables move together or show unusual patterns?")
    elif numeric:
        _add(recs, "1️⃣", "Profile the Primary Numeric Signal",
             "Inspect distribution, variability and outliers of the available numeric measure.",
             "Only one suitable numeric feature is available.",
             "Prevents unsupported multivariate conclusions.", "Pandas, Plotly",
             "What does the primary measure reveal about the observations?")

    if cats and numeric:
        _add(recs, "3️⃣", "Compare Categorical Segments",
             "Compare numeric measures across the most informative categorical dimensions.",
             "Categorical dimensions and measurable fields are both available.",
             "Supports targeted group comparisons.", "Pandas, Plotly, Power BI",
             "Which groups differ most on the key measure?")

    if len(numeric) >= 2 and not dates and not target:
        _add(recs, "3️⃣", "Investigate Feature Relationships",
             "Use correlations and pairwise plots to understand relationships among measurable variables.",
             "Multiple numeric features are available without a supervised target.",
             "Supports exploratory and unsupervised analysis.", "Pandas, Plotly",
             "Which features are strongly associated?")

    if reference_cols and any("anomaly" in str(c).lower() or "outlier" in str(c).lower() for c in reference_cols):
        _add(recs, "High", "Validate Anomaly Labels",
             f"Use `{reference_cols[0]}` as an independent reference label when evaluating anomaly detection; do not use it as a model input feature.",
             "A ground-truth/reference anomaly field is available.",
             "Enables quantitative anomaly validation without target leakage.", "scikit-learn, Pandas",
             "How closely do model-flagged observations agree with the known anomaly labels?")

    if anomaly and anomaly.get("ok"):
        if anomaly.get("ground_truth_available"):
            _add(recs, "High", "Validate Detected Anomalies",
                 "Compare model-flagged observations with the available ground-truth anomaly label and inspect false positives and false negatives.",
                 "A reference anomaly label is available and was excluded from model inputs.",
                 "Provides quantitative anomaly-validation evidence.", "scikit-learn, Pandas",
                 "How closely do model flags agree with the known anomaly labels?")
        else:
            _add(recs, "High", "Investigate Flagged Observations",
                 "Review model-flagged observations and their feature values; treat them as candidates for investigation rather than confirmed anomalies.",
                 "Isolation Forest identified unusual observations but no ground-truth label is available.",
                 "Supports data-quality and risk investigation without overstating certainty.", "scikit-learn, Pandas",
                 "Which flagged observations warrant review?")

    if clustering and clustering.get("ok"):
        sil = clustering.get("silhouette")
        if sil is not None and sil < 0.25:
            _add(recs, "Medium", "Reassess Cluster Separation",
                 "Test alternative cluster counts or dimensionality-reduction approaches before interpreting the segments.",
                 f"The current silhouette score is {sil:.3f}, indicating limited separation under the evaluated configuration.",
                 "Reduces the risk of over-interpreting weak clusters.", "scikit-learn, Plotly",
                 "Can another representation or K value produce clearer separation?")

    if not recs:
        _add(recs, "ℹ️", "Inspect Dataset Structure",
             "Review the dataset's meaning and available analytical signals before advanced analytics.",
             "The current structure does not provide enough evidence for a more specific recommendation.",
             "Prevents unsupported analysis.", "Python, Pandas",
             "What decision is this dataset intended to support?")

    # Stable ordering: data quality first, then numbered/High/Medium recommendations.
    unique=[]; seen=set()
    for item in recs:
        if item['title'] not in seen:
            unique.append(item); seen.add(item['title'])
    return unique[:6]
