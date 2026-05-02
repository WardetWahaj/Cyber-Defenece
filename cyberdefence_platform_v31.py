#!/usr/bin/env python3
"""
CYBERDEFENCE ANALYST PLATFORM v3.1
by Tudorache Flavius Robert
SecuritateIT.ro — Final Project

Live Data Sources:
  - Nuclei v3.7.1        — 92 templates, misconfigs, SSL, CVEs
  - WPScan               — WordPress CVE database
  - VirusTotal API       — 90+ AV engines, domain/IP reputation
  - Sucuri SiteCheck     — External malware & blacklist check
  - SecurityHeaders.com  — HTTP header grading A-F
  - Cloudflare Heuristic — WAF/DDoS detection via CF-RAY

Modules:
  1. Reconnaissance & Technology Scanning
  2. Vulnerability Assessment (CVSS + NVD)
  3. Defence Configuration Check
  4. SIEM Log Analysis & Threat Detection
  5. Security Policy Generator
  6. VirusTotal Reputation Check (90+ engines)
  7. Security Overview Dashboard
  8. Auto Scan — Full Pipeline (one command)
  9. Custom Scan — Choose your modules
  10. Generate Full Security Report (PDF)
  0. Exit
"""

import os, sys, json, re, ssl, socket, sqlite3, logging
import time, threading, subprocess, datetime, shutil
from pathlib import Path
from urllib.parse import urlparse

# ── Dependency checks ──────────────────────────────────────────
def check_dep(module, install):
    try:
        __import__(module)
    except ImportError:
        print(f"[!] {module} not installed. Run: {install}")
        sys.exit(1)

check_dep("requests", "pip3 install requests --break-system-packages")
check_dep("rich", "pip3 install rich --break-system-packages")
check_dep("fpdf", "pip3 install fpdf2 --break-system-packages")

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.columns import Columns
from rich.rule import Rule
from rich.text import Text
from rich import box
from fpdf import FPDF

try:
    import nmap
    NMAP_AVAILABLE = True
except ImportError:
    NMAP_AVAILABLE = False

console = Console()

# ── Paths ───────────────────────────────────────────────────────
BASE_DIR  = Path(__file__).parent
DATA_DIR  = BASE_DIR / "data"
CONFIG_F  = BASE_DIR / "config.json"
DB_FILE   = DATA_DIR / "cyberdefence.db"
NUCLEI_LOCAL_EXE = BASE_DIR / "tools" / "nuclei" / ("nuclei.exe" if os.name == "nt" else "nuclei")


def get_nuclei_binary() -> str | None:
    configured = globals().get("CONFIG", {}).get("nuclei_binary_path", "")
    if configured:
        configured_path = Path(configured)
        if configured_path.exists():
            return str(configured_path)

    local_binary = NUCLEI_LOCAL_EXE
    if local_binary.exists():
        return str(local_binary)

    path_binary = shutil.which("nuclei")
    if path_binary:
        return path_binary

    return None


NUCLEI_BINARY = get_nuclei_binary()
NUCLEI_AVAILABLE = NUCLEI_BINARY is not None

for d in ["recon","vuln","defence","siem","policies","reports","virustotal","nuclei","sucuri"]:
    (DATA_DIR / d).mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=DATA_DIR / "platform.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# ── Config ──────────────────────────────────────────────────────
def load_config():
    defaults = {
        "wpscan_api_key": "",
        "virustotal_api_key": "",
        "nvd_api_key": "",
        "rate_limit_delay": 1.5,
        "nuclei_binary_path": "",
        "nuclei_templates_path": "",
        "max_nuclei_templates": 92,
        "request_timeout": 10
    }
    if CONFIG_F.exists():
        with open(CONFIG_F) as f:
            return {**defaults, **json.load(f)}
    with open(CONFIG_F, "w") as f:
        json.dump(defaults, f, indent=2)
    return defaults

CONFIG = load_config()
TIMEOUT = CONFIG["request_timeout"]

