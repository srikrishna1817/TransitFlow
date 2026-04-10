import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import datetime
import calendar
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth.page_guard import require_auth
from auth.permissions import can_perform_action
from utils.analytics_utils import (
    forecast_fleet_health,
    predict_maintenance_calendar,
    calculate_cost_forecast,
    analyze_seasonal_patterns,
    generate_recommendations
)

st.set_page_config(page_title="Predictive Analytics", page_icon="📈", layout="wide")
user = require_auth('Predictive_Analytics')

st.title("📈 Predictive Analytics Hub")
st.markdown("Forecasts, trends, and seasonal optimization for Hyderabad Metro Rail fleet operations.")
st.divider()

# Cache heavy computations
@st.cache_data(ttl=3600)
def load_all_forecasts(cache_buster=5):
    health_data, slope = forecast_fleet_health(days_ahead=30)
    preds, daily, top_trains, top_failures = predict_maintenance_calendar(days_ahead=30)
    monthly, hist, fut, h_tot, f_tot, over_b, routes = calculate_cost_forecast(months_ahead=3)
    seasons, dow = analyze_seasonal_patterns()
    recs = generate_recommendations(slope, top_failures, over_b)
    return {
        'health_data': health_data, 'slope': slope,
        'preds': preds, 'daily': daily, 'top_trains': top_trains, 'top_failures': top_failures,
        'monthly': monthly, 'hist': hist, 'fut': fut, 'h_tot': h_tot, 'f_tot': f_tot, 'over_b': over_b, 'routes': routes,
        'seasons': seasons, 'dow': dow,
        'recs': recs
    }

with st.spinner("Crunching historical & predictive data..."):
    data = load_all_forecasts()

# Recommendations Banner
if data['recs']:
    st.info("💡 **AI Actionable Insights**")
    for rec in data['recs']:
        st.markdown(f"- {rec}")
    st.divider()

tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Fleet Health Trends", 
    "🔮 Maintenance Forecast", 
    "💰 Cost Forecasting", 
    "📉 Seasonal Patterns"
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1: FLEET HEALTH TRENDS
# ═══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.subheader("90-Day Historical vs 30-Day Forecast")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Line chart for fleet health
        fig_health = px.line(
            data['health_data'], x='Date', y='Health', color='Type',
            color_discrete_map={'Historical': '#3B9EFF', 'Forecast': '#FB923C'},
            title="Fleet Average Health Trend"
        )
        # Adding trendline
        fig_health.add_scatter(
            x=data['health_data']['Date'],
            y=data['health_data']['Health'].rolling(window=7).mean(),
            mode='lines', name='7-Day MA', line=dict(dash='dash', color='rgba(226,232,240,0.5)')
        )
        fig_health.update_layout(height=450, hovermode='x unified')
        st.plotly_chart(fig_health, use_container_width=True)
        
    with col2:
        st.markdown("### Trend Metrics")
        slope_pct = data['slope'] * 30  # change over 30 days
        st.metric(
            "Forecasted 30-Day Change",
            f"{slope_pct:+.2f} pts",
            delta=f"{slope_pct:+.2f}%", delta_color="normal" if slope_pct > 0 else "inverse"
        )
        
        avg_hist = data['health_data'][data['health_data']['Type'] == 'Historical']['Health'].mean()
        avg_fut  = data['health_data'][data['health_data']['Type'] == 'Forecast']['Health'].mean()
        
        st.metric("Avg Health (Last 90d)", f"{avg_hist:.1f}/100")
        st.metric("Expected Health (Next 30d)", f"{avg_fut:.1f}/100", 
                  delta=f"{avg_fut - avg_hist:+.1f}", delta_color="normal" if avg_fut > avg_hist else "inverse")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2: MAINTENANCE FORECAST
