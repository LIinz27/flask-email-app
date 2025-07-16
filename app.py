# === IMPORTS & APP INIT ===
from flask import Flask, render_template, request, redirect, session, url_for, flash
import mysql.connector
import bcrypt
from config import db_config

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
app.secret_key = 'your_secret_key'

# Initialize database tables
init_db()

# === DRAFTS ===
@app.route('/drafts')
def drafts():
    if 'user_id' not in session:
        return redirect('/login')
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute('''
        SELECT emails.*, users.username AS receiver_name
        FROM emails
        LEFT JOIN users ON emails.receiver_id = users.id
        WHERE emails.sender_id = %s AND emails.is_draft = 1
        ORDER BY emails.timestamp DESC
    ''', (user_id,))
    drafts = cursor.fetchall()
    cursor.close()
    db.close()
    from datetime import datetime
    for d in drafts:
        if d['timestamp'] and not isinstance(d['timestamp'], str):
            d['timestamp'] = d['timestamp']
    return render_template('drafts.html', drafts=drafts)

# === REGISTER ===
@app.route('/register', methods=['GET', 'POST'])
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

# === LOGIN ===
@app.route('/login', methods=['GET', 'POST'])
def login():
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
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect('/inbox')
        else:
            flash('Username atau password salah!', 'danger')

    return render_template('login.html')

# === LOGOUT ===
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/')
def index():
    return redirect('/login')


# === INBOX ===
@app.route('/inbox')
def inbox():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor(dictionary=True)

    # Ambil email yang diterima user saat ini
    cursor.execute("""
        SELECT emails.id, emails.subject, emails.message, emails.timestamp, 
               emails.is_read, users.username AS sender_name
        FROM emails
        JOIN users ON emails.sender_id = users.id
        WHERE emails.receiver_id = %s
        ORDER BY emails.timestamp DESC
    """, (user_id,))
    
    emails = cursor.fetchall()
    cursor.close()
    db.close()

    from datetime import datetime
    today = datetime.now().date()
    return render_template('inbox.html', emails=emails, today=today)

# === COMPOSE ===

# === COMPOSE & DRAFT ===
@app.route('/compose', methods=['GET', 'POST'])
@app.route('/compose/<int:draft_id>', methods=['GET', 'POST'])
def compose(draft_id=None):
    if 'user_id' not in session:
        return redirect('/login')

    db = get_db()
    cursor = db.cursor(dictionary=True)
    draft = None
    if draft_id:
        cursor.execute("SELECT * FROM emails WHERE id = %s AND sender_id = %s AND is_draft = 1", (draft_id, session['user_id']))
        draft = cursor.fetchone()

    if request.method == 'POST':
        receiver_username = request.form['receiver']
        subject = request.form['subject']
        message = request.form['message']
        sender_id = session['user_id']
        action = request.form.get('action')

        receiver_id = None
        if receiver_username:
            cursor.execute("SELECT id FROM users WHERE username = %s", (receiver_username,))
            receiver = cursor.fetchone()
            if receiver:
                receiver_id = receiver['id']

        if action == 'draft':
            if draft:  # update existing draft
                cursor.execute("""
                    UPDATE emails SET receiver_id=%s, subject=%s, message=%s, is_draft=1 WHERE id=%s AND sender_id=%s
                """, (receiver_id, subject, message, draft_id, sender_id))
                db.commit()
                flash('Draft berhasil diperbarui.', 'success')
                return redirect('/drafts')
            else:  # create new draft
                cursor.execute("""
                    INSERT INTO emails (sender_id, receiver_id, subject, message, is_draft)
                    VALUES (%s, %s, %s, %s, 1)
                """, (sender_id, receiver_id, subject, message))
                db.commit()
                flash('Draft berhasil disimpan.', 'success')
                return redirect('/drafts')
        elif action == 'send':
            if not receiver_id:
                flash('Username penerima tidak ditemukan.', 'danger')
                return render_template('compose.html', draft=draft)
            if draft:  # update draft and send
                cursor.execute("""
                    UPDATE emails SET receiver_id=%s, subject=%s, message=%s, is_draft=0 WHERE id=%s AND sender_id=%s
                """, (receiver_id, subject, message, draft_id, sender_id))
                db.commit()
                flash('Draft berhasil dikirim!', 'success')
                return redirect('/sent')
            else:  # new send
                cursor.execute("""
                    INSERT INTO emails (sender_id, receiver_id, subject, message, is_draft)
                    VALUES (%s, %s, %s, %s, 0)
                """, (sender_id, receiver_id, subject, message))
                db.commit()
                flash('Email berhasil dikirim!', 'success')
                return redirect('/sent')

    cursor.close()
    db.close()
    return render_template('compose.html', draft=draft)

