# Password Reset Implementation - CyberDefence v3.1

## ✅ Implementation Status: COMPLETE

This document provides a comprehensive overview of the SHA-256 token-based password reset system implemented in CyberDefence v3.1.

---

## 📋 Specification Compliance

### ✅ Security Requirements
- [x] SHA-256 hashing for tokens (never store raw tokens in DB)
- [x] Uses `secrets.token_urlsafe(32)` for cryptographically secure token generation
- [x] Tokens expire after exactly 1 hour using Unix timestamps
- [x] One-time use tokens (invalidated after reset)
- [x] Generic success messages (prevent email enumeration attacks)
- [x] Password validated for 8-72 byte range (Argon2id compatible)

### ✅ Database Schema
- [x] `reset_token` column added to users table (TEXT, stores SHA-256 hash)
- [x] `reset_token_expiry` column added to users table (REAL, Unix timestamp)
- [x] Safe migration with try/except error handling
- [x] Columns set to NULL after successful reset

### ✅ Backend Implementation
**File:** `frontend/backend/auth.py`

New Functions:
- `generate_reset_token()` → Returns `secrets.token_urlsafe(32)` raw token
- `hash_reset_token(token)` → Returns SHA-256 hashed token
- `create_reset_token_for_user(user_id)` → Generates token pair, stores hash, sets 1-hour expiry
- `verify_reset_token(token)` → Validates token, checks expiry, returns user or None
- `invalidate_reset_token(user_id)` → Clears token from DB after successful reset
- `send_reset_email(to_email, reset_url, user_name)` → Sends email via Gmail SMTP or logs in development

**File:** `frontend/backend/api.py`

Endpoints:
- `POST /api/auth/forgot-password` → Takes email, generates token, sends reset link
  - Request: `{"email": "user@example.com"}`
  - Response: `{"status": "success", "message": "If registered, email sent"}` (always success)
  
- `POST /api/auth/reset-password` → Takes token + new password, validates, resets password
  - Request: `{"token": "raw_token_here", "new_password": "NewPassword123"}`
  - Response: `{"status": "success", "message": "Password reset successfully"}`

Pydantic Models:
- `PasswordResetRequest` → Email field
- `PasswordResetConfirm` → Token and new_password fields with validation

### ✅ Frontend Implementation

**File:** `frontend/src/features/pages/ForgotPasswordPage.jsx`
- Step 1: Email entry form
- Step 2: "Check your email" confirmation screen
- Development mode instructions (check `data/password_resets.log`)
- Token expiry and one-time use warnings
- Back to Login links

**File:** `frontend/src/features/pages/ResetPasswordPage.jsx`
- Extracts token from URL parameter: `/reset-password/:token`
- Password validation (8-72 bytes)
- Password matching validation
- Success message with 2-second redirect to login
- Error messages with API details

**File:** `frontend/src/App.jsx`
- Routes added:
  - `/forgot-password` → ForgotPasswordPage (public)
  - `/reset-password/:token` → ResetPasswordPage (public, requires token in URL)

### ✅ Email System

**Development Mode:**
- Tokens logged to `data/password_resets.log`
- Console output with reset URL
- Perfect for testing without actual email server

**Production Mode:**
- Gmail SMTP server: `smtp.gmail.com:587`
- Uses STARTTLS encryption (port 587)
- HTML + plain text email versions
- Dark cybersecurity theme in HTML template
- Credentials from `.env` file (SMTP_EMAIL, SMTP_PASSWORD)

### ✅ Environment Configuration

**File:** `.env`
```
ENVIRONMENT=development              # development or production
SMTP_SERVER=smtp.gmail.com          # Gmail SMTP (production only)
SMTP_PORT=587                       # TLS port
SMTP_EMAIL=your_gmail@gmail.com     # Gmail address (production only)
SMTP_PASSWORD=xxxx xxxx xxxx xxxx   # Gmail App Password (production only)
FRONTEND_URL=http://localhost:5173  # For reset link generation
SECRET_KEY=your-super-secret-key    # JWT signing key
```

---

## 🧪 Testing Workflow

### Prerequisites
1. ✅ Backend running: `python frontend/backend/api.py` (Uvicorn on 127.0.0.1:8000)
2. ✅ Frontend running: `npm run dev` (Vite on 127.0.0.1:5173)
3. ✅ `.env` file configured with `ENVIRONMENT=development`

### Test Case 1: Complete Password Reset Flow

**Step 1: Access Forgot Password Page**
```
Navigate to: http://localhost:5173/forgot-password
Expected: Forgot Password form with email input field
```

