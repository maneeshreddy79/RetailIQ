# RetailIQ V1.0 Research Evaluation

The V1.0 Expanded Research Suite is the primary evidence source for the research paper.

## Dataset coverage
The suite contains 12 datasets: 5 classification, 2 regression, 3 unsupervised, 1 anomaly-detection benchmark with ground truth, and 1 temporal forecasting benchmark.

## Supervised evaluation
General tabular classification and regression use 5 repeats × 5 folds. Preprocessing is fitted independently inside each training fold. Classification uses weighted F1 as the primary metric; regression uses RMSE. Logistic/Linear Regression, Decision Tree, Random Forest and Gradient Boosting are evaluated using the same folds.

## Unsupervised evaluation
K-Means is evaluated over K=2..6 with Silhouette, Davies–Bouldin, Calinski–Harabasz and Inertia. Reference/ground-truth labels are excluded from model inputs.

## Anomaly evaluation
Isolation Forest is evaluated on the synthetic retail anomaly dataset. The `is_anomaly` field is reserved as ground truth and excluded from model inputs. Precision, recall and F1 are reported against that independent label. For datasets without ground truth, only flagged counts/rates are reported.

## Forecasting
The synthetic retail forecasting dataset is evaluated using chronological holdout validation. Lag and rolling features are constructed only from historical observations. Ridge and Gradient Boosting lag models are compared on a future holdout and then used for recursive future forecasting.

## Statistical testing
Friedman tests compare repeated model observations. Pairwise Wilcoxon signed-rank tests are run only after a significant Friedman result and are Holm-adjusted for multiple comparisons.

## Interpretation
The benchmark demonstrates reproducible behavior of the implemented methods on the selected datasets. It does not establish universal model superiority or causal relationships.
