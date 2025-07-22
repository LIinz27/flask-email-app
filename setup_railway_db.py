#!/usr/bin/env python3
"""
Setup database with Railway MySQL connection
"""

import mysql.connector
import os

def setup_railway_db():
    """Setup database menggunakan Railway MySQL credentials"""
    
    # Railway MySQL connection info (menggunakan public URL untuk akses external)
    railway_config = {
        'host': 'shuttle.proxy.rlwy.net',
        'user': 'root', 
        'password': 'UROjVgOwOprYUPvuaiMYWaQgZAgmFmHb',
        'database': 'railway',
        'port': 30655,  # Railway TCP proxy port
        'autocommit': True,
        'charset': 'utf8mb4'
    }
    
    try:
        print("=== Railway Database Setup ===")
        print("Connecting to Railway MySQL...")
        
        db = mysql.connector.connect(**railway_config)
        cursor = db.cursor()
        
        print("✅ Connected to Railway MySQL!")
        
        # Create tables
        print("Creating tables...")
        
        # Drop existing tables if they exist (untuk update struktur)
        cursor.execute("DROP TABLE IF EXISTS emails")
        cursor.execute("DROP TABLE IF EXISTS users")
        
        # Create users table
        cursor.execute("""
            CREATE TABLE users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(80) UNIQUE NOT NULL,
                email VARCHAR(120) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
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
        
        print("✅ Tables created successfully!")
        
        # Check for existing admin user
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
        if cursor.fetchone()[0] == 0:
            # Create default admin user
            from werkzeug.security import generate_password_hash
            hashed_pw = generate_password_hash('admin123')
            
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, full_name) 
                VALUES (%s, %s, %s, %s)
            """, ('admin', 'admin@email.com', hashed_pw, 'Administrator'))
            
            print("✅ Default admin user created!")
            print("   Username: admin")
            print("   Password: admin123")
        else:
            print("✅ Admin user already exists")
        
        # Show table info
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"✅ Database tables: {[table[0] for table in tables]}")
        
        cursor.close()
        db.close()
        
        print("\n🎉 Database setup completed successfully!")
        print("URL aplikasi Anda: https://web-production-cc0cb.up.railway.app")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    setup_railway_db()
