from __future__ import annotations

import datetime as dt
import json
import os
import sys
import threading
import time
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv(ROOT_DIR / ".env")

import cyberdefence_platform_v31 as core
from fpdf import FPDF
from frontend.backend import auth

core.init_db()
auth.init_auth_db()

app = FastAPI(title="CyberDefence API", version="3.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TargetRequest(BaseModel):
    target: str = Field(..., min_length=1)


class PolicyRequest(BaseModel):
    policy_id: str = Field(default="1")
    org_name: str = Field(default="Organisation")


class ReportRequest(BaseModel):
    org_name: str = Field(default="Organisation")
    target: str = Field(default="N/A")
    author: str = Field(default="Security Analyst")
    include_pdf: bool = Field(default=True)


class CustomScanRequest(BaseModel):
    target: str = Field(..., min_length=1)
    modules: list[str] = Field(default_factory=list)


LIVE_JOBS: dict[str, dict[str, Any]] = {}
LIVE_JOBS_LOCK = threading.Lock()


def _history_rows(limit: int, user_id: str = None) -> list[dict[str, Any]]:
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


def _safe_call(name: str, fn, user_id=None):
    try:
        result = fn()
        # Save to database with user_id if provided
        if user_id:
            core.save_db(target="", module=name, results=result, user_id=user_id)
        else:
            core.save_db(target="", module=name, results=result)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"{name} failed: {exc}") from exc


def _derive_vuln_badge(result_blob: dict[str, Any]) -> str:
    summary = result_blob.get("summary", {}) if isinstance(result_blob, dict) else {}
    critical = int(summary.get("critical", 0))
    high = int(summary.get("high", 0))
    medium = int(summary.get("medium", 0))
    return f"{critical}C/{high}H/{medium}M"


def _derive_score(module: str, result_blob: dict[str, Any]) -> str:
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


def _module_siem_noninteractive(target: str) -> dict[str, Any]:
    events = core.generate_demo_events(60)

    ip_counts: dict[str, int] = {}
    for event in events:
                ip = str(event.get("ip", "unknown"))
                ip_counts[ip] = ip_counts.get(ip, 0) + 1

    top_ip_pairs = sorted(ip_counts.items(), key=lambda pair: pair[1], reverse=True)[:8]
    top_ips = [
        {
            "ip": ip,
            "country": "Unknown",
            "risk": f"{min(10.0, max(1.0, round(4.0 + count / 2.5, 1)))}/10",
            "events": count,
        }
        for ip, count in top_ip_pairs
    ]

    patterns: dict[str, int] = {}
    for event in events:
        attack_type = str(event.get("attack_type", "UNKNOWN"))
        patterns[attack_type] = patterns.get(attack_type, 0) + 1

    critical = sum(1 for event in events if core.SEVERITY_MAP.get(event.get("attack_type")) == "CRITICAL")
    high = sum(1 for event in events if core.SEVERITY_MAP.get(event.get("attack_type")) == "HIGH")
    medium = sum(1 for event in events if core.SEVERITY_MAP.get(event.get("attack_type")) == "MEDIUM")

    results = {
        "target": target,
        "events": len(events),
        "top_ips": top_ips,
        "patterns": patterns,
        "attack_counts": patterns,
        "critical": critical,
        "high": high,
        "medium": medium,
    }
    core.save_db(target or "siem", "siem", results)
    return results


