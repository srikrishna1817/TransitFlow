import os
from dotenv import load_dotenv

# Load environmental variables from .env file
load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'transitflow_user'),
    'password': os.getenv('DB_PASSWORD', 'YourStrongPassword123!'),
    'database': os.getenv('DB_NAME', 'transitflow_db'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'charset': 'utf8mb4',
    'use_unicode': True,
    'autocommit': True
}

# SQLAlchemy connection string format: mysql+pymysql://user:password@host:port/dbname
SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
