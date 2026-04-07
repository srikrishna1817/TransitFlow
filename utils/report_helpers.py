import io
import os
import matplotlib.pyplot as plt
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from utils.db_utils import db

def save_chart_as_image(fig):
    """Save matplotlib figure as BytesIO for embedding in PDF"""
    img_buf = io.BytesIO()
    fig.savefig(img_buf, format='png', bbox_inches='tight', dpi=300)
    img_buf.seek(0)
    plt.close(fig)
    return img_buf

def format_currency(amount):
    """Format numbers as Indian currency (₹X,XX,XXX)"""
    return f"₹{amount:,.0f}"

def create_summary_table(data, headers, colWidths=None):
    """Create a beautifully styled ReportLab table"""
    table_data = [headers] + data
    t = Table(table_data, colWidths=colWidths)
    
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f2f2f2')),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')])
    ])
    t.setStyle(style)
    return t

def log_report_generation(report_type, report_date, generated_by, file_path):
    """Log generated report into the report_history table"""
    try:
        if not os.path.exists(file_path):
            file_size_kb = 0
        else:
            file_size_kb = os.path.getsize(file_path) // 1024
            
        query = """
        INSERT INTO report_history (report_type, report_date, generated_by, file_path, file_size_kb)
        VALUES (%s, %s, %s, %s, %s)
        """
        db.execute_query(query, (report_type, report_date, generated_by, file_path, file_size_kb))
    except Exception as e:
        print(f"Failed to log report: {e}")

def get_report_history():
    """Fetch all report histories with user names"""
    try:
        query = """
        SELECT r.report_id, r.report_type, r.report_date, r.generated_at, r.file_path, r.file_size_kb, u.username
        FROM report_history r
        LEFT JOIN users u ON r.generated_by = u.user_id
        ORDER BY r.generated_at DESC
        """
        df = db.fetch_dataframe(query)
        if df is None:
            import pandas as pd
            return pd.DataFrame()
        return df
    except Exception:
        import pandas as pd
        return pd.DataFrame()

def delete_report(report_id):
    """Delete a report from the database and potentially disk"""
    try:
        # Get path first
        query = "SELECT file_path FROM report_history WHERE report_id=%s"
        rows = db.execute_query(query, (report_id,), fetch=True)
        if rows:
            path = rows[0].get('file_path')
            if path and os.path.exists(path):
                os.remove(path)
                
        # Delete from DB
        db.execute_query("DELETE FROM report_history WHERE report_id=%s", (report_id,))
        return True
    except Exception as e:
        print(f"Delete report error: {e}")
        return False