def _new_live_job(target: str) -> dict[str, Any]:
    job_id = str(uuid.uuid4())
    now = dt.datetime.now().isoformat()
    return {
        "job_id": job_id,
        "target": target,
        "status": "running",
        "overall_progress": 0,
        "time_remaining": "~5:00",
        "kpis": {
            "threats_neutralized": 0,
            "open_ports_found": 0,
            "throughput": "0.0 GB/s",
            "module_elapsed": "00:00",
        },
        "modules": [
            {"id": 1, "name": "Reconnaissance Phase", "status": "running", "progress": 5, "elapsed": "00:10"},
            {"id": 2, "name": "Vulnerability Assessment", "status": "awaiting", "progress": 0, "elapsed": "00:00"},
            {"id": 3, "name": "Exploitation Payload Deployment", "status": "awaiting", "progress": 0, "elapsed": "00:00"},
            {"id": 4, "name": "Post-Exfiltration & Reporting", "status": "awaiting", "progress": 0, "elapsed": "00:00"},
        ],
        "subtasks": {
            "sql_injection_probe": {"status": "queued", "progress": 0},
            "buffer_overflow_tests": {"status": "queued", "progress": 0},
        },
        "console": [
            "[OK] Session created and module pipeline initialized.",
            "[*] Preparing reconnaissance engines...",
        ],
        "active_nodes": [
            {"region": "NA", "status": "active"},
            {"region": "EU", "status": "active"},
            {"region": "APAC", "status": "standby"},
        ],
        "created_at": now,
        "updated_at": now,
        "completed_at": None,
        "cancel_requested": False,
    }


def _update_live_job(job_id: str, update_fn) -> None:
    with LIVE_JOBS_LOCK:
        job = LIVE_JOBS.get(job_id)
        if not job:
            return
        update_fn(job)
        job["updated_at"] = dt.datetime.now().isoformat()


def _run_live_job(job_id: str) -> None:
    for progress in range(5, 101, 5):
        time.sleep(1.5)

        def _tick(job: dict[str, Any]) -> None:
            if job.get("cancel_requested"):
                job["status"] = "cancelled"
                job["time_remaining"] = "stopped"
                if not job.get("completed_at"):
                    job["completed_at"] = dt.datetime.now().isoformat()
                return

            job["overall_progress"] = progress
            remaining = max(0, (100 - progress) * 3)
            mins = remaining // 60
            secs = remaining % 60
            job["time_remaining"] = f"~{mins}:{secs:02d}"
            job["kpis"]["threats_neutralized"] = max(0, int(progress * 0.32))
            job["kpis"]["open_ports_found"] = max(0, int(progress * 1.8))
            job["kpis"]["throughput"] = f"{(2.1 + progress / 50):.1f} GB/s"
            job["kpis"]["module_elapsed"] = f"{int(progress * 0.6):02d}:{int((progress * 1.4) % 60):02d}"

            if progress < 30:
                job["modules"][0]["status"] = "running"
                job["modules"][0]["progress"] = min(100, progress * 3)
                job["modules"][1]["status"] = "awaiting"
            elif progress < 80:
                job["modules"][0]["status"] = "completed"
                job["modules"][0]["progress"] = 100
                job["modules"][1]["status"] = "running"
                job["modules"][1]["progress"] = min(100, (progress - 25) * 2)
                job["subtasks"]["sql_injection_probe"] = {"status": "ready", "progress": 100}
                job["subtasks"]["buffer_overflow_tests"] = {
                    "status": "scanning",
                    "progress": min(100, max(15, (progress - 35) * 2)),
                }
            else:
                job["modules"][0]["status"] = "completed"
                job["modules"][1]["status"] = "completed"
                job["modules"][1]["progress"] = 100
                job["modules"][2]["status"] = "completed"
                job["modules"][2]["progress"] = 100
                job["modules"][3]["status"] = "running" if progress < 100 else "completed"
                job["modules"][3]["progress"] = 100 if progress >= 100 else 70

            if progress in {20, 40, 60, 80, 100}:
                job["console"].append(f"[*] Progress checkpoint reached: {progress}%")
            if progress == 100:
                job["status"] = "completed"
                job["time_remaining"] = "0:00"
                job["console"].append("[OK] Full module sequence completed.")
                job["completed_at"] = dt.datetime.now().isoformat()

        _update_live_job(job_id, _tick)

        with LIVE_JOBS_LOCK:
            current = LIVE_JOBS.get(job_id)
            if not current or current.get("status") in {"cancelled", "completed"}:
                break


