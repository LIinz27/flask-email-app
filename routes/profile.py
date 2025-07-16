from flask import Blueprint, render_template, request, redirect, session, flash
import bcrypt
import mysql.connector
from config import db_config

def get_db():
    return mysql.connector.connect(**db_config)

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect('/login')
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute('SELECT username, email FROM users WHERE id = %s', (user_id,))
    user = cursor.fetchone()
    cursor.close()
    db.close()
    return render_template('profile.html', user=user)

@profile_bp.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if 'user_id' not in session:
        return redirect('/login')
    if request.method == 'POST':
        current_password = request.form['current_password'].encode('utf-8')
        new_password = request.form['new_password'].encode('utf-8')
        confirm_password = request.form['confirm_password'].encode('utf-8')
        if new_password != confirm_password:
            flash('Konfirmasi password baru tidak cocok.', 'danger')
            return redirect('/change_password')
        user_id = session['user_id']
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute('SELECT password FROM users WHERE id = %s', (user_id,))
        user = cursor.fetchone()
        if not user or not bcrypt.checkpw(current_password, user['password'].encode('utf-8')):
            flash('Password lama salah.', 'danger')
            cursor.close()
            db.close()
            return redirect('/change_password')
        hashed_pw = bcrypt.hashpw(new_password, bcrypt.gensalt())
        cursor.execute('UPDATE users SET password = %s WHERE id = %s', (hashed_pw, user_id))
        db.commit()
        cursor.close()
        db.close()
        flash('Password berhasil diubah.', 'success')
        return redirect('/profile')
    return render_template('change_password.html')
