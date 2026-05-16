"""
Export router for CyberDefence Platform.
Handles exporting scan results and vulnerabilities to CSV and JSON formats.
"""

import csv
import io
import json
import sys
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

import cyberdefence_platform_v31 as core
from frontend.backend.db import DatabaseConnection, USE_POSTGRESQL
from frontend.backend.routers.auth_routes import get_current_user

router = APIRouter()

# ── Database Helper Functions ──────────────────────────────────────
def execute_query(cursor, query: str, params: tuple = ()) -> None:
    """Execute query with automatic placeholder conversion."""
    if not USE_POSTGRESQL:
        query = query.replace("%s", "?")
    cursor.execute(query, params)

def fetch_query(cursor, query: str, params: tuple = ()) -> list:
    """Execute SELECT query and fetch results."""
    execute_query(cursor, query, params)
    return cursor.fetchall()

def fetch_one(cursor, query: str, params: tuple = ()) -> tuple:
    """Execute SELECT query and fetch one result."""
    execute_query(cursor, query, params)
    return cursor.fetchone()

# ── CSV Export Function ────────────────────────────────────────────
def export_scan_csv(scan_data: dict) -> str:
    """
    Convert scan data to CSV format.
    
    Args:
        scan_data: Scan results dictionary
        
    Returns:
        CSV string
    """
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        "Target",
        "Module",
        "Severity",
        "Finding",
        "Description",
        "Remediation",
        "Confidence",
        "Type"
    ])
    
    # Write vulnerability rows
    vulnerabilities = scan_data.get("vulnerabilities", [])
    if isinstance(vulnerabilities, str):
        try:
            vulnerabilities = json.loads(vulnerabilities)
        except:
            vulnerabilities = []
    
    for vuln in vulnerabilities:
        writer.writerow([
            scan_data.get("target", ""),
            vuln.get("module", ""),
            vuln.get("severity", ""),
            vuln.get("title", ""),
            vuln.get("description", "")[:100],  # Truncate long descriptions
            vuln.get("remediation", "")[:100],
            vuln.get("confidence", ""),
            vuln.get("type", "")
        ])
    
    return output.getvalue()