@app.get("/api/health")
def health() -> dict[str, Any]:
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
    limit = max(1, min(limit, 200))
    return {"items": _history_rows(limit), "count": limit}


@app.get("/api/dashboard")
def dashboard(authorization: str = Header(None)) -> dict[str, Any]:
    # Get current user for personalized dashboard
    user = get_current_user(authorization)
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
                "score": _derive_score(row["module"], blob),
                "vulns": _derive_vuln_badge(blob),
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


@app.post("/api/scan/live/start")
def scan_live_start(payload: TargetRequest) -> dict[str, Any]:
    job = _new_live_job(payload.target)
    with LIVE_JOBS_LOCK:
        LIVE_JOBS[job["job_id"]] = job

    t = threading.Thread(target=_run_live_job, args=(job["job_id"],), daemon=True)
    t.start()
    return {
        "job_id": job["job_id"],
        "status": job["status"],
        "target": job["target"],
        "created_at": job["created_at"],
    }


@app.get("/api/scan/live/{job_id}")
def scan_live_status(job_id: str) -> dict[str, Any]:
    with LIVE_JOBS_LOCK:
        job = LIVE_JOBS.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Live scan job not found")
        return json.loads(json.dumps(job))


@app.post("/api/scan/live/{job_id}/cancel")
def scan_live_cancel(job_id: str) -> dict[str, Any]:
    with LIVE_JOBS_LOCK:
        job = LIVE_JOBS.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Live scan job not found")
        job["cancel_requested"] = True
        job["status"] = "cancelling"
        job["updated_at"] = dt.datetime.now().isoformat()
    return {"job_id": job_id, "status": "cancelling"}


@app.post("/api/scan/recon")
def scan_recon(payload: TargetRequest, authorization: str = Header(None)) -> dict[str, Any]:
    user = get_current_user(authorization)
    return _safe_call("recon", lambda: core.module_recon(payload.target, silent=True), user_id=user["id"])


@app.post("/api/scan/vulnerability")
def scan_vulnerability(payload: TargetRequest, authorization: str = Header(None)) -> dict[str, Any]:
    user = get_current_user(authorization)
    recon_data = core.get_latest("recon")
    return _safe_call(
        "vulnerability",
        lambda: core.module_vuln(payload.target, silent=True, recon_data=recon_data),
        user_id=user["id"]
    )


@app.post("/api/scan/defence")
def scan_defence(payload: TargetRequest, authorization: str = Header(None)) -> dict[str, Any]:
    user = get_current_user(authorization)
    return _safe_call("defence", lambda: core.module_defence(payload.target, silent=True), user_id=user["id"])


@app.post("/api/scan/siem")
def scan_siem(payload: TargetRequest, authorization: str = Header(None)) -> dict[str, Any]:
    user = get_current_user(authorization)
    return _safe_call("siem", lambda: _module_siem_noninteractive(payload.target), user_id=user["id"])


@app.post("/api/scan/virustotal")
def scan_virustotal(payload: TargetRequest, authorization: str = Header(None)) -> dict[str, Any]:
    user = get_current_user(authorization)
    return _safe_call("virustotal", lambda: core.module_virustotal(payload.target, silent=True), user_id=user["id"])


@app.post("/api/scan/custom")
def scan_custom(payload: CustomScanRequest, authorization: str = Header(None)) -> dict[str, Any]:
    user = get_current_user(authorization)
    requested = payload.modules or ["recon", "vulnerability", "defence", "siem", "virustotal"]
    allowed = {
        "recon": lambda target: core.module_recon(target, silent=True),
        "vulnerability": lambda target: core.module_vuln(target, silent=True, recon_data=core.get_latest("recon")),
        "defence": lambda target: core.module_defence(target, silent=True),
        "siem": lambda target: core.module_siem(target, silent=True),
        "virustotal": lambda target: core.module_virustotal(target, silent=True),
    }

    results: dict[str, Any] = {}
    for module_name in requested:
        if module_name not in allowed:
            continue
        results[module_name] = _safe_call(module_name, lambda m=module_name: allowed[m](payload.target), user_id=user["id"])

    return {
        "target": payload.target,
        "modules": list(results.keys()),
        "results": results,
        "completed_at": dt.datetime.now().isoformat(),
    }