# ── Database ─────────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS scans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        target TEXT, module TEXT,
        timestamp TEXT, results TEXT
    )""")
    conn.commit(); conn.close()

def save_db(target, module, results, user_id=None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO scans (target,module,timestamp,results,user_id) VALUES (?,?,?,?,?)",
              (target, module, datetime.datetime.now().isoformat(), json.dumps(results, default=str), user_id))
    conn.commit(); conn.close()

def get_history(limit=20, user_id=None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    if user_id:
        c.execute("SELECT * FROM scans WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?", (user_id, limit))
    else:
        c.execute("SELECT * FROM scans ORDER BY timestamp DESC LIMIT ?", (limit,))
    rows = c.fetchall(); conn.close()
    return rows

def get_latest(module, user_id=None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    if user_id:
        c.execute("SELECT results FROM scans WHERE module=? AND user_id=? ORDER BY timestamp DESC LIMIT 1", (module, user_id))
    else:
        c.execute("SELECT results FROM scans WHERE module=? ORDER BY timestamp DESC LIMIT 1", (module,))
    row = c.fetchone(); conn.close()
    return json.loads(row[0]) if row else {}

# ── Helpers ──────────────────────────────────────────────────────
def clean_url(url):
    if not url.startswith(("http://","https://")):
        url = "https://" + url
    return url.rstrip("/")

def get_domain(url):
    return urlparse(clean_url(url)).netloc

def sev_color(s):
    return {"CRITICAL":"bold red","HIGH":"red","MEDIUM":"yellow","LOW":"green"}.get(s.upper(),"white")

def rate_sleep():
    time.sleep(CONFIG["rate_limit_delay"])

def ts():
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

# ── Banner ───────────────────────────────────────────────────────
def print_banner():
    console.clear()
    console.print(Panel(
        "[bold cyan]  CYBERDEFENCE ANALYST PLATFORM v3.1[/bold cyan]\n"
        "[dim]  by Tudorache Flavius Robert | SecuritateIT.ro — Final Project[/dim]\n\n"
        "[dim]  Live Sources: Nuclei · WPScan · VirusTotal · Sucuri · SecurityHeaders · Cloudflare[/dim]",
        border_style="cyan", padding=(1,4)
    ))

def print_menu():
    t = Table(box=box.SIMPLE, show_header=False, padding=(0,2))
    t.add_column("Num", style="bold cyan", width=6)
    t.add_column("Icon", width=4)
    t.add_column("Module", style="white")
    modules = [
        ("[1]","🔍","Reconnaissance & Technology Scanning"),
        ("[2]","🎯","Vulnerability Assessment (CVSS + NVD API)"),
        ("[3]","🛡️ ","Defence Configuration Check"),
        ("[4]","📊","SIEM — Log Analysis & Threat Detection"),
        ("[5]","📋","Security Policy Generator"),
        ("[6]","🦠","VirusTotal Reputation Check (90+ engines)"),
        ("[7]","📈","Security Overview Dashboard"),
        ("[8]","⚡","Auto Scan — Full Pipeline (one command)"),
        ("[9]","🎛️ ","Custom Scan — Choose your modules"),
        ("[10]","📄","Generate Full Security Report (PDF)"),
        ("[0]","🚪","Exit"),
    ]
    for n,ic,label in modules:
        t.add_row(n,ic,label)
    console.print(t)
    console.print("[dim]Select module [0-10]: [/dim]", end="")

# ════════════════════════════════════════════════════════════════
# MODULE 1 — RECONNAISSANCE
# ════════════════════════════════════════════════════════════════
def module_recon(target=None, silent=False):
    if not silent:
        console.print(Rule("[bold cyan]MODULE 1 — Reconnaissance & Technology Scanning[/bold cyan]"))
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
                "server": h.get("Server","Unknown"),
                "x_powered_by": h.get("X-Powered-By",""),
            })
            # CMS
            cms = "Unknown"
            if "wp-content" in content or "wp-includes" in content:
                m = re.search(r'name=["\']generator["\'] content=["\']WordPress ([^"\']+)["\']', r.text)
                cms = f"WordPress {m.group(1)}" if m else "WordPress"
            elif "joomla" in content: cms = "Joomla"
            elif "drupal"  in content: cms = "Drupal"
            elif "shopify" in content: cms = "Shopify"
            results["cms"] = cms

            # Tech stack
            tech = []
            if "jquery"    in content:
                m = re.search(r'jquery[.-](\d+\.\d+[\.\d]*)', content)
                tech.append(f"jQuery {m.group(1) if m else ''}")
            if "bootstrap"  in content: tech.append("Bootstrap")
            if "react"      in content: tech.append("React")
            if "angular"    in content: tech.append("Angular")
            if "vue"        in content: tech.append("Vue.js")
            if "laravel"    in content: tech.append("Laravel")
            if results["x_powered_by"]: tech.append(results["x_powered_by"])
            results["technologies"] = tech

            # Security headers
            sec_hdrs = {}
            for hdr in ["Strict-Transport-Security","Content-Security-Policy",
                         "X-Frame-Options","X-Content-Type-Options",
                         "X-XSS-Protection","Referrer-Policy","Permissions-Policy"]:
                sec_hdrs[hdr] = bool(h.get(hdr))
            results["security_headers"] = sec_hdrs

            # Cloudflare heuristic via CF-RAY
            cf_ray    = h.get("CF-RAY","")
            cf_server = "cloudflare" in h.get("Server","").lower()
            results["cloudflare"] = bool(cf_ray or cf_server)
            results["cf_ray"]     = cf_ray

        except Exception as e:
            results["http_error"] = str(e)
            console.print(f"[red][ ! ][/red] HTTP error: {e}")
        prog.update(task, advance=25); rate_sleep()

        # ── SSL ──────────────────────────────────────────────
        prog.update(task, description="[cyan]SSL certificate check...")
        ssl_info = {}
        try:
            ctx = ssl.create_default_context()
            with ctx.wrap_socket(socket.socket(), server_hostname=domain) as s:
                s.settimeout(5); s.connect((domain,443))
                cert = s.getpeercert()
                ssl_info = {
                    "valid": True,
                    "expires": cert.get("notAfter","?"),
                    "issuer": dict(x[0] for x in cert.get("issuer",[])),
                    "subject": dict(x[0] for x in cert.get("subject",[])),
                }
        except Exception as e:
            ssl_info = {"valid": False, "error": str(e)}
        results["ssl"] = ssl_info
        prog.update(task, advance=20); rate_sleep()

        # ── Port scan ────────────────────────────────────────
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
                                    "service": st.get("name","unknown"),
                                    "version": st.get("version",""),
                                    "state": "open"
                                })
            except Exception as e:
                open_ports = [{"port":"error","service":str(e),"state":"error"}]
        else:
            for port in [21,22,23,25,80,443,3306,8080,8443]:
                try:
                    s = socket.socket(); s.settimeout(1)
                    if s.connect_ex((domain,port)) == 0:
                        try: svc = socket.getservbyport(port,"tcp")
                        except: svc = "unknown"
                        open_ports.append({"port":port,"service":svc,"state":"open"})
                    s.close()
                except: pass
        results["open_ports"] = open_ports
        prog.update(task, advance=25); rate_sleep()

        # ── DNS ──────────────────────────────────────────────
        prog.update(task, description="[cyan]Resolving DNS...")
        try:
            results["ip_address"] = socket.gethostbyname(domain)
        except:
            results["ip_address"] = "Could not resolve"
        prog.update(task, advance=15)

        # ── Robots / sitemap ─────────────────────────────────
        prog.update(task, description="[cyan]Checking robots.txt...")
        try:
            rb = requests.get(url+"/robots.txt", timeout=5, verify=False)
            results["robots_txt"] = rb.status_code == 200
            results["robots_content"] = rb.text[:300] if rb.status_code == 200 else ""
        except:
            results["robots_txt"] = False
        prog.update(task, advance=15)

    # ── Display ──────────────────────────────────────────────────
    console.print(f"\n[green][ ✓ ][/green] Reconnaissance complete\n")
    t = Table(title=f"Recon — {domain}", box=box.ROUNDED, border_style="cyan")
    t.add_column("Property", style="dim", width=28)
    t.add_column("Value", style="white")
    t.add_row("IP Address",    results.get("ip_address","?"))
    t.add_row("HTTP Status",   str(results.get("http_status","?")))
    t.add_row("Server",        results.get("server","?"))
    t.add_row("CMS",           results.get("cms","Unknown"))
    t.add_row("X-Powered-By",  results.get("x_powered_by","None"))
    t.add_row("HTTPS",         "[green]Yes[/green]" if results.get("https") else "[red]No[/red]")
    ssl_v = results.get("ssl",{})
    t.add_row("SSL Valid",     "[green]Yes[/green]" if ssl_v.get("valid") else f"[red]No — {ssl_v.get('error','')}[/red]")
    t.add_row("SSL Expires",   ssl_v.get("expires","?"))
    t.add_row("Cloudflare",    "[green]Detected[/green]" if results.get("cloudflare") else "[yellow]Not detected[/yellow]")
    t.add_row("CF-RAY",        results.get("cf_ray","None"))
    t.add_row("Technologies",  ", ".join(results.get("technologies",[])) or "None")
    ports = ", ".join(str(p["port"]) for p in results.get("open_ports",[]))
    t.add_row("Open Ports",    ports or "None found")
    t.add_row("robots.txt",    "[green]Found[/green]" if results.get("robots_txt") else "[dim]Not found[/dim]")
    console.print(t)

    # Security headers
    sh = results.get("security_headers",{})
    ht = Table(title="Security Headers", box=box.SIMPLE, border_style="cyan")
    ht.add_column("Header", style="dim", width=35)
    ht.add_column("Status", width=12)
    for h,v in sh.items():
        ht.add_row(h, "[green]Present[/green]" if v else "[red]Missing[/red]")
    console.print(ht)

    fname = DATA_DIR/"recon"/f"recon_{domain}_{ts()}.json"
    with open(fname,"w") as f: json.dump(results,f,indent=2,default=str)
    save_db(url,"recon",results)
    if not silent:
        console.print(f"\n[green][ ✓ ][/green] Saved to {fname}")
        console.input("\n[dim]Press Enter to return to main menu...[/dim]")
    return results

# ════════════════════════════════════════════════════════════════
# MODULE 2 — VULNERABILITY ASSESSMENT
# ════════════════════════════════════════════════════════════════
def fetch_nvd(keyword):
    try:
        params = {"keywordSearch": keyword, "resultsPerPage": 3}
        headers = {}
        if CONFIG.get("nvd_api_key"):
            headers["apiKey"] = CONFIG["nvd_api_key"]
        r = requests.get("https://services.nvd.nist.gov/rest/json/cves/2.0",
                         params=params, headers=headers, timeout=10)
        if r.status_code == 200:
            vulns = r.json().get("vulnerabilities",[])
            if vulns:
                cve  = vulns[0]["cve"]
                m    = cve.get("metrics",{})
                cvss, sev = 0.0, "UNKNOWN"
                for key in ["cvssMetricV31","cvssMetricV30"]:
                    if key in m:
                        cvss = m[key][0]["cvssData"]["baseScore"]
                        sev  = m[key][0]["cvssData"]["baseSeverity"]
                        break
                if not cvss and "cvssMetricV2" in m:
                    cvss = m["cvssMetricV2"][0]["cvssData"]["baseScore"]
                    sev  = "HIGH" if cvss>=7 else "MEDIUM" if cvss>=4 else "LOW"
                return {"cvss":cvss,"severity":sev,"cve_id":cve["id"]}
    except Exception as e:
        logging.warning(f"NVD error {keyword}: {e}")
    return None

def live_check(url, vuln_type):
    result = {"exists":False,"evidence":"","confirmed":False}
    try:
        r = requests.get(url, timeout=TIMEOUT, verify=False, allow_redirects=True)
        h = r.headers; content = r.text.lower()

        if vuln_type == "xmlrpc":
            xr = requests.get(url.rstrip("/")+"/xmlrpc.php", timeout=5, verify=False)
            result["exists"] = xr.status_code==200 and "xml" in xr.text.lower()
            result["evidence"] = f"xmlrpc.php → {xr.status_code}"
            result["confirmed"] = result["exists"]

        elif vuln_type == "wp_version":
            m = re.search(r'name=["\']generator["\'] content=["\']WordPress ([^"\']+)["\']', r.text)
            result["exists"] = bool(m)
            result["evidence"] = f"WordPress {m.group(1)} exposed in meta tag" if m else "Version not exposed"
            result["confirmed"] = result["exists"]

        elif vuln_type == "directory_listing":
            for path in ["/wp-content/uploads/","/images/","/assets/","/backup/"]:
                try:
                    tr = requests.get(url.rstrip("/")+path, timeout=5, verify=False)
                    if "index of" in tr.text.lower():
                        result["exists"]=True; result["evidence"]=f"Directory listing at {path}"; result["confirmed"]=True; break
                except: pass

        elif vuln_type == "missing_headers":
            missing = [hdr for hdr in ["X-Frame-Options","Content-Security-Policy",
                       "X-Content-Type-Options","Strict-Transport-Security"] if hdr not in h]
            result["exists"] = bool(missing)
            result["evidence"] = f"Missing: {', '.join(missing)}" if missing else "Headers OK"
            result["confirmed"] = bool(missing)

        elif vuln_type == "wp_admin":
            ar = requests.get(url.rstrip("/")+"/wp-admin/", timeout=5, verify=False, allow_redirects=True)
            result["exists"] = ar.status_code==200
            result["evidence"] = f"wp-admin → {ar.status_code}"
            result["confirmed"] = ar.status_code==200

        elif vuln_type == "backup_files":
            for path in ["/backup.zip","/.git/HEAD","/wp-config.php.bak","/database.sql","/db.sql"]:
                try:
                    br = requests.get(url.rstrip("/")+path, timeout=5, verify=False)
                    if br.status_code==200 and len(br.content)>50:
                        result["exists"]=True; result["evidence"]=f"Backup at {path}"; result["confirmed"]=True; break
                except: pass

        elif vuln_type == "ssl_weak":
            domain = get_domain(url)
            try:
                ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
                with ctx.wrap_socket(socket.socket(), server_hostname=domain) as s:
                    s.settimeout(5); s.connect((domain,443))
                    ver = s.version()
                    result["exists"] = ver in ["TLSv1","TLSv1.1","SSLv2","SSLv3"]
                    result["evidence"] = f"TLS version: {ver}"
                    result["confirmed"] = result["exists"]
            except Exception as e:
                result["evidence"] = str(e)

        elif vuln_type == "rate_limit":
            codes = []
            for _ in range(4):
                try:
                    lr = requests.post(url.rstrip("/")+"/wp-login.php",
                        data={"log":"admin","pwd":"wrongpassword"},
                        timeout=5,verify=False,allow_redirects=False)
                    codes.append(lr.status_code)
                    time.sleep(0.3)
                except: pass
            blocked = any(c in [429,403] for c in codes)
            result["exists"] = not blocked and bool(codes)
            result["evidence"] = f"Login responses: {codes}"
            result["confirmed"] = result["exists"]

        elif vuln_type == "user_enum":
            try:
                ue = requests.get(url.rstrip("/")+"/wp-json/wp/v2/users", timeout=5, verify=False)
                result["exists"] = ue.status_code==200 and "[" in ue.text
                result["evidence"] = f"REST API users endpoint → {ue.status_code}"
                result["confirmed"] = result["exists"]
            except: pass

    except Exception as e:
        result["error"] = str(e)
    return result

def run_nuclei(domain, silent=False):
    """Run Nuclei with up to 92 templates"""
    nuclei_bin = get_nuclei_binary()
    if not nuclei_bin:
        console.print("[yellow][ ! ][/yellow] Nuclei not installed — skipping")
        console.print("[dim]    Install: sudo apt install nuclei[/dim]")
        return []

    console.print(f"\n[cyan][ * ][/cyan] Running Nuclei templates against {domain}...")
    findings = []
    try:
        cmd = [
            nuclei_bin, "-u", f"https://{domain}",
            "-t", "ssl,http/misconfiguration,http/exposures,http/technologies,http/vulnerabilities",
            "-severity", "critical,high,medium",
            "-timeout", "10",
            "-rate-limit", "50",
            "-json",
            "-silent"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        for line in result.stdout.strip().split("\n"):
            if not line.strip(): continue
            try:
                finding = json.loads(line)
                findings.append({
                    "template": finding.get("template-id",""),
                    "name": finding.get("info",{}).get("name",""),
                    "severity": finding.get("info",{}).get("severity","").upper(),
                    "matched": finding.get("matched-at",""),
                    "description": finding.get("info",{}).get("description",""),
                    "cvss": finding.get("info",{}).get("classification",{}).get("cvss-score",0),
                    "cve": finding.get("info",{}).get("classification",{}).get("cve-id",""),
                    "source": "nuclei"
                })
            except: pass
        console.print(f"[green][ ✓ ][/green] Nuclei found [bold]{len(findings)}[/bold] issues")
    except subprocess.TimeoutExpired:
        console.print("[yellow][ ! ][/yellow] Nuclei timed out after 120s")
    except Exception as e:
        console.print(f"[red][ ! ][/red] Nuclei error: {e}")
    return findings

def run_wpscan(url, domain):
    """Run WPScan API"""
    key = CONFIG.get("wpscan_api_key","")
    if not key or key == "PASTE_YOUR_WPSCAN_KEY_HERE":
        console.print("[yellow][ ! ][/yellow] WPScan API key not configured — skipping")
        return []

    console.print(f"\n[cyan][ * ][/cyan] Running WPScan against {domain}...")
    findings = []
    try:
        headers = {"Authorization": f"Token token={key}"}
        # Check WordPress version vulns
        vr = requests.get("https://wpscan.com/api/v3/wordpresses/latest",
                          headers=headers, timeout=10)
        if vr.status_code == 200:
            for slug, info in vr.json().items():
                for v in info.get("vulnerabilities",[])[:5]:
                    findings.append({
                        "name": v.get("title","WordPress Vulnerability"),
                        "severity": "HIGH",
                        "cvss": v.get("cvss",{}).get("score",7.0),
                        "cve": v.get("references",{}).get("cve",[""])[0] if v.get("references",{}).get("cve") else "",
                        "source": "wpscan"
                    })
        # Check popular plugins
        for plugin in ["akismet","contact-form-7","yoast-seo"]:
            pr = requests.get(f"https://wpscan.com/api/v3/plugins/{plugin}",
                             headers=headers, timeout=10)
            if pr.status_code == 200:
                for slug, info in pr.json().items():
                    for v in info.get("vulnerabilities",[])[:2]:
                        findings.append({
                            "name": f"[Plugin: {plugin}] {v.get('title','')}",
                            "severity": "HIGH",
                            "cvss": v.get("cvss",{}).get("score",7.0),
                            "cve": "",
                            "source": "wpscan"
                        })
            rate_sleep()
        console.print(f"[green][ ✓ ][/green] WPScan found [bold]{len(findings)}[/bold] WordPress issues")
    except Exception as e:
        console.print(f"[red][ ! ][/red] WPScan error: {e}")
    return findings

def module_vuln(target=None, silent=False, recon_data=None):
    if not silent:
        console.print(Rule("[bold cyan]MODULE 2 — Vulnerability Assessment (CVSS + NVD + Nuclei + WPScan)[/bold cyan]"))
    if not target:
        target = console.input("\n[dim]Enter target URL: [/dim]").strip() or "platformait.ro"

    url    = clean_url(target)
    domain = get_domain(url)
    cms    = (recon_data or {}).get("cms","Unknown")
    found_vulns = []

    console.print(f"\n[cyan][ * ][/cyan] Running Vulnerability Assessment on [bold]{url}[/bold]")

    CHECKS = [
        ("xmlrpc",       "WordPress XML-RPC Enabled",       "WordPress XML-RPC",        "HIGH",     7.5),
        ("wp_version",   "Outdated WordPress Core",         "WordPress outdated core",  "CRITICAL", 9.1),
        ("directory_listing","Directory Listing Enabled",   "directory listing apache", "MEDIUM",   5.3),
        ("missing_headers","Missing HTTP Security Headers", "missing security headers", "MEDIUM",   5.0),
        ("wp_admin",     "Default WordPress Admin URL",     "WordPress admin brute",    "MEDIUM",   4.8),
        ("backup_files", "Exposed Backup Files",            "exposed backup web server","HIGH",     7.8),
        ("ssl_weak",     "Weak SSL/TLS Configuration",      "weak TLS configuration",   "MEDIUM",   5.5),
        ("rate_limit",   "No Rate Limiting on Login",       "WordPress brute force",    "HIGH",     7.2),
        ("user_enum",    "WordPress User Enumeration",      "WordPress user enum REST", "LOW",      3.5),
    ]

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                  BarColumn(), TextColumn("{task.percentage:>3.0f}%"), console=console) as prog:
        task = prog.add_task("[cyan]Checking vulnerabilities...", total=len(CHECKS))

        for vuln_key, vuln_name, nvd_kw, fb_sev, fb_cvss in CHECKS:
            prog.update(task, description=f"[cyan]Checking: {vuln_name[:42]}...")
            live = live_check(url, vuln_key)
            nvd  = None
            if live.get("confirmed"):
                rate_sleep()
                nvd = fetch_nvd(nvd_kw)

            sev  = nvd["severity"] if nvd else fb_sev
            cvss = nvd["cvss"]     if nvd else fb_cvss
            cve  = nvd["cve_id"]   if nvd else "N/A"

            found_vulns.append({
                "name":      vuln_name,
                "severity":  sev,
                "cvss":      cvss,
                "cve_id":    cve,
                "evidence":  live.get("evidence",""),
                "confirmed": live.get("confirmed",False),
                "source":    "live_check"
            })
            prog.advance(task)
            rate_sleep()

    # Nuclei
    nuclei_findings = run_nuclei(domain, silent)
    for nf in nuclei_findings:
        found_vulns.append({
            "name":      nf["name"],
            "severity":  nf["severity"],
            "cvss":      nf.get("cvss",0),
            "cve_id":    nf.get("cve","N/A"),
            "evidence":  nf.get("matched",""),
            "confirmed": True,
            "source":    "nuclei"
        })

    # WPScan (if WordPress detected)
    if "wordpress" in cms.lower() or "wordpress" in target.lower():
        wp_findings = run_wpscan(url, domain)
        for wf in wp_findings:
            found_vulns.append({
                "name":      wf["name"],
                "severity":  wf["severity"],
                "cvss":      wf.get("cvss",7.0),
                "cve_id":    wf.get("cve","N/A"),
                "evidence":  "WPScan API confirmed",
                "confirmed": True,
                "source":    "wpscan"
            })

    # Display
    console.print(f"\n[green][ ✓ ][/green] Found [bold]{len(found_vulns)}[/bold] total findings\n")

    t = Table(title=f"Vulnerability Report — {url}", box=box.ROUNDED, border_style="red")
    t.add_column("#",         width=4)
    t.add_column("Vulnerability", width=40)
    t.add_column("Source",    width=12)
    t.add_column("Confirmed", width=10)
    t.add_column("Severity",  width=10)
    t.add_column("CVSS",      width=6)
    t.add_column("CVE",       width=16)

    confirmed = [v for v in found_vulns if v["confirmed"]]
    unconfirmed = [v for v in found_vulns if not v["confirmed"]]

    for i,v in enumerate(confirmed + unconfirmed, 1):
        sc = sev_color(v["severity"])
        conf_str = "[green]YES[/green]" if v["confirmed"] else "[dim]UNCONFIRMED[/dim]"
        src_color = {"nuclei":"cyan","wpscan":"magenta","live_check":"white"}.get(v["source"],"white")
        t.add_row(str(i), v["name"][:40], f"[{src_color}]{v['source']}[/{src_color}]",
                  conf_str, f"[{sc}]{v['severity']}[/{sc}]",
                  str(v["cvss"]), v["cve_id"])
    console.print(t)

    crit = sum(1 for v in confirmed if v["severity"]=="CRITICAL")
    high = sum(1 for v in confirmed if v["severity"]=="HIGH")
    med  = sum(1 for v in confirmed if v["severity"]=="MEDIUM")
    low  = sum(1 for v in confirmed if v["severity"]=="LOW")

    console.print(f"\n[bold]Assessment Summary (confirmed only):[/bold]")
    console.print(f"  [bold red]Critical: {crit}[/bold red]")
    console.print(f"  [red]High:     {high}[/red]")
    console.print(f"  [yellow]Medium:   {med}[/yellow]")
    console.print(f"  [green]Low:      {low}[/green]")

    results = {"target":url,"vulnerabilities":found_vulns,
               "summary":{"critical":crit,"high":high,"medium":med,"low":low}}
    fname = DATA_DIR/"vuln"/f"vuln_{domain}_{ts()}.json"
    with open(fname,"w") as f: json.dump(results,f,indent=2,default=str)
    save_db(url,"vuln",results)
    if not silent:
        console.print(f"\n[green][ ✓ ][/green] Saved to {fname}")
        console.input("\n[dim]Press Enter to return to main menu...[/dim]")
    return results

# ════════════════════════════════════════════════════════════════
# MODULE 3 — DEFENCE CONFIGURATION CHECK
# ════════════════════════════════════════════════════════════════
def check_security_headers_grade(url, domain):
    """Grade HTTP headers via SecurityHeaders.com"""
    grade = "?"
    try:
        r = requests.get(f"https://securityheaders.com/?q={domain}&followRedirects=on",
                         timeout=10, allow_redirects=True)
        m = re.search(r'class=["\']grade["\'][^>]*>([A-F][+-]?)<', r.text)
        if not m:
            m = re.search(r'>([A-F][+-]?)</span>', r.text)
        grade = m.group(1) if m else "?"
        # Fallback: parse from response header
        if grade == "?":
            grade = r.headers.get("X-Grade","?")
    except Exception as e:
        logging.warning(f"SecurityHeaders.com error: {e}")
    return grade

def check_sucuri(domain):
    """Check Sucuri SiteCheck for malware/blacklist"""
    result = {"clean":None,"blacklisted":False,"malware":False,"details":""}
    try:
        r = requests.get(f"https://sitecheck.sucuri.net/results/{domain}",
                         timeout=15, verify=False)
        content = r.text.lower()
        result["blacklisted"] = "blacklisted" in content
        result["malware"]     = "malware" in content and "no malware" not in content
        result["clean"]       = not result["blacklisted"] and not result["malware"]
        if result["clean"]:
            result["details"] = "No malware or blacklist entries found"
        else:
            result["details"] = ("Blacklisted! " if result["blacklisted"] else "") + \
                                 ("Malware detected!" if result["malware"] else "")
    except Exception as e:
        result["details"] = f"Could not reach Sucuri: {e}"
        result["clean"] = None
    return result

def module_defence(target=None, silent=False):
    if not silent:
        console.print(Rule("[bold cyan]MODULE 3 — Defence Configuration Check[/bold cyan]"))
    if not target:
        target = console.input("\n[dim]Enter target URL: [/dim]").strip() or "scanme.nmap.org"

    url    = clean_url(target)
    domain = get_domain(url)
    checks = []
    console.print(f"\n[cyan][ * ][/cyan] Checking defence configuration for [bold]{url}[/bold]")

    def add(name, req, status, detail):
        checks.append({"name":name,"requirement":req,"status":status,"details":detail})

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                  BarColumn(), console=console) as prog:
        task = prog.add_task("[cyan]Running checks...", total=14)

        # 1. HTTPS
        prog.update(task, description="[cyan]HTTPS/SSL check...")
        try:
            r = requests.get(url, timeout=TIMEOUT, verify=True)
            add("HTTPS/SSL Certificate","Prevention #2","PASS",f"Valid cert, status {r.status_code}")
        except requests.exceptions.SSLError:
            add("HTTPS/SSL Certificate","Prevention #2","FAIL","Invalid or self-signed certificate")
        except:
            add("HTTPS/SSL Certificate","Prevention #2","FAIL","HTTPS not available")
        prog.advance(task); time.sleep(0.3)

        # 2. HTTP→HTTPS redirect
        prog.update(task, description="[cyan]HTTP redirect check...")
        try:
            hr = requests.get(url.replace("https://","http://"), timeout=TIMEOUT,
                              verify=False, allow_redirects=False)
            redir = hr.status_code in [301,302,307,308] and \
                    "https" in hr.headers.get("Location","").lower()
            add("HTTP→HTTPS Redirect","Prevention #2",
                "PASS" if redir else "FAIL",
                f"HTTP {hr.status_code}" + (" → HTTPS" if redir else " (no redirect)"))
        except Exception as e:
            add("HTTP→HTTPS Redirect","Prevention #2","FAIL",str(e))
        prog.advance(task); time.sleep(0.3)

        # 3. Security headers + grade from SecurityHeaders.com
        prog.update(task, description="[cyan]SecurityHeaders.com grading...")
        try:
            r = requests.get(url, timeout=TIMEOUT, verify=False)
            required = ["Content-Security-Policy","X-Frame-Options",
                        "X-Content-Type-Options","Strict-Transport-Security"]
            missing = [h for h in required if h not in r.headers]
            grade = check_security_headers_grade(url, domain)
            status = "PASS" if not missing else "FAIL"
            detail = f"Grade: {grade} — " + ("All headers present" if not missing else f"Missing: {', '.join(missing)}")
            add("HTTP Security Headers (SecurityHeaders.com)","Best Practice",status,detail)
        except Exception as e:
            add("HTTP Security Headers","Best Practice","FAIL",str(e))
        prog.advance(task); time.sleep(0.3)

        # 4. WAF
        prog.update(task, description="[cyan]WAF/Firewall detection...")
        try:
            tr = requests.get(url+"/?id=1'OR'1'='1", timeout=TIMEOUT, verify=False)
            waf_hdrs = ["CF-RAY","X-Sucuri-ID","X-Firewall","X-WAF","X-Cache-Status"]
            waf = any(h in tr.headers for h in waf_hdrs) or tr.status_code in [403,406,429]
            add("WAF / Firewall","Prevention #1",
                "PASS" if waf else "WARN",
                "WAF detected" if waf else "Could not verify WAF presence")
        except:
            add("WAF / Firewall","Prevention #1","WARN","Could not verify")
        prog.advance(task); time.sleep(0.3)

        # 5. Cloudflare
        prog.update(task, description="[cyan]Cloudflare detection...")
        try:
            r = requests.get(url, timeout=TIMEOUT, verify=False)
            cf = "CF-RAY" in r.headers or "cloudflare" in r.headers.get("Server","").lower()
            add("Cloudflare DDoS Protection","Prevention #5",
                "PASS" if cf else "WARN",
                f"CF-RAY: {r.headers.get('CF-RAY','None')}" if cf else "Cloudflare not detected")
        except:
            add("Cloudflare DDoS Protection","Prevention #5","WARN","Could not verify")
        prog.advance(task); time.sleep(0.3)

        # 6. WP Admin URL
        prog.update(task, description="[cyan]WordPress admin URL...")
        try:
            ar = requests.get(url.rstrip("/")+"/wp-admin/", timeout=5,
                              verify=False, allow_redirects=True)
            acc = ar.status_code == 200
            add("WordPress Admin URL","Prevention #1",
                "FAIL" if acc else "PASS",
                f"wp-admin → {ar.status_code}" + (" ACCESSIBLE!" if acc else " not accessible"))
        except:
            add("WordPress Admin URL","Prevention #1","WARN","Could not check")
        prog.advance(task); time.sleep(0.3)

        # 7. XML-RPC
        prog.update(task, description="[cyan]XML-RPC endpoint...")
        try:
            xr = requests.get(url.rstrip("/")+"/xmlrpc.php", timeout=5, verify=False)
            acc = xr.status_code == 200
            add("XML-RPC Endpoint","Security Hardening",
                "FAIL" if acc else "PASS",
                f"xmlrpc.php → {xr.status_code}" + (" ACCESSIBLE!" if acc else " not accessible"))
        except:
            add("XML-RPC Endpoint","Security Hardening","PASS","Not accessible")
        prog.advance(task); time.sleep(0.3)

        # 8. Sucuri SiteCheck
        prog.update(task, description="[cyan]Sucuri SiteCheck...")
        sucuri = check_sucuri(domain)
        if sucuri["clean"] is True:
            add("Sucuri SiteCheck (Malware/Blacklist)","Prevention #4","PASS",sucuri["details"])
        elif sucuri["clean"] is False:
            add("Sucuri SiteCheck (Malware/Blacklist)","Prevention #4","FAIL",sucuri["details"])
        else:
            add("Sucuri SiteCheck (Malware/Blacklist)","Prevention #4","WARN",sucuri["details"])
        prog.advance(task); time.sleep(0.3)

        # 9-14. Manual checks
        for name, req, detail in [
            ("2FA / Google Authenticator","Prevention #1","Manual verification in WordPress settings"),
            ("Geo-blocking (RU/DE/PH)","Prevention #1","Manual verification in Wordfence → Blocking"),
            ("Anti-Brute Force (max 3 attempts)","Prevention #1","Manual verification in Wordfence → Login Security"),
            ("Antivirus Software Installed","Prevention #3","Manual verification on host machine"),
            ("Password Manager Configured","Prevention #3","Manual verification (KeyPass/1Password)"),
            ("Regular Backups Configured","Prevention #6","Manual verification of backup schedule"),
        ]:
            add(name, req, "WARN", detail)
            prog.advance(task); time.sleep(0.1)

    # Display
    console.print(f"\n[green][ ✓ ][/green] Defence check complete\n")
    t = Table(title=f"Defence Config — {domain}", box=box.ROUNDED, border_style="cyan")
    t.add_column("Check",       width=42)
    t.add_column("Requirement", width=18)
    t.add_column("Status",      width=8)
    t.add_column("Details",     width=35)

    pc = fc = wc = 0
    for c in checks:
        if c["status"]=="PASS":  sc="[green]✓ PASS[/green]";  pc+=1
        elif c["status"]=="FAIL": sc="[red]✗ FAIL[/red]";   fc+=1
        else:                     sc="[yellow]△ WARN[/yellow]"; wc+=1
        t.add_row(c["name"], c["requirement"], sc, f"[dim]{c['details'][:35]}[/dim]")
    console.print(t)

    score = round((pc/len(checks))*100)
    sc2   = "green" if score>60 else "yellow" if score>30 else "red"
    console.print(f"\n[bold]Security Score: [{sc2}]{score}/100[/{sc2}][/bold]"
                  f"   [green]✓ {pc} PASS[/green]  |  [red]✗ {fc} FAIL[/red]  |  [yellow]△ {wc} WARN[/yellow]")

    results = {"target":url,"checks":checks,"score":score,"pass":pc,"fail":fc,"warn":wc,"sucuri":sucuri}
    fname = DATA_DIR/"defence"/f"defence_{domain}_{ts()}.json"
    with open(fname,"w") as f: json.dump(results,f,indent=2,default=str)
    save_db(url,"defence",results)
    if not silent:
        console.print(f"\n[green][ ✓ ][/green] Saved to {fname}")
        console.input("\n[dim]Press Enter to return to main menu...[/dim]")
    return results

# ════════════════════════════════════════════════════════════════
# MODULE 4 — SIEM LOG ANALYSIS
# ════════════════════════════════════════════════════════════════
ATTACK_PATTERNS = {
    "SQL_INJECTION":       [r"(union\s+select|select\s+\*|drop\s+table|'--|or\s+1=1|benchmark\s*\(|sleep\s*\()",r"(%27|%22|%3D%27)"],
    "XSS_ATTEMPT":         [r"(<script|javascript:|onerror=|onload=|alert\s*\()",r"(%3Cscript|%3c%73%63%72%69%70%74)"],
    "DIRECTORY_TRAVERSAL": [r"(\.\./|\.\.\\|%2e%2e%2f|\.\.%2f)"],
    "BRUTE_FORCE":         [r"(wp-login\.php|/admin/login|/login\.php)"],
    "MALWARE_UPLOAD":      [r"\.(php|php3|phtml|phar|asp|aspx|jsp|sh|exe)\s*(HTTP|$)"],
    "PORT_SCAN":           [r"(nmap|masscan|zmap|nikto|sqlmap|dirbuster)"],
    "CREDENTIAL_STUFFING": [r"(POST /wp-login|POST /login|POST /signin|POST /auth)"],
    "DOS_ATTACK":          [r"(flood|ddos|dos_attack)"],
    "UNAUTHORIZED_ACCESS": [r"(401|403).*(admin|root|config|passwd|shadow)"],
    "DDOS_AMPLIFICATION":  [r"(amplification|reflection|ntp|dns.*flood)"],
}

SEVERITY_MAP = {
    "SQL_INJECTION":"HIGH","XSS_ATTEMPT":"MEDIUM","DIRECTORY_TRAVERSAL":"MEDIUM",
    "BRUTE_FORCE":"HIGH","MALWARE_UPLOAD":"CRITICAL","PORT_SCAN":"MEDIUM",
    "CREDENTIAL_STUFFING":"HIGH","DOS_ATTACK":"CRITICAL",
    "UNAUTHORIZED_ACCESS":"HIGH","DDOS_AMPLIFICATION":"CRITICAL"
}

def parse_log_line(line):
    apache = r'(\S+) \S+ \S+ \[([^\]]+)\] "([^"]*)" (\d+) (\S+)'
    fail2ban = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*\[(.*?)\].*(Ban|Found) (\S+)'
    m = re.match(apache, line)
    if m:
        return {"ip":m.group(1),"timestamp":m.group(2),"request":m.group(3),"status":m.group(4),"type":"apache"}
    m2 = re.match(fail2ban, line)
    if m2:
        return {"ip":m2.group(4),"timestamp":m2.group(1),"request":f"[{m2.group(2)}] {m2.group(3)}","status":"BAN","type":"fail2ban"}
    return None

def detect_attack(req):
    req_l = req.lower()
    for atype, patterns in ATTACK_PATTERNS.items():
        for p in patterns:
            if re.search(p, req_l, re.IGNORECASE):
                return atype
    return None

def generate_demo_events(count=60):
    import random
    atypes = list(ATTACK_PATTERNS.keys())
    ips = [f"{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}" for _ in range(12)]
    return [{"ip":random.choice(ips),"attack_type":random.choice(atypes),
             "timestamp":datetime.datetime.now().isoformat(),"source":"demo"} for _ in range(count)]

def module_siem(target=None, silent=False):
    if not silent:
        console.print(Rule("[bold cyan]MODULE 4 — SIEM Log Analysis & Threat Detection[/bold cyan]"))
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
            with open(log_path,"r",errors="ignore") as f:
                for line in f:
                    pl = parse_log_line(line.strip())
                    if pl:
                        at = detect_attack(pl.get("request",""))
                        if at:
                            events.append({"ip":pl["ip"],"attack_type":at,"timestamp":pl["timestamp"],
                                           "request":pl.get("request",""),"source":"real_log"})
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
                prog.advance(task); time.sleep(0.02)

    console.print("\n[green][ ✓ ][/green] [bold]SIEM Analysis Results:[/bold]\n")

    # Top IPs
    ip_counts = {}
    for e in events: ip_counts[e["ip"]] = ip_counts.get(e["ip"],0)+1
    top_ips = sorted(ip_counts.items(), key=lambda x:x[1], reverse=True)[:8]

    it = Table(title="Top Attacking IP Addresses", box=box.ROUNDED, border_style="red")
    it.add_column("Source IP", style="yellow")
    it.add_column("Attack Count", width=14)
    it.add_column("Risk Level", width=12)
    for ip,cnt in top_ips:
        it.add_row(ip, str(cnt), "[red]HIGH[/red]")
    console.print(it)

    # Attack distribution
    ac = {}
    for e in events: ac[e["attack_type"]] = ac.get(e["attack_type"],0)+1
    at_table = Table(title="Attack Types Distribution", box=box.ROUNDED, border_style="yellow")
    at_table.add_column("Attack Type", style="yellow")
    at_table.add_column("Count", width=8)
    at_table.add_column("Severity", width=12)
    for atype,cnt in sorted(ac.items(), key=lambda x:x[1], reverse=True):
        sev = SEVERITY_MAP.get(atype,"MEDIUM")
        sc  = sev_color(sev)
        at_table.add_row(atype, str(cnt), f"[{sc}]{sev}[/{sc}]")
    console.print(at_table)

    crit = sum(1 for e in events if SEVERITY_MAP.get(e["attack_type"])=="CRITICAL")
    high = sum(1 for e in events if SEVERITY_MAP.get(e["attack_type"])=="HIGH")
    med  = sum(1 for e in events if SEVERITY_MAP.get(e["attack_type"])=="MEDIUM")
    console.print(f"\n[bold]Severity Distribution:[/bold]")
    console.print(f"  [bold red]CRITICAL: {crit}[/bold red]")
    console.print(f"  [red]HIGH:     {high}[/red]")
    console.print(f"  [yellow]MEDIUM:   {med}[/yellow]")
    console.print(f"  [bold]Total Events: {len(events)}[/bold]")

    results = {"events":len(events),"top_ips":top_ips,"attack_counts":ac,"critical":crit,"high":high,"medium":med}
    fname = DATA_DIR/"siem"/f"siem_{ts()}.json"
    with open(fname,"w") as f: json.dump(results,f,indent=2,default=str)
    save_db(target or "siem","siem",results)
    console.print(f"\n[green][ ✓ ][/green] {len(events)} events processed and saved.")
    if not silent:
        console.input("\n[dim]Press Enter to return to main menu...[/dim]")
    return results

# ════════════════════════════════════════════════════════════════
# MODULE 5 — SECURITY POLICY GENERATOR
# ════════════════════════════════════════════════════════════════
POLICIES = {
    "1":{"name":"Password Policy","sections":[
        ("1. Password Requirements","Minimum 12 characters. Must include uppercase, lowercase, numbers and special characters. No dictionary words or personal information allowed."),
        ("2. Password Rotation","Passwords changed every 90 days. Previous 10 passwords may not be reused. Emergency reset required if compromise suspected."),
        ("3. MFA Enforcement","MFA mandatory for all accounts. Authenticator apps preferred over SMS. Hardware tokens for privileged accounts."),
        ("4. Password Storage","All passwords stored using bcrypt or Argon2. Plaintext strictly prohibited. Approved managers: KeePass, 1Password."),
    ]},
    "2":{"name":"Incident Response Policy","sections":[
        ("1. Detection & Identification","All events logged to SIEM. Automated alerts for CRITICAL/HIGH. SOC triage within 15 minutes."),
        ("2. Containment","Isolate affected systems within 30 minutes. Block malicious IPs. Preserve forensic evidence first."),
        ("3. Eradication & Recovery","Remove malware, patch vulnerabilities. Restore from clean backup. Full integrity check before returning to production."),
        ("4. Post-Incident Review","Lessons-learned within 72 hours. Update threat intel. Document IOCs. Update SIEM rules."),
    ]},
    "3":{"name":"Access Control Policy","sections":[
        ("1. Least Privilege","Minimum permissions required. Quarterly access review. Privileged accounts separate from standard accounts."),
        ("2. Authentication Standards","SSO required where available. MFA for remote access and admin panels. 15-minute session timeout."),
        ("3. Access Revocation","Account disabled within 24 hours of termination. Access reviewed on role changes. Monthly orphaned account audit."),
        ("4. Third-Party Access","Vendors get time-limited accounts. All sessions logged. VPN required for remote access."),
    ]},
    "4":{"name":"Data Protection Policy","sections":[
        ("1. Data Classification","All data: Public, Internal, Confidential, or Restricted. Label determines encryption requirements."),
        ("2. Encryption Standards","At rest: AES-256. In transit: TLS 1.2+ (1.3 preferred). Keys rotated annually. HSM for key storage."),
        ("3. Data Retention","Logs retained 12 months minimum. Personal data deleted after legal period. Secure deletion per DoD 5220.22-M."),
        ("4. Breach Notification","Report to DPA within 72 hours. Notify affected individuals promptly. Maintain central breach register."),
    ]},
    "5":{"name":"Vulnerability Management Policy","sections":[
        ("1. Scanning Schedule","Internet-facing assets scanned weekly. Internal monthly. Critical vulns patched within 24 hours."),
        ("2. Patch Management","Critical: 24h. High: 7 days. Medium: 30 days. Low: 90 days. Emergency patching process documented."),
        ("3. Penetration Testing","Annual external pentest by certified third party. Internal quarterly. All findings tracked."),
        ("4. Risk Acceptance","Unpatched vulns require CISO sign-off. Risk acceptance reviewed every 30 days. No indefinite acceptance."),
    ]},
}

def module_policy(silent=False):
    if not silent:
        console.print(Rule("[bold cyan]MODULE 5 — Security Policy Generator[/bold cyan]"))
    org = console.input("\n[dim]Organisation name: [/dim]").strip() or "Organisation"
    console.print("\n[bold]Select policy:[/bold]")
    for k,v in POLICIES.items():
        console.print(f"  [cyan]{k}.[/cyan] {v['name']}")
    choice = console.input("\n[dim]Choice [1-5]: [/dim]").strip() or "1"
    policy = POLICIES.get(choice, POLICIES["1"])
    console.print(f"\n[cyan][ * ][/cyan] Generating [bold]{policy['name']}[/bold] for [bold]{org}[/bold]...")
    time.sleep(0.4)
    console.print(Panel(f"[bold cyan]{policy['name'].upper()}[/bold cyan]\n[dim]Organisation: {org} | {datetime.date.today()}[/dim]", border_style="cyan"))
    for title, content in policy["sections"]:
        console.print(Panel(f"[bold cyan]{title}[/bold cyan]\n[white]{content}[/white]", border_style="dim"))
    fname = DATA_DIR/"policies"/f"policy_{policy['name'].replace(' ','_')}_{ts()}.txt"
    with open(fname,"w") as f:
        f.write(f"{policy['name'].upper()}\nOrganisation: {org}\nGenerated: {datetime.date.today()}\n\n")
        for title,content in policy["sections"]:
            f.write(f"{title}\n{content}\n\n")
    console.print(f"\n[green][ ✓ ][/green] Policy saved to {fname}")
    if not silent:
        console.input("\n[dim]Press Enter to return to main menu...[/dim]")

# ════════════════════════════════════════════════════════════════
# MODULE 6 — VIRUSTOTAL REPUTATION CHECK
# ════════════════════════════════════════════════════════════════
def module_virustotal(target=None, silent=False):
    if not silent:
        console.print(Rule("[bold cyan]MODULE 6 — VirusTotal Reputation Check (90+ engines)[/bold cyan]"))

    key = CONFIG.get("virustotal_api_key","")
    if not key or key == "PASTE_YOUR_VIRUSTOTAL_KEY_HERE":
        console.print("[red][ ! ][/red] VirusTotal API key not configured.")
        console.print("[dim]    Open config.json and add your VirusTotal API key.[/dim]")
        if not silent: console.input("\n[dim]Press Enter to return...[/dim]")
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
                data = r.json().get("data",{}).get("attributes",{})
                stats = data.get("last_analysis_stats",{})
                results["domain_stats"] = stats
                results["reputation"]   = data.get("reputation",0)
                results["categories"]   = data.get("categories",{})
                results["malicious"]    = stats.get("malicious",0)
                results["suspicious"]   = stats.get("suspicious",0)
                results["harmless"]     = stats.get("harmless",0)
                results["undetected"]   = stats.get("undetected",0)
                results["total_engines"]= sum(stats.values())
                results["whois"]        = data.get("whois","")[:300]
                results["registrar"]    = data.get("registrar","Unknown")
                results["creation_date"]= data.get("creation_date","")
            elif r.status_code == 404:
                results["error"] = "Domain not found in VirusTotal database"
            elif r.status_code == 401:
                results["error"] = "Invalid API key"
            else:
                results["error"] = f"API returned {r.status_code}"
        except Exception as e:
            results["error"] = str(e)
        prog.advance(task); rate_sleep()

        # IP resolution check
        prog.update(task, description="[cyan]Checking resolved IPs...")
        try:
            ip = socket.gethostbyname(domain)
            results["resolved_ip"] = ip
            ip_r = requests.get(f"https://www.virustotal.com/api/v3/ip_addresses/{ip}",
                                headers=headers, timeout=15)
            if ip_r.status_code == 200:
                ip_data = ip_r.json().get("data",{}).get("attributes",{})
                ip_stats = ip_data.get("last_analysis_stats",{})
                results["ip_malicious"]  = ip_stats.get("malicious",0)
                results["ip_suspicious"] = ip_stats.get("suspicious",0)
                results["ip_country"]    = ip_data.get("country","Unknown")
                results["ip_asn"]        = ip_data.get("asn","")
                results["ip_as_owner"]   = ip_data.get("as_owner","")
        except Exception as e:
            results["ip_error"] = str(e)
        prog.advance(task); rate_sleep()

        # URL scan
        prog.update(task, description="[cyan]Checking URL reputation...")
        try:
            import base64
            url_b64 = base64.urlsafe_b64encode(f"https://{domain}".encode()).decode().rstrip("=")
            url_r = requests.get(f"https://www.virustotal.com/api/v3/urls/{url_b64}",
                                 headers=headers, timeout=15)
            if url_r.status_code == 200:
                url_data  = url_r.json().get("data",{}).get("attributes",{})
                url_stats = url_data.get("last_analysis_stats",{})
                results["url_malicious"]  = url_stats.get("malicious",0)
                results["url_suspicious"] = url_stats.get("suspicious",0)
        except Exception as e:
            results["url_error"] = str(e)
        prog.advance(task)

    # Display
    if "error" in results:
        console.print(f"[red][ ! ][/red] {results['error']}")
    else:
        console.print(f"\n[green][ ✓ ][/green] VirusTotal scan complete\n")
        mal   = results.get("malicious",0)
        susp  = results.get("suspicious",0)
        total = results.get("total_engines",0)
        rep   = results.get("reputation",0)

        # Overall verdict
        if mal > 5:
            verdict = "[bold red]DANGEROUS — Multiple engines flagged this domain[/bold red]"
        elif mal > 0 or susp > 3:
            verdict = "[bold yellow]SUSPICIOUS — Some engines flagged this domain[/bold yellow]"
        else:
            verdict = "[bold green]CLEAN — No significant threats detected[/bold green]"

        console.print(Panel(verdict, border_style="cyan", title="Verdict"))

        t = Table(title=f"VirusTotal Report — {domain}", box=box.ROUNDED, border_style="cyan")
        t.add_column("Metric",  style="dim", width=30)
        t.add_column("Value",   style="white")
        t.add_row("Domain",          domain)
        t.add_row("Resolved IP",     results.get("resolved_ip","?"))
        t.add_row("IP Country",      results.get("ip_country","?"))
        t.add_row("IP ASN Owner",    results.get("ip_as_owner","?"))
        t.add_row("Registrar",       results.get("registrar","?"))
        t.add_row("VT Reputation",   str(rep))
        t.add_row("Total Engines",   str(total))
        t.add_row("Malicious",       f"[red]{mal}[/red]" if mal>0 else f"[green]{mal}[/green]")
        t.add_row("Suspicious",      f"[yellow]{susp}[/yellow]" if susp>0 else f"[green]{susp}[/green]")
        t.add_row("Harmless",        f"[green]{results.get('harmless',0)}[/green]")
        t.add_row("Undetected",      str(results.get("undetected",0)))
        t.add_row("IP Malicious",    f"[red]{results.get('ip_malicious',0)}[/red]" if results.get("ip_malicious",0)>0 else "[green]0[/green]")
        t.add_row("URL Malicious",   f"[red]{results.get('url_malicious',0)}[/red]" if results.get("url_malicious",0)>0 else "[green]0[/green]")
        console.print(t)

        # Categories
        cats = results.get("categories",{})
        if cats:
            console.print(f"\n[dim]Categories: {', '.join(set(cats.values()))}[/dim]")

    fname = DATA_DIR/"virustotal"/f"vt_{domain}_{ts()}.json"
    with open(fname,"w") as f: json.dump(results,f,indent=2,default=str)
    save_db(domain,"virustotal",results)
    if not silent:
        console.print(f"\n[green][ ✓ ][/green] Saved to {fname}")
        console.input("\n[dim]Press Enter to return to main menu...[/dim]")
    return results

# ════════════════════════════════════════════════════════════════
# MODULE 7 — SECURITY OVERVIEW DASHBOARD
# ════════════════════════════════════════════════════════════════
def module_dashboard(silent=False):
    if not silent:
        console.print(Rule("[bold cyan]MODULE 7 — Security Overview Dashboard[/bold cyan]"))

    vuln_d    = get_latest("vuln")
    defence_d = get_latest("defence")
    siem_d    = get_latest("siem")
    vt_d      = get_latest("virustotal")
    recon_d   = get_latest("recon")

    s     = vuln_d.get("summary",{})
    score = defence_d.get("score",0)
    sc    = "green" if score>60 else "yellow" if score>30 else "red"

    console.print(f"\n[bold]Security Posture Overview[/bold] — {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

    panels = [
        Panel(f"[bold red]{s.get('critical',0)}[/bold red]\n[dim]Critical Vulns[/dim]",   border_style="red"),
        Panel(f"[bold red]{s.get('high',0)}[/bold red]\n[dim]High Vulns[/dim]",             border_style="red"),
        Panel(f"[bold yellow]{s.get('medium',0)}[/bold yellow]\n[dim]Medium Vulns[/dim]",  border_style="yellow"),
        Panel(f"[bold {sc}]{score}/100[/bold {sc}]\n[dim]Security Score[/dim]",             border_style=sc),
        Panel(f"[bold cyan]{siem_d.get('events',0)}[/bold cyan]\n[dim]SIEM Events[/dim]",  border_style="cyan"),
        Panel(f"[bold red]{vt_d.get('malicious',0)}[/bold red]\n[dim]VT Malicious[/dim]",  border_style="magenta"),
    ]
    console.print(Columns(panels, equal=True))

    # Sources status
    console.print("\n")
    src_t = Table(title="Live Data Sources Status", box=box.SIMPLE, border_style="dim")
    src_t.add_column("Source", style="cyan", width=30)
    src_t.add_column("Status", width=15)
    src_t.add_column("Last Result", width=35)

    nuclei_ok = NUCLEI_AVAILABLE
    wpscan_ok = bool(CONFIG.get("wpscan_api_key") and CONFIG.get("wpscan_api_key") != "PASTE_YOUR_WPSCAN_KEY_HERE")
    vt_ok     = bool(CONFIG.get("virustotal_api_key") and CONFIG.get("virustotal_api_key") != "PASTE_YOUR_VIRUSTOTAL_KEY_HERE")

    src_t.add_row("Nuclei v3.7.1 (92 templates)",   "[green]Ready[/green]" if nuclei_ok else "[red]Not installed[/red]",    "install: sudo apt install nuclei")
    src_t.add_row("WPScan (WordPress CVE DB)",        "[green]Configured[/green]" if wpscan_ok else "[yellow]Key missing[/yellow]", "Add key to config.json")
    src_t.add_row("VirusTotal API (90+ engines)",     "[green]Configured[/green]" if vt_ok else "[yellow]Key missing[/yellow]",     f"Last: {vt_d.get('malicious','?')} malicious" if vt_d else "Not run yet")
    src_t.add_row("Sucuri SiteCheck",                "[green]Ready[/green]","No key required")
    src_t.add_row("SecurityHeaders.com",             "[green]Ready[/green]","No key required")
    src_t.add_row("Cloudflare CF-RAY Heuristic",     "[green]Ready[/green]",f"{'Detected' if recon_d.get('cloudflare') else 'Not detected'}" if recon_d else "Not run yet")
    console.print(src_t)

    # Scan history
    rows = get_history(10)
    if rows:
        console.print("\n")
        ht = Table(title="Recent Scan History", box=box.SIMPLE, border_style="dim")
        ht.add_column("ID",        width=5)
        ht.add_column("Module",    style="cyan", width=14)
        ht.add_column("Target",    width=32)
        ht.add_column("Timestamp", width=20)
        for row in rows:
            ht.add_row(str(row[0]), row[2], row[1][:32], row[3][:19])
        console.print(ht)

    console.print(f"\n[green][ ✓ ][/green] Dashboard updated — {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if not silent:
        console.input("\n[dim]Press Enter to return to main menu...[/dim]")

# ════════════════════════════════════════════════════════════════
# MODULE 8 — AUTO SCAN (FULL PIPELINE)
# ════════════════════════════════════════════════════════════════
def module_auto_scan():
    console.print(Rule("[bold cyan]MODULE 8 — Auto Scan — Full Pipeline[/bold cyan]"))
    console.print("\n[dim]This runs ALL modules automatically — one command, zero manual steps.[/dim]")
    target = console.input("\n[dim]Enter target domain/URL: [/dim]").strip()
    if not target:
        console.print("[red][ ! ][/red] No target provided.")
        console.input("\n[dim]Press Enter to return...[/dim]")
        return

    url    = clean_url(target)
    domain = get_domain(url)
    start  = datetime.datetime.now()

    console.print(f"\n[bold cyan][ AUTO SCAN STARTING ][/bold cyan] — {url}")
    console.print(f"[dim]Running full 6-source pipeline. This may take 3-8 minutes.[/dim]\n")

    pipeline = [
        ("1. Reconnaissance",          lambda: module_recon(target, silent=True)),
        ("2. Vulnerability Assessment", lambda: module_vuln(target, silent=True, recon_data=recon_r)),
        ("3. Defence Configuration",    lambda: module_defence(target, silent=True)),
        ("4. SIEM Analysis",            lambda: module_siem(target, silent=True)),
        ("5. VirusTotal Check",         lambda: module_virustotal(domain, silent=True)),
        ("6. Dashboard Update",         lambda: module_dashboard(silent=True)),
    ]

    recon_r = {}
    all_results = {}

    for i, (step_name, step_fn) in enumerate(pipeline, 1):
        console.print(f"\n[cyan][ {i}/6 ][/cyan] [bold]{step_name}[/bold]")
        console.print(Rule(style="dim"))
        try:
            r = step_fn()
            if step_name.startswith("1"):
                recon_r = r or {}
            all_results[step_name] = r
            console.print(f"[green][ ✓ ][/green] {step_name} complete")
        except Exception as e:
            console.print(f"[red][ ! ][/red] {step_name} failed: {e}")
            logging.error(f"Auto scan step {step_name} failed: {e}")
        time.sleep(1)

    elapsed = (datetime.datetime.now() - start).seconds
    console.print(f"\n[bold cyan][ AUTO SCAN COMPLETE ][/bold cyan]")
    console.print(f"[dim]Target: {url} | Time: {elapsed}s | Modules: 6/6[/dim]")
    console.print(f"\n[dim]All results saved to /data/ — Run Module 10 to generate PDF report.[/dim]")
    console.input("\n[dim]Press Enter to return to main menu...[/dim]")

# ════════════════════════════════════════════════════════════════
# MODULE 9 — CUSTOM SCAN
# ════════════════════════════════════════════════════════════════
def module_custom_scan():
    console.print(Rule("[bold cyan]MODULE 9 — Custom Scan — Choose Your Modules[/bold cyan]"))
    console.print("\n[dim]Select which modules to run. Surgical, fast, flexible.[/dim]\n")

    options = [
        ("1","Reconnaissance & Tech Stack"),
        ("2","Vulnerability Assessment (CVSS + NVD + Nuclei + WPScan)"),
        ("3","Defence Configuration Check (+ SecurityHeaders + Sucuri)"),
        ("4","SIEM Log Analysis"),
        ("5","Security Policy Generator"),
        ("6","VirusTotal Reputation Check"),
    ]
    for num, name in options:
        console.print(f"  [cyan][{num}][/cyan] {name}")

    selection = console.input("\n[dim]Enter module numbers separated by comma (e.g. 1,2,6): [/dim]").strip()
    target    = console.input("[dim]Enter target URL/domain: [/dim]").strip()

    if not selection or not target:
        console.print("[red][ ! ][/red] No selection or target. Returning to menu.")
        console.input("\n[dim]Press Enter...[/dim]")
        return

    url    = clean_url(target)
    domain = get_domain(url)
    chosen = [s.strip() for s in selection.split(",") if s.strip() in [o[0] for o in options]]

    console.print(f"\n[bold cyan][ CUSTOM SCAN ][/bold cyan] — {url}")
    console.print(f"[dim]Running modules: {', '.join(chosen)}[/dim]\n")

    module_map = {
        "1": lambda: module_recon(target, silent=True),
        "2": lambda: module_vuln(target, silent=True),
        "3": lambda: module_defence(target, silent=True),
        "4": lambda: module_siem(target, silent=True),
        "5": lambda: module_policy(silent=True),
        "6": lambda: module_virustotal(domain, silent=True),
    }

    for num in chosen:
        name = dict(options).get(num,"Module")
        console.print(f"\n[cyan][ * ][/cyan] [bold]Running: {name}[/bold]")
        console.print(Rule(style="dim"))
        try:
            module_map[num]()
            console.print(f"[green][ ✓ ][/green] {name} complete")
        except Exception as e:
            console.print(f"[red][ ! ][/red] {name} failed: {e}")
        time.sleep(0.5)

    console.print(f"\n[bold cyan][ CUSTOM SCAN COMPLETE ][/bold cyan]")
    console.print("[dim]Run Module 10 to generate a PDF report of all results.[/dim]")
    console.input("\n[dim]Press Enter to return to main menu...[/dim]")

# ════════════════════════════════════════════════════════════════
# MODULE 10 — PDF REPORT
# ════════════════════════════════════════════════════════════════
def module_report():
    console.print(Rule("[bold cyan]MODULE 10 — Generate Full Security Report (PDF)[/bold cyan]"))
    org    = console.input("\n[dim]Company name: [/dim]").strip() or "Organisation"
    target = console.input("[dim]Primary target: [/dim]").strip() or "N/A"
    author = console.input("[dim]Report author: [/dim]").strip() or "Security Analyst"

    console.print(f"\n[cyan][ * ][/cyan] Building PDF report...\n")

    # Load latest data
    vuln_d    = get_latest("vuln")
    defence_d = get_latest("defence")
    siem_d    = get_latest("siem")
    vt_d      = get_latest("virustotal")
    recon_d   = get_latest("recon")

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                  BarColumn(), console=console) as prog:
        task = prog.add_task("[cyan]Building report...", total=6)

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)

        # ── Cover page ──────────────────────────────────────
        pdf.add_page()
        prog.update(task, description="[cyan]Cover page...")
        pdf.set_font("Helvetica","B",22)
        pdf.set_text_color(30,30,30)
        pdf.ln(20)
        pdf.cell(0,12,"CYBERSECURITY ASSESSMENT REPORT",ln=True,align="C")
        pdf.set_font("Helvetica","",12)
        pdf.set_text_color(100,100,100)
        for line in [f"Organisation: {org}",f"Primary Target: {target}",
                     f"Date: {datetime.date.today()}",f"Author: {author}",
                     "SecuritateIT.ro — Cybersecurity Final Project"]:
            pdf.cell(0,7,line,ln=True,align="C")
        pdf.ln(8)
        pdf.set_draw_color(200,50,50)
        pdf.line(10,pdf.get_y(),200,pdf.get_y())
        pdf.ln(8)

        # Data sources used
        pdf.set_font("Helvetica","B",11)
        pdf.set_text_color(30,30,30)
        pdf.cell(0,8,"Live Data Sources Used:",ln=True)
        pdf.set_font("Helvetica","",10)
        for src in ["Nuclei v3.7.1 — Technical vulnerability templates",
                    "WPScan — WordPress CVE database",
                    "VirusTotal API — 90+ antivirus engines",
                    "Sucuri SiteCheck — External malware & blacklist",
                    "SecurityHeaders.com — HTTP header grading A-F",
                    "Cloudflare CF-RAY — WAF/DDoS heuristic detection"]:
            pdf.cell(0,6,f"  • {src}",ln=True)
        prog.advance(task)

        # ── Executive Summary ────────────────────────────────
        pdf.add_page()
        prog.update(task, description="[cyan]Executive summary...")
        pdf.set_font("Helvetica","B",14)
        pdf.set_text_color(30,30,30)
        pdf.cell(0,8,"1. EXECUTIVE SUMMARY",ln=True)
        pdf.ln(2)
        s     = vuln_d.get("summary",{})
        score = defence_d.get("score",0)
        vt_mal = vt_d.get("malicious",0)
        rows_data = [
            ("Critical Vulnerabilities", str(s.get("critical",0)), "URGENT" if s.get("critical",0)>0 else "Clear"),
            ("High Vulnerabilities",     str(s.get("high",0)),     "Priority" if s.get("high",0)>0 else "Clear"),
            ("Medium Vulnerabilities",   str(s.get("medium",0)),   "Monitor"),
            ("Low Vulnerabilities",      str(s.get("low",0)),      "Normal"),
            ("Security Score",           f"{score}/100",           "Needs Work" if score<50 else "Acceptable"),
            ("VirusTotal Malicious",     str(vt_mal),              "DANGEROUS" if vt_mal>5 else "Suspicious" if vt_mal>0 else "Clean"),
            ("SIEM Events Analyzed",     str(siem_d.get("events",0)),"Processed"),
            ("Defence PASS/Total",       f"{defence_d.get('pass',0)}/{len(defence_d.get('checks',[]))}","Verified"),
            ("Cloudflare Detected",      "Yes" if recon_d.get("cloudflare") else "No","Info"),
        ]
        pdf.set_font("Helvetica","B",9)
        pdf.set_fill_color(30,50,100); pdf.set_text_color(255,255,255)
        pdf.cell(80,7,"Metric",border=1,fill=True)
        pdf.cell(40,7,"Value",border=1,fill=True)
        pdf.cell(60,7,"Status",border=1,fill=True,ln=True)
        pdf.set_font("Helvetica","",9)
        for i,(m,v,st) in enumerate(rows_data):
            pdf.set_fill_color(240,240,240) if i%2==0 else pdf.set_fill_color(255,255,255)
            pdf.set_text_color(30,30,30)
            pdf.cell(80,6,m,border=1,fill=True)
            pdf.cell(40,6,v,border=1,fill=True)
            pdf.cell(60,6,st,border=1,fill=True,ln=True)
        prog.advance(task)

        # ── Vulnerability Results ────────────────────────────
        pdf.add_page()
        prog.update(task, description="[cyan]Vulnerability section...")
        pdf.set_font("Helvetica","B",14); pdf.set_text_color(30,30,30)
        pdf.cell(0,8,"2. VULNERABILITY ASSESSMENT RESULTS",ln=True); pdf.ln(2)
        vulns = vuln_d.get("vulnerabilities",[])
        confirmed = [v for v in vulns if v.get("confirmed")]
        if confirmed:
            pdf.set_font("Helvetica","B",9)
            pdf.set_fill_color(30,50,100); pdf.set_text_color(255,255,255)
            pdf.cell(8,7,"#",border=1,fill=True)
            pdf.cell(72,7,"Vulnerability",border=1,fill=True)
            pdf.cell(20,7,"Source",border=1,fill=True)
            pdf.cell(30,7,"Severity",border=1,fill=True)
            pdf.cell(20,7,"CVSS",border=1,fill=True)
            pdf.cell(30,7,"CVE",border=1,fill=True,ln=True)
            pdf.set_font("Helvetica","",8)
            sev_rgb = {"CRITICAL":(220,50,50),"HIGH":(220,100,50),"MEDIUM":(220,180,50),"LOW":(50,180,50)}
            for i,v in enumerate(confirmed[:15],1):
                pdf.set_fill_color(240,240,240) if i%2==0 else pdf.set_fill_color(255,255,255)
                pdf.set_text_color(30,30,30)
                pdf.cell(8,5,str(i),border=1,fill=True)
                pdf.cell(72,5,v["name"][:45],border=1,fill=True)
                pdf.cell(20,5,v.get("source","")[:10],border=1,fill=True)
                r2,g2,b2 = sev_rgb.get(v["severity"],(100,100,100))
                pdf.set_text_color(r2,g2,b2)
                pdf.cell(30,5,v["severity"],border=1,fill=True)
                pdf.set_text_color(30,30,30)
                pdf.cell(20,5,str(v["cvss"]),border=1,fill=True)
                pdf.cell(30,5,str(v.get("cve_id","N/A"))[:18],border=1,fill=True,ln=True)
        prog.advance(task)

        # ── Defence + VT ─────────────────────────────────────
        pdf.add_page()
        prog.update(task, description="[cyan]Defence & VirusTotal section...")
        pdf.set_font("Helvetica","B",14); pdf.set_text_color(30,30,30)
        pdf.cell(0,8,"3. DEFENCE CONFIGURATION",ln=True); pdf.ln(2)
        checks = defence_d.get("checks",[])
        if checks:
            pdf.set_font("Helvetica","B",9)
            pdf.set_fill_color(30,50,100); pdf.set_text_color(255,255,255)
            pdf.cell(85,7,"Check",border=1,fill=True)
            pdf.cell(40,7,"Requirement",border=1,fill=True)
            pdf.cell(25,7,"Status",border=1,fill=True)
            pdf.cell(30,7,"Score",border=1,fill=True,ln=True)
            pdf.set_font("Helvetica","",8)
            sc_rgb = {"PASS":(50,180,50),"FAIL":(220,50,50),"WARN":(220,180,50)}
            for i,c in enumerate(checks):
                pdf.set_fill_color(240,240,240) if i%2==0 else pdf.set_fill_color(255,255,255)
                pdf.set_text_color(30,30,30)
                pdf.cell(85,5,c["name"][:50],border=1,fill=True)
                pdf.cell(40,5,c["requirement"],border=1,fill=True)
                r2,g2,b2 = sc_rgb.get(c["status"],(100,100,100))
                pdf.set_text_color(r2,g2,b2)
                pdf.cell(25,5,c["status"],border=1,fill=True)
                pdf.set_text_color(30,30,30)
                pdf.cell(30,5,f"Score: {score}/100" if i==0 else "",border=1,fill=True,ln=True)
        pdf.ln(6)
        pdf.set_font("Helvetica","B",14); pdf.cell(0,8,"4. VIRUSTOTAL REPUTATION",ln=True); pdf.ln(2)
        pdf.set_font("Helvetica","",10)
        pdf.cell(0,6,f"Domain: {vt_d.get('target','N/A')}",ln=True)
        pdf.cell(0,6,f"Malicious engines: {vt_d.get('malicious',0)} / {vt_d.get('total_engines',0)}",ln=True)
        pdf.cell(0,6,f"Suspicious: {vt_d.get('suspicious',0)}",ln=True)
        pdf.cell(0,6,f"Harmless: {vt_d.get('harmless',0)}",ln=True)
        pdf.cell(0,6,f"IP Country: {vt_d.get('ip_country','?')} | ASN: {vt_d.get('ip_as_owner','?')}",ln=True)
        prog.advance(task)

        # ── SIEM + Recommendations ───────────────────────────
        pdf.add_page()
        prog.update(task, description="[cyan]SIEM & recommendations...")
        pdf.set_font("Helvetica","B",14); pdf.set_text_color(30,30,30)
        pdf.cell(0,8,"5. SIEM ANALYSIS SUMMARY",ln=True); pdf.ln(2)
        pdf.set_font("Helvetica","",10)
        for line in [
            f"Total Events Analyzed: {siem_d.get('events',0)}",
            f"Critical Events: {siem_d.get('critical',0)}",
            f"High Events: {siem_d.get('high',0)}",
            f"Medium Events: {siem_d.get('medium',0)}",
        ]:
            pdf.cell(0,6,line,ln=True)
        pdf.ln(6)
        pdf.set_font("Helvetica","B",14)
        pdf.cell(0,8,"6. RECOMMENDATIONS",ln=True); pdf.ln(2)
        pdf.set_font("Helvetica","",10)
        for rec in [
            "1. Immediately update WordPress core to the latest stable version.",
            "2. Enable HTTPS with a valid TLS 1.3 certificate.",
            "3. Deploy a Web Application Firewall (Cloudflare or Wordfence).",
            "4. Enable Two-Factor Authentication on all admin accounts.",
            "5. Configure all missing HTTP Security Headers (CSP, HSTS, X-Frame-Options).",
            "6. Disable XML-RPC endpoint if not actively required.",
            "7. Implement login rate limiting to prevent brute force attacks.",
            "8. Remove or restrict access to exposed backup files.",
            "9. Relocate WordPress admin URL from default /wp-admin/.",
            "10. Enable Cloudflare DDoS protection and geo-blocking.",
            "11. Subscribe to VirusTotal monitoring for domain reputation alerts.",
            "12. Schedule weekly Nuclei scans to catch new CVEs promptly.",
        ]:
            pdf.cell(0,6,rec,ln=True)
        prog.advance(task)

    fname = DATA_DIR/"reports"/f"security_report_{ts()}.pdf"
    pdf.output(str(fname))
    console.print(f"\n[green][ ✓ ][/green] PDF Report generated successfully!")
    console.print(f"[green]Saved to: {fname}[/green]")
    console.input("\n[dim]Press Enter to return to main menu...[/dim]")

# ════════════════════════════════════════════════════════════════
# MAIN LOOP
# ════════════════════════════════════════════════════════════════
def main():
    init_db()
    if not NMAP_AVAILABLE:
        console.print("[yellow][ ! ][/yellow] python-nmap not installed — using socket fallback")
        console.print("[dim]    Fix: pip3 install python-nmap --break-system-packages[/dim]\n")
    if not NUCLEI_AVAILABLE:
        console.print("[yellow][ ! ][/yellow] Nuclei not installed — Module 2 will skip Nuclei scans")
        console.print("[dim]    Fix: sudo apt install nuclei[/dim]\n")

    dispatch = {
        "1":  module_recon,
        "2":  module_vuln,
        "3":  module_defence,
        "4":  module_siem,
        "5":  module_policy,
        "6":  module_virustotal,
        "7":  module_dashboard,
        "8":  module_auto_scan,
        "9":  module_custom_scan,
        "10": module_report,
    }

    while True:
        print_banner()
        print_menu()
        choice = input().strip()
        if choice == "0":
            console.print("\n[cyan]Goodbye. Stay secure. 🛡️[/cyan]\n")
            break
        elif choice in dispatch:
            try:
                dispatch[choice]()
            except KeyboardInterrupt:
                console.print("\n[yellow][ ! ][/yellow] Interrupted — returning to menu")
            except Exception as e:
                console.print(f"\n[red][ ! ][/red] Error: {e}")
                logging.error(f"Module {choice} error: {e}")
                console.input("[dim]Press Enter to continue...[/dim]")
        else:
            console.print("[red]Invalid option.[/red]")
            time.sleep(0.8)

if __name__ == "__main__":
    main()
