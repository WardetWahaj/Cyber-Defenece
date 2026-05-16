"""
Report and policy generation endpoints for the CyberDefence API.

Provides PDF report generation, policy document creation, and report retrieval.
"""

import datetime as dt
import json
from typing import Any

from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

import cyberdefence_platform_v31 as core
from frontend.backend import auth
from frontend.backend.routers.auth_routes import get_current_user
from frontend.backend.services.pdf_generator import _create_pdf_report

router = APIRouter(tags=["reports"])


class PolicyRequest(BaseModel):
    policy_id: str = Field(default="1")
    org_name: str = Field(default="Organisation")


class ReportRequest(BaseModel):
    org_name: str = Field(default="Organisation")
    target: str = Field(default="N/A")
    author: str = Field(default="Security Analyst")
    include_pdf: bool = Field(default=True)


def _derive_vuln_badge(result_blob: dict[str, Any]) -> str:
    """Derive vulnerability severity badge from result data."""
    summary = result_blob.get("summary", {}) if isinstance(result_blob, dict) else {}
    critical = int(summary.get("critical", 0))
    high = int(summary.get("high", 0))
    medium = int(summary.get("medium", 0))
    return f"{critical}C/{high}H/{medium}M"


def _derive_score(module: str, result_blob: dict[str, Any]) -> str:
    """Derive security score from module results."""
    if module == "defence":
        return str(result_blob.get("score", "--"))
    if module == "vuln":
        summary = result_blob.get("summary", {}) if isinstance(result_blob, dict) else {}
        critical = int(summary.get("critical", 0))
        high = int(summary.get("high", 0))
        medium = int(summary.get("medium", 0))
        low = int(summary.get("low", 0))
        weighted = max(0, 100 - (critical * 15 + high * 6 + medium * 2 + low))
        return str(weighted)
    return "--"


@router.post("/api/policy/generate")
def generate_policy(payload: PolicyRequest) -> dict[str, Any]:
    """Generate a security policy document."""
    policy = core.POLICIES.get(payload.policy_id, core.POLICIES["1"])
    out_dir = core.DATA_DIR / "policies"
    out_dir.mkdir(parents=True, exist_ok=True)

    filename = out_dir / f"policy_{policy['name'].replace(' ', '_')}_{core.ts()}.txt"
    with open(filename, "w", encoding="utf-8") as handle:
        handle.write(f"{policy['name'].upper()}\n")
        handle.write(f"Organisation: {payload.org_name}\n")
        handle.write(f"Generated: {dt.date.today()}\n\n")
        for title, content in policy["sections"]:
            handle.write(f"{title}\n{content}\n\n")

    return {
        "policy": policy["name"],
        "organisation": payload.org_name,
        "path": str(filename),
        "sections": [{"title": title, "content": content} for title, content in policy["sections"]],
    }


@router.post("/api/report/generate")
def generate_report(payload: ReportRequest, authorization: str = Header(None)) -> dict[str, Any]:
    """Generate a comprehensive security assessment report."""
    user = get_current_user(authorization)
    
    vuln = core.get_latest("vuln")
    defence = core.get_latest("defence")
    siem = core.get_latest("siem")
    vt = core.get_latest("virustotal")
    shodan_data = core.get_latest("shodan", user_id=user["id"])
    abuseipdb_data = core.get_latest("abuseipdb", user_id=user["id"])
    
    summary = {
        "security_score": defence.get("score", 0),
        "vulnerability_summary": vuln.get("summary", {}),
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
        "shodan": {
            "ports": len(shodan_data.get("ports", [])) if shodan_data and not shodan_data.get("error") else 0,
            "vulns": len(shodan_data.get("vulns", [])) if shodan_data and not shodan_data.get("error") else 0,
            "organization": shodan_data.get("organization", "N/A") if shodan_data and not shodan_data.get("error") else "N/A",
        },
        "abuseipdb": {
            "abuse_score": abuseipdb_data.get("abuse_confidence_score", 0) if abuseipdb_data and not abuseipdb_data.get("error") else 0,
            "total_reports": abuseipdb_data.get("total_reports", 0) if abuseipdb_data and not abuseipdb_data.get("error") else 0,
        },
    }
    
    details = None
    pdf_path = None
    
    if payload.include_pdf:
        pdf_path = _create_pdf_report(payload.org_name, payload.target, payload.author, summary, details)
        report_filename = pdf_path.split("/")[-1] if pdf_path else None
    else:
        report_filename = None
    
    report = auth.save_report(
        user_id=user["id"],
        target=payload.target,
        org_name=payload.org_name,
        author=payload.author,
        pdf_path=report_filename
    )
    
    return {
        "report_id": report["id"] if report else None,
        "generated_at": dt.datetime.now().isoformat(),
        "org_name": payload.org_name,
        "target": payload.target,
        "author": payload.author,
        "summary": summary,
        "details": details,
        "pdf_path": pdf_path,
    }


@router.get("/api/report/download")
def download_pdf(filename: str = None):
    """Download a generated PDF report file."""
    if not filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    # Sanitize filename to prevent directory traversal
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    pdf_path = core.DATA_DIR / "reports" / filename
    
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF file not found")

    # Mobile-friendly headers for better download support
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Content-Type": "application/pdf",
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0",
    }
    
    return FileResponse(
        path=pdf_path,
        filename=filename,
        media_type="application/pdf",
        headers=headers
    )


@router.get("/api/reports/list")
def list_user_reports(authorization: str = Header(None), limit: int = 100) -> dict:
    """Get user's generated reports."""
    user = get_current_user(authorization)
    
    # Get user's actual reports from reports table (not scan history)
    reports = auth.get_user_reports(user["id"], limit=limit)
    
    if not reports:
        return {"reports": [], "total": 0}
    
    # auth.get_user_reports() already returns list of dicts, no transformation needed
    return {"reports": reports, "total": len(reports)}


@router.get("/api/reports/{report_id}")
def get_user_report(report_id: int, authorization: str = Header(None)) -> dict:
    """Get a specific report by ID (user must own the report)."""
    user = get_current_user(authorization)
    report = auth.get_report_by_id(report_id, user_id=user["id"])
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found or access denied")
    
    return report
