# CYBERDEFENCE ANALYST PLATFORM v3.1
## Complete Project Documentation

**Author:** Danger Wolf
**Institution:** SecuritateIT.ro — Final Project  
**Version:** 3.1  
**Date:** 2024-2025  
**Language:** Python 3  

---

## 📋 PROJECT OVERVIEW

The **CyberDefence Analyst Platform v3.1** is a comprehensive, enterprise-grade cybersecurity assessment tool designed for Security Operations Centers (SOCs), cybersecurity professionals, and defensive security teams. It integrates multiple live data sources into a unified platform that automates security scanning, vulnerability detection, threat analysis, and compliance reporting.

This is a **full-stack security platform** that bridges the gap between automated scanning tools (Nuclei, WPScan) and actionable security intelligence through real-time analysis, historical logging, and professional PDF reporting.

---

## 🎯 CORE MISSION

To provide security analysts with a **360-degree view** of a target's security posture by:
1. **Automating** multi-source vulnerability scanning
2. **Combining** results from 6+ live security databases
3. **Analyzing** SIEM logs for threat patterns
4. **Grading** defence configurations against best practices
5. **Generating** professional security reports for stakeholders

---

## 🔧 TECHNICAL STACK

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Core Language** | Python 3.8+ | Main platform engine |
| **CLI Framework** | `rich` | Beautiful console UI/UX |
| **HTTP Client** | `requests` | API interactions, web scanning |
| **Reporting** | `fpdf2` | PDF report generation |
| **Port Scanning** | `python-nmap` | Network reconnaissance |
| **Database** | SQLite3 | Historical scan storage |
| **Logging** | Python `logging` | Platform audit trail |

### Live Data Sources Integrated

| Source | API/Tool | Coverage | Key Data |
|--------|----------|----------|----------|
| **Nuclei** | CLI (v3.7.1) | 92 templates | Misconfigs, SSL, CVEs |
| **WPScan** | REST API | WordPress | Plugin CVEs, core vulns |
| **VirusTotal** | REST API | 90+ engines | Domain/IP reputation |
| **Sucuri** | Web scraping | Malware/blacklist | Site safety check |
| **SecurityHeaders.com** | Web scraping | HTTP headers | Grade A-F, missing headers |
| **Cloudflare** | HTTP headers | WAF/DDoS | CF-RAY detection |

---

## 📦 PROJECT STRUCTURE

```
cyberdefence_v31/
├── cyberdefence_platform_v31.py    # Main application (1600+ lines)
├── config.json                      # API keys & settings
├── requirements.txt                 # Python dependencies
├── setup.sh                         # Installation script
└── data/                            # Output directories
    ├── recon/                       # Reconnaissance results
    ├── vuln/                        # Vulnerability scans
    ├── defence/                     # Defence config checks
    ├── siem/                        # Log analysis results
    ├── policies/                    # Generated security policies
    ├── reports/                     # PDF reports
    ├── virustotal/                  # VT reputation data
    ├── nuclei/                      # Nuclei findings
    ├── sucuri/                      # Sucuri safety checks
    ├── cyberdefence.db              # SQLite scan history
    └── platform.log                 # Audit log
```

---

## 🎮 MODULES & FEATURES

### **MODULE 1: RECONNAISSANCE & TECHNOLOGY SCANNING** 🔍
**Purpose:** Gather intelligence about a target's infrastructure and tech stack

**What it does:**
- Performs HTTP fingerprinting to detect server software
- Identifies CMS platforms (WordPress, Joomla, Drupal, Shopify, etc.)
- Discovers frontend technologies (jQuery, React, Angular, Bootstrap, etc.)
- Audits HTTP security headers (HSTS, CSP, X-Frame-Options, etc.)
- Extracts SSL/TLS certificate details
- Port scans common ports (21, 22, 25, 53, 80, 443, 3306, 5432, 6379, 8080, 8443, 9200)
- Detects Cloudflare presence via CF-RAY headers

**Output:**
- Detailed JSON report with all discovered technologies
- SSL certificate validity, expiration, issuer
- List of open ports with service identification
- Security header assessment
- Cloudflare WAF detection

---

### **MODULE 2: VULNERABILITY ASSESSMENT** 🎯
**Purpose:** Identify CVEs, misconfigurations, and known vulnerabilities

**Integrated Scanners:**
1. **Live Manual Checks** (9 checks)
   - XML-RPC endpoint exposure (WordPress brute force vector)
   - Outdated WordPress version detection
   - Directory listing misconfiguration
   - Missing HTTP security headers
   - Default WordPress /wp-admin/ accessibility
   - Exposed backup files (.git, .bak, SQL dumps)
   - Weak SSL/TLS configuration (TLSv1.0, TLSv1.1)
   - No rate limiting on login endpoints
   - WordPress user enumeration via REST API

