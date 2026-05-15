"""
MODULE 6 — VIRUSTOTAL REPUTATION CHECK
Queries VirusTotal API for domain/IP reputation across 90+ antivirus engines.
Includes malware detection, suspicious activity, and whois information.
"""

import os
import json
import re
import socket
import time
import datetime
import logging
import base64
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
        "virustotal_api_key": "",
        "request_timeout": 10,
        "rate_limit_delay": 1.5,
    }
    if CONFIG_F.exists():
        with open(CONFIG_F) as f:
            return {**defaults, **json.load(f)}
    return defaults

CONFIG = load_config()
CONFIG["virustotal_api_key"] = os.environ.get("VIRUSTOTAL_API_KEY", CONFIG.get("virustotal_api_key", ""))
TIMEOUT = CONFIG["request_timeout"]

console = Console()

# ── Setup logging ────────────────────────────────────────────────
(DATA_DIR / "virustotal").mkdir(parents=True, exist_ok=True)
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
# MODULE 6 — VIRUSTOTAL REPUTATION CHECK
# ════════════════════════════════════════════════════════════════
def module_virustotal(target=None, silent=False):
    """
    VirusTotal Reputation Check module
    
    Queries VirusTotal API v3 for:
    - Domain reputation across 90+ AV engines
    - Resolved IP address and geographic info
    - Malicious/suspicious/harmless detection counts
    - URL reputation
    - ASN and ISP information
    """
    if not silent:
        console.print("[bold cyan]MODULE 6 — VirusTotal Reputation Check (90+ engines)[/bold cyan]")

    key = CONFIG.get("virustotal_api_key", "")
    if not key or key == "PASTE_YOUR_VIRUSTOTAL_KEY_HERE":
        console.print("[red][ ! ][/red] VirusTotal API key not configured.")
        console.print("[dim]    Open config.json and add your VirusTotal API key.[/dim]")
        if not silent:
            console.input("\n[dim]Press Enter to return...[/dim]")
        return {}

    if not target:
        target = console.input("\n[dim]Enter domain or IP to check: [/dim]").strip() or "example.com"

    domain = get_domain(clean_url(target)) if "http" in target else target
    console.print(f"\n[cyan][ * ][/cyan] Checking [bold]{domain}[/bold] across 90+ AV engines via VirusTotal...")

    headers = {"x-apikey": key}
    results = {"target": domain, "timestamp": datetime.datetime.now().isoformat()}

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                  BarColumn(), console=console) as prog:
        task = prog.add_task("[cyan]Querying VirusTotal...", total=3)

        # Domain report
        prog.update(task, description="[cyan]Fetching domain report...")
        try:
            r = requests.get(f"https://www.virustotal.com/api/v3/domains/{domain}",
                             headers=headers, timeout=15)
            if r.status_code == 200:
                data = r.json().get("data", {}).get("attributes", {})
                stats = data.get("last_analysis_stats", {})
                results["domain_stats"] = stats
                results["reputation"] = data.get("reputation", 0)
                results["categories"] = data.get("categories", {})
                results["malicious"] = stats.get("malicious", 0)
                results["suspicious"] = stats.get("suspicious", 0)
                results["harmless"] = stats.get("harmless", 0)
                results["undetected"] = stats.get("undetected", 0)
                results["total_engines"] = sum(stats.values())
                results["whois"] = data.get("whois", "")[:300]
                results["registrar"] = data.get("registrar", "Unknown")
                results["creation_date"] = data.get("creation_date", "")
            elif r.status_code == 404:
                results["error"] = "Domain not found in VirusTotal database"
            elif r.status_code == 401:
                results["error"] = "Invalid API key"
            else:
                results["error"] = f"API returned {r.status_code}"
        except Exception as e:
            results["error"] = str(e)
        prog.advance(task)
        rate_sleep()

        # IP resolution check
        prog.update(task, description="[cyan]Checking resolved IPs...")
        try:
            ip = socket.gethostbyname(domain)
            results["resolved_ip"] = ip
            ip_r = requests.get(f"https://www.virustotal.com/api/v3/ip_addresses/{ip}",
                                headers=headers, timeout=15)
            if ip_r.status_code == 200:
                ip_data = ip_r.json().get("data", {}).get("attributes", {})
                ip_stats = ip_data.get("last_analysis_stats", {})
                results["ip_malicious"] = ip_stats.get("malicious", 0)
                results["ip_suspicious"] = ip_stats.get("suspicious", 0)
                results["ip_country"] = ip_data.get("country", "Unknown")
                results["ip_asn"] = ip_data.get("asn", "")
                results["ip_as_owner"] = ip_data.get("as_owner", "")
        except Exception as e:
            results["ip_error"] = str(e)
        prog.advance(task)
        rate_sleep()

        # URL scan
        prog.update(task, description="[cyan]Checking URL reputation...")
        try:
            url_b64 = base64.urlsafe_b64encode(f"https://{domain}".encode()).decode().rstrip("=")
            url_r = requests.get(f"https://www.virustotal.com/api/v3/urls/{url_b64}",
                                 headers=headers, timeout=15)
            if url_r.status_code == 200:
                url_data = url_r.json().get("data", {}).get("attributes", {})
                url_stats = url_data.get("last_analysis_stats", {})
                results["url_malicious"] = url_stats.get("malicious", 0)
                results["url_suspicious"] = url_stats.get("suspicious", 0)
        except Exception as e:
            results["url_error"] = str(e)
        prog.advance(task)

    # Display results
    if "error" in results:
        console.print(f"[red][ ! ][/red] {results['error']}")
    else:
        console.print(f"\n[green][ ✓ ][/green] VirusTotal scan complete\n")
        mal = results.get("malicious", 0)
        susp = results.get("suspicious", 0)
        total = results.get("total_engines", 0)
        rep = results.get("reputation", 0)

        # Overall verdict
        if mal > 5:
            verdict = "[bold red]DANGEROUS — Multiple engines flagged this domain[/bold red]"
        elif mal > 0 or susp > 3:
            verdict = "[bold yellow]SUSPICIOUS — Some engines flagged this domain[/bold yellow]"
        else:
            verdict = "[bold green]CLEAN — No significant threats detected[/bold green]"

        console.print(Panel(verdict, border_style="cyan", title="Verdict"))

        t = Table(title=f"VirusTotal Report — {domain}", box=box.ROUNDED, border_style="cyan")
        t.add_column("Metric", style="dim", width=30)
        t.add_column("Value", style="white")
        t.add_row("Domain", domain)
        t.add_row("Resolved IP", results.get("resolved_ip", "?"))
        t.add_row("IP Country", results.get("ip_country", "?"))
        t.add_row("IP ASN Owner", results.get("ip_as_owner", "?"))
        t.add_row("Registrar", results.get("registrar", "?"))
        t.add_row("VT Reputation", str(rep))
        t.add_row("Total Engines", str(total))
        t.add_row("Malicious", f"[red]{mal}[/red]" if mal > 0 else f"[green]{mal}[/green]")
        t.add_row("Suspicious", f"[yellow]{susp}[/yellow]" if susp > 0 else f"[green]{susp}[/green]")
        t.add_row("Harmless", f"[green]{results.get('harmless', 0)}[/green]")
        t.add_row("Undetected", str(results.get("undetected", 0)))
        t.add_row("IP Malicious", f"[red]{results.get('ip_malicious', 0)}[/red]" if results.get("ip_malicious", 0) > 0 else "[green]0[/green]")
        t.add_row("URL Malicious", f"[red]{results.get('url_malicious', 0)}[/red]" if results.get("url_malicious", 0) > 0 else "[green]0[/green]")
        console.print(t)

        # Categories
        cats = results.get("categories", {})
        if cats:
            console.print(f"\n[dim]Categories: {', '.join(set(cats.values()))}[/dim]")

    fname = DATA_DIR / "virustotal" / f"vt_{domain}_{ts()}.json"
    with open(fname, "w") as f:
        json.dump(results, f, indent=2, default=str)
    save_db(domain, "virustotal", results)
    
    if not silent:
        console.print(f"\n[green][ ✓ ][/green] Saved to {fname}")
        console.input("\n[dim]Press Enter to return to main menu...[/dim]")
    
    return results