@app.post("/api/scan/auto")
def scan_auto(payload: TargetRequest, authorization: str = Header(None)) -> dict[str, Any]:
    user = get_current_user(authorization)
    started = time.time()
    target = payload.target
    domain = core.get_domain(core.clean_url(target))

    recon = _safe_call("recon", lambda: core.module_recon(target, silent=True), user_id=user["id"])
    vulnerability = _safe_call("vulnerability", lambda: core.module_vuln(target, silent=True, recon_data=recon), user_id=user["id"])
    defence = _safe_call("defence", lambda: core.module_defence(target, silent=True), user_id=user["id"])
    siem = _safe_call("siem", lambda: _module_siem_noninteractive(target), user_id=user["id"])
    virustotal = _safe_call("virustotal", lambda: core.module_virustotal(domain, silent=True), user_id=user["id"])
    dashboard = _safe_call("dashboard", lambda: core.module_dashboard(silent=True), user_id=user["id"])

    return {
        "meta": {
            "target": target,
            "elapsed_seconds": round(time.time() - started, 2),
            "completed_at": dt.datetime.now().isoformat(),
        },
        "results": {
            "recon": recon,
            "vulnerability": vulnerability,
            "defence": defence,
            "siem": siem,
            "virustotal": virustotal,
            "dashboard": dashboard,
        },
    }


@app.post("/api/policy/generate")
def generate_policy(payload: PolicyRequest) -> dict[str, Any]:
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