# ── Endpoint: GET /api/export/scan/{scan_id} ──────────────────────
@router.get("/export/scan/{scan_id}")
async def export_scan(
    scan_id: int,
    format: str = "csv",
    current_user: dict = Depends(get_current_user)
):
    """
    Export scan results in CSV or JSON format.
    
    Args:
        scan_id: Scan ID to export
        format: "csv" or "json"
        current_user: Authenticated user
        
    Returns:
        File download with appropriate headers
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    if format not in ["csv", "json"]:
        raise HTTPException(status_code=400, detail="Format must be 'csv' or 'json'")
    
    # Fetch scan from database
    db = DatabaseConnection()
    conn = db.connect()
    try:
        c = conn.cursor()
        user_id = current_user.get("user_id")
        
        # Get scan details (may be limited by ownership, but for now allow if accessible)
        query = """
            SELECT id, target_asset, module, timestamp, results
            FROM scan_history
            WHERE id = %s
        """
        scan = fetch_one(c, query, (scan_id,))
        
        if not scan:
            raise HTTPException(status_code=404, detail="Scan not found")
        
        scan_dict = {
            "id": scan[0],
            "target": scan[1],
            "module": scan[2],
            "timestamp": scan[3],
            "vulnerabilities": []
        }
        
        # Parse results
        try:
            results = json.loads(scan[4]) if isinstance(scan[4], str) else scan[4]
            scan_dict["vulnerabilities"] = results.get("vulnerabilities", []) if isinstance(results, dict) else []
        except:
            pass
        
        if format == "csv":
            csv_content = export_scan_csv(scan_dict)
            return StreamingResponse(
                iter([csv_content]),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=scan_{scan_id}.csv"}
            )
        else:  # json
            return StreamingResponse(
                iter([json.dumps(scan_dict, indent=2)]),
                media_type="application/json",
                headers={"Content-Disposition": f"attachment; filename=scan_{scan_id}.json"}
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export scan: {str(e)}")
    finally:
        conn.close()

# ── Endpoint: GET /api/export/vulnerabilities ──────────────────────
@router.get("/export/vulnerabilities")
async def export_vulnerabilities(
    target: Optional[str] = None,
    format: str = "csv",
    current_user: dict = Depends(get_current_user)
):
    """
    Export vulnerability list for a target in CSV or JSON format.
    
    Args:
        target: Target to export vulnerabilities for (optional - exports all if not provided)
        format: "csv" or "json"
        current_user: Authenticated user
        
    Returns:
        File download with appropriate headers
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    if format not in ["csv", "json"]:
        raise HTTPException(status_code=400, detail="Format must be 'csv' or 'json'")
    
    db = DatabaseConnection()
    conn = db.connect()
    try:
        c = conn.cursor()
        
        # Build query
        if target:
            query = """
                SELECT id, target_asset, module, timestamp, results
                FROM scan_history
                WHERE target_asset = %s
                ORDER BY timestamp DESC
            """
            scans = fetch_query(c, query, (target,))
        else:
            query = """
                SELECT id, target_asset, module, timestamp, results
                FROM scan_history
                ORDER BY timestamp DESC
                LIMIT 100
            """
            scans = fetch_query(c, query, ())
        
        # Aggregate all vulnerabilities
        all_vulns = []
        for scan in scans:
            scan_id, target_asset, module, timestamp, results = scan
            try:
                results_data = json.loads(results) if isinstance(results, str) else results
                vulns = results_data.get("vulnerabilities", []) if isinstance(results_data, dict) else []
                for vuln in vulns:
                    vuln["scan_id"] = scan_id
                    vuln["target"] = target_asset
                    vuln["module"] = module
                    vuln["timestamp"] = timestamp
                    all_vulns.append(vuln)
            except:
                pass
        
        if format == "csv":
            # Create CSV with aggregated vulnerabilities
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow([
                "Scan ID",
                "Target",
                "Module",
                "Timestamp",
                "Severity",
                "Finding",
                "Description",
                "Remediation",
                "Confidence",
                "Type"
            ])
            
            for vuln in all_vulns:
                writer.writerow([
                    vuln.get("scan_id", ""),
                    vuln.get("target", ""),
                    vuln.get("module", ""),
                    vuln.get("timestamp", ""),
                    vuln.get("severity", ""),
                    vuln.get("title", ""),
                    vuln.get("description", "")[:100],
                    vuln.get("remediation", "")[:100],
                    vuln.get("confidence", ""),
                    vuln.get("type", "")
                ])
            
            csv_content = output.getvalue()
            filename = f"vulnerabilities_{target}.csv" if target else "vulnerabilities_all.csv"
            
            return StreamingResponse(
                iter([csv_content]),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        else:  # json
            filename = f"vulnerabilities_{target}.json" if target else "vulnerabilities_all.json"
            
            return StreamingResponse(
                iter([json.dumps({"vulnerabilities": all_vulns, "count": len(all_vulns)}, indent=2)]),
                media_type="application/json",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export vulnerabilities: {str(e)}")
    finally:
        conn.close()

# ── Endpoint: GET /api/export/summary ──────────────────────────────
@router.get("/export/summary")
async def export_summary(
    target: Optional[str] = None,
    format: str = "json",
    current_user: dict = Depends(get_current_user)
):
    """
    Export a summary of scans for a target.
    
    Args:
        target: Target to summarize (optional)
        format: "csv" or "json"
        current_user: Authenticated user
        
    Returns:
        File download with appropriate headers
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    db = DatabaseConnection()
    conn = db.connect()
    try:
        c = conn.cursor()
        
        # Get scan summary
        if target:
            query = """
                SELECT target_asset, module, COUNT(*) as scan_count, MAX(timestamp) as last_scan
                FROM scan_history
                WHERE target_asset = %s
                GROUP BY target_asset, module
                ORDER BY target_asset, module
            """
            summaries = fetch_query(c, query, (target,))
        else:
            query = """
                SELECT target_asset, module, COUNT(*) as scan_count, MAX(timestamp) as last_scan
                FROM scan_history
                GROUP BY target_asset, module
                ORDER BY target_asset, module
                LIMIT 100
            """
            summaries = fetch_query(c, query, ())
        
        if format == "csv":
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["Target", "Module", "Scan Count", "Last Scan"])
            
            for summary in summaries:
                writer.writerow(summary)
            
            csv_content = output.getvalue()
            filename = f"summary_{target}.csv" if target else "summary_all.csv"
            
            return StreamingResponse(
                iter([csv_content]),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        else:  # json
            summary_list = [
                {
                    "target": s[0],
                    "module": s[1],
                    "scan_count": s[2],
                    "last_scan": s[3]
                }
                for s in summaries
            ]
            
            filename = f"summary_{target}.json" if target else "summary_all.json"
            
            return StreamingResponse(
                iter([json.dumps({"summary": summary_list, "count": len(summary_list)}, indent=2)]),
                media_type="application/json",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export summary: {str(e)}")
    finally:
        conn.close()
