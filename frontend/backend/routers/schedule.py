"""
Scheduled scans router for recurring security scans.

Endpoints:
- POST /api/schedules - Create a new scheduled scan
- GET /api/schedules - List user's scheduled scans
- DELETE /api/schedules/{schedule_id} - Delete a scheduled scan
- PUT /api/schedules/{schedule_id}/toggle - Enable/disable a schedule
"""

from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel

from frontend.backend.auth import get_user_by_id
from frontend.backend.routers.auth_routes import get_current_user
from frontend.backend.db import DatabaseConnection, USE_POSTGRESQL

router = APIRouter()


class ScheduleCreate(BaseModel):
    target: str
    scan_mode: str = "Comprehensive"
    frequency: str  # "daily", "weekly", "monthly"


class ScheduleResponse(BaseModel):
    id: int
    user_id: int
    target: str
    scan_mode: str
    frequency: str
    next_run: str
    last_run: str | None
    is_active: bool
    created_at: str


def calculate_next_run(frequency: str) -> datetime:
    """Calculate next run time based on frequency."""
    now = datetime.now(timezone.utc)
    
    if frequency == "daily":
        return now + timedelta(days=1)
    elif frequency == "weekly":
        return now + timedelta(weeks=1)
    elif frequency == "monthly":
        return now + timedelta(days=30)
    else:
        return now + timedelta(weeks=1)  # Default to weekly


@router.post("/api/schedules", response_model=ScheduleResponse)
def create_schedule(
    schedule: ScheduleCreate,
    authorization: str = Header(None)
):
    """Create a new scheduled scan for the authenticated user."""
    # Get current user
    user = get_current_user(authorization)
    user_id = user["id"]
    
    # Validate input
    if not schedule.target or len(schedule.target.strip()) == 0:
        raise HTTPException(status_code=400, detail="Target cannot be empty")
    
    if schedule.frequency not in ["daily", "weekly", "monthly"]:
        raise HTTPException(status_code=400, detail="Frequency must be 'daily', 'weekly', or 'monthly'")
    
    # Calculate next run time
    next_run = calculate_next_run(schedule.frequency)
    
    # Insert into database
    db = DatabaseConnection()
    conn = db.connect()
    try:
        c = conn.cursor()
        
        # Insert schedule
        now = datetime.now(timezone.utc).isoformat()
        
        if USE_POSTGRESQL:
            c.execute("""
                INSERT INTO scheduled_scans 
                (user_id, target, scan_mode, frequency, next_run, is_active, created_at)
                VALUES (%s, %s, %s, %s, %s, TRUE, %s)
                RETURNING id, user_id, target, scan_mode, frequency, next_run, last_run, is_active, created_at
            """, (user_id, schedule.target, schedule.scan_mode, schedule.frequency, next_run.isoformat(), now))
            row = c.fetchone()
        else:
            c.execute("""
                INSERT INTO scheduled_scans 
                (user_id, target, scan_mode, frequency, next_run, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, 1, ?)
            """, (user_id, schedule.target, schedule.scan_mode, schedule.frequency, next_run.isoformat(), now))
            
            # Get the inserted row
            schedule_id = c.lastrowid
            if USE_POSTGRESQL:
                c.execute("SELECT * FROM scheduled_scans WHERE id = %s", (schedule_id,))
            else:
                c.execute("SELECT * FROM scheduled_scans WHERE id = ?", (schedule_id,))
            row = c.fetchone()
        
        conn.commit()
        
        return ScheduleResponse(
            id=row[0],
            user_id=row[1],
            target=row[2],
            scan_mode=row[3],
            frequency=row[4],
            next_run=row[5],
            last_run=row[6],
            is_active=bool(row[7]),
            created_at=row[8]
        )
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create schedule: {str(e)}")
    finally:
        conn.close()


@router.get("/api/schedules")
def get_schedules(authorization: str = Header(None)):
    """Get all scheduled scans for the authenticated user."""
    # Get current user
    user = get_current_user(authorization)
    user_id = user["id"]
    
    # Query database
    db = DatabaseConnection()
    conn = db.connect()
    try:
        c = conn.cursor()
        
        if USE_POSTGRESQL:
            c.execute(
                "SELECT id, user_id, target, scan_mode, frequency, next_run, last_run, is_active, created_at FROM scheduled_scans WHERE user_id = %s ORDER BY created_at DESC",
                (user_id,)
            )
        else:
            c.execute(
                "SELECT id, user_id, target, scan_mode, frequency, next_run, last_run, is_active, created_at FROM scheduled_scans WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,)
            )
        
        rows = c.fetchall()
        
        schedules = []
        for row in rows:
            schedules.append({
                "id": row[0],
                "user_id": row[1],
                "target": row[2],
                "scan_mode": row[3],
                "frequency": row[4],
                "next_run": row[5],
                "last_run": row[6],
                "is_active": bool(row[7]),
                "created_at": row[8]
            })
        
        return {"schedules": schedules, "count": len(schedules)}
    finally:
        conn.close()


@router.delete("/api/schedules/{schedule_id}")
def delete_schedule(
    schedule_id: int,
    authorization: str = Header(None)
):
    """Delete a scheduled scan (only owner can delete)."""
    # Get current user
    user = get_current_user(authorization)
    user_id = user["id"]
    
    # Verify ownership
    db = DatabaseConnection()
    conn = db.connect()
    try:
        c = conn.cursor()
        
        if USE_POSTGRESQL:
            c.execute("SELECT user_id FROM scheduled_scans WHERE id = %s", (schedule_id,))
        else:
            c.execute("SELECT user_id FROM scheduled_scans WHERE id = ?", (schedule_id,))
        
        row = c.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        if row[0] != user_id:
            raise HTTPException(status_code=403, detail="You can only delete your own schedules")
        
        # Delete schedule
        if USE_POSTGRESQL:
            c.execute("DELETE FROM scheduled_scans WHERE id = %s", (schedule_id,))
        else:
            c.execute("DELETE FROM scheduled_scans WHERE id = ?", (schedule_id,))
        
        conn.commit()
        
        return {"success": True, "message": "Schedule deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete schedule: {str(e)}")
    finally:
        conn.close()


@router.put("/api/schedules/{schedule_id}/toggle")
def toggle_schedule(
    schedule_id: int,
    authorization: str = Header(None)
):
    """Toggle a schedule between active and inactive."""
    # Get current user
    user = get_current_user(authorization)
    user_id = user["id"]
    
    # Verify ownership and toggle
    db = DatabaseConnection()
    conn = db.connect()
    try:
        c = conn.cursor()
        
        if USE_POSTGRESQL:
            c.execute("SELECT user_id, is_active FROM scheduled_scans WHERE id = %s", (schedule_id,))
        else:
            c.execute("SELECT user_id, is_active FROM scheduled_scans WHERE id = ?", (schedule_id,))
        
        row = c.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        if row[0] != user_id:
            raise HTTPException(status_code=403, detail="You can only modify your own schedules")
        
        # Toggle is_active
        new_state = not bool(row[1])
        
        if USE_POSTGRESQL:
            c.execute("UPDATE scheduled_scans SET is_active = %s WHERE id = %s", (new_state, schedule_id))
        else:
            c.execute("UPDATE scheduled_scans SET is_active = ? WHERE id = ?", (1 if new_state else 0, schedule_id))
        
        conn.commit()
        
        return {"success": True, "is_active": new_state, "message": f"Schedule {'enabled' if new_state else 'disabled'}"}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to toggle schedule: {str(e)}")
    finally:
        conn.close()
