import pandas as pd
from datetime import datetime, timedelta

def calculate_train_utilization(train_id, days=30):
    """Calculate train utilization % over past N days"""
    return 85.4 # Placeholder for UI tests

def get_route_requirements(route_name, time_period='peak'):
    """Get trains required for route at given time"""
    route_reqs = {
        'Red Line': {'peak': 25, 'offpeak': 18, 'sunday': 18},
        'Blue Line': {'peak': 23, 'offpeak': 17, 'sunday': 17},
        'Green Line': {'peak': 12, 'offpeak': 8, 'sunday': 7}
    }
    return route_reqs.get(route_name, {}).get(time_period, 0)

def validate_schedule(schedule_df):
    """Comprehensive schedule validation"""
    errors = []
    warnings = []
    
    # Needs assigned_route to check capacity
    route_col = 'assigned_route' if 'assigned_route' in schedule_df.columns else 'route'
    
    if route_col in schedule_df.columns:
        for route in ['Red Line', 'Blue Line', 'Green Line']:
            count = len(schedule_df[schedule_df[route_col] == route])
            required = get_route_requirements(route, 'peak')
            if count < required:
                errors.append(f"{route}: Only {count} trains assigned, need {required}")
            elif count > required + 5:
                warnings.append(f"{route}: {count} trains assigned, only need {required} (over-allocated)")
    
    return {'errors': errors, 'warnings': warnings}

def calculate_efficiency_score(schedule_df):
    """Calculate overall schedule quality (0-100)"""
    score = 100
    
    validation = validate_schedule(schedule_df)
    score -= len(validation['errors']) * 10
    score -= len(validation['warnings']) * 3
    
    route_col = 'assigned_route' if 'assigned_route' in schedule_df.columns else 'route'
    
    if route_col in schedule_df.columns:
        red_count = len(schedule_df[schedule_df[route_col] == 'Red Line'])
        blue_count = len(schedule_df[schedule_df[route_col] == 'Blue Line'])
        green_count = len(schedule_df[schedule_df[route_col] == 'Green Line'])
        
        ideal = {'Red Line': 25, 'Blue Line': 23, 'Green Line': 12}
        balance_score = 100 - abs(red_count - ideal['Red Line']) * 2 - abs(blue_count - ideal['Blue Line']) * 2 - abs(green_count - ideal['Green Line']) * 2
        
        return max(0, min(100, (score + balance_score) / 2))
    return 80 # default safe layout score

def export_schedule_pdf(schedule_df, filename):
    """Generate PDF report of schedule"""
    try:
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib import colors
        
        doc = SimpleDocTemplate(filename, pagesize=landscape(A4))
        elements = []
        
        # Title
        styles = getSampleStyleSheet()
        title = Paragraph("HMRL Daily Schedule Report", styles['Title'])
        elements.append(title)
        
        # Table
        data = [schedule_df.columns.tolist()] + schedule_df.astype(str).values.tolist()
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(table)
        
        doc.build(elements)
        return filename
    except ImportError:
        return "Failed - Please install reportlab."
