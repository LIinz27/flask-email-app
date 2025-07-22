import os

# Database configuration for different environments
if os.environ.get('DATABASE_URL') or os.environ.get('MYSQL_URL'):
    # Production environment (Railway, Heroku, etc.)
    DATABASE_URL = os.environ.get('DATABASE_URL') or os.environ.get('MYSQL_URL')
    # Parse DATABASE_URL for mysql-connector-python
    import urllib.parse as urlparse
    
    url = urlparse.urlparse(DATABASE_URL)
    db_config = {
        'host': url.hostname,
        'user': url.username,
        'password': url.password,
        'database': url.path[1:],  # Remove leading slash
        'port': url.port or 3306,
        'autocommit': True,
        'charset': 'utf8mb4'
    }
elif os.environ.get('MYSQL_HOST'):
    # Railway individual environment variables
    db_config = {
        'host': os.environ.get('MYSQL_HOST'),
        'user': os.environ.get('MYSQL_USER'),
        'password': os.environ.get('MYSQL_PASSWORD'),
        'database': os.environ.get('MYSQL_DATABASE'),
        'port': int(os.environ.get('MYSQL_PORT', 3306)),
        'autocommit': True,
        'charset': 'utf8mb4'
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
