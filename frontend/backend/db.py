"""
Database abstraction layer for CyberDefence Platform v3.1
Supports both SQLite (default) and PostgreSQL (when DATABASE_URL is set)
"""

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Optional

# Try to import psycopg2 for PostgreSQL support
try:
    import psycopg2
    import psycopg2.extras
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    psycopg2 = None

# ── Database Configuration ─────────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parents[2]
DATABASE_URL = os.getenv("DATABASE_URL", None)
DB_FILE = ROOT_DIR / "data" / "cyberdefence.db"

# Convert postgres:// to postgresql:// for psycopg2 compatibility
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Determine if using PostgreSQL or SQLite
USE_POSTGRESQL = DATABASE_URL is not None and PSYCOPG2_AVAILABLE

if DATABASE_URL and not PSYCOPG2_AVAILABLE:
    print("[!] Warning: DATABASE_URL is set but psycopg2 is not installed.")
    print("[!] Install with: pip install psycopg2-binary")
    print("[!] Falling back to SQLite...")
    USE_POSTGRESQL = False


class DatabaseConnection:
    """Abstract database connection handler for both SQLite and PostgreSQL"""
    
    def __init__(self):
        self.use_postgresql = USE_POSTGRESQL
        self.db_url = DATABASE_URL
    
    def connect(self):
        """Create a new database connection"""
        if self.use_postgresql:
            return self._connect_postgres()
        else:
            return self._connect_sqlite()
    
    def _connect_sqlite(self):
        """Create SQLite connection"""
        return sqlite3.connect(str(DB_FILE))
    
    def _connect_postgres(self):
        """Create PostgreSQL connection"""
        try:
            conn = psycopg2.connect(self.db_url)
            return conn
        except Exception as e:
            print(f"[!] PostgreSQL connection failed: {e}")
            print("[!] Falling back to SQLite...")
            self.use_postgresql = False
            return self._connect_sqlite()
    
    def execute(self, query: str, params: tuple = None, fetch: str = None) -> Any:
        """
        Execute a query and return results.
        
        Args:
            query: SQL query (use ? for SQLite, %s for PostgreSQL)
            params: Query parameters
            fetch: 'one', 'all', or None (for INSERT/UPDATE/DELETE)
        
        Returns:
            Single row (fetch='one'), list of rows (fetch='all'), or None
        """
        conn = self.connect()
        try:
            cursor = conn.cursor()
            
            # Convert SQLite placeholders to PostgreSQL if needed
            if self.use_postgresql:
                query = self._convert_placeholders(query)
            
            # Execute query
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # Fetch results if requested
            if fetch == 'one':
                result = cursor.fetchone()
            elif fetch == 'all':
                result = cursor.fetchall()
            else:
                result = None
                conn.commit()
            
            conn.close()
            return result
        
        except Exception as e:
            conn.close()
            raise e
    
    @staticmethod
    def _convert_placeholders(query: str) -> str:
        """Convert SQLite ? placeholders to PostgreSQL %s"""
        # Simple conversion - replace ? with %s
        # Note: This works for simple queries; complex ones may need manual conversion
        query_list = query.split("'")
        for i in range(0, len(query_list), 2):
            query_list[i] = query_list[i].replace("?", "%s")
        return "'".join(query_list)


# Global database connection instance
db = DatabaseConnection()


# ── Helper functions for common operations ─────────────────────────

def get_connection():
    """Get a new database connection"""
    return db.connect()


@contextmanager
def get_db():
    """Context manager for database connections. Ensures connections are always closed.
    
    Important for Heroku Postgres which has limited connection slots (~20).
    Prevents connection leaks that can crash the app.
    
    Usage:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users")
            rows = cursor.fetchall()
    """
    conn = db.connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def execute_query(query: str, params: tuple = None, fetch: str = None) -> Any:
    """Execute a query directly"""
    return db.execute(query, params, fetch)


# ── Database info ──────────────────────────────────────────────────

def get_database_info() -> dict:
    """Get information about the current database"""
    return {
        "type": "PostgreSQL" if db.use_postgresql else "SQLite",
        "location": DATABASE_URL if db.use_postgresql else str(DB_FILE),
        "connected": True
    }


def log_database_info():
    """Log database connection info"""
    info = get_database_info()
    print(f"[✓] Database: {info['type']}")
    if db.use_postgresql:
        print(f"[✓] URL: {DATABASE_URL}")
    else:
        print(f"[✓] Path: {info['location']}")
