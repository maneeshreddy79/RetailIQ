# RetailIQ V1.0 Corrections Log

Implemented after systematic testing of all 12 test datasets.

1. Advanced-model recommendations now compare Gradient Boosting with the best baseline using the same primary metric. A weaker advanced model is not presented as superior.
2. Supervised targets are excluded from clustering and anomaly-detection feature inputs.
3. Explicit reference/ground-truth labels such as `is_anomaly`, `anomaly_label`, `ground_truth` and `outlier_label` are excluded from unsupervised model inputs.
4. When a valid binary anomaly reference label exists, Isolation Forest predictions are independently evaluated with precision, recall and F1.
5. Datasets without anomaly ground truth report flagged observations without claiming anomaly accuracy.
6. Recommended Analytics is dataset-adaptive rather than a fixed three-card list.
7. Executive KPIs no longer use arbitrary first numeric columns as business measures; semantic measures such as sales/revenue/profit are preferred, otherwise structural KPIs are shown.
8. Date-like columns are no longer treated as categorical dimensions.
9. Dataset profiles distinguish Date/Time, Numeric/Measure, Categorical/Dimension and Text/Identifier roles.
10. Cleaning changes are summarized as raw rows/columns versus cleaned rows/columns.
11. Temporal supervised datasets use chronological holdout validation rather than random future/past mixing.
12. Forecast charts use the selected measure as the Y-axis label rather than a hard-coded `Amount` label.
13. Forecast recommendations include model, horizon and projected change and are framed as reviewable evidence rather than certainty.
14. Automated natural-language insights exclude reference labels from ordinary numeric summaries and explicitly distinguish reference labels from model predictions.
15. ML interpretation text is dataset-specific and does not merely list system capabilities.
16. General research evaluation includes Gradient Boosting alongside the existing supervised baselines.
17. The primary V1.0 research suite contains 12 datasets and records 5×5 repeated cross-validation for general supervised benchmarks.
18. Statistical testing is regenerated after the final model set using Friedman tests and Holm-corrected Wilcoxon comparisons where appropriate.
19. Public, synthetic, anomaly and forecasting datasets are explicitly identified in the research manifest.
20. Legacy V0.9 result files are separated from the primary V1.0 research evidence.
