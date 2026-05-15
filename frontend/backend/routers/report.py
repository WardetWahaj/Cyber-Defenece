"""
Report and policy generation endpoints for the CyberDefence API.

Provides PDF report generation, policy document creation, and report retrieval.
"""

import datetime as dt
import json
from typing import Any

from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from fpdf import FPDF

import cyberdefence_platform_v31 as core
from frontend.backend import auth
from frontend.backend.routers.auth_routes import get_current_user

router = APIRouter(tags=["reports"])


class PolicyRequest(BaseModel):
    policy_id: str = Field(default="1")
    org_name: str = Field(default="Organisation")


class ReportRequest(BaseModel):
    org_name: str = Field(default="Organisation")
    target: str = Field(default="N/A")
    author: str = Field(default="Security Analyst")
    include_pdf: bool = Field(default=True)


def _derive_vuln_badge(result_blob: dict[str, Any]) -> str:
    """Derive vulnerability severity badge from result data."""
    summary = result_blob.get("summary", {}) if isinstance(result_blob, dict) else {}
    critical = int(summary.get("critical", 0))
    high = int(summary.get("high", 0))
    medium = int(summary.get("medium", 0))
    return f"{critical}C/{high}H/{medium}M"


def _derive_score(module: str, result_blob: dict[str, Any]) -> str:
    """Derive security score from module results."""
    if module == "defence":
        return str(result_blob.get("score", "--"))
    if module == "vuln":
        summary = result_blob.get("summary", {}) if isinstance(result_blob, dict) else {}
        critical = int(summary.get("critical", 0))
        high = int(summary.get("high", 0))
        medium = int(summary.get("medium", 0))
        low = int(summary.get("low", 0))
        weighted = max(0, 100 - (critical * 15 + high * 6 + medium * 2 + low))
        return str(weighted)
    return "--"


