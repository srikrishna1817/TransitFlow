# TransitFlow Defect Tracker

| Bug ID | Severity (1-3) | Page Element / Feature | Description | Status | Fixed in Version | Fixed by | Notes / Resolution Steps |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **BUG-001** | 3 (Low) | Settings Page | 'DB Backup' button spins indefinitely if database is over 500MB | **RESOLVED** | v1.1 | AI Engineering | Simulated asynchronous streaming chunk logic |
| **BUG-002** | 2 (Med) | Reports Engine | Missing internal formatting breaks page loops | **RESOLVED** | v1.1 | QA/Testing | Handled `dict` object typing bounds cleanly |
| **BUG-003** | 1 (High)| ML Predictions | SHAP waterfall chart crashes on `np.nan` inputs | **RESOLVED** | v1.1 | AI Engineering | Handled missing features directly in ML pipeline imputation |
| **BUG-004** | 2 (Med) | Authentication | Edge case: Multiple logins from same cache / Session Timeout | **RESOLVED** | v1.1 | Security | Enforced expiry checks and cache-busting redirects |
| **BUG-005** | 2 (Med) | Dashboards | Gantt chart natively overlapping rendering text on trains | **RESOLVED** | v1.1 | UI/UX Team | Hardcoded auto-height rendering algorithms into Plotly configurations |
| **BUG-006** | 1 (High)| Fleet Schedule | Crew scheduling exceeding basic 8-hour legal caps | **RESOLVED** | v1.1 | Engine Team | Overrode `crew_scheduler.py` assignment capabilities to truncate loops |
| **BUG-007** | 1 (High)| Report Builder | Report PDFs occasionally corrupting or generating empty | **RESOLVED** | v1.1 | QA/Testing | Built robust error handling and verification gates before byte writing |
| **BUG-008** | 3 (Low) | Layout / Mobile | Layouts & Charts not rendering cleanly on Mobile / Small displays | **RESOLVED** | v1.1 | UI/UX Team | Bound all `st.plotly_chart` items directly with `use_container_width=True` |
