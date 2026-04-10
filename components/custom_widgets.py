import streamlit as st

def metric_card(title: str, value: str, delta: str = None, color_indicator: str = "#3B9EFF"):
    """Renders a dark-mode HMRL-branded metric card."""
    delta_html = ""
    if delta:
        if str(delta).startswith("-"):
            delta_html = f"<span style='color:#F87171;font-size:0.82rem;padding-left:10px;font-weight:600;'>↓ {delta}</span>"
        else:
            delta_html = f"<span style='color:#34D399;font-size:0.82rem;padding-left:10px;font-weight:600;'>↑ {delta}</span>"

    html = f"""
    <div class="hmrl-metric-card" style="border-left-color: {color_indicator};">
        <div class="hmrl-metric-title">{title}</div>
        <div class="hmrl-metric-value">{value} {delta_html}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def status_badge(status: str):
    """Renders a dark-mode-safe color-coded status pill."""
    valid_classes = ['Critical', 'High', 'Medium', 'Low', 'Success']
    css_class = status if status in valid_classes else 'Medium'
    html = f"<span class='hmrl-badge {css_class}'>{status}</span>"
    st.markdown(html, unsafe_allow_html=True)

def breadcrumb(path_array):
    """Renders a navigation breadcrumb e.g. Home > Schedule > Editor (dark-mode safe)."""
    path_str = " <span style='color:#475569;'>&gt;</span> ".join([
        f"<b style='color:#E2E8F0;'>{p}</b>" if i == len(path_array) - 1
        else f"<span style='color:#3B9EFF;cursor:pointer;'>{p}</span>"
        for i, p in enumerate(path_array)
    ])
    st.markdown(f"<div style='margin-bottom:1rem;font-size:0.88rem;'>{path_str}</div>", unsafe_allow_html=True)

def loading_overlay(message="Optimizing System Data..."):
    """Displays a branded loading spinner container."""
    with st.spinner(f"⏳ {message}"):
        pass
