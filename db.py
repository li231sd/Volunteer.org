import sqlite3
from config import Config

# Global database connection
conn = sqlite3.connect(Config.DATABASE_PATH, check_same_thread=False, isolation_level=None)
db = conn.cursor()

def get_db():
    """Get database cursor"""
    return db

def execute_query(query, params=None):
    """Execute a query and return results"""
    if params:
        return db.execute(query, params)
    else:
        return db.execute(query)

def fetchone(query, params=None):
    """Execute query and fetch one result"""
    if params:
        return db.execute(query, params).fetchone()
    else:
        return db.execute(query).fetchone()

def fetchall(query, params=None):
    """Execute query and fetch all results"""
    if params:
        return db.execute(query, params).fetchall()
    else:
        return db.execute(query).fetchall()
    