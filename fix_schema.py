#!/usr/bin/env python3
"""
Fix database schema mismatches in email routes
"""

import re

def fix_email_routes():
    """Fix all schema mismatches in routes/email.py"""
    
    print("🔧 Fixing database schema mismatches...")
    
    # Read the current file
    with open('routes/email.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Schema fixes mapping
    fixes = [
        # Fix column names
        ('emails.message', 'emails.body'),
        ('receiver_id', 'recipient'),  
        ('sender_id', 'sender'),
        ('emails.receiver_id', 'emails.recipient'),
        ('emails.sender_id', 'emails.sender'),
        
        # Fix JOIN queries - change to use email strings instead of user IDs
        ('LEFT JOIN users ON emails.receiver_id = users.id', 'LEFT JOIN users ON emails.recipient = users.email'),
        ('LEFT JOIN users ON emails.sender_id = users.id', 'LEFT JOIN users ON emails.sender = users.email'),
        ('JOIN users ON emails.receiver_id = users.id', 'JOIN users ON emails.recipient = users.email'),
        ('JOIN users ON emails.sender_id = users.id', 'JOIN users ON emails.sender = users.email'),
        
        # Fix WHERE clauses for user filtering
        ('WHERE emails.sender_id = %s', 'WHERE emails.sender = (SELECT email FROM users WHERE id = %s)'),
        ('WHERE emails.receiver_id = %s', 'WHERE emails.recipient = (SELECT email FROM users WHERE id = %s)'),
        ('AND emails.sender_id = %s', 'AND emails.sender = (SELECT email FROM users WHERE id = %s)'),
        ('AND emails.receiver_id = %s', 'AND emails.recipient = (SELECT email FROM users WHERE id = %s)'),
        ('OR emails.sender_id = %s', 'OR emails.sender = (SELECT email FROM users WHERE id = %s)'),
        ('OR emails.receiver_id = %s', 'OR emails.recipient = (SELECT email FROM users WHERE id = %s)'),
        
        # Fix INSERT statements
        ('INSERT INTO emails (sender_id, receiver_id', 'INSERT INTO emails (sender, recipient'),
        ('VALUES (%s, %s, %s, %s, %s)', 'VALUES ((SELECT email FROM users WHERE id = %s), %s, %s, %s, %s)'),
    ]
    
    # Apply fixes
    original_content = content
    for old, new in fixes:
        content = content.replace(old, new)
        if old in original_content:
            print(f"✅ Fixed: {old[:50]}... → {new[:50]}...")
    
    # Write back the fixed content
    with open('routes/email.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("🎉 Email routes schema fixes completed!")

if __name__ == "__main__":
    fix_email_routes()
