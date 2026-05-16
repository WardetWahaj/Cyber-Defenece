"""
Team collaboration router for CyberDefence Platform.
Enables users to create teams, manage members, and share scan results.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from frontend.backend.db import DatabaseConnection, USE_POSTGRESQL
from frontend.backend.routers.auth_routes import get_current_user

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
class TeamCreate(BaseModel):
    name: str

class TeamMemberInvite(BaseModel):
    email: str
    role: str = "viewer"  # "owner", "analyst", "viewer"

class TeamResponse(BaseModel):
    id: int
    name: str
    created_by: int
    created_at: str
    role: str  # User's role in this team

class TeamMember(BaseModel):
    id: int
    user_id: int
    email: str
    full_name: str
    role: str
    joined_at: str

# ── Endpoint: POST /api/teams — Create Team ────────────────────────
@router.post("/teams")
async def create_team(team_data: TeamCreate, current_user: dict = Depends(get_current_user)):
    """
    Create a new team. Creator becomes owner.
    
    Args:
        team_data: Team name
        current_user: Authenticated user
        
    Returns:
        {id, name, created_by, role: "owner"}
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    db = DatabaseConnection()
    conn = db.connect()
    try:
        c = conn.cursor()
        user_id = current_user.get("id")
        
        # Create team
        execute_query(c, 
            "INSERT INTO teams (name, created_by) VALUES (%s, %s)",
            (team_data.name, user_id)
        )
        team_id = c.lastrowid
        
        # Add creator as owner
        execute_query(c,
            "INSERT INTO team_members (team_id, user_id, role) VALUES (%s, %s, %s)",
            (team_id, user_id, "owner")
        )
        
        conn.commit()
        return {
            "id": team_id,
            "name": team_data.name,
            "created_by": user_id,
            "role": "owner"
        }
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create team: {str(e)}")
    finally:
        conn.close()

# ── Endpoint: GET /api/teams — List User's Teams ────────────────────
@router.get("/teams")
async def list_teams(current_user: dict = Depends(get_current_user)):
    """
    Get all teams the user belongs to with member and scan info.
    
    Args:
        current_user: Authenticated user
        
    Returns:
        [{id, name, created_by, created_at, role, member_count, scan_count}]
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    db = DatabaseConnection()
    conn = db.connect()
    try:
        c = conn.cursor()
        user_id = current_user.get("id")
        
        # Get teams with member role and counts
        query = """
            SELECT 
                t.id, t.name, t.created_by, t.created_at, tm.role,
                (SELECT COUNT(*) FROM team_members WHERE team_id = t.id) as member_count,
                (SELECT COUNT(*) FROM team_shared_scans WHERE team_id = t.id) as scan_count
            FROM teams t
            JOIN team_members tm ON t.id = tm.team_id
            WHERE tm.user_id = %s
            ORDER BY t.created_at DESC
        """
        teams = fetch_query(c, query, (user_id,))
        
        return [
            {
                "id": team[0],
                "name": team[1],
                "created_by": team[2],
                "created_at": team[3],
                "role": team[4],
                "member_count": team[5],
                "scan_count": team[6]
            }
            for team in teams
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch teams: {str(e)}")
    finally:
        conn.close()

# ── Endpoint: POST /api/teams/{team_id}/invite — Invite User ───────
@router.post("/teams/{team_id}/invite")
async def invite_user(team_id: int, invite_data: TeamMemberInvite, current_user: dict = Depends(get_current_user)):
    """
    Invite a user to team by email. Only owner/analyst can invite.
    
    Args:
        team_id: Team ID
        invite_data: Email and role to assign
        current_user: Authenticated user
        
    Returns:
        {success: true, user_id, email, role}
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    db = DatabaseConnection()
    conn = db.connect()
    try:
        c = conn.cursor()
        user_id = current_user.get("id")
        
        # Check if requester is owner/analyst of team
        member = fetch_one(c,
            "SELECT role FROM team_members WHERE team_id = %s AND user_id = %s",
            (team_id, user_id)
        )
        if not member:
            raise HTTPException(status_code=403, detail="Not a member of this team")
        if member[0] not in ["owner", "analyst"]:
            raise HTTPException(status_code=403, detail="Only owners and analysts can invite members")
        
        # Check if team exists
        team = fetch_one(c, "SELECT id FROM teams WHERE id = %s", (team_id,))
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        
        # Find user by email
        target_user = fetch_one(c,
            "SELECT id, email, full_name FROM users WHERE email = %s",
            (invite_data.email,)
        )
        if not target_user:
            raise HTTPException(status_code=404, detail=f"User with email {invite_data.email} not found")
        
        target_user_id = target_user[0]
        
        # Check if already a member
        existing = fetch_one(c,
            "SELECT id FROM team_members WHERE team_id = %s AND user_id = %s",
            (team_id, target_user_id)
        )
        if existing:
            raise HTTPException(status_code=400, detail="User is already a member of this team")
        
        # Add member with specified role
        execute_query(c,
            "INSERT INTO team_members (team_id, user_id, role) VALUES (%s, %s, %s)",
            (team_id, target_user_id, invite_data.role)
        )
        
        conn.commit()
        return {
            "success": True,
            "user_id": target_user_id,
            "email": target_user[1],
            "full_name": target_user[2],
            "role": invite_data.role
        }
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to invite user: {str(e)}")
    finally:
        conn.close()

