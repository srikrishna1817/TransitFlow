import streamlit as st

def get_custom_css():
    """Returns custom CSS strings for HMRL Branding injection — Premium Glassmorphism Theme."""
    return """
    <style>
        /* ── Fonts ─────────────────────────────────────────────── */
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');
        html, body, [class*="css"] {
            font-family: 'Outfit', sans-serif;
        }

        /* ── Premium Glassmorphism Tokens ─────────────────── */
        :root {
            --hmrl-primary:        #3B82F6;   /* Royal blue */
            --hmrl-secondary:      #10B981;   /* Emerald green */
            --hmrl-accent:         #8B5CF6;   /* Rich purple */
            --hmrl-critical:       #EF4444;   /* Crimson red */
            --hmrl-warning:        #F59E0B;   /* Amber */
            
            /* Glassmorphism Surfaces */
            --glass-bg:            rgba(15, 23, 42, 0.45);
            --glass-border:        rgba(255, 255, 255, 0.08);
            --glass-border-hover:  rgba(255, 255, 255, 0.15);
        }

        /* ── App Background Override ───────────────────────────── */
        .stApp {
            background: radial-gradient(circle at top right, #1E1B4B, #0F172A 40%, #020617 100%);
            background-attachment: fixed;
        }

        /* Hide the default Streamlit header and footer for a cleaner look */
        header {background: rgba(15,23,42,0.3) !important; backdrop-filter: blur(10px) !important;}
        footer {visibility: hidden;}

        /* ── Premium Glassmorphism Metric Cards ───────────────────────── */
        .hmrl-metric-card {
            background: var(--glass-bg);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid var(--glass-border);
            border-top: 1px solid rgba(255, 255, 255, 0.12);
            padding: 24px 28px;
            border-radius: 20px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
            margin-bottom: 20px;
            position: relative;
            overflow: hidden;
            transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
        }
        .hmrl-metric-card::before {
            content: '';
            position: absolute;
            top: 0; left: 0; width: 4px; height: 100%;
            background: var(--card-color, var(--hmrl-primary));
            box-shadow: 0 0 20px var(--card-color, var(--hmrl-primary));
        }
        .hmrl-metric-card:hover {
            transform: translateY(-6px);
            border-color: var(--glass-border-hover);
            box-shadow: 0 16px 40px 0 rgba(0, 0, 0, 0.5), inset 0 0 0 1px rgba(255,255,255,0.05);
            background: rgba(30, 41, 59, 0.6);
        }
        
        .hmrl-metric-title {
            color: #94A3B8;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            font-weight: 500;
            margin-bottom: 10px;
        }
        .hmrl-metric-value {
            font-size: 2.8rem;
            font-weight: 800;
            background: linear-gradient(180deg, #FFFFFF 0%, #94A3B8 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            line-height: 1.1;
            text-shadow: 0 4px 20px rgba(0,0,0,0.3);
            display: flex;
            align-items: baseline;
        }

        /* ── Dynamic Status Badges ─────────────────────── */
        .hmrl-badge {
            display: inline-block;
            padding: 6px 14px;
            border-radius: 30px;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            backdrop-filter: blur(4px);
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        }
        .hmrl-badge.Critical  { background: rgba(239,68,68,0.15); color: #EF4444; border: 1px solid rgba(239,68,68,0.4); box-shadow: 0 0 15px rgba(239,68,68,0.2); }
        .hmrl-badge.High      { background: rgba(245,158,11,0.15); color: #F59E0B; border: 1px solid rgba(245,158,11,0.4); box-shadow: 0 0 15px rgba(245,158,11,0.2); }
        .hmrl-badge.Medium    { background: rgba(59,130,246,0.15); color: #3B82F6; border: 1px solid rgba(59,130,246,0.4); box-shadow: 0 0 15px rgba(59,130,246,0.2); }
        .hmrl-badge.Success   { background: rgba(16,185,129,0.15); color: #10B981; border: 1px solid rgba(16,185,129,0.4); box-shadow: 0 0 15px rgba(16,185,129,0.2); }

        /* ── Tables Overhaul ─────────────────────────────────────────────── */
        .dataframe {
            border: none !important;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }
        .dataframe th {
            background-color: rgba(15,23,42,0.8) !important;
            color: #94A3B8 !important;
            font-weight: 600 !important;
            border-bottom: 2px solid rgba(255,255,255,0.1) !important;
            letter-spacing: 0.8px;
            font-size: 0.82rem;
            text-transform: uppercase;
            padding: 12px 16px !important;
        }
        .dataframe td {
            background-color: rgba(30,41,59,0.4) !important;
            border-bottom: 1px solid rgba(255,255,255,0.05) !important;
            color: #E2E8F0 !important;
            padding: 12px 16px !important;
        }
        .dataframe tr:hover td {
            background-color: rgba(59,130,246,0.15) !important;
        }

        /* ── Streamlit Buttons Overhaul ─────────────────────────────────── */
        .stButton>button {
            border-radius: 12px !important;
            font-weight: 600 !important;
            letter-spacing: 0.5px !important;
            transition: all 0.3s ease !important;
            border: 1px solid rgba(255,255,255,0.1) !important;
            background: rgba(30,41,59,0.6) !important;
            backdrop-filter: blur(8px) !important;
            color: white !important;
        }
        .stButton>button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba(0,0,0,0.4) !important;
            border-color: rgba(255,255,255,0.3) !important;
            background: rgba(59,130,246,0.2) !important;
        }
        .stButton>button[kind="primary"] {
            background: linear-gradient(135deg, #3B82F6 0%, #8B5CF6 100%) !important;
            border: none !important;
            box-shadow: 0 4px 15px rgba(59,130,246,0.4) !important;
        }
        .stButton>button[kind="primary"]:hover {
            box-shadow: 0 8px 25px rgba(59,130,246,0.6) !important;
            transform: translateY(-2px) scale(1.02) !important;
        }

        /* ── Action Panel Titles ───────────────────────────────────────── */
        .panel-title {
            font-size: 1.4rem;
            font-weight: 600;
            color: #F8FAFC;
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        
        .hero-banner {
            background: linear-gradient(135deg, rgba(15,23,42,0.8) 0%, rgba(30,27,75,0.8) 100%);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 24px;
            padding: 30px 40px;
            margin-bottom: 30px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.4);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .hero-title {
            font-size: 2.5rem;
            font-weight: 800;
            background: linear-gradient(to right, #60A5FA, #A78BFA);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin: 0 0 10px 0;
        }
        .hero-subtitle {
            color: #94A3B8;
            font-size: 1.1rem;
            font-weight: 400;
            margin: 0;
        }
    </style>
    """

def apply_theme():
    """Wrapper function to inject theme directly into st"""
    st.markdown(get_custom_css(), unsafe_allow_html=True)
