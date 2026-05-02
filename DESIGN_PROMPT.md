# 🛡️ CYBERDEFENCE ANALYST PLATFORM v3.1
## Design System & UI/UX Prompt

---

## 🎯 DESIGN OBJECTIVE

Design a **professional, intuitive enterprise security dashboard** for the **CyberDefence Analyst Platform v3.1** — a unified cybersecurity assessment tool that aggregates 6+ live data sources (Nuclei, WPScan, VirusTotal, Sucuri, SecurityHeaders.com, Cloudflare) into a single command center.

**Primary Goal:** Enable security analysts to run comprehensive vulnerability scans, view results, and generate professional PDF reports in <10 minutes via an intuitive web interface.

---

## 👥 TARGET USERS & PERSONAS

| Persona | Role | Primary Need | Time on Platform |
|---------|------|--------------|------------------|
| **Sarah** | SOC Analyst | Fast scanning, accurate reporting | 8-10 min/scan |
| **Marcus** | Security Manager | High-level overview, trend tracking | 2-3 min/dashboard |
| **Priya** | DevSecOps Engineer | Custom module selection, API integration | 5-7 min/custom |
| **James** | CISO | Executive summary, risk prioritization | 3-5 min/report |

---

## 📋 CORE FEATURES TO DESIGN

### **1. Landing Dashboard**
**Purpose:** First screen users see - security posture snapshot

**Must Include:**
- ✅ KPI Cards: 🔴 Critical vulns, 🔴 High vulns, 🟡 Medium, 🟢 Low (with counts)
- ✅ Security Score (0-100) with progress bar
- ✅ SIEM Events counter
- ✅ VirusTotal reputation status
- ✅ Quick Action Buttons: [Auto Scan] [Custom Scan] [View History]
- ✅ Live Data Source Status (6 sources with ✅/❌ indicators)
- ✅ Scan History Table (last 10 scans, sortable)

**Design Notes:**
- Grid layout: 2 columns on desktop, 1 on mobile
- Cards with color-coded borders matching severity
- Refresh button updates all metrics
- Professional, minimal design (no clutter)

---

### **2. New Scan Modal Dialog**
**Purpose:** Initiate security assessment

**Must Include:**
- ✅ Target Input Field (domain/URL input with validation)
- ✅ Scan Mode Selection (radio buttons):
  - Quick Scan (Reconnaissance only)
  - Standard Assessment (Recon + Vulnerabilities)
  - Comprehensive Audit (Full 6-module pipeline)
  - Custom Select (user chooses modules)
- ✅ Module Selection Checkboxes (6 modules, all pre-checked by default):
  - Module 1: Reconnaissance & Tech Scanning
  - Module 2: Vulnerability Assessment
  - Module 3: Defence Configuration Check
  - Module 4: SIEM Log Analysis
  - Module 5: Security Policy Generator
  - Module 6: VirusTotal Reputation Check
- ✅ API Key Verification (shows ✅ or ⚠️ for each key)
- ✅ Action Buttons: [Cancel] [Start Scan →]

**Design Notes:**
- Centered modal, 500px width (responsive)
- Clean form layout with clear field labels
- Helper text under each section
- Disabled state if required API keys missing

---

### **3. Live Scan Progress Tracker**
**Purpose:** Real-time feedback during active scan

**Must Include:**
- ✅ Target & status heading (e.g., "🟡 SCAN IN PROGRESS: example.com")
- ✅ Module-by-module progress (1/6, 2/6, etc.):
  - Status icon (✅ complete, 🔄 in progress, ⏳ pending)
  - Module name
  - Progress line (visual bar)
  - Live findings count (if applicable)
- ✅ Overall Progress Bar (0-100%)
- ✅ Estimated Time Remaining
- ✅ Control Buttons: [Pause] [Cancel]

**Design Notes:**
- Vertical timeline layout
- Smooth progress bar animation
- Real-time updates (no page refresh)
- Success color for completed modules, blue for active, gray for pending

---

### **4. Vulnerability Results View**
**Purpose:** Display detailed vulnerability findings

