"""
MODULE 6B — SHODAN INTERNET INTELLIGENCE
Queries Shodan API for device discovery and service information.
Identifies open ports, services, versions, and vulnerability information.
"""

import os
import json
import socket
import datetime
import logging
from pathlib import Path
from urllib.parse import urlparse

from rich.console import Console
from rich.panel import Panel

# ── Configuration ────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent.parent.parent
CONFIG_F = BASE_DIR / "config.json"
DATA_DIR = BASE_DIR / "data"

def load_config():
    defaults = {"shodan_api_key": ""}
    if CONFIG_F.exists():
        with open(CONFIG_F) as f:
            return {**defaults, **json.load(f)}
    return defaults

CONFIG = load_config()
CONFIG["shodan_api_key"] = os.environ.get("SHODAN_API_KEY", CONFIG.get("shodan_api_key", ""))

console = Console()

# ── Setup logging ────────────────────────────────────────────────
(DATA_DIR / "shodan").mkdir(parents=True, exist_ok=True)
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
# MODULE 6B — SHODAN INTERNET INTELLIGENCE
# ════════════════════════════════════════════════════════════════
def module_shodan(target=None, silent=False):
    """
    Shodan Internet Intelligence module
    
    Queries Shodan API for:
    - Open ports and services
    - Service versions and banners
    - Vulnerability information
    - Geographic and ISP data
    - Device identification
    """
    if not silent:
        console.print("[bold cyan]SHODAN — Internet Intelligence[/bold cyan]")
    
    if not target:
        target = console.input("\n[dim]Enter target domain/IP: [/dim]").strip()

    domain = get_domain(clean_url(target))
    api_key = CONFIG.get("shodan_api_key", "") or os.environ.get("SHODAN_API_KEY", "")
    
    results = {"target": domain, "timestamp": datetime.datetime.now().isoformat()}

    if not api_key:
        results["error"] = "Shodan API key not configured"
        if not silent:
            console.print("[red][ ! ][/red] Shodan API key not set. Add SHODAN_API_KEY to environment or config.json")
        return results

    try:
        import shodan
        api = shodan.Shodan(api_key)
        
        # DNS resolve - use socket instead of Shodan DNS API
        try:
            ip = socket.gethostbyname(domain)
        except socket.gaierror:
            ip = None
        results["resolved_ip"] = ip
        
        if ip:
            # Try host lookup (requires paid plan)
            try:
                host = api.host(ip)
                results["ip"] = host.get("ip_str", ip)
                results["organization"] = host.get("org", "Unknown")
                results["os"] = host.get("os", "Unknown")
                results["ports"] = host.get("ports", [])
                results["vulns"] = host.get("vulns", [])
                results["last_update"] = host.get("last_update", "")
                results["country"] = host.get("country_name", "Unknown")
                results["city"] = host.get("city", "Unknown")
                results["isp"] = host.get("isp", "Unknown")
                
                services = []
                for item in host.get("data", []):
                    services.append({
                        "port": item.get("port"),
                        "transport": item.get("transport", "tcp"),
                        "product": item.get("product", "Unknown"),
                        "version": item.get("version", ""),
                        "banner": (item.get("data", ""))[:200]
                    })
                results["services"] = services
                results["total_services"] = len(services)
                results["total_vulns"] = len(results["vulns"])
            except Exception as host_err:
                # Free plan fallback - use search instead
                results["ip"] = ip
                results["note"] = "Limited results (free Shodan plan). Upgrade for full host details."
                try:
                    search_results = api.search(f"ip:{ip}")
                    matches = search_results.get("matches", [])
                    ports = list(set(m.get("port") for m in matches if m.get("port")))
                    results["ports"] = ports
                    services = []
                    for m in matches[:10]:
                        services.append({
                            "port": m.get("port"),
                            "transport": m.get("transport", "tcp"),
                            "product": m.get("product", "Unknown"),
                            "version": m.get("version", ""),
                            "banner": (m.get("data", ""))[:200]
                        })
                    results["services"] = services
                    results["total_services"] = len(services)
                    results["organization"] = matches[0].get("org", "Unknown") if matches else "Unknown"
                    results["isp"] = matches[0].get("isp", "Unknown") if matches else "Unknown"
                    results["country"] = matches[0].get("location", {}).get("country_name", "Unknown") if matches else "Unknown"
                    results["city"] = matches[0].get("location", {}).get("city", "Unknown") if matches else "Unknown"
                except Exception:
                    results["error"] = f"Shodan query failed: {str(host_err)}"
        
    except Exception as e:
        results["error"] = str(e)
        if not silent:
            console.print(f"[red][ ! ][/red] Shodan error: {e}")

    fname = DATA_DIR / "shodan" / f"shodan_{domain}_{ts()}.json"
    fname.parent.mkdir(parents=True, exist_ok=True)
    with open(fname, "w") as f:
        json.dump(results, f, indent=2, default=str)
    save_db(domain, "shodan", results)
    
    if not silent:
        if "error" not in results:
            console.print(f"\n[green][ ✓ ][/green] Shodan scan complete")
        console.print(f"[green][ done ][/green] Saved to {fname}")
    return results