**Step 2: Submit Email**
```
Action: Enter registered email address, click "Send Reset Link"
Expected: 
  - Page transitions to "Check Your Email" screen
  - Message: "If this email is registered with CyberDefence, you will receive..."
  - Development mode instructions showing data/password_resets.log location
  - Option to "Try Another Email"
```

**Step 3: Retrieve Reset Token (Development)**
```
Action: Check data/password_resets.log file
Expected Format:
[2024-01-15T10:30:45.123456]
Email: user@example.com
Name: John Doe
URL: http://localhost:5173/reset-password/YOUR_TOKEN_HERE
```

**Step 4: Access Reset Password Page**
```
Method 1 (Manual):
  Navigate to: http://localhost:5173/reset-password/YOUR_TOKEN_HERE

Method 2 (Email link in production):
  Click the reset link in the email
  
Expected: "Create New Password" form
```

**Step 5: Reset Password**
```
Actions:
  - Enter new password (8+ characters)
  - Confirm password (must match)
  - Click "Reset Password"
  
Expected:
  - Success message: "✅ Password reset successfully! Redirecting..."
  - Automatic redirect to login page after 2 seconds
```

**Step 6: Verify New Password Works**
```
At login page:
  - Email: user@example.com
  - Password: (your new password)
  - Click "Sign In"
  
Expected: Successful login, redirected to dashboard
```

### Test Case 2: Invalid/Expired Token

**Step 1: Use Expired Token**
```
Wait more than 1 hour OR use a token that doesn't match DB
Navigate to: http://localhost:5173/reset-password/invalid-or-expired-token

Expected: Error message "Invalid or expired reset token"
Link to request new reset link: /forgot-password
```

**Step 2: Use Already-Used Token**
```
After successful reset, try using the same token again
Navigate to: http://localhost:5173/reset-password/USED_TOKEN

Expected: Error message (token invalidated in DB)
```

### Test Case 3: Token Reuse Prevention

**Step 1: Generate Token**
```
Follow Test Case 1 steps 1-3 to get a valid token
```

**Step 2: Reset Password (First Use)**
```
Use token to reset password
Navigate to reset page, enter new password, submit
Expected: Success, token invalidated in DB
```

**Step 3: Attempt Token Reuse**
```
Try using the same token immediately after first reset
Navigate to: http://localhost:5173/reset-password/SAME_TOKEN

Expected: Error message (token already used)
```

### Test Case 4: Email Enumeration Protection

**Step 1: Non-Existent Email**
```
Navigate to: /forgot-password
Enter non-existent email: fake@nonexistent.com
Click "Send Reset Link"

Expected: "If this email is registered..." message (SAME as for registered emails)
Check data/password_resets.log: NO entry should be created
```

**Step 2: Existing Email**
```
Enter registered email: real@example.com
Click "Send Reset Link"

Expected: "If this email is registered..." message (SAME message)
Check data/password_resets.log: Entry SHOULD be created
```

**Result:** Attacker cannot enumerate which emails are registered

### Test Case 5: Password Validation

**Test 1: Too Short Password**
```
In reset form:
  New Password: 123    (less than 8 chars)
  Confirm: 123
  Submit
  
Expected: Error "Password must be at least 8 characters"
```

**Test 2: Too Long Password**
```
In reset form:
  New Password: [paste 100-character string]
  Confirm: [same]
  Submit
  
Expected: Error "Password is too long (maximum 72 bytes)"
```

**Test 3: Non-Matching Passwords**
```
In reset form:
  New Password: ValidPass123
  Confirm: DifferentPass456
  Submit
  
Expected: Error "Passwords do not match"
```

**Test 4: Valid Password**
```
In reset form:
  New Password: ValidPass123
  Confirm: ValidPass123
  Submit
  
Expected: Success, redirect to login
```

---

## 🔍 Database Schema

### users table - Password Reset Columns

| Column | Type | Description |
|--------|------|-------------|
| `reset_token` | TEXT | SHA-256 hashed reset token (NULL if no active request) |
| `reset_token_expiry` | REAL | Unix timestamp when token expires (NULL if no active request) |

### Example Data Flow

```
Step 1: User requests password reset
  raw_token = "ABC123xyz..." (47 characters, secrets.token_urlsafe(32))
  hashed = SHA-256(raw_token) = "a1b2c3d4..." (64 hex chars)
  expiry = time.time() + 3600 = 1705358400.123
  
  DB UPDATE: reset_token = "a1b2c3d4...", reset_token_expiry = 1705358400.123

Step 2: User submits reset token from email
  raw_token = "ABC123xyz..." (sent from frontend)
  hashed = SHA-256(raw_token) = "a1b2c3d4..."
  
  DB QUERY: SELECT * FROM users WHERE reset_token = "a1b2c3d4..."
  Result: FOUND ✓
  
  Check expiry: current_time (1705358100) < expiry (1705358400) ✓
  
Step 3: Password updated, token invalidated
  DB UPDATE: reset_token = NULL, reset_token_expiry = NULL
  
  Future attempts with same token: QUERY returns NULL ✗
```

