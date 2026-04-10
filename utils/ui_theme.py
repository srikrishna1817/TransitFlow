import streamlit as st

def get_custom_css():
    """Returns custom CSS strings for HMRL Branding injection — Dark-mode optimised."""
    return """
    <style>
        /* ── Fonts ─────────────────────────────────────────────── */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        /* ── Design Tokens (dark-mode palette) ─────────────────── */
        :root {
            --hmrl-primary:        #3B9EFF;   /* vibrant sky-blue   */
            --hmrl-primary-dim:    #1a3a5c;   /* deep blue panel bg */
            --hmrl-secondary:      #34D399;   /* emerald green      */
            --hmrl-accent:         #FB923C;   /* warm orange        */
            --hmrl-critical:       #F87171;   /* soft red           */
            --hmrl-warning:        #FBBF24;   /* amber              */
            --hmrl-info:           #60A5FA;   /* light blue         */
            --hmrl-success:        #34D399;   /* emerald            */

            /* Surface colours */
            --hmrl-bg-card:        #1E2535;   /* card background    */
            --hmrl-bg-card-hover:  #263044;   /* card hover         */
            --hmrl-border:         #2D3A50;   /* subtle border      */
            --hmrl-text-primary:   #E2E8F0;   /* almost-white text  */
            --hmrl-text-secondary: #94A3B8;   /* muted slate        */
            --hmrl-text-value:     #F1F5F9;   /* metric values      */
        }

        /* ── Metric Cards ───────────────────────────────────────── */
        .hmrl-metric-card {
            background-color: var(--hmrl-bg-card);
            border-left: 4px solid var(--hmrl-primary);
            padding: 18px 20px;
            border-radius: 10px;
            box-shadow: 0 4px 16px rgba(0,0,0,0.35);
            margin-bottom: 14px;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .hmrl-metric-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 24px rgba(0,0,0,0.45);
            background-color: var(--hmrl-bg-card-hover);
        }
        .hmrl-metric-title {
            color: var(--hmrl-text-secondary);
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            font-weight: 600;
            margin-bottom: 6px;
        }
        .hmrl-metric-value {
            font-size: 2rem;
            font-weight: 700;
            color: var(--hmrl-text-value);
            line-height: 1.1;
        }

        /* ── Status Badges (dark-mode safe) ─────────────────────── */
        .hmrl-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.6px;
        }
        .hmrl-badge.Critical  { background-color: rgba(248,113,113,0.2); color: #F87171; border: 1px solid rgba(248,113,113,0.4); }
        .hmrl-badge.High      { background-color: rgba(251,191,36,0.15); color: #FBBF24; border: 1px solid rgba(251,191,36,0.35); }
        .hmrl-badge.Medium    { background-color: rgba(251,191,36,0.10); color: #FCD34D; border: 1px solid rgba(251,191,36,0.25); }
        .hmrl-badge.Low       { background-color: rgba(52,211,153,0.15); color: #34D399; border: 1px solid rgba(52,211,153,0.35); }
        .hmrl-badge.Success   { background-color: rgba(52,211,153,0.15); color: #34D399; border: 1px solid rgba(52,211,153,0.35); }

        /* ── Tables ─────────────────────────────────────────────── */
        .dataframe {
            border: none !important;
        }
        .dataframe th {
            background-color: #1a2236 !important;
            color: var(--hmrl-text-secondary) !important;
            font-weight: 600 !important;
            border-bottom: 2px solid var(--hmrl-border) !important;
            letter-spacing: 0.4px;
            font-size: 0.82rem;
            text-transform: uppercase;
        }
        .dataframe td {
            border-bottom: 1px solid var(--hmrl-border) !important;
            color: var(--hmrl-text-primary) !important;
            padding: 10px 14px !important;
        }
        .dataframe tr:hover td {
            background-color: var(--hmrl-bg-card-hover) !important;
        }

        /* ── Mobile Responsive ──────────────────────────────────── */
        @media (max-width: 768px) {
            .hide-on-mobile { display: none !important; }
        }
    </style>
    """

def apply_theme():
    """Wrapper function to inject theme directly into st"""
    st.markdown(get_custom_css(), unsafe_allow_html=True)