2. **Nuclei Integration** (92+ templates)
   - Runs SSL/TLS templates
   - HTTP misconfiguration checks
   - Technology exposure scanning
   - Advanced vulnerability detection
   - Automatic CVSS scoring

3. **WPScan API Integration** (WordPress-specific)
   - WordPress core version vulnerabilities
   - Popular plugin vulnerability database
   - Real-time CVE matching

4. **NVD (National Vulnerability Database)**
   - CVSS v3.1 scoring
   - Detailed CVE descriptions
   - Attack vectors and impact ratings

**Output:**
- Comprehensive vulnerability table with severity levels
- CVSS scores (0-10)
- CVE identifiers
- Evidence of confirmation
- Source attribution (nuclei, wpscan, live_check, nvd)
- Statistical summary (Critical/High/Medium/Low counts)

---

### **MODULE 3: DEFENCE CONFIGURATION CHECK** 🛡️
**Purpose:** Grade the target's defensive posture against OWASP best practices

**Checks Performed (14 total):**

| Check | Source | Pass Criteria | Status |
|-------|--------|--------------|--------|
| HTTPS/SSL Certificate | Live | Valid cert | Automated |
| HTTP→HTTPS Redirect | Live | 301/302/307/308 to HTTPS | Automated |
| HTTP Security Headers | SecurityHeaders.com | All 4 required | Automated |
| WAF/Firewall Present | Live + headers | CF-RAY or custom heuristic | Automated |
| Cloudflare DDoS Protection | HTTP headers | CF-RAY present | Automated |
| WordPress /wp-admin/ Hidden | Live | 404 response | Automated |
| XML-RPC Disabled | Live | 404 response | Automated |
| Sucuri Malware/Blacklist Check | Sucuri API | Clean status | Automated |
| 2FA/Google Authenticator | Manual | Manual verification | Manual |
| Geo-blocking (RU/DE/PH) | Manual | Wordfence settings | Manual |
| Anti-Brute Force (3 attempts) | Manual | Wordfence config | Manual |
| Antivirus Software | Manual | Host machine | Manual |
| Password Manager | Manual | KeyPass/1Password | Manual |
| Regular Backups | Manual | Backup schedule | Manual |

**Scoring System:**
- PASS (✓): 1 point
- FAIL (✗): 0 points
- WARN (△): Manual review needed

**Final Score:** (PASS count / Total checks) × 100

**Output:**
- Detailed check table with status, requirements, and details
- Security posture score (0-100)
- Visual indicator: Green (>60), Yellow (30-60), Red (<30)
- Sucuri safety assessment (clean/malware/blacklisted)

---

### **MODULE 4: SIEM LOG ANALYSIS & THREAT DETECTION** 📊
**Purpose:** Parse and analyze security logs for attack patterns

**Attack Patterns Detected (10 types):**
```python
SQL_INJECTION       → union select, drop table, OR 1=1, etc.
XSS_ATTEMPT        → <script>, javascript:, onerror=, etc.
DIRECTORY_TRAVERSAL → ../, ..\, %2e%2e%2f, etc.
BRUTE_FORCE        → /wp-login.php, /admin/login, /login.php
MALWARE_UPLOAD     → .php, .asp, .jsp files in requests
PORT_SCAN          → nmap, masscan, zmap, nikto, sqlmap
CREDENTIAL_STUFFING → POST /wp-login, /login, /signin
DOS_ATTACK         → flood, ddos patterns
UNAUTHORIZED_ACCESS → 401/403 + admin/config/passwd
DDOS_AMPLIFICATION  → reflection, amplification, NTP/DNS
```

**Log Formats Supported:**
- Apache Combined Log Format
- fail2ban logs
- Nginx logs

**Features:**
- Parses up to 10,000+ log lines
- Auto-generates 60 realistic demo events if no logs provided
- Groups attacks by source IP
- Calculates attack frequency
- Identifies top attacking IPs
- Severity classification (CRITICAL/HIGH/MEDIUM/LOW)
- Exportable to JSON for SIEM ingestion

**Output:**
- Top 8 attacking IPs with counts
- Attack type distribution chart
- Attack timeline
- Severity breakdown
- Threat actor IP geolocation hints

---

### **MODULE 5: SECURITY POLICY GENERATOR** 📋
**Purpose:** Auto-generate security policies based on scan results

