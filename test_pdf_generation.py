import sys
from pathlib import Path

# Add root to path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

# Import the API module
from frontend.backend import api

# Create test data
summary = {
    "security_score": 65,
    "vulnerability_summary": {
        "critical": 1,
        "high": 2,
        "medium": 3,
        "low": 2
    },
    "defence": {
        "pass": 8,
        "fail": 2,
        "warn": 4
    },
    "siem": {
        "events": 12,
        "critical": 2,
        "high": 3,
        "medium": 4
    },
    "virustotal": {
        "malicious": 0,
        "suspicious": 1,
        "total_engines": 94
    }
}

details = {
    "vulnerabilities": [
        {
            "name": "SQL Injection",
            "severity": "CRITICAL",
            "cvss": "9.1",
            "source": "nuclei",
            "cve_id": "CVE-2021-12345",
            "evidence": "Found SQL injection vulnerability in login form"
        },
        {
            "name": "Missing Security Header",
            "severity": "HIGH",
            "cvss": "7.2",
            "source": "live_check",
            "cve_id": "N/A",
            "evidence": "Content-Security-Policy header missing"
        },
        {
            "name": "Weak SSL Configuration",
            "severity": "HIGH",
            "cvss": "7.5",
            "source": "live_check",
            "cve_id": "N/A",
            "evidence": "TLS 1.0 protocol still enabled"
        }
    ],
    "defence_checks": [
        {
            "name": "HTTPS/SSL Certificate",
            "status": "PASS",
            "description": "Valid certificate installed"
        },
        {
            "name": "Security Headers",
            "status": "FAIL",
            "description": "Missing multiple security headers"
        },
        {
            "name": "WAF Protection",
            "status": "WARN",
            "description": "WAF status could not be verified"
        }
    ],
    "siem_events": [
        {
            "type": "Brute Force Attempt",
            "severity": "CRITICAL",
            "description": "Multiple failed login attempts detected"
        },
        {
            "type": "Suspicious File Access",
            "severity": "HIGH",
            "description": "Unauthorized file access detected"
        }
    ]
}

try:
    # Test the PDF generation
    pdf_path = api._create_pdf_report("Test Org", "example.com", "Test Analyst", summary, details)
    print(f"[SUCCESS] PDF generated: {pdf_path}")
    
    # Check if file exists
    if Path(pdf_path).exists():
        file_size = Path(pdf_path).stat().st_size
        print(f"[SUCCESS] File exists with size: {file_size} bytes")
    else:
        print("[ERROR] PDF file not found")
except Exception as e:
    print(f"[ERROR] PDF generation failed: {e}")
    import traceback
    traceback.print_exc()
