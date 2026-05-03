"""
Authentication module for CyberDefence Platform v3.1
Handles user management, JWT tokens, and password security.
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
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

# ── Database abstraction layer (supports PostgreSQL and SQLite) ────
import sqlite3

DATABASE_URL = os.getenv("DATABASE_URL", "")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

USE_POSTGRES = bool(DATABASE_URL)

if USE_POSTGRES:
    try:
        import psycopg2
        def get_db_connection():
            return psycopg2.connect(DATABASE_URL)
    except ImportError:
        print("[!] psycopg2 not available. Install with: pip install psycopg2-binary")
        USE_POSTGRES = False
        DB_FILE = ROOT_DIR / "data" / "cyberdefence.db"
        def get_db_connection():
            return sqlite3.connect(DB_FILE)
else:
    DB_FILE = ROOT_DIR / "data" / "cyberdefence.db"
    def get_db_connection():
        return sqlite3.connect(DB_FILE)

from pydantic import BaseModel, EmailStr, validator
import jwt

# ── Configuration ──────────────────────────────────────────────────
DB_FILE = ROOT_DIR / "data" / "cyberdefence.db"
SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-change-in-production")
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24
PASSWORD_RESET_TOKEN_EXPIRE_HOURS = 1
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")  # development or production

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
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)
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
        msg["Subject"] = "🔐 Password Reset — CyberDefence v3.1"
        msg["From"] = f"CyberDefence Security <{sender_email}>"
        msg["To"] = to_email
        
        # Plain text version (fallback for email clients without HTML support)
        text_body = f"""Hi {user_name},

You requested a password reset for your CyberDefence account.

Reset link: {reset_url}

This link expires in 1 hour.
If you did not request this, ignore this email.

— CyberDefence v3.1 Security Platform"""
        
        # HTML version with dark cybersecurity theme
        html_body = f"""<html>
  <body style="background-color:#0d1117; font-family:Arial,sans-serif; color:#c9d1d9;">
    <div style="max-width:600px; margin:0 auto; padding:40px 20px;">
      
      <!-- Header -->
      <div style="text-align:center; padding-bottom:20px; border-bottom:2px solid #238636;">
        <h2 style="color:#58a6ff; margin:0;">🔐 CyberDefence v3.1</h2>
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
        <p style="margin:0;">CyberDefence v3.1 — Enterprise Security Analysis Platform</p>
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
    c = conn.cursor()
    
    # Users table with password reset support
    # Use SERIAL for PostgreSQL, INTEGER PRIMARY KEY AUTOINCREMENT for SQLite
    if USE_POSTGRES:
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
    if USE_POSTGRES:
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
    
    conn.commit()
    conn.close()

def get_user_by_email(email: str) -> dict | None:
    """Get a user by email."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = c.fetchone()
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
            "is_active": row[7]
        }
    return None

def get_user_by_id(user_id: int) -> dict | None:
    """Get a user by ID."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = c.fetchone()
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
            "is_active": row[7]
        }
    return None

def create_user(email: str, full_name: str, password: str, organization: str = "") -> dict | None:
    """Create a new user."""
    # Check if user exists
    if get_user_by_email(email):
        return None
    
    password_hash = hash_password(password)
    now = datetime.utcnow().isoformat()
    
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO users (email, full_name, organization, password_hash, created_at) VALUES (?, ?, ?, ?, ?)",
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
    c = conn.cursor()
    c.execute("UPDATE users SET last_login = ? WHERE id = ?", 
              (datetime.utcnow().isoformat(), user_id))
    conn.commit()
    conn.close()

def update_password(user_id: int, new_password: str) -> bool:
    """Update user's password."""
    password_hash = hash_password(new_password)
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET password_hash = ? WHERE id = ?", 
              (password_hash, user_id))
    conn.commit()
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
        c.execute(
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
        c.execute(
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
        c.execute(
            "UPDATE users SET reset_token = NULL, reset_token_expiry = NULL WHERE id = %s",
            (user_id,)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Error invalidating reset token: {e}")
        return False

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
    def password_length(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        # bcrypt has a maximum of 72 bytes
        if len(v.encode('utf-8')) > 72:
            raise ValueError('Password must be no more than 72 bytes (usually ~70 characters)')
        return v

class LoginRequest(BaseModel):
    email: str
    password: str

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
    def password_length(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if len(v.encode('utf-8')) > 72:
            raise ValueError('Password must be no more than 72 bytes (usually ~70 characters)')
        return v
