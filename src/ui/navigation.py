"""RetailIQ sidebar navigation — collapsible, icon-based, grouped sections."""

import streamlit as st

from .theme import logo_wordmark, get_theme

NAV_SECTIONS = [
    {
        "label": "MAIN",
        "items": [
            {"id": "dashboard", "label": "Dashboard", "icon": "house"},
            {"id": "data", "label": "Data", "icon": "table"},
            {"id": "data_quality", "label": "Data Quality", "icon": "shield"},
        ],
    },
    {
        "label": "ANALYTICS",
        "items": [
            {"id": "breakdown", "label": "Breakdown", "icon": "bar-chart"},
            {"id": "relationships", "label": "Relationships", "icon": "scatter"},
        ],
    },
    {
        "label": "ML STUDIO",
        "items": [
            {"id": "classification", "label": "Classification", "icon": "tags"},
            {"id": "regression", "label": "Regression", "icon": "trending-up"},
            {"id": "clustering", "label": "Clustering", "icon": "circles"},
            {"id": "forecasting", "label": "Forecasting", "icon": "clock"},
            {"id": "anomaly", "label": "Anomaly Detection", "icon": "alert"},
        ],
    },
    {
        "label": "INSIGHTS",
        "items": [
            {"id": "recommendations", "label": "Recommendations", "icon": "lightbulb"},
        ],
    },
    {
        "label": "RESEARCH",
        "items": [
            {"id": "research", "label": "Research Evaluation", "icon": "flask"},
        ],
    },
]

ALL_PAGES = [item["id"] for sec in NAV_SECTIONS for item in sec["items"]]


def _nav_icon(icon: str) -> str:
    """Return a simple SVG icon string for navigation."""
    icons = {
        "house": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>',
        "table": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="3" y1="15" x2="21" y2="15"/><line x1="12" y1="3" x2="12" y2="21"/></svg>',
        "shield": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
        "bar-chart": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="20" x2="12" y2="10"/><line x1="18" y1="20" x2="18" y2="4"/><line x1="6" y1="20" x2="6" y2="16"/></svg>',
        "scatter": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="6" cy="18" r="2"/><circle cx="10" cy="10" r="2"/><circle cx="18" cy="6" r="2"/><circle cx="14" cy="14" r="2"/><circle cx="18" cy="18" r="2"/></svg>',
        "tags": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/><line x1="7" y1="7" x2="7.01" y2="7"/></svg>',
        "trending-up": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>',
        "circles": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="4"/></svg>',
        "clock": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
        "alert": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
        "lightbulb": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18h6"/><path d="M10 22h4"/><path d="M15.09 14c.18-.98.65-1.74 1.41-2.5A4.65 4.65 0 0 0 18 8 6 6 0 0 0 6 8c0 1 .23 2.23 1.5 3.5A4.61 4.61 0 0 1 8.91 14"/></svg>',
        "flask": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 3h6"/><path d="M10 3v6L4 20a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1l-6-11V3"/></svg>',
    }
    return icons.get(icon, icons["house"])


def render_sidebar(mode: str, current_page: str, has_data: bool):
    """Render the full sidebar with logo, navigation, theme toggle, and filters."""
    t = get_theme(mode)

    with st.sidebar:
        # Logo
        st.markdown(logo_wordmark(36, 36, mode), unsafe_allow_html=True)
        st.markdown("---")

        if has_data:
            # Navigation
            for section in NAV_SECTIONS:
                st.markdown(f'<div class="riq-nav-section">{section["label"]}</div>', unsafe_allow_html=True)
                for item in section["items"]:
                    active = item["id"] == current_page
                    active_cls = "active" if active else ""
                    icon_svg = _nav_icon(item["icon"])
                    color = t["primary"] if active else t["muted"]
                    if st.button(
                        f"{item['label']}",
                        key=f"nav_{item['id']}",
                        use_container_width=True,
                        help=item["label"],
                    ):
                        st.session_state["current_page"] = item["id"]
                        st.rerun()
                    # Apply active styling via CSS hack — Streamlit buttons don't support custom classes
                    if active:
                        st.markdown(
                            f"""<style>
                            div[data-testid="stButton"] button[kind="secondary"] {{
                                background: rgba(99,102,241,0.12) !important;
                                color: {t['primary']} !important;
                                font-weight: 600 !important;
                                border: none !important;
                            }}
                            </style>""",
                            unsafe_allow_html=True,
                        )

            st.markdown("---")

            # Theme toggle
            col1, col2 = st.columns([3, 1])
            with col1:
                st.caption("Theme")
            with col2:
                if st.button("🌙" if mode == "dark" else "☀️", key="theme_toggle", help="Toggle dark/light mode"):
                    st.session_state["theme_mode"] = "light" if mode == "dark" else "dark"
                    st.rerun()

            st.markdown("---")

            # File info
            if "uploaded_name" in st.session_state:
                st.success(f"Loaded: {st.session_state['uploaded_name']}")
                st.caption(f"{st.session_state.get('row_count', 0):,} rows · {st.session_state.get('col_count', 0):,} columns")

            st.markdown("---")

            # Dashboard filters
            st.markdown("#### Dashboard Filters")
            _render_filters()
        else:
            # No data — just show upload
            st.markdown("#### Upload Dataset")
            uploaded = st.file_uploader(
                "Upload CSV / Excel",
                type=["csv", "xlsx", "xls"],
                label_visibility="collapsed",
            )
            if uploaded is not None:
                st.session_state["uploaded_file"] = uploaded
                st.rerun()


def _render_filters():
    """Render dashboard filter widgets in the sidebar. Does not apply filtering —
    app.py's apply_filters() reads the widget keys after rendering."""
    df = st.session_state.get("cleaned_df")
    clean_profile = st.session_state.get("clean_profile")
    if df is None or clean_profile is None:
        return

    cat_cols = clean_profile["categorical_columns"]
    date_cols = clean_profile["date_columns"]

    for col in cat_cols[:4]:
        vals = sorted(df[col].dropna().astype(str).unique().tolist())
        if 1 < len(vals) <= 100:
            st.multiselect(
                col.replace("_", " ").title(),
                vals,
                default=vals,
                key=f"filter_{col}",
            )

    if date_cols:
        dc = date_cols[0]
        temp = df.copy()
        temp[dc] = pd.to_datetime(temp[dc], errors="coerce")
        valid_dates = temp[dc].dropna()
        if not valid_dates.empty:
            start, end = valid_dates.min().date(), valid_dates.max().date()
            st.date_input("Date range", value=(start, end), min_value=start, max_value=end,
                           key="sidebar_date_range")
