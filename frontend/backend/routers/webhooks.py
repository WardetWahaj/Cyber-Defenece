"""
Webhooks router for CyberDefence Platform.
Manages webhook configurations for notifications.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, HttpUrl
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from frontend.backend.db import DatabaseConnection, USE_POSTGRESQL
from frontend.backend.routers.auth_routes import get_current_user
from frontend.backend.services.notifications import send_test_notification

router = APIRouter()

# ── Database Helper Functions ──────────────────────────────────────
def execute_query(cursor, query: str, params: tuple = ()) -> None:
    """Execute query with automatic placeholder conversion."""
    if not USE_POSTGRESQL:
        query = query.replace("%s", "?")
    cursor.execute(query, params)

def fetch_query(cursor, query: str, params: tuple = ()) -> list:
    """Execute SELECT query and fetch results."""
    execute_query(cursor, query, params)
    return cursor.fetchall()

def fetch_one(cursor, query: str, params: tuple = ()) -> tuple:
    """Execute SELECT query and fetch one result."""
    execute_query(cursor, query, params)
    return cursor.fetchone()

# ── Pydantic Models ────────────────────────────────────────────────
class WebhookCreate(BaseModel):
    webhook_url: str
    webhook_type: str = "slack"
    notify_on_complete: bool = True
    notify_on_critical: bool = True

class WebhookUpdate(BaseModel):
    webhook_url: str = None
    notify_on_complete: bool = None
    notify_on_critical: bool = None
    is_active: bool = None

class WebhookResponse(BaseModel):
    id: int
    webhook_url: str
    webhook_type: str
    notify_on_complete: bool
    notify_on_critical: bool
    is_active: bool
    created_at: str

# ── Endpoint: GET /api/webhooks — List Webhooks ────────────────────
@router.get("/webhooks")
async def list_webhooks(current_user: dict = Depends(get_current_user)):
    """
    Get all webhook configurations for the user.
    
    Args:
        current_user: Authenticated user
        
    Returns:
        [{id, webhook_url, webhook_type, notify_on_complete, notify_on_critical, is_active, created_at}]
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    db = DatabaseConnection()
    conn = db.connect()
    try:
        c = conn.cursor()
        user_id = current_user.get("user_id")
        
        query = """
            SELECT id, webhook_url, webhook_type, notify_on_complete, notify_on_critical, is_active, created_at
            FROM webhook_configs
            WHERE user_id = %s
            ORDER BY created_at DESC
        """
        webhooks = fetch_query(c, query, (user_id,))
        
        return [
            {
                "id": w[0],
                "webhook_url": w[1],
                "webhook_type": w[2],
                "notify_on_complete": bool(w[3]),
                "notify_on_critical": bool(w[4]),
                "is_active": bool(w[5]),
                "created_at": w[6]
            }
            for w in webhooks
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch webhooks: {str(e)}")
    finally:
        conn.close()

# ── Endpoint: POST /api/webhooks — Create Webhook ──────────────────
@router.post("/webhooks")
async def create_webhook(webhook_data: WebhookCreate, current_user: dict = Depends(get_current_user)):
    """
    Create a new webhook configuration.
    
    Args:
        webhook_data: Webhook details
        current_user: Authenticated user
        
    Returns:
        {id, webhook_url, webhook_type, notify_on_complete, notify_on_critical, is_active}
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    if not webhook_data.webhook_url or not webhook_data.webhook_url.strip():
        raise HTTPException(status_code=400, detail="Webhook URL is required")
    
    # Validate webhook URL starts with https
    if not webhook_data.webhook_url.startswith("https://"):
        raise HTTPException(status_code=400, detail="Webhook URL must start with https://")
    
    db = DatabaseConnection()
    conn = db.connect()
    try:
        c = conn.cursor()
        user_id = current_user.get("user_id")
        
        query = """
            INSERT INTO webhook_configs (user_id, webhook_url, webhook_type, notify_on_complete, notify_on_critical)
            VALUES (%s, %s, %s, %s, %s)
        """
        execute_query(c, query, (
            user_id,
            webhook_data.webhook_url,
            webhook_data.webhook_type,
            webhook_data.notify_on_complete,
            webhook_data.notify_on_critical
        ))
        webhook_id = c.lastrowid
        
        conn.commit()
        return {
            "id": webhook_id,
            "webhook_url": webhook_data.webhook_url,
            "webhook_type": webhook_data.webhook_type,
            "notify_on_complete": webhook_data.notify_on_complete,
            "notify_on_critical": webhook_data.notify_on_critical,
            "is_active": True
        }
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create webhook: {str(e)}")
    finally:
        conn.close()

# ── Endpoint: DELETE /api/webhooks/{id} — Delete Webhook ───────────
@router.delete("/webhooks/{webhook_id}")
async def delete_webhook(webhook_id: int, current_user: dict = Depends(get_current_user)):
    """
    Delete a webhook configuration.
    
    Args:
        webhook_id: Webhook ID
        current_user: Authenticated user
        
    Returns:
        {success: true}
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    db = DatabaseConnection()
    conn = db.connect()
    try:
        c = conn.cursor()
        user_id = current_user.get("user_id")
        
        # Check if webhook belongs to user
        webhook = fetch_one(c,
            "SELECT id FROM webhook_configs WHERE id = %s AND user_id = %s",
            (webhook_id, user_id)
        )
        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook not found")
        
        # Delete webhook
        execute_query(c,
            "DELETE FROM webhook_configs WHERE id = %s",
            (webhook_id,)
        )
        
        conn.commit()
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete webhook: {str(e)}")
    finally:
        conn.close()

# ── Endpoint: PUT /api/webhooks/{id} — Update Webhook ──────────────
@router.put("/webhooks/{webhook_id}")
async def update_webhook(webhook_id: int, webhook_data: WebhookUpdate, current_user: dict = Depends(get_current_user)):
    """
    Update a webhook configuration.
    
    Args:
        webhook_id: Webhook ID
        webhook_data: Fields to update
        current_user: Authenticated user
        
    Returns:
        {id, webhook_url, webhook_type, notify_on_complete, notify_on_critical, is_active}
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    db = DatabaseConnection()
    conn = db.connect()
    try:
        c = conn.cursor()
        user_id = current_user.get("user_id")
        
        # Check if webhook belongs to user
        webhook = fetch_one(c,
            "SELECT id, webhook_url, webhook_type, notify_on_complete, notify_on_critical, is_active FROM webhook_configs WHERE id = %s AND user_id = %s",
            (webhook_id, user_id)
        )
        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook not found")
        
        # Build update query with provided fields
        updates = []
        params = []
        
        if webhook_data.webhook_url is not None:
            if not webhook_data.webhook_url.startswith("https://"):
                raise HTTPException(status_code=400, detail="Webhook URL must start with https://")
            updates.append("webhook_url = %s")
            params.append(webhook_data.webhook_url)
        
        if webhook_data.notify_on_complete is not None:
            updates.append("notify_on_complete = %s")
            params.append(webhook_data.notify_on_complete)
        
        if webhook_data.notify_on_critical is not None:
            updates.append("notify_on_critical = %s")
            params.append(webhook_data.notify_on_critical)
        
        if webhook_data.is_active is not None:
            updates.append("is_active = %s")
            params.append(webhook_data.is_active)
        
        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        params.append(webhook_id)
        
        query = f"UPDATE webhook_configs SET {', '.join(updates)} WHERE id = %s"
        execute_query(c, query, tuple(params))
        
        conn.commit()
        
        # Fetch and return updated webhook
        updated = fetch_one(c,
            "SELECT id, webhook_url, webhook_type, notify_on_complete, notify_on_critical, is_active FROM webhook_configs WHERE id = %s",
            (webhook_id,)
        )
        
        return {
            "id": updated[0],
            "webhook_url": updated[1],
            "webhook_type": updated[2],
            "notify_on_complete": bool(updated[3]),
            "notify_on_critical": bool(updated[4]),
            "is_active": bool(updated[5])
        }
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update webhook: {str(e)}")
    finally:
        conn.close()

# ── Endpoint: POST /api/webhooks/test — Send Test Notification ─────
@router.post("/webhooks/test")
async def test_webhook(webhook_id: int = None, webhook_url: str = None, current_user: dict = Depends(get_current_user)):
    """
    Send a test notification to verify webhook is working.
    Either webhook_id (existing) or webhook_url (new) must be provided.
    
    Args:
        webhook_id: Optional - test an existing webhook
        webhook_url: Optional - test a new webhook URL
        current_user: Authenticated user
        
    Returns:
        {success: true, message: "Test notification sent"}
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    test_url = None
    
    if webhook_id:
        # Test existing webhook
        db = DatabaseConnection()
        conn = db.connect()
        try:
            c = conn.cursor()
            user_id = current_user.get("user_id")
            
            webhook = fetch_one(c,
                "SELECT webhook_url, webhook_type FROM webhook_configs WHERE id = %s AND user_id = %s",
                (webhook_id, user_id)
            )
            if not webhook:
                raise HTTPException(status_code=404, detail="Webhook not found")
            
            test_url = webhook[0]
            webhook_type = webhook[1]
        finally:
            conn.close()
    elif webhook_url:
        # Test new webhook
        if not webhook_url.startswith("https://"):
            raise HTTPException(status_code=400, detail="Webhook URL must start with https://")
        test_url = webhook_url
        webhook_type = "slack"
    else:
        raise HTTPException(status_code=400, detail="Either webhook_id or webhook_url must be provided")
    
    # Send test notification
    success = send_test_notification(test_url, webhook_type)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send test notification. Check webhook URL and try again.")
    
    return {
        "success": True,
        "message": "Test notification sent successfully"
    }
