# 🛡️ CYBERDEFENCE ANALYST PLATFORM v3.1
## Complete AI Designer Prompt

---

## 📌 PROJECT BRIEF (READ THIS FIRST)

You are designing a **professional enterprise cybersecurity assessment platform** called **CyberDefence Analyst Platform v3.1**. This is a dashboard for security professionals to run automated vulnerability scans, view results, and generate PDF reports.

**Key Insight:** This is a high-density, data-driven interface for security analysts who spend 6-10 hours per day staring at dashboards. Design for clarity, speed, and professional aesthetics—NOT playful or decorative design.

**Design Philosophy:** "The Tactical Obsidian" — a high-density, authoritative environment that feels like a precision instrument carved from dark glass.

---

## 🎯 DESIGN OBJECTIVE

Create a **complete web application frontend** with **10 screens** that:
1. Enables security analysts to initiate scans with 1 click
2. Shows real-time progress during scanning
3. Displays vulnerability findings with sorting/filtering
4. Generates professional PDF reports in 2 clicks
5. Integrates 6 live security data sources
6. Works on desktop, tablet, and mobile

**Time Constraints for Users:**
- Sarah (SOC Analyst): Complete scan + report in **<10 minutes**
- Marcus (Manager): Dashboard overview in **<2 minutes**
- Priya (DevSecOps): Custom scan setup in **<5 minutes**
- James (CISO): Executive brief generation in **<3 minutes**

---

## 👥 TARGET USERS & PERSONAS

### **Persona 1: Sarah - SOC Analyst**
- **Age:** 28 | **Experience:** 4 years in security ops
- **Goal:** Run comprehensive scans on multiple targets and generate reports for management
- **Pain Point:** Currently uses 5 different tools, manually correlates data, takes 3+ hours
- **Needs:** Speed, accuracy, one-click scanning, clear findings
- **Success Metric:** Complete assessment in <10 minutes with confidence

### **Persona 2: Marcus - Security Manager**
- **Age:** 42 | **Experience:** 10 years, now managing team
- **Goal:** Monitor security posture across 20+ assets, track trends, make budgeting decisions
- **Pain Point:** No unified visibility, manual reporting, slow updates
- **Needs:** Dashboard overview, historical comparison, professional reports for board
- **Success Metric:** See security status at a glance, generate report for C-suite

### **Persona 3: Priya - DevSecOps Engineer**
- **Age:** 26 | **Experience:** Automation-focused, infrastructure security
- **Goal:** Integrate security scanning into CI/CD pipeline, quickly assess API security
- **Pain Point:** Tools not modular, hard to customize, no good JSON export
- **Needs:** Custom scan workflows, API-friendly outputs, quick results
- **Success Metric:** Run selected modules, export JSON for CI/CD integration

### **Persona 4: James - CISO**
- **Age:** 55 | **Experience:** 20 years, C-level executive
- **Goal:** Make strategic security decisions, allocate budget, understand risk
- **Pain Point:** Too much technical jargon, unclear priorities, vendor lock-in
- **Needs:** Executive summary, clear risk levels, actionable recommendations
- **Success Metric:** 1-page executive brief with risk/mitigation trade-offs in 5 minutes

---

## 📊 DESIGN SYSTEM: "TACTICAL OBSIDIAN"

### **Color Palette**

Use **dark mode only** for eye strain reduction during long watches.

| Color | Hex | RGB | Use Case | Example |
|-------|-----|-----|----------|---------|
| Critical/Alert | #DC2626 | 220, 38, 38 | 🔴 CRITICAL vulnerabilities | "WordPress RCE" badge |
| High/Urgent | #EF4444 | 239, 68, 68 | 🔴 HIGH severity findings | "SQL Injection" |
| Medium/Warning | #FBBF24 | 251, 191, 36 | 🟡 MEDIUM priority alerts | "Missing headers" |
| Low/Safe | #34D399 | 52, 211, 153 | 🟢 LOW severity, safe status | "Configuration OK" |
| Success/Verified | #45dfa4 | 69, 223, 164 | ✅ Passed checks, verified | API "Connected" badge |
| Primary Blue | #3B82F6 | 59, 130, 246 | CTAs, active states | "Start Scan" button |
| Dark Blue (Primary Container) | #2563eb | 37, 99, 235 | Hover state, filled buttons | Button pressed |
| Light Primary | #b4c5ff | 180, 197, 255 | Accent, thin strokes | Progress bar color |
| Background (Darkest) | #0b1326 | 11, 19, 38 | Base surface | Page background |
| Surface | #131b2e | 19, 27, 46 | Card backgrounds | Module containers |
| Surface High | #222a3d | 34, 42, 61 | Hovered/active cards | Selected scan |
| Surface Highest | #2d3449 | 45, 52, 73 | Maximum elevation | Modal background |
| Text Primary | #dae2fd | 218, 226, 253 | Main body text | Scan results |
| Text Secondary | #c3c6d7 | 195, 198, 215 | Secondary info, labels | Timestamps, hints |
| Text Muted | #8d90a0 | 141, 144, 160 | Disabled text, hints | "Not available" |
| Border Ghost | #434655 | 67, 70, 85 | 15% opacity only | Faint dividers |

**Critical Rule:** Do NOT use 1px solid borders. Instead, define boundaries through background color shifts (surface-to-surface-container layers).

### **Typography**

**Font Family:** Inter (or Roboto, system sans-serif as fallback)

| Level | Size | Weight | Line Height | Letter Spacing | Use Case |
|-------|------|--------|-------------|---|----------|
| **Display Large** | 32px | 700 | 1.2 | -0.02em | Main page titles (rare) |
| **Display Med** | 28px | 700 | 1.25 | -0.015em | Module section headers |
| **Headline Large** | 24px | 700 | 1.3 | 0 | Dashboard title "Tactical Overview" |
| **Headline Med** | 20px | 600 | 1.4 | 0 | Card titles, modal headers |
| **Headline Small** | 18px | 600 | 1.4 | 0 | Subsection titles "Security Score" |
| **Title Large** | 16px | 600 | 1.5 | 0.01em | Table headers, secondary headers |
| **Title Small** | 14px | 600 | 1.5 | 0.01em | Card section titles |
| **Body Large** | 16px | 400 | 1.5 | 0 | Primary scan results data |
| **Body Med** | 14px | 400 | 1.5 | 0.025em | Workhorse text (most content) |
| **Body Small** | 12px | 400 | 1.5 | 0.04em | Secondary data, timestamps |
| **Label Large** | 12px | 600 | 1.25 | 0.05em | Buttons, labels (all-caps) |
| **Label Med** | 11px | 600 | 1.3 | 0.05em | Tags, badges, metadata |
| **Label Small** | 10px | 600 | 1.5 | 0.125em | High-density tables, small status |