def _sanitize_for_pdf(text: str) -> str:
    """Sanitize text to be compatible with Helvetica font in PDF"""
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
    
    pdf.cell(0, 6, f"  Critical Vulnerabilities: {crit} | High: {high} | Medium: {med} | Low: {low}", ln=True)
    
    defence = summary.get("defence", {})
    pdf.cell(0, 6, f"  Security Config Status: {defence.get('pass', 0)} Passed | {defence.get('fail', 0)} Failed | {defence.get('warn', 0)} Warnings", ln=True)
    
    siem = summary.get("siem", {})
    pdf.cell(0, 6, f"  Security Events: {siem.get('events', 0)} Total | {siem.get('critical', 0)} Critical | {siem.get('high', 0)} High", ln=True)
    
    vt = summary.get("virustotal", {})
    pdf.cell(0, 6, f"  Malware Analysis: {vt.get('malicious', 0)} Malicious (from {vt.get('total_engines', 0)} engines)", ln=True)
    
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "KEY RECOMMENDATIONS", ln=True)
    pdf.set_font("Helvetica", "", 9)
    
    if crit > 0:
        pdf.cell(0, 5, "  1. URGENT: Address {0} critical vulnerabilities immediately".format(crit), ln=True)
    if high > 0:
        pdf.cell(0, 5, "  2. HIGH PRIORITY: Fix {0} high-risk issues within 3-5 days".format(high), ln=True)
    if defence.get('fail', 0) > 0:
        pdf.cell(0, 5, "  3. Review and remediate {0} failed security checks".format(defence.get('fail', 0)), ln=True)
    pdf.cell(0, 5, "  4. Implement continuous monitoring and regular security assessments", ln=True)
    
    # ===== PAGE 3+: DETAILED VULNERABILITIES =====
    if details and details.get("vulnerabilities"):
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, "2. DETAILED VULNERABILITY FINDINGS", ln=True)
        pdf.ln(3)
        
        for i, vuln in enumerate(details.get("vulnerabilities", [])[:12], 1):
            severity = _sanitize_for_pdf(vuln.get("severity", "UNKNOWN"))
            vuln_name = _sanitize_for_pdf(vuln.get('name', 'Vulnerability'))
            
            pdf.set_font("Helvetica", "B", 10)
            severity_label = "[CRITICAL]" if severity == "CRITICAL" else "[HIGH]" if severity == "HIGH" else "[MEDIUM]" if severity == "MEDIUM" else "[LOW]"
            pdf.cell(0, 6, f"{i}. {severity_label} {vuln_name}", ln=True)
            
            pdf.set_font("Helvetica", "", 9)
            pdf.cell(0, 5, f"  CVSS: {vuln.get('cvss', 'N/A')}/10  |  Source: {_sanitize_for_pdf(vuln.get('source', 'Unknown'))}", ln=True)
            
            if vuln.get('cve_id') and vuln.get('cve_id') != 'N/A':
                pdf.cell(0, 5, f"  CVE: {_sanitize_for_pdf(vuln.get('cve_id'))}", ln=True)
            
            if vuln.get('evidence'):
                evidence = _sanitize_for_pdf(vuln.get('evidence')[:90])
                pdf.set_font("Helvetica", "", 8)
                pdf.cell(0, 5, f"  Finding: {evidence}", ln=True)
            
            # Add severity explanation
            if severity == "CRITICAL":
                pdf.set_font("Helvetica", "I", 8)
                pdf.cell(0, 5, "  Impact: Immediate risk - complete system compromise possible", ln=True)
                pdf.set_font("Helvetica", "", 9)
            elif severity == "HIGH":
                pdf.set_font("Helvetica", "I", 8)
                pdf.cell(0, 5, "  Impact: Significant risk - fix within 3-5 days", ln=True)
                pdf.set_font("Helvetica", "", 9)
            
            pdf.ln(2)
    
    # ===== SECURITY CONFIGURATION =====
    if details and details.get("defence_checks"):
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, "3. SECURITY CONFIGURATION AUDIT", ln=True)
        pdf.ln(3)
        
        passed = sum(1 for c in details.get("defence_checks", []) if c.get("status") == "PASS")
        failed = sum(1 for c in details.get("defence_checks", []) if c.get("status") == "FAIL")
        warned = sum(1 for c in details.get("defence_checks", []) if c.get("status") == "WARN")
        
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(0, 6, f"Security Configuration Status: {passed} Passed | {failed} Failed | {warned} Warnings", ln=True)
        pdf.ln(2)
        
        for i, check in enumerate(details.get("defence_checks", [])[:10], 1):
            status = check.get("status", "UNKNOWN")
            status_symbol = "[OK]" if status == "PASS" else "[FAIL]" if status == "FAIL" else "[!]"
            check_name = _sanitize_for_pdf(check.get('name', check.get('check', 'Check')))
            
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(0, 6, f"{i}. {status_symbol} {check_name}", ln=True)
            
            pdf.set_font("Helvetica", "", 8)
            pdf.cell(0, 5, f"  Status: {status}", ln=True)
            
            if check.get('description') or check.get('detail'):
                desc = _sanitize_for_pdf(check.get('description') or check.get('detail'))
                pdf.set_font("Helvetica", "", 7)
                pdf.cell(0, 5, f"  Detail: {desc[:70]}", ln=True)
            
            pdf.ln(1)
    
    # ===== SIEM EVENTS =====
    if details and details.get("siem_events") and len(details.get("siem_events", [])) > 0:
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, "4. SECURITY EVENTS & INCIDENT DETECTION", ln=True)
        pdf.ln(3)
        
        events_data = details.get("siem_events", [])
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(0, 6, f"Total Events Detected: {len(events_data)}", ln=True)
        pdf.ln(2)
        
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(0, 6, "Recent High/Critical Events:", ln=True)
        pdf.ln(1)
        
        for i, event in enumerate(events_data[:8], 1):
            severity = _sanitize_for_pdf(event.get('severity', 'INFO'))
            event_type = _sanitize_for_pdf(event.get('type', event.get('event_type', 'Event')))
            
            sev_indicator = "[!!]" if severity == "CRITICAL" else "[!]" if severity == "HIGH" else "[-]"
            
            pdf.set_font("Helvetica", "B", 8)
            pdf.cell(0, 5, f"{i}. {sev_indicator} {event_type}", ln=True)
            
            pdf.set_font("Helvetica", "", 8)
            pdf.cell(0, 5, f"  Severity: {severity}", ln=True)
            
            if event.get('description') or event.get('message'):
                desc = _sanitize_for_pdf(event.get('description') or event.get('message'))
                pdf.set_font("Helvetica", "", 7)
                pdf.cell(0, 5, f"  Details: {desc[:70]}", ln=True)
            
            pdf.ln(1)
    
    # ===== RECOMMENDATIONS PAGE =====
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "5. REMEDIATION ROADMAP & ACTION ITEMS", ln=True)
    pdf.ln(5)
    
    if crit > 0:
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 7, "PRIORITY 1: CRITICAL (Address Today)", ln=True)
        pdf.set_font("Helvetica", "", 9)
        pdf.multi_cell(0, 4.5, "These vulnerabilities pose an immediate and severe risk to your systems:\n- Stop affected services if necessary\n- Apply emergency patches or workarounds\n- Implement temporary mitigations\n- Schedule downtime for permanent fixes\n- Document all changes and approvals")
        pdf.ln(2)
    
    if high > 0:
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 7, "PRIORITY 2: HIGH (This Week)", ln=True)
        pdf.set_font("Helvetica", "", 9)
        pdf.multi_cell(0, 4.5, "These issues significantly increase security risk:\n- Plan remediation within 3-5 days\n- Apply vendor security patches\n- Test fixes in staging environment first\n- Implement additional monitoring\n- Update security policies if needed")
        pdf.ln(2)
    
    if med > 0 or defence.get("fail", 0) > 0:
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 7, "PRIORITY 3: MEDIUM & CONFIG (Next 2 Weeks)", ln=True)
        pdf.set_font("Helvetica", "", 9)
        pdf.multi_cell(0, 4.5, "Address these to improve overall security posture:\n- Fix configuration issues (enable security headers, WAF, etc.)\n- Remediate medium severity vulnerabilities\n- Implement missing security controls\n- Update and strengthen access controls\n- Enable security features in existing tools")
        pdf.ln(2)
    
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "ONGOING: Continuous Security Practices", ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(0, 4.5, "- Keep all systems, software, and plugins updated\n- Use strong, unique passwords with 2FA enabled\n- Monitor logs and alerts continuously\n- Perform regular backups and test recovery\n- Run security scans monthly and after changes\n- Train staff on security and phishing awareness")
    
    # ===== FOOTER PAGE =====
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "REPORT DETAILS", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.ln(5)
    
    pdf.cell(0, 7, f"Report Generated: {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}", ln=True)
    pdf.cell(0, 7, f"Target Asset: {target_sanitized}", ln=True)
    pdf.cell(0, 7, f"Organization: {org_sanitized}", ln=True)
    pdf.cell(0, 7, f"Analyst: {author_sanitized}", ln=True)
    pdf.cell(0, 7, f"Assessment Type: Comprehensive Security Evaluation", ln=True)
    pdf.cell(0, 7, f"Platform: Cyber Defence", ln=True)
    
    pdf.ln(15)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "SEVERITY DEFINITIONS", ln=True)
    pdf.set_font("Helvetica", "", 9)
    
    pdf.cell(0, 5, "CRITICAL: Immediate exploitation risk, likely to be attacked", ln=True)
    pdf.cell(0, 5, "HIGH: Significant risk, attackers would likely exploit", ln=True)
    pdf.cell(0, 5, "MEDIUM: Moderate risk, may be exploited in targeted attacks", ln=True)
    pdf.cell(0, 5, "LOW: Low risk, rarely exploited unless part of larger attack", ln=True)
    
    pdf.ln(10)
    pdf.set_font("Helvetica", "", 7)
    pdf.cell(0, 5, "CONFIDENTIALITY: This report is strictly confidential and intended only for", ln=True)
    pdf.cell(0, 5, "authorized recipients. Unauthorized access, use, or disclosure is prohibited.", ln=True)
    
    pdf.output(str(path))
    return str(path)


