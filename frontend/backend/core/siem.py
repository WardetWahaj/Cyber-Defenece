"""
MODULE 4 — SIEM LOG ANALYSIS & THREAT DETECTION
Analyzes Apache, Nginx, fail2ban logs and generates synthetic attack events.
Detects SQL injection, XSS, brute force, DDoS, and other attack patterns.
"""

import os
import json
import re
import time
import datetime
import random
import logging
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich import box

# ── Configuration ────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent.parent.parent
CONFIG_F = BASE_DIR / "config.json"
DATA_DIR = BASE_DIR / "data"

def load_config():
    defaults = {"rate_limit_delay": 1.5}
    if CONFIG_F.exists():
        try:
            with open(CONFIG_F) as f:
                return {**defaults, **json.load(f)}
        except Exception:
            return defaults
    return defaults

CONFIG = load_config()

console = Console()

# ── Setup logging ────────────────────────────────────────────────
(DATA_DIR / "siem").mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    filename=DATA_DIR / "platform.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# ── Helpers ──────────────────────────────────────────────────────
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

def sev_color(s):
    return {"CRITICAL": "bold red", "HIGH": "red", "MEDIUM": "yellow", "LOW": "green"}.get(s.upper(), "white")

# ════════════════════════════════════════════════════════════════
# ATTACK PATTERNS & SEVERITY MAP
# ════════════════════════════════════════════════════════════════
ATTACK_PATTERNS = {
    "SQL_INJECTION": [
        r"(union\s+select|select\s+\*|drop\s+table|'--|or\s+1=1|benchmark\s*\(|sleep\s*\()",
        r"(%27|%22|%3D%27)"
    ],
    "XSS_ATTEMPT": [
        r"(<script|javascript:|onerror=|onload=|alert\s*\()",
        r"(%3Cscript|%3c%73%63%72%69%70%74)"
    ],
    "DIRECTORY_TRAVERSAL": [r"(\.\./|\.\.\\|%2e%2e%2f|\.\.%2f)"],
    "BRUTE_FORCE": [r"(wp-login\.php|/admin/login|/login\.php)"],
    "MALWARE_UPLOAD": [r"\.(php|php3|phtml|phar|asp|aspx|jsp|sh|exe)\s*(HTTP|$)"],
    "PORT_SCAN": [r"(nmap|masscan|zmap|nikto|sqlmap|dirbuster)"],
    "CREDENTIAL_STUFFING": [r"(POST /wp-login|POST /login|POST /signin|POST /auth)"],
    "DOS_ATTACK": [r"(flood|ddos|dos_attack)"],
    "UNAUTHORIZED_ACCESS": [r"(401|403).*(admin|root|config|passwd|shadow)"],
    "DDOS_AMPLIFICATION": [r"(amplification|reflection|ntp|dns.*flood)"],
}

SEVERITY_MAP = {
    "SQL_INJECTION": "HIGH",
    "XSS_ATTEMPT": "MEDIUM",
    "DIRECTORY_TRAVERSAL": "MEDIUM",
    "BRUTE_FORCE": "HIGH",
    "MALWARE_UPLOAD": "CRITICAL",
    "PORT_SCAN": "MEDIUM",
    "CREDENTIAL_STUFFING": "HIGH",
    "DOS_ATTACK": "CRITICAL",
    "UNAUTHORIZED_ACCESS": "HIGH",
    "DDOS_AMPLIFICATION": "CRITICAL"
}

# ════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ════════════════════════════════════════════════════════════════
def parse_log_line(line):
    """Parse Apache or fail2ban log line"""
    apache = r'(\S+) \S+ \S+ \[([^\]]+)\] "([^"]*)" (\d+) (\S+)'
    fail2ban = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*\[(.*?)\].*(Ban|Found) (\S+)'
    
    m = re.match(apache, line)
    if m:
        return {
            "ip": m.group(1),
            "timestamp": m.group(2),
            "request": m.group(3),
            "status": m.group(4),
            "type": "apache"
        }
    
    m2 = re.match(fail2ban, line)
    if m2:
        return {
            "ip": m2.group(4),
            "timestamp": m2.group(1),
            "request": f"[{m2.group(2)}] {m2.group(3)}",
            "status": "BAN",
            "type": "fail2ban"
        }
    
    return None

def detect_attack(req):
    """Detect attack type from request string"""
    req_l = req.lower()
    for atype, patterns in ATTACK_PATTERNS.items():
        for p in patterns:
            if re.search(p, req_l, re.IGNORECASE):
                return atype
    return None

def generate_demo_events(count=60):
    """Generate realistic synthetic attack events for demonstration"""
    atypes = list(ATTACK_PATTERNS.keys())
    ips = [f"{random.randint(1, 254)}.{random.randint(1, 254)}.{random.randint(1, 254)}.{random.randint(1, 254)}"
           for _ in range(12)]
    return [
        {
            "ip": random.choice(ips),
            "attack_type": random.choice(atypes),
            "timestamp": datetime.datetime.now().isoformat(),
            "source": "demo"
        }
        for _ in range(count)
    ]