# === SENT ===
@app.route('/sent')
def sent():
    if 'user_id' not in session:
        return redirect('/login')
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute('''
        SELECT emails.id, emails.subject, emails.message, emails.timestamp,
               users.username AS receiver_name
        FROM emails
        JOIN users ON emails.receiver_id = users.id
        WHERE emails.sender_id = %s
        ORDER BY emails.timestamp DESC
    ''', (user_id,))
    emails = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template('sent.html', emails=emails)

# === EMAIL DETAIL ===
@app.route('/email/<int:email_id>')
def email_detail(email_id):
    if 'user_id' not in session:
        return redirect('/login')
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute('''
        SELECT emails.*, 
               sender.username AS sender_name, 
               receiver.username AS receiver_name
        FROM emails
        JOIN users sender ON emails.sender_id = sender.id
        JOIN users receiver ON emails.receiver_id = receiver.id
        WHERE emails.id = %s AND (emails.sender_id = %s OR emails.receiver_id = %s)
    ''', (email_id, user_id, user_id))
    email = cursor.fetchone()
    
    # Mark as read if the current user is the receiver
    if email and email['receiver_id'] == user_id and not email['is_read']:
        cursor.execute('UPDATE emails SET is_read = 1 WHERE id = %s', (email_id,))
        db.commit()
        email['is_read'] = True
    
    cursor.close()
    db.close()
    if not email:
        flash('Email tidak ditemukan atau akses ditolak.', 'danger')
        return redirect('/inbox')
    return render_template('email_detail.html', email=email)

# === PROFILE ===
@app.route('/profile')
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

# === CHANGE PASSWORD ===
@app.route('/change_password', methods=['GET', 'POST'])
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

# === MARK EMAIL AS READ ===
@app.route('/mark_as_read/<int:email_id>')
def mark_as_read(email_id):
    if 'user_id' not in session:
        return redirect('/login')
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute('UPDATE emails SET is_read = 1 WHERE id = %s AND receiver_id = %s', (email_id, user_id))
    db.commit()
    cursor.close()
    db.close()
    return '', 204  # No content response

# === GET UNREAD COUNT ===
@app.route('/unread_count')
def unread_count():
    if 'user_id' not in session:
        return {'count': 0}
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute('SELECT COUNT(*) as count FROM emails WHERE receiver_id = %s AND is_read = 0', (user_id,))
    result = cursor.fetchone()
    cursor.close()
    db.close()
    return {'count': result['count']}

# === FAVORITES ===
@app.route('/favorites')
def favorites():
    if 'user_id' not in session:
        return redirect('/login')
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute('''
        SELECT emails.*, 
               sender.username AS sender_name,
               receiver.username AS receiver_name
        FROM emails
        JOIN users sender ON emails.sender_id = sender.id
        JOIN users receiver ON emails.receiver_id = receiver.id
        WHERE (emails.receiver_id = %s OR emails.sender_id = %s)
        AND emails.is_favorite = 1
        ORDER BY emails.timestamp DESC
    ''', (user_id, user_id))
    favorites = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template('favorites.html', emails=favorites)

# === TOGGLE FAVORITE ===
@app.route('/toggle_favorite/<int:email_id>')
def toggle_favorite(email_id):
    if 'user_id' not in session:
        return redirect('/login')
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    # First check if user has access to this email
    cursor.execute('''
        SELECT is_favorite
        FROM emails
        WHERE id = %s AND (sender_id = %s OR receiver_id = %s)
    ''', (email_id, user_id, user_id))
    email = cursor.fetchone()
    
    if email:
        new_state = not email['is_favorite']
        cursor.execute('''
            UPDATE emails 
            SET is_favorite = %s 
            WHERE id = %s
        ''', (new_state, email_id))
        db.commit()
        message = 'Email ditambahkan ke favorit.' if new_state else 'Email dihapus dari favorit.'
        flash(message, 'success')
    else:
        flash('Email tidak ditemukan atau akses ditolak.', 'danger')
    
    cursor.close()
    db.close()
    return redirect(request.referrer or url_for('inbox'))

if __name__ == '__main__':
    app.run(debug=True)
