"""RetailIQ theme system — CSS, colors, logo, chart styling."""

DARK = {
    "bg": "#0F172A",
    "surface": "#1F2937",
    "surface_alt": "#111827",
    "border": "#374151",
    "text": "#E2E8F0",
    "muted": "#94A3B8",
    "primary": "#6366F1",
    "cyan": "#06B6D4",
    "orange": "#F59E0B",
    "green": "#22C55E",
    "red": "#EF4444",
    "pink": "#F472B6",
    "plotly_template": "plotly_dark",
}

LIGHT = {
    "bg": "#F8FAFC",
    "surface": "#FFFFFF",
    "surface_alt": "#F1F5F9",
    "border": "#E2E8F0",
    "text": "#0F172A",
    "muted": "#64748B",
    "primary": "#6366F1",
    "cyan": "#0891B2",
    "orange": "#D97706",
    "green": "#16A34A",
    "red": "#DC2626",
    "pink": "#DB2777",
    "plotly_template": "plotly_white",
}

MODULE_COLORS = {
    "dashboard": "cyan",
    "data": "primary",
    "data_quality": "orange",
    "breakdown": "primary",
    "relationships": "cyan",
    "classification": "primary",
    "regression": "cyan",
    "clustering": "pink",
    "forecasting": "orange",
    "anomaly": "red",
    "recommendations": "green",
    "research": "cyan",
}


def get_theme(mode: str) -> dict:
    return DARK if mode == "dark" else LIGHT


def logo_svg(width: int = 36, height: int = 36) -> str:
    """RetailIQ logo — a stylized bar-chart + brain/spark hybrid conveying retail analytics intelligence."""
    return f'''<svg width="{width}" height="{height}" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="riq-grad" x1="0" y1="0" x2="48" y2="48">
      <stop offset="0%" stop-color="#6366F1"/>
      <stop offset="100%" stop-color="#06B6D4"/>
    </linearGradient>
  </defs>
  <rect x="2" y="2" width="44" height="44" rx="12" fill="url(#riq-grad)" opacity="0.15"/>
  <rect x="2" y="2" width="44" height="44" rx="12" stroke="url(#riq-grad)" stroke-width="1.5"/>
  <rect x="11" y="26" width="5" height="12" rx="2" fill="#6366F1"/>
  <rect x="20" y="20" width="5" height="18" rx="2" fill="#06B6D4"/>
  <rect x="29" y="14" width="5" height="24" rx="2" fill="#F59E0B"/>
  <path d="M38 10 L41 13 L44 10" stroke="#22C55E" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
  <circle cx="42" cy="8" r="2.5" fill="#22C55E"/>
</svg>'''


def logo_wordmark(width: int = 36, height: int = 36, mode: str = "dark") -> str:
    """Logo + wordmark for sidebar header."""
    t = get_theme(mode)
    logo = logo_svg(width, height)
    return f'''<div style="display:flex;align-items:center;gap:10px;">
  {logo}
  <div>
    <div style="font-size:1.25rem;font-weight:700;letter-spacing:-0.02em;color:{t['text']};line-height:1.1;">RetailIQ</div>
    <div style="font-size:0.65rem;color:{t['muted']};letter-spacing:0.08em;text-transform:uppercase;">Analytics Platform</div>
  </div>
</div>'''


