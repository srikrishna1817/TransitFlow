# 🚇 TransitFlow — Hyderabad Metro Rail AI Scheduling System

A comprehensive AI-powered scheduling and operations management 
system for Hyderabad Metro Rail (HMRL), built with Streamlit, 
MySQL, and Machine Learning.

## 🌐 Live Demo
**URL:** https://transitflow-hmrl.streamlit.app

| Role | Username | Password |
|------|----------|----------|
| Admin | admin | admin123 |
| Scheduler | scheduler | scheduler123 |
| Maintenance | maintenance | maint123 |
| Viewer | viewer | viewer123 |

## ✨ Features

- **AI Schedule Optimization** — Genetic Algorithm-based train 
  and crew scheduling across Red, Blue, and Green metro lines
- **ML Predictions** — Multi-output predictor with SHAP 
  explainability for fleet health and maintenance forecasting
- **Real-time Simulation** — Live train movement simulation 
  across all HMRL stations
- **Predictive Analytics** — 90-day fleet health trends, 
  30-day maintenance calendar, cost forecasting
- **Automated Reports** — PDF report generation with 
  6 report types including Executive Summary
- **Role-based Access** — 4 roles with feature-level 
  permissions (Admin, Scheduler, Maintenance, Viewer)
- **Alert System** — Real-time critical/warning/info alerts 
  with acknowledgment

## 🛠️ Tech Stack

| Category | Technologies |
|----------|-------------|
| Frontend | Streamlit 1.32.2 |
| Database | MySQL (Railway Cloud) |
| ML | scikit-learn, XGBoost, LightGBM, SHAP |
| Scheduling | DEAP (Genetic Algorithms) |
| Visualization | Plotly, Matplotlib |
| Auth | bcrypt |
| Reports | ReportLab |
| Deployment | Streamlit Cloud |

## 📱 Pages

| Page | Description |
|------|-------------|
| 🔐 Login | Role-based authentication |
| 🏠 Home | Fleet overview dashboard |
| 📅 Schedule | Gantt charts, route maps, shift planner |
| 🔧 Maintenance | Job tracking and fleet health |
| 📊 Analytics | GA vs Heuristic performance comparison |
| 🚨 Alerts | Real-time alert management |
| ⚙️ Settings | System configuration |
| 🤖 ML Insights | AI predictions with SHAP explainability |
| 📈 Predictive Analytics | Forecasting dashboards |
| 📄 Reports | Automated PDF report generation |
| 🚇 Simulation | Real-time HMRL train simulation |

## 🧬 Computational Intelligence

Two Genetic Algorithm implementations replace traditional 
heuristic approaches:

- **GA Crew Scheduler** — Optimizes 120 crew members across 
  8-hour shifts with labor law compliance
- **GA Route Optimizer** — Assigns trains to Red/Blue/Green 
  lines maximizing coverage and fleet health

## 🚀 Local Setup

1. Clone the repository:
   git clone https://github.com/srikrishna1817/TransitFlow.git
   cd TransitFlow

2. Install dependencies:
   pip install -r requirements.txt

3. Setup environment variables in .env:
   MYSQLHOST=your_host
   MYSQLPORT=3306
   MYSQLUSER=your_user
   MYSQLPASSWORD=your_password
   MYSQLDATABASE=transitflow_db

4. Setup database:
   python scripts/create_auth_tables.py
   python scripts/create_default_users.py
   python generate_data.py
   cd scripts && python migrate_csv_to_mysql.py && cd ..

5. Run:
   streamlit run app.py

## 📊 Dataset

- 60 trains across 3 metro lines
- 17,000+ historical operation records
- 365 days of seasonal data
- 180 fitness certificates
- 39 maintenance jobs

## 👨‍💻 Developer

**Srikrishna Kausik Kasivajhula**
GitHub: [@srikrishna1817](https://github.com/srikrishna1817)