# ════════════════════════════════════════════════════════════════
# MODULE 4 — SIEM LOG ANALYSIS & THREAT DETECTION
# ════════════════════════════════════════════════════════════════
def module_siem(target=None, silent=False):
    """
    SIEM Log Analysis & Threat Detection module
    
    Performs:
    - Generates realistic attack events (60 synthetic events)
    - Parses real Apache, Nginx, fail2ban logs
    - Detects SQL injection, XSS, directory traversal, brute force, etc.
    - Identifies top attacking IP addresses
    - Categorizes attack distribution by type
    - Calculates severity distribution
    """
    if not silent:
        console.print("[bold cyan]MODULE 4 — SIEM Log Analysis & Threat Detection[/bold cyan]")
    
    console.print("\n[bold]Select log source:[/bold]")
    console.print("  [cyan]1.[/cyan] Generate realistic demo events (60)")
    console.print("  [cyan]2.[/cyan] Import real log file (Apache, fail2ban, Nginx)")
    choice = console.input("\n[dim]Choice [1/2] (1): [/dim]").strip() or "1"
    events = []

    if choice == "2":
        log_path = console.input("[dim]Log file path: [/dim]").strip()
        if not log_path or not Path(log_path).exists():
            console.print("[yellow][ ! ][/yellow] File not found — using demo events")
            events = generate_demo_events(60)
        else:
            console.print(f"\n[cyan][ * ][/cyan] Parsing {log_path}...")
            parsed = 0
            with open(log_path, "r", errors="ignore") as f:
                for line in f:
                    pl = parse_log_line(line.strip())
                    if pl:
                        at = detect_attack(pl.get("request", ""))
                        if at:
                            events.append({
                                "ip": pl["ip"],
                                "attack_type": at,
                                "timestamp": pl["timestamp"],
                                "request": pl.get("request", ""),
                                "source": "real_log"
                            })
                        parsed += 1
            console.print(f"[green][ ✓ ][/green] Parsed {parsed} lines → {len(events)} attack events")
            if not events:
                console.print("[yellow][ ! ][/yellow] No attacks found — using demo events")
                events = generate_demo_events(60)
    else:
        console.print(f"\n[cyan][ * ][/cyan] Generating 60 realistic SIEM events...")
        with Progress(SpinnerColumn(), BarColumn(), TextColumn("{task.percentage:>3.0f}%"), console=console) as prog:
            task = prog.add_task("Processing...", total=60)
            events = generate_demo_events(60)
            for _ in events:
                prog.advance(task)
                time.sleep(0.02)

    console.print("\n[green][ ✓ ][/green] [bold]SIEM Analysis Results:[/bold]\n")

    # Top attacking IP addresses
    ip_counts = {}
    for e in events:
        ip_counts[e["ip"]] = ip_counts.get(e["ip"], 0) + 1
    top_ips = sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)[:8]

    it = Table(title="Top Attacking IP Addresses", box=box.ROUNDED, border_style="red")
    it.add_column("Source IP", style="yellow")
    it.add_column("Attack Count", width=14)
    it.add_column("Risk Level", width=12)
    for ip, cnt in top_ips:
        it.add_row(ip, str(cnt), "[red]HIGH[/red]")
    console.print(it)

    # Attack distribution
    ac = {}
    for e in events:
        ac[e["attack_type"]] = ac.get(e["attack_type"], 0) + 1
    
    at_table = Table(title="Attack Types Distribution", box=box.ROUNDED, border_style="yellow")
    at_table.add_column("Attack Type", style="yellow")
    at_table.add_column("Count", width=8)
    at_table.add_column("Severity", width=12)
    for atype, cnt in sorted(ac.items(), key=lambda x: x[1], reverse=True):
        sev = SEVERITY_MAP.get(atype, "MEDIUM")
        sc = sev_color(sev)
        at_table.add_row(atype, str(cnt), f"[{sc}]{sev}[/{sc}]")
    console.print(at_table)

    # Severity distribution
    crit = sum(1 for e in events if SEVERITY_MAP.get(e["attack_type"]) == "CRITICAL")
    high = sum(1 for e in events if SEVERITY_MAP.get(e["attack_type"]) == "HIGH")
    med = sum(1 for e in events if SEVERITY_MAP.get(e["attack_type"]) == "MEDIUM")
    
    console.print(f"\n[bold]Severity Distribution:[/bold]")
    console.print(f"  [bold red]CRITICAL: {crit}[/bold red]")
    console.print(f"  [red]HIGH:     {high}[/red]")
    console.print(f"  [yellow]MEDIUM:   {med}[/yellow]")
    console.print(f"  [bold]Total Events: {len(events)}[/bold]")

    results = {
        "events": len(events),
        "top_ips": top_ips,
        "attack_counts": ac,
        "critical": crit,
        "high": high,
        "medium": med
    }
    fname = DATA_DIR / "siem" / f"siem_{ts()}.json"
    with open(fname, "w") as f:
        json.dump(results, f, indent=2, default=str)
    save_db(target or "siem", "siem", results)
    
    console.print(f"\n[green][ ✓ ][/green] {len(events)} events processed and saved.")
    if not silent:
        console.input("\n[dim]Press Enter to return to main menu...[/dim]")
    
    return results