**Generated Policies:**
1. **Access Control Policy** (Role-based access, principle of least privilege)
2. **Incident Response Plan** (Detection → Containment → Recovery → Post-mortem)
3. **Backup & Disaster Recovery** (RPO/RTO targets, failover procedures)
4. **Password Policy** (Min length, complexity, rotation schedule)
5. **Patch Management** (Update schedule, testing procedures)
6. **Data Protection Policy** (Encryption standards, retention)
7. **Acceptable Use Policy** (Employee conduct guidelines)
8. **Compliance Mappings** (GDPR, HIPAA, PCI-DSS alignment)

**Output:**
- Multi-page markdown document
- DOCX-ready format
- Customizable with organization details

---

### **MODULE 6: VIRUSTOTAL REPUTATION CHECK** 🦠
**Purpose:** Get external reputation of a domain across 90+ AV engines

**VirusTotal API Integration:**
- Domain reputation scoring
- IP geolocation and ASN data
- Malicious/Suspicious/Harmless engine results
- URL malware detection
- IP address reputation

**Analyzed Metrics:**
```javascript
{
  "target": "example.com",
  "resolved_ip": "93.184.216.34",
  "ip_country": "United States",
  "ip_as_owner": "EDGECAST / Verizon",
  "registrar": "VeriSign Global Registry Services",
  "vt_reputation": 0.0,
  "total_engines": 92,
  "malicious": 0,
  "suspicious": 0,
  "harmless": 92,
  "undetected": 0,
  "ip_malicious": 0,
  "url_malicious": 0,
  "categories": { "phishing": 0, "malware": 0 }
}
```

**Verdict System:**
- 🔴 **DANGEROUS** (5+ engines flag)
- 🟡 **SUSPICIOUS** (1-4 engines flag)
- 🟢 **CLEAN** (0 engines flag)

**Output:**
- Detailed VirusTotal report
- Engine voting breakdown
- Geolocation data
- Category classifications

---

### **MODULE 7: SECURITY OVERVIEW DASHBOARD** 📈
**Purpose:** Real-time security posture summary with live data source status

**Dashboard Metrics:**
- Critical, High, Medium, Low vulnerability counts
- Security score (0-100)
- SIEM events analyzed
- VirusTotal malicious engines
- Live data source status indicators

**Live Source Status:**
- ✅ Nuclei: CLI installed?
- ✅ WPScan: API key configured?
- ✅ VirusTotal: API key configured?
- ✅ Sucuri: Ready (no auth needed)
- ✅ SecurityHeaders.com: Ready (no auth needed)
- ✅ Cloudflare: Ready (detects via headers)

**Output:**
- Color-coded metrics panels
- Source availability status
- Scan history (last 10 scans)
- Timestamp of last update

---

### **MODULE 8: AUTO SCAN (FULL PIPELINE)** ⚡
**Purpose:** Run all 6 assessment modules automatically in sequence

**Execution Order:**
1. Reconnaissance (gathers target intel)
2. Vulnerability Assessment (uses recon data)
3. Defence Configuration Check
4. SIEM Analysis
5. VirusTotal Check
6. Dashboard Update

**Features:**
- One command, zero manual steps
- Auto-saves results at each step
- Displays progress for each module
- Calculates total execution time
- Error recovery (skips failed modules, continues)

**Time Estimate:** 3-8 minutes depending on target responsiveness

**Output:**
- Complete results database
- All individual module outputs
- Ready for PDF report generation

---

### **MODULE 9: CUSTOM SCAN** 🎛️
**Purpose:** Surgical, flexible scanning with user-selected modules

**Features:**
- Choose any combination of modules
- Comma-separated module selection
- Skip unwanted checks
- Fast targeted assessments

**Example Usage:**
```
"Enter module numbers: 1,2,6"
→ Runs: Recon + Vulnerability + VirusTotal
→ Skips: Defence, SIEM, Policy
```

**Output:**
- Only selected module results
- Can be combined into PDF report

---

### **MODULE 10: PDF REPORT GENERATION** 📄
**Purpose:** Professional, stakeholder-ready security assessment report

**Report Sections:**
1. **Cover Page** (Organization, target, date, author, data sources)
2. **Executive Summary** (Key metrics table, risk ratings)
3. **Vulnerability Assessment Results** (Detailed table, top 15 vulns)
4. **Defence Configuration** (14-point check table, score)
5. **VirusTotal Reputation** (Engine breakdown, geo data, verdict)
6. **SIEM Analysis** (Event counts, severity breakdown)
7. **Recommendations** (12 actionable security improvements)

**Report Qualities:**
- Color-coded severity indicators
- Professional formatting
- CVSS scoring included
- CVE references
- Timestamp recorded
- Fully printable

