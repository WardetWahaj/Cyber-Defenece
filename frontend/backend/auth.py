"""
Authentication module for CyberDefence Platform v3.1
Handles user management, JWT tokens, and password security.
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime, timedelta, timezone
import hashlib
import secrets
import hmac
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv(ROOT_DIR / ".env")

# ── Database abstraction layer (import from db module) ──────────────
# Consolidates PostgreSQL/SQLite switching, connection management, and environment config
from frontend.backend.db import DatabaseConnection, USE_POSTGRESQL

def get_db_connection():
    """Get a new database connection (delegates to db.py)."""
    db = DatabaseConnection()
    return db.connect()

# ── SQL Placeholder Conversion Helper ──────────────────────────────
# TODO: Replace with db.py's built-in _convert_placeholders() method when all code is migrated
def execute_query(cursor, query: str, params: tuple = ()) -> None:
    """
    Execute a query with automatic placeholder conversion.
    Converts PostgreSQL %s placeholders to SQLite ? placeholders when needed.
    
    Args:
        cursor: Database cursor
        query: SQL query (can use %s for any database)
        params: Query parameters as tuple
    """
    # Retrieve database type from db module to determine placeholder conversion
    if not USE_POSTGRESQL:
        # Convert %s placeholders to ? for SQLite
        query = query.replace("%s", "?")
    cursor.execute(query, params)

def fetch_query(cursor, query: str, params: tuple = ()) -> list:
    """
    Execute a SELECT query and fetch results with automatic placeholder conversion.
    
    Args:
        cursor: Database cursor
        query: SQL query (can use %s for any database)
        params: Query parameters as tuple
        
    Returns:
        List of fetched rows
    """
    execute_query(cursor, query, params)
    return cursor.fetchall()

from pydantic import BaseModel, EmailStr, validator
import jwt

# ── Configuration ──────────────────────────────────────────────────
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")  # development or production
SECRET_KEY = os.getenv("SECRET_KEY", "")
if ENVIRONMENT == "production" and (not SECRET_KEY or SECRET_KEY == "your-super-secret-key-change-in-production"):
    raise RuntimeError("FATAL: SECRET_KEY environment variable must be set in production. Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(32))\"")
if not SECRET_KEY:
    SECRET_KEY = "dev-only-insecure-key-not-for-production"
    print("[WARNING] No SECRET_KEY set — using insecure default. Set SECRET_KEY env var for production.")
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24
REFRESH_TOKEN_EXPIRE_DAYS = 7
PASSWORD_RESET_TOKEN_EXPIRE_HOURS = 1

# ── Password hashing using Argon2id ────────────────────────────────
try:
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError, InvalidHash
    ARGON2_AVAILABLE = True
except ImportError:
    ARGON2_AVAILABLE = False

if ARGON2_AVAILABLE:
    ph = PasswordHasher()
else:
    print("[!] Warning: argon2-cffi not installed. Using fallback password hashing.")

def hash_password(password: str) -> str:
    """Hash a password using Argon2id or PBKDF2 fallback."""
    if ARGON2_AVAILABLE:
        try:
            return ph.hash(password)
        except Exception as e:
            print(f"[!] Argon2 hashing failed: {e}, using fallback")
    
    # Fallback: PBKDF2-SHA256 with salt
    salt = secrets.token_hex(32)  # 64 character hex string
    derived = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 480000)
    return f"pbkdf2_sha256$480000${salt}${derived.hex()}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    if not hashed_password:
        return False
    
    # Try Argon2 first
    if ARGON2_AVAILABLE and hashed_password.startswith("$argon2"):
        try:
            ph.verify(hashed_password, plain_password)
            return True
        except (VerifyMismatchError, InvalidHash, Exception):
            pass
    
    # Try PBKDF2 fallback
    if hashed_password.startswith("pbkdf2_sha256$"):
        try:
            parts = hashed_password.split("$")
            if len(parts) == 4:
                iterations = int(parts[1])
                salt = parts[2]
                stored_hash = parts[3]
                derived = hashlib.pbkdf2_hmac('sha256', plain_password.encode('utf-8'), salt.encode('utf-8'), iterations)
                return hmac.compare_digest(derived.hex(), stored_hash)
        except Exception:
            pass
    
    return False

# ── JWT Token Management ───────────────────────────────────────────
def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> dict | None:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token with 7-day expiry."""
    to_encode = data.copy()
    to_encode.update({"type": "refresh"})
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_refresh_token(token: str) -> dict | None:
    """Verify and decode a refresh JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            return None
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def create_password_reset_token(email: str) -> str:
    """Create a password reset token."""
    data = {"email": email, "type": "password_reset"}
    return create_access_token(data, expires_delta=timedelta(hours=PASSWORD_RESET_TOKEN_EXPIRE_HOURS))

# ── Email Management ───────────────────────────────────────────────
def send_reset_email(to_email: str, reset_url: str, user_name: str) -> bool:
    """
    Send password reset email via Gmail SMTP (production only).
    
    ✅ PRODUCTION MODE ONLY - No development logging to file
    ✅ Raw token NEVER appears in logs or files
    ✅ Always sends real email via Gmail SMTP
    
    Args:
        to_email: Recipient email address
        reset_url: Full reset URL with token (e.g., http://localhost:5173/reset-password/TOKEN)
        user_name: User's full name for personalization
        
    Returns:
        True if email sent successfully
        
    Raises:
        Exception: If email sending fails (API endpoint will catch and return 500)
    """
    # Get SMTP configuration from environment variables
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    sender_email = os.getenv("SMTP_EMAIL")
    sender_password = os.getenv("SMTP_PASSWORD")
    
    # Validate SMTP credentials are configured
    if not sender_email or not sender_password:
        error_msg = "SMTP credentials not configured in .env (SMTP_EMAIL, SMTP_PASSWORD)"
        print(f"❌ {error_msg}")
        raise ValueError(error_msg)
    
    try:
        # Create message with both plain text and HTML versions
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "🔐 Password Reset — Cyber Defence"
        msg["From"] = f"Cyber Defence Security <{sender_email}>"
        msg["To"] = to_email
        
        # Plain text version (fallback for email clients without HTML support)
        text_body = f"""Hi {user_name},

You requested a password reset for your CyberDefence account.

Reset link: {reset_url}

This link expires in 1 hour.
If you did not request this, ignore this email.

— Cyber Defence Security Platform"""
        
        # HTML version with dark cybersecurity theme
        html_body = f"""<html>
  <body style="background-color:#0d1117; font-family:Arial,sans-serif; color:#c9d1d9;">
    <div style="max-width:600px; margin:0 auto; padding:40px 20px;">
      
      <!-- Header -->
      <div style="text-align:center; padding-bottom:20px; border-bottom:2px solid #238636;">
        <h2 style="color:#58a6ff; margin:0;">🔐 Cyber Defence</h2>
      </div>
      
      <!-- Main Content -->
      <div style="padding:30px 0;">
        <p style="font-size:16px;">Hi <strong>{user_name}</strong>,</p>
        
        <p>You requested a password reset for your CyberDefence account.</p>
        
        <!-- Reset Button -->
        <div style="text-align:center; margin:30px 0;">
          <a href="{reset_url}" 
             style="display:inline-block; background-color:#238636; color:#ffffff; 
                    padding:14px 32px; border-radius:6px; text-decoration:none; 
                    font-weight:bold; transition:background-color 0.3s;">
            Reset My Password
          </a>
        </div>
        
        <!-- Copy-Paste Link -->
        <div style="background-color:#161b22; border-left:4px solid #238636; 
                    padding:15px; margin:20px 0; border-radius:4px;">
          <p style="font-size:12px; color:#8b949e; margin:0 0 10px 0;">Or copy this link:</p>
          <p style="word-break:break-all; font-family:monospace; font-size:11px; 
                    color:#58a6ff; margin:0;">
            {reset_url}
          </p>
        </div>
        
        <!-- Expiry Warning -->
        <p style="color:#f85149; font-weight:bold; margin:20px 0;">
          ⏱ This link will expire in 1 hour
        </p>
        
        <p>If you did not request this password reset, please ignore this email and do not share the link.</p>
        
        <p style="color:#8b949e; font-size:12px;">
          🔒 For security, never share your password reset link with anyone.
        </p>
      </div>
      
      <!-- Footer -->
      <div style="text-align:center; padding-top:20px; border-top:1px solid #30363d; 
                  color:#8b949e; font-size:11px;">
        <p style="margin:0;">Cyber Defence — Enterprise Security Analysis Platform</p>
      </div>
      
    </div>
  </body>
</html>"""
        
        # Attach both text and HTML versions to message
        part1 = MIMEText(text_body, "plain")
        part2 = MIMEText(html_body, "html")
        msg.attach(part1)
        msg.attach(part2)
        
        # Send email via Gmail SMTP with STARTTLS encryption
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            # Start TLS encryption on port 587
            server.starttls()
            # Login with Gmail credentials
            server.login(sender_email, sender_password)
            # Send the email
            server.sendmail(sender_email, to_email, msg.as_string())
        
        # Log success to console only (not to any file)
        print(f"✅ Password reset email sent to {to_email}")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        error_msg = f"Gmail authentication failed - check SMTP_EMAIL and SMTP_PASSWORD in .env"
        print(f"❌ {error_msg}")
        raise Exception(error_msg) from e
    except smtplib.SMTPException as e:
        error_msg = f"SMTP error sending reset email: {str(e)}"
        print(f"❌ {error_msg}")
        raise Exception(error_msg) from e
    except Exception as e:
        error_msg = f"Failed to send password reset email to {to_email}: {str(e)}"
        print(f"❌ {error_msg}")
        raise Exception(error_msg) from e

def send_password_reset_email(email: str, reset_token: str) -> bool:
    """
    ⚠️ DEPRECATED - This function is no longer used.
    
    Legacy function kept for backward compatibility only.
    Use send_reset_email() instead.
    """
    raise NotImplementedError("This function is deprecated. Use send_reset_email() instead.")

# ── Database Management ────────────────────────────────────────────
def column_exists(cursor, table_name: str, column_name: str) -> bool:
    """
    Check if a column exists in a table.
    Works with both PostgreSQL and SQLite.
    
    Args:
        cursor: Database cursor
        table_name: Name of the table
        column_name: Name of the column
        
    Returns:
        True if column exists, False otherwise
    """
    try:
        # Try PostgreSQL method first
        cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = %s AND column_name = %s
        """, (table_name, column_name))
        if cursor.fetchone():
            return True
    except Exception:
        # Fall back to SQLite method
        try:
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in cursor.fetchall()]
            return column_name in columns
        except Exception:
            return False

