
# === IMPORTS & APP INIT ===
from flask import Flask, redirect, render_template
from config import db_config
import mysql.connector
import bcrypt
import os
import secrets

def get_db():
    return mysql.connector.connect(**db_config)

# Initialize database when app starts
def init_db():
    db = get_db()
    cursor = db.cursor()
    try:
        # Check if is_read column exists
        cursor.execute("""
            SELECT COUNT(*)
            FROM information_schema.COLUMNS
            WHERE TABLE_NAME = 'emails'
            AND COLUMN_NAME = 'is_read'
        """)
        if cursor.fetchone()[0] == 0:
            # Add is_read column if it doesn't exist
            cursor.execute("""
                ALTER TABLE emails
                ADD COLUMN is_read BOOLEAN DEFAULT 0
            """)
            db.commit()
        # Check if is_draft column exists
        cursor.execute("""
            SELECT COUNT(*)
            FROM information_schema.COLUMNS
            WHERE TABLE_NAME = 'emails'
            AND COLUMN_NAME = 'is_draft'
        """)
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                ALTER TABLE emails
                ADD COLUMN is_draft BOOLEAN DEFAULT 0
            """)
            db.commit()
            
        # Check if is_favorite column exists
        cursor.execute("""
            SELECT COUNT(*)
            FROM information_schema.COLUMNS
            WHERE TABLE_NAME = 'emails'
            AND COLUMN_NAME = 'is_favorite'
        """)
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                ALTER TABLE emails
                ADD COLUMN is_favorite BOOLEAN DEFAULT 0
            """)
            db.commit()
    except Exception as e:
        print(f"Error initializing database: {e}")
    finally:
        cursor.close()
        db.close()


app = Flask(__name__)
# Generate new secret key on each restart to invalidate old sessions
app.secret_key = secrets.token_hex(16)
print(f"New session secret generated: {app.secret_key[:8]}...")

# Configure session to not be permanent
app.permanent_session_lifetime = 0  # Session expires when browser closes

# Initialize database tables
init_db()

# Register Blueprints
from routes.auth import auth_bp, is_session_valid
from routes.email import email_bp
from routes.profile import profile_bp

app.register_blueprint(auth_bp)
app.register_blueprint(email_bp)
app.register_blueprint(profile_bp)

# Middleware untuk validasi session
@app.before_request
def validate_session():
    from flask import request, session, redirect, flash
    
    # Skip validation untuk auth routes dan static files
    if (request.endpoint and 
        (request.endpoint.startswith('auth.') or 
         request.endpoint.startswith('static') or
         request.endpoint == 'index')):
        return None
    
    # Validate session untuk route yang membutuhkan login
    if 'user_id' in session:
        if not is_session_valid():
            session.clear()
            flash('Sesi telah berakhir karena server di-restart. Silakan login kembali.', 'warning')
            return redirect('/login')
    elif request.endpoint:  # User belum login
        return redirect('/login')

# Index route
@app.route('/')
def index():
    return redirect('/login')

# === ERROR HANDLERS ===
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True)
