"""
Scan endpoints for the CyberDefence API.

Provides reconnaissance, vulnerability, defence, SIEM, VirusTotal, and custom scans.
Supports both job-based (async) and live scans with real-time progress tracking.
"""

import datetime as dt
import json
import threading
import time
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Header, Request
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address

import cyberdefence_platform_v31 as core
from frontend.backend.routers.auth_routes import get_current_user

router = APIRouter(prefix="/api/scan", tags=["scan"])
limiter = Limiter(key_func=get_remote_address)


class TargetRequest(BaseModel):
    target: str = Field(..., min_length=1)


class CustomScanRequest(BaseModel):
    target: str = Field(..., min_length=1)
    modules: list[str] = Field(default_factory=list)


# Global job tracking
LIVE_JOBS: dict[str, dict[str, Any]] = {}
LIVE_JOBS_LOCK = threading.Lock()

SCAN_JOBS: dict[str, dict] = {}
SCAN_JOBS_LOCK = threading.Lock()


def _module_siem_noninteractive(target: str) -> dict[str, Any]:
    """Run SIEM module in non-interactive mode (for API use)."""
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
    """Create a new live scan job structure."""
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
    """Update a live job with thread safety."""
    with LIVE_JOBS_LOCK:
        job = LIVE_JOBS.get(job_id)
        if not job:
            return
        update_fn(job)
        job["updated_at"] = dt.datetime.now().isoformat()


def _run_live_job(job_id: str) -> None:
    """Simulate a long-running live scan with progress updates."""
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


def _safe_call(name: str, fn, user_id=None):
    """Execute a scan module safely with error handling and database persistence."""
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


@router.post("/live/start")
def scan_live_start(payload: TargetRequest) -> dict[str, Any]:
    """Start a new live scan with real-time progress."""
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


@router.get("/live/{job_id}")
def scan_live_status(job_id: str) -> dict[str, Any]:
    """Get status of a live scan job."""
    with LIVE_JOBS_LOCK:
        job = LIVE_JOBS.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Live scan job not found")
        return json.loads(json.dumps(job))


@router.post("/live/{job_id}/cancel")
def scan_live_cancel(job_id: str) -> dict[str, Any]:
    """Cancel a running live scan."""
    with LIVE_JOBS_LOCK:
        job = LIVE_JOBS.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Live scan job not found")
        job["cancel_requested"] = True
        job["status"] = "cancelling"
        job["updated_at"] = dt.datetime.now().isoformat()
    return {"job_id": job_id, "status": "cancelling"}


@limiter.limit("10/minute")
@router.post("/recon")
def scan_recon(payload: TargetRequest, authorization: str = Header(None), request: Request = None) -> dict[str, Any]:
    """Run reconnaissance scan."""
    user = get_current_user(authorization)
    return _safe_call("recon", lambda: core.module_recon(payload.target, silent=True), user_id=user["id"])


@limiter.limit("10/minute")
@router.post("/vulnerability")
def scan_vulnerability(payload: TargetRequest, authorization: str = Header(None), request: Request = None) -> dict[str, Any]:
    """Run vulnerability assessment scan."""
    user = get_current_user(authorization)
    recon_data = core.get_latest("recon")
    return _safe_call(
        "vulnerability",
        lambda: core.module_vuln(payload.target, silent=True, recon_data=recon_data),
        user_id=user["id"]
    )


@limiter.limit("10/minute")
@router.post("/defence")
def scan_defence(payload: TargetRequest, authorization: str = Header(None), request: Request = None) -> dict[str, Any]:
    """Run defence/security headers assessment scan."""
    user = get_current_user(authorization)
    return _safe_call("defence", lambda: core.module_defence(payload.target, silent=True), user_id=user["id"])


@limiter.limit("10/minute")
@router.post("/siem")
def scan_siem(payload: TargetRequest, authorization: str = Header(None), request: Request = None) -> dict[str, Any]:
    """Run SIEM threat detection scan."""
    user = get_current_user(authorization)
    return _safe_call("siem", lambda: _module_siem_noninteractive(payload.target), user_id=user["id"])


@limiter.limit("10/minute")
@router.post("/virustotal")
def scan_virustotal(payload: TargetRequest, authorization: str = Header(None), request: Request = None) -> dict[str, Any]:
    """Run VirusTotal reputation scan."""
    user = get_current_user(authorization)
    return _safe_call("virustotal", lambda: core.module_virustotal(payload.target, silent=True), user_id=user["id"])


