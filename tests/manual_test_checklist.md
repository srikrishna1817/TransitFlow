# TransitFlow Manual UI Testing Checklist

## General & Authentication
- [ ] Login screen renders correctly (inputs, forgot password link).
- [ ] Login with `Admin` works. (Access to 9 pages).
- [ ] Login with `Scheduler` works. (No access to Settings/Users).
- [ ] Login with `Maintenance_Team` works. (No scheduling capabilities).
- [ ] Login with `Viewer` works. (Read-only on all forms).
- [ ] Logout functionality destroys session completely.
- [ ] Incorrect username/password shows valid error banner (no DB traceback).

## Home Page
- [ ] KPIs at the top evaluate correctly (Total Trains, etc.).
- [ ] Navigation shortcuts correctly jump to corresponding pages.

## Schedule Planning
- [ ] 'Generate Schedule' button works flawlessly.
- [ ] Map distribution confirms 25 Red, 23 Blue, 12 Green.
- [ ] Expandable alerts accordion loads maintenance and crew overlaps correctly.

## Maintenance Logs
- [ ] "Log New Maintenance" inserts record dynamically into the MySQL database.
- [ ] "Mark Resolved" toggles jobs to historical.
- [ ] Form strictly accepts valid dates (Resolved >= Reported).

## Analytics & ML Insights
- [ ] SHAP Waterfall chart renders perfectly.
- [ ] Fleet Health timeline dynamically changes with slider dates.
- [ ] Accuracy KPIs match the cross-validated ML engine output.

## Predictive Analytics (Hub)
- [ ] 30-Day ML Line Chart and shaded standard deviation loads seamlessly.
- [ ] Calendar heatmap handles "empty" predictions perfectly using simulation fallback.
- [ ] Cost Bar Chart correctly compares 90-day history with 30-day forecasted costs.
- [ ] Seasonal Stacked Bar Chart groups issues by Indian seasons.

## Reports Engine
- [ ] Can switch between 6 different dropdown options.
- [ ] Report generation completes without hanging.
- [ ] Generated file is a valid PDF.
- [ ] Table renders dynamically inside the Report History tab.
- [ ] Admin can delete reports smoothly.

## Settings & Administration
- [ ] Role hierarchy enforced (cannot downgrade super admins).
- [ ] Add New User successfully hashes password to DB using bcrypt.
- [ ] "Download DB Core Backup" works perfectly.