**Contrast Rule:** All text must have 4.5:1 contrast ratio (WCAG AA) against its background.

### **Spacing Scale (8px base)**

```
xs: 4px    (tight spacing between icon + text)
sm: 8px    (default padding)
md: 16px   (section spacing)
lg: 24px   (container padding)
xl: 32px   (major sections)
2xl: 48px  (dashboard grid gaps)
```

### **Border Radius**

```
none: 0px              (sharp edges, tactical)
sm: 2px                (inputs, tight elements)
md: 4px                (cards, buttons, standard)
lg: 6px                (modals, containers)
full: 9999px           (badges, circular buttons)
```

### **Shadows (Tonal Elevation)**

```
Elevation 1: 0 1px 2px rgba(0,0,0,0.05)           (subtle dividers)
Elevation 2: 0 2px 4px rgba(0,0,0,0.1)            (hovered cards)
Elevation 3: 0 4px 8px rgba(0,0,0,0.15)           (cards, modals)
Elevation 4: 0 8px 16px rgba(0,0,0,0.2)           (floating dropdowns)
Ambient: 0 0 32px rgba(0, 83, 219, 0.08)          (primary-tinted shadow)
Focus: 0 0 0 3px rgba(59,130,246,0.1)             (focus ring on buttons/inputs)
```

---

## 📐 RESPONSIVE BREAKPOINTS

| Device | Width | Layout | Columns | Screen Type |
|--------|-------|--------|---------|------------|
| Mobile | 375px | Single column stack | 1 | Portrait phones |
| Tablet | 768px | 2 column | 2 | iPad, tablets |
| Desktop | 1024px | Full grid | 3-4 | Monitors |
| Ultra-wide | 1920px | Maximum density | 4+ | Large displays |

**Mobile-Specific:**
- Button height: 56px minimum
- Tap target: 44px minimum
- Full-width inputs
- Bottom action sheets instead of center modals
- Swipeable tabs

---

## 🎮 COMPLETE SCREEN SPECIFICATIONS

### **SCREEN 1: LANDING DASHBOARD**

**Purpose:** First screen users see when opening app — security posture snapshot

**Layout:** 
- Top: Navigation bar + user profile
- Left: Sidebar navigation (collapsible on mobile)
- Main: Dashboard grid

**Components to Include:**

1. **Top Navigation Bar (Fixed, Sticky)**
   - Left: Logo "🛡️ CYBERDEFENCE v3.1"
   - Center: Breadcrumb "DASHBOARD"
   - Right: 
     - 🔔 Notifications bell (badge with count if alerts)
     - 🌙 Dark/Light toggle (currently dark only)
     - ⚙️ Settings icon
     - 👤 User avatar (circle with initials/photo)

2. **Left Sidebar Navigation**
   - Sections:
     - "COMMAND CENTER" (label)
       - 📊 DASHBOARD (highlighted in blue)
       - 🔍 SCANS
       - 📋 REPORTS
       - ⚙️ SETTINGS
   - Bottom:
     - 📚 Documentation
     - 🚪 Log Out