@app.post("/api/report/generate")
def generate_report(payload: ReportRequest, authorization: str = Header(None)) -> dict[str, Any]:
    user = get_current_user(authorization)
    vuln = core.get_latest("vuln", user_id=user["id"])
    defence = core.get_latest("defence", user_id=user["id"])
    siem = core.get_latest("siem", user_id=user["id"])
    vt = core.get_latest("virustotal", user_id=user["id"])

    summary = {
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
    }

    # Extract detailed findings
    detailed_vulnerabilities = vuln.get("vulnerabilities", [])[:15]  # Top 15
    detailed_defence_checks = defence.get("checks", [])[:12]  # Top 12
    detailed_siem_events = siem.get("events_list", [])[:10]  # Top 10 events
    
    details = {
        "vulnerabilities": detailed_vulnerabilities,
        "defence_checks": detailed_defence_checks,
        "siem_events": detailed_siem_events,
        "virustotal_full": vt,
    }
    
    pdf_path = None
    if payload.include_pdf:
        pdf_path = _create_pdf_report(payload.org_name, payload.target, payload.author, summary, details)

    # Save report to database
    report = auth.save_report(
        user_id=user["id"],
        target=payload.target,
        org_name=payload.org_name,
        author=payload.author,
        pdf_path=pdf_path
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


@app.get("/api/report/download")
def download_pdf(filename: str = None):
    """Download a generated PDF report file - mobile optimized"""
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


@app.get("/api/reports/list")
def list_user_reports(authorization: str = Header(None), limit: int = 100) -> dict:
    user = get_current_user(authorization)
    rows = core.get_history(limit=limit, user_id=user["id"])
    
    reports = []
    for row in rows:
        try:
            results = json.loads(row[4]) if row[4] else {}
            if results is None:
                results = {}
        except (json.JSONDecodeError, TypeError):
            results = {}
        reports.append({
            "id": f"RPT-{row[0]}",
            "target": row[1] or "N/A",
            "org_name": results.get("org_name", "N/A"),
            "generated_at": row[3],
            "score": results.get("score", results.get("security_score", "--")),
            "module": row[2],
        })
    
    return {"reports": reports, "total": len(reports)}


@app.get("/api/reports/{report_id}")
def get_user_report(report_id: int, authorization: str = Header(None)) -> dict:
    """Get a specific report by ID (user must own the report)"""
    user = get_current_user(authorization)
    report = auth.get_report_by_id(report_id, user_id=user["id"])
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found or access denied")
    
    return report


# ── Scan History Endpoints ────────────────────────────────────────

@app.get("/api/scan/history")
def get_scan_history(authorization: str = Header(None), limit: int = 20) -> dict:
    """Get authenticated user's scan history"""
    user = get_current_user(authorization)
    history = core.get_history(limit=limit, user_id=user["id"])
    
    scans = []
    for row in history:
        scans.append({
            "id": row[0],
            "target": row[1],
            "module": row[2],
            "timestamp": row[3],
            "results": json.loads(row[4]) if row[4] else {}
        })
    
    return {
        "user_id": user["id"],
        "total": len(scans),
        "scans": scans
    }


# ── Authentication Endpoints ───────────────────────────────────────

def get_current_user(authorization: str = Header(None)) -> dict:
    """Extract and verify user from Authorization header."""
    if not authorization:
        raise HTTPException(status_code=401, detail="No authorization header")
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid auth scheme")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    payload = auth.verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Convert user_id to integer (JWT stores it as string)
    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Invalid token format")
    
    user = auth.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user


@app.post("/api/auth/signup")
def signup(request: auth.SignupRequest) -> dict:
    """Create a new user account."""
    user = auth.create_user(
        email=request.email,
        full_name=request.full_name,
        password=request.password,
        organization=request.organization
    )
    
    if not user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create access token (convert user ID to string for JWT spec)
    access_token = auth.create_access_token(data={"sub": str(user["id"])})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "organization": user["organization"]
        }
    }


