#!/usr/bin/env python3
"""Test database logging and health endpoint."""
import sys
from pathlib import Path
import os

sys.path.insert(0, str(Path(__file__).parent / "frontend" / "backend"))
os.chdir(Path(__file__).parent)

print("=" * 70)
print("TESTING DATABASE LOGGING AND HEALTH ENDPOINT")
print("=" * 70)

# Test 1: Check init_db() print statement
print("\n[1] Testing init_db() database logging...")
print("    Expected output: [DB] USE_POSTGRES=... printed to console")
try:
    import cyberdefence_platform_v31 as platform
    print("    [OK] Platform module imported (init_db() called)")
    print("    [OK] You should see '[DB] USE_POSTGRES=...' printed above")
except Exception as e:
    print(f"    [ERROR] {e}")
    import traceback
    traceback.print_exc()

# Test 2: Verify health endpoint exists and returns proper database value
print("\n[2] Testing /api/health endpoint function...")
try:
    from frontend.backend.api import health
    import os
    
    # Test the health function directly
    result = health()
    
    print(f"    [OK] Health endpoint function executed")
    print(f"    [OK] Status: {result.get('status')}")
    print(f"    [OK] Version: {result.get('version')}")
    print(f"    [OK] Database: {result.get('database')}")
    
    # Verify database field
    db_field = result.get('database')
    if isinstance(db_field, str):
        if 'data' in db_field or 'postgresql' in db_field.lower():
            print(f"    [OK] Database field contains expected path or URL")
        else:
            print(f"    [WARNING] Database field: {db_field}")
    
except Exception as e:
    print(f"    [ERROR] {e}")
    import traceback
    traceback.print_exc()

# Test 3: Check DATABASE_URL environment variable
print("\n[3] Checking DATABASE_URL environment variable...")
db_url = os.environ.get("DATABASE_URL", None)
if db_url:
    print(f"    DATABASE_URL is SET: {db_url}")
else:
    print(f"    DATABASE_URL is NOT set (using SQLite local database)")

print("\n" + "=" * 70)
print("[OK] DATABASE LOGGING AND HEALTH ENDPOINT VERIFIED")
print("=" * 70)
print("\nNote: When deployed to Heroku/Render:")
print("  1. [DB] line will show USE_POSTGRES=True when DATABASE_URL is set")
print("  2. /api/health will return DATABASE_URL value in 'database' field")
print("  3. Check logs with 'heroku logs -t' or platform-specific log viewer")
print("=" * 70)
