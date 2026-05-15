"""
MODULE 3 — DEFENCE CONFIGURATION CHECK
Audits security infrastructure including HTTPS, HTTP redirects, security headers,
WAF detection, Cloudflare, and malware/blacklist status via Sucuri SiteCheck.
"""

import os
import json
import re
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
(DATA_DIR / "defence").mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    filename=DATA_DIR / "platform.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# ── Helpers from recon module ────────────────────────────────────
def clean_url(url):
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url.rstrip("/")

def get_domain(url):
    return urlparse(clean_url(url)).netloc

def rate_sleep():
    time.sleep(CONFIG["rate_limit_delay"])

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
# HELPER FUNCTIONS
# ════════════════════════════════════════════════════════════════
def check_security_headers_grade(url, domain):
    """Grade HTTP security headers via SecurityHeaders.com"""
    grade = "?"
    try:
        r = requests.get(f"https://securityheaders.com/?q={domain}&followRedirects=on",
                         timeout=10, allow_redirects=True)
        m = re.search(r'class=["\']grade["\'][^>]*>([A-F][+-]?)<', r.text)
        if not m:
            m = re.search(r'>([A-F][+-]?)</span>', r.text)
        grade = m.group(1) if m else "?"
        if grade == "?":
            grade = r.headers.get("X-Grade", "?")
    except Exception as e:
        logging.warning(f"SecurityHeaders.com error: {e}")
    return grade

def check_sucuri(domain):
    """Check Sucuri SiteCheck for malware/blacklist presence"""
    result = {"clean": None, "blacklisted": False, "malware": False, "details": ""}
    try:
        r = requests.get(f"https://sitecheck.sucuri.net/results/{domain}",
                         timeout=15, verify=False)
        content = r.text.lower()
        result["blacklisted"] = "blacklisted" in content
        result["malware"] = "malware" in content and "no malware" not in content
        result["clean"] = not result["blacklisted"] and not result["malware"]
        if result["clean"]:
            result["details"] = "No malware or blacklist entries found"
        else:
            result["details"] = ("Blacklisted! " if result["blacklisted"] else "") + \
                                ("Malware detected!" if result["malware"] else "")
    except Exception as e:
        result["details"] = f"Could not reach Sucuri: {e}"
        result["clean"] = None
    return result

