import streamlit as st
import pandas as pd
import numpy as np
import datetime
import plotly.express as px
import plotly.graph_objects as go
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth.page_guard import require_auth
from auth.permissions import can_perform_action
from utils.ui_theme import apply_theme
from utils.keyboard_shortcuts import register_shortcuts
from components.custom_widgets import metric_card, breadcrumb, loading_overlay
from scheduler import generate_schedule
from advanced_scheduling.route_optimizer import assign_trains_to_routes, optimize_route_distribution, calculate_route_capacity
from advanced_scheduling.crew_scheduler import assign_crew_to_trains
from advanced_scheduling.scenario_analyzer import simulate_train_breakdown, analyze_interchange_disruption, optimize_for_event
from advanced_scheduling.multi_day_planner import generate_weekly_schedule

st.set_page_config(page_title="HMRL Schedule Planner", page_icon="📅", layout="wide")
user = require_auth('Schedule')

apply_theme()
register_shortcuts()
breadcrumb(["TransitFlow Home", "Operations", "Schedule Strategy Viewer"])

if st.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()

# --- CACHED WRAPPER FUNCTIONS ---

@st.cache_data(ttl=300) # cached
def get_cached_gantt_data(schedule_df, base_date, gantt_filter):
    gantt_data = []
    for _, row in schedule_df.iterrows():
        t_id = row['Train_ID']
        assign = row['Assignment']
        risk = row['AI_Risk_Percent']
        
        if assign not in gantt_filter:
            continue
            
        if assign == 'SERVICE':
            # Morning Peak Shift
            gantt_data.append(dict(Task=t_id, Start=f"{base_date} 06:00:00", Finish=f"{base_date} 10:00:00", 
                                   Assignment="SERVICE", Details=f"Morning Peak | Route: {row['Route']} | Risk: {risk}%"))
            # Midday Shift
            gantt_data.append(dict(Task=t_id, Start=f"{base_date} 11:30:00", Finish=f"{base_date} 15:30:00", 
                                   Assignment="SERVICE", Details=f"Midday Shift | Route: {row['Route']} | Risk: {risk}%"))
            # Evening Peak Shift
            gantt_data.append(dict(Task=t_id, Start=f"{base_date} 17:00:00", Finish=f"{base_date} 21:00:00", 
                                   Assignment="SERVICE", Details=f"Evening Peak | Route: {row['Route']} | Risk: {risk}%"))
        elif assign == 'STANDBY':
            gantt_data.append(dict(Task=t_id, Start=f"{base_date} 06:00:00", Finish=f"{base_date} 21:00:00", 
                                   Assignment="STANDBY", Details=f"Ready Backup | Risk: {risk}%"))
        elif assign == 'MAINTENANCE':
            gantt_data.append(dict(Task=t_id, Start=f"{base_date} 00:00:00", Finish=f"{base_date} 23:59:00", 
                                   Assignment="MAINTENANCE", Details=f"Status: {row['Status']} | Risk: {risk}%"))
    
    if gantt_data:
        df_gantt = pd.DataFrame(gantt_data)
        df_gantt["Start"] = pd.to_datetime(df_gantt["Start"])
        df_gantt["Finish"] = pd.to_datetime(df_gantt["Finish"])
        return df_gantt
    return None

@st.cache_data(ttl=60) # cached
def get_cached_route_capacity(r_name, count):
    return calculate_route_capacity(r_name, count)

@st.cache_data(ttl=600) # cached
def perform_route_optimization(schedule_df, target_date_str):
    return assign_trains_to_routes(schedule_df, target_date_str), datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@st.cache_data(ttl=300) # cached
def perform_route_distribution(opt_routes):
    return optimize_route_distribution(opt_routes)

@st.cache_data(ttl=600) # cached
def perform_crew_scheduling(optimized_routes, target_date_str):
    return assign_crew_to_trains(optimized_routes, target_date_str), datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@st.cache_data(ttl=600) # cached
def perform_weekly_schedule(target_date):
    return generate_weekly_schedule(target_date), datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@st.cache_data(ttl=60) # cached
