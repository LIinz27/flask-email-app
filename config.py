import os

# Database configuration for different environments
if os.environ.get('DATABASE_URL'):
    # Production environment (Railway, Heroku, etc.)
    DATABASE_URL = os.environ.get('DATABASE_URL')
    # Parse DATABASE_URL for mysql-connector-python
    import urllib.parse as urlparse
    
    url = urlparse.urlparse(DATABASE_URL)
    db_config = {
        'host': url.hostname,
        'user': url.username,
        'password': url.password,
        'database': url.path[1:],  # Remove leading slash
        'port': url.port or 3306
    }
else:
    # Local development
    db_config = {
        'host': os.environ.get('DB_HOST', 'localhost'),
        'user': os.environ.get('DB_USER', 'root'),
        'password': os.environ.get('DB_PASSWORD', 'admin'),
        'database': os.environ.get('DB_NAME', 'email_app'),
        'port': int(os.environ.get('DB_PORT', 3306))
    }
