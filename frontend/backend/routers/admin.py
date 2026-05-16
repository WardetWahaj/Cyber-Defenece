"""
Admin endpoints for the CyberDefence API.

Provides administrative functions for user and scan management.
Requires admin role for all endpoints.
"""

import os
from typing import Any

import requests as http_requests
from fastapi import APIRouter, HTTPException, Depends, Header, Request
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address

import cyberdefence_platform_v31 as core
from frontend.backend import auth
from frontend.backend.routers.auth_routes import get_current_user

router = APIRouter(prefix="/api/admin", tags=["admin"])
limiter = Limiter(key_func=get_remote_address)


class UpdateApiKeyRequest(BaseModel):
    key_name: str = Field(...)
    key_value: str = Field(..., min_length=1)


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
    try:
        c = conn.cursor()
        c.execute("SELECT id, email, full_name, organization, role, created_at, last_login FROM users ORDER BY created_at DESC")
        rows = c.fetchall()
        users = [{"id": r[0], "email": r[1], "full_name": r[2], "organization": r[3], "role": r[4], "created_at": r[5], "last_login": r[6]} for r in rows]
        return {"users": users, "total": len(users)}
    finally:
        conn.close()


@router.get("/scans")
def admin_get_scans(admin: dict = Depends(require_admin), limit: int = 100) -> dict:
    """Get recent scans across all users."""
    rows = core.get_history(limit=limit)
    scans = [{"id": r[0], "target": r[1], "module": r[2], "timestamp": r[3], "user_id": r[5] if len(r) > 5 else None} for r in rows]
    return {"scans": scans, "total": len(scans)}


@router.get("/api-keys")
@limiter.limit("10/minute")
def get_api_keys_status(request: Request, admin: dict = Depends(require_admin)) -> dict:
    """Return which API keys are configured (not the actual values)."""
    keys_status = {
        "SHODAN_API_KEY": bool(os.environ.get("SHODAN_API_KEY")),
        "ABUSEIPDB_API_KEY": bool(os.environ.get("ABUSEIPDB_API_KEY")),
        "VIRUSTOTAL_API_KEY": bool(os.environ.get("VIRUSTOTAL_API_KEY")),
        "WPSCAN_API_KEY": bool(os.environ.get("WPSCAN_API_KEY")),
        "NVD_API_KEY": bool(os.environ.get("NVD_API_KEY")),
    }
    return {"keys": keys_status}


@router.put("/api-keys")
@limiter.limit("5/minute")
def update_api_key(payload: UpdateApiKeyRequest, request: Request, admin: dict = Depends(require_admin)) -> dict:
    """Update an API key in Heroku Config Vars."""
    allowed_keys = ["SHODAN_API_KEY", "ABUSEIPDB_API_KEY", "VIRUSTOTAL_API_KEY", "WPSCAN_API_KEY", "NVD_API_KEY"]
    if payload.key_name not in allowed_keys:
        raise HTTPException(status_code=400, detail=f"Invalid key name. Allowed: {', '.join(allowed_keys)}")
    
    heroku_api_key = os.environ.get("HEROKU_API_KEY")
    heroku_app_name = os.environ.get("HEROKU_APP_NAME")
    
    if not heroku_api_key or not heroku_app_name:
        raise HTTPException(status_code=500, detail="Heroku API key or app name not configured on server")
    
    try:
        resp = http_requests.patch(
            f"https://api.heroku.com/apps/{heroku_app_name}/config-vars",
            headers={
                "Authorization": f"Bearer {heroku_api_key}",
                "Content-Type": "application/json",
                "Accept": "application/vnd.heroku+json; version=3",
            },
            json={payload.key_name: payload.key_value.strip()},
            timeout=10,
        )
        if resp.status_code == 200:
            os.environ[payload.key_name] = payload.key_value.strip()
            return {"success": True, "message": f"{payload.key_name} updated successfully"}
        else:
            raise HTTPException(status_code=500, detail=f"Heroku API error: {resp.status_code}")
    except http_requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to update Heroku: {str(e)}")