def get_table_columns(cursor, table_name: str) -> list:
    """
    Get all column names from a table.
    Works with both PostgreSQL and SQLite.
    
    Args:
        cursor: Database cursor
        table_name: Name of the table
        
    Returns:
        List of column names
    """
    try:
        # Try PostgreSQL method first
        cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = %s ORDER BY ordinal_position
        """, (table_name,))
        return [row[0] for row in cursor.fetchall()]
    except Exception:
        # Fall back to SQLite method
        try:
            cursor.execute(f"PRAGMA table_info({table_name})")
            return [col[1] for col in cursor.fetchall()]
        except Exception:
            return []

def init_auth_db():
    """Initialize authentication tables and add new columns for password reset."""
    conn = get_db_connection()
    try:
        c = conn.cursor()
        
        # Users table with password reset support
        # Use SERIAL for PostgreSQL, INTEGER PRIMARY KEY AUTOINCREMENT for SQLite
        if USE_POSTGRESQL:
            c.execute("""CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                organization TEXT,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_login TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                reset_token TEXT,
                reset_token_expiry REAL
            )""")
        else:
            c.execute("""CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                organization TEXT,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_login TEXT,
                is_active BOOLEAN DEFAULT 1,
                reset_token TEXT,
                reset_token_expiry REAL
            )""")
        
        # ── Migration: Add reset_token and reset_token_expiry columns if they don't exist ──
        columns = get_table_columns(c, "users")
        
        try:
            if 'reset_token' not in columns:
                c.execute("""ALTER TABLE users ADD COLUMN reset_token TEXT""")
                print("✅ Added 'reset_token' column to users table")
        except Exception:
            pass  # Column already exists
        
        try:
            if 'reset_token_expiry' not in columns:
                c.execute("""ALTER TABLE users ADD COLUMN reset_token_expiry REAL""")
                print("✅ Added 'reset_token_expiry' column to users table")
        except Exception:
            pass  # Column already exists
        
        # Add user_id to scans table if it doesn't exist
        scans_columns = get_table_columns(c, "scans")
        if 'user_id' not in scans_columns:
            c.execute("""ALTER TABLE scans ADD COLUMN user_id INTEGER""")
        
        # Reports table for tracking generated reports
        # Use SERIAL for PostgreSQL, INTEGER PRIMARY KEY AUTOINCREMENT for SQLite
        if USE_POSTGRESQL:
            c.execute("""CREATE TABLE IF NOT EXISTS reports (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                target TEXT,
                org_name TEXT,
                author TEXT,
                pdf_path TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )""")
        else:
            c.execute("""CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                target TEXT,
                org_name TEXT,
                author TEXT,
                pdf_path TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )""")
        
        # ── Migration: Add role column if it doesn't exist ──
        try:
            if 'role' not in columns:
                c.execute("""ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'analyst'""")
                print("✅ Added 'role' column to users table")
        except Exception:
            pass  # Column already exists
        
        # Login attempts table for brute-force protection
        if USE_POSTGRESQL:
            c.execute("""CREATE TABLE IF NOT EXISTS login_attempts (
                id SERIAL PRIMARY KEY,
                email TEXT NOT NULL,
                ip_address TEXT,
                attempted_at TEXT NOT NULL,
                success BOOLEAN DEFAULT FALSE
            )""")
        else:
            c.execute("""CREATE TABLE IF NOT EXISTS login_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                ip_address TEXT,
                attempted_at TEXT NOT NULL,
                success BOOLEAN DEFAULT 0
            )""")
        
        conn.commit()
    finally:
        conn.close()

def migrate_pdf_paths_for_reports():
    """
    Migration: Update existing reports that have NULL pdf_path.
    Links reports with available PDF files using intelligent timestamp matching.
    """
    try:
        # Import cyberdefence_platform_v31 to get DATA_DIR
        import cyberdefence_platform_v31 as core
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # Get all reports where pdf_path is NULL or empty
        execute_query(c, 
            "SELECT id, user_id, target, org_name, author, created_at FROM reports WHERE pdf_path IS NULL OR pdf_path = ''",
            ()
        )
        null_reports = c.fetchall()
        
        if not null_reports:
            conn.close()
            return  # No migration needed
        
        print(f"📋 Found {len(null_reports)} reports without pdf_path")
        
        # Check if data/reports directory exists and has orphaned PDFs
        reports_dir = core.DATA_DIR / "reports"
        if not reports_dir.exists():
            conn.close()
            return
        
        pdf_files = sorted(reports_dir.glob("*.pdf"), reverse=True)
        
        if not pdf_files:
            conn.close()
            return
        
        print(f"   Found {len(pdf_files)} PDF files in reports directory")
        
        # Strategy: Try to match reports with PDFs by timestamp proximity
        # If no close match found, use most recent PDF for that user
        for report_row in null_reports:
            report_id = report_row[0]
            user_id = report_row[1]
            target = report_row[2]
            created_at = report_row[5]  # ISO format timestamp
            
            try:
                # Parse report created_at timestamp
                if "T" in created_at:
                    # ISO format: 2026-05-02T16:45:24
                    report_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                else:
                    # Other format - skip this one
                    continue
                
                # Find closest PDF by modification time (within 120 seconds)
                closest_pdf = None
                closest_diff = float('inf')
                
                for pdf_file in pdf_files:
                    try:
                        pdf_mtime = datetime.fromtimestamp(pdf_file.stat().st_mtime)
                        time_diff = abs((pdf_mtime - report_time).total_seconds())
                        
                        # If PDF was created within 120 seconds of report, it's a potential match
                        if time_diff < 120 and time_diff < closest_diff:
                            closest_pdf = pdf_file
                            closest_diff = time_diff
                    except Exception:
                        continue
                
                # Update report with matched PDF
                if closest_pdf:
                    pdf_path = str(closest_pdf)
                    execute_query(c,
                        "UPDATE reports SET pdf_path = %s WHERE id = %s",
                        (pdf_path, report_id)
                    )
                    print(f"   ✅ Report #{report_id} → {closest_pdf.name} (Δ {closest_diff:.0f}s)")
                else:
                    # No close match - use the most recent PDF as fallback
                    if pdf_files:
                        latest_pdf = pdf_files[0]  # Most recent
                        pdf_path = str(latest_pdf)
                        execute_query(c,
                            "UPDATE reports SET pdf_path = %s WHERE id = %s",
                            (pdf_path, report_id)
                        )
                        print(f"   ⚠️  Report #{report_id} → {latest_pdf.name} (using latest)")
                        
            except Exception as e:
                print(f"   ❌ Error processing Report #{report_id}: {e}")
                continue
        
        conn.commit()
        conn.close()
        print("✅ Migration completed!")
        
    except Exception as e:
        print(f"❌ Migration error: {e}")
        import traceback
        traceback.print_exc()

# Run migration on startup
migrate_pdf_paths_for_reports()

def get_user_by_email(email: str) -> dict | None:
    """Get a user by email."""
    conn = get_db_connection()
    try:
        c = conn.cursor()
        execute_query(c, "SELECT * FROM users WHERE email = %s", (email,))
        row = c.fetchone()
    finally:
        conn.close()
    
    if row:
        return {
            "id": row[0],
            "email": row[1],
            "full_name": row[2],
            "organization": row[3],
            "password_hash": row[4],
            "created_at": row[5],
            "last_login": row[6],
            "is_active": row[7],
            "reset_token": row[8] if len(row) > 8 else None,
            "reset_token_expiry": row[9] if len(row) > 9 else None,
            "role": row[10] if len(row) > 10 else "analyst"
        }
    return None

def get_user_by_id(user_id: int) -> dict | None:
    """Get a user by ID."""
    conn = get_db_connection()
    try:
        c = conn.cursor()
        execute_query(c, "SELECT * FROM users WHERE id = %s", (user_id,))
        row = c.fetchone()
    finally:
        conn.close()
    
    if row:
        return {
            "id": row[0],
            "email": row[1],
            "full_name": row[2],
            "organization": row[3],
            "password_hash": row[4],
            "created_at": row[5],
            "last_login": row[6],
            "is_active": row[7],
            "reset_token": row[8] if len(row) > 8 else None,
            "reset_token_expiry": row[9] if len(row) > 9 else None,
            "role": row[10] if len(row) > 10 else "analyst"
        }
    return None

def record_login_attempt(email: str, ip_address: str = None, success: bool = False):
    """Record a login attempt for brute-force tracking."""
    conn = get_db_connection()
    try:
        c = conn.cursor()
        execute_query(c, "INSERT INTO login_attempts (email, ip_address, attempted_at, success) VALUES (%s, %s, %s, %s)",
                      (email, ip_address, datetime.now().isoformat(), success))
        conn.commit()
    finally:
        conn.close()

def is_account_locked(email: str, max_attempts: int = 5, lockout_minutes: int = 15) -> bool:
    """Check if an account is locked due to too many failed login attempts."""
    conn = get_db_connection()
    try:
        c = conn.cursor()
        cutoff = (datetime.now() - timedelta(minutes=lockout_minutes)).isoformat()
        execute_query(c, "SELECT COUNT(*) FROM login_attempts WHERE email = %s AND attempted_at > %s AND success = %s",
                      (email, cutoff, False if not USE_POSTGRESQL else False))
        count = c.fetchone()[0]
    finally:
        conn.close()
    conn.close()
    return count >= max_attempts

def create_user(email: str, full_name: str, password: str, organization: str = "") -> dict | None:
    """Create a new user."""
    # Check if user exists
    if get_user_by_email(email):
        return None
    
    password_hash = hash_password(password)
    now = datetime.now(timezone.utc).isoformat()
    
    conn = get_db_connection()
    c = conn.cursor()
    try:
        execute_query(c,
            "INSERT INTO users (email, full_name, organization, password_hash, created_at) VALUES (%s, %s, %s, %s, %s)",
            (email, full_name, organization, password_hash, now)
        )
        conn.commit()
        user_id = c.lastrowid
        conn.close()
        
        return {
            "id": user_id,
            "email": email,
            "full_name": full_name,
            "organization": organization,
            "created_at": now
        }
    except Exception:
        conn.close()
        return None

def update_last_login(user_id: int):
    """Update user's last login timestamp."""
    conn = get_db_connection()
    try:
        c = conn.cursor()
        execute_query(c, "UPDATE users SET last_login = %s WHERE id = %s", 
                  (datetime.now(timezone.utc).isoformat(), user_id))
        conn.commit()
    finally:
        conn.close()