**Must Include:**
- ✅ Summary Card (top section):
  - 🔴 X Critical | 🔴 X High | 🟡 X Medium | 🟢 X Low
  - Total Confirmed vulnerabilities count
- ✅ Sortable Data Table:
  - Columns: # | Vulnerability Name | Source | Confirmed | Severity | CVSS | CVE
  - Color-coded severity badges
  - Sortable by any column
  - Paginated (10/25/50 rows per page)
- ✅ Expandable Row Details:
  - Evidence of vulnerability
  - CVSS score breakdown
  - CVE link
  - Remediation steps
- ✅ Action Buttons: [Export JSON] [Generate Report] [Save to History]

**Design Notes:**
- Severity-based color coding in table rows
- Light gray alternating row backgrounds for readability
- Hover effect on rows (shadow, pointer cursor)
- Expandable details use accordion pattern

---

### **5. Defence Configuration Assessment Card**
**Purpose:** Show security hardening grade

**Must Include:**
- ✅ Overall Security Score (0-100) with grade:
  - >60 = Green (✅ Good)
  - 30-60 = Yellow (⚠️ Acceptable)
  - <30 = Red (❌ Poor)
- ✅ Pass/Fail/Warn Summary: "✓ 10 PASS | ✗ 2 FAIL | △ 2 WARN"
- ✅ 14-Point Defence Checklist Table:
  - Check name | Requirement | Status | Details
  - Status indicators: ✅ PASS (green) | ❌ FAIL (red) | △ WARN (yellow)
- ✅ Top Recommendations List (4-5 actionable items):
  - 🔴 CRITICAL items first
  - 🟡 MEDIUM items next
- ✅ Action Buttons: [View Details] [Generate Report]

**Design Notes:**
- Large progress bar showing score percentage
- Table with alternating row colors
- Icons in status column for quick scanning
- Recommendations as numbered list with severity emoji

---

### **6. VirusTotal Reputation Report**
**Purpose:** Display domain reputation across 90+ AV engines

**Must Include:**
- ✅ Reputation Verdict Card (prominent, centered):
  - 🟢 CLEAN (0 detections)
  - 🟡 SUSPICIOUS (1-4 detections)
  - 🔴 DANGEROUS (5+ detections)
- ✅ Metrics Table:
  - Resolved IP | Country | ASN | Registrar
  - Total Engines | Malicious | Suspicious | Harmless | Undetected
  - Each with percentage display
- ✅ Engine Agreement Breakdown:
  - Sample of major AV engines (Kaspersky, Avast, McAfee, etc.)
  - Their verdict for the domain
- ✅ Threat Categories (if applicable):
  - Phishing, Malware, Shortener, Adware (with counts)
- ✅ Action Buttons: [View Full Report] [Export]

**Design Notes:**
- Large verdict badge with appropriate color
- Metrics in 2-column layout for desktop
- Engine list as compact items
- Responsive: stack to single column on mobile

---

### **7. SIEM Threat Analysis Dashboard**
**Purpose:** Show attack patterns from log analysis

**Must Include:**
- ✅ Threat Summary Box:
  - 🔴 X CRITICAL | 🔴 X HIGH | 🟡 X MEDIUM | 🟢 X LOW
  - Top threat type highlighted
- ✅ Top Attacking IPs Table:
  - Source IP | Attack Count | Risk Level
  - Sortable by count
  - Color-coded risk levels
  - 8 rows displayed
- ✅ Attack Patterns Detected (10 types):
  - SQL Injection, XSS, Directory Traversal, Brute Force, etc.
  - Count per type
  - Severity badge
  - Unique source IPs count
- ✅ Recommendations Section:
  - Bulleted list of action items based on data
  - Ordered by priority
- ✅ Action Buttons: [View Raw Logs] [Export] [Alert]

**Design Notes:**
- Horizontal bar charts for attack counts
- Tables with hover effects
- Color coding matches severity scale
- Mobile: collapse tables into expandable sections

---

### **8. PDF Report Generator Interface**
**Purpose:** Build and preview professional security report

**Must Include:**
- ✅ Report Metadata Form:
  - Organization Name (text input)
  - Primary Target (text input)
  - Report Author (text input)
  - Report Date (auto-filled, editable)
