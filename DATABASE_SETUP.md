# PostgreSQL Configuration Guide

## Overview

The CyberDefence platform now supports both **SQLite** (default) and **PostgreSQL** databases. The system automatically detects which database to use based on the `DATABASE_URL` environment variable.

- **When `DATABASE_URL` is NOT set:** Uses SQLite (data/cyberdefence.db) - perfect for development
- **When `DATABASE_URL` is set:** Uses PostgreSQL - recommended for production

---

## Quick Start

### Option 1: SQLite (Development - Default)

No configuration needed! Just run:

```bash
# Backend will use SQLite automatically
uvicorn frontend.backend.api:app --reload
```

Database file will be created at: `data/cyberdefence.db`

---

### Option 2: PostgreSQL (Production)

#### Step 1: Install PostgreSQL

**Windows:**
- Download: https://www.postgresql.org/download/windows/
- Run installer, remember your password
- Default port: 5432

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
```

**macOS:**
```bash
brew install postgresql
brew services start postgresql
```

---

#### Step 2: Create Database and User

Open PostgreSQL prompt:

```bash
# Windows: 
psql -U postgres

# Linux/macOS:
sudo -u postgres psql
```

Then run these SQL commands:

```sql
-- Create database
CREATE DATABASE cyberdefence;

-- Create user with password
CREATE USER cyberdefence_user WITH PASSWORD 'your-secure-password';

-- Grant privileges
ALTER ROLE cyberdefence_user SET client_encoding TO 'utf8';
ALTER ROLE cyberdefence_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE cyberdefence_user SET default_transaction_deferrable TO on;
ALTER ROLE cyberdefence_user SET default_transaction_read_only TO off;
GRANT ALL PRIVILEGES ON DATABASE cyberdefence TO cyberdefence_user;

-- Connect to database
\c cyberdefence

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO cyberdefence_user;

-- Exit
\q
```

---

#### Step 3: Configure .env File

Edit `.env` in project root:

```env
# Add this line
DATABASE_URL=postgresql://cyberdefence_user:your-secure-password@localhost:5432/cyberdefence

# Other settings remain the same
ENVIRONMENT=production
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_EMAIL=your-email@gmail.com
SMTP_PASSWORD=your-gmail-app-password
FRONTEND_URL=http://localhost:5173
SECRET_KEY=your-secret-key-here
```

---

#### Step 4: Start Backend

```bash
uvicorn frontend.backend.api:app --reload
```

The system will:
1. Detect `DATABASE_URL`
2. Connect to PostgreSQL
3. Create tables automatically
4. Start serving API

**Console output will show:**
```
[✓] Database: PostgreSQL
[✓] URL: postgresql://cyberdefence_user:...@localhost:5432/cyberdefence
INFO:     Uvicorn running on http://127.0.0.1:8000
```

---

## Database URL Format

```
postgresql://username:password@host:port/database_name
```

### Examples

**Local PostgreSQL:**
```
postgresql://cyberdefence_user:mypassword@localhost:5432/cyberdefence
```

**With non-default port:**
```
postgresql://cyberdefence_user:mypassword@localhost:5433/cyberdefence
```

**Remote server:**
```
postgresql://cyberdefence_user:mypassword@db.example.com:5432/cyberdefence
```

**Render PostgreSQL (production):**
```
postgresql://user:password@dpg-xxxxx.c.aws-us-east-1.render.com:5432/database_name
```

**AWS RDS:**
```
postgresql://admin:password@cyberdefence-db.c9akciq32.us-east-1.rds.amazonaws.com:5432/cyberdefence
```

---

## Remote PostgreSQL Services

### Render.com (Recommended - $7/month)

1. Create account at https://render.com
2. Create new PostgreSQL database
3. Copy connection string from Dashboard
4. Add to `.env`:
   ```env
   DATABASE_URL=postgresql://user:password@dpg-xxxx.render.com:5432/database
   ```

### AWS RDS

1. Create RDS PostgreSQL database
2. Copy endpoint from AWS Console
3. Add to `.env`:
   ```env
   DATABASE_URL=postgresql://admin:password@your-instance.rds.amazonaws.com:5432/cyberdefence
   ```

### Heroku Postgres

1. Create Heroku app with PostgreSQL addon
2. Get DATABASE_URL from `heroku config:get DATABASE_URL`
3. Add to `.env`:
   ```env
   DATABASE_URL=postgres://user:password@ec2-xxx.amazonaws.com:5432/dbname
   ```

---

## How to Check Which Database is Being Used

### Check at Runtime

Look at API startup messages:

```bash
# SQLite - default
[✓] Database: SQLite
[✓] Path: d:\...\data\cyberdefence.db

# PostgreSQL
[✓] Database: PostgreSQL  
[✓] URL: postgresql://user:password@localhost:5432/cyberdefence
```

### Programmatically

In Python code:
```python
from frontend.backend.db import db, get_database_info

