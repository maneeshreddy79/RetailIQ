"""RetailIQ reusable UI components."""

import streamlit as st
import pandas as pd
import numpy as np

from .theme import get_theme, MODULE_COLORS


def fmt_num(x):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "—"
    x = float(x)
    ax = abs(x)
    if ax >= 1_000_000_000:
        return f"{x/1_000_000_000:.2f}B"
    if ax >= 1_000_000:
        return f"{x/1_000_000:.2f}M"
    if ax >= 1_000:
        return f"{x/1_000:.1f}K"
    return f"{x:,.0f}" if x.is_integer() else f"{x:,.2f}"


def choose_metric(columns, df=None, target=None):
    """Select a semantically meaningful measure; never use an arbitrary feature as a KPI."""
    priority = ["sales", "revenue", "profit", "amount", "value", "total", "net_sales", "quantity", "demand"]
    lower = {str(c).lower(): c for c in columns}
    for key in priority:
        if key in lower:
            c = lower[key]
            if df is None or df[c].nunique(dropna=True) > 1:
                return c
    return None


def choose_dimension(df, exclude=None):
    exclude = set(exclude or [])
    cats = [c for c in df.select_dtypes(include=["object", "string", "category", "bool"]).columns if c not in exclude]
    ranked = []
    for c in cats:
        n = df[c].nunique(dropna=True)
        ratio = n / max(len(df), 1)
        if n >= 2 and ratio < 0.8:
            ranked.append((0 if n <= 30 else 1, n, c))
    if ranked:
        ranked.sort()
        return ranked[0][2]
    return cats[0] if cats else None


def page_header(title: str, description: str, accent: str = "cyan", mode: str = "dark"):
    """Render a page header with accent bar, title, and description."""
    t = get_theme(mode)
    color = t[accent] if accent in t else t["cyan"]
    st.markdown(
        f'<div class="riq-page-header riq-fade-in">'
        f'<div class="riq-page-accent" style="background:{color};"></div>'
        f'<div class="riq-page-title">{title}</div>'
        f'<div class="riq-page-desc">{description}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def kpi_card(label: str, value: str, sub: str = "", accent: str = "cyan", mode: str = "dark"):
    """Render a single KPI card with accent bar."""
    st.markdown(
        f'<div class="riq-kpi riq-kpi-accent-{accent}">'
        f'<div class="riq-kpi-label">{label}</div>'
        f'<div class="riq-kpi-value">{value}</div>'
        f'{"<div class=\"riq-kpi-sub\">" + sub + "</div>" if sub else ""}'
        f'</div>',
        unsafe_allow_html=True,
    )


def kpi_row(cards: list, mode: str = "dark"):
    """Render a row of KPI cards. Each card is dict(label, value, sub, accent)."""
    cols = st.columns(len(cards))
    for col, card in zip(cols, cards):
        with col:
            kpi_card(
                card["label"],
                card["value"],
                card.get("sub", ""),
                card.get("accent", "cyan"),
                mode,
            )


def card(title: str = "", body_html: str = "", mode: str = "dark", glass: bool = False):
    """Render a generic card."""
    cls = "riq-glass" if glass else "riq-card"
    title_html = f'<div class="riq-section-header">{title}</div>' if title else ""
    st.markdown(
        f'<div class="{cls}">{title_html}{body_html}</div>',
        unsafe_allow_html=True,
    )


def badge(text: str, color: str = "cyan"):
    """Render a small badge."""
    return f'<span class="riq-badge riq-badge-{color}">{text}</span>'


def empty_state(icon: str, message: str, mode: str = "dark"):
    """Render an empty state placeholder."""
    st.markdown(
        f'<div class="riq-empty"><div class="riq-empty-icon">{icon}</div><div>{message}</div></div>',
        unsafe_allow_html=True,
    )


def insight_card(text: str, mode: str = "dark"):
    """Render a natural-language insight card."""
    st.markdown(f'<div class="riq-insight-card">{text}</div>', unsafe_allow_html=True)


def recommendation_card(rec: dict, index: int, mode: str = "dark"):
    """Render a recommendation card with priority badge."""
    t = get_theme(mode)
    priority = str(rec.get("priority", ""))
    priority_lower = priority.lower()
    if "high" in priority_lower or "⚠" in priority:
        priority_cls = "riq-priority-high"
    elif "medium" in priority_lower:
        priority_cls = "riq-priority-medium"
    elif "low" in priority_lower:
        priority_cls = "riq-priority-low"
    else:
        priority_cls = "riq-priority-info"

    title = rec.get("title", "")
    desc = rec.get("description", "")
    why = rec.get("why", "")
    bv = rec.get("business_value", "")
    tools = rec.get("tools", "")
    question = rec.get("question", "")

    st.markdown(
        f'<div class="riq-rec-card">'
        f'<span class="riq-rec-priority {priority_cls}">{priority}</span>'
        f'<div style="font-size:1.05rem;font-weight:600;color:{t["text"]};margin-bottom:6px;">{title}</div>'
        f'<div style="font-size:0.9rem;color:{t["muted"]};line-height:1.5;margin-bottom:8px;">{desc}</div>'
        f'<div style="font-size:0.8rem;color:{t["muted"]};">'
        f'{"<strong>Why:</strong> " + why + "<br>" if why else ""}'
        f'{"<strong>Value:</strong> " + bv + "<br>" if bv else ""}'
        f'{"<strong>Tools:</strong> " + tools + "<br>" if tools else ""}'
        f'{"<strong>Question:</strong> " + question if question else ""}'
        f'</div></div>',
        unsafe_allow_html=True,
    )


def safe_metric_col_value(df, col):
    """Safely get a column value, returning None if column doesn't exist."""
    if col is None or col not in df.columns:
        return None
    return df[col]


def no_data_message(page_name: str):
    """Show a consistent no-data message for any page."""
    st.info(f"Upload a dataset to access the {page_name} page.")