3. **Main Content: KPI Overview Cards**
   - Grid layout: 4 columns (desktop), 2 (tablet), 1 (mobile)
   - Card 1: "🔴 CRITICAL THREATS"
     - Large number: 12
     - Subtitle: "-2 from last 24h" (with trend arrow)
     - Border-left: Red (#DC2626)
   - Card 2: "🔴 HIGH RISK"
     - Large number: 45
     - Subtitle: "+1 last 24h"
     - Border-left: Red (#EF4444)
   - Card 3: "🟡 MEDIUM ALERTS"
     - Large number: 89
     - Subtitle: "-5% vs last 24h"
     - Border-left: Amber (#FBBF24)
   - Card 4: "🟢 LOW PRIORITY"
     - Large number: 234
     - Subtitle: "Background noise"
     - Border-left: Green (#34D399)

4. **Security Score Card (Prominent)**
   - Title: "SECURITY HEALTH SCORE"
   - Large circular gauge showing 78/100
     - Gauge background: Surface container
     - Gauge fill: Blue gradient from #b4c5ff to #2563eb
     - Center text: "78" (large), "/100" (small)
   - Assessment: "⚠️ Acceptable - Configuration aligns with 72% of Tier-1 Security Standards"
   - Color indicator:
     - >80 = Green (Good)
     - 60-80 = Yellow (Acceptable)
     - <60 = Red (Poor)

5. **Live Data Source Status Grid**
   - Title: "LIVE DATA SOURCE STATUS"
   - 2x3 grid of status cards:
     - Nuclei v3.7.1: ✅ Connected | Ready | "92 templates loaded"
     - WPScan API: ✅ Connected | Ready | "Latest CVEs active"
     - VirusTotal: ✅ Connected | Ready | "90+ engines checking"
     - Sucuri SiteCheck: ✅ Connected | Ready | "No key required"
     - SecurityHeaders.com: ✅ Connected | Ready | "Grade A-F active"
     - Cloudflare CF-RAY: ✅ Connected | Ready | "WAF detection active"
   - Each card shows: Icon + Name + Status badge (✅ green or ❌ red)

6. **SIEM Metrics Bar**
   - 4 metrics in a row:
     - SIEM Events Today: 2,450 (blue text)
     - Threats Neutralized: 14 (green)
     - Active Monitors: 18/20 (yellow if not all active)
     - Integration Health: 83% (shows bar)

7. **VirusTotal Quick Status**
   - Badge: "🟢 VIRUSTOTAL REPUTATION: CLEAN"
   - Subtitle: "No malicious detections across 94 engines"

8. **Quick Action Buttons (Prominent CTA Area)**
   - Grid of 3 large buttons:
     - [⚡ AUTO SCAN] → Full 6-module pipeline
     - [🎛️ CUSTOM SCAN] → User selects modules
     - [📊 VIEW HISTORY] → Historical results

9. **Scan History Table**
   - Title: "LAST 10 SCANS"
   - Columns: TARGET ASSET | TIMESTAMP | SCORE | VULNS | STATUS | ACTIONS
   - Example rows:
     - api-gateway-v4.prod.sec | Oct 24, 14:32 | 42 | 2⚠️ 5🔴 | COMPLETED | [View]
     - auth-node-west-01 | Oct 24, 13:15 | 86 | 0⚠️ 0🔴 | COMPLETED | [View]
     - internal-erp-bridge | Oct 24, 12:11 | — | — | PROCESSING... | [Cancel]
   - Footer: "DOWNLOAD FULL CSV" button

**Design Notes:**
- Dark background (#0b1326)
- Cards with 1-2px shadow on hover
- Color severity consistently used (🔴🟡🟢)
- No 1px borders, only tonal layers
- Mobile: Stack cards vertically
- Animations: Smooth fade-in, no bouncing

---

### **SCREEN 2: NEW SCAN MODAL**

**Purpose:** Initiate a new security scan

**Trigger:** Click [AUTO SCAN] or [CUSTOM SCAN] from dashboard

**Layout:** Centered modal, 500px width (full-width on mobile)

**Components:**

1. **Modal Header**
   - Title: "✨ NEW SECURITY SCAN"
   - Subtitle: "PROTOCOL V3-ALPHA"
   - Close button (X) top-right

2. **Target Input Section**
   - Label: "PRIMARY TARGET"
   - Input field: "https://example.com or 192.168.1.1"
   - Helper text: "Supports domains, IPv4 and IPv6 ranges"
   - Validation:
     - Green checkmark when valid domain detected
     - Red error: "Invalid domain format"

3. **Scan Mode Selection**
   - Label: "OPERATIONAL MODE"
   - 4 radio button options (selected state = highlighted with border):
     - ⚡ **Quick** - "Reconnaissance only (5 min)"
     - ◑ **Standard** - "Recon + Weak Spots (12 min)"
     - ✖ **Comprehensive** - "Full audit, all 6 modules (25 min)"
     - ⚙ **Custom** - "Choose your modules below"

4. **Active Modules Checkbox Grid**
   - Label: "ACTIVE MODULES" + Badge "6 SELECTED" (in blue)
   - 2x3 grid:
     - ☑ Port Discovery
     - ☑ SSL/TLS Audit
     - ☑ Asset Mapping
     - ☑ DNS Analysis
     - ☑ OSINT Sweep
     - ☑ SQLI Probe
   - When "Quick" selected: Only "Port Discovery" checked
   - When "Standard": Port + SSL + Asset checked
   - When "Comprehensive": All 6 checked
   - When "Custom": User controls

5. **API Source Authentication Status**
   - Label: "API SOURCE AUTHENTICATION"
   - List of sources with status:
     - Shodan Intelligence: ✅ Verified (green text + checkmark)
     - VirusTotal API: ✅ Verified
     - BinaryEdge Engine: ✅ Verified
     - HaveIBeenPwned: ✅ Verified
     - Censys Data: ✅ Verified
     - (Show first 5, "...1 more" if more than 5)
   - If any API fails:
     - VirusTotal API: ❌ Error (red text)
     - Helper: "API key expired. [EDIT KEY] to fix"

6. **Action Buttons (Bottom of modal)**
   - Left: [CANCEL] (transparent button)
   - Right: [START SCAN →] (primary blue button, filled)
   - Button disabled if:
     - No target entered
     - Required API keys missing

**Interactions:**
- Smooth 300ms modal slide-up animation
- Form validation on blur (real-time)
- "Start Scan" button changes to loading state with spinner
- Modal closes and transitions to live progress screen

---

### **SCREEN 3: LIVE SCAN PROGRESS TRACKER**

**Purpose:** Show real-time progress during active scan

**Layout:**
- Top: Target info + stop controls
- Middle: KPI metrics dashboard
- Center: Module progress timeline
- Right: System console (optional tech view)
- Bottom: [Pause] [Cancel] buttons

**Components:**

1. **Scan Header (Top Bar)**
   - Status badge: "🟡 SCAN IN PROGRESS: EXAMPLE.COM"
   - Session info: "SESSION ID: x9-224-BETA • TARGET.IP: 192.168.1.1"
   - Controls: [⏸️ PAUSE] [🔴 CANCEL] (top-right)

2. **KPI Dashboard (4-column grid)**
   - Card 1: "OVERALL SYSTEM PROGRESS"
     - Large bar: 42% filled (blue)
     - Percentage: "42%"
   - Card 2: "THREATS NEUTRALIZED"
     - Number: 14 (green)
     - Icon: 🛡️
   - Card 3: "OPEN PORTS FOUND"
     - Number: 122 (blue)
     - Icon: 🔌
   - Card 4: "DATA THROUGHPUT"
     - Speed: "4.2 GB/s" (bright text)
     - Icon: ⚡

3. **Module Progress Timeline (Vertical)**
   - Each module as a progress step:
     ```
     ✅ MODULE 01: RECONNAISSANCE
        Configuration, WHOIS enumeration and sub-domain discovery completed
        (Green checkmark, collapsed)

     🔄 MODULE 02: VULNERABILITY ASSESSMENT (65% COMPLETE)
        Executing tactical payload simulations and CVE mapping
        [████████░░░░░░░░░░] 65%
        - Sub-task 1: ✅ Nuclei templates running (25/92)
        - Sub-task 2: ⏳ WPScan checking WordPress plugins...
        - Sub-task 3: ⏳ NVD scoring vulnerabilities...

     ⏳ MODULE 03: EXPLOIT VERIFICATION (AWAITING)
        Awaiting completion of previous module sequences

     ⏳ MODULE 04: PRIVILEGE ESCALATION (AWAITING)
     ⏳ MODULE 05: REPORT SYNTHESIS (AWAITING)
     ⏳ MODULE 06: ARTIFACT PURGE (AWAITING)
     ```
   - Timeline line on left side connecting all modules
   - Colors: ✅ Green, 🔄 Blue, ⏳ Gray

4. **Estimated Time Remaining**
   - Text: "ESTIMATED TIME REMAINING: ~4:38 MINUTES"
   - Updates in real-time

5. **System Console (Optional, bottom-right)**
   - Title: "SYSTEM CONSOLE"
   - Log output:
     ```
     [SKIP123] Recon module completed at 62.1s
     [SKIP124] Starting OSINT scan
     [SKIP125] Parallel port 22... [open]
     [ERROR] Timeout on port 443... [RETRY]
     ```
   - Dark background (#060e20)
   - Monospace font, small text (#8d90a0)
   - Close button (X) collapses console

**Interactions:**
- Real-time updates (WebSocket or polling)
- Progress bars animate smoothly
- Module steps collapse/expand on click for details
- [Pause] temporarily halts scan
- [Cancel] shows confirmation: "Stop scan and discard results?" [No] [Yes]

---

### **SCREEN 4: VULNERABILITY RESULTS VIEW**

**Purpose:** Display detailed vulnerability findings from completed scan

**Layout:**
- Top: Summary cards
- Middle: Tabbed interface
- Main: Results table with expandable rows
- Bottom: Export/Report actions

**Components:**

1. **Summary Cards (Top Row, 4 columns)**
   - Card 1: "🔴 CRITICAL" + "2" (in red)
   - Card 2: "🔴 HIGH" + "5" (in red)
   - Card 3: "🟡 MEDIUM" + "12" (in amber)
   - Card 4: "🟢 LOW" + "8" (in green)

2. **Tab Navigation (Under summary)**
   - Tabs: [VULNERABILITIES] [DEFENCE CONFIG] [VIRUSTOTAL] [SIEM] [RAW DATA]
   - Active tab underlined in blue
   - Smooth 200ms fade between tab content

3. **Data Table (Main Content)**
   - Columns: # | VULN NAME | SOURCE | CONFIRMED | SEVERITY | CVSS | CVE
   - Sortable: Click column header to sort
   - Pagination: "Showing 1-10 of 27 vulnerabilities" + [Previous] [1] [2] [3] [Next]
   - Rows:
   ```
   # 1 | WordPress RCE (Remote Code Execution)
        | Manual Check ✓ | YES ✓ | 🔴 CRITICAL | 9.8 | CVE-2024-8451
   
   # 2 | SQL Injection Vulnerability
        | DAST Scanner | YES ✓ | 🔴 HIGH | 8.4 | CVE-2024-8432
   
   # 3 | SSL Certificate Expired
        | External Verify | YES ✓ | 🟡 MEDIUM | 5.3 | N/A
   ```

4. **Expandable Rows (Click to expand)**
   - Shows detailed finding with sections:
     - **Evidence:** "GET /wp-content/plugins/index.php responded with 200 OK..."
     - **Remediation Steps:**
       1. Update WordPress to latest version
       2. Disable unnecessary plugins
       3. Enable automatic security updates
     - **External References:** [CVE-2024-8451] [NVD Link] [CyberDefence Blog]

5. **Row Styling (Color-coded by Severity)**
   - Background slightly tinted with severity color (15% opacity)
   - Border-left: Full severity color
   - Hover: Slightly lighter background, shadow

6. **Pagination Controls**
   - Rows per page dropdown: 10 / 25 / 50
   - Current page indicator

7. **Action Buttons (Bottom)**
   - [📋 EXPORT JSON] (gray button, left)
   - [💾 SAVE TO HISTORY] (gray button, center)
   - [📄 GENERATE REPORT] (primary blue button, right)

8. **Performance Stats (Footer, subtle)**
   - "SCAN PERFORMANCE | QUALITY: 122-441 | CONFIDENCE: 89.2%"
   - "⚠️ THREAT INTELLIGENCE ADVISORY: Your environment is currently showing vulnerabilities associated with APT-28. We recommend immediate audit of administrative credentials and enabling enhanced SIEM..."

---

### **SCREEN 5: DEFENCE CONFIGURATION ASSESSMENT**

**Purpose:** Show security hardening grade and recommendations

**Layout:**
- Left: Large score gauge
- Right: 14-point checklist + recommendations

**Components:**

1. **Score Gauge (Left side, 40% width)**
   - Large circular gauge showing 72/100
   - Gauge color: Blue gradient inside, gray background
   - Center text:
     ```
     72
     SCORE/100
     ```
   - Below gauge: Badge "⚠️ Acceptable"
     - Color based on score:
       - 80+: Green "Good"
       - 60-80: Yellow "Acceptable"
       - <60: Red "Poor"
   - Subtitle: "Configuration aligns with 72% of Tier-1 Security Standards"

2. **Pass/Fail Summary (Under gauge)**
   - ✓ 10 PASS (green)
   - ✗ 2 FAIL (red)
   - △ 2 WARN (yellow)

3. **14-Point Defence Checklist (Right side, 60% width)**
   - Title: "14-POINT DEFENCE CHECKLIST" | "Full Coverage: 100%"
   - Table columns: CHECK NAME | REQUIREMENT | STATUS | DETAILS
   - Rows (each 44px height):
   ```
   Encrypted EBS
   Volumes          | AES-256      | ✅ PASS | All 42 active volumes verified

   IAM Password
   Policy           | Min 14 chars | ❌ FAIL | Current policy allows 8 chars

   Network ACL
   Ingress          | Port 22 restricted | ✅ PASS | SSH open to staging VPCs only

   VPC Flow Logs    | Enabled all  | ✅ PASS | Active monitoring active

   RDS Public
   Access           | PublicAccess | ✅ PASS | No instances exposed
                      = False

   MFA Active
   Status           | All users    | ❌ FAIL | 4 accounts missing hardware 2FA

   Root Account
   Use              | 0 usage logs | ✅ PASS | No root logins in 365 days

   Unused
   Credentials      | Disable if   | ✅ PASS | 3 keys rotated for 90 days
                      90d unused

   [+ 6 more checks below]
   ```

4. **Status Badge Styling**
   - ✅ PASS: Green (#45dfa4) background, green text
   - ❌ FAIL: Red (#DC2626) background, light text
   - △ WARN: Yellow (#FBBF24) background, dark text

5. **Critical Recommendations Section**
   - Title: "CRITICAL RECOMMENDATIONS"
   - Bulleted list (4 items):
     ```
     1. 🔴 Enable MFA Enforcement
        Enforce multi-factor authentication on all user accounts
        Priority: CRITICAL | Effort: 2 hours

     2. 🔴 Rotate Root API Keys
        Primary keys have exceeded 90-day rotation threshold
        Priority: CRITICAL | Effort: 1 hour

     3. 🟡 Enable CloudTrail Logging
        Global region logging is disabled in US-EAST-1
        Priority: MEDIUM | Effort: 30 mins

     4. 🟡 Restrict S3 Public Access
        Check open to staging VPCs, which is allowed
        (more items...)
     ```

6. **Compliance Trends (Bottom)**
   - Left: "COMPLIANCE DRIFT (30 DAYS)" + 30-day bar graph showing score trend
   - Right: "GLOBAL RANK" + badge "Top 15% | +2.4% vs last week"

7. **Action Button**
   - Large button bottom-left: [🚀 DEPLOY COUNTERMEASURE]

---

### **SCREEN 6: VIRUSTOTAL REPUTATION REPORT**

**Purpose:** External reputation analysis across 90+ antivirus engines

**Layout:**
- Top: Large verdict badge
- Middle: Metadata + detection breakdown
- Bottom: Individual engine results

**Components:**

1. **Verdict Badge (Prominent, centered)**
   - Status icon: 🟢 (if clean), 🟡 (if suspicious), 🔴 (if dangerous)
   - Text: "CLEAN" | "SUSPICIOUS" | "DANGEROUS"
   - Subtitle: "0 DETECTIONS / 94 ENGINES ANALYZED"
   - Description: "This file has been cross-referenced across our global threat intelligence network. No malicious signatures or suspicious behavioral patterns were detected."

2. **Metadata & Infrastructure Section**
   - 4-column layout:
     - **RESOLVED IP:** 104.26.11.144
     - **COUNTRY:** United States 🇺🇸
     - **ASN:** AS13335 CLOUDFLARE
     - **REGISTRAR:** GoDaddy.com, LLC

3. **Detection Breakdown (Horizontal bar visualization)**
   - Bar segments showing proportion:
     - 82 Harmless (green)
     - 12 Suspicious (yellow)
     - 0 Malicious (red)
     - 0 Undetected (gray)
   - Numbers below each segment

4. **Classification Breakdown (4-column grid)**
   - **MALWARE:** 0% ✅
   - **PHISHING:** 0% ✅
   - **BOTNET:** 0% ✅
   - **SPYWARE:** 0% ✅

5. **Engine Analysis Breakdown**
   - Title: "ENGINE ANALYSIS BREAKDOWN"
   - Grid of engine badges (5 per row):
     ```
     Kaspersky    CLEAN       Avast       CLEAN       McAfee      CLEAN
     CrowdStrike  CLEAN       SentinelOne CLEAN       BitDefender CLEAN
     Microsoft    CLEAN       Sophos      CLEAN       TrendMicro  CLEAN
     Defender
     ESET-NOD32   CLEAN       Malwarebytes CLEAN      FireEye     CLEAN
     [+79 more engines...]
     ```
   - Each badge: Engine name in light text, verdict in green/red

6. **Action Buttons (Top-right)**
   - [👁️ VIEW FULL REPORT]
   - [📥 EXPORT]

---

### **SCREEN 7: SIEM THREAT ANALYSIS DASHBOARD**

**Purpose:** Log analysis and attack pattern detection from 1,247 events

**Layout:**
- Top: KPI metrics
- Middle: Attack patterns + top IPs side-by-side
- Bottom: Recommendations

**Components:**

1. **Critical Metrics KPI (4 columns)**
   - Card 1: "🔴 CRITICAL"
     - Large number: 42
     - Trend: "-8% from last 24h" (green down arrow)
     - Details: "Last hit: 2 hours ago"
   - Card 2: "🔴 HIGH"
     - Large number: 128
     - Trend: "Stable" (dash)
   - Card 3: "🟡 MEDIUM"
     - Large number: 592
     - Trend: "-5% vs last 24h" (green)
   - Card 4: "🟢 LOW"
     - Large number: 1.2k
     - Trend: "System automated"

2. **Primary Threat Alert (Prominent card, full width)**
   - Title: "PRIMARY VECTOR"
   - Alert: 🔴 "Brute Force Attempt"
   - Description: "Repetitive SSH authentication failures detected from multiple subnets targeting production cluster alpha-01."
   - "ACTIVE THREAT | 1.3 PRIORITY" (red badge)
   - [View Details] link

3. **Attack Patterns Detected (Left side, 50% width)**
   - Title: "ATTACK PATTERNS DETECTED"
   - List with hit counts and severity:
     ```
     • SQL Injection         284 hits    🔴 CRITICAL
     • XSS Attack           102 hits    🔴 CRITICAL
     • Directory Traversal   85 hits    🔴 HIGH
     • Unauthorized API Call 62 hits    🔴 HIGH
     • Credential Stuffing  1,204 hits  🟡 MEDIUM
     • Port Scanning        4,832 hits  🟡 MEDIUM
     • Session Hijacking     32 hits    🟡 MEDIUM
     • Slowloris DoS         4 hits     🟢 LOW
     • Malformed Packet     1,241 hits  🟢 LOW
     • Bot Crawling        15,821 hits  🟢 LOW
     ```
   - Each row clickable to expand details

4. **Top Attacking IPs (Right side, 50% width)**
   - Title: "TOP ATTACKING IPS"
   - Table:
     ```
     SOURCE IP        | GEOLOCATION    | ATTACK COUNT | RISK LEVEL
     192.168.4.12     | Moscow, RU     | 14,283       | 9.8/10 🔴
     45.22.198.5      | Shenzhen, CN   | 12,811       | 9.4/10 🔴
     183.4.1-25       | Seoul, KR      | 8,401        | 8.1/10 🟡
     182.1.22.9       | Singapore, SG  | 6,220        | 7.5/10 🟡
     88.2.19.44       | Berlin, DE     | 4,119        | 5.2/10 🟡
     211.5.88.11      | Tokyo, JP      | 3,992        | 4.8/10 🟡
     15.90.1.281      | Ashburn, US    | 2,118        | 3.1/10 🟢
     172.16.8.55      | Internal Subnet| 1,852        | 🌐(internal)
     ```
   - Rows colored by risk level
   - Click row to see detailed attack history

5. **Actionable Intelligence & Recommendations (Bottom)**
   - Title: "ACTIONABLE INTELLIGENCE & RECOMMENDATIONS"
   - Bulleted list:
     - 🔴 Block IP 192.168.4.12 immediately (187 SQL injections from same source)
     - 🟡 Enable CAPTCHA on /login endpoint (234 credential stuffing from bot nets)
     - 🟡 Investigate 8 malware upload attempts (all from Moscow region)
     - 🟡 Activate DDoS protection (67 DoS + 15 amplification events detected)

6. **Action Button (Bottom-left)**
   - Large blue button: [🚀 DEPLOY COUNTERMEASURE]

---

### **SCREEN 8: PDF REPORT GENERATOR**

**Purpose:** Build and preview professional security report

**Layout:**
- Left: Metadata form
- Right: Live PDF preview + compilation progress

**Components:**

1. **Metadata Configuration Form (Left, 40%)**
   - Title: "REPORT ENGINE"
   - Subtitle: "Intelligence Generator"
   - Input fields:
     ```
     METADATA CONFIGURATION
     
     ORGANIZATION NAME
     [Aegis Global Logistics________________]
     
     PRIMARY TARGET / ASSET ID
     [ASSET-V72-NETWORK-CORE______________]
     
     REPORT AUTHOR
     [Senior Analyst J. Vance_____________]
     
     REFERENCE DATE
     [05/24/2024] [calendar icon]
     ```

2. **Live Document Preview (Right, 60%)**
   - Header: "Live Document Preview  PAGE 1/2" + [< › >] navigation
   - Document preview area showing PDF mockup:
     ```
     [White preview area showing:]
     
     CONFIDENTIAL
     
     INTELLIGENCE REPORT
     
     Assessment &
     Network Integrity
     Analysis
     
     ---
     
     [PAGE 2 shows:]
     
     EXECUTIVE SUMMARY        [DATE: JUN 15, 2024]
     
     HIGHLEVEL OVERVIEW
     
     The following assessment highlights
     significant vulnerabilities detected
     within the analysis period of 2-2024...
     
     CRITICAL FINDINGS
     
     RCE VULN OR
     Remote code execution possibility...
     ```

3. **Compiler Status (Below preview)**
   - Progress bar: [████████░░] 70% COMPLETED
   - Status steps:
     ```
     ✅ Injecting metadata parameters...
     ✅ Generating automated summary maps...
     ⏳ Building executive summary...
     ◯ Finalizing threat profiles (pending)
     ```

4. **Output Action Buttons**
   - [👁️ VIEW FULL PDF] (gray)
   - [⬇️ DOWNLOAD] (primary blue, highlighted)
   - [📧 EMAIL] (gray)
   - [✏️ EDIT META] (gray)

---

### **SCREEN 9: REPORTS HISTORY**

**Purpose:** Access and audit comprehensive security assessment logs

**Layout:**
- Top: High-level stats
- Middle: Archive table with filters
- Bottom: Pagination + system intelligence

**Components:**

1. **High-Level Statistics Cards (3 columns)**
   - Card 1: "TOTAL REPORTS"
     - Large number: 1,248
     - Trend: "+12%" (green arrow)
   - Card 2: "AVERAGE SECURITY GRADE"
     - Grade: B+ (in yellow box)
     - Score: "88.4 / 100"
     - Trend bar
   - Card 3: "VULNS FOUND (30D)"
     - Number: 42
     - Trend: "-4%" (green)

2. **Filter Controls (Top of table)**
   - Left to right:
     - "DATE RANGE:" dropdown "Last 30 Days ▼"
     - "SCORE:" dropdown "All Grades ▼"
     - "TARGET DOMAIN:" search input "Search..."

3. **Archive Table (Main)**
   - Columns: ID | TARGET ENTITY | DATE ANALYZED | SECURITY SCORE | RISK DISTRIBUTION | ACTIONS
   - Rows (example data):
     ```
     #REP-5942 | corp-main-server.io      | Oct 24, 2023 14:32 | Grade A [green]   | ⚫⚫○○○ | [View]
     #REP-5938 | api-gateway-v3.internal  | Oct 23, 2023 09:15 | Grade F [red]     | ⚫⚫⚫⚫⚫ | [View]
     #REP-5931 | legacy-vault.db          | Oct 21, 2023 18:00 | Grade C [yellow]  | ⚫⚫⚫○○ | [View]
     #REP-5925 | cdn-edge-04.global       | Oct 20, 2023 23:11 | Grade B [yellow]  | ⚫⚫○○○ | [View]
     #REP-5919 | dev-stack-registry       | Oct 24, 2023 12:22 | Grade A [green]   | ⚫○○○○ | [View]
     ```
   - Risk Distribution: Colored dots representing risk profile
   - Sortable columns: Click header to sort

4. **Pagination**
   - Bottom: "SHOWING 1-10 OF 1,248"
   - Controls: [‹ Previous] [1] [2] [3] ... [Next ›]

5. **Export & Actions**
   - Top-right:
     - [⬇️ EXPORT CSV]
     - [+ MANUAL REPORT]

6. **System Intelligence Box (Bottom, subtle)**
   - Title: "SYSTEM INTELLIGENCE"
   - Text: "Analysis suggests a 94% improvement in edge-case vulnerability detection since the v3.1 update last week. Manual audits are recommended for 3 identified internal subnets."
   - Icon: 💡 (info)

---

### **SCREEN 10: SETTINGS & API INTEGRATIONS**

**Purpose:** Configure platform settings, manage API keys, user profile

**Layout:**
- Left: Sidebar tabs
- Center: Settings content
- Right: Profile card + integration health

**Components:**

1. **Settings Header**
   - Title: "Settings"
   - Subtitle: "SYSTEM CONFIGURATION"
   - Search field: 🔍 "Search parameters..."

2. **Tab Navigation (Left sidebar)**
   - [ Profile ]
   - [ API Integrations ] (highlighted)
   - [ Security ]
   - [ Notifications ]

3. **Content Area: API Integrations**

   **Section: External Threat Intel Feeds**
   - Subtitle: "Configure third-party APIKeys for automated threat hunting."
   - Badge: "5 SERVICES ACTIVE" (blue)

   **Integration Items (vertical list):**
   ```
   [Icon] Nuclei
   Template-based vulnerability scanner
   ✅ Connected                         [EDIT KEY]
   
   [Icon] WPScan
   WordPress vulnerability database
   ✅ Connected                         [EDIT KEY]
   
   [Icon] VirusTotal
   Malware analysis and sandbox
   ❌ Error                             [EDIT KEY] (red)
   Hint: "API key expired. Update to restore service."
   
   [Icon] Sucuri
   Website security & firewall engine
   ✅ Connected                         [EDIT KEY]
   
   [Icon] SecurityHeaders
   HTTP response header analysis
   ✅ Connected                         [EDIT KEY]
   
   [Icon] Cloudflare
   Edge protection & DNS audit logs
   ✅ Connected                         [EDIT KEY]
   ```

   Each integration shows:
   - Service name + icon
   - Description
   - Status indicator (✅ green or ❌ red)
   - Edit key button

4. **Integration Health (Right sidebar)**
   - Title: "INTEGRATION HEALTH"
   - Large percentage: 83%
   - Trend: "+5% from last week" (green)
   - Circular progress indicator (83% filled)
   - System message:
     ```
     "System performance is optimized. 
     One API disruption detected in the 
     last 24h. Manual re-sync recommended 
     for VirusTotal node."
     ```

5. **Profile Card (Right sidebar, below health)**
   - Avatar: Circle with initials/photo
   - Name: "Kaelen Vance"
   - Title: "LEAD THREAT ANALYST"
   - Email: "k.vance@cyberdefence.pro"
   - Security Status: "✅ Two-Factor Auth Enabled"
   - System Access: "Alpha-Cluster-09 (Primary)"
   - Button: [UPDATE PROFILE]

6. **Bottom Action**
   - Large blue button (full width at bottom-left):
     - [+ NEW SCAN] (always available)

---

## 📱 RESPONSIVE BEHAVIOR

**Desktop (1024px+):**
- 2-3 column layouts
- Side-by-side data visualization
- Full tables visible
- Sidebar always visible

**Tablet (768px):**
- Single column stacked layout
- Tables become collapsible cards
- Sidebar collapses to hamburger menu
- Full-width inputs

**Mobile (375px):**
- Single column, full-width
- Modals as bottom sheets
- Large tap targets (56px)
- Swipeable tabs
- Hamburger menu for navigation

---

## 🎯 DATA EXAMPLES (Use Real Data)

### **Vulnerability Example:**
```json
{
  "id": 1,
  "name": "WordPress RCE Remote Code Execution",
  "severity": "CRITICAL",
  "cvss": 9.8,
  "cve": "CVE-2024-8451",
  "source": "manual_check",
  "confirmed": true,
  "evidence": "WordPress 5.9 detected in meta tag",
  "remediation": "Update to latest WordPress version (6.4+)",
  "detected_at": "2024-10-24T14:32:00Z"
}
```

### **Scan History Example:**
```json
{
  "id": 42,
  "target": "api-gateway-v4.prod.sec",
  "status": "COMPLETED",
  "score": 42,
  "critical": 2,
  "high": 5,
  "medium": 12,
  "low": 8,
  "timestamp": "2024-10-24T14:32:00Z",
  "duration_seconds": 480
}
```

### **API Integration Status Example:**
```json
{
  "service": "VirusTotal",
  "status": "error",
  "last_sync": "2024-10-24T08:15:00Z",
  "error_message": "API key expired",
  "health_score": 0,
  "engines_available": 0
}
```

---

## 🎨 COMPONENT SPECIFICATIONS

### **Buttons**

**Primary Button (Start Scan, Generate Report)**
- Background: Linear gradient #b4c5ff → #2563eb (135°)
- Text color: #002a78
- Padding: 12px 24px
- Border radius: 4px
- Font: Label Label, 12px, 600 weight
- Hover: Darker blue, shadow elevation 3
- Active: Brighter blue
- Disabled: 50% opacity, no pointer

**Secondary Button (Cancel, Close)**
- Background: Transparent
- Border: 1px #434655 (ghost border, 15% opacity)
- Text: #dae2fd
- Padding: 12px 24px
- Hover: Slight background tint
- Active: Full color background

**Danger Button (CANCEL scan, DELETE)**
- Background: #DC2626 (red)
- Text: white
- Same sizing as primary
- Hover: Darker red #EF4444

### **Inputs**

**Text Input Field**
- Background: #0b1326 (surface base)
- Border: 1px #434655 (15% opacity ghost)
- Border radius: 4px
- Padding: 10px 12px
- Font: Body Med, 14px
- Text color: #dae2fd
- Placeholder: #8d90a0 (muted)
- Focus: 3px blue outline (#3B82F6), box-shadow with blue tint
- Error: Red border (#DC2626)
- Disabled: 50% opacity

**Select Dropdown**
- Same as text input
- Icon: Chevron down ▼ in muted color
- Hover: Border color brightens

### **Checkboxes & Radio Buttons**

**Checkbox**
- Size: 20px × 20px
- Unchecked: Border #434655, background #0b1326
- Checked: Background #3B82F6 with ✓ checkmark
- Border radius: 2px
- Hover: Border brightens
- Focus: Blue outline

**Radio Button**
- Size: 20px × 20px (circular)
- Unchecked: Border #434655, hollow center
- Checked: Center dot #3B82F6
- Border radius: full
- Hover: Border brightens

### **Cards/Containers**

**Result Card**
- Background: #131b2e
- Border: None (tonal layer)
- Border radius: 6px
- Padding: 16px
- Shadow: Elevation 2 on normal, Elevation 3 on hover
- Transition: 200ms smooth

**Severity-Colored Card Border**
- Add 2px left border matching severity:
  - CRITICAL: #DC2626
  - HIGH: #EF4444
  - MEDIUM: #FBBF24
  - LOW: #34D399

### **Badges/Labels**

**Severity Badge**
- Background: Color-coded (red/amber/green)
- Text: White, all-caps
- Padding: 4px 8px
- Border radius: 2px
- Font: Label Small, 10px, 600 weight

**Status Badge**
- Shape: Pill-shaped (border-radius: full)
- Examples:
  - "✅ COMPLETED" (green)
  - "🔄 IN PROGRESS" (blue)
  - "❌ FAILED" (red)
  - "⏳ PENDING" (gray)

### **Tables**

**Table Header**
- Background: #222a3d (surface-container-high)
- Text: #c3c6d7 (secondary)
- Font: Label Large, 12px, 600 weight
- All-caps
- Padding: 12px 16px
- Border-bottom: 1px #434655 (15% opacity ghost)

**Table Row**
- Background: #131b2e (default)
- Hover: #222a3d (slightly lighter)
- Height: 44px
- Padding: 12px 16px
- Border-bottom: 1px #434655 (very subtle)

**Expandable Row**
- Arrow indicator on left
- Click to expand details panel
- Details panel background: #0b1326 (darkest)
- Smooth 200ms height animation

### **Progress Bar**

**Linear Progress**
- Background (unfilled): #222a3d
- Foreground (filled): Gradient #b4c5ff → #2563eb
- Height: 6px
- Border radius: 3px
- Animation: Smooth fill, no bouncing

**Circular Progress (Gauge)**
- Background: #222a3d
- Foreground: Gradient blue
- Stroke width: 8px
- Center text: Large percentage
- Size: 180px diameter (in score card)

### **Modals**

**Modal Container**
- Background: #131b2e
- Border radius: 8px
- Shadow: Elevation 4 (32px blur, tinted)
- Width: 500px (desktop), full-width minus 16px margin (mobile)
- Max-height: 90vh

**Modal Overlay**
- Background: #000000 50% opacity
- Click overlay to close (optional)

**Modal Header**
- Title: Headline Med, 20px, 600 weight
- Close button (X): Top-right corner, 24px icon
- Padding: 24px

**Modal Body**
- Padding: 24px
- Scrollable if content > max-height

**Modal Footer**
- Background: #0b1326
- Padding: 16px 24px
- Border-top: 1px #434655 (15% opacity)
- Buttons: Right-aligned

---

## ✨ ANIMATIONS & INTERACTIONS

**Page Transition:** 200ms fade-in
**Button Hover:** 200ms state change + 100ms color fade
**Modal Open:** 300ms slide-up + fade-in
**Tab Switch:** 200ms fade between content
**Progress Bar Fill:** Smooth real-time animation (no bouncing)
**Alert Toast:** 300ms slide-in from right, auto-dismiss after 5-7s
**Severity Badge Pulse:** 2s ease-in-out pulse (CRITICAL only)
**Dropdown Open:** 150ms slide-down
**Row Expand:** Smooth height animation 200ms

**General Rules:**
- All animations <400ms for responsiveness
- Respect `prefers-reduced-motion` media query
- No bouncing or playful animations
- Focus on clarity and speed

---

## 📋 FEATURE CHECKLIST

✅ **Must Include:**
- 10 complete screens with all components
- Dark theme (Tactical Obsidian design)
- Responsive for 375px - 1920px
- Severity color coding (🔴🟡🟢)
- KPI metrics cards
- Data tables with sorting/pagination
- Progress tracking with real-time updates
- API integration status display
- Export options (JSON, CSV, PDF)
- Professional typography (Inter font)
- Accessibility: WCAG 2.1 AA compliant
- High-density information layout
- No 1px borders (tonal layering only)
- Glassmorphism on floating modals

✅ **Nice to Have:**
- Light mode toggle (currently dark-only)
- Keyboard shortcuts
- Advanced filters/search
- Custom report scheduling
- Real-time WebSocket updates
- Notification center

---

## 🎯 DESIGN DELIVERABLES CHECKLIST

**Before you start:**
- [ ] All 10 screens designed in Figma
- [ ] Components created in component library
- [ ] Design tokens exported (colors, spacing, typography)
- [ ] Interactive prototype with flows
- [ ] Mobile mockups shown
- [ ] Accessibility audit (color contrast, keyboard nav)

**Wireframes Phase:**
- [ ] All 10 screens in wireframe view
- [ ] User flows documented
- [ ] Interaction points marked

**Design Phase:**
- [ ] High-fidelity mockups (desktop + mobile)
- [ ] Dark theme colors applied
- [ ] Typography hierarchy visible
- [ ] Hover/active states shown
- [ ] Error states included
- [ ] Loading states included

**Handoff Phase:**
- [ ] Figma file shared with dev team
- [ ] Component specs documented
- [ ] Color palette exported
- [ ] Spacing scale documented
- [ ] All interactions documented
- [ ] Responsive breakpoints defined

---

## 🚀 FINAL INSTRUCTIONS FOR AI DESIGNER

1. **Start with wireframes** of all 10 screens
2. **Apply the Tactical Obsidian design system** (dark, high-density, professional)
3. **Use the exact color palette** provided (no modifications)
4. **Make it responsive** for mobile, tablet, desktop
5. **Include all components** specified in each screen
6. **Show hover/active states** for interactive elements
7. **Use Inter font** for typography
8. **No decorative design** — focus on clarity and functional beauty
9. **Make it production-ready** — not a prototype
10. **Export design tokens** for developer handoff

---

## 📞 CONTEXT FOR AI DESIGNER

This platform is designed for **security professionals** who:
- Spend 6-10 hours/day analyzing security data
- Need information **fast and accurate**
- Expect **professional, enterprise-grade** design
- Use multiple **high-resolution monitors**
- Work in **24/7 SOC environments** (hence dark theme)
- Require **high accessibility standards**
- Need **zero distractions** in the UI

**Design for their workflow, not for beauty.** Clarity is beauty in this context.

---

*Complete AI Designer Prompt v3.1*  
*Ready to use with v0, Galileo, Cursor, or any AI design tool*
