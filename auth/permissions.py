"""auth/permissions.py — Role-Based Access Control."""

# Pages each role is allowed to access
PAGE_ACCESS = {
    'Admin':            {'Home','Schedule','Maintenance','Analytics','Alerts','Settings','ML_Insights','Predictive_Analytics','Reports','Simulation'},
    'Scheduler':        {'Home','Schedule','Analytics','Alerts','ML_Insights','Predictive_Analytics','Reports','Simulation'},
    'Maintenance_Team': {'Home','Maintenance','Analytics','Alerts','Predictive_Analytics','Reports','Simulation'},
    'Viewer':           {'Home','Schedule','Maintenance','Analytics','Predictive_Analytics','Reports','Simulation'},
}

# Fine-grained action permissions
ACTION_ACCESS = {
    'generate_schedule':  {'Admin','Scheduler'},
    'update_maintenance': {'Admin','Maintenance_Team'},
    'retrain_model':      {'Admin'},
    'manage_users':       {'Admin'},
    'acknowledge_alerts': {'Admin','Scheduler','Maintenance_Team'},
    'export_data':        {'Admin','Scheduler'},
    'generate_all_reports': {'Admin','Scheduler'},
    'generate_maintenance_reports': {'Admin','Maintenance_Team'},
    'delete_reports':     {'Admin'},
}

ROLE_LABELS = {
    'Admin':            '🔴 Admin',
    'Scheduler':        '🟠 Scheduler',
    'Maintenance_Team': '🔵 Maintenance Team',
    'Viewer':           '🟢 Viewer',
}

ROLE_COLORS = {
    'Admin':            '#d62728',
    'Scheduler':        '#ff7f0e',
    'Maintenance_Team': '#1f77b4',
    'Viewer':           '#2ca02c',
}


def can_access_page(role: str, page_name: str) -> bool:
    return page_name in PAGE_ACCESS.get(role, set())


def can_perform_action(role: str, action_name: str) -> bool:
    return role in ACTION_ACCESS.get(action_name, set())


def get_role_label(role: str) -> str:
    return ROLE_LABELS.get(role, role)


def get_role_color(role: str) -> str:
    return ROLE_COLORS.get(role, '#888')