info = get_database_info()
print(f"Database type: {info['type']}")  # 'SQLite' or 'PostgreSQL'
```

---

## Migrating from SQLite to PostgreSQL

### Step 1: Export SQLite Data (if needed)

```bash
# Backup SQLite database
cp data/cyberdefence.db data/cyberdefence.db.backup
```

### Step 2: Create PostgreSQL Database

Follow "Step 1-2" above to create PostgreSQL database and user.

### Step 3: Update .env

```env
DATABASE_URL=postgresql://user:password@localhost:5432/cyberdefence
```

### Step 4: Restart Backend

```bash
uvicorn frontend.backend.api:app --reload
```

Tables will be created automatically in PostgreSQL. To migrate existing data, see "Data Migration" section below.

---

## Data Migration (SQLite → PostgreSQL)

### Using Python Script

Create `migrate_db.py`:

```python
import sqlite3
import psycopg2
import json
from datetime import datetime

# Connect to SQLite
sqlite_conn = sqlite3.connect('data/cyberdefence.db')
sqlite_cursor = sqlite_conn.cursor()

# Connect to PostgreSQL
pg_conn = psycopg2.connect(
    "dbname=cyberdefence user=cyberdefence_user password=password host=localhost"
)
pg_cursor = pg_conn.cursor()

# Migrate users table
sqlite_cursor.execute("SELECT * FROM users")
users = sqlite_cursor.fetchall()
for user in users:
    pg_cursor.execute(
        """INSERT INTO users 
        (id, email, full_name, organization, password_hash, created_at, last_login, is_active, reset_token, reset_token_expiry)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
        user
    )

# Migrate scans table
sqlite_cursor.execute("SELECT * FROM scans")
scans = sqlite_cursor.fetchall()
for scan in scans:
    pg_cursor.execute(
        """INSERT INTO scans
        (id, target, module, timestamp, results, user_id)
        VALUES (%s, %s, %s, %s, %s, %s)""",
        scan
    )

pg_conn.commit()
pg_cursor.close()
pg_conn.close()
sqlite_cursor.close()
sqlite_conn.close()

print("✅ Migration complete!")
```

Run migration:
```bash
python migrate_db.py
```

---

## Troubleshooting

### Error: "psycopg2 not installed"

Solution:
```bash
pip install psycopg2-binary
```

### Error: "could not connect to database server"

Checklist:
- [ ] Is PostgreSQL running? (`sudo systemctl status postgresql` on Linux)
- [ ] Is port 5432 open? (`telnet localhost 5432`)
- [ ] Is DATABASE_URL correct in `.env`?
- [ ] Database user has correct password?
- [ ] Database exists? (`\l` in psql)

### Error: "FATAL: role does not exist"

Solution: User doesn't exist. Create it:
```sql
CREATE USER cyberdefence_user WITH PASSWORD 'password';
```

### Error: "FATAL: database does not exist"

Solution: Database not created. Create it:
```sql
CREATE DATABASE cyberdefence OWNER cyberdefence_user;
```

### Falling back to SQLite when PostgreSQL errors

The system automatically falls back to SQLite if PostgreSQL connection fails. This is safe but check logs for the error:

Look for:
```
[!] Warning: DATABASE_URL is set but psycopg2 is not installed.
[!] Falling back to SQLite...
```

Or:
```
[!] PostgreSQL connection failed: ...
[!] Falling back to SQLite...
```

---

## Performance Comparison

| Aspect | SQLite | PostgreSQL |
|--------|--------|-----------|
| Development | ✅ Perfect | Setup overhead |
| Multi-user | Single | Handles many concurrent |
| Scalability | Limited | Enterprise-grade |
| Backups | Simple | More complex |
| Reliability | Dev-only | Production-ready |
| Typical users | < 10 | 100+ concurrent |

---

## Security Best Practices

### For Production

1. **Use strong passwords:**
   ```sql
   CREATE USER cyberdefence_user WITH PASSWORD 'MyStr0ng!P@ssw0rd123';
   ```

2. **Restrict user permissions:**
   ```sql
   GRANT CONNECT ON DATABASE cyberdefence TO cyberdefence_user;
   GRANT USAGE ON SCHEMA public TO cyberdefence_user;
   GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO cyberdefence_user;
   ```

3. **Use environment variables:**
   ```bash
   # Never commit DATABASE_URL to git!
   export DATABASE_URL="postgresql://user:password@host:5432/db"
   ```

4. **Enable SSL connections:**
   ```
   DATABASE_URL=postgresql://user:password@host:5432/db?sslmode=require
   ```

5. **Regular backups:**
   ```bash
   pg_dump cyberdefence > backup_$(date +%Y%m%d).sql
   ```

---

## Next Steps

1. Choose SQLite for development or PostgreSQL for production
2. Update `.env` with correct DATABASE_URL
3. Restart backend - database tables created automatically
4. Start scanning!

For deployment to production (Render, AWS, etc.), see [DEPLOYMENT.md](DEPLOYMENT.md)
