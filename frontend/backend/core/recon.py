"""
MODULE 1 — RECONNAISSANCE & TECHNOLOGY SCANNING
Performs comprehensive technology discovery, HTTP fingerprinting, SSL analysis, 
port scanning, and security header auditing.
"""

import os
import json
import re
import ssl
import socket
import time
import datetime
import logging
from pathlib import Path
from urllib.parse import urlparse

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich import box

# ── Configuration ────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent.parent.parent
CONFIG_F = BASE_DIR / "config.json"
DATA_DIR = BASE_DIR / "data"

def load_config():
    defaults = {
        "request_timeout": 10,
        "rate_limit_delay": 1.5,
    }
    if CONFIG_F.exists():
        with open(CONFIG_F) as f:
            return {**defaults, **json.load(f)}
    return defaults

CONFIG = load_config()
TIMEOUT = CONFIG["request_timeout"]

console = Console()

# ── Setup logging ────────────────────────────────────────────────
(DATA_DIR / "recon").mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    filename=DATA_DIR / "platform.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

try:
    import nmap
    NMAP_AVAILABLE = True
except ImportError:
    NMAP_AVAILABLE = False

# ── Helpers ──────────────────────────────────────────────────────
def clean_url(url):
    """Normalize URL to https:// format and remove trailing slashes"""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url.rstrip("/")

def get_domain(url):
    """Extract domain from URL"""
    return urlparse(clean_url(url)).netloc

def rate_sleep():
    """Apply rate limiting delay"""
    time.sleep(CONFIG["rate_limit_delay"])

def ts():
    """Get timestamp string for file naming"""
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