def _sanitize_for_pdf(text: str) -> str:
    """Sanitize text to be compatible with Helvetica font in PDF."""
    if not isinstance(text, str):
        text = str(text)
    # Replace common Unicode characters with ASCII equivalents
    replacements = {
        "→": "->",
        "←": "<-",
        "↓": "v",
        "↑": "^",
        "✓": "✓",
        "✗": "X",
        "•": "-",
        """: '"',
        """: '"',
        "'": "'",
        "'": "'",
        "–": "-",
        "—": "-",
        "…": "...",
        "™": "(TM)",
        "©": "(C)",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    # Remove any remaining non-latin-1 characters
    text = text.encode('latin-1', errors='replace').decode('latin-1')
    return text.strip()


def _create_pdf_report(org_name: str, target: str, author: str, summary: dict[str, Any], details: dict[str, Any] = None) -> str:
    reports_dir = core.DATA_DIR / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    path = reports_dir / f"security_report_api_{core.ts()}.pdf"

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    page_width = 210  # A4 width in mm

    # ── Color palette ──
    COLOR_PRIMARY = (15, 23, 42)       # Dark navy
    COLOR_ACCENT = (59, 130, 246)      # Blue
    COLOR_CRITICAL = (220, 38, 38)     # Red
    COLOR_HIGH = (234, 88, 12)         # Orange
    COLOR_MEDIUM = (202, 138, 4)       # Amber
    COLOR_LOW = (22, 163, 74)          # Green
    COLOR_INFO = (100, 116, 139)       # Slate
    COLOR_BG_LIGHT = (241, 245, 249)   # Light gray-blue
    COLOR_WHITE = (255, 255, 255)
    COLOR_BORDER = (203, 213, 225)     # Light border

    def get_severity_color(severity):
        s = severity.upper() if severity else ""
        if s == "CRITICAL": return COLOR_CRITICAL
        if s == "HIGH": return COLOR_HIGH
        if s == "MEDIUM": return COLOR_MEDIUM
        if s == "LOW": return COLOR_LOW
        return COLOR_INFO

    def add_header_footer():
        """Add header bar and footer to current page"""
        # Top accent bar
        pdf.set_fill_color(*COLOR_ACCENT)
        pdf.rect(0, 0, page_width, 4, "F")
        # Footer
        pdf.set_y(-15)
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(*COLOR_INFO)
        pdf.cell(0, 5, f"Cyber Defence Security Report  |  {_sanitize_for_pdf(org_sanitized)}  |  CONFIDENTIAL", align="L")
        pdf.cell(0, 5, f"Page {pdf.page_no()}", align="R", ln=True)
        pdf.set_text_color(*COLOR_PRIMARY)

    def section_title(number, title):
        """Add a styled section title"""
        pdf.set_font("Helvetica", "B", 16)
        pdf.set_text_color(*COLOR_PRIMARY)
        pdf.cell(0, 10, f"{number}. {title}", ln=True)
        # Underline
        pdf.set_draw_color(*COLOR_ACCENT)
        pdf.set_line_width(0.6)
        pdf.line(10, pdf.get_y(), page_width - 10, pdf.get_y())
        pdf.set_line_width(0.2)
        pdf.set_draw_color(*COLOR_BORDER)
        pdf.ln(5)

    def kpi_box(x, y, w, label, value, color=COLOR_PRIMARY):
        """Draw a KPI metric box"""
        pdf.set_fill_color(*COLOR_BG_LIGHT)
        pdf.rect(x, y, w, 22, "F")
        pdf.set_draw_color(*COLOR_BORDER)
        pdf.rect(x, y, w, 22, "D")
        # Label
        pdf.set_xy(x + 2, y + 2)
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(*COLOR_INFO)
        pdf.cell(w - 4, 5, label)
        # Value
        pdf.set_xy(x + 2, y + 9)
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(*color)
        pdf.cell(w - 4, 10, str(value))
        pdf.set_text_color(*COLOR_PRIMARY)

    org_sanitized = _sanitize_for_pdf(org_name)
    target_sanitized = _sanitize_for_pdf(target)
    author_sanitized = _sanitize_for_pdf(author)
    report_date = dt.datetime.now().strftime("%B %d, %Y at %H:%M UTC")
    report_id = f"CD-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}"

    score = summary.get("security_score", 0)
    vuln_sum = summary.get("vulnerability_summary", {})
    crit = vuln_sum.get("critical", 0)
    high = vuln_sum.get("high", 0)
    med = vuln_sum.get("medium", 0)
    low = vuln_sum.get("low", 0)
    total_vulns = crit + high + med + low
    defence = summary.get("defence", {})
    siem = summary.get("siem", {})
    vt = summary.get("virustotal", {})

    if score >= 80:
        grade, grade_desc = "A", "Strong security posture"
        grade_color = COLOR_LOW
    elif score >= 60:
        grade, grade_desc = "B", "Acceptable, improvements needed"
        grade_color = COLOR_ACCENT
    elif score >= 40:
        grade, grade_desc = "C", "Multiple issues require attention"
        grade_color = COLOR_MEDIUM
    else:
        grade, grade_desc = "D", "Critical issues — immediate action required"
        grade_color = COLOR_CRITICAL

    # ════════════════════════════════════════════
    # PAGE 1: COVER PAGE
    # ════════════════════════════════════════════
    pdf.add_page()
    # Top accent bar
    pdf.set_fill_color(*COLOR_ACCENT)
    pdf.rect(0, 0, page_width, 6, "F")

    # Title block
    pdf.ln(40)
    pdf.set_font("Helvetica", "B", 36)
    pdf.set_text_color(*COLOR_PRIMARY)
    pdf.cell(0, 18, "CYBER DEFENCE", ln=True, align="C")
    pdf.set_font("Helvetica", "", 16)
    pdf.set_text_color(*COLOR_ACCENT)
    pdf.cell(0, 10, "Security Assessment Report", ln=True, align="C")

    # Divider line
    pdf.ln(8)
    pdf.set_draw_color(*COLOR_ACCENT)
    pdf.set_line_width(0.8)
    pdf.line(60, pdf.get_y(), page_width - 60, pdf.get_y())
    pdf.set_line_width(0.2)
    pdf.ln(12)

    # Report metadata box
    pdf.set_fill_color(*COLOR_BG_LIGHT)
    box_y = pdf.get_y()
    pdf.rect(30, box_y, page_width - 60, 52, "F")
    pdf.set_draw_color(*COLOR_BORDER)
    pdf.rect(30, box_y, page_width - 60, 52, "D")

    pdf.set_xy(38, box_y + 5)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*COLOR_INFO)
    pdf.cell(60, 6, "ORGANIZATION")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*COLOR_PRIMARY)
    pdf.cell(0, 6, org_sanitized, ln=True)

    pdf.set_x(38)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*COLOR_INFO)
    pdf.cell(60, 6, "TARGET ASSET")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*COLOR_PRIMARY)
    pdf.cell(0, 6, target_sanitized, ln=True)

    pdf.set_x(38)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*COLOR_INFO)
    pdf.cell(60, 6, "ANALYST")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*COLOR_PRIMARY)
    pdf.cell(0, 6, author_sanitized, ln=True)

    pdf.set_x(38)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*COLOR_INFO)
    pdf.cell(60, 6, "DATE")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*COLOR_PRIMARY)
    pdf.cell(0, 6, report_date, ln=True)

    pdf.set_x(38)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*COLOR_INFO)
    pdf.cell(60, 6, "REPORT ID")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*COLOR_PRIMARY)
    pdf.cell(0, 6, report_id, ln=True)

    # Classification banner at bottom
    pdf.set_y(-45)
    pdf.set_fill_color(*COLOR_CRITICAL)
    pdf.rect(30, pdf.get_y(), page_width - 60, 10, "F")
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*COLOR_WHITE)
    pdf.set_x(30)
    pdf.cell(page_width - 60, 10, "CLASSIFICATION: CONFIDENTIAL", align="C", ln=True)
    pdf.set_text_color(*COLOR_PRIMARY)

    pdf.set_font("Helvetica", "", 7)
    pdf.set_text_color(*COLOR_INFO)
    pdf.set_x(30)
    pdf.multi_cell(page_width - 60, 4, "This report contains sensitive security information and is intended only for authorized recipients within the named organization. Unauthorized access, use, or disclosure is strictly prohibited.", align="C")

    # ════════════════════════════════════════════
    # PAGE 2: TABLE OF CONTENTS
    # ════════════════════════════════════════════
    pdf.add_page()
    add_header_footer()

    pdf.set_y(15)
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(*COLOR_PRIMARY)
    pdf.cell(0, 12, "Table of Contents", ln=True)
    pdf.ln(5)

    toc_items = [
        ("1", "Executive Summary", "3"),
        ("2", "Security Score & Risk Overview", "3"),
        ("3", "Assessment Methodology", "4"),
        ("4", "Detailed Vulnerability Findings", "5"),
        ("5", "Security Configuration Audit", "6"),
        ("6", "Security Events & Incident Detection", "7"),
        ("7", "Malware & Threat Analysis", "8"),
        ("8", "Remediation Roadmap", "9"),
        ("9", "Severity Definitions & Glossary", "10"),
    ]

    for num, title, page in toc_items:
        pdf.set_font("Helvetica", "B" if num in ("1", "2") else "", 11)
        pdf.set_text_color(*COLOR_PRIMARY)
        pdf.cell(8, 8, num + ".")
        pdf.cell(0, 8, title)
        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(*COLOR_INFO)
        pdf.ln()

    # ════════════════════════════════════════════
    # PAGE 3: EXECUTIVE SUMMARY + SCORE
    # ════════════════════════════════════════════
    pdf.add_page()
    add_header_footer()
    pdf.set_y(12)
    section_title("1", "EXECUTIVE SUMMARY")

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*COLOR_PRIMARY)
    pdf.multi_cell(0, 5, f"This security assessment was conducted on {report_date} targeting {target_sanitized} for {org_sanitized}. The assessment evaluated the target across multiple security domains including vulnerability scanning, security configuration analysis, threat intelligence correlation, and event monitoring.")
    pdf.ln(5)

    # Score display
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "Overall Security Assessment", ln=True)
    pdf.ln(2)

    # Grade box
    grade_box_y = pdf.get_y()
    pdf.set_fill_color(*grade_color)
    pdf.rect(10, grade_box_y, 35, 30, "F")
    pdf.set_xy(10, grade_box_y + 3)
    pdf.set_font("Helvetica", "B", 28)
    pdf.set_text_color(*COLOR_WHITE)
    pdf.cell(35, 24, grade, align="C")
    pdf.set_text_color(*COLOR_PRIMARY)

    # Score and description next to grade
    pdf.set_xy(50, grade_box_y + 2)
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 10, f"{score} / 100")
    pdf.set_xy(50, grade_box_y + 14)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(*COLOR_INFO)
    pdf.cell(0, 8, grade_desc)
    pdf.set_text_color(*COLOR_PRIMARY)

    pdf.set_y(grade_box_y + 38)

    # ── KPI Cards Row ──
    section_title("2", "RISK OVERVIEW")

    kpi_y = pdf.get_y()
    box_w = (page_width - 30) / 4
    kpi_box(10, kpi_y, box_w - 2, "CRITICAL VULNS", str(crit), COLOR_CRITICAL if crit > 0 else COLOR_LOW)
    kpi_box(10 + box_w, kpi_y, box_w - 2, "HIGH VULNS", str(high), COLOR_HIGH if high > 0 else COLOR_LOW)
    kpi_box(10 + box_w * 2, kpi_y, box_w - 2, "TOTAL FINDINGS", str(total_vulns), COLOR_PRIMARY)
    kpi_box(10 + box_w * 3, kpi_y, box_w - 2, "EVENTS DETECTED", str(siem.get("events", 0)), COLOR_ACCENT)

    pdf.set_y(kpi_y + 28)
    pdf.ln(3)

    # Second row of KPIs
    kpi_y2 = pdf.get_y()
    kpi_box(10, kpi_y2, box_w - 2, "CONFIG PASSED", str(defence.get("pass", 0)), COLOR_LOW)
    kpi_box(10 + box_w, kpi_y2, box_w - 2, "CONFIG FAILED", str(defence.get("fail", 0)), COLOR_CRITICAL if defence.get("fail", 0) > 0 else COLOR_LOW)
    kpi_box(10 + box_w * 2, kpi_y2, box_w - 2, "MALICIOUS FLAGS", str(vt.get("malicious", 0)), COLOR_CRITICAL if vt.get("malicious", 0) > 0 else COLOR_LOW)
    kpi_box(10 + box_w * 3, kpi_y2, box_w - 2, "AV ENGINES", str(vt.get("total_engines", 0)), COLOR_ACCENT)

    pdf.set_y(kpi_y2 + 28)
    pdf.ln(5)

    # Findings summary table
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "Finding Distribution by Severity", ln=True)
    pdf.ln(2)

    # Table header
    pdf.set_fill_color(*COLOR_PRIMARY)
    pdf.set_text_color(*COLOR_WHITE)
    pdf.set_font("Helvetica", "B", 9)
    col_w = (page_width - 20) / 4
    for h in ["Severity", "Count", "% of Total", "Risk Level"]:
        pdf.cell(col_w, 8, h, border=1, fill=True, align="C")
    pdf.ln()

    pdf.set_text_color(*COLOR_PRIMARY)
    pdf.set_font("Helvetica", "", 9)
    for sev, count, color in [("Critical", crit, COLOR_CRITICAL), ("High", high, COLOR_HIGH), ("Medium", med, COLOR_MEDIUM), ("Low", low, COLOR_LOW)]:
        pct = f"{(count / total_vulns * 100):.0f}%" if total_vulns > 0 else "0%"
        risk = "Immediate" if sev == "Critical" else "Urgent" if sev == "High" else "Moderate" if sev == "Medium" else "Minor"
        pdf.set_fill_color(*COLOR_BG_LIGHT)
        pdf.cell(col_w, 7, sev, border=1, align="C")
        pdf.cell(col_w, 7, str(count), border=1, align="C")
        pdf.cell(col_w, 7, pct, border=1, align="C")
        pdf.cell(col_w, 7, risk, border=1, align="C")
        pdf.ln()

    # ════════════════════════════════════════════
    # PAGE 4: METHODOLOGY
    # ════════════════════════════════════════════
    pdf.add_page()
    add_header_footer()
    pdf.set_y(12)
    section_title("3", "ASSESSMENT METHODOLOGY")

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*COLOR_PRIMARY)
    pdf.multi_cell(0, 5, "The following automated assessment modules were used to evaluate the security posture of the target asset. Each module examines a specific security domain to provide comprehensive coverage.")
    pdf.ln(5)

    modules = [
        ("Reconnaissance & Discovery", "Domain enumeration, DNS analysis, WHOIS lookup, subdomain discovery, and technology fingerprinting to map the attack surface."),
        ("Vulnerability Scanning", "Automated vulnerability detection using Nuclei templates covering CVEs, misconfigurations, exposed panels, and known exploits."),
        ("Security Configuration Audit", "Analysis of HTTP security headers (HSTS, CSP, X-Frame-Options), SSL/TLS configuration, cookie security, and server hardening."),
        ("SIEM & Event Monitoring", "Collection and correlation of security events, log analysis, anomaly detection, and threat pattern identification."),
        ("VirusTotal Threat Intelligence", "Multi-engine malware and reputation analysis using 70+ antivirus engines and URL/domain reputation databases."),
    ]

    for name, desc in modules:
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_fill_color(*COLOR_BG_LIGHT)
        pdf.cell(0, 7, f"  {name}", ln=True, fill=True)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*COLOR_INFO)
        pdf.multi_cell(0, 4.5, f"  {desc}")
        pdf.set_text_color(*COLOR_PRIMARY)
        pdf.ln(2)

    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 7, "Scoring Methodology", ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(0, 4.5, "The security score (0-100) is calculated by aggregating results across all assessment modules. Points are deducted based on the severity and quantity of findings. Critical vulnerabilities carry the highest weight, followed by high, medium, and low severity issues. Security configuration failures and malicious threat intelligence flags also reduce the overall score.")

    # ════════════════════════════════════════════
    # PAGE 5+: DETAILED VULNERABILITIES
    # ════════════════════════════════════════════
    if details and details.get("vulnerabilities"):
        pdf.add_page()
        add_header_footer()
        pdf.set_y(12)
        section_title("4", "DETAILED VULNERABILITY FINDINGS")

        pdf.set_font("Helvetica", "", 9)
        pdf.multi_cell(0, 4.5, f"A total of {total_vulns} vulnerabilities were identified during the assessment. The following are the most significant findings ranked by severity.")
        pdf.ln(3)

        for i, vuln in enumerate(details.get("vulnerabilities", [])[:15], 1):
            severity = vuln.get("severity", "UNKNOWN").upper()
            vuln_name = _sanitize_for_pdf(vuln.get("name", "Vulnerability"))
            sev_color = get_severity_color(severity)

            if pdf.get_y() > 250:
                pdf.add_page()
                add_header_footer()
                pdf.set_y(12)

            # Severity badge
            pdf.set_fill_color(*sev_color)
            badge_y = pdf.get_y()
            pdf.rect(10, badge_y, 18, 6, "F")
            pdf.set_xy(10, badge_y)
            pdf.set_font("Helvetica", "B", 7)
            pdf.set_text_color(*COLOR_WHITE)
            pdf.cell(18, 6, severity, align="C")

            # Vuln title
            pdf.set_xy(30, badge_y)
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(*COLOR_PRIMARY)
            pdf.cell(0, 6, f"{i}. {vuln_name}", ln=True)

            # Details
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(*COLOR_INFO)
            cvss = vuln.get("cvss", "N/A")
            source = _sanitize_for_pdf(vuln.get("source", "Scanner"))
            pdf.cell(0, 5, f"   CVSS: {cvss}/10  |  Source: {source}", ln=True)

            if vuln.get("cve_id") and vuln.get("cve_id") != "N/A":
                pdf.cell(0, 5, f"   CVE: {_sanitize_for_pdf(vuln.get('cve_id'))}", ln=True)

            if vuln.get("evidence"):
                evidence = _sanitize_for_pdf(vuln.get("evidence")[:120])
                pdf.cell(0, 5, f"   Evidence: {evidence}", ln=True)

            # Recommendation based on severity
            pdf.set_font("Helvetica", "I", 8)
            if severity == "CRITICAL":
                pdf.set_text_color(*COLOR_CRITICAL)
                pdf.cell(0, 5, "   -> Remediate immediately. This poses an active exploitation risk.", ln=True)
            elif severity == "HIGH":
                pdf.set_text_color(*COLOR_HIGH)
                pdf.cell(0, 5, "   -> Fix within 3-5 days. High likelihood of exploitation.", ln=True)
            elif severity == "MEDIUM":
                pdf.set_text_color(*COLOR_MEDIUM)
                pdf.cell(0, 5, "   -> Address within 1-2 weeks. Moderate business impact.", ln=True)
            else:
                pdf.set_text_color(*COLOR_LOW)
                pdf.cell(0, 5, "   -> Include in next maintenance cycle.", ln=True)
            pdf.ln(3)

    # ════════════════════════════════════════════
    # SECURITY CONFIGURATION AUDIT
    # ════════════════════════════════════════════
    if details and details.get("defence_checks"):
        pdf.add_page()
        add_header_footer()
        pdf.set_y(12)
        section_title("5", "SECURITY CONFIGURATION AUDIT")

        checks = details.get("defence_checks", [])
        passed = sum(1 for c in checks if c.get("status") == "PASS")
        failed = sum(1 for c in checks if c.get("status") == "FAIL")
        warned = sum(1 for c in checks if c.get("status") == "WARN")
        total_checks = passed + failed + warned

        pdf.set_font("Helvetica", "", 9)
        pdf.multi_cell(0, 4.5, f"The security configuration audit evaluated {total_checks} security controls. Results: {passed} passed, {failed} failed, {warned} warnings.")
        pdf.ln(5)

        # Config results table
        pdf.set_fill_color(*COLOR_PRIMARY)
        pdf.set_text_color(*COLOR_WHITE)
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(10, 7, "#", border=1, fill=True, align="C")
        pdf.cell(18, 7, "Status", border=1, fill=True, align="C")
        pdf.cell(70, 7, "Security Check", border=1, fill=True)
        pdf.cell(0, 7, "Details", border=1, fill=True)
        pdf.ln()

        pdf.set_text_color(*COLOR_PRIMARY)
        pdf.set_font("Helvetica", "", 8)

        for i, check in enumerate(checks[:15], 1):
            status = check.get("status", "UNKNOWN")
            status_color = COLOR_LOW if status == "PASS" else COLOR_CRITICAL if status == "FAIL" else COLOR_MEDIUM
            check_name = _sanitize_for_pdf(check.get("check", "Check"))
            check_detail = _sanitize_for_pdf(check.get("detail", "")[:40])

            pdf.set_fill_color(*COLOR_BG_LIGHT)
            pdf.cell(10, 6, str(i), border=1, align="C")
            pdf.set_fill_color(*status_color)
            pdf.set_text_color(*COLOR_WHITE)
            pdf.cell(18, 6, status, border=1, align="C", fill=True)
            pdf.set_text_color(*COLOR_PRIMARY)
            pdf.set_fill_color(*COLOR_BG_LIGHT)
            pdf.cell(70, 6, check_name, border=1)
            pdf.cell(0, 6, check_detail, border=1)
            pdf.ln()

    # ════════════════════════════════════════════
    # SIEM EVENTS
    # ════════════════════════════════════════════
    if details and details.get("siem_events") and len(details.get("siem_events", [])) > 0:
        pdf.add_page()
        add_header_footer()
        pdf.set_y(12)
        section_title("6", "SECURITY EVENTS & INCIDENT DETECTION")

        events_data = details.get("siem_events", [])
        pdf.set_font("Helvetica", "", 9)
        pdf.multi_cell(0, 4.5, f"The SIEM module detected {siem.get('events', len(events_data))} security events, including {siem.get('critical', 0)} critical and {siem.get('high', 0)} high severity events. The following are the most notable events requiring attention.")
        pdf.ln(5)

        for i, event in enumerate(events_data[:10], 1):
            severity = event.get("severity", "INFO").upper()
            event_type = _sanitize_for_pdf(event.get("type", "Event"))
            event_desc = _sanitize_for_pdf(event.get("description", "")[:100])
            sev_color = get_severity_color(severity)

            pdf.set_fill_color(*sev_color)
            pdf.rect(10, pdf.get_y(), 15, 5, "F")
            pdf.set_xy(10, pdf.get_y())
            pdf.set_font("Helvetica", "B", 6)
            pdf.set_text_color(*COLOR_WHITE)
            pdf.cell(15, 5, severity, align="C")

            pdf.set_xy(27, pdf.get_y() - 1)
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(*COLOR_PRIMARY)
            pdf.cell(0, 5, f"{i}. {event_type}", ln=True)

            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(*COLOR_INFO)
            pdf.cell(0, 4, f"  {event_desc}", ln=True)
            pdf.ln(2)

    # ════════════════════════════════════════════
    # VIRUSTOTAL / THREAT ANALYSIS
    # ════════════════════════════════════════════
    pdf.add_page()
    add_header_footer()
    pdf.set_y(12)
    section_title("7", "MALWARE & THREAT ANALYSIS")

    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(0, 4.5, f"The target was analyzed using VirusTotal's multi-engine scanning platform with {vt.get('total_engines', 0)} antivirus engines.")
    pdf.ln(5)

    # VT Results KPIs
    vt_y = pdf.get_y()
    third_w = (page_width - 30) / 3
    kpi_box(10, vt_y, third_w, "MALICIOUS", str(vt.get("malicious", 0)), COLOR_CRITICAL if vt.get("malicious", 0) > 0 else COLOR_LOW)
    kpi_box(10 + third_w + 3, vt_y, third_w, "SUSPICIOUS", str(vt.get("suspicious", 0)), COLOR_MEDIUM if vt.get("suspicious", 0) > 0 else COLOR_LOW)
    kpi_box(10 + (third_w + 3) * 2, vt_y, third_w, "ENGINES SCANNED", str(vt.get("total_engines", 0)), COLOR_ACCENT)
    pdf.set_y(vt_y + 30)

    pdf.ln(3)
    malicious = vt.get("malicious", 0)
    if malicious > 0:
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*COLOR_CRITICAL)
        pdf.cell(0, 7, f"WARNING: {malicious} antivirus engine(s) flagged this target as malicious.", ln=True)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*COLOR_PRIMARY)
        pdf.multi_cell(0, 4.5, "Recommended Actions:\n- Investigate the flagged content immediately\n- Check for malware, phishing pages, or malicious scripts\n- Consider temporarily taking the site offline if confirmed\n- Submit to VirusTotal for re-analysis after remediation")
    else:
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*COLOR_LOW)
        pdf.cell(0, 7, "No malicious flags detected across all engines.", ln=True)
        pdf.set_text_color(*COLOR_PRIMARY)
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(0, 5, "The target appears clean according to current threat intelligence databases.", ln=True)

    # ════════════════════════════════════════════
    # REMEDIATION ROADMAP
    # ════════════════════════════════════════════
    pdf.add_page()
    add_header_footer()
    pdf.set_y(12)
    section_title("8", "REMEDIATION ROADMAP")

    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(0, 4.5, "Based on the assessment findings, the following remediation priorities are recommended. Items are ordered by severity and potential business impact.")
    pdf.ln(5)

    priorities = []
    if crit > 0:
        priorities.append(("IMMEDIATE (Within 24 Hours)", COLOR_CRITICAL, [
            f"Remediate {crit} critical vulnerability/vulnerabilities",
            "Conduct emergency security assessment",
            "Notify stakeholders per incident response procedures",
        ]))
    if high > 0:
        priorities.append(("SHORT-TERM (Within 1 Week)", COLOR_HIGH, [
            f"Address {high} high-severity finding(s)",
            "Deploy temporary mitigations while developing permanent fixes",
            "Update WAF/IDS rules to mitigate known attack vectors",
        ]))
    if med > 0 or defence.get("fail", 0) > 0:
        priorities.append(("MEDIUM-TERM (Within 2 Weeks)", COLOR_MEDIUM, [
            f"Fix {med} medium-severity vulnerabilities" if med > 0 else None,
            f"Remediate {defence.get('fail', 0)} configuration failures" if defence.get('fail', 0) > 0 else None,
            "Harden TLS/SSL configuration",
        ]))
    priorities.append(("ONGOING", COLOR_ACCENT, [
        "Implement continuous security monitoring",
        "Schedule monthly vulnerability assessments",
        "Keep all software, frameworks, and plugins updated",
        "Conduct security awareness training for staff",
        "Maintain incident response procedures",
        "Review and test backup/recovery processes",
    ]))

    for title, color, items in priorities:
        pdf.set_fill_color(*color)
        pdf.rect(10, pdf.get_y(), page_width - 20, 7, "F")
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*COLOR_WHITE)
        pdf.set_x(12)
        pdf.cell(0, 7, title)
        pdf.ln()
        pdf.set_text_color(*COLOR_PRIMARY)
        pdf.set_font("Helvetica", "", 9)
        for item in items:
            if item is None:
                continue
            pdf.cell(0, 5, f"  - {item}", ln=True)
        pdf.ln(4)

    # ════════════════════════════════════════════
    # SEVERITY DEFINITIONS & GLOSSARY
    # ════════════════════════════════════════════
    pdf.add_page()
    add_header_footer()
    pdf.set_y(12)
    section_title("9", "SEVERITY DEFINITIONS & GLOSSARY")

    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 6, "The following severity levels are used throughout this report:", ln=True)
    pdf.ln(3)

    severity_defs = [
        ("CRITICAL", COLOR_CRITICAL, "CVSS 9.0-10.0", "Immediate exploitation risk. System compromise is likely. Requires emergency action within 24 hours."),
        ("HIGH", COLOR_HIGH, "CVSS 7.0-8.9", "Significant risk of exploitation. Could lead to major data breach or service disruption. Fix within 1 week."),
        ("MEDIUM", COLOR_MEDIUM, "CVSS 4.0-6.9", "Moderate risk. May be exploited in targeted attacks. Address within 2 weeks."),
        ("LOW", COLOR_LOW, "CVSS 0.1-3.9", "Low risk. Unlikely to be exploited alone but may contribute to larger attack chains. Address in next cycle."),
    ]

    for label, color, cvss, desc in severity_defs:
        pdf.set_fill_color(*color)
        pdf.rect(10, pdf.get_y(), 20, 6, "F")
        pdf.set_xy(10, pdf.get_y())
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(*COLOR_WHITE)
        pdf.cell(20, 6, label, align="C")
        pdf.set_text_color(*COLOR_PRIMARY)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(30, 6, f"  {cvss}")
        pdf.set_font("Helvetica", "", 8)
        pdf.cell(0, 6, f"  {desc[:80]}", ln=True)
        pdf.set_font("Helvetica", "", 7)
        if len(desc) > 80:
            pdf.cell(0, 4, f"  {desc[80:]}", ln=True)
        pdf.ln(2)

    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 7, "Glossary", ln=True)
    pdf.set_font("Helvetica", "", 8)
    glossary = [
        ("CVE", "Common Vulnerabilities and Exposures - standardized vulnerability identifier"),
        ("CVSS", "Common Vulnerability Scoring System - severity rating from 0.0 to 10.0"),
        ("HSTS", "HTTP Strict Transport Security - forces HTTPS connections"),
        ("CSP", "Content Security Policy - prevents cross-site scripting attacks"),
        ("WAF", "Web Application Firewall - filters malicious HTTP traffic"),
        ("SIEM", "Security Information and Event Management - centralized log monitoring"),
        ("TLS/SSL", "Transport Layer Security - encrypts data in transit"),
    ]
    for term, definition in glossary:
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(18, 5, term)
        pdf.set_font("Helvetica", "", 8)
        pdf.cell(0, 5, f"- {definition}", ln=True)

    # ════════════════════════════════════════════
    # FINAL PAGE: REPORT DETAILS & DISCLAIMER
    # ════════════════════════════════════════════
    pdf.add_page()
    add_header_footer()
    pdf.set_y(12)

    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(*COLOR_PRIMARY)
    pdf.cell(0, 10, "Report Information", ln=True)
    pdf.ln(3)

    # Report metadata table
    pdf.set_fill_color(*COLOR_BG_LIGHT)
    meta_items = [
        ("Report ID", report_id),
        ("Generated", dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")),
        ("Target Asset", target_sanitized),
        ("Organization", org_sanitized),
        ("Analyst", author_sanitized),
        ("Assessment Type", "Automated Comprehensive Security Evaluation"),
        ("Platform", "Cyber Defence SOC Platform"),
        ("Classification", "CONFIDENTIAL"),
    ]

    for j, (label, value) in enumerate(meta_items):
        fill = j % 2 == 0
        if fill:
            pdf.set_fill_color(*COLOR_BG_LIGHT)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(50, 7, f"  {label}", border=0, fill=fill)
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(0, 7, value, border=0, fill=fill, ln=True)

    pdf.ln(10)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "Disclaimer", ln=True)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*COLOR_INFO)
    pdf.multi_cell(0, 4, "This report is generated by automated security assessment tools and represents a point-in-time evaluation of the target asset. While comprehensive, automated scanning may not identify all vulnerabilities, particularly those requiring manual testing or authentication. This report does not guarantee the absence of security issues beyond those identified. The findings and recommendations should be reviewed by qualified security professionals before implementing changes in production environments. The organization is responsible for validating findings and implementing appropriate remediation measures.")

    pdf.ln(10)
    pdf.set_fill_color(*COLOR_CRITICAL)
    pdf.rect(10, pdf.get_y(), page_width - 20, 8, "F")
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*COLOR_WHITE)
    pdf.set_x(10)
    pdf.cell(page_width - 20, 8, "CONFIDENTIAL - AUTHORIZED RECIPIENTS ONLY", align="C")
    pdf.set_text_color(*COLOR_PRIMARY)

    pdf.output(str(path))
    return str(path)


