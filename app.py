"""RetailIQ — Adaptive Data Analytics & Business Insight System.

Main entry point. Handles data loading, session state, navigation, and page routing.
All analytics are performed by the existing backend modules in src/.
"""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# Ensure project root is on sys.path for src imports
PROJECT_ROOT = Path(__file__).parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.analyzer import analyze_dataset
from src.cleaner import build_cleaning_plan, clean_dataset
from src.recommender import generate_recommendations
from src.ml_analyzer import detect_target, infer_task, target_candidates, reference_label_columns
from src.ui.theme import inject_css, get_theme
from src.ui.navigation import render_sidebar, ALL_PAGES
from src.ui.components import choose_metric, choose_dimension
from src.ui.pages.landing import render_landing
from src.ui.pages.overview import render_dashboard
from src.ui.pages.data import render_data
from src.ui.pages.data_quality import render_data_quality
from src.ui.pages.breakdown import render_breakdown
from src.ui.pages.relationships import render_relationships
from src.ui.pages.classification import render_classification
from src.ui.pages.regression import render_regression
from src.ui.pages.clustering import render_clustering
from src.ui.pages.forecasting import render_forecasting
from src.ui.pages.anomaly import render_anomaly
from src.ui.pages.recommendations import render_recommendations
from src.ui.pages.research import render_research