def save_db(target, module, results, user_id=None):
    """Save results to database (if available)"""
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
# MODULE 1 — RECONNAISSANCE & TECHNOLOGY SCANNING
# ════════════════════════════════════════════════════════════════
def module_recon(target=None, silent=False):
    """
    Reconnaissance & Technology Scanning module
    
    Performs:
    - HTTP fingerprinting (server, version, CMS, tech stack)
    - SSL/TLS certificate validation
    - Port scanning
    - DNS resolution
    - robots.txt checking
    - Security headers audit
    """
    if not silent:
        console.print("[bold cyan]MODULE 1 — Reconnaissance & Technology Scanning[/bold cyan]")
    
    if not target:
        target = console.input("\n[dim]Enter target domain/URL: [/dim]").strip() or "testphp.vulnweb.com"

    url    = clean_url(target)
    domain = get_domain(url)
    results = {"target": url, "domain": domain, "timestamp": datetime.datetime.now().isoformat()}

    console.print(f"\n[cyan][ * ][/cyan] Scanning [bold]{url}[/bold]")

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                  BarColumn(), TextColumn("{task.percentage:>3.0f}%"), console=console) as prog:
        task = prog.add_task("[cyan]Initialising...", total=100)

        # ── HTTP fingerprint ─────────────────────────────────
        prog.update(task, description="[cyan]HTTP fingerprinting...", advance=0)
        try:
            r = requests.get(url, timeout=TIMEOUT, verify=False, allow_redirects=True)
            h = r.headers
            content = r.text.lower()
            results.update({
                "http_status": r.status_code,
                "final_url": r.url,
                "https": r.url.startswith("https://"),
                "server": h.get("Server", "Unknown"),
                "x_powered_by": h.get("X-Powered-By", ""),
            })
            
            # CMS detection
            cms = "Unknown"
            if "wp-content" in content or "wp-includes" in content:
                m = re.search(r'name=["\']generator["\'] content=["\']WordPress ([^"\']+)["\']', r.text)
                cms = f"WordPress {m.group(1)}" if m else "WordPress"
            elif "joomla" in content:
                cms = "Joomla"
            elif "drupal" in content:
                cms = "Drupal"
            elif "shopify" in content:
                cms = "Shopify"
            results["cms"] = cms

            # Tech stack detection
            tech = []
            if "jquery" in content:
                m = re.search(r'jquery[.-](\d+\.\d+[\.\d]*)', content)
                tech.append(f"jQuery {m.group(1) if m else ''}")
            if "bootstrap" in content:
                tech.append("Bootstrap")
            if "react" in content:
                tech.append("React")
            if "angular" in content:
                tech.append("Angular")
            if "vue" in content:
                tech.append("Vue.js")
            if "laravel" in content:
                tech.append("Laravel")
            if results["x_powered_by"]:
                tech.append(results["x_powered_by"])
            results["technologies"] = tech

            # Security headers audit
            sec_hdrs = {}
            for hdr in ["Strict-Transport-Security", "Content-Security-Policy",
                        "X-Frame-Options", "X-Content-Type-Options",
                        "X-XSS-Protection", "Referrer-Policy", "Permissions-Policy"]:
                sec_hdrs[hdr] = bool(h.get(hdr))
            results["security_headers"] = sec_hdrs

            # Cloudflare detection via CF-RAY
            cf_ray = h.get("CF-RAY", "")
            cf_server = "cloudflare" in h.get("Server", "").lower()
            results["cloudflare"] = bool(cf_ray or cf_server)
            results["cf_ray"] = cf_ray

        except Exception as e:
            results["http_error"] = str(e)
            console.print(f"[red][ ! ][/red] HTTP error: {e}")
        prog.update(task, advance=25)
        rate_sleep()

        # ── SSL certificate ──────────────────────────────────
        prog.update(task, description="[cyan]SSL certificate check...")
        ssl_info = {}
        try:
            ctx = ssl.create_default_context()
            with ctx.wrap_socket(socket.socket(), server_hostname=domain) as s:
                s.settimeout(5)
                s.connect((domain, 443))
                cert = s.getpeercert()
                ssl_info = {
                    "valid": True,
                    "expires": cert.get("notAfter", "?"),
                    "issuer": dict(x[0] for x in cert.get("issuer", [])),
                    "subject": dict(x[0] for x in cert.get("subject", [])),
                }
        except Exception as e:
            ssl_info = {"valid": False, "error": str(e)}
        results["ssl"] = ssl_info
        prog.update(task, advance=20)
        rate_sleep()

        # ── Port scanning ────────────────────────────────────
        prog.update(task, description="[cyan]Port scanning...")
        open_ports = []
        if NMAP_AVAILABLE:
            try:
                nm = nmap.PortScanner()
                nm.scan(domain, "21,22,23,25,53,80,443,3306,5432,6379,8080,8443,9200",
                        arguments="-T3 --open -sV")
                for host in nm.all_hosts():
                    for proto in nm[host].all_protocols():
                        for port in nm[host][proto]:
                            st = nm[host][proto][port]
                            if st["state"] == "open":
                                open_ports.append({
                                    "port": port,
                                    "service": st.get("name", "unknown"),
                                    "version": st.get("version", ""),
                                    "state": "open"
                                })
            except Exception as e:
                open_ports = [{"port": "error", "service": str(e), "state": "error"}]
        else:
            # Fallback to socket scanning
            for port in [21, 22, 23, 25, 80, 443, 3306, 8080, 8443]:
                try:
                    s = socket.socket()
                    s.settimeout(1)
                    if s.connect_ex((domain, port)) == 0:
                        try:
                            svc = socket.getservbyport(port, "tcp")
                        except Exception:
                            svc = "unknown"
                        open_ports.append({"port": port, "service": svc, "state": "open"})
                    s.close()
                except Exception:
                    pass
        results["open_ports"] = open_ports
        prog.update(task, advance=25)
        rate_sleep()

        # ── DNS resolution ───────────────────────────────────
        prog.update(task, description="[cyan]Resolving DNS...")
        try:
            results["ip_address"] = socket.gethostbyname(domain)
        except Exception:
            results["ip_address"] = "Could not resolve"
        prog.update(task, advance=15)

        # ── robots.txt check ────────────────────────────────
        prog.update(task, description="[cyan]Checking robots.txt...")
        try:
            rb = requests.get(url + "/robots.txt", timeout=5, verify=False)
            results["robots_txt"] = rb.status_code == 200
            results["robots_content"] = rb.text[:300] if rb.status_code == 200 else ""
        except Exception:
            results["robots_txt"] = False
        prog.update(task, advance=15)

    # ── Display results ──────────────────────────────────────────
    console.print(f"\n[green][ ✓ ][/green] Reconnaissance complete\n")
    t = Table(title=f"Recon — {domain}", box=box.ROUNDED, border_style="cyan")
    t.add_column("Property", style="dim", width=28)
    t.add_column("Value", style="white")
    t.add_row("IP Address", results.get("ip_address", "?"))
    t.add_row("HTTP Status", str(results.get("http_status", "?")))
    t.add_row("Server", results.get("server", "?"))
    t.add_row("CMS", results.get("cms", "Unknown"))
    t.add_row("X-Powered-By", results.get("x_powered_by", "None"))
    t.add_row("HTTPS", "[green]Yes[/green]" if results.get("https") else "[red]No[/red]")
    ssl_v = results.get("ssl", {})
    t.add_row("SSL Valid", "[green]Yes[/green]" if ssl_v.get("valid") else f"[red]No — {ssl_v.get('error', '')}[/red]")
    t.add_row("SSL Expires", ssl_v.get("expires", "?"))
    t.add_row("Cloudflare", "[green]Detected[/green]" if results.get("cloudflare") else "[yellow]Not detected[/yellow]")
    t.add_row("CF-RAY", results.get("cf_ray", "None"))
    t.add_row("Technologies", ", ".join(results.get("technologies", [])) or "None")
    ports = ", ".join(str(p["port"]) for p in results.get("open_ports", []))
    t.add_row("Open Ports", ports or "None found")
    t.add_row("robots.txt", "[green]Found[/green]" if results.get("robots_txt") else "[dim]Not found[/dim]")
    console.print(t)

    # Security headers table
    sh = results.get("security_headers", {})
    ht = Table(title="Security Headers", box=box.SIMPLE, border_style="cyan")
    ht.add_column("Header", style="dim", width=35)
    ht.add_column("Status", width=12)
    for h, v in sh.items():
        ht.add_row(h, "[green]Present[/green]" if v else "[red]Missing[/red]")
    console.print(ht)

    # Save results
    fname = DATA_DIR / "recon" / f"recon_{domain}_{ts()}.json"
    with open(fname, "w") as f:
        json.dump(results, f, indent=2, default=str)
    save_db(url, "recon", results)
    
    if not silent:
        console.print(f"\n[green][ ✓ ][/green] Saved to {fname}")
        console.input("\n[dim]Press Enter to return to main menu...[/dim]")
    
    return results