@router.post("/api/policy/generate")
def generate_policy(payload: PolicyRequest) -> dict[str, Any]:
    """Generate a security policy document."""
    policy = core.POLICIES.get(payload.policy_id, core.POLICIES["1"])
    out_dir = core.DATA_DIR / "policies"
    out_dir.mkdir(parents=True, exist_ok=True)

    filename = out_dir / f"policy_{policy['name'].replace(' ', '_')}_{core.ts()}.txt"
    with open(filename, "w", encoding="utf-8") as handle:
        handle.write(f"{policy['name'].upper()}\n")
        handle.write(f"Organisation: {payload.org_name}\n")
        handle.write(f"Generated: {dt.date.today()}\n\n")
        for title, content in policy["sections"]:
            handle.write(f"{title}\n{content}\n\n")

    return {
        "policy": policy["name"],
        "organisation": payload.org_name,
        "path": str(filename),
        "sections": [{"title": title, "content": content} for title, content in policy["sections"]],
    }


@router.post("/api/report/generate")
def generate_report(payload: ReportRequest, authorization: str = Header(None)) -> dict[str, Any]:
    """Generate a comprehensive security assessment report."""
    user = get_current_user(authorization)
    
    vuln = core.get_latest("vuln")
    defence = core.get_latest("defence")
    siem = core.get_latest("siem")
    vt = core.get_latest("virustotal")
    shodan_data = core.get_latest("shodan", user_id=user["id"])
    abuseipdb_data = core.get_latest("abuseipdb", user_id=user["id"])
    
    summary = {
        "security_score": defence.get("score", 0),
        "vulnerability_summary": vuln.get("summary", {}),
        "defence": {
            "pass": defence.get("pass", 0),
            "fail": defence.get("fail", 0),
            "warn": defence.get("warn", 0),
        },
        "siem": {
            "events": siem.get("events", 0),
            "critical": siem.get("critical", 0),
            "high": siem.get("high", 0),
            "medium": siem.get("medium", 0),
        },
        "virustotal": {
            "malicious": vt.get("malicious", 0),
            "suspicious": vt.get("suspicious", 0),
            "total_engines": vt.get("total_engines", 0),
        },
        "shodan": {
            "ports": len(shodan_data.get("ports", [])) if shodan_data and not shodan_data.get("error") else 0,
            "vulns": len(shodan_data.get("vulns", [])) if shodan_data and not shodan_data.get("error") else 0,
            "organization": shodan_data.get("organization", "N/A") if shodan_data and not shodan_data.get("error") else "N/A",
        },
        "abuseipdb": {
            "abuse_score": abuseipdb_data.get("abuse_confidence_score", 0) if abuseipdb_data and not abuseipdb_data.get("error") else 0,
            "total_reports": abuseipdb_data.get("total_reports", 0) if abuseipdb_data and not abuseipdb_data.get("error") else 0,
        },
    }
    
    details = None
    pdf_path = None
    
    if payload.include_pdf:
        pdf_path = _create_pdf_report(payload.org_name, payload.target, payload.author, summary, details)
        report_filename = pdf_path.split("/")[-1] if pdf_path else None
    else:
        report_filename = None
    
    report = auth.save_report(
        user_id=user["id"],
        target=payload.target,
        org_name=payload.org_name,
        author=payload.author,
        pdf_path=report_filename
    )
    
    return {
        "report_id": report["id"] if report else None,
        "generated_at": dt.datetime.now().isoformat(),
        "org_name": payload.org_name,
        "target": payload.target,
        "author": payload.author,
        "summary": summary,
        "details": details,
        "pdf_path": pdf_path,
    }


