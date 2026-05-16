"""
CyberDefence Platform v3.1 - Main API Server

FastAPI application orchestrating security scans, authentication, reporting, and administration.
Routes are modularized in the routers package:
- routers.auth_routes: Authentication endpoints
- routers.scan: Security scan operations  
- routers.report: Report and policy generation
- routers.admin: Administrative functions
"""

from __future__ import annotations

import datetime as dt
import json
import os
import sys
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv(ROOT_DIR / ".env")

import cyberdefence_platform_v31 as core
from frontend.backend import auth
from frontend.backend.routers import auth_routes, scan, report, admin, schedule, scores, teams

core.init_db()
auth.init_auth_db()

# ──────────────────────────────────────────────────────────────────
# FastAPI App Setup
# ──────────────────────────────────────────────────────────────────

app = FastAPI(title="CyberDefence API", version="3.1.0")

# Configure rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS with restricted origins
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
ALLOWED_ORIGINS = [
    FRONTEND_URL,
    "https://cyber-defence.live",
    "https://www.cyber-defence.live",
    "https://cyber-defenece.vercel.app",
    "https://cyberdefence-app-ebf9df3d3adb.herokuapp.com",
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──────────────────────────────────────────────────────────────────
# Include Routers
# ──────────────────────────────────────────────────────────────────

app.include_router(auth_routes.router)
app.include_router(scan.router)
app.include_router(report.router)
app.include_router(admin.router)
app.include_router(schedule.router)
app.include_router(scores.router)
app.include_router(teams.router)

# ──────────────────────────────────────────────────────────────────
# Helper Functions
# ──────────────────────────────────────────────────────────────────


def _history_rows(limit: int, user_id: str = None) -> list[dict[str, Any]]:
    """Get formatted history rows from database."""
    rows = core.get_history(limit, user_id=user_id)
    return [
        {
            "id": row[0],
            "target": row[1],
            "module": row[2],
            "timestamp": row[3],
            "results": json.loads(row[4]) if row[4] else {},
        }
        for row in rows
    ]


# ──────────────────────────────────────────────────────────────────
# Core Endpoints
# ──────────────────────────────────────────────────────────────────


@app.api_route("/api/health", methods=["GET", "HEAD"])
def health() -> dict[str, Any]:
    """Health check endpoint."""
    db_url = os.environ.get("DATABASE_URL", str(core.DB_FILE))
    if "@" in db_url:
        db_url = "postgresql://***@" + db_url.split("@")[1]
    return {
        "status": "ok",
        "version": "3.1.0",
        "database": db_url,
        "nuclei_available": core.NUCLEI_AVAILABLE,
        "nmap_available": core.NMAP_AVAILABLE,
        "timestamp": dt.datetime.now().isoformat(),
    }


@app.get("/api/history")
def history(limit: int = 20) -> dict[str, Any]:
    """Get scan history."""
    limit = max(1, min(limit, 200))
    return {"items": _history_rows(limit), "count": limit}


@app.get("/api/dashboard")
def dashboard(authorization: str = Header(None)) -> dict[str, Any]:
    """Get personalized dashboard for authenticated user."""
    # Get current user for personalized dashboard
    user = auth_routes.get_current_user(authorization)
    user_id = user["id"]
    
    # Get user-specific latest scan results for each module
    vuln = core.get_latest("vuln", user_id=user_id)
    defence = core.get_latest("defence", user_id=user_id)
    siem = core.get_latest("siem", user_id=user_id)
    vt = core.get_latest("virustotal", user_id=user_id)
    recon = core.get_latest("recon", user_id=user_id)

    # Get user's recent scan history (filtered by user_id)
    recent_rows = _history_rows(10, user_id=user_id)
    recent_scan_history = []
    for row in recent_rows:
        blob = row.get("results", {}) if isinstance(row.get("results", {}), dict) else {}
        recent_scan_history.append(
            {
                "id": row["id"],
                "target_asset": row["target"],
                "timestamp": row["timestamp"],
                "score": report._derive_score(row["module"], blob),
                "vulns": report._derive_vuln_badge(blob),
                "status": "COMPLETED",
                "actions": "open_in_new",
                "module": row["module"],
            }
        )

    return {
        "user": {
            "id": user_id,
            "full_name": user.get("full_name", "Analyst"),
            "email": user.get("email", ""),
            "role": user.get("role", "analyst"),
        },
        "vulnerability_summary": vuln.get("summary", {}),
        "security_score": defence.get("score", 0),
        "defence": {
            "pass": defence.get("pass", 0),
            "fail": defence.get("fail", 0),
            "warn": defence.get("warn", 0),
        },
        "siem": {
            "events": siem.get("events", 0),
            "critical": siem.get("critical", 0),
            "high": siem.get("high", 0),
            "medium": siem.get("medium", 0),
        },
        "virustotal": {
            "malicious": vt.get("malicious", 0),
            "suspicious": vt.get("suspicious", 0),
            "total_engines": vt.get("total_engines", 0),
        },
        "recon": {
            "cloudflare": recon.get("cloudflare", False),
            "domain": recon.get("domain", ""),
        },
        "data_sources": {
            "nuclei": core.refresh_nuclei_status(),
            "wpscan": bool(core.CONFIG.get("wpscan_api_key")),
            "virustotal": bool(core.CONFIG.get("virustotal_api_key")),
            "sucuri": True,
            "securityheaders": True,
            "cloudflare": True,
        },
        "recent_scan_history": recent_scan_history,
        "total_scans": len(recent_rows),
    }


# ── Admin Router (see routers/admin.py) ────────────────────────────
