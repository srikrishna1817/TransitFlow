import streamlit as st

def metric_card(title: str, value: str, delta: str = None, color_indicator: str = "#3B82F6"):
    """Renders a premium glassmorphism metric card."""
    delta_html = ""
    if delta:
        if str(delta).startswith("-"):
            delta_html = f"<span style='color:#EF4444;font-size:1rem;margin-left:12px;font-weight:600;text-shadow: 0 0 10px rgba(239,68,68,0.4);'>↓ {delta}</span>"
        else:
            delta_html = f"<span style='color:#10B981;font-size:1rem;margin-left:12px;font-weight:600;text-shadow: 0 0 10px rgba(16,185,129,0.4);'>↑ {delta}</span>"

    html = f"""
    <div class="hmrl-metric-card" style="--card-color: {color_indicator};">
        <div class="hmrl-metric-title">{title}</div>
        <div class="hmrl-metric-value">{value} {delta_html}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def status_badge(status: str):
    """Renders a glowing color-coded status pill."""
    valid_classes = ['Critical', 'High', 'Medium', 'Low', 'Success']
    css_class = status if status in valid_classes else 'Medium'
    html = f"<span class='hmrl-badge {css_class}'>{status}</span>"
    st.markdown(html, unsafe_allow_html=True)

def breadcrumb(path_array):
    """Renders a modern glowing navigation breadcrumb."""
    path_str = " <span style='color:#475569;margin:0 8px;'>/</span> ".join([
        f"<b style='color:#F8FAFC;text-shadow: 0 0 10px rgba(255,255,255,0.3);'>{p}</b>" if i == len(path_array) - 1
        else f"<span style='color:#60A5FA;cursor:pointer;font-weight:500;transition:color 0.2s;' onmouseover='this.style.color=\"#3B82F6\"' onmouseout='this.style.color=\"#60A5FA\"'>{p}</span>"
        for i, p in enumerate(path_array)
    ])
    st.markdown(f"<div style='margin-bottom:1.5rem;font-size:0.9rem;background:rgba(15,23,42,0.4);display:inline-block;padding:8px 16px;border-radius:20px;border:1px solid rgba(255,255,255,0.05);'>{path_str}</div>", unsafe_allow_html=True)

def loading_overlay(message="Optimizing System Data..."):
    """Displays a branded loading spinner container."""
    with st.spinner(f"✨ {message}"):
        pass