- ✅ PDF Preview Section (2-page preview):
  - Page 1: Cover page with company branding space
  - Page 2: Executive Summary table
- ✅ Generation Progress (during build):
  - Step-by-step: Building cover page... Executive summary... Vulnerability table...
  - Progress bar
- ✅ Output Options:
  - [👁️ View Full PDF] [📥 Download] [📧 Email] [✏️ Edit Metadata]

**Design Notes:**
- Form fields in light gray background box
- PDF preview shows actual rendered output
- Download button prominent (primary action)
- Email option with recipient field (optional)

---

### **9. Tabs/Module Switcher**
**Purpose:** Navigate between result views

**Must Include:**
- ✅ Tab Bar with 4-5 options:
  - [Vulnerabilities] [Defence Config] [VirusTotal] [SIEM] [Raw Data]
- ✅ Active tab styling (underline + primary color)
- ✅ Inactive tabs (gray text)
- ✅ Tab content switches without page reload

**Design Notes:**
- Sticky tab bar at top of results
- Smooth fade transition between tabs
- Mobile: horizontal scroll for overflow

---

### **10. Alert & Notification System**
**Purpose:** Communicate system status and findings

**Must Include:**
- ✅ Alert Types (4 styles):
  - **Critical Alert** 🔴: Red border, red icon, dark red background
  - **Warning Alert** 🟡: Yellow border, yellow icon, light yellow background
  - **Success Alert** 🟢: Green border, green icon, light green background
  - **Info Alert** 🔵: Blue border, blue icon, light blue background
- ✅ Alert Content:
  - Icon + Title + Description + Optional CTA button
  - Close button (X)
  - Auto-dismiss (5-7 seconds for info/success)
- ✅ Positioning:
  - Top-right corner, stacked if multiple
  - Toast-style appearance

**Design Notes:**
- Consistent icon set (checkmark, warning, error, info)
- Readable text contrast (WCAG AA minimum)
- Smooth slide-in/out animation

---

## 🎨 DESIGN SYSTEM

### **Color Palette**

| Use Case | Color | Hex | RGB |
|----------|-------|-----|-----|
| Critical/Alert | Red | #DC2626 | 220, 38, 38 |
| High/Urgent | Red Orange | #EF4444 | 239, 68, 68 |
| Medium/Warning | Amber | #FBBF24 | 251, 191, 36 |
| Low/Safe | Green | #34D399 | 52, 211, 153 |
| Inactive/Info | Gray | #6B7280 | 107, 114, 128 |
| Processing/Active | Blue | #3B82F6 | 59, 130, 246 |
| Primary Brand | Blue | #2563EB | 37, 99, 235 |
| Backgrounds | Light Gray | #F3F4F6 | 243, 244, 246 |
| Text Primary | Dark Gray | #1F2937 | 31, 41, 55 |
| Text Secondary | Medium Gray | #6B7280 | 107, 114, 128 |
| Border/Divider | Light Gray | #E5E7EB | 229, 231, 235 |

### **Typography**

| Level | Font Size | Weight | Line Height | Use Case |
|-------|-----------|--------|-------------|----------|
| H1 | 32px | 700 | 1.2 | Main titles, page headers |
| H2 | 24px | 600 | 1.3 | Section headers |
| H3 | 18px | 600 | 1.4 | Subsection headers |
| Body | 14px | 400 | 1.5 | Regular text, table data |
| Small | 12px | 400 | 1.4 | Secondary text, captions |
| Caption | 11px | 400 | 1.4 | Helper text, timestamps |
| Badge | 11px | 600 | 1 | Status indicators |

**Font Family:** Sans-serif (Inter, Roboto, SF Pro, or system sans-serif)

### **Spacing Scale (8px base)**

```
xs: 4px      (1/2 unit)   - Tight spacing
sm: 8px      (1 unit)     - Default padding
md: 16px     (2 units)    - Section spacing
lg: 24px     (3 units)    - Container padding
xl: 32px     (4 units)    - Major spacing
2xl: 48px    (6 units)    - Large gaps
```

