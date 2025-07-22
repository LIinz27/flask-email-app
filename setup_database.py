#!/usr/bin/env python3
"""
Database initialization script for Railway MySQL
Run this after MySQL database is connected
"""

import mysql.connector
import os
from config import db_config

def create_tables():
    """Create all required tables for the email app"""
    try:
        print("Connecting to database...")
        db = mysql.connector.connect(**db_config)
        cursor = db.cursor()
        
        print("Creating tables...")
        
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(80) UNIQUE NOT NULL,
                email VARCHAR(120) UNIQUE NOT NULL,
                password_hash VARCHAR(128) NOT NULL,
                full_name VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create emails table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS emails (
                id INT AUTO_INCREMENT PRIMARY KEY,
                sender VARCHAR(120) NOT NULL,
                recipient VARCHAR(120) NOT NULL,
                subject VARCHAR(200) NOT NULL,
                body TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_read BOOLEAN DEFAULT 0,
                is_draft BOOLEAN DEFAULT 0,
                is_favorite BOOLEAN DEFAULT 0
            )
        """)
        
        db.commit()
        print("✅ Tables created successfully!")
        
        # Insert sample admin user (optional)
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
        if cursor.fetchone()[0] == 0:
            # Default password: 'admin123' (hashed)
            from werkzeug.security import generate_password_hash
            hashed_pw = generate_password_hash('admin123')
            
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, full_name) 
                VALUES (%s, %s, %s, %s)
            """, ('admin', 'admin@email.com', hashed_pw, 'Administrator'))
            db.commit()
            print("✅ Default admin user created (username: admin, password: admin123)")
        
        cursor.close()
        db.close()
        print("✅ Database initialization completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure MySQL database is running and environment variables are set correctly.")

if __name__ == "__main__":
    create_tables()
