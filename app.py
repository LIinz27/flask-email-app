
# === IMPORTS & APP INIT ===
from flask import Flask, redirect, render_template
from config import db_config
import mysql.connector
import os

def get_db():
    try:
        return mysql.connector.connect(**db_config)
    except mysql.connector.Error as e:
        print(f"Database connection error: {e}")
        print("Database config:", {k: v if k != 'password' else '***' for k, v in db_config.items()})
        raise

# Initialize database when app starts
def init_db():
    try:
        db = get_db()
        cursor = db.cursor()
        print("Database connection successful!")
    except Exception as e:
        print(f"Cannot connect to database during init: {e}")
        print("Skipping database initialization - app will still start...")
        return
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

# Session configuration - production ready
app.secret_key = os.environ.get('SECRET_KEY', 'email-app-secret-key-2025-very-long-and-secure')
app.config.update(
    SESSION_COOKIE_NAME='email_session',
    SESSION_COOKIE_SECURE=os.environ.get('FLASK_ENV') == 'production',  # True for HTTPS in production
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=3600  # 1 hour
)

# Initialize database tables
try:
    init_db()
    print("Database initialization completed successfully!")
except Exception as e:
    print(f"Warning: Database initialization failed: {e}")
    print("App will continue to run, but database features may not work until database is configured.")

# Register Blueprints
from routes.auth import auth_bp
from routes.email import email_bp
from routes.profile import profile_bp

app.register_blueprint(auth_bp)
app.register_blueprint(email_bp)
app.register_blueprint(profile_bp)

# Middleware untuk validasi session
@app.before_request
def validate_session():
    from flask import request, session, redirect, flash
    
    # Skip validation untuk routes yang tidak memerlukan login
    skip_routes = ['auth.login', 'auth.register', 'static', 'index', 'email.unread_count']
    
    if request.endpoint in skip_routes or (request.endpoint and request.endpoint.startswith('static')):
        return None
    
    # Check if user is logged in
    if 'user_id' not in session:
        if request.endpoint:  # Only redirect if it's a real endpoint
            flash('Session telah berakhir, silakan login kembali.', 'warning')
            return redirect('/login')

# Index route
@app.route('/')
def index():
    return redirect('/login')

# Health check route for Railway
@app.route('/health')
def health_check():
    return {'status': 'healthy', 'message': 'Flask app is running'}, 200

# === ERROR HANDLERS ===
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