@app.post("/api/auth/login")
def login(request: auth.LoginRequest) -> dict:
    """Authenticate user and return access token."""
    user = auth.get_user_by_email(request.email)
    
    if not user or not auth.verify_password(request.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Update last login
    auth.update_last_login(user["id"])
    
    # Create access token (convert user ID to string for JWT spec)
    access_token = auth.create_access_token(data={"sub": str(user["id"])})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "organization": user["organization"]
        }
    }


@app.get("/api/auth/me")
def get_current_user_info(authorization: str = Header(None)) -> dict:
    """Get current authenticated user info."""
    user = get_current_user(authorization)
    return {
        "id": user["id"],
        "email": user["email"],
        "full_name": user["full_name"],
        "organization": user["organization"],
        "created_at": user["created_at"]
    }


@app.post("/api/auth/forgot-password")
def forgot_password(request: auth.PasswordResetRequest) -> dict:
    """
    Request a password reset token via email.
    Uses SHA-256 hashed tokens stored in database.
    
    ✅ PRODUCTION MODE - Sends real emails via Gmail SMTP
    ✅ Security: Always returns success message whether email exists or not,
       preventing email enumeration attacks.
    """
    try:
        # Query user - but don't reveal if found or not
        user = auth.get_user_by_email(request.email)
        
        if user:
            # User exists - generate and send reset token
            raw_token = auth.create_reset_token_for_user(user["id"])
            
            if raw_token:
                # Build the reset URL (user will click this or paste the token)
                frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
                reset_url = f"{frontend_url}/reset-password/{raw_token}"
                
                # Send email with reset URL via Gmail SMTP
                # This will raise an exception if email sending fails
                try:
                    auth.send_reset_email(
                        to_email=request.email,
                        reset_url=reset_url,
                        user_name=user.get("full_name", "User")
                    )
                except Exception as e:
                    # Log the error but still return generic success (don't reveal email sending issues)
                    print(f"❌ Failed to send reset email: {str(e)}")
                    # In production, you might want to return 500 here
                    # For now, we silently fail to avoid revealing if email exists
        
        # Always return success message (security best practice)
        # Same response whether email exists or not = no email enumeration
        return {
            "status": "success",
            "message": "If this email is registered, a password reset link has been sent"
        }
        
    except Exception as e:
        # Unexpected error - log and return 500
        print(f"❌ Unexpected error in forgot_password: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred processing your request")