# ═══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("Predicted Maintenance Events (Next 30 Days)")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if not data['preds'].empty:
            st.markdown("#### Upcoming Failures Heatmap")
            # Create a dense daily count dataframe for heatmapping
            daily = data['preds'].groupby('Predicted_Date').size().reset_index(name='Failures')
            daily['Predicted_Date'] = pd.to_datetime(daily['Predicted_Date'])
            daily['Day'] = daily['Predicted_Date'].dt.day
            daily['DayOfWeek'] = daily['Predicted_Date'].dt.day_name()
            
            # Simple heatmap representation
            fig_cal = px.density_heatmap(
                daily, x="Predicted_Date", y="DayOfWeek", z="Failures",
                color_continuous_scale="Reds", title="Maintenance Event Density",
                category_orders={"DayOfWeek": list(calendar.day_name)}
            )
            st.plotly_chart(fig_cal, use_container_width=True)
        else:
            st.info("No train failures predicted within the next 30 days!")
            
    with col2:
        if not data['preds'].empty:
            st.markdown("#### Failure Types Breakdown")
            fig_pie = px.pie(
                data['preds'], names='failure_type', hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_pie.update_layout(margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig_pie, use_container_width=True)
            
    st.markdown("#### Top 10 Trains Requiring Attention")
    if not data['top_trains'].empty:
        display_cols = ['train_id', 'maintenance_probability', 'failure_type', 'time_to_failure_days', 'estimated_cost_inr', 'severity_score']
        rename_map = {
            'train_id': 'Train ID', 'maintenance_probability': 'Probability %', 
            'failure_type': 'Predicted Failure', 'time_to_failure_days': 'Days Until Failure', 
            'estimated_cost_inr': 'Est. Cost (₹)', 'severity_score': 'Severity (1-10)'
        }
        df_show = data['top_trains'][display_cols].rename(columns=rename_map)
        df_show['Probability %'] = (df_show['Probability %'] * 100).round(1).astype(str) + '%'
        df_show['Days Until Failure'] = df_show['Days Until Failure'].round(1)
        df_show['Est. Cost (₹)'] = df_show['Est. Cost (₹)'].apply(lambda x: f"₹{x:,.0f}")
        
        st.dataframe(df_show, use_container_width=True, hide_index=True)
        
        # Download button
        csv = df_show.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📄 Export Forecast as CSV",
            data=csv,
            file_name=f"maintenance_forecast_{datetime.date.today()}.csv",
            mime="text/csv"
        )

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3: COST FORECASTING
# ═══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("Financial Forecasting (Maintenance Ops)")
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Spent (Last 30d)", f"₹{data['h_tot']:,.0f}")
    m2.metric("Predicted Spend (Next 30d)", f"₹{data['f_tot']:,.0f}", 
              delta=f"{((data['f_tot'] - data['h_tot'])/data['h_tot']*100 if data['h_tot'] > 0 else 0):+.1f}%",
              delta_color="inverse")
              
    m3.metric("Budget Variance", "OVER BUDGET" if data['over_b'] else "UNDER BUDGET", 
              delta="-10% Threshold" if data['over_b'] else "Safe", delta_color="inverse" if data['over_b'] else "normal")
    
    num_trains = len(data['preds']) if not data['preds'].empty else 1
    m4.metric("Avg Predicted Cost / Train", f"₹{(data['f_tot']/num_trains):,.0f}" if num_trains > 0 else "₹0")
    
    st.divider()
    
    c1, c2 = st.columns([2, 1])
    
    with c1:
        if not data['monthly'].empty and 'Cost' in data['monthly'].columns:
            st.markdown("#### Historical vs Predicted Costs (Monthly)")
            fig_cost = px.bar(
                data['monthly'], x='Date', y='Cost', color='Type', barmode='group',
                color_discrete_map={'Actual': '#34D399', 'Predicted': '#F87171'},
                text_auto='.2s'
            )
            st.plotly_chart(fig_cost, use_container_width=True)
        else:
            st.info("Insufficient cost data to plot.")
            
    with c2:
        if data['routes'] is not None and not data['routes'].empty:
            st.markdown("#### Cost Distribution by Route")
            fig_route = px.pie(
                data['routes'], values='Total_Cost', names='assigned_route', hole=0.3,
                color_discrete_sequence=['#ef553b', '#636efa', '#00cc96'] # Approximate HMRL colors
            )
            fig_route.update_traces(textposition='inside', textinfo='percent+label')
            fig_route.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig_route, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4: SEASONAL PATTERNS
# ═══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.subheader("Temporal and Seasonal Operations Analysis")
    
    if data['seasons'].empty:
        st.info("Not enough historical data to analyze seasons.")
    else:
        scol1, scol2 = st.columns(2)
        
        with scol1:
            st.markdown("#### Failures by Season")
            fig_season = px.bar(
                data['seasons'], x='Season', y='Count', color='issue_type',
                barmode='stack', color_discrete_sequence=px.colors.qualitative.Set2
            )
            st.plotly_chart(fig_season, use_container_width=True)
            
        with scol2:
            st.markdown("#### Failures by Day of Week")
            
            fig_dow = px.density_heatmap(
                data['dow'], x="DayOfWeek", y="issue_type", z="Count",
                color_continuous_scale="Viridis", title="Day of Week Vulnerability Heatmap"
            )
            st.plotly_chart(fig_dow, use_container_width=True)
            
        st.info("📊 **Insight:** Understanding seasonal variations in Hyderabad (like heavier Monsoon wear on electricals, or Summer strain on HVAC) enables pre-emptive part purchasing and schedule loosening during hard months.")
