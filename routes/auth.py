from flask import Blueprint, render_template, request, redirect, session, flash
auth_bp = Blueprint('auth', __name__)
import bcrypt
import mysql.connector
from config import db_config
import time

# Store server start time to validate sessions
SERVER_START_TIME = time.time()

def get_db():
    return mysql.connector.connect(**db_config)

def is_session_valid():
    """Check if session is valid (created after server restart)"""
    session_time = session.get('created_at', 0)
    return session_time > SERVER_START_TIME

def create_session(user_id, username):
    """Create a new session with timestamp"""
    session.clear()  # Clear any existing session
    session['user_id'] = user_id
    session['username'] = username
    session['created_at'] = time.time()
    session.permanent = False  # Session expires when browser closes

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password'].encode('utf-8')
        hashed_pw = bcrypt.hashpw(password, bcrypt.gensalt())

        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                           (username, email, hashed_pw))
            db.commit()
            flash('Registrasi berhasil, silakan login.', 'success')
            return redirect('/login')
        except mysql.connector.IntegrityError:
            flash('Username sudah digunakan!', 'danger')
        finally:
            cursor.close()
            db.close()
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Clear any existing invalid session
    if 'user_id' in session and not is_session_valid():
        session.clear()
        flash('Sesi telah berakhir, silakan login kembali.', 'info')
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password'].encode('utf-8')

        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        db.close()

        if user and bcrypt.checkpw(password, user['password'].encode('utf-8')):
            create_session(user['id'], user['username'])
            flash(f'Selamat datang, {user["username"]}!', 'success')
            return redirect('/inbox')
        else:
            flash('Username atau password salah!', 'danger')

    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect('/login')
