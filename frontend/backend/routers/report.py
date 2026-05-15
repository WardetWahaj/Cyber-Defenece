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
from fpdf import FPDF

import cyberdefence_platform_v31 as core
from frontend.backend import auth
from frontend.backend.routers.auth_routes import get_current_user

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


def _sanitize_for_pdf(text: str) -> str:
    """Sanitize text to be compatible with Helvetica font in PDF."""
    if not isinstance(text, str):
        text = str(text)
    # Replace common Unicode characters with ASCII equivalents
    replacements = {
        "→": "->",
        "←": "<-",
        "↓": "v",
        "↑": "^",
        "✓": "✓",
        "✗": "X",
        "•": "-",
        """: '"',
        """: '"',
        "'": "'",
        "'": "'",
        "–": "-",
        "—": "-",
        "…": "...",
        "™": "(TM)",
        "©": "(C)",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    # Remove any remaining non-latin-1 characters
    text = text.encode('latin-1', errors='replace').decode('latin-1')
    return text.strip()


def _create_pdf_report(org_name: str, target: str, author: str, summary: dict[str, Any], details: dict[str, Any] = None) -> str:
    """Generate a professional security assessment PDF report."""
    reports_dir = core.DATA_DIR / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    path = reports_dir / f"security_report_api_{core.ts()}.pdf"

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=12)
    
    # ===== PAGE 1: COVER PAGE =====
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 32)
    pdf.ln(50)
    pdf.cell(0, 20, "CYBER DEFENCE", ln=True, align="C")
    pdf.set_font("Helvetica", "B", 24)
    pdf.cell(0, 15, "Security Assessment Report", ln=True, align="C")
    
    pdf.ln(25)
    pdf.set_font("Helvetica", "", 11)
    org_sanitized = _sanitize_for_pdf(org_name)
    target_sanitized = _sanitize_for_pdf(target)
    author_sanitized = _sanitize_for_pdf(author)
    
    pdf.cell(0, 7, f"Organization: {org_sanitized}", ln=True)
    pdf.cell(0, 7, f"Target Asset: {target_sanitized}", ln=True)
    pdf.cell(0, 7, f"Analyst: {author_sanitized}", ln=True)
    pdf.cell(0, 7, f"Date: {dt.datetime.now().strftime('%B %d, %Y at %H:%M UTC')}", ln=True)
    
    pdf.ln(35)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "CLASSIFICATION: CONFIDENTIAL", ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(0, 5, "This report contains sensitive security information and is intended only for authorized recipients. Unauthorized access, use, or disclosure is prohibited by law.")
    
    # ===== PAGE 2: EXECUTIVE SUMMARY =====
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "1. EXECUTIVE SUMMARY", ln=True)
    pdf.ln(3)
    
    score = summary.get("security_score", 0)
    if score >= 80:
        grade, assessment = "A (Excellent)", "Strong security posture with few issues"
    elif score >= 60:
        grade, assessment = "B (Good)", "Acceptable security level, some improvements needed"
    elif score >= 40:
        grade, assessment = "C (Fair)", "Multiple issues require attention to reduce risk"
    else:
        grade, assessment = "D (Poor)", "Critical issues must be addressed immediately"
    
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, f"Overall Security Grade: {grade}", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 8, f"Security Score: {score}/100", ln=True)
    pdf.multi_cell(0, 5, f"Assessment: {assessment}")
    
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "FINDING SUMMARY", ln=True)
    pdf.set_font("Helvetica", "", 9)
    
    vuln_sum = summary.get("vulnerability_summary", {})
    crit = vuln_sum.get('critical', 0)
    high = vuln_sum.get('high', 0)
    med = vuln_sum.get('medium', 0)
    low = vuln_sum.get('low', 0)
    pdf.cell(0, 5, f"Critical: {crit} | High: {high} | Medium: {med} | Low: {low}", ln=True)
    
    pdf.output(str(path))
    return str(path)


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
    rows = auth.get_user_reports(user["id"], limit=limit)
    
    if not rows:
        return {"reports": [], "total": 0}
    
    reports = []
    for row in rows:
        # Row structure: (id, user_id, target, org_name, author, pdf_path, created_at)
        report_dict = {
            "id": row[0],
            "user_id": row[1],
            "target": row[2] if row[2] else "N/A",
            "org_name": row[3] if row[3] else "N/A",
            "author": row[4] if row[4] else "Security Analyst",
            "pdf_path": row[5],
            "generated_at": row[6],
            "status": "COMPLETED",
            "score": "--"
        }
        reports.append(report_dict)
    
    return {"reports": reports, "total": len(reports)}


@router.get("/api/reports/{report_id}")
def get_user_report(report_id: int, authorization: str = Header(None)) -> dict:
    """Get a specific report by ID (user must own the report)."""
    user = get_current_user(authorization)
    report = auth.get_report_by_id(report_id, user_id=user["id"])
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found or access denied")
    
    return report
