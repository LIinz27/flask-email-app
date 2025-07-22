
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
    cursor.execute('DELETE FROM emails WHERE id = %s AND sender = %s AND is_draft = 1', (draft_id, user_id))
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
        SELECT emails.*, emails.recipient AS receiver_name
        FROM emails
        LEFT JOIN users ON emails.recipient = users.id
        WHERE emails.sender = %s AND emails.is_draft = 1
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
        SELECT emails.id, emails.subject, emails.body, emails.timestamp, 
               emails.is_read, emails.sender AS sender_name
        FROM emails
        JOIN users ON emails.sender = users.id
        WHERE emails.recipient = %s
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
        cursor.execute("SELECT * FROM emails WHERE id = %s AND sender = %s AND is_draft = 1", (draft_id, session['user_id']))
        draft = cursor.fetchone()
    if request.method == 'POST':
        receiver_username = request.form['receiver']
        subject = request.form['subject']
        message = request.form['message']
        sender = session['user_id']
        action = request.form.get('action')
        recipient = None
        if receiver_username:
            cursor.execute("SELECT id FROM users WHERE username = %s", (receiver_username,))
            receiver = cursor.fetchone()
            if receiver:
                recipient = receiver['id']
        
        # Handle auto-save draft
        if action == 'auto_draft':
            # Jika ada draft_id, update existing draft
            if draft:
                cursor.execute("""
                    UPDATE emails SET recipient=%s, subject=%s, message=%s, is_draft=1 WHERE id=%s AND sender=%s
                """, (recipient, subject, message, draft_id, sender))
                db.commit()
            else:
                # Cek apakah ada auto-draft existing untuk user ini (draft yang tidak memiliki judul khusus)
                cursor.execute("""
                    SELECT id FROM emails WHERE sender = %s AND is_draft = 1 
                    AND (subject = '' OR subject IS NULL OR subject LIKE 'Auto-draft%')
                    ORDER BY timestamp DESC LIMIT 1
                """, (sender,))
                existing_auto_draft = cursor.fetchone()
                
                if existing_auto_draft:
                    # Update existing auto-draft
                    cursor.execute("""
                        UPDATE emails SET recipient=%s, subject=%s, message=%s WHERE id=%s
                    """, (recipient, subject, message, existing_auto_draft['id']))
                    db.commit()
                else:
                    # Create new auto-draft
                    cursor.execute("""
                        INSERT INTO emails (sender, recipient, subject, body, is_draft)
                        VALUES (%s, %s, %s, %s, 1)
                    """, (sender, recipient, subject, message))
                    db.commit()
            
            cursor.close()
            db.close()
            return '', 204  # Return success without content for AJAX
            
        elif action == 'draft':
            if draft:  # update existing draft
                cursor.execute("""
                    UPDATE emails SET recipient=%s, subject=%s, message=%s, is_draft=1 WHERE id=%s AND sender=%s
                """, (recipient, subject, message, draft_id, sender))
                db.commit()
                flash('Draft berhasil diperbarui.', 'success')
                return redirect('/drafts')
            else:  # create new draft
                cursor.execute("""
                    INSERT INTO emails (sender, recipient, subject, body, is_draft)
                    VALUES (%s, %s, %s, %s, 1)
                """, (sender, recipient, subject, message))
                db.commit()
                flash('Draft berhasil disimpan.', 'success')
                return redirect('/drafts')
        elif action == 'send':
            if not recipient:
                flash('Username penerima tidak ditemukan.', 'danger')
                return render_template('compose.html', draft=draft)
            if draft:  # update draft and send
                cursor.execute("""
                    UPDATE emails SET recipient=%s, subject=%s, message=%s, is_draft=0 WHERE id=%s AND sender=%s
                """, (recipient, subject, message, draft_id, sender))
                db.commit()
                flash('Draft berhasil dikirim!', 'success')
                return redirect('/sent')
            else:  # new send
                cursor.execute("""
                    INSERT INTO emails (sender, recipient, subject, body, is_draft)
                    VALUES (%s, %s, %s, %s, 0)
                """, (sender, recipient, subject, message))
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
        SELECT emails.id, emails.subject, emails.body, emails.timestamp,
               emails.recipient AS receiver_name
        FROM emails
        JOIN users ON emails.recipient = users.id
        WHERE emails.sender = %s
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
               emails.sender AS sender_name, 
               emails.recipient AS receiver_name
        FROM emails
        JOIN users sender ON emails.sender = sender.id
        JOIN users receiver ON emails.recipient = receiver.id
        WHERE emails.id = %s AND (emails.sender = %s OR emails.recipient = %s)
    ''', (email_id, user_id, user_id))
    email = cursor.fetchone()
    # Mark as read if the current user is the receiver
    if email and email['recipient'] == user_id and not email['is_read']:
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
    cursor.execute('UPDATE emails SET is_read = 1 WHERE id = %s AND recipient = %s', (email_id, user_id))
    db.commit()
    cursor.close()
    db.close()
    return '', 204

# === GET UNREAD COUNT ===
@email_bp.route('/unread_count')
def unread_count():
    if 'user_id' not in session:
        from flask import jsonify
        return jsonify({'count': 0})
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute('SELECT COUNT(*) as count FROM emails WHERE recipient = %s AND is_read = 0', (user_id,))
    result = cursor.fetchone()
    cursor.close()
    db.close()
    from flask import jsonify
    return jsonify({'count': result['count']})

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
               emails.sender AS sender_name,
               emails.recipient AS receiver_name
        FROM emails
        JOIN users sender ON emails.sender = sender.id
        JOIN users receiver ON emails.recipient = receiver.id
        WHERE (emails.recipient = %s OR emails.sender = %s)
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
        WHERE id = %s AND (sender = %s OR recipient = %s)
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

# === SEARCH ===
@email_bp.route('/search')
def search():
    if 'user_id' not in session:
        return redirect('/login')
    
    query = request.args.get('q', '').strip()
    user_id = session['user_id']
    emails = []
    
    if query:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        # Search in subject, message, and sender name
        search_query = f"%{query}%"
        cursor.execute("""
            SELECT emails.id, emails.subject, emails.body, emails.timestamp, 
                   emails.is_read, emails.sender AS sender_name, 'inbox' AS type
            FROM emails
            JOIN users ON emails.sender = users.id
            WHERE emails.recipient = %s 
                AND (emails.subject LIKE %s OR emails.body LIKE %s OR users.username LIKE %s)
            
            UNION
            
            SELECT emails.id, emails.subject, emails.body, emails.timestamp, 
                   emails.is_read, emails.recipient AS receiver_name, 'sent' AS type
            FROM emails
            LEFT JOIN users ON emails.recipient = users.id
            WHERE emails.sender = %s 
                AND emails.is_draft = 0
                AND (emails.subject LIKE %s OR emails.body LIKE %s OR users.username LIKE %s)
            
            ORDER BY timestamp DESC
        """, (user_id, search_query, search_query, search_query, 
              user_id, search_query, search_query, search_query))
        
        emails = cursor.fetchall()
        cursor.close()
        db.close()
    
    today = datetime.now().date()
    return render_template('search.html', emails=emails, query=query, today=today)
