import streamlit as st
import pandas as pd
import datetime
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth.page_guard import require_auth
from auth.permissions import can_perform_action
from utils.db_utils import db
from utils.report_generator import ReportGenerator
from utils.report_helpers import get_report_history, delete_report

st.set_page_config(page_title="Reports & Export", page_icon="📄", layout="wide")
user = require_auth('Reports')

# Filter options based on permissions
REPORT_OPTIONS = [
    "Daily Operations Report",
    "Weekly Schedule Report", 
    "Monthly Maintenance Report",
    "Fleet Health Report",
    "ML Predictions Report",
    "Executive Summary"
]

if not can_perform_action(user['role'], 'generate_all_reports'):
    if can_perform_action(user['role'], 'generate_maintenance_reports'):
        REPORT_OPTIONS = [r for r in REPORT_OPTIONS if "Maintenance" in r or "Health" in r]
    else:
        REPORT_OPTIONS = []

st.title("📄 Automated Reporting Engine")
st.markdown("Generate and track professional PDFs for HMRL executives and operations teams.")
st.divider()

report_gen = ReportGenerator(user_id=user['user_id'] if user else None)

tab1, tab2 = st.tabs(["📋 Generate Reports", "🗂️ Report History"])

with tab1:
    if not REPORT_OPTIONS:
        st.warning("You do not have permission to generate new reports.")
    else:
        st.subheader("Generate Custom Report")
        col1, col2 = st.columns([1, 2])
        
        with col1:
            report_type = st.selectbox("Select Report Type", REPORT_OPTIONS)
            
            # Dynamic date inputs
            if "Daily" in report_type or "ML Predictions" in report_type:
                selected_date = st.date_input("Select Date", datetime.date.today())
            elif "Weekly" in report_type:
                # Align to Monday
                today = datetime.date.today()
                start = today - datetime.timedelta(days=today.weekday())
                selected_date = st.date_input("Week Starting (Monday)", value=start)
            elif "Fleet Health" in report_type:
                dr = st.date_input("Date Range", value=(datetime.date.today() - datetime.timedelta(days=30), datetime.date.today()))
                if len(dr) == 2:
                    start_date, end_date = dr
                else:
                    start_date, end_date = dr[0], dr[0]
            else:
                # Monthly / Executive
                mc1, mc2 = st.columns(2)
                with mc1:
                    selected_month = st.selectbox("Month", list(range(1, 13)), index=datetime.date.today().month-1)
                with mc2:
                    selected_year = st.number_input("Year", min_value=2020, max_value=2030, value=datetime.date.today().year)

            if st.button("Generate Report", type="primary"):
                with st.spinner("Compiling data & generating PDF..."):
                    try:
                        pdf_path = None
                        if report_type == "Daily Operations Report":
                            pdf_path = report_gen.generate_daily_operations_report(selected_date)
                        elif report_type == "Weekly Schedule Report":
                            pdf_path = report_gen.generate_weekly_schedule_report(selected_date)
                        elif report_type == "Monthly Maintenance Report":
                            pdf_path = report_gen.generate_monthly_maintenance_report(selected_month, selected_year)
                        elif report_type == "Fleet Health Report":
                            pdf_path = report_gen.generate_fleet_health_report(start_date, end_date)
                        elif report_type == "ML Predictions Report":
                            pdf_path = report_gen.generate_ml_predictions_report(selected_date)
                        elif report_type == "Executive Summary":
                            pdf_path = report_gen.generate_executive_summary(selected_month, selected_year)
                            
                        if pdf_path and os.path.exists(pdf_path):
                            st.success(f"Report generated successfully!")
                            with open(pdf_path, "rb") as pdf_file:
                                st.download_button(
                                    label="📥 Download PDF",
                                    data=pdf_file,
                                    file_name=os.path.basename(pdf_path),
                                    mime="application/pdf",
                                    use_container_width=True
                                )
                    except Exception as e:
                        st.error(f"Error generating report: {str(e)}")

        with col2:
            st.info("💡 **Tip:** PDFs are automatically stamped with HMRL branding and saved to the local `reports/` folder.")


with tab2:
    st.subheader("🗂️ Report History")
    df_history = get_report_history()
    
    if df_history.empty:
        st.info("No reports generated yet.")
    else:
        # Simple display table
        display_df = df_history.copy()
        display_df['generated_at'] = pd.to_datetime(display_df['generated_at']).dt.strftime("%Y-%m-%d %H:%M")
        display_df['Size'] = display_df['file_size_kb'].astype(str) + " KB"
        display_df = display_df[['report_type', 'report_date', 'generated_at', 'username', 'Size', 'report_id', 'file_path']]
        display_df.columns = ['Report Type', 'Report Date', 'Generated At', 'Generated By', 'Size', 'ID', 'Path']
        
        st.dataframe(display_df[['ID', 'Report Type', 'Report Date', 'Generated At', 'Generated By', 'Size']], hide_index=True, use_container_width=True)
        
        st.markdown("### Actions")
        action_col1, action_col2 = st.columns([1, 1])
        with action_col1:
            dl_id = st.selectbox("Select Report ID to Download:", display_df['ID'].tolist())
            if dl_id:
                path = display_df[display_df['ID'] == dl_id]['Path'].values[0]
                if os.path.exists(path):
                    with open(path, "rb") as f:
                        st.download_button("📥 Download", data=f, file_name=os.path.basename(path), mime="application/pdf")
                else:
                    st.warning("File not found on disk.")
                    
        with action_col2:
            if can_perform_action(user['role'], 'delete_reports'):
                del_id = st.selectbox("Select Report ID to Delete:", display_df['ID'].tolist(), key="del")
                if st.button("🗑️ Delete Report", type="primary"):
                    if delete_report(del_id):
                        st.success("Report deleted successfully. Refresh the page.")
                    else:
                        st.error("Failed to delete.")