def update_password(user_id: int, new_password: str) -> bool:
    """Update user's password."""
    password_hash = hash_password(new_password)
    conn = get_db_connection()
    try:
        c = conn.cursor()
        execute_query(c, "UPDATE users SET password_hash = %s WHERE id = %s", 
                  (password_hash, user_id))
        conn.commit()
    finally:
        conn.close()
    return True

# ── Password Reset Token Management (SHA-256 Based) ────────────────
def generate_reset_token() -> str:
    """
    Generate a cryptographically secure password reset token.
    Uses secrets.token_urlsafe(32) for maximum security.
    
    Returns:
        Raw token (NOT hashed) - will be sent to user via email
    """
    return secrets.token_urlsafe(32)

def hash_reset_token(token: str) -> str:
    """
    Hash a reset token using SHA-256 for database storage.
    NEVER store raw tokens in the database.
    
    Args:
        token: Raw reset token
        
    Returns:
        SHA-256 hashed token (hexdigest)
    """
    return hashlib.sha256(token.encode()).hexdigest()

def create_reset_token_for_user(user_id: int) -> str | None:
    """
    Create and store a password reset token for a user.
    Token expires in 1 hour.
    
    Args:
        user_id: User's ID
        
    Returns:
        Raw token to send to user, or None if failed
    """
    try:
        # Generate raw token
        raw_token = generate_reset_token()
        
        # Hash it for storage
        hashed_token = hash_reset_token(raw_token)
        
        # Set expiry to 1 hour from now (Unix timestamp)
        expiry_time = time.time() + 3600  # 3600 seconds = 1 hour
        
        # Store in database
        conn = get_db_connection()
        c = conn.cursor()
        execute_query(c,
            "UPDATE users SET reset_token = %s, reset_token_expiry = %s WHERE id = %s",
            (hashed_token, expiry_time, user_id)
        )
        conn.commit()
        conn.close()
        
        return raw_token  # Return raw token to send via email
        
    except Exception as e:
        print(f"❌ Error creating reset token: {e}")
        return None