**Output:**
- PDF file: `reports/report_{timestamp}.pdf`
- Suitable for C-level executive briefings

---

## 🗄️ DATA PERSISTENCE

### SQLite Database (`cyberdefence.db`)
```sql
CREATE TABLE scans (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  target TEXT,                    -- Domain/URL scanned
  module TEXT,                    -- Module name (vuln, defence, etc.)
  timestamp TEXT,                 -- ISO format datetime
  results TEXT                    -- JSON blob of results
)
```

### File Storage
- **Reconnaissance:** `data/recon/recon_{domain}_{timestamp}.json`
- **Vulnerabilities:** `data/vuln/vuln_{domain}_{timestamp}.json`
- **Defence:** `data/defence/defence_{domain}_{timestamp}.json`
- **SIEM:** `data/siem/siem_{timestamp}.json`
- **VirusTotal:** `data/virustotal/vt_{domain}_{timestamp}.json`
- **Reports:** `data/reports/report_{timestamp}.pdf`

### Audit Trail
- **Platform Log:** `data/platform.log`
- Logs all operations, errors, and API calls
- Useful for troubleshooting and compliance audits

---

## ⚙️ CONFIGURATION

### config.json
```json
{
  "wpscan_api_key": "YOUR_KEY_HERE",           // WPScan API key
  "virustotal_api_key": "YOUR_KEY_HERE",       // VirusTotal API key
  "nvd_api_key": "",                           // NVD API key (optional)
  "rate_limit_delay": 1.5,                     // Delay between API calls (seconds)
  "nuclei_templates_path": "",                 // Custom Nuclei template path
  "max_nuclei_templates": 92,                  // Max templates to run
  "request_timeout": 10                        // HTTP timeout (seconds)
}
```

### API Keys Required
- **WPScan:** Get from https://wpscan.com/api (Free token 50 reqs/day)
- **VirusTotal:** Get from https://www.virustotal.com/gui/home/upload (Free 4 domains/minute)

---

## 🚀 INSTALLATION & SETUP

### Prerequisites
```bash
# System requirements
Python 3.8+
pip3
sudo (for system package installation)
```

### Installation Steps
```bash
# 1. Clone/download project
cd cyberdefence_v31

# 2. Install Python dependencies
pip3 install -r requirements.txt --break-system-packages

# 3. Install system tools
sudo apt install nuclei python3-nmap    # Ubuntu/Debian
sudo yum install nuclei python3-nmap    # CentOS/RHEL

# 4. Configure API keys
nano config.json
# Add your WPScan and VirusTotal API keys

# 5. Run the platform
python3 cyberdefence_platform_v31.py
```

---

## 📊 USAGE EXAMPLES

### Example 1: Quick Reconnaissance
```
Menu → Select [1]
Enter target: example.com
→ 5-minute scan revealing:
  - Server software (Apache/Nginx/IIS)
  - CMS detected (WordPress, Joomla, etc.)
  - Tech stack (React, jQuery, Laravel, etc.)
  - SSL certificate validity
  - Open ports
  - Security headers assessment
→ Output: data/recon/recon_example.com_20240515_143022.json
```

### Example 2: Full Auto Scan
```
Menu → Select [8]
Enter target: wordpress-site.com
→ Runs complete 6-module pipeline (5-8 minutes)
→ Generates comprehensive results database
→ Select [10] to create final PDF report
→ Output: data/reports/report_20240515_144500.pdf
```

### Example 3: Vulnerability Focused Scan
```
Menu → Select [9] (Custom Scan)
Enter modules: 2,4
Enter target: apis.example.com
→ Runs only Vulnerability + SIEM modules
→ Fast 10-minute assessment
→ Outputs: vuln_*.json + siem_*.json
```

---

## 🔐 SECURITY BEST PRACTICES

### For Users
1. **API Keys:** Never commit `config.json` to version control
2. **Targets:** Only scan systems with authorization
3. **HTTPS:** Use only for authorized penetration testing
4. **Logs:** Review `platform.log` for suspicious activity
5. **Storage:** Encrypt the `data/` directory for sensitive reports

### For Administrators
1. Run on isolated SOC network segment
2. Implement RBAC for report access
3. Archive old reports (30+ days) to cold storage
4. Monitor API rate limits to avoid blocks
5. Regularly update Nuclei templates (`nuclei -update-templates`)

---

## 📈 PERFORMANCE METRICS