@router.get("/api/report/download")
def download_pdf(filename: str = None):
    """Download a generated PDF report file."""
    if not filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    # Sanitize filename to prevent directory traversal
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    pdf_path = core.DATA_DIR / "reports" / filename
    
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF file not found")

    # Mobile-friendly headers for better download support
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Content-Type": "application/pdf",
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0",
    }
    
    return FileResponse(
        path=pdf_path,
        filename=filename,
        media_type="application/pdf",
        headers=headers
    )


@router.get("/api/reports/list")
def list_user_reports(authorization: str = Header(None), limit: int = 100) -> dict:
    """Get user's generated reports."""
    user = get_current_user(authorization)
    
    # Get user's actual reports from reports table (not scan history)
    rows = auth.get_user_reports(user["id"], limit=limit)
    
    if not rows:
        return {"reports": [], "total": 0}
    
    reports = []
    for row in rows:
        # Row structure: (id, user_id, target, org_name, author, pdf_path, created_at)
        report_dict = {
            "id": row[0],
            "user_id": row[1],
            "target": row[2] if row[2] else "N/A",
            "org_name": row[3] if row[3] else "N/A",
            "author": row[4] if row[4] else "Security Analyst",
            "pdf_path": row[5],
            "generated_at": row[6],
            "status": "COMPLETED",
            "score": "--"
        }
        reports.append(report_dict)
    
    return {"reports": reports, "total": len(reports)}


@router.get("/api/reports/{report_id}")
def get_user_report(report_id: int, authorization: str = Header(None)) -> dict:
    """Get a specific report by ID (user must own the report)."""
    user = get_current_user(authorization)
    report = auth.get_report_by_id(report_id, user_id=user["id"])
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found or access denied")
    
    return report
