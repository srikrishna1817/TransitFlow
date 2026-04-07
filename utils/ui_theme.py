import streamlit as st

def get_custom_css():
    """Returns custom CSS strings for HMRL Branding injection"""
    return """
    <style>
        /* Base Spacing and Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }
        
        /* Brand Colors */
        :root {
            --hmrl-primary: #0066CC;
            --hmrl-secondary: #00CC66;
            --hmrl-accent: #FF6B35;
            --hmrl-bg-light: #f8f9fa;
        }

        /* Metric Cards */
        .hmrl-metric-card {
            background-color: white;
            border-left: 5px solid var(--hmrl-primary);
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            margin-bottom: 15px;
            transition: transform 0.2s;
        }
        .hmrl-metric-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.1);
        }
        .hmrl-metric-title {
            color: #6c757d;
            font-size: 0.9rem;
            text-transform: uppercase;
            font-weight: 600;
            margin-bottom: 5px;
        }
        .hmrl-metric-value {
            font-size: 2rem;
            font-weight: 700;
            color: #212529;
            margin-bottom: 0px;
            line-height: 1;
        }
        
        /* Status Badges */
        .hmrl-badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .hmrl-badge.Critical { background-color: #ffebee; color: #c62828; }
        .hmrl-badge.High { background-color: #fff3e0; color: #ef6c00; }
        .hmrl-badge.Medium { background-color: #fff8e1; color: #f9a825; }
        .hmrl-badge.Low { background-color: #e8f5e9; color: #2e7d32; }
        .hmrl-badge.Success { background-color: #e8f5e9; color: var(--hmrl-secondary); }

        /* Tables */
        .dataframe {
            border: none !important;
        }
        .dataframe th {
            background-color: var(--hmrl-bg-light) !important;
            color: #495057 !important;
            font-weight: 600 !important;
            border-bottom: 2px solid #dee2e6 !important;
        }
        .dataframe td {
            border-bottom: 1px solid #dee2e6 !important;
            padding: 12px 15px !important;
        }
        
        /* Mobile responsive hides */
        @media (max-width: 768px) {
            .hide-on-mobile { display: none !important; }
        }
    </style>
    """

def apply_theme():
    """Wrapper function to inject theme directly into st"""
    st.markdown(get_custom_css(), unsafe_allow_html=True)