@app.post("/api/auth/reset-password")
def reset_password(request: auth.PasswordResetConfirm) -> dict:
    """
    Reset password using a valid reset token.
    Uses SHA-256 hashed tokens verified against database.
    
    The token must be:
    1. Present and unhashed in the request
    2. Match the hashed value in the database
    3. Not be expired (less than 1 hour old)
    """
    # Verify the reset token
    user = auth.verify_reset_token(request.token)
    
    if not user:
        # Token is invalid or expired
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    
    # Validate new password
    try:
        # Use the existing validator from the model
        auth.PasswordResetConfirm.parse_obj({"token": request.token, "new_password": request.new_password})
    except Exception as e:
        raise HTTPException(status_code=422, detail="Password does not meet requirements")
    
    # Update password to the new value (hashed with Argon2id)
    auth.update_password(user["id"], request.new_password)
    
    # Invalidate the reset token (prevent reuse)
    auth.invalidate_reset_token(user["id"])
    
    return {
        "status": "success",
        "message": "Password reset successfully"
    }


# Legacy endpoints for backward compatibility
@app.post("/api/auth/password-reset-request")
def password_reset_request(request: auth.PasswordResetRequest) -> dict:
    """Deprecated - use /api/auth/forgot-password instead."""
    return forgot_password(request)


@app.post("/api/auth/password-reset-confirm")
def password_reset_confirm(request: auth.PasswordResetConfirm) -> dict:
    """Deprecated - use /api/auth/reset-password instead."""
    return reset_password(request)


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
    