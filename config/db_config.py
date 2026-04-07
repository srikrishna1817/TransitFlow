import os
import sys
import streamlit as st
from dotenv import load_dotenv

# Load environmental variables from .env file
load_dotenv()  # loads .env locally, ignored on cloud

DB_CONFIG = {
    "host": os.environ.get("MYSQLHOST"),
    "port": int(os.environ.get("MYSQLPORT", 3306)) if os.environ.get("MYSQLPORT") else 3306,
    "user": os.environ.get("MYSQLUSER"),
    "password": os.environ.get("MYSQLPASSWORD"),
    "database": os.environ.get("MYSQLDATABASE")
}

required_keys = ["host", "user", "password", "database"]
missing_keys = [key for key in required_keys if not DB_CONFIG[key]]

if missing_keys:
    error_msg = "Database configuration missing. Please check environment variables."
    print(error_msg)
    try:
        st.error(error_msg)
    except:
        pass

DB_CONFIG['charset'] = 'utf8mb4'
DB_CONFIG['use_unicode'] = True
DB_CONFIG['autocommit'] = True

# SQLAlchemy connection string format: mysql+pymysql://user:password@host:port/dbname
SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