| Module | Avg Time | Concurrency | API Calls |
|--------|----------|-------------|-----------|
| Reconnaissance | 30-60s | 5-10 | ~15 |
| Vulnerability | 60-120s | 10 | ~50 |
| Defence Config | 40-90s | 3 | ~20 |
| SIEM Analysis | 10-30s | N/A | 0 |
| VirusTotal | 5-15s | 1 | 1 |
| Dashboard | 5-10s | N/A | 0 |

**Total Auto Scan Time:** 3-8 minutes (depending on network latency and API response times)

---

## 🎓 LEARNING OUTCOMES

This project demonstrates mastery in:

### Security Domain
✅ Vulnerability assessment methodologies  
✅ OWASP top 10 detection and remediation  
✅ SIEM log analysis and threat hunting  
✅ Incident response procedures  
✅ Security hardening best practices  
✅ CVE/CVSS scoring systems  

### Software Engineering
✅ Multi-module architecture design  
✅ API integration (REST, web scraping)  
✅ Database design and persistence  
✅ Concurrent HTTP requests  
✅ Error handling and logging  
✅ CLI UI/UX design (rich library)  

### DevOps & Tools
✅ Nuclei template engine  
✅ WPScan API integration  
✅ VirusTotal API usage  
✅ Nmap port scanning  
✅ SQLite database management  
✅ Log file parsing  

---

## 📚 DEPENDENCIES & LIBRARIES

| Library | Version | Purpose |
|---------|---------|---------|
| `requests` | 2.28+ | HTTP client for APIs/web scraping |
| `rich` | 13.0+ | Beautiful terminal output |
| `fpdf2` | 2.7+ | PDF report generation |
| `python-nmap` | 0.0.1+ | Port scanning wrapper |
| `nuclei` (CLI) | 3.7.1+ | Vulnerability template scanner |

---

## 🛠️ TROUBLESHOOTING

### Issue: "Nuclei not installed"
```bash
Solution: sudo apt install nuclei
Check: nuclei -version
```

### Issue: "VirusTotal API limit exceeded"
```bash
Solution: Wait 1 minute (4 requests/minute limit on free tier)
Alternative: Upgrade to VT Premium (500 req/day)
```

### Issue: "SSL certificate verification failed"
```bash
Solution: Code disables SSL verification (insecure only for testing!)
Production: Use valid certificates and enable verification
```

### Issue: "Database locked"
```bash
Solution: Close other instances accessing cyberdefence.db
Check: lsof data/cyberdefence.db
Kill: pkill -f cyberdefence_platform_v31.py
```

---

## 🎗️ COMPLIANCE FRAMEWORKS

This platform helps organizations comply with:
- **OWASP Top 10** (Web application security risks)
- **PCI-DSS** (Payment card security)
- **HIPAA** (Health data protection)
- **GDPR** (Data privacy)
- **ISO 27001** (Information security management)
- **SOC 2 Type II** (Security audit requirements)

---

## 🔮 FUTURE ENHANCEMENTS (v4.0 Roadmap)

1. **Machine Learning** - Anomaly detection in SIEM logs
2. **Web Dashboard** - Real-time monitoring interface
3. **Slack Integration** - Alert notifications
4. **AWS/GCP Support** - Cloud-native scanning
5. **GraphQL API** - Programmatic access
6. **Multi-threaded Scanner** - Parallel module execution
7. **Threat Intelligence Feed** - OSINT integration
8. **Custom Rules Engine** - User-defined detection patterns

---

## 👨‍💼 PROJECT METADATA

| Property | Value |
|----------|-------|
| **Project Type** | Cybersecurity Assessment Platform |
| **Complexity Level** | Advanced (1500+ LoC) |
| **Estimated Development Time** | 60-80 hours |
| **Test Coverage** | Manual QA on 50+ targets |
| **Deployment** | Standalone CLI + SQLite |
| **License** | Educational Use |
| **Contact** | SecuritateIT.ro |

---

## 📞 SUPPORT & DOCUMENTATION

For detailed API documentation of individual modules, see inline code comments in [cyberdefence_platform_v31.py](cyberdefence_platform_v31.py).

Each module has:
- Detailed docstrings
- Error handling
- Logging statements
- Sample output JSON schemas

---

## ✅ QUALITY CHECKLIST

- ✅ Multi-source vulnerability scanning
- ✅ Automated defence grading
- ✅ SIEM log analysis
- ✅ Professional PDF reports
- ✅ SQLite persistence
- ✅ API key management
- ✅ Rate limiting
- ✅ Rich CLI interface
- ✅ Error recovery
- ✅ Audit logging
- ✅ Modular architecture
- ✅ Documentation complete

---

**END OF DOCUMENTATION**  
*Last Updated: 2024-2025*  
*Platform: CyberDefence Analyst Platform v3.1*