def verify_reset_token(token: str) -> dict | None:
    """
    Verify a reset token and return the user if valid.
    Checks both the token hash and expiry time.
    
    Args:
        token: Raw reset token from user
        
    Returns:
        User dict if token is valid, None otherwise
    """
    try:
        # Hash the incoming token to match DB
        hashed_token = hash_reset_token(token)
        
        # Query database
        conn = get_db_connection()
        c = conn.cursor()
        execute_query(c,
            "SELECT id, email, full_name, reset_token_expiry FROM users WHERE reset_token = %s",
            (hashed_token,)
        )
        row = c.fetchone()
        conn.close()
        
        if not row:
            return None  # Token not found
        
        user_id, email, full_name, expiry_time = row
        
        # Check if token has expired
        current_time = time.time()
        if expiry_time is None or current_time > expiry_time:
            return None  # Token expired
        
        return {
            "id": user_id,
            "email": email,
            "full_name": full_name,
            "expiry_time": expiry_time
        }
        
    except Exception as e:
        print(f"❌ Error verifying reset token: {e}")
        return None

def invalidate_reset_token(user_id: int) -> bool:
    """
    Invalidate (clear) a reset token after successful password reset.
    This prevents token reuse.
    
    Args:
        user_id: User's ID
        
    Returns:
        True if successful
    """
    try:
        conn = get_db_connection()
        c = conn.cursor()
        execute_query(c,
            "UPDATE users SET reset_token = NULL, reset_token_expiry = NULL WHERE id = %s",
            (user_id,)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Error invalidating reset token: {e}")
        return False

# ── Report Management ──────────────────────────────────────────────
def save_report(user_id: int, target: str, org_name: str, author: str, pdf_path: str = None) -> dict | None:
    """
    Save a generated security report to the database.
    
    Args:
        user_id: User's ID
        target: Target URL/domain
        org_name: Organization name
        author: Report author name
        pdf_path: Path to generated PDF file (optional)
        
    Returns:
        Report dict with id and metadata, or None if failed
    """
    try:
        now = datetime.now(timezone.utc).isoformat()
        conn = get_db_connection()
        c = conn.cursor()
        execute_query(c,
            "INSERT INTO reports (user_id, target, org_name, author, pdf_path, created_at) VALUES (%s, %s, %s, %s, %s, %s)",
            (user_id, target, org_name, author, pdf_path, now)
        )
        conn.commit()
        report_id = c.lastrowid
        conn.close()
        
        return {
            "id": report_id,
            "user_id": user_id,
            "target": target,
            "org_name": org_name,
            "author": author,
            "pdf_path": pdf_path,
            "created_at": now
        }
    except Exception as e:
        print(f"❌ Error saving report: {e}")
        return None

def get_user_reports(user_id: int, limit: int = 50) -> list:
    """
    Get all reports generated by a user.
    
    Args:
        user_id: User's ID
        limit: Maximum number of reports to fetch
        
    Returns:
        List of report dicts
    """
    try:
        conn = get_db_connection()
        c = conn.cursor()
        execute_query(c,
            "SELECT id, user_id, target, org_name, author, pdf_path, created_at FROM reports WHERE user_id = %s ORDER BY created_at DESC LIMIT %s",
            (user_id, limit)
        )
        rows = c.fetchall()
        conn.close()
        
        reports = []
        for row in rows:
            reports.append({
                "id": row[0],
                "user_id": row[1],
                "target": row[2],
                "org_name": row[3],
                "author": row[4],
                "pdf_path": row[5],
                "created_at": row[6]
            })
        return reports
    except Exception as e:
        print(f"❌ Error fetching user reports: {e}")
        return []

def get_report_by_id(report_id: int, user_id: int = None) -> dict | None:
    """
    Get a specific report by ID. Optionally verify it belongs to a specific user.
    
    Args:
        report_id: Report's ID
        user_id: User's ID (for permission check), optional
        
    Returns:
        Report dict or None if not found
    """
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        if user_id:
            execute_query(c,
                "SELECT id, user_id, target, org_name, author, pdf_path, created_at FROM reports WHERE id = %s AND user_id = %s",
                (report_id, user_id)
            )
        else:
            execute_query(c,
                "SELECT id, user_id, target, org_name, author, pdf_path, created_at FROM reports WHERE id = %s",
                (report_id,)
            )
        
        row = c.fetchone()
        conn.close()
        
        if row:
            return {
                "id": row[0],
                "user_id": row[1],
                "target": row[2],
                "org_name": row[3],
                "author": row[4],
                "pdf_path": row[5],
                "created_at": row[6]
            }
        return None
    except Exception as e:
        print(f"❌ Error fetching report: {e}")
        return None

# ── Pydantic Models ────────────────────────────────────────────────
class SignupRequest(BaseModel):
    email: str
    full_name: str
    password: str
    organization: str = ""
    
    @validator('email')
    def email_valid(cls, v):
        if '@' not in v:
            raise ValueError('Invalid email address')
        return v
    
    @validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if len(v.encode('utf-8')) > 72:
            raise ValueError('Password must be no more than 72 bytes (usually ~70 characters)')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in v):
            raise ValueError('Password must contain at least one special character (!@#$%^&*...)')
        return v

class LoginRequest(BaseModel):
    email: str
    password: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    organization: str
    created_at: str

class PasswordResetRequest(BaseModel):
    email: str

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str
    
    @validator('new_password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if len(v.encode('utf-8')) > 72:
            raise ValueError('Password must be no more than 72 bytes (usually ~70 characters)')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in v):
            raise ValueError('Password must contain at least one special character (!@#$%^&*...)')
        return v
