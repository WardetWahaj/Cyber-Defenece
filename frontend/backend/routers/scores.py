"""
Score history router for tracking and retrieving security score trends.

Endpoints:
- GET /api/scores/history - Get score history for a target
- POST /api/scores/save - Save a score to history (internal use)
"""

from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Header, Query
from pydantic import BaseModel

from frontend.backend.routers.auth_routes import get_current_user
from frontend.backend.db import DatabaseConnection, USE_POSTGRESQL

router = APIRouter()


class ScoreSaveRequest(BaseModel):
    target: str
    score: int
    grade: str
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0


class ScoreHistoryItem(BaseModel):
    id: int
    target: str
    score: int
    grade: str
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    scanned_at: str


def calculate_grade(score: int) -> str:
    """Calculate grade from score."""
    if score >= 80:
        return "A"
    elif score >= 60:
        return "B"
    elif score >= 40:
        return "C"
    else:
        return "D"


@router.post("/api/scores/save")
def save_score(
    request: ScoreSaveRequest,
    authorization: str = Header(None)
):
    """Save a security score to history (internal endpoint used by scan completion)."""
    # Get current user
    user = get_current_user(authorization)
    user_id = user["id"]
    
    # Validate input
    if not request.target or len(request.target.strip()) == 0:
        raise HTTPException(status_code=400, detail="Target cannot be empty")
    
    if request.score < 0 or request.score > 100:
        raise HTTPException(status_code=400, detail="Score must be between 0 and 100")
    
    grade = calculate_grade(request.score)
    
    # Insert into database
    db = DatabaseConnection()
    conn = db.connect()
    try:
        c = conn.cursor()
        now = datetime.now(timezone.utc).isoformat()
        
        if USE_POSTGRESQL:
            c.execute("""
                INSERT INTO score_history 
                (user_id, target, score, grade, critical_count, high_count, medium_count, low_count, scanned_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, target, score, grade, critical_count, high_count, medium_count, low_count, scanned_at
            """, (user_id, request.target, request.score, grade, 
                  request.critical_count, request.high_count, request.medium_count, request.low_count, now))
            row = c.fetchone()
        else:
            c.execute("""
                INSERT INTO score_history 
                (user_id, target, score, grade, critical_count, high_count, medium_count, low_count, scanned_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, request.target, request.score, grade,
                  request.critical_count, request.high_count, request.medium_count, request.low_count, now))
            
            score_id = c.lastrowid
            if USE_POSTGRESQL:
                c.execute("SELECT * FROM score_history WHERE id = %s", (score_id,))
            else:
                c.execute("SELECT * FROM score_history WHERE id = ?", (score_id,))
            row = c.fetchone()
        
        conn.commit()
        
        return {
            "success": True,
            "score_id": row[0],
            "score": row[2],
            "grade": row[3]
        }
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save score: {str(e)}")
    finally:
        conn.close()


@router.get("/api/scores/history")
def get_score_history(
    target: str = Query(..., description="Target domain or IP"),
    limit: int = Query(30, ge=1, le=100, description="Number of records"),
    authorization: str = Header(None)
):
    """Get score history for a target."""
    # Get current user
    user = get_current_user(authorization)
    user_id = user["id"]
    
    # Query database
    db = DatabaseConnection()
    conn = db.connect()
    try:
        c = conn.cursor()
        
        if USE_POSTGRESQL:
            c.execute("""
                SELECT id, target, score, grade, critical_count, high_count, medium_count, low_count, scanned_at
                FROM score_history 
                WHERE user_id = %s AND target = %s
                ORDER BY scanned_at DESC
                LIMIT %s
            """, (user_id, target, limit))
        else:
            c.execute("""
                SELECT id, target, score, grade, critical_count, high_count, medium_count, low_count, scanned_at
                FROM score_history 
                WHERE user_id = ? AND target = ?
                ORDER BY scanned_at DESC
                LIMIT ?
            """, (user_id, target, limit))
        
        rows = c.fetchall()
        
        history = []
        for row in rows:
            history.append({
                "id": row[0],
                "target": row[1],
                "score": row[2],
                "grade": row[3],
                "critical_count": row[4],
                "high_count": row[5],
                "medium_count": row[6],
                "low_count": row[7],
                "scanned_at": row[8]
            })
        
        # Calculate trend
        trend = None
        if len(history) >= 2:
            latest = history[0]["score"]
            previous = history[1]["score"]
            change = latest - previous
            trend = {
                "change": change,
                "direction": "up" if change > 0 else "down" if change < 0 else "neutral",
                "display": f"{'+' if change > 0 else ''}{change} points since last scan"
            }
        
        return {
            "target": target,
            "history": history,
            "count": len(history),
            "trend": trend
        }
    finally:
        conn.close()