def inject_css(mode: str) -> str:
    """Return the full CSS block for the given theme mode."""
    t = get_theme(mode)
    is_dark = mode == "dark"
    card_bg = t["surface"]
    card_border = t["border"]
    hover_bg = t["surface_alt"]
    text = t["text"]
    muted = t["muted"]
    bg = t["bg"]
    glass_bg = "rgba(31,41,55,0.65)" if is_dark else "rgba(255,255,255,0.75)"
    glass_border = f"1px solid {card_border}"
    shadow = "0 4px 24px rgba(0,0,0,0.25)" if is_dark else "0 2px 12px rgba(0,0,0,0.08)"
    sidebar_bg = "#0B1120" if is_dark else "#FFFFFF"
    sidebar_border = "#1E293B" if is_dark else "#E2E8F0"

    return f"""
    <style>
    /* ===== RetailIQ Global Theme ===== */
    .stApp {{
        background: {bg};
        color: {text};
    }}

    /* Main content area */
    .block-container {{
        padding-top: 1.5rem;
        padding-bottom: 3rem;
        max-width: 1480px;
    }}

    /* Typography */
    h1, h2, h3, h4, h5, h6, p, span, div, li, td, th {{
        color: {text};
    }}
    .small-muted, .caption {{
        color: {muted} !important;
    }}

    /* ===== Sidebar ===== */
    section[data-testid="stSidebar"] {{
        background: {sidebar_bg};
        border-right: 1px solid {sidebar_border};
    }}
    section[data-testid="stSidebar"] .stMarkdown {{
        color: {muted};
    }}

    /* ===== Cards ===== */
    .riq-card {{
        background: {card_bg};
        border: 1px solid {card_border};
        border-radius: 14px;
        padding: 20px 22px;
        margin-bottom: 16px;
        transition: border-color 0.2s ease, box-shadow 0.2s ease;
    }}
    .riq-card:hover {{
        border-color: {t['primary']};
        box-shadow: {shadow};
    }}
    .riq-glass {{
        background: {glass_bg};
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: {glass_border};
        border-radius: 14px;
        padding: 20px 22px;
        margin-bottom: 16px;
        box-shadow: {shadow};
    }}

    /* ===== KPI Cards ===== */
    div[data-testid="stMetric"] {{
        background: {card_bg};
        border: 1px solid {card_border};
        border-radius: 12px;
        padding: 16px 18px;
        transition: border-color 0.2s ease;
    }}
    div[data-testid="stMetric"]:hover {{
        border-color: {t['primary']};
    }}
    div[data-testid="stMetricLabel"] {{
        color: {muted};
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        font-weight: 600;
    }}
    div[data-testid="stMetricValue"] {{
        font-size: 1.6rem;
        font-weight: 700;
        color: {text};
    }}
    div[data-testid="stMetricDelta"] {{
        font-size: 0.82rem;
    }}

    /* KPI accent variants */
    .riq-kpi {{
        background: {card_bg};
        border: 1px solid {card_border};
        border-radius: 12px;
        padding: 18px 20px;
        position: relative;
        overflow: hidden;
        transition: border-color 0.2s ease, transform 0.15s ease;
    }}
    .riq-kpi:hover {{
        transform: translateY(-2px);
        box-shadow: {shadow};
    }}
    .riq-kpi::before {{
        content: '';
        position: absolute;
        left: 0; top: 0; bottom: 0;
        width: 4px;
        border-radius: 12px 0 0 12px;
    }}
    .riq-kpi-accent-cyan::before {{ background: {t['cyan']}; }}
    .riq-kpi-accent-primary::before {{ background: {t['primary']}; }}
    .riq-kpi-accent-orange::before {{ background: {t['orange']}; }}
    .riq-kpi-accent-green::before {{ background: {t['green']}; }}
    .riq-kpi-accent-red::before {{ background: {t['red']}; }}
    .riq-kpi-accent-pink::before {{ background: {t['pink']}; }}
    .riq-kpi-label {{
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 600;
        color: {muted};
        margin-bottom: 6px;
    }}
    .riq-kpi-value {{
        font-size: 1.7rem;
        font-weight: 700;
        color: {text};
        line-height: 1.2;
    }}
    .riq-kpi-sub {{
        font-size: 0.78rem;
        color: {muted};
        margin-top: 4px;
    }}

    /* ===== Page header ===== */
    .riq-page-header {{
        margin-bottom: 24px;
    }}
    .riq-page-title {{
        font-size: 1.75rem;
        font-weight: 700;
        color: {text};
        letter-spacing: -0.02em;
        line-height: 1.2;
    }}
    .riq-page-desc {{
        font-size: 0.92rem;
        color: {muted};
        margin-top: 6px;
        line-height: 1.5;
    }}
    .riq-page-accent {{
        height: 3px;
        width: 48px;
        border-radius: 3px;
        margin-bottom: 14px;
    }}

    /* ===== Section headers ===== */
    .riq-section-header {{
        font-size: 1.05rem;
        font-weight: 600;
        color: {text};
        margin-bottom: 12px;
        margin-top: 8px;
    }}

    /* ===== Recommendation cards ===== */
    .riq-rec-card {{
        background: {card_bg};
        border: 1px solid {card_border};
        border-radius: 12px;
        padding: 18px 20px;
        margin-bottom: 12px;
        cursor: pointer;
        transition: border-color 0.2s ease, transform 0.15s ease;
    }}
    .riq-rec-card:hover {{
        border-color: {t['green']};
        transform: translateY(-1px);
        box-shadow: {shadow};
    }}
    .riq-rec-priority {{
        display: inline-block;
        font-size: 0.68rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        padding: 3px 10px;
        border-radius: 20px;
        margin-bottom: 8px;
    }}
    .riq-priority-high {{ background: rgba(239,68,68,0.15); color: {t['red']}; }}
    .riq-priority-medium {{ background: rgba(245,158,11,0.15); color: {t['orange']}; }}
    .riq-priority-low {{ background: rgba(34,197,94,0.15); color: {t['green']}; }}
    .riq-priority-info {{ background: rgba(99,102,241,0.15); color: {t['primary']}; }}

    /* ===== Upload zone ===== */
    .riq-upload-zone {{
        border: 2px dashed {card_border};
        border-radius: 16px;
        padding: 48px 32px;
        text-align: center;
        transition: border-color 0.2s ease, background 0.2s ease;
        background: {card_bg};
    }}

    /* ===== Insight cards ===== */
    .riq-insight-card {{
        background: {card_bg};
        border: 1px solid {card_border};
        border-left: 3px solid {t['cyan']};
        border-radius: 10px;
        padding: 14px 18px;
        margin-bottom: 10px;
        font-size: 0.9rem;
        line-height: 1.55;
        color: {text};
    }}

    /* ===== Tables ===== */
    .stDataFrame {{
        border-radius: 10px;
        overflow: hidden;
    }}
    .stDataFrame [data-testid="stDataFrameResizable"] {{
        border: 1px solid {card_border};
        border-radius: 10px;
    }}

    /* ===== Buttons ===== */
    .stButton > button {{
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.15s ease;
    }}
    .stButton > button:hover {{
        transform: translateY(-1px);
    }}

    /* ===== Expanders ===== */
    .stExpander {{
        border: 1px solid {card_border};
        border-radius: 12px;
        background: {card_bg};
    }}

    /* ===== Dividers ===== */
    .stDivider > hr {{
        border-color: {card_border};
    }}

    /* ===== Selectbox / Input styling ===== */
    .stSelectbox > div > div {{
        border-radius: 8px;
    }}

    /* ===== Animations ===== */
    @keyframes riq-fade-in {{
        from {{ opacity: 0; transform: translateY(8px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    .riq-fade-in {{
        animation: riq-fade-in 0.3s ease-out;
    }}

    /* ===== Scrollbar ===== */
    ::-webkit-scrollbar {{
        width: 8px;
        height: 8px;
    }}
    ::-webkit-scrollbar-track {{
        background: {bg};
    }}
    ::-webkit-scrollbar-thumb {{
        background: {card_border};
        border-radius: 4px;
    }}
    ::-webkit-scrollbar-thumb:hover {{
        background: {muted};
    }}

    /* ===== Sidebar nav items ===== */
    .riq-nav-section {{
        font-size: 0.65rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: {muted};
        padding: 16px 0 6px 0;
    }}
    .riq-nav-item {{
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 8px 12px;
        border-radius: 8px;
        color: {muted};
        font-size: 0.88rem;
        font-weight: 500;
        transition: background 0.15s ease, color 0.15s ease;
        cursor: pointer;
        text-decoration: none;
    }}
    .riq-nav-item:hover {{
        background: {hover_bg};
        color: {text};
    }}
    .riq-nav-item.active {{
        background: rgba(99,102,241,0.12);
        color: {t['primary']};
        font-weight: 600;
    }}

    /* ===== Badge ===== */
    .riq-badge {{
        display: inline-block;
        font-size: 0.68rem;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 6px;
        letter-spacing: 0.02em;
    }}
    .riq-badge-cyan {{ background: rgba(6,182,212,0.15); color: {t['cyan']}; }}
    .riq-badge-primary {{ background: rgba(99,102,241,0.15); color: {t['primary']}; }}
    .riq-badge-orange {{ background: rgba(245,158,11,0.15); color: {t['orange']}; }}
    .riq-badge-green {{ background: rgba(34,197,94,0.15); color: {t['green']}; }}
    .riq-badge-red {{ background: rgba(239,68,68,0.15); color: {t['red']}; }}
    .riq-badge-pink {{ background: rgba(244,114,182,0.15); color: {t['pink']}; }}

    /* ===== Theme toggle ===== */
    .riq-theme-toggle {{
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 6px 12px;
        border-radius: 8px;
        border: 1px solid {card_border};
        background: {card_bg};
        cursor: pointer;
        font-size: 0.82rem;
        color: {muted};
        transition: border-color 0.15s ease;
    }}
    .riq-theme-toggle:hover {{
        border-color: {t['primary']};
    }}

    /* ===== Empty state ===== */
    .riq-empty {{
        text-align: center;
        padding: 40px 20px;
        color: {muted};
    }}
    .riq-empty-icon {{
        font-size: 2.5rem;
        margin-bottom: 12px;
        opacity: 0.5;
    }}
    </style>
    """


def make_chart(fig, mode: str = "dark", height: int = 380):
    """Apply consistent RetailIQ chart styling."""
    t = get_theme(mode)
    fig.update_layout(
        template=t["plotly_template"],
        height=height,
        margin=dict(l=10, r=10, t=50, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=t["text"], size=12),
        legend_title_text="",
        hoverlabel=dict(bgcolor=t["surface"], bordercolor=t["border"], font_color=t["text"]),
    )
    fig.update_xaxes(gridcolor=t["border"], zerolinecolor=t["border"])
    fig.update_yaxes(gridcolor=t["border"], zerolinecolor=t["border"])
    return fig