# ════════════════════════════════════════════════════════════════
# MODULE 3 — DEFENCE CONFIGURATION CHECK
# ════════════════════════════════════════════════════════════════
def module_defence(target=None, silent=False):
    """
    Defence Configuration Check module
    
    Performs:
    - HTTPS/SSL certificate validation
    - HTTP → HTTPS redirect check
    - HTTP Security Headers grading (SecurityHeaders.com)
    - WAF/Firewall detection
    - Cloudflare DDoS protection detection
    - WordPress admin URL accessibility
    - XML-RPC endpoint check
    - Sucuri malware/blacklist check
    - Manual verification recommendations
    """
    if not silent:
        console.print("[bold cyan]MODULE 3 — Defence Configuration Check[/bold cyan]")
    
    if not target:
        target = console.input("\n[dim]Enter target URL: [/dim]").strip() or "scanme.nmap.org"

    url = clean_url(target)
    domain = get_domain(url)
    checks = []
    console.print(f"\n[cyan][ * ][/cyan] Checking defence configuration for [bold]{url}[/bold]")

    def add(name, req, status, detail):
        checks.append({"name": name, "requirement": req, "status": status, "details": detail})

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                  BarColumn(), console=console) as prog:
        task = prog.add_task("[cyan]Running checks...", total=14)

        # 1. HTTPS
        prog.update(task, description="[cyan]HTTPS/SSL check...")
        try:
            r = requests.get(url, timeout=TIMEOUT, verify=True)
            add("HTTPS/SSL Certificate", "Prevention #2", "PASS", f"Valid cert, status {r.status_code}")
        except requests.exceptions.SSLError:
            add("HTTPS/SSL Certificate", "Prevention #2", "FAIL", "Invalid or self-signed certificate")
        except Exception:
            add("HTTPS/SSL Certificate", "Prevention #2", "FAIL", "HTTPS not available")
        prog.advance(task)
        time.sleep(0.3)

        # 2. HTTP→HTTPS redirect
        prog.update(task, description="[cyan]HTTP redirect check...")
        try:
            hr = requests.get(url.replace("https://", "http://"), timeout=TIMEOUT,
                              verify=False, allow_redirects=False)
            redir = hr.status_code in [301, 302, 307, 308] and \
                    "https" in hr.headers.get("Location", "").lower()
            add("HTTP→HTTPS Redirect", "Prevention #2",
                "PASS" if redir else "FAIL",
                f"HTTP {hr.status_code}" + (" → HTTPS" if redir else " (no redirect)"))
        except Exception as e:
            add("HTTP→HTTPS Redirect", "Prevention #2", "FAIL", str(e))
        prog.advance(task)
        time.sleep(0.3)

        # 3. Security headers + grade from SecurityHeaders.com
        prog.update(task, description="[cyan]SecurityHeaders.com grading...")
        try:
            r = requests.get(url, timeout=TIMEOUT, verify=False)
            required = ["Content-Security-Policy", "X-Frame-Options",
                        "X-Content-Type-Options", "Strict-Transport-Security"]
            missing = [h for h in required if h not in r.headers]
            grade = check_security_headers_grade(url, domain)
            status = "PASS" if not missing else "FAIL"
            detail = f"Grade: {grade} — " + ("All headers present" if not missing else f"Missing: {', '.join(missing)}")
            add("HTTP Security Headers (SecurityHeaders.com)", "Best Practice", status, detail)
        except Exception as e:
            add("HTTP Security Headers", "Best Practice", "FAIL", str(e))
        prog.advance(task)
        time.sleep(0.3)

        # 4. WAF detection
        prog.update(task, description="[cyan]WAF/Firewall detection...")
        try:
            tr = requests.get(url + "/?id=1'OR'1'='1", timeout=TIMEOUT, verify=False)
            waf_hdrs = ["CF-RAY", "X-Sucuri-ID", "X-Firewall", "X-WAF", "X-Cache-Status"]
            waf = any(h in tr.headers for h in waf_hdrs) or tr.status_code in [403, 406, 429]
            add("WAF / Firewall", "Prevention #1",
                "PASS" if waf else "WARN",
                "WAF detected" if waf else "Could not verify WAF presence")
        except Exception:
            add("WAF / Firewall", "Prevention #1", "WARN", "Could not verify")
        prog.advance(task)
        time.sleep(0.3)

        # 5. Cloudflare detection
        prog.update(task, description="[cyan]Cloudflare detection...")
        try:
            r = requests.get(url, timeout=TIMEOUT, verify=False)
            cf = "CF-RAY" in r.headers or "cloudflare" in r.headers.get("Server", "").lower()
            add("Cloudflare DDoS Protection", "Prevention #5",
                "PASS" if cf else "WARN",
                f"CF-RAY: {r.headers.get('CF-RAY', 'None')}" if cf else "Cloudflare not detected")
        except Exception:
            add("Cloudflare DDoS Protection", "Prevention #5", "WARN", "Could not verify")
        prog.advance(task)
        time.sleep(0.3)

        # 6. WP Admin URL
        prog.update(task, description="[cyan]WordPress admin URL...")
        try:
            ar = requests.get(url.rstrip("/") + "/wp-admin/", timeout=5,
                              verify=False, allow_redirects=True)
            acc = ar.status_code == 200
            add("WordPress Admin URL", "Prevention #1",
                "FAIL" if acc else "PASS",
                f"wp-admin → {ar.status_code}" + (" ACCESSIBLE!" if acc else " not accessible"))
        except Exception:
            add("WordPress Admin URL", "Prevention #1", "WARN", "Could not check")
        prog.advance(task)
        time.sleep(0.3)

        # 7. XML-RPC endpoint
        prog.update(task, description="[cyan]XML-RPC endpoint...")
        try:
            xr = requests.get(url.rstrip("/") + "/xmlrpc.php", timeout=5, verify=False)
            acc = xr.status_code == 200
            add("XML-RPC Endpoint", "Security Hardening",
                "FAIL" if acc else "PASS",
                f"xmlrpc.php → {xr.status_code}" + (" ACCESSIBLE!" if acc else " not accessible"))
        except Exception:
            add("XML-RPC Endpoint", "Security Hardening", "PASS", "Not accessible")
        prog.advance(task)
        time.sleep(0.3)

        # 8. Sucuri SiteCheck
        prog.update(task, description="[cyan]Sucuri SiteCheck...")
        sucuri = check_sucuri(domain)
        if sucuri["clean"] is True:
            add("Sucuri SiteCheck (Malware/Blacklist)", "Prevention #4", "PASS", sucuri["details"])
        elif sucuri["clean"] is False:
            add("Sucuri SiteCheck (Malware/Blacklist)", "Prevention #4", "FAIL", sucuri["details"])
        else:
            add("Sucuri SiteCheck (Malware/Blacklist)", "Prevention #4", "WARN", sucuri["details"])
        prog.advance(task)
        time.sleep(0.3)

        # 9-14. Manual checks
        for name, req, detail in [
            ("2FA / Google Authenticator", "Prevention #1", "Manual verification in WordPress settings"),
            ("Geo-blocking (RU/DE/PH)", "Prevention #1", "Manual verification in Wordfence → Blocking"),
            ("Anti-Brute Force (max 3 attempts)", "Prevention #1", "Manual verification in Wordfence → Login Security"),
            ("Antivirus Software Installed", "Prevention #3", "Manual verification on host machine"),
            ("Password Manager Configured", "Prevention #3", "Manual verification (KeyPass/1Password)"),
            ("Regular Backups Configured", "Prevention #6", "Manual verification of backup schedule"),
        ]:
            add(name, req, "WARN", detail)
            prog.advance(task)
            time.sleep(0.1)

    # Display results
    console.print(f"\n[green][ ✓ ][/green] Defence check complete\n")
    t = Table(title=f"Defence Config — {domain}", box=box.ROUNDED, border_style="cyan")
    t.add_column("Check", width=42)
    t.add_column("Requirement", width=18)
    t.add_column("Status", width=8)
    t.add_column("Details", width=35)

    pc = fc = wc = 0
    for c in checks:
        if c["status"] == "PASS":
            sc = "[green]✓ PASS[/green]"
            pc += 1
        elif c["status"] == "FAIL":
            sc = "[red]✗ FAIL[/red]"
            fc += 1
        else:
            sc = "[yellow]△ WARN[/yellow]"
            wc += 1
        t.add_row(c["name"], c["requirement"], sc, f"[dim]{c['details'][:35]}[/dim]")
    console.print(t)

    score = round((pc / len(checks)) * 100)
    sc2 = "green" if score > 60 else "yellow" if score > 30 else "red"
    console.print(f"\n[bold]Security Score: [{sc2}]{score}/100[/{sc2}][/bold]"
                  f"   [green]✓ {pc} PASS[/green]  |  [red]✗ {fc} FAIL[/red]  |  [yellow]△ {wc} WARN[/yellow]")

    results = {"target": url, "checks": checks, "score": score, "pass": pc, "fail": fc, "warn": wc, "sucuri": sucuri}
    fname = DATA_DIR / "defence" / f"defence_{domain}_{ts()}.json"
    with open(fname, "w") as f:
        json.dump(results, f, indent=2, default=str)
    save_db(url, "defence", results)
    
    if not silent:
        console.print(f"\n[green][ ✓ ][/green] Saved to {fname}")
        console.input("\n[dim]Press Enter to return to main menu...[/dim]")
    
    return results
