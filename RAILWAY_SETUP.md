# Railway Database Setup Instructions

## Step 1: Add MySQL Database in Railway

1. Go to your Railway project dashboard
2. Click "New" → "Database" → "Add MySQL"
3. Railway will automatically create a MySQL database
4. Copy the connection details

## Step 2: Set Environment Variables

Railway will automatically set these variables:
- `MYSQL_URL` (we'll use this as DATABASE_URL)
- `MYSQL_HOST`
- `MYSQL_PORT` 
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_DATABASE`

## Step 3: Manual Environment Variables (if needed)

Add these in Railway dashboard under "Variables":

```
FLASK_ENV=production
SECRET_KEY=your-super-secret-key-change-this
DATABASE_URL=${{MYSQL_URL}}
```

## Step 4: Initialize Database Tables

After database is connected, the app will automatically create tables on first run.

## Troubleshooting

If the app still doesn't work:
1. Check logs in Railway dashboard
2. Ensure database is running
3. Verify environment variables are set correctly

## Database Schema

The app will automatically create these tables:
- `users` (id, username, email, password_hash, full_name, created_at)
- `emails` (id, sender, recipient, subject, body, timestamp, is_read, is_draft, is_favorite)
