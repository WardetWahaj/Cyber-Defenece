"""
MODULE 6C — ABUSEIPDB IP REPUTATION CHECK
Queries AbuseIPDB API for IP reputation and abuse reports.
Identifies malicious IPs with confidence scoring.
"""

import os
import json
import socket
import datetime
import logging
from pathlib import Path
from urllib.parse import urlparse

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

from rich.console import Console

# ── Configuration ────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent.parent.parent
CONFIG_F = BASE_DIR / "config.json"
DATA_DIR = BASE_DIR / "data"

def load_config():
    defaults = {
        "abuseipdb_api_key": "",
        "request_timeout": 10,
    }
    if CONFIG_F.exists():
        with open(CONFIG_F) as f:
            return {**defaults, **json.load(f)}
    return defaults

CONFIG = load_config()
CONFIG["abuseipdb_api_key"] = os.environ.get("ABUSEIPDB_API_KEY", CONFIG.get("abuseipdb_api_key", ""))
TIMEOUT = CONFIG["request_timeout"]

console = Console()

# ── Setup logging ────────────────────────────────────────────────
(DATA_DIR / "abuseipdb").mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    filename=DATA_DIR / "platform.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# ── Helpers ──────────────────────────────────────────────────────
def clean_url(url):
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url.rstrip("/")

def get_domain(url):
    return urlparse(clean_url(url)).netloc

def ts():
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

def save_db(target, module, results, user_id=None):
    try:
        import sqlite3
        db_file = DATA_DIR / "cyberdefence.db"
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target TEXT, module TEXT,
            timestamp TEXT, results TEXT, user_id INTEGER
        )""")
        c.execute("INSERT INTO scans (target,module,timestamp,results,user_id) VALUES (?,?,?,?,?)",
                  (target, module, datetime.datetime.now().isoformat(), json.dumps(results, default=str), user_id))
        conn.commit()
        conn.close()
    except Exception as e:
        logging.warning(f"Database save error: {e}")

# ════════════════════════════════════════════════════════════════
# MODULE 6C — ABUSEIPDB IP REPUTATION CHECK
# ════════════════════════════════════════════════════════════════
def module_abuseipdb(target=None, silent=False):
    """
    AbuseIPDB IP Reputation Check module
    
    Queries AbuseIPDB API for:
    - IP abuse confidence score (0-100)
    - Total abuse reports count
    - Distinct reporter count
    - ISP and country information
    - Whitelist status
    - Usage type classification
    """
    if not silent:
        console.print("[bold cyan]ABUSEIPDB — IP Reputation Check[/bold cyan]")
    
    if not target:
        target = console.input("\n[dim]Enter target domain/IP: [/dim]").strip()

    domain = get_domain(clean_url(target))
    api_key = CONFIG.get("abuseipdb_api_key", "") or os.environ.get("ABUSEIPDB_API_KEY", "")
    
    results = {"target": domain, "timestamp": datetime.datetime.now().isoformat()}

    if not api_key:
        results["error"] = "AbuseIPDB API key not configured"
        if not silent:
            console.print("[red][ ! ][/red] AbuseIPDB API key not set. Add ABUSEIPDB_API_KEY to environment or config.json")
        return results

    try:
        # Resolve domain to IP
        ip = socket.gethostbyname(domain)
        results["resolved_ip"] = ip
        
        # Check IP reputation
        headers = {"Key": api_key, "Accept": "application/json"}
        params = {"ipAddress": ip, "maxAgeInDays": 90, "verbose": True}
        r = requests.get("https://api.abuseipdb.com/api/v2/check", headers=headers, params=params, timeout=15)
        
        if r.status_code == 200:
            data = r.json().get("data", {})
            results["abuse_confidence_score"] = data.get("abuseConfidenceScore", 0)
            results["total_reports"] = data.get("totalReports", 0)
            results["country_code"] = data.get("countryCode", "")
            results["isp"] = data.get("isp", "")
            results["domain"] = data.get("domain", "")
            results["is_public"] = data.get("isPublic", True)
            results["is_whitelisted"] = data.get("isWhitelisted", False)
            results["last_reported_at"] = data.get("lastReportedAt", "")
            results["usage_type"] = data.get("usageType", "")
            results["num_distinct_users"] = data.get("numDistinctUsers", 0)
        else:
            results["error"] = f"API returned status {r.status_code}"
            
    except Exception as e:
        results["error"] = str(e)
        if not silent:
            console.print(f"[red][ ! ][/red] AbuseIPDB error: {e}")

    fname = DATA_DIR / "abuseipdb" / f"abuseipdb_{domain}_{ts()}.json"
    fname.parent.mkdir(parents=True, exist_ok=True)
    with open(fname, "w") as f:
        json.dump(results, f, indent=2, default=str)
    save_db(domain, "abuseipdb", results)
    
    if not silent:
        if "error" not in results:
            console.print(f"\n[green][ ✓ ][/green] AbuseIPDB check complete")
        console.print(f"[green][ done ][/green] Saved to {fname}")
    return results