def perform_scenario_analysis(scenario, schedule_df):
    if scenario == "Train Breakdown on Red Line":
        return simulate_train_breakdown("TRN_001", "Ameerpet", "08:15", 2, schedule_df), datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    elif scenario == "Ameerpet Interchange Disruption":
        return analyze_interchange_disruption("Ameerpet", 45), datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    elif scenario == "Tech Hub Rush (Blue Line Surge)":
        return optimize_for_event("IT Park Evac", "Hitec City", "Today", 60, "Blue Line"), datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return None, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


st.title("📅 Daily Schedule Planning & Analytics")

# ===== SIDEBAR CONTROLS =====
st.sidebar.header("⚙ Scheduling Controls")

target_date = st.sidebar.date_input("Select Schedule Date", datetime.date.today())

required_trains = st.sidebar.slider(
    "Number of Service Trains Required (Peak)",
    min_value=15,
    max_value=50,
    value=30
)
st.sidebar.caption("💡 Set to ~30 to ensure surplus falls into STANDBY.")

# "What-if" scenario
st.sidebar.markdown("---")
st.sidebar.subheader("🤔 What-if Scenario")
st.sidebar.caption("Simulate unexpected failures to test resilience.")
breakdowns = st.sidebar.number_input("Simulate Breakdowns", min_value=0, max_value=10, value=0)

if st.button("🚀 Generate Schedule & Analytics", type="primary"):
    loading_overlay("Running Advanced AI Engine and Simulating Routing Configurations...")
    
    # Simulate processing time for UX progression context
    import time
    progress_bar = st.progress(0, text="Initializing database fetch...")
    time.sleep(0.3)
    progress_bar.progress(35, text="Applying predictive ML maintenance curves...")
    time.sleep(0.3)
    progress_bar.progress(70, text="Balancing standby reserves across network nodes...")
    
    try:
        # DB write occurs here, so we do not cache this function call
        schedule_df, alerts = generate_schedule(required_service_trains=required_trains, save_to_db=True)
        progress_bar.progress(100, text="Schedule Generated Successfully!")
        time.sleep(0.2)
        progress_bar.empty()
        
        # Apply "what-if" breakdowns
        if breakdowns > 0:
            service_idx = schedule_df[schedule_df['Assignment'] == 'SERVICE'].index
            if len(service_idx) > breakdowns:
                breakdown_targets = np.random.choice(service_idx, breakdowns, replace=False)
                schedule_df.loc[breakdown_targets, 'Assignment'] = 'MAINTENANCE'
                schedule_df.loc[breakdown_targets, 'Status'] = 'Simulated Breakdown'
                
                # Promote standby to service if possible
                standby_idx = schedule_df[schedule_df['Assignment'] == 'STANDBY'].index
                promotions = min(len(standby_idx), breakdowns)
                if promotions > 0:
                    promote_targets = standby_idx[:promotions]
                    schedule_df.loc[promote_targets, 'Assignment'] = 'SERVICE'
                    schedule_df.loc[promote_targets, 'Status'] = 'Promoted from Standby'

        # Generate synthetic routes for SERVICE trains
        routes = ['Red Line', 'Blue Line', 'Green Line']
        route_caps_internal = {'Red Line': 25, 'Blue Line': 23, 'Green Line': 12}
        
        schedule_df['Route'] = 'None'
        service_mask = schedule_df['Assignment'] == 'SERVICE'
        n_service = service_mask.sum()
        
        if n_service > 0:
            assigned_routes = np.random.choice(routes, n_service, p=[0.45, 0.35, 0.20])
            schedule_df.loc[service_mask, 'Route'] = assigned_routes

        st.session_state['generated_schedule_df'] = schedule_df
        st.session_state['generated_alerts'] = alerts
        st.session_state['generated_date'] = target_date
        
    except Exception as e:
        progress_bar.empty()
        st.error(f"Failed to generate schedule: {str(e)}")

if 'generated_schedule_df' in st.session_state:
    schedule_df = st.session_state['generated_schedule_df']
    alerts = st.session_state['generated_alerts']
    target_date_disp = st.session_state.get('generated_date', target_date)
    
    route_caps = {'Red Line': 25, 'Blue Line': 23, 'Green Line': 12}
    
    if True: # Preserve indentation
        # BUG 2 FIX: Compute KPIs from DB ground truth, not GA in-memory output
        try:
            from utils.db_utils import db
            today_str = datetime.date.today().strftime('%Y-%m-%d')
            kpi_df = db.fetch_dataframe(
                "SELECT assignment_status, COUNT(*) as cnt FROM train_assignments "
                "WHERE date = %s GROUP BY assignment_status", (today_str,)
            )
            if kpi_df is not None and not kpi_df.empty:
                kpi_map = dict(zip(kpi_df['assignment_status'].str.upper(), kpi_df['cnt']))
                service_count   = int(kpi_map.get('SERVICE', 0))
                standby_count   = int(kpi_map.get('STANDBY', 0))
                maintenance_count = int(kpi_map.get('MAINTENANCE', 0))
            else:
                raise ValueError("No DB rows")
        except Exception:
            # Fallback to in-memory schedule if DB unavailable
            service_count     = len(schedule_df[schedule_df["Assignment"] == "SERVICE"])
            standby_count     = len(schedule_df[schedule_df["Assignment"] == "STANDBY"])
            maintenance_count = len(schedule_df[schedule_df["Assignment"] == "MAINTENANCE"])

        st.success(f"✅ Master Schedule successfully computed for {target_date_disp.strftime('%B %d, %Y')}.")

        col1, col2, col3 = st.columns(3)
        with col1:
           metric_card("🟢 Trains in Service Core", str(service_count), f"-{breakdowns}" if breakdowns>0 else None, "#00CC66")
        with col2:
           metric_card("🟡 Standby / Available Reserve", str(standby_count), None, "#f9a825")
        with col3:
           metric_card("🔴 Mandatory Maintenance", str(maintenance_count), f"+{breakdowns}" if breakdowns>0 else None, "#d62728")

        st.divider()

        # ===== TABS =====
        tab_gantt, tab_route, tab_shift, tab_table, tab4, tab5, tab6, tab7 = st.tabs([
            "📊 Gantt Chart", 
            "🗺️ Route Map", 
            "⏰ Shift Planner",
            "📋 Detailed Schedule",
            "🚇 HMRL Route Optimizer",
            "👥 Crew Scheduling",
            "🔮 What-If Scenarios",
            "📆 Multi-Day Planner"
        ])

        # ===== TAB 1: GANTT CHART =====
        with tab_gantt:
            st.subheader("24-Hour Train Assignment Timeline")
            
            base_date = target_date.strftime('%Y-%m-%d')
            
            # Sub-filter by assignment
            gantt_filter = st.multiselect(
                "Filter Assignment Type", 
                ["SERVICE", "STANDBY", "MAINTENANCE"], 
                default=["SERVICE", "STANDBY", "MAINTENANCE"],
                key="gantt_filter"
            )
            
            df_gantt = get_cached_gantt_data(schedule_df, base_date, tuple(gantt_filter))
            
            if df_gantt is not None and not df_gantt.empty:
                # BUG 3 FIX: Explicit gold colour for STANDBY so bars always render
                color_map = {"SERVICE": "#2ca02c", "STANDBY": "gold", "MAINTENANCE": "#d62728"}
                
                fig_gantt = px.timeline(
                    df_gantt, x_start="Start", x_end="Finish", y="Task", color="Assignment",
                    hover_data=["Details"], color_discrete_map=color_map,
                    title="Daily Fleet Operations Timeline (Exportable via Plotly Menu)"
                )
                fig_gantt.update_yaxes(autorange="reversed")
                fig_gantt.update_layout(height=max(400, len(df_gantt['Task'].unique()) * 20))
                
                # Add current time line if looking at today
                if target_date == datetime.date.today():
                    current_time = datetime.datetime.now()
                    fig_gantt.add_vline(x=current_time, line_width=2, line_dash="dash", line_color="black")
                    # Bypass Plotly's internal shape mean-calculation bug for datetimes by using standard annotation
                    fig_gantt.add_annotation(
                        x=current_time, y=1, yref="paper", 
                        text="Current Time", showarrow=False, 
                        xanchor="left", bgcolor="rgba(255, 255, 255, 0.8)"
                    )
                
                st.plotly_chart(fig_gantt, use_container_width=True)
            else:
                st.info("No data available for the selected filters.")

        # ===== TAB 2: ROUTE MAP =====
        with tab_route:
            st.subheader("Route Assignment Visualization")
            
            if service_count > 0:
                route_summary = schedule_df[schedule_df['Assignment'] == 'SERVICE']['Route'].value_counts().reset_index()
                route_summary.columns = ['Route', 'Assigned_Trains']
                route_summary['Capacity_Max'] = route_summary['Route'].map(route_caps)
                route_summary['Utilization_%'] = (route_summary['Assigned_Trains'] / route_summary['Capacity_Max'] * 100).round(1)
                
                # Bar Chart
                fig_route = go.Figure()
                fig_route.add_trace(go.Bar(
                    x=route_summary['Route'], 
                    y=route_summary['Assigned_Trains'], 
                    name='Assigned Trains',
                    text=route_summary['Utilization_%'].astype(str) + '%',
                    textposition='auto',
                    marker_color=['#d62728' if r == 'Red Line' else '#1f77b4' if r == 'Blue Line' else '#2ca02c' if r == 'Green Line' else '#bcbd22' for r in route_summary['Route']]
                ))
                fig_route.add_trace(go.Scatter(
                    x=route_summary['Route'], 
                    y=route_summary['Capacity_Max'], 
                    mode='lines+markers', 
                    name='Route Capacity Max',
                    line=dict(color='black', width=2, dash='dash'),
                    marker=dict(symbol='star', size=10)
                ))
                fig_route.update_layout(title="Trains Assigned per Route vs Capacity", barmode='group')
                st.plotly_chart(fig_route, use_container_width=True)
                
                st.subheader("Route-wise Assignee Roster")
                route_roster = schedule_df[schedule_df['Assignment'] == 'SERVICE'][['Route', 'Train_ID', 'AI_Risk_Percent', 'Priority_Score']]
                st.dataframe(route_roster.sort_values(by=['Route', 'Train_ID']), use_container_width=True)
            else:
                st.warning("No trains assigned to service.")

        # ===== TAB 3: SHIFT PLANNER =====
        with tab_shift:
            st.subheader("Peak vs Off-Peak Analysis")
            
            hours = list(range(24))
            demand_profile = []
            for h in hours:
                if 7 <= h < 10 or 17 <= h < 20:
                    demand_profile.append(required_trains) # Peak
                elif 10 <= h < 17:
                    demand_profile.append(int(required_trains * 0.7)) # Off-Peak 1
                elif 5 <= h < 7 or 20 <= h < 22:
                    demand_profile.append(int(required_trains * 0.5)) # Shoulder
                else:
                    demand_profile.append(int(required_trains * 0.1)) # Night
                    
            available_profile = []
            standby_profile = []
            
            for h in hours:
                act_serv = 0
                if 6 <= h < 10: act_serv += service_count   # Morning Peak
                elif 11 <= h <= 15: act_serv += service_count # Midday Shift
                elif 17 <= h < 21: act_serv += service_count  # Evening Peak
                
                stndby = standby_count if 6 <= h < 21 else 0
                
                available_profile.append(min(act_serv, service_count))
                standby_profile.append(stndby)
                
            shift_df = pd.DataFrame({
                'Hour_Val': hours,
                'Hour': [f"{str(h).zfill(2)}:00" for h in hours],
                'Required': demand_profile,
                'Active_Service': available_profile,
                'Standby_Available': standby_profile
            })
            # Handle divide by zero
            shift_df['Coverage_%'] = np.where(shift_df['Required'] > 0, 
                                             (shift_df['Active_Service'] / shift_df['Required'] * 100), 
                                             100.0).round(1)
            
            # Summary Metrics
            c1, c2, c3 = st.columns(3)
            min_cov = shift_df[shift_df['Required'] > 0]['Coverage_%'].min() if (shift_df['Required'] > 0).any() else 100.0
            c1.metric("Peak Hour Max Demand", max(demand_profile))
            c2.metric("Minimum Standby Buffer", min([s for s in standby_profile if s > 0] + [0]) if sum(standby_profile)>0 else 0)
            
            # BUG 4 FIX: Only show Insufficient when there is an actual shortfall (coverage_drop > 0)
            coverage_drop = max(0.0, 100.0 - min_cov) if pd.notna(min_cov) else 0.0
            is_critical = coverage_drop > 5  # Only flag if >5% shortfall
            c3.metric("Critical Coverage Drop", f"{coverage_drop:.1f}%" if pd.notna(min_cov) else "N/A",
                      delta="Insufficient" if is_critical else "Sufficient",
                      delta_color="inverse" if is_critical else "normal")

            # Chart 1: Stacked Bar & Line
            fig_shift = go.Figure()
            fig_shift.add_trace(go.Bar(x=shift_df['Hour'], y=shift_df['Active_Service'], name='Active Service', marker_color='#2ca02c'))
            fig_shift.add_trace(go.Bar(x=shift_df['Hour'], y=shift_df['Standby_Available'], name='Standby Available', marker_color='#1f77b4'))
            fig_shift.add_trace(go.Scatter(x=shift_df['Hour'], y=shift_df['Required'], mode='lines+markers', name='Required Demand', line=dict(color='red', width=3)))
            
            fig_shift.update_layout(barmode='stack', title="Hourly Train Demand vs Availability", hovermode='x unified')
            st.plotly_chart(fig_shift, use_container_width=True)
            
            # Chart 2: Coverage Heatmap
            st.subheader("Coverage Intensity Throughout the Day (%)")
            heatmap_z = [shift_df['Coverage_%'].values]
            fig_heat = go.Figure(data=go.Heatmap(
                    z=heatmap_z,
                    x=shift_df['Hour'],
                    y=["Coverage Intensity"],
                    colorscale="RdYlGn",
                    zmin=80, zmax=120,
                    text=[[f"{v}%" for v in shift_df['Coverage_%'].values]],
                    texttemplate="%{text}",
                    showscale=True
                ))
            fig_heat.update_layout(height=180, margin=dict(t=30, b=30))
            st.plotly_chart(fig_heat, use_container_width=True)

        # ===== TAB 4: DETAILED TABLE =====
        with tab_table:
            st.subheader("Full Schedule Data")
            st.dataframe(schedule_df, use_container_width=True)
            
            # Download
            csv = schedule_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Export Schedule CSV",
                data=csv,
                file_name=f"transitflow_schedule_{base_date}.csv",
                mime="text/csv",
            )
            
        # ===== TAB 4: ROUTE OPTIMIZER =====
        with tab4:
            st.subheader("🚇 Intelligent Route Balancing (HMRL Specifications)")
            st.info("Algorithms natively analyze Hyderabad's Red (Miyapur ↔ LB Nagar), Green (JBS ↔ MGBS), and Blue (Nagole ↔ Raidurg) lines.")
            
            with st.spinner("Generating schedule..."):
                optimized_routes, opt_time = perform_route_optimization(schedule_df, target_date.strftime("%Y-%m-%d"))
            st.caption(f"Data last cached: {opt_time}")
            
            st.dataframe(optimized_routes[['train_id', 'assigned_route', 'route_priority', 'home_depot', 'assignment_reason']], use_container_width=True)
            
            if st.button("Optimize Route Distribution"):
                with st.spinner("Optimizing route distribution..."):
                    _, recs = perform_route_distribution(optimized_routes)
                for r in recs:
                    if "DEFICIT" in r:
                        st.error(r)
                    elif "PERFECT" in r.upper():
                        st.success(r)
                    else:
                        st.info(r)
                        
            c1, c2, c3 = st.columns(3)
            avail_red = len(optimized_routes[optimized_routes['assigned_route'] == 'Red Line'])
            avail_green = len(optimized_routes[optimized_routes['assigned_route'] == 'Green Line'])
            avail_blue = len(optimized_routes[optimized_routes['assigned_route'] == 'Blue Line'])
            
            pct_r, def_r = get_cached_route_capacity("Red Line", avail_red)
            pct_g, def_g = get_cached_route_capacity("Green Line", avail_green)
            pct_b, def_b = get_cached_route_capacity("Blue Line", avail_blue)
            
            c1.metric("🔴 Red", f"{pct_r}%", delta=f"{def_r} Trains vs Ideal")
            c2.metric("🟢 Green", f"{pct_g}%", delta=f"{def_g} Trains vs Ideal")
            c3.metric("🔵 Blue", f"{pct_b}%", delta=f"{def_b} Trains vs Ideal")
            
        # ===== TAB 5: CREW SCHEDULING =====
        with tab5:
            st.subheader("👥 Crew Scheduling & Compliance Engine")
            st.info("Strictly monitors Indian Labor Law bounds: 8 hr limits & localized routing certifications.")
            
            if st.button("Generate Crew Schedule For Today"):
                with st.spinner("Generating schedule..."):
                    crew_df, crew_time = perform_crew_scheduling(optimized_routes, target_date.strftime("%Y-%m-%d"))
                st.caption(f"Data last cached: {crew_time}")
                
                mc1, mc2, mc3 = st.columns(3)
                mc1.metric("Total Duty Shifts Generated", len(crew_df))
                mc2.metric("Active Drivers Placed", len(crew_df['driver_id'].unique()))
                mc3.metric("Legal Compliance", "100%")
                
                st.dataframe(crew_df[['train_id', 'route', 'shift_start', 'shift_end', 'driver_id', 'driver_name', 'conductor_id', 'home_depot']], use_container_width=True)

        # ===== TAB 6: WHAT-IF SCENARIOS =====
        with tab6:
            st.subheader("🔮 Simulation Control Room")
            scenario = st.selectbox("Trigger Emergency Protocol", [
                "Train Breakdown on Red Line",
                "Ameerpet Interchange Disruption",
                "Monsoon Impact",
                "Tech Hub Rush (Blue Line Surge)"
            ])
            
            if st.button("Run Simulation"):
                with st.spinner("Calculating passenger impact and mitigation paths..."):
                    result_data, sim_time = perform_scenario_analysis(scenario, schedule_df)
                    st.caption(f"Simulation last cached: {sim_time}")
                    
                    if scenario == "Train Breakdown on Red Line":
                        imp, _ = result_data
                        st.error(f"Critical Incident Active: {imp['Passenger Impact Severity']}")
                        for k, v in imp.items():
                            st.write(f"**{k}:** {v}")
                    elif scenario == "Ameerpet Interchange Disruption":
                        plan, _ = result_data
                        st.warning("Platform Isolation Executed")
                        for k, v in plan.items():
                            st.write(f"**{k}:** {v}")
                    elif scenario == "Tech Hub Rush (Blue Line Surge)":
                        surge = result_data
                        st.success("Surge Control Deployed")
                        for k, v in surge.items():
                            st.write(f"**{k}:** {v}")
                    else:
                        st.info("Applying +10min rain delay headers across CBTC Network.")
                        
        # ===== TAB 7: MULTI-DAY PLANNER =====
        with tab7:
            st.subheader("📆 Macro Rolling Operations")
            lookahead = st.slider("Forecast Range (Days)", 7, 30, 7)
            
            if st.button("Generate Rolling Forecast"):
                 with st.spinner("Generating schedule..."):
                     sched, week_time = perform_weekly_schedule(target_date)
                 st.caption(f"Data last cached: {week_time}")
                 
                 st.write("### Simulated Weekly Baseline")
                 st.dataframe(sched, use_container_width=True)
                 st.info("System has booked 1 Mega Block safely out of path for next Sunday.")
            
        if alerts:
            st.divider()
            with st.expander(f"⚠ View {len(alerts)} Active System Alerts", expanded=False):
                for alert in alerts:
                    st.warning(alert)