### **Border Radius**

```
none: 0px
sm: 2px      (inputs, tight elements)
md: 4px      (cards, buttons, regular)
lg: 6px      (modals, containers)
full: 9999px (badges, pill buttons, circles)
```

### **Shadows**

```
Elevation 1: 0 1px 2px rgba(0,0,0,0.05)
Elevation 2: 0 2px 4px rgba(0,0,0,0.1)
Elevation 3: 0 4px 8px rgba(0,0,0,0.15)      (Cards, modals)
Elevation 4: 0 8px 16px rgba(0,0,0,0.2)      (Dropdowns)
Focus: 0 0 0 3px rgba(59,130,246,0.1)        (Focus states)
```

### **Anti-Patterns** (What NOT to do)
- ❌ Playful animations (focus on clarity)
- ❌ Bright neon colors (professional only)
- ❌ Comic Sans or handwritten fonts
- ❌ Ornamental graphics (data-driven design)
- ❌ Excessive white space (high information density)
- ❌ Hover effects lasting >400ms

---

## 🎯 RESPONSIVE BREAKPOINTS

| Device | Width | Layout | Columns |
|--------|-------|--------|---------|
| Mobile | 375px | Single column stack | 1 |
| Tablet | 768px | 2-column | 2 |
| Desktop | 1024px | Multi-column grid | 3-4 |
| Ultra-wide | 1920px | Full layout | 4+ |

**Mobile-Specific:**
- Button height: 56px minimum
- Tap target: 44px minimum
- Bottom sheets instead of center modals
- Swipeable tabs
- Collapse tables into cards

---

## ♿ ACCESSIBILITY REQUIREMENTS

**WCAG 2.1 AA Compliance (Minimum):**
- ✅ Color contrast: 4.5:1 for text, 3:1 for graphics
- ✅ Semantic HTML: nav, main, aside, article, section
- ✅ ARIA labels: aria-label, aria-describedby, aria-live
- ✅ Keyboard navigation: Tab, Enter, Escape, Arrow keys
- ✅ Focus indicators: Minimum 3px visible outline
- ✅ Screen reader support: Proper heading hierarchy
- ✅ Alt text: All images, icons, charts
- ✅ Form labels: Linked via htmlFor
- ✅ Error messages: Clear, actionable, linked to input
- ✅ Skip links: Jump to main content
- ✅ Motion: Respect prefers-reduced-motion

---

## 🌙 DARK MODE SUPPORT

**Required:**
- Toggle in header (☀️ Light | 🌙 Dark)
- Respect system preference (prefers-color-scheme)
- Save user preference to localStorage
- All colors must work in both modes

**Dark Mode Colors:**
```
Background:    #0F172A (very dark blue)
Surface:       #1E293B (card background)
Text Primary:  #F1F5F9 (light white-gray)
Text Secondary: #CBD5E1 (muted light gray)
Border:        #334155 (muted border)
Accent:        #3B82F6 (bright blue for contrast)
```

---

## 📊 DATA VISUALIZATION REQUIREMENTS

### **Charts & Graphs**
- **Pie Chart:** Vulnerability severity breakdown (Critical/High/Medium/Low)
- **Horizontal Bar:** CVSS score distribution
- **Timeline:** Attack events over time (SIEM)
- **Table:** Sortable vulnerability/IP/threat data
- **Gauge:** Security score (0-100)
- **Heatmap:** IP geolocation of attacking sources (optional)

**Library Recommendations:** Chart.js, Recharts, D3.js, or ApexCharts

### **Progress Indicators**
- Linear progress bar (0-100%)
- Circular progress (scan completion %)
- Step indicators (module 1/6, 2/6, etc.)
- Skeleton screens during data load

---

## 🎬 MICRO-INTERACTIONS & ANIMATIONS

| Interaction | Duration | Easing | Behavior |
|-------------|----------|--------|----------|
| Hover (button) | 200ms | ease-in-out | Color fade + slight lift |
| Modal open | 300ms | cubic-bezier | Slide up + fade in |
| Tab switch | 200ms | ease-out | Fade between content |
| Progress fill | Smooth | linear | Real-time animation |
| Alert toast | 300ms | ease-out | Slide in from right |
| Severity badge pulse | 2s | ease-in-out | Subtle pulse (CRITICAL only) |

