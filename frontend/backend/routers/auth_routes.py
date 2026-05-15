"""
Authentication endpoints for the CyberDefence API.

Provides user registration, login, token management, and password reset functionality.
"""

import os
from fastapi import APIRouter, HTTPException, Header, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from frontend.backend import auth

router = APIRouter(prefix="/api/auth", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)


def get_current_user(authorization: str = Header(None)) -> dict:
    """Extract and verify user from Authorization header."""
    if not authorization:
        raise HTTPException(status_code=401, detail="No authorization header")
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid auth scheme")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    payload = auth.verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Convert user_id to integer (JWT stores it as string)
    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Invalid token format")
    
    user = auth.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user


@limiter.limit("10/minute")
@router.post("/signup")
def signup(request_data: auth.SignupRequest, request: Request = None) -> dict:
    """Create a new user account."""
    user = auth.create_user(
        email=request_data.email,
        full_name=request_data.full_name,
        password=request_data.password,
        organization=request_data.organization
    )
    
    if not user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create access token (convert user ID to string for JWT spec)
    access_token = auth.create_access_token(data={"sub": str(user["id"])})
    
    # Create refresh token
    refresh_token = auth.create_refresh_token(data={"sub": str(user["id"])})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "organization": user["organization"],
            "role": user.get("role", "analyst")
        }
    }


@limiter.limit("5/minute")
@router.post("/login")
def login(request_data: auth.LoginRequest, request: Request = None) -> dict:
    """Authenticate user and return access token."""
    # Check if account is locked due to brute-force attempts
    if auth.is_account_locked(request_data.email):
        raise HTTPException(status_code=429, detail="Account temporarily locked. Try again in 15 minutes.")
    
    # Get client IP address for logging
    client_ip = request.client.host if request else None
    
    user = auth.get_user_by_email(request_data.email)
    
    if not user or not auth.verify_password(request_data.password, user["password_hash"]):
        # Record failed login attempt
        auth.record_login_attempt(request_data.email, ip_address=client_ip, success=False)
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Record successful login attempt
    auth.record_login_attempt(request_data.email, ip_address=client_ip, success=True)
    
    # Update last login
    auth.update_last_login(user["id"])
    
    # Create access token (convert user ID to string for JWT spec)
    access_token = auth.create_access_token(data={"sub": str(user["id"])})
    
    # Create refresh token
    refresh_token = auth.create_refresh_token(data={"sub": str(user["id"])})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "organization": user["organization"],
            "role": user.get("role", "analyst")
        }
    }


@limiter.limit("10/minute")
@router.post("/refresh")
def refresh_access_token(request_data: auth.RefreshTokenRequest, request: Request = None) -> dict:
    """Refresh access token using a valid refresh token."""
    refresh_token = request_data.refresh_token
    
    payload = auth.verify_refresh_token(refresh_token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    
    # Extract user ID from the refresh token payload
    user_id = payload.get("sub")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    # Create new access token
    new_access_token = auth.create_access_token(data={"sub": user_id})
    
    # Create new refresh token
    new_refresh_token = auth.create_refresh_token(data={"sub": user_id})
    
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }


@router.get("/me")
def get_current_user_info(authorization: str = Header(None)) -> dict:
    """Get current authenticated user info."""
    user = get_current_user(authorization)
    return {
        "id": user["id"],
        "email": user["email"],
        "full_name": user["full_name"],
        "organization": user["organization"],
        "role": user.get("role", "analyst"),
        "created_at": user["created_at"]
    }


@limiter.limit("3/minute")
@router.post("/forgot-password")
def forgot_password(request_data: auth.PasswordResetRequest, request: Request = None) -> dict:
    """
    Request a password reset token via email.
    Uses SHA-256 hashed tokens stored in database.
    
    ✅ PRODUCTION MODE - Sends real emails via Gmail SMTP
    ✅ Security: Always returns success message whether email exists or not,
       preventing email enumeration attacks.
    """
    try:
        # Query user - but don't reveal if found or not
        user = auth.get_user_by_email(request_data.email)
        
        if user:
            # User exists - generate and send reset token
            raw_token = auth.create_reset_token_for_user(user["id"])
            
            if raw_token:
                # Build the reset URL (user will click this or paste the token)
                frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
                reset_url = f"{frontend_url}/reset-password/{raw_token}"
                
                # Send email with reset URL via Gmail SMTP
                # This will raise an exception if email sending fails
                try:
                    auth.send_reset_email(
                        to_email=request.email,
                        reset_url=reset_url,
                        user_name=user.get("full_name", "User")
                    )
                except Exception as e:
                    # Log the error but still return generic success (don't reveal email sending issues)
                    print(f"❌ Failed to send reset email: {str(e)}")
                    # In production, you might want to return 500 here
                    # For now, we silently fail to avoid revealing if email exists
        
        # Always return success message (security best practice)
        # Same response whether email exists or not = no email enumeration
        return {
            "status": "success",
            "message": "If this email is registered, a password reset link has been sent"
        }
        
    except Exception as e:
        # Unexpected error - log and return 500
        print(f"❌ Unexpected error in forgot_password: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred processing your request")


@router.post("/reset-password")
def reset_password(request: auth.PasswordResetConfirm) -> dict:
    """
    Reset password using a valid reset token.
    Uses SHA-256 hashed tokens verified against database.
    
    The token must be:
    1. Present and unhashed in the request
    2. Match the hashed value in the database
    3. Not be expired (less than 1 hour old)
    """
    # Verify the reset token
    user = auth.verify_reset_token(request.token)
    
    if not user:
        # Token is invalid or expired
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    
    # Validate new password
    try:
        # Use the existing validator from the model
        auth.PasswordResetConfirm.parse_obj({"token": request.token, "new_password": request.new_password})
    except Exception as e:
        raise HTTPException(status_code=422, detail="Password does not meet requirements")
    
    # Update password to the new value (hashed with Argon2id)
    auth.update_password(user["id"], request.new_password)
    
    # Invalidate the reset token (prevent reuse)
    auth.invalidate_reset_token(user["id"])
    
    return {
        "status": "success",
        "message": "Password reset successfully"
    }
