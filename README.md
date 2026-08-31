# RetailIQ V0.5

RetailIQ is an adaptive Streamlit analytics application that turns a CSV/Excel dataset into a Power BI–style interactive analytics workspace.

## Highlights
- CSV/XLSX/XLS ingestion
- Automatic dataset profiling and data-quality assessment
- Conservative cleaning with an audit log
- KPI cards with adaptive metric selection
- Sidebar slicer-style categorical filters
- Date-range filtering when a date column is detected
- Trend, category ranking, share, distribution and relationship analysis
- Business snapshot and analytics recommendations
- Filtered-data CSV export
- Generic column handling — does not depend on fixed retail column names

## Run locally
```powershell
cd RetailIQ_V0_5
pip install -r requirements.txt
streamlit run app.py
```

Then open the localhost URL shown by Streamlit.

## Project structure
```text
RetailIQ_V0_5/
├── app.py
├── requirements.txt
├── data/
│   └── sample_retail_data.csv
├── docs/
│   └── methodology.md
├── reports/
├── results/
└── src/
    ├── analyzer.py
    ├── cleaner.py
    ├── recommender.py
    └── visualizer.py
```
