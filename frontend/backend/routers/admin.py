"""
Admin endpoints for the CyberDefence API.

Provides administrative functions for user and scan management.
Requires admin role for all endpoints.
"""

from typing import Any

from fastapi import APIRouter, HTTPException, Depends, Header

import cyberdefence_platform_v31 as core
from frontend.backend import auth
from frontend.backend.routers.auth_routes import get_current_user

router = APIRouter(prefix="/api/admin", tags=["admin"])


def require_admin(authorization: str = Header(None)) -> dict:
    """Extract and verify user, ensuring they have admin role."""
    user = get_current_user(authorization)
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


@router.get("/users")
def admin_get_users(admin: dict = Depends(require_admin)) -> dict:
    """Get all registered users."""
    conn = auth.get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, email, full_name, organization, role, created_at, last_login FROM users ORDER BY created_at DESC")
    rows = c.fetchall()
    conn.close()
    users = [{"id": r[0], "email": r[1], "full_name": r[2], "organization": r[3], "role": r[4], "created_at": r[5], "last_login": r[6]} for r in rows]
    return {"users": users, "total": len(users)}


@router.get("/scans")
def admin_get_scans(admin: dict = Depends(require_admin), limit: int = 100) -> dict:
    """Get recent scans across all users."""
    rows = core.get_history(limit=limit)
    scans = [{"id": r[0], "target": r[1], "module": r[2], "timestamp": r[3], "user_id": r[5] if len(r) > 5 else None} for r in rows]
    return {"scans": scans, "total": len(scans)}