st.set_page_config(
    page_title="RetailIQ — Adaptive Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


def init_session_state():
    """Initialize session state defaults."""
    if "current_page" not in st.session_state:
        st.session_state["current_page"] = "dashboard"
    if "theme_mode" not in st.session_state:
        st.session_state["theme_mode"] = "dark"
    if "selected_target" not in st.session_state:
        st.session_state["selected_target"] = None
    if "resolved_task" not in st.session_state:
        st.session_state["resolved_task"] = None


def load_data(uploaded):
    """Load, profile, clean, and store dataset in session state."""
    try:
        if uploaded.name.lower().endswith(".csv"):
            raw_df = pd.read_csv(uploaded)
        else:
            raw_df = pd.read_excel(uploaded)
    except Exception as exc:
        st.error(f"Could not read the dataset: {exc}")
        return False

    if raw_df.empty:
        st.error("The uploaded dataset is empty.")
        return False

    profile = analyze_dataset(raw_df)
    plan = build_cleaning_plan(raw_df)
    cleaned_df, cleaning_log = clean_dataset(raw_df)
    clean_profile = analyze_dataset(cleaned_df)

    rec_context = {
        "target": None,
        "task": None,
    }
    recommendations = generate_recommendations(clean_profile, cleaned_df, rec_context)

    st.session_state["raw_df"] = raw_df
    st.session_state["cleaned_df"] = cleaned_df
    st.session_state["clean_profile"] = clean_profile
    st.session_state["cleaning_log"] = cleaning_log
    st.session_state["recommendations"] = recommendations
    st.session_state["uploaded_name"] = uploaded.name
    st.session_state["row_count"] = len(cleaned_df)
    st.session_state["col_count"] = cleaned_df.shape[1]
    st.session_state["cleaned_row_count"] = len(cleaned_df)
    st.session_state["filtered_df"] = cleaned_df.copy()
    st.session_state["data_loaded"] = True

    return True


def apply_filters():
    """Apply sidebar filters to the filtered_df. Called after navigation renders filters."""
    cleaned_df = st.session_state.get("cleaned_df")
    clean_profile = st.session_state.get("clean_profile")
    if cleaned_df is None or clean_profile is None:
        return

    df = cleaned_df.copy()
    cat_cols = clean_profile["categorical_columns"]
    date_cols = clean_profile["date_columns"]

    selected = {}
    for col in cat_cols[:4]:
        vals = sorted(df[col].dropna().astype(str).unique().tolist())
        if 1 < len(vals) <= 100:
            filter_key = f"filter_{col}"
            if filter_key in st.session_state:
                selected[col] = st.session_state[filter_key]

    if date_cols:
        dc = date_cols[0]
        df[dc] = pd.to_datetime(df[dc], errors="coerce")
        valid_dates = df[dc].dropna()
        if not valid_dates.empty:
            start, end = valid_dates.min().date(), valid_dates.max().date()
            date_range = st.date_input("Date range", value=(start, end), min_value=start, max_value=end,
                                       key="sidebar_date_range")
            if isinstance(date_range, tuple) and len(date_range) == 2:
                df = df[df[dc].dt.date.between(date_range[0], date_range[1])]

    if selected:
        for col, vals in selected.items():
            if vals:
                df = df[df[col].astype(str).isin(vals)]

    st.session_state["filtered_df"] = df


def main():
    init_session_state()
    mode = st.session_state["theme_mode"]

    # Inject CSS
    st.markdown(inject_css(mode), unsafe_allow_html=True)

    # Check for uploaded file
    uploaded = st.session_state.get("uploaded_file")
    if uploaded is not None and not st.session_state.get("data_loaded", False):
        if load_data(uploaded):
            st.session_state["uploaded_file"] = None
            st.rerun()

    has_data = st.session_state.get("data_loaded", False)

    # Render sidebar (handles upload when no data, nav + filters when data loaded)
    # We need a custom sidebar approach since Streamlit's sidebar is special
    with st.sidebar:
        from src.ui.theme import logo_wordmark
        st.markdown(logo_wordmark(36, 36, mode), unsafe_allow_html=True)
        st.markdown("---")

        if not has_data:
            st.markdown("#### Upload Dataset")
            uploaded = st.file_uploader("Upload CSV / Excel", type=["csv", "xlsx", "xls"],
                                        label_visibility="collapsed")
            if uploaded is not None:
                st.session_state["uploaded_file"] = uploaded
                st.rerun()
        else:
            # Navigation
            from src.ui.navigation import NAV_SECTIONS, _nav_icon
            for section in NAV_SECTIONS:
                st.markdown(f'<div class="riq-nav-section">{section["label"]}</div>', unsafe_allow_html=True)
                for item in section["items"]:
                    is_active = st.session_state["current_page"] == item["id"]
                    if st.button(
                        item["label"],
                        key=f"nav_{item['id']}",
                        use_container_width=True,
                    ):
                        st.session_state["current_page"] = item["id"]
                        st.rerun()

            st.markdown("---")

            # Theme toggle
            toggle_col1, toggle_col2 = st.columns([3, 1])
            with toggle_col1:
                st.caption("Theme")
            with toggle_col2:
                if st.button("🌙" if mode == "dark" else "☀️", key="theme_toggle"):
                    st.session_state["theme_mode"] = "light" if mode == "dark" else "dark"
                    st.rerun()

            st.markdown("---")

            # File info
            st.success(f"Loaded: {st.session_state.get('uploaded_name', '')}")
            st.caption(f"{st.session_state.get('row_count', 0):,} rows · {st.session_state.get('col_count', 0):,} columns")

            st.markdown("---")

            # Dashboard filters
            st.markdown("#### Dashboard Filters")
            apply_filters()
            st.caption(f"Showing {len(st.session_state.get('filtered_df', pd.DataFrame())):,} of {st.session_state.get('cleaned_row_count', 0):,} rows")

            st.markdown("---")

            # Upload new file
            new_upload = st.file_uploader("Upload new dataset", type=["csv", "xlsx", "xls"],
                                          label_visibility="collapsed")
            if new_upload is not None:
                st.session_state["data_loaded"] = False
                st.session_state["uploaded_file"] = new_upload
                st.rerun()

    # Main content area
    if not has_data:
        render_landing(mode)
        return

    # Get data from session state
    df = st.session_state.get("filtered_df")
    clean_profile = st.session_state.get("clean_profile")
    cleaning_log = st.session_state.get("cleaning_log")
    raw_df = st.session_state.get("raw_df")
    cleaned_df = st.session_state.get("cleaned_df")
    uploaded_name = st.session_state.get("uploaded_name", "dataset")

    if df is None or clean_profile is None:
        st.error("Dataset could not be loaded. Please re-upload your file.")
        return

    num_cols = clean_profile["numeric_columns"]
    cat_cols = clean_profile["categorical_columns"]
    date_cols = clean_profile["date_columns"]
    metric = choose_metric(num_cols, df=df)
    dimension = choose_dimension(df)
    other_num = [c for c in num_cols if c != metric]
    second_metric = other_num[0] if other_num else None

    selected_target = st.session_state.get("selected_target")
    resolved_task = st.session_state.get("resolved_task")

    page = st.session_state["current_page"]

    if page == "dashboard":
        render_dashboard(df, clean_profile, mode, metric, dimension, date_cols, num_cols, cat_cols, second_metric)

    elif page == "data":
        render_data(df, clean_profile, mode, uploaded_name)

    elif page == "data_quality":
        render_data_quality(df, clean_profile, cleaning_log, raw_df, cleaned_df, mode)

    elif page == "breakdown":
        render_breakdown(df, clean_profile, mode, metric, dimension)

    elif page == "relationships":
        render_relationships(df, clean_profile, mode, metric)

    elif page == "classification":
        result_target, result_task = render_classification(df, clean_profile, mode, selected_target, resolved_task)
        if result_target is not None:
            st.session_state["selected_target"] = result_target
        if result_task is not None:
            st.session_state["resolved_task"] = result_task

    elif page == "regression":
        result_target, result_task = render_regression(df, clean_profile, mode, selected_target, resolved_task)
        if result_target is not None:
            st.session_state["selected_target"] = result_target
        if result_task is not None:
            st.session_state["resolved_task"] = result_task

    elif page == "clustering":
        render_clustering(df, clean_profile, mode, selected_target)

    elif page == "forecasting":
        render_forecasting(df, clean_profile, mode, metric, date_cols, num_cols)

    elif page == "anomaly":
        render_anomaly(df, clean_profile, mode, selected_target)

    elif page == "recommendations":
        render_recommendations(df, clean_profile, mode, selected_target, resolved_task, date_cols, metric)

    elif page == "research":
        render_research(df, clean_profile, mode)

    else:
        st.session_state["current_page"] = "dashboard"
        st.rerun()


if __name__ == "__main__":
    main()