# ── Endpoint: DELETE /api/teams/{team_id}/members/{member_user_id} ────
@router.delete("/teams/{team_id}/members/{member_user_id}")
async def remove_member(team_id: int, member_user_id: int, current_user: dict = Depends(get_current_user)):
    """
    Remove a member from team. Only owner can remove.
    
    Args:
        team_id: Team ID
        member_user_id: User ID to remove
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
        user_id = current_user.get("id")
        
        # Check if requester is owner
        member = fetch_one(c,
            "SELECT role FROM team_members WHERE team_id = %s AND user_id = %s",
            (team_id, user_id)
        )
        if not member:
            raise HTTPException(status_code=403, detail="Not a member of this team")
        if member[0] != "owner":
            raise HTTPException(status_code=403, detail="Only team owners can remove members")
        
        # Can't remove owner (only way to remove owner is delete team)
        target_member = fetch_one(c,
            "SELECT role FROM team_members WHERE team_id = %s AND user_id = %s",
            (team_id, member_user_id)
        )
        if not target_member:
            raise HTTPException(status_code=404, detail="Member not found in team")
        if target_member[0] == "owner":
            raise HTTPException(status_code=400, detail="Cannot remove team owner")
        
        # Remove member
        execute_query(c,
            "DELETE FROM team_members WHERE team_id = %s AND user_id = %s",
            (team_id, member_user_id)
        )
        
        conn.commit()
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to remove member: {str(e)}")
    finally:
        conn.close()

# ── Endpoint: GET /api/teams/{team_id}/members — Get Team Members ────
@router.get("/teams/{team_id}/members")
async def get_team_members(team_id: int, current_user: dict = Depends(get_current_user)):
    """
    Get all members of a team.
    
    Args:
        team_id: Team ID
        current_user: Authenticated user
        
    Returns:
        [{id, user_id, email, full_name, role, joined_at}]
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    db = DatabaseConnection()
    conn = db.connect()
    try:
        c = conn.cursor()
        user_id = current_user.get("id")
        
        # Check if requester is member of team
        member = fetch_one(c,
            "SELECT id FROM team_members WHERE team_id = %s AND user_id = %s",
            (team_id, user_id)
        )
        if not member:
            raise HTTPException(status_code=403, detail="Not a member of this team")
        
        # Get all members with user details
        query = """
            SELECT tm.id, tm.user_id, u.email, u.full_name, tm.role, tm.joined_at
            FROM team_members tm
            JOIN users u ON tm.user_id = u.id
            WHERE tm.team_id = %s
            ORDER BY tm.role DESC, u.full_name ASC
        """
        members = fetch_query(c, query, (team_id,))
        
        return [
            {
                "id": member[0],
                "user_id": member[1],
                "email": member[2],
                "full_name": member[3],
                "role": member[4],
                "joined_at": member[5]
            }
            for member in members
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch members: {str(e)}")
    finally:
        conn.close()

# ── Endpoint: GET /api/teams/{team_id}/scans — Get Team Shared Scans ─
@router.get("/teams/{team_id}/scans")
async def get_team_scans(team_id: int, current_user: dict = Depends(get_current_user)):
    """
    Get all scans shared with a team.
    
    Args:
        team_id: Team ID
        current_user: Authenticated user
        
    Returns:
        [{scan_id, target, score, shared_by, shared_at, shared_by_name}]
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    db = DatabaseConnection()
    conn = db.connect()
    try:
        c = conn.cursor()
        user_id = current_user.get("id")
        
        # Check if requester is member of team
        member = fetch_one(c,
            "SELECT id FROM team_members WHERE team_id = %s AND user_id = %s",
            (team_id, user_id)
        )
        if not member:
            raise HTTPException(status_code=403, detail="Not a member of this team")
        
        # Get shared scans (assuming a scans table with target, score fields)
        query = """
            SELECT tss.scan_id, tss.shared_by, u.full_name, tss.shared_at
            FROM team_shared_scans tss
            JOIN users u ON tss.shared_by = u.id
            WHERE tss.team_id = %s
            ORDER BY tss.shared_at DESC
        """
        scans = fetch_query(c, query, (team_id,))
        
        return [
            {
                "scan_id": scan[0],
                "shared_by": scan[1],
                "shared_by_name": scan[2],
                "shared_at": scan[3]
            }
            for scan in scans
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch team scans: {str(e)}")
    finally:
        conn.close()

# ── Endpoint: POST /api/teams/{team_id}/share-scan/{scan_id} ──────────
@router.post("/teams/{team_id}/share-scan/{scan_id}")
async def share_scan_with_team(team_id: int, scan_id: int, current_user: dict = Depends(get_current_user)):
    """
    Share a scan with a team. User must be analyst+ or owner of team.
    
    Args:
        team_id: Team ID
        scan_id: Scan ID to share
        current_user: Authenticated user
        
    Returns:
        {success: true, scan_id, team_id}
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    db = DatabaseConnection()
    conn = db.connect()
    try:
        c = conn.cursor()
        user_id = current_user.get("id")
        
        # Check if requester is analyst+ in team
        member = fetch_one(c,
            "SELECT role FROM team_members WHERE team_id = %s AND user_id = %s",
            (team_id, user_id)
        )
        if not member:
            raise HTTPException(status_code=403, detail="Not a member of this team")
        if member[0] not in ["owner", "analyst"]:
            raise HTTPException(status_code=403, detail="Only analysts and owners can share scans")
        
        # Check if scan exists
        scan = fetch_one(c, "SELECT id FROM scans WHERE id = %s", (scan_id,))
        if not scan:
            raise HTTPException(status_code=404, detail="Scan not found")
        
        # Check if already shared
        existing = fetch_one(c,
            "SELECT id FROM team_shared_scans WHERE team_id = %s AND scan_id = %s",
            (team_id, scan_id)
        )
        if existing:
            raise HTTPException(status_code=400, detail="Scan already shared with this team")
        
        # Add shared scan
        execute_query(c,
            "INSERT INTO team_shared_scans (team_id, scan_id, shared_by) VALUES (%s, %s, %s)",
            (team_id, scan_id, user_id)
        )
        
        conn.commit()
        return {
            "success": True,
            "scan_id": scan_id,
            "team_id": team_id
        }
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to share scan: {str(e)}")
    finally:
        conn.close()
