#!/usr/bin/env python3
"""
Fix JOIN queries that still use old schema
"""

def fix_join_queries():
    """Fix JOIN queries to work with email-based schema"""
    
    print("🔧 Fixing JOIN queries...")
    
    # Read the current file
    with open('routes/email.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Complex JOIN fixes
    join_fixes = [
        # Fix simple username lookups - just show email instead of username for now
        ('users.username AS receiver_name', 'emails.recipient AS receiver_name'),
        ('users.username AS sender_name', 'emails.sender AS sender_name'),
        
        # Remove problematic JOINs for now - we'll use emails directly
        ('LEFT JOIN users ON emails.recipient = users.email', ''),
        ('LEFT JOIN users ON emails.sender = users.email', ''),
        ('JOIN users ON emails.recipient = users.email', ''),
        ('JOIN users ON emails.sender = users.email', ''),
        
        # Complex JOINs with aliases
        ('LEFT JOIN users AS sender ON emails.sender = sender.email', ''),
        ('LEFT JOIN users AS receiver ON emails.recipient = receiver.email', ''),
        ('sender.username AS sender_name,', 'emails.sender AS sender_name,'),
        ('receiver.username AS receiver_name', 'emails.recipient AS receiver_name'),
    ]
    
    original_content = content
    for old, new in join_fixes:
        if old in content:
            content = content.replace(old, new)
            print(f"✅ Fixed JOIN: {old[:50]}...")
    
    # Write back the fixed content
    with open('routes/email.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("🎉 JOIN queries fixed!")

if __name__ == "__main__":
    fix_join_queries()
