
from flask import Blueprint, render_template, request, redirect, session, flash, url_for
import mysql.connector
from config import db_config
from datetime import datetime

def get_db():
    return mysql.connector.connect(**db_config)

email_bp = Blueprint('email', __name__)

# === DELETE DRAFT ===
@email_bp.route('/delete_draft/<int:draft_id>', methods=['POST'])
def delete_draft(draft_id):
    if 'user_id' not in session:
        return redirect('/login')
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute('DELETE FROM emails WHERE id = %s AND sender_id = %s AND is_draft = 1', (draft_id, user_id))
    db.commit()
    cursor.close()
    db.close()
    flash('Draft berhasil dihapus.', 'success')
    return redirect(url_for('email.drafts'))

# === DRAFTS ===
@email_bp.route('/drafts')
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
    for d in drafts:
        if d['timestamp'] and not isinstance(d['timestamp'], str):
            d['timestamp'] = d['timestamp']
    return render_template('drafts.html', drafts=drafts)

# === INBOX ===
@email_bp.route('/inbox')
def inbox():
    if 'user_id' not in session:
        return redirect('/login')
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor(dictionary=True)
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
    today = datetime.now().date()
    return render_template('inbox.html', emails=emails, today=today)

# === COMPOSE & DRAFT ===
@email_bp.route('/compose', methods=['GET', 'POST'])
@email_bp.route('/compose/<int:draft_id>', methods=['GET', 'POST'])
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
@email_bp.route('/sent')
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
@email_bp.route('/email/<int:email_id>')
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

# === MARK EMAIL AS READ ===
@email_bp.route('/mark_as_read/<int:email_id>')
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
    return '', 204

# === GET UNREAD COUNT ===
@email_bp.route('/unread_count')
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
@email_bp.route('/favorites')
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
@email_bp.route('/toggle_favorite/<int:email_id>')
def toggle_favorite(email_id):
    if 'user_id' not in session:
        return redirect('/login')
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor(dictionary=True)
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
