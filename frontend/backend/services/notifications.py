"""
Notification service for CyberDefence Platform.
Handles sending notifications via webhooks (Slack, etc.) when scans complete or critical vulnerabilities are found.
"""

import time
import requests
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from frontend.backend.db import DatabaseConnection, USE_POSTGRESQL

def execute_query(cursor, query: str, params: tuple = ()) -> None:
    """Execute query with automatic placeholder conversion."""
    if not USE_POSTGRESQL:
        query = query.replace("%s", "?")
    cursor.execute(query, params)

def fetch_query(cursor, query: str, params: tuple = ()) -> list:
    """Execute SELECT query and fetch results."""
    execute_query(cursor, query, params)
    return cursor.fetchall()

def send_slack_notification(webhook_url: str, message: str, color: str = "#36a64f") -> bool:
    """
    Send a notification to Slack via webhook.
    
    Args:
        webhook_url: Slack webhook URL
        message: Message text (supports markdown)
        color: Hex color code for the attachment bar
        
    Returns:
        True if successful, False otherwise
    """
    try:
        payload = {
            "attachments": [{
                "color": color,
                "text": message,
                "footer": "🔒 Cyber Defence SOC Platform",
                "ts": int(time.time())
            }]
        }
        response = requests.post(webhook_url, json=payload, timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"[!] Failed to send Slack notification: {str(e)}")
        return False

def notify_scan_complete(user_id: int, target: str, score: int, grade: str, vuln_counts: dict):
    """
    Send notification when a scan completes.
    
    Args:
        user_id: User ID
        target: Target scanned
        score: Security score (0-100)
        grade: Grade (A, B, C, D)
        vuln_counts: Dict with keys: critical, high, medium, low
    """
    db = DatabaseConnection()
    conn = db.connect()
    try:
        c = conn.cursor()
        
        # Get active webhook configs for user with notify_on_complete enabled
        query = """
            SELECT id, webhook_url, webhook_type FROM webhook_configs
            WHERE user_id = %s AND is_active = TRUE AND notify_on_complete = TRUE
        """
        webhooks = fetch_query(c, query, (user_id,))
        
        if not webhooks:
            return  # No webhooks configured
        
        # Determine color based on grade
        if grade in ("D", "F"):
            color = "#dc2626"  # Red
            grade_emoji = "🔴"
        elif grade == "C":
            color = "#fbbf24"  # Yellow
            grade_emoji = "🟡"
        else:  # A, B
            color = "#36a64f"  # Green
            grade_emoji = "🟢"
        
        # Format vulnerability counts
        c_count = vuln_counts.get("critical", 0)
        h_count = vuln_counts.get("high", 0)
        m_count = vuln_counts.get("medium", 0)
        l_count = vuln_counts.get("low", 0)
        
        message = f"""✅ *Scan Completed*
Target: `{target}`
{grade_emoji} Score: *{score}/100* (Grade: *{grade}*)
🐛 Vulnerabilities: *{c_count}C* / *{h_count}H* / *{m_count}M* / *{l_count}L*"""
        
        # Send to all configured webhooks
        for webhook_id, webhook_url, webhook_type in webhooks:
            if webhook_type == "slack":
                send_slack_notification(webhook_url, message, color)
    finally:
        conn.close()

def notify_critical_vulnerability(user_id: int, target: str, vuln_count: int):
    """
    Send notification when critical vulnerabilities are found.
    
    Args:
        user_id: User ID
        target: Target with critical vulnerabilities
        vuln_count: Number of critical vulnerabilities
    """
    db = DatabaseConnection()
    conn = db.connect()
    try:
        c = conn.cursor()
        
        # Get active webhook configs for user with notify_on_critical enabled
        query = """
            SELECT id, webhook_url, webhook_type FROM webhook_configs
            WHERE user_id = %s AND is_active = TRUE AND notify_on_critical = TRUE
        """
        webhooks = fetch_query(c, query, (user_id,))
        
        if not webhooks:
            return  # No webhooks configured
        
        message = f"""🚨 *CRITICAL VULNERABILITIES FOUND*
Target: `{target}`
Critical Issues: *{vuln_count}*
Action Required: Immediate investigation and remediation recommended."""
        
        # Send to all configured webhooks (always red for critical)
        for webhook_id, webhook_url, webhook_type in webhooks:
            if webhook_type == "slack":
                send_slack_notification(webhook_url, message, "#dc2626")  # Red
    finally:
        conn.close()

def send_test_notification(webhook_url: str, webhook_type: str = "slack") -> bool:
    """
    Send a test notification to verify webhook is working.
    
    Args:
        webhook_url: Webhook URL to test
        webhook_type: Type of webhook (slack, etc.)
        
    Returns:
        True if successful, False otherwise
    """
    message = """🧪 *Test Notification from Cyber Defence*
This is a test notification to verify your webhook is properly configured.
If you see this message, your integration is working!"""
    
    if webhook_type == "slack":
        return send_slack_notification(webhook_url, message, "#3b82f6")  # Blue
    
    return False