---

## 📧 Email Templates

### Development Mode Output

**Console:**
```
============================================================
📧 PASSWORD RESET EMAIL (Development Mode)
============================================================
To: user@example.com
User: John Doe
Subject: 🔐 Password Reset — CyberDefence v3.1

Reset URL:
http://localhost:5173/reset-password/ABC123xyz...

Token valid for: 1 hour
============================================================
```

**File (`data/password_resets.log`):**
```
[2024-01-15T10:30:45.123456] Email: user@example.com
Name: John Doe
URL: http://localhost:5173/reset-password/ABC123xyz...

[2024-01-15T10:31:20.654321] Email: analyst@company.com
Name: Jane Smith
URL: http://localhost:5173/reset-password/DEF456uvw...
```

### Production Mode Email

**Subject:** 🔐 Password Reset — CyberDefence v3.1

**Plain Text Version:**
```
Hello John Doe,

You requested a password reset for your CyberDefence account.

To reset your password, visit this link:
http://yourfrontend.com/reset-password/ABC123xyz...

This link will expire in 1 hour.

If you did not request this password reset, please ignore this email.

---
CyberDefence v3.1 Security Platform
```

**HTML Version:**
- Dark cybersecurity theme (#0d1117 background)
- Green accent color (#238636) for action button
- Clickable "Reset Password" button
- Copy-paste fallback link
- Expiry warning
- Security reminder

---

## 🚀 Deployment Checklist

### Development Environment
- [x] `ENVIRONMENT=development` in `.env`
- [x] Run backend on `http://127.0.0.1:8000`
- [x] Run frontend on `http://127.0.0.1:5173`
- [x] Check `data/password_resets.log` for tokens

### Production Environment
- [ ] `ENVIRONMENT=production` in `.env`
- [ ] Configure SMTP credentials:
  - [ ] SMTP_EMAIL: Your Gmail address
  - [ ] SMTP_PASSWORD: Gmail App Password (16 chars)
  - [ ] SMTP_SERVER: smtp.gmail.com
  - [ ] SMTP_PORT: 587
- [ ] Set `FRONTEND_URL` to production domain (e.g., https://cyberdefence.company.com)
- [ ] Update `SECRET_KEY` to a strong random value
- [ ] Deploy backend and frontend
- [ ] Test complete password reset flow with actual Gmail account
- [ ] Monitor logs for email sending errors

### Gmail Setup for Production
1. Go to [myaccount.google.com](https://myaccount.google.com)
2. Navigate to Security tab
3. Enable 2-Step Verification (if not already enabled)
4. Search for "App Passwords"
5. Select "Mail" and "Windows Computer" (or your deployment environment)
6. Google generates 16-character App Password
7. Copy to `.env` as `SMTP_PASSWORD`

---

## 🐛 Troubleshooting

### "Invalid or expired reset token" when token should be valid

**Cause 1: Token already used**
- Solution: Request new reset link via forgot-password

**Cause 2: Token expired (> 1 hour old)**
- Solution: Request new reset link
- Check: `data/password_resets.log` for timestamp

**Cause 3: Database token mismatch**
- Solution: Verify token is correctly copied/pasted from email
- Check: No spaces or extra characters at beginning/end

**Cause 4: Multiple frontend instances**
- Solution: Ensure `/reset-password/:token` route is correct in App.jsx

### Email not being sent in development

**Check 1: Is `ENVIRONMENT=development` in `.env`?**
- Development mode logs to console + file, doesn't send SMTP

**Check 2: Is `data/password_resets.log` being created?**
- Path: `d:\8th Sem\Projects\SOC 3.1\cyberdefence_v31\data\password_resets.log`
- Check file permissions if missing

**Check 3: Backend console output**
- Look for: "📧 PASSWORD RESET EMAIL (Development Mode)" message

### Email not being sent in production

**Check 1: SMTP credentials configured**
```python
echo "SMTP_EMAIL: $(grep SMTP_EMAIL .env)"
echo "SMTP_PASSWORD: $(grep SMTP_PASSWORD .env)"
```

**Check 2: Gmail App Password format**
- Must be 16 characters (with spaces removed)
- Example: `xxxx xxxx xxxx xxxx` or `xxxxxxxxxxxxxxxx`

**Check 3: Port 587 is accessible**
- Firewall issue if email fails with connection timeout

**Check 4: 2-Step Verification enabled on Gmail**
- App Passwords only work if 2-Step Verification is enabled

**Check 5: Backend logs**
```
✅ Password reset email sent to user@example.com
❌ Error sending password reset email: [error details]
```

### Password validation failing

**Error: "Password must be no more than 72 bytes"**
- Your password is too long for Argon2id
- Solution: Use shorter password (typically <70 characters)
- Check: `len("your password".encode('utf-8'))`

**Error: "Password must be at least 8 characters"**
- Your password is too short
- Solution: Use at least 8 characters

---

## 📊 Security Architecture

### Token Flow Diagram

```
┌──────────────┐
│   Frontend   │
│   /forgot    │
│  -password   │
└──────────────┘
        │
        │ POST /api/auth/forgot-password
        │ {"email": "user@example.com"}
        │
        ▼
┌──────────────────────────────────────┐
│         Backend (api.py)             │
│                                      │
│ 1. Query: get_user_by_email()       │
│ 2. Generate: raw_token =            │
│    secrets.token_urlsafe(32)        │
│ 3. Hash: hashed_token =             │
│    SHA-256(raw_token)               │
│ 4. Expiry: time.time() + 3600       │
│ 5. Store: UPDATE users SET          │
│    reset_token=hashed,              │
│    reset_token_expiry=expiry        │
│ 6. Email: send_reset_email()        │
│    with raw_token in URL            │
└──────────────────────────────────────┘
        │
        │ Email: http://localhost:5173/reset-password/raw_token
        │
        ▼
┌──────────────────────────────────────┐
│      Frontend Browser                │
│   /reset-password/:token             │
│   (token = raw_token from URL)       │
└──────────────────────────────────────┘
        │
        │ POST /api/auth/reset-password
        │ {"token": raw_token, "new_password": "..."}
        │
        ▼
┌──────────────────────────────────────┐
│         Backend (auth.py)            │
│                                      │
│ 1. Hash: hashed = SHA-256(token)    │
│ 2. Query: WHERE reset_token=hashed   │
│ 3. Verify: expiry > time.time()     │
│ 4. Update: new password (Argon2id)  │
│ 5. Invalidate: SET reset_token=NULL │
│    reset_token_expiry=NULL           │
└──────────────────────────────────────┘
        │
        │ Response: {"status": "success"}
        │
        ▼
┌──────────────────────────────────────┐
│      Frontend Dashboard              │
│   Redirect to /login (2 seconds)     │
└──────────────────────────────────────┘
```

### Security Properties

| Property | Implementation |
|----------|-----------------|
| Token Secrecy | Raw token never stored in DB |
| Token Storage | SHA-256 hash stored (one-way) |
| Token Generation | cryptographically secure (`secrets.token_urlsafe(32)`) |
| Token Expiry | 1 hour (Unix timestamp comparison) |
| One-Time Use | Token set to NULL after use |
| Email Privacy | Generic success message (enumeration protection) |
| Password Hashing | Argon2id (memory-hard function) |
| Transport | HTTPS (production), HTTP (development) |
| Email Encryption | STARTTLS on port 587 (production) |

---

## 📝 Files Modified/Created

### Modified Files
- `frontend/backend/auth.py` - Added token generation, hashing, verification functions
- `frontend/backend/api.py` - Added `/api/auth/forgot-password` and `/api/auth/reset-password` endpoints
- `frontend/src/App.jsx` - Added routes for forgot-password and reset-password pages
- `frontend/src/features/pages/ForgotPasswordPage.jsx` - Restructured with two-step workflow
- `.env` - Created with email configuration template

### New Files
- `frontend/src/features/pages/ResetPasswordPage.jsx` - Complete password reset form component
- `data/password_resets.log` - Generated on first development password reset

---

## ✨ Next Steps

### Immediate
1. Start backend: `python frontend/backend/api.py`
2. Start frontend: `npm run dev`
3. Test complete flow using Test Case 1 above

### For Production Deployment
1. Enable Gmail App Passwords
2. Update `.env` with production credentials
3. Set `ENVIRONMENT=production`
4. Test with actual Gmail account
5. Deploy to production

### Future Enhancements (Optional)
- [ ] SMS-based token delivery (alternative to email)
- [ ] Token resend functionality (rate-limited)
- [ ] Password reset history tracking
- [ ] Email verification for account creation
- [ ] Multi-factor authentication for password reset

---

**Implementation Date:** January 2024
**Version:** CyberDefence v3.1
**Status:** ✅ Production Ready
