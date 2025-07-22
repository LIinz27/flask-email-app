#!/usr/bin/env python3
"""
Test Railway database connection
"""

import os
from config import db_config
import mysql.connector

def test_connection():
    print("=== Railway Database Connection Test ===")
    print()
    
    # Print environment info
    print("Environment Variables:")
    env_vars = ['DATABASE_URL', 'MYSQL_URL', 'MYSQL_HOST', 'MYSQL_USER', 'MYSQL_DATABASE', 'MYSQL_PORT']
    for var in env_vars:
        value = os.environ.get(var, 'Not Set')
        if var in ['MYSQL_PASSWORD', 'DATABASE_URL', 'MYSQL_URL'] and value != 'Not Set':
            value = value[:10] + "..." if len(value) > 10 else value
        print(f"  {var}: {value}")
    print()
    
    # Print db_config (masked password)
    print("Database Configuration:")
    for key, value in db_config.items():
        if key == 'password':
            print(f"  {key}: {'*' * len(str(value))}")
        else:
            print(f"  {key}: {value}")
    print()
    
    # Test connection
    try:
        print("Testing connection...")
        db = mysql.connector.connect(**db_config)
        cursor = db.cursor()
        
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()
        print(f"✅ Connection successful!")
        print(f"✅ MySQL Version: {version[0]}")
        
        cursor.execute("SHOW DATABASES")
        databases = cursor.fetchall()
        print(f"✅ Available databases: {[db[0] for db in databases]}")
        
        cursor.close()
        db.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    test_connection()