@limiter.limit("10/minute")
@router.post("/custom")
def scan_custom(payload: CustomScanRequest, authorization: str = Header(None), request: Request = None) -> dict[str, Any]:
    """Run custom scan with selected modules."""
    user = get_current_user(authorization)
    job_id = str(uuid.uuid4())
    
    with SCAN_JOBS_LOCK:
        SCAN_JOBS[job_id] = {"status": "running", "progress": 0, "result": None, "error": None}
    
    def run_scan():
        try:
            requested = payload.modules or ["recon", "vulnerability", "defence", "siem", "virustotal"]
            allowed = {
                "recon": lambda target: core.module_recon(target, silent=True),
                "vulnerability": lambda target: core.module_vuln(target, silent=True, recon_data=core.get_latest("recon")),
                "defence": lambda target: core.module_defence(target, silent=True),
                "siem": lambda target: _module_siem_noninteractive(target),
                "virustotal": lambda target: core.module_virustotal(target, silent=True),
            }

            results: dict[str, Any] = {}
            module_count = len(requested)
            for idx, module_name in enumerate(requested):
                if module_name not in allowed:
                    continue
                results[module_name] = _safe_call(module_name, lambda m=module_name: allowed[m](payload.target), user_id=user["id"])
                progress = int((idx + 1) / module_count * 100)
                with SCAN_JOBS_LOCK:
                    SCAN_JOBS[job_id]["progress"] = min(progress, 95)
            
            with SCAN_JOBS_LOCK:
                SCAN_JOBS[job_id]["progress"] = 100
                SCAN_JOBS[job_id]["status"] = "completed"
                SCAN_JOBS[job_id]["result"] = {
                    "target": payload.target,
                    "modules": list(results.keys()),
                    "results": results,
                    "completed_at": dt.datetime.now().isoformat(),
                }
        except Exception as e:
            with SCAN_JOBS_LOCK:
                SCAN_JOBS[job_id]["status"] = "failed"
                SCAN_JOBS[job_id]["error"] = str(e)
    
    t = threading.Thread(target=run_scan, daemon=True)
    t.start()
    return {"job_id": job_id, "status": "running", "message": "Scan started in background"}


@limiter.limit("10/minute")
@router.post("/auto")
def scan_auto(payload: TargetRequest, authorization: str = Header(None), request: Request = None) -> dict[str, Any]:
    """Run automated full security scan with all modules."""
    user = get_current_user(authorization)
    job_id = str(uuid.uuid4())
    
    with SCAN_JOBS_LOCK:
        SCAN_JOBS[job_id] = {"status": "running", "progress": 0, "result": None, "error": None}
    
    def run_scan():
        try:
            started = time.time()
            target = payload.target
            domain = core.get_domain(core.clean_url(target))
            
            recon = _safe_call("recon", lambda: core.module_recon(target, silent=True), user_id=user["id"])
            with SCAN_JOBS_LOCK:
                SCAN_JOBS[job_id]["progress"] = 20
            
            vulnerability = _safe_call("vulnerability", lambda: core.module_vuln(target, silent=True, recon_data=recon), user_id=user["id"])
            with SCAN_JOBS_LOCK:
                SCAN_JOBS[job_id]["progress"] = 40
            
            defence = _safe_call("defence", lambda: core.module_defence(target, silent=True), user_id=user["id"])
            with SCAN_JOBS_LOCK:
                SCAN_JOBS[job_id]["progress"] = 60
            
            siem = _safe_call("siem", lambda: _module_siem_noninteractive(target), user_id=user["id"])
            with SCAN_JOBS_LOCK:
                SCAN_JOBS[job_id]["progress"] = 80
            
            virustotal = _safe_call("virustotal", lambda: core.module_virustotal(domain, silent=True), user_id=user["id"])
            dashboard = _safe_call("dashboard", lambda: core.module_dashboard(silent=True), user_id=user["id"])
            with SCAN_JOBS_LOCK:
                SCAN_JOBS[job_id]["progress"] = 100
                SCAN_JOBS[job_id]["status"] = "completed"
                SCAN_JOBS[job_id]["result"] = {
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
        except Exception as e:
            with SCAN_JOBS_LOCK:
                SCAN_JOBS[job_id]["status"] = "failed"
                SCAN_JOBS[job_id]["error"] = str(e)
    
    t = threading.Thread(target=run_scan, daemon=True)
    t.start()
    return {"job_id": job_id, "status": "running", "message": "Scan started in background"}


@router.get("/status/{job_id}")
def scan_job_status(job_id: str) -> dict[str, Any]:
    """Get status of an async scan job."""
    with SCAN_JOBS_LOCK:
        job = SCAN_JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/history")
def get_scan_history(authorization: str = Header(None), limit: int = 20) -> dict:
    """Get authenticated user's scan history."""
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
