import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth.page_guard import require_auth
from auth.permissions import can_perform_action
from utils.ui_theme import apply_theme

st.set_page_config(page_title="ML Insights", page_icon="🤖", layout="wide")
apply_theme()
user = require_auth('ML_Insights')
st.title("🤖 ML Insights — Advanced Predictive Maintenance")
st.caption("Explainable AI | Multi-output predictions | Auto-retraining | SHAP analysis")

# ── Lazy-import heavy ML modules only on use ──────────────────────────────────
@st.cache_resource
def get_prediction_service():
    from ml.prediction_service import PredictionService
    return PredictionService()

@st.cache_resource
def get_model_trainer():
    from ml.model_trainer import ModelTrainer
    return ModelTrainer()

@st.cache_resource
def get_model_explainer():
    from ml.model_explainer import ModelExplainer
    svc = get_prediction_service()
    svc._ensure_ready()
    return ModelExplainer(svc._predictor)

# ── Risk colour helper ─────────────────────────────────────────────────────────
# Dark-mode safe risk palette
RISK_COLORS = {'CRITICAL': '#F87171', 'HIGH': '#FB923C', 'MEDIUM': '#FBBF24', 'LOW': '#34D399'}
RISK_BG     = {'CRITICAL': 'rgba(248,113,113,0.18)', 'HIGH': 'rgba(251,146,60,0.18)', 'MEDIUM': 'rgba(251,191,36,0.15)', 'LOW': 'rgba(52,211,153,0.15)'}
RISK_BORDER = {'CRITICAL': 'rgba(248,113,113,0.5)',  'HIGH': 'rgba(251,146,60,0.5)',  'MEDIUM': 'rgba(251,191,36,0.4)',  'LOW': 'rgba(52,211,153,0.4)'}

def risk_badge(risk):
    c  = RISK_COLORS.get(risk, '#94A3B8')
    bg = RISK_BG.get(risk, 'rgba(148,163,184,0.15)')
    bd = RISK_BORDER.get(risk, 'rgba(148,163,184,0.4)')
    return (f'<span style="background:{bg};color:{c};padding:3px 12px;border-radius:20px;'
            f'font-weight:700;font-size:0.78rem;letter-spacing:0.6px;text-transform:uppercase;'
            f'border:1px solid {bd};">{risk}</span>')

# ─────────────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🔮 Fleet Predictions",
    "🔍 Individual Train Analysis",
    "📊 Model Performance",
    "🔄 Model Retraining",
    "📈 Feature Importance",
    "🧬 GA Performance",
])
# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — FLEET PREDICTIONS
# ═══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.subheader("Fleet-Wide Risk Predictions")

    if st.button("🚀 Generate Predictions for All Trains", key="btn_fleet"):
        with st.spinner("Running AI engine across all 60 HMRL trains…"):
            svc = get_prediction_service()
            fleet_df = svc.predict_all_fleet()
            st.session_state['fleet_predictions'] = fleet_df

    if 'fleet_predictions' in st.session_state:
        df = st.session_state['fleet_predictions']

        # Metrics row
        counts = df['risk_level'].value_counts().to_dict()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🔴 Critical", counts.get('CRITICAL', 0))
        c2.metric("🟠 High",     counts.get('HIGH', 0))
        c3.metric("🟡 Medium",  counts.get('MEDIUM', 0))
        c4.metric("🟢 Low",     counts.get('LOW', 0))

        st.divider()

        # Colour-coded table
        def style_risk(val):
            c  = RISK_COLORS.get(val, '#94A3B8')
            bg = RISK_BG.get(val, 'rgba(148,163,184,0.1)')
            return f'background-color:{bg};color:{c};font-weight:700;border-radius:4px;'

        styled = df.style.applymap(style_risk, subset=['risk_level'])
        st.dataframe(styled, use_container_width=True)

        fig_pie = px.pie(
            df, names='risk_level',
            color='risk_level',
            color_discrete_map=RISK_COLORS,
            title="Risk Distribution Across Fleet",
            hole=0.4,
        )
        st.plotly_chart(fig_pie, use_container_width=True)

        # Download
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Export Fleet Predictions CSV", csv, "fleet_predictions.csv", "text/csv")
    else:
        st.info("Click **Generate Predictions** to run the AI analysis on all trains.")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — INDIVIDUAL TRAIN ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("Single Train Deep-Dive Analysis")

    train_ids = [f"HMRL-{i+1:02d}" for i in range(60)]
    selected_train = st.selectbox("Select Train ID", train_ids, key="sel_train")

    if st.button("🔍 Analyze Train", key="btn_single"):
        with st.spinner(f"Building full risk profile for {selected_train}…"):
            svc = get_prediction_service()
            result = svc.predict_single_train(selected_train)
            st.session_state['single_result'] = result

    if 'single_result' in st.session_state:
        r = st.session_state['single_result']
        prob = r['maintenance_probability']
        risk = r['risk_level']

        st.markdown(f"### {r['train_id']} — Risk: {risk_badge(risk)}", unsafe_allow_html=True)
        st.divider()

        col1, col2, col3 = st.columns(3)
        # Gauge
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=prob,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Maintenance Probability (%)"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': RISK_COLORS.get(risk, '#888')},
                'steps': [
                    {'range': [0, 35], 'color': 'rgba(52,211,153,0.25)'},
                    {'range': [35, 55], 'color': 'rgba(251,191,36,0.20)'},
                    {'range': [55, 75], 'color': 'rgba(251,146,60,0.25)'},
                    {'range': [75, 100], 'color': 'rgba(248,113,113,0.25)'},
                ],
                'threshold': {'line': {'color': '#E2E8F0', 'width': 3}, 'thickness': 0.8, 'value': prob},
            },
        ))
        fig_gauge.update_layout(height=260, margin=dict(t=40, b=10))
        col1.plotly_chart(fig_gauge, use_container_width=True)

        with col2:
            st.metric("🔧 Failure Type", r['failure_type'])
            st.metric("⏳ Time to Failure", f"{r['time_to_failure_days']} days")
            st.metric("💰 Estimated Cost", f"₹{r['estimated_cost_inr']:,}")

        with col3:
            st.metric("📊 Severity Score", f"{r['severity_score']}/100")
            sev_val = r['severity_score'] / 100
            st.progress(sev_val, text=f"Severity: {r['severity_score']:.0f}/100")

        st.divider()
        st.subheader("🧠 SHAP Explanation — Why This Prediction?")

        if r.get('explanation'):
            exp_df = pd.DataFrame(r['explanation'])
            exp_df.columns = ['Feature', 'Current Value', 'SHAP Impact']
            exp_df['Direction'] = exp_df['SHAP Impact'].apply(lambda x: '🔴 Increases Risk' if x > 0 else '🟢 Decreases Risk')
            st.dataframe(exp_df.style.background_gradient(subset=['SHAP Impact'], cmap='RdYlGn_r'), use_container_width=True)

            # Simple waterfall bar
            fig_wf = go.Figure(go.Bar(
                x=exp_df['SHAP Impact'],
                y=exp_df['Feature'],
                orientation='h',
                marker_color=['#F87171' if v > 0 else '#34D399' for v in exp_df['SHAP Impact']],
            ))
            fig_wf.update_layout(title="Feature Impact on Prediction (SHAP)", height=280,
                                  xaxis_title="SHAP Value", yaxis_autorange='reversed')
            st.plotly_chart(fig_wf, use_container_width=True)
        else:
            st.info("SHAP values not available. Install `shap` for full explanations.")

        st.subheader("💡 Recommendation")
        st.info(r.get('recommendation', 'No recommendation available.'))

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — MODEL PERFORMANCE
# ═══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("Model Performance Dashboard")
    svc = get_prediction_service()
    svc._ensure_ready()
    metrics = svc._predictor.metrics_ if svc._predictor else {}

    if not metrics:
        st.warning("No metrics available — train the model first (Tab 4).")
    else:
        mc1, mc2, mc3, mc4 = st.columns(4)
        mc1.metric("Accuracy",  f"{metrics.get('maintenance_accuracy', 0):.1%}")
        mc2.metric("F1-Score",  f"{metrics.get('maintenance_f1', 0):.1%}")
        mc3.metric("TTF MAE",   f"{metrics.get('ttf_mae', 0):.1f} days")
        mc4.metric("Severity MAE", f"{metrics.get('severity_mae', 0):.1f}")

        st.metric("Cost MAE", f"₹{metrics.get('cost_mae', 0):,.0f}")
        st.caption(f"Model Version: `{metrics.get('model_version', 'N/A')}` | Trained: {str(metrics.get('trained_at','N/A'))[:19]}")

    # Deployment history
    trainer = get_model_trainer()
    try:
        history = trainer.get_deployment_history()
    except Exception:
        history = pd.DataFrame()
        
    if history is not None and not history.empty:
        st.subheader("Model Version History")
        st.dataframe(history, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4 — MODEL RETRAINING
# ═══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.subheader("Automated Retraining Control Panel")
    trainer = get_model_trainer()
    status = trainer.get_status_summary()

    col_l, col_r = st.columns(2)
    with col_l:
        st.metric("📅 Days Since Last Training", status['days_since_last_training'])
        st.metric("📊 New Samples Available",   status['new_samples_since_train'])
        st.metric("📉 Data Drift",              f"{status['drift_pct']}%")
    with col_r:
        curr_acc = status['current_accuracy']
        if curr_acc != 'N/A':
            st.metric("🎯 Current Accuracy", f"{float(curr_acc):.1%}")
        retrain_flag = status['retrain_needed']
        if retrain_flag:
            st.error(f"⚡ Retraining Recommended\n\n{status['reason']}")
        else:
            st.success(status['reason'])

    if st.button("🔍 Check if Retraining Needed"):
        needed, reason = trainer.should_retrain()
        if needed:
            st.warning(f"Retraining needed: {reason}")
        else:
            st.success(reason)

    st.divider()
    if can_perform_action(user['role'], 'retrain_model'):
        if st.button("🔄 Retrain Model Now (Admin)", type="primary"):
            with st.spinner("Training new multi-output model… this may take 30-60 seconds."):
                progress = st.progress(0, text="Feature Engineering…")
                new_predictor, new_metrics = trainer.train_new_model()
                progress.progress(70, text="Comparing with production…")
                comparison = trainer.compare_with_production(new_predictor)
                progress.progress(100, text="Done!")

            st.success("New model trained and deployed!")
            cc1, cc2, cc3 = st.columns(3)
            cc1.metric("Old Accuracy", f"{comparison['old_accuracy']:.1%}")
            cc2.metric("New Accuracy", f"{comparison['new_accuracy']:.1%}",
                       delta=f"{comparison['improvement']:+.1%}")
            cc3.metric("Recommendation", comparison['recommendation'])
            st.cache_resource.clear()
            st.info("Cache cleared - new model active on next page load.")
    else:
        st.warning("Model retraining is restricted to Admin role only.")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5 — FEATURE IMPORTANCE
# ═══════════════════════════════════════════════════════════════════════════════
with tab5:
    st.subheader("Global Feature Importance Analysis")
    svc = get_prediction_service()
    svc._ensure_ready()
    explainer = get_model_explainer()
    try:
        importance_df = explainer.get_global_importance()
    except Exception:
        importance_df = pd.DataFrame()

    if importance_df is not None and not importance_df.empty:
        top10 = importance_df.head(10)
        fig_imp = px.bar(
            top10, x='importance', y='feature', orientation='h',
            color='importance', color_continuous_scale='Oranges',
            title="Top 10 Most Important Features (SHAP-based)",
        )
        fig_imp.update_layout(yaxis_autorange='reversed', height=420)
        st.plotly_chart(fig_imp, use_container_width=True)

        st.subheader("Full Feature Ranking")
        st.dataframe(importance_df.style.bar(subset=['importance'], color='#ff7f0e'),
                     use_container_width=True)

        # Feature distribution histograms (fetch feature df)
        st.subheader("Feature Distributions Across Fleet")
        try:
            svc._ensure_ready()
            all_feat = svc._feature_engineer.create_all_features()
            top5_names = top10['feature'].head(5).tolist()
            top5_avail = [f for f in top5_names if f in all_feat.columns]
            if top5_avail:
                hist_fig = px.histogram(all_feat.melt(id_vars=['train_id'], value_vars=top5_avail),
                                        x='value', facet_col='variable', facet_col_wrap=3,
                                        title="Top-5 Feature Distributions", height=500,
                                        color_discrete_sequence=['#1f77b4'])
                hist_fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
                st.plotly_chart(hist_fig, use_container_width=True)
        except Exception as e:
            st.info(f"Feature distributions unavailable: {e}")
    else:
        st.info("Train the model first to see feature importance.")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 6 — GA INSIGHTS SECTION
# ═══════════════════════════════════════════════════════════════════════════════
with tab6:
    st.header("🧬 Genetic Algorithm Insights")
    st.caption("Review the performance and convergence of DEAP-based evolutionary schedulers.")
    
    ga_ready = False
    try:
        from advanced_scheduling.crew_scheduler import assign_crew_to_trains, get_ga_stats as get_crew_ga_stats
        from advanced_scheduling.route_optimizer import assign_trains_to_routes, get_optimization_summary as get_route_ga_stats
        ga_ready = True
    except ImportError as e:
        st.error(f"Failed to load Genetic Algorithm modules: {e}")
    
    if ga_ready:
        if st.button("🚀 Run GA Optimization", key="btn_run_ga"):
            with st.spinner("Executing DEAP Genetic Algorithms for Crew and Route Optimization..."):
                # Dummy datasets for GA triggering as required by the assignment functions
                dummy_crew_schedule = pd.DataFrame({
                    'train_id': [f"TRN_{i}" for i in range(50)], 
                    'assigned_route': ['Red Line']*25 + ['Blue Line']*15 + ['Green Line']*10
                })
                dummy_available_trains = pd.DataFrame({
                    'train_id': [f"HMRL-{i:02d}" for i in range(60)], 
                    'health_score': np.random.randint(60, 100, 60), 
                    'home_depot': ['Miyapur']*20 + ['Uppal']*20 + ['Secunderabad']*20
                })
                
                # Execute GAs
                assign_crew_to_trains(dummy_crew_schedule, '2026-04-06')
                assign_trains_to_routes(dummy_available_trains, '2026-04-06')
                st.success("GA Optimization complete! Stats have been refreshed.")
    
        # Fetch stats after running or initially
        try:
            crew_stats = get_crew_ga_stats()
            route_stats = get_route_ga_stats()
            
            has_run = crew_stats.get('generations_run', 0) > 0 or route_stats.get('generations_taken', 0) > 0
            
            if not has_run:
                st.info("Click 'Run GA Optimization' to generate and visualize the GA metrics.")
            else:
                # --- 2. GA Summary Cards ---
                st.subheader("Optimization Summary Metrics")
                rc1, rc2 = st.columns(2)
                
                with rc1:
                    st.markdown("#### 👷 Crew Scheduler (Minimization)")
                    st.metric("Generations Run", crew_stats.get('generations_run', 0))
                    st.metric("Best Fitness Score (Penalty)", f"{crew_stats.get('best_fitness_score', 0):.1f}")
                    st.metric("Convergence Generation", crew_stats.get('convergence_generation', 0))
                    
                with rc2:
                    st.markdown("#### 🚉 Route Optimizer (Maximization)")
                    best_assignments = route_stats.get('best_assignments', pd.DataFrame())
                    num_routes_opt = len(best_assignments['assigned_route'].unique()) if isinstance(best_assignments, pd.DataFrame) and best_assignments is not None and not best_assignments.empty else 0
                    st.metric("Generations Taken", route_stats.get('generations_taken', 0))
                    st.metric("Best Fitness Score", f"{route_stats.get('fitness_score', 0):.1f}")
                    st.metric("Routes Optimized", num_routes_opt)
                    
                # --- 1. Fitness Convergence Chart ---
                st.subheader("GA Convergence Over Generations")
                
                # Helper to simulate the historical convergence trajectory using the result scalars
                def simulate_convergence(gens, best_fit, conv_gen, maximize=True):
                    if gens <= 0: return []
                    curve = []
                    start_fit = best_fit * 0.3 if maximize else (best_fit * 3 if best_fit > 0 else -best_fit * 3 + 100)
                    if start_fit == 0: start_fit = -1000 if maximize else 10000
                    conv_gen = max(1, conv_gen)
                    for i in range(1, gens + 1):
                        if i < conv_gen:
                            # Quadratic approach towards best_fit
                            ratio = ((conv_gen - i) / conv_gen) ** 2
                            val = best_fit + (start_fit - best_fit) * ratio
                        else:
                            val = best_fit
                        curve.append(val)
                    return curve
                    
                crew_gens = crew_stats.get('generations_run', 0)
                crew_best = crew_stats.get('best_fitness_score', 0)
                crew_conv = crew_stats.get('convergence_generation', 0)
                crew_curve = simulate_convergence(crew_gens, crew_best, crew_conv, maximize=False)
                
                route_gens = route_stats.get('generations_taken', 0)
                route_best = route_stats.get('fitness_score', 0)
                # Route logic stops at generations_taken without a separate convergence gen logged
                route_curve = simulate_convergence(route_gens, route_best, max(1, route_gens - 10), maximize=True)
                
                # Standardize sizes for plotting together
                max_plot_gens = max(crew_gens, route_gens, 1)
                crew_plot = crew_curve + [crew_curve[-1]] * (max_plot_gens - len(crew_curve)) if crew_curve else [0]*max_plot_gens
                route_plot = route_curve + [route_curve[-1]] * (max_plot_gens - len(route_curve)) if route_curve else [0]*max_plot_gens
                
                df_conv = pd.DataFrame({
                    'Generation': list(range(1, max_plot_gens + 1)),
                    'Crew Scheduler Fitness': crew_plot,
                    'Route Optimizer Fitness': route_plot
                })
                
                fig_conv = px.line(df_conv, x='Generation', y=['Crew Scheduler Fitness', 'Route Optimizer Fitness'],
                                   title="Convergence Trace (Simulated from Result Scalars)",
                                   labels={'value': 'Best Fitness Score', 'variable': 'GA Module'},
                                   color_discrete_sequence=['#ff7f0e', '#1f77b4'])
                st.plotly_chart(fig_conv, use_container_width=True)
                
    
        except Exception as e:
            st.error(f"Error fetching or rendering GA stats: {e}")

