# TransitFlow MySQL Integration Guide

## Setup Instructions
1. Install a local MySQL Server on your machine.
2. Create the required database and user:
   ```sql
   CREATE DATABASE transitflow_db;
   CREATE USER 'transitflow_user'@'localhost' IDENTIFIED BY 'YourStrongPassword123!';
   GRANT ALL PRIVILEGES ON transitflow_db.* TO 'transitflow_user'@'localhost';
   FLUSH PRIVILEGES;
   ```
3. Ensure `.env` is setup in your project root with your credentials.
4. Install dependencies: `pip install -r requirements.txt`

## Running Migrations
Run the Python scripts to automate loading your CSV data into MySQL:
```bash
cd scripts
python migrate_csv_to_mysql.py
python verify_migration.py
```

## Troubleshooting
- **Connection Error**: Check your MySQL service is running and credentials in `.env` match.
- **Missing Tables**: Rerun `migrate_csv_to_mysql.py` which uses `if_exists='replace'` to format and build the base tables automatically.
