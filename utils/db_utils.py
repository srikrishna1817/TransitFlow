import os
import mysql.connector
from mysql.connector import Error
from sqlalchemy import create_engine
import pandas as pd
import logging
from dotenv import load_dotenv

load_dotenv()  # loads .env locally, ignored on cloud

DB_CONFIG = {
    "host": os.environ.get("MYSQLHOST"),
    "port": int(os.environ.get("MYSQLPORT", 3306)),
    "user": os.environ.get("MYSQLUSER"),
    "password": os.environ.get("MYSQLPASSWORD"),
    "database": os.environ.get("MYSQLDATABASE")
}

# Add required MySQL connection properties safely
conn_config = DB_CONFIG.copy()
conn_config['charset'] = 'utf8mb4'
conn_config['use_unicode'] = True
conn_config['autocommit'] = True

# SQLAlchemy connection string format: mysql+pymysql://user:password@host:port/dbname
SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename='db_operations.log')

class DatabaseManager:
    """Manages all MySQL database connections and operations"""
    
    def __init__(self):
        """Initialize connection and engine variables"""
        self.config = conn_config
        self.connection = None
        self.engine = None
        
    def connect(self):
        """Create MySQL connection using mysql.connector"""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connection = mysql.connector.connect(**self.config)
            return self.connection
        except Error as e:
            logging.error(f"Error connecting to MySQL: {e}")
            return None

    def get_sqlalchemy_engine(self):
        """Return SQLAlchemy engine for pandas operations"""
        try:
            if not self.engine:
                self.engine = create_engine(SQLALCHEMY_DATABASE_URL)
            return self.engine
        except Exception as e:
            logging.error(f"Error creating SQLAlchemy engine: {e}")
            return None

    def close(self):
        """Close database connection properly"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logging.info("Database connection closed.")

    def execute_query(self, query, params=None, fetch=False):
        """Execute single query with optional fetch"""
        conn = self.connect()
        if not conn:
            return None
            
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params or ())
            
            if fetch:
                result = cursor.fetchall()
                cursor.close()
                return result
            else:
                conn.commit()
                cursor.close()
                return True
        except Error as e:
            logging.error(f"Failed to execute query '{query}': {e}")
            return None

    def fetch_dataframe(self, query, params=None):
        """Return query results as pandas DataFrame"""
        engine = self.get_sqlalchemy_engine()
        if not engine:
            return None
        try:
            return pd.read_sql_query(query, con=engine, params=params)
        except Exception as e:
            logging.error(f"Failed to fetch dataframe: {e}")
            return None

    def insert_dataframe(self, df, table_name, if_exists='append'):
        """Insert DataFrame into MySQL table"""
        engine = self.get_sqlalchemy_engine()
        if not engine:
            return False
            
        try:
            df.to_sql(name=table_name, con=engine, if_exists=if_exists, index=False)
            logging.info(f"Successfully inserted {len(df)} rows into {table_name}")
            return True
        except Exception as e:
            logging.error(f"Failed to insert dataframe into {table_name}: {e}")
            return False

    def update_record(self, table, updates, condition, params=None):
        """Update records in table. 
        Example: update_record('users', 'status = %s', 'id = %s', ('active', 5))"""
        query = f"UPDATE {table} SET {updates} WHERE {condition}"
        return self.execute_query(query, params, fetch=False)

    def delete_record(self, table, condition, params=None):
        """Delete records from table"""
        query = f"DELETE FROM {table} WHERE {condition}"
        return self.execute_query(query, params, fetch=False)

# Singleton accessible instance
db = DatabaseManager()
