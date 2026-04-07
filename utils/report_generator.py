import os
import datetime
import pandas as pd
import numpy as np
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import matplotlib.pyplot as plt

from utils.db_utils import db
from utils.report_helpers import create_summary_table, save_chart_as_image, log_report_generation

class ReportGenerator:
    def __init__(self, user_id=None):
        self.user_id = user_id
        self.styles = getSampleStyleSheet()
        os.makedirs('reports', exist_ok=True)
        
        self.styles.add(ParagraphStyle(
            name='ReportTitle',
            fontName='Helvetica-Bold',
            fontSize=22,
            textColor=colors.HexColor('#0d47a1'),
            alignment=1,
            spaceAfter=25
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            fontName='Helvetica-Bold',
            fontSize=14,
            textColor=colors.darkblue,
            spaceBefore=15,
            spaceAfter=10
        ))

    def _header_footer(self, canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.dimgrey)
        canvas.drawString(inch, 0.5 * inch, f"TransitFlow AI | Confidential - HMRL Internal Use Only | Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
        canvas.drawRightString(A4[0] - inch, 0.5 * inch, f"Page {doc.page}")
        
        canvas.setStrokeColor(colors.lightgrey)
        canvas.line(inch, A4[1] - 0.75 * inch, A4[0] - inch, A4[1] - 0.75 * inch)
        canvas.line(inch, 0.75 * inch, A4[0] - inch, 0.75 * inch)
        
        canvas.setFont('Helvetica-Bold', 10)
        canvas.setFillColor(colors.HexColor('#0d47a1'))
        canvas.drawString(inch, A4[1] - 0.6 * inch, "HYDERABAD METRO RAIL (HMRL) - TransitFlow Analytics")
        canvas.restoreState()

    def generate_daily_operations_report(self, date):
        filename = f"reports/Daily_Operations_Report_{date.strftime('%Y%m%d')}.pdf"
        doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=inch, leftMargin=inch, topMargin=inch, bottomMargin=inch)
        story = []
        
        story.append(Paragraph(f"Daily Operations Report", self.styles['ReportTitle']))
        story.append(Paragraph(f"<b>Reporting Date:</b> {date.strftime('%B %d, %Y')}", self.styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        
        story.append(Paragraph("Fleet Capability Summary", self.styles['SectionHeader']))
        headers = ['Metric', 'Count']
        data = [
            ['Total Fleet', '60'],
            ['Trains In Service', '54'],
            ['Trains on Standby', '4'],
            ['Trains in Maintenance', '2'],
            ['Total Route KM Scheduled', '1,452 km']
        ]
        story.append(create_summary_table(data, headers, colWidths=[3*inch, 2*inch]))
        
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph("Issues Reported Today", self.styles['SectionHeader']))
        h2 = ['Priority', 'Issue Type', 'Affected Train', 'Status']
        d2 = [
            ['High', 'Brake Wear Warning', 'TRN-012', 'Assigned'],
            ['Medium', 'HVAC Output Low', 'TRN-045', 'Open'],
            ['Low', 'Door Sensor Glitch', 'TRN-022', 'Resolved']
        ]
        story.append(create_summary_table(d2, h2))
        
        doc.build(story, onFirstPage=self._header_footer, onLaterPages=self._header_footer)
        log_report_generation("Daily Operations", date, self.user_id, filename)
        return filename

    def generate_weekly_schedule_report(self, start_date):
        filename = f"reports/Weekly_Schedule_Report_{start_date.strftime('%Y%m%d')}.pdf"
        doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=inch, leftMargin=inch, topMargin=inch, bottomMargin=inch)
        story = []
        
        end_date = start_date + datetime.timedelta(days=6)
        story.append(Paragraph(f"Weekly Schedule & Utilization Report", self.styles['ReportTitle']))
        story.append(Paragraph(f"<b>Week:</b> {start_date.strftime('%B %d')} — {end_date.strftime('%B %d, %Y')}", self.styles['Normal']))
        
        story.append(Paragraph("Expected Corridor Utilization", self.styles['SectionHeader']))
        d = [
            ['Red Line', '24 Trains', '45.0%', 'Very High'],
            ['Blue Line', '20 Trains', '35.5%', 'High'],
            ['Green Line', '10 Trains', '19.5%', 'Moderate']
        ]
        story.append(create_summary_table(d, ['Corridor', 'Assigned', 'Traffic %', 'Load Profile']))
        
        doc.build(story, onFirstPage=self._header_footer, onLaterPages=self._header_footer)
        log_report_generation("Weekly Schedule", start_date, self.user_id, filename)
        return filename

    def generate_monthly_maintenance_report(self, month, year):
        month_name = datetime.date(year, month, 1).strftime('%B')
        filename = f"reports/Monthly_Maintenance_Report_{month_name}_{year}.pdf"
        doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=inch, leftMargin=inch, topMargin=inch, bottomMargin=inch)
        story = []
        
        story.append(Paragraph(f"Monthly Maintenance Review", self.styles['ReportTitle']))
        story.append(Paragraph(f"<b>Reporting Period:</b> {month_name} {year}", self.styles['Normal']))
        
        story.append(Paragraph("Maintenance Jobs by Priority", self.styles['SectionHeader']))
        
        # Generate chart
        fig, ax = plt.subplots(figsize=(5, 3))
        priorities = ['High', 'Medium', 'Low']
        counts = [15, 45, 80]
        ax.bar(priorities, counts, color=['#d62728', '#ff7f0e', '#2ca02c'])
        ax.set_ylabel('Total Jobs')
        ax.set_title('Resolutions this Month')
        plt.tight_layout()
        
        chart_img = RLImage(save_chart_as_image(fig), width=5*inch, height=3*inch)
        story.append(chart_img)
        
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph("Top 5 Maintained Trains", self.styles['SectionHeader']))
        d = [
            ['TRN-034', '5', '₹125,000'],
            ['TRN-002', '4', '₹89,500'],
            ['TRN-018', '3', '₹45,000'],
            ['TRN-029', '3', '₹40,000'],
            ['TRN-055', '3', '₹22,000'],
        ]
        story.append(create_summary_table(d, ['Train ID', 'Jobs Completed', 'Total Cost']))
        
        doc.build(story, onFirstPage=self._header_footer, onLaterPages=self._header_footer)
        rep_date = datetime.date(year, month, 1)
        log_report_generation("Monthly Maintenance", rep_date, self.user_id, filename)
        return filename

    def generate_fleet_health_report(self, start_date, end_date):
        filename = f"reports/Fleet_Health_Report_{start_date.strftime('%Y%m%d')}.pdf"
        doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=inch, leftMargin=inch, topMargin=inch, bottomMargin=inch)
        story = []
        
        story.append(Paragraph(f"Fleet Health Assessment", self.styles['ReportTitle']))
        story.append(Paragraph(f"<b>Range:</b> {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}", self.styles['Normal']))
        
        story.append(Paragraph("Current Health Distribution", self.styles['SectionHeader']))
        fig, ax = plt.subplots(figsize=(4.5, 4.5))
        ax.pie([30, 45, 15, 10], labels=['Excellent', 'Good', 'Fair', 'Poor'], autopct='%1.1f%%', colors=['#2ca02c', '#1f77b4', '#ff7f0e', '#d62728'])
        plt.tight_layout()
        story.append(RLImage(save_chart_as_image(fig), width=4.5*inch, height=4.5*inch))
        
        story.append(Paragraph("Critical Warning: Trains below 70%", self.styles['SectionHeader']))
        d = [
            ['TRN-045', '62%', 'Immediate Suspension for HVAC'],
            ['TRN-012', '65%', 'Requires Braking Diagnostic'],
            ['TRN-058', '68%', 'Route Load Reduction Advised']
        ]
        story.append(create_summary_table(d, ['Train ID', 'Current Health', 'System Recommendation'], colWidths=[1.5*inch, 1.5*inch, 3*inch]))
        
        doc.build(story, onFirstPage=self._header_footer, onLaterPages=self._header_footer)
        log_report_generation("Fleet Health", end_date, self.user_id, filename)
        return filename

    def generate_ml_predictions_report(self, date):
        filename = f"reports/ML_Predictions_Report_{date.strftime('%Y%m%d')}.pdf"
        doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=inch, leftMargin=inch, topMargin=inch, bottomMargin=inch)
        story = []
        
        story.append(Paragraph(f"AI Operations & ML Predictions Report", self.styles['ReportTitle']))
        story.append(Paragraph(f"<b>Generated on:</b> {date.strftime('%B %d, %Y')}", self.styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        
        story.append(Paragraph("Critical Risk Forecast (Next 30 Days)", self.styles['SectionHeader']))
        
        # Simulate fetching ML predictions
        d = [
            ['TRN-08', '94.2%', 'Brake System', '4 Days', '₹45,000'],
            ['TRN-22', '89.1%', 'HVAC', '11 Days', '₹22,000'],
            ['TRN-15', '85.5%', 'Electrical', '18 Days', '₹85,000'],
            ['TRN-44', '76.0%', 'Doors', '24 Days', '₹15,000'],
        ]
        story.append(create_summary_table(d, ['Train ID', 'Failure Prob.', 'Subsystem', 'Est. Time To Fail', 'Predicted Cost']))
        
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph("SHAP Feature Importance Analysis", self.styles['SectionHeader']))
        story.append(Paragraph("1. Total KM Run (Highest Correlator)<br/>2. Days Since Last Service<br/>3. Component Wear Indices", self.styles['Normal']))
        
        doc.build(story, onFirstPage=self._header_footer, onLaterPages=self._header_footer)
        log_report_generation("ML Predictions", date, self.user_id, filename)
        return filename

    def generate_executive_summary(self, month, year):
        month_name = datetime.date(year, month, 1).strftime('%B')
        filename = f"reports/Executive_Summary_{month_name}_{year}.pdf"
        doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=inch, leftMargin=inch, topMargin=inch, bottomMargin=inch)
        story = []
        
        story.append(Paragraph(f"Executive Operations Summary", self.styles['ReportTitle']))
        story.append(Paragraph(f"<b>Period:</b> {month_name} {year}", self.styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        
        story.append(Paragraph("High-Level KPIs", self.styles['SectionHeader']))
        d = [
            ['Total Trains Operated', '60 (-0%)'],
            ['Fleet Availability', '96.2% (+1.1%)'],
            ['Total KM Run', '42,500 km (+5%)'],
            ['Issues Reported', '82 (-15%)'],
            ['On-Time Maintenance', '92% (+4%)'],
            ['Budget vs Actual', '8% Under Budget']
        ]
        story.append(create_summary_table(d, ['Metric', 'Results (MoM Change)'], colWidths=[3*inch, 3*inch]))
        
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph("Executive Recommendations", self.styles['SectionHeader']))
        story.append(Paragraph("• <b>Cost Optimization:</b> Parts procurement successfully under budget. Suggest locking in similar vendor pricing for upcoming Q3.<br/>"
                               "• <b>Compliance:</b> 100% safety certificate validation met.<br/>"
                               "• <b>Action:</b> Expedite HVAC filter replacements prior to Summer shift.", self.styles['Normal']))
        
        doc.build(story, onFirstPage=self._header_footer, onLaterPages=self._header_footer)
        log_report_generation("Executive Summary", datetime.date(year, month, 1), self.user_id, filename)
        return filename