**Animation Library:** Framer Motion (React) or CSS Transitions

---

## 📱 RESPONSIVE BEHAVIOR

### **Desktop (1920px+)**
- Full dashboard grid (4 columns)
- Data tables fully visible
- Side-by-side module results
- All actions visible

### **Tablet (768px)**
- 2-column layout
- Tables scroll horizontally
- Stacked cards
- Bottom action bar

### **Mobile (375px)**
- Single column stack
- Card-based layout
- Collapsible sections
- Full-width buttons (56px height)
- Vertical scrolling
- Modal as full-screen sheet

---

## 🔑 KEY UI COMPONENTS

### **Buttons**
- Primary: Solid color (#2563EB), white text
- Secondary: Outlined, gray border
- Danger: Red background for destructive actions
- Disabled: 50% opacity, no pointer
- Min height: 40px desktop, 56px mobile
- Padding: 8px 16px

### **Input Fields**
- Border: 1px solid #E5E7EB
- Padding: 8px 12px
- Border radius: 4px
- Focus: Blue outline (3px), box-shadow
- Error state: 1px solid red border, helper text in red
- Min height: 40px

### **Cards/Containers**
- Background: White (#FFFFFF) or light gray (#F9FAFB)
- Border: 1px solid #E5E7EB (optional)
- Border radius: 6px
- Padding: 16px
- Shadow: Elevation 2-3

### **Badges/Labels**
- Background: Severity-dependent color
- Text: White
- Padding: 4px 8px
- Border radius: 4px
- Font weight: 600

### **Tables**
- Header background: Light gray (#F3F4F6)
- Row hover: Bg color change + shadow
- Borders: Light gray (#E5E7EB)
- Font: 14px body text
- Row height: 44px minimum
- Pagination: Show 10/25/50 options

### **Modals/Dialogs**
- Width: 500px (responsive)
- Max height: 90vh
- Border radius: 8px
- Background: White
- Close button (X) top-right
- Content padding: 24px
- Overlay opacity: 50% (#000000)

---

## 🚀 FRONTEND TECH STACK

### **Recommended Framework**
- **React 18+** (Component reusability, state management)
- Alternative: Vue 3 or Svelte

### **Key Libraries**
- **UI Framework:** Tailwind CSS (utility-first) or Material-UI
- **State:** Redux, Zustand, or Jotai
- **Forms:** React Hook Form + Zod validation
- **Tables:** TanStack Table (React Table)
- **Charts:** Recharts or Chart.js
- **Icons:** Heroicons or Feather Icons
- **PDF:** html2pdf or jsPDF
- **Real-time:** WebSocket or Server-Sent Events (SSE)
- **Animations:** Framer Motion
- **Date/Time:** date-fns or Day.js

### **Styling Approach**
- Tailwind CSS for utilities (fastest development)
- CSS Modules for scoped component styles
- Design Tokens exported as CSS variables

---

## ✅ DESIGN REQUIREMENTS CHECKLIST

### **Functional Requirements**
- ✅ Dashboard displays real-time KPIs from last scan
- ✅ New Scan modal allows target input + module selection
- ✅ Progress tracker shows live updates (no page refresh)
- ✅ Results viewable in 5+ tabs (Vuln, Defence, SIEM, VT, Raw)
- ✅ Each result type has sortable table + expandable details
- ✅ PDF report generator with metadata form + preview
- ✅ Scan history displays last 20 scans, clickable to reload
- ✅ API key status shown on dashboard

### **Visual Requirements**
- ✅ Severity color-coded (#DC2626 for critical, #FBBF24 for medium, #34D399 for low)
- ✅ Consistent spacing (8px base unit)
- ✅ Professional sans-serif typography
- ✅ High information density without clutter
- ✅ Minimal animations (focus on clarity)
- ✅ Dark mode fully functional

### **Responsive & Accessibility**
- ✅ Works on 375px - 1920px+ screens
- ✅ Touch targets 44px+ on mobile
- ✅ WCAG 2.1 AA color contrast
- ✅ Full keyboard navigation (Tab, Enter, Escape)
- ✅ Screen reader compatible (ARIA labels)
- ✅ Proper heading hierarchy (H1 → H2 → H3)
- ✅ Respects prefers-reduced-motion

### **Performance**
- ✅ Dashboard loads <2 seconds
- ✅ Modal opens <500ms
- ✅ Tab switching <800ms
- ✅ Skeleton screens during data fetch
- ✅ Lazy load charts/tables if needed
- ✅ <3s First Contentful Paint

### **UX Patterns**
- ✅ Progressive disclosure (expand details on demand)
- ✅ Undo/destructive action confirmation
- ✅ Contextual help text under inputs
- ✅ Loading states for all async operations
- ✅ Error messages clear & actionable
- ✅ Success confirmations for critical actions

---

## 📊 EXAMPLE DATA STRUCTURES

### **Vulnerability Result Object**
```json
{
  "vulnerability": "WordPress Core Remote Code Execution",
  "source": "nuclei",
  "confirmed": true,
  "severity": "CRITICAL",
  "cvss": 9.8,
  "cve_id": "CVE-2024-12345",
  "evidence": "WordPress 5.9 detected in meta tag",
  "remediation": "Update to latest WordPress version immediately"
}
```

### **Defence Check Object**
```json
{
  "name": "HTTPS/SSL Certificate",
  "requirement": "Prevention #2",
  "status": "PASS",
  "details": "Valid certificate, expires Dec 2025"
}
```

### **SIEM Attack Event Object**
```json
{
  "attack_type": "SQL_INJECTION",
  "source_ip": "195.108.229.254",
  "count": 187,
  "severity": "CRITICAL"
}
```

---

## 🎯 SUCCESS CRITERIA

1. **Usability:** User completes full scan + report in <10 minutes
2. **Performance:** Dashboard renders in <2 seconds
3. **Accessibility:** WAVE/AXE audit shows 0 errors
4. **Mobile:** Lighthouse score >90 on 80% of mobile devices
5. **Professional:** Looks enterprise-grade, not toy-ish
6. **Data Clarity:** Security findings immediately understandable
7. **Navigation:** User never lost, always knows how to go back

---

## 📞 DELIVERABLES

### **Design Phase**
- [ ] Wireframes for 8 main screens
- [ ] High-fidelity mockups (desktop + mobile)
- [ ] Interactive Figma prototype with flows
- [ ] Component library (buttons, cards, inputs, etc.)
- [ ] Design tokens file (colors, spacing, typography)
- [ ] Accessibility audit report

### **Handoff Phase**
- [ ] Figma design file with all components
- [ ] Design system documentation
- [ ] CSS/Tailwind token export
- [ ] Mock API responses (JSON)
- [ ] Performance baseline (Lighthouse)
- [ ] Mobile device testing results

---

## 🏁 FINAL NOTES

**This is an enterprise security platform.** The design must communicate:
- ✅ **Trust** (professional, clean, minimal)
- ✅ **Clarity** (data immediately understandable)
- ✅ **Speed** (fast, no unnecessary steps)
- ✅ **Urgency** (severity colors stand out)
- ✅ **Action** (clear CTAs, recommendations visible)

**Target Audience:** Security professionals who use enterprise tools daily. They expect:
- High information density
- Keyboard shortcuts
- Export options (JSON, CSV, PDF)
- Dark mode
- Mobile support (but desktop-primary)
- Zero playful design

**Design Philosophy:**
> "Turn security complexity into clarity. Make 6 data sources feel like 1 command."

---

## 🚀 NEXT STEPS

1. **Present this brief** to design team
2. **Create wireframes** for core 8 screens
3. **Build interactive prototype** in Figma
4. **Conduct accessibility audit** (WCAG 2.1 AA)
5. **Perform user testing** with 3-5 security professionals
6. **Export design tokens** for developer handoff
7. **Hand over to frontend team** with component library

---

*Design Prompt v3.1 | CyberDefence Analyst Platform*  
*Ready for Figma / Design Implementation*
