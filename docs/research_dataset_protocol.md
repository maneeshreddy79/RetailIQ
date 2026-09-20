# RetailIQ V1.0 Research Dataset Protocol

The primary V1.0 research suite contains 12 datasets:
- 5 classification datasets
- 2 regression datasets
- 3 unsupervised datasets
- 1 synthetic anomaly-detection dataset with independent ground-truth labels
- 1 synthetic temporal forecasting dataset

Public benchmark datasets are kept separate from synthetic retail benchmarks.

## General supervised evaluation
Classification and regression datasets use 5 repeats × 5 folds. Preprocessing is fitted inside each training fold. The primary classification metric is weighted F1; the primary regression metric is RMSE. Accuracy, precision, recall, MAE and R² are also recorded.

Gradient Boosting is evaluated alongside the existing Logistic/Linear Regression, Decision Tree and Random Forest baselines. Model comparisons use the same folds and preprocessing pipeline.

## Unsupervised evaluation
K-Means is evaluated over K=2..6 using Silhouette, Davies–Bouldin, Calinski–Harabasz and Inertia. Explicit reference/ground-truth labels are never used as clustering features.

## Anomaly evaluation
The synthetic retail anomaly dataset contains a binary `is_anomaly` reference label. Isolation Forest excludes this field from its input features and the predictions are compared with the reference label using precision, recall and F1.

Datasets without ground-truth anomaly labels report only the number/rate of model-flagged observations and do not claim anomaly accuracy.

## Forecasting
The synthetic retail forecasting dataset contains daily `date` and `sales`. Forecasting uses chronological validation, lag and rolling features, and compares Ridge and Gradient Boosting forecasting baselines. Future observations are never used to train the holdout evaluation.

## Statistical testing
For general supervised model comparisons, Friedman tests are applied across repeated CV observations. Pairwise Wilcoxon signed-rank tests are performed only after a significant Friedman result, with Holm correction for multiple comparisons.

The suite is a reproducible benchmark of the implemented methods, not a claim of global model optimality.
