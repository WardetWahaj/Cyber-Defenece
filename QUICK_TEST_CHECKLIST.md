# Quick Password Reset Testing Checklist

## 🚀 Quick Start (5 minutes)

### Prerequisites
- [ ] Backend running on `http://127.0.0.1:8000`
- [ ] Frontend running on `http://127.0.0.1:5173`
- [ ] `.env` set to `ENVIRONMENT=development`
- [ ] Existing test user account (or create one via signup)

---

## ✅ Test Flow

### 1. Navigate to Forgot Password
- [ ] Go to `http://localhost:5173/login`
- [ ] Click "Forgot Password?" link
- [ ] Should see: "Forgot Password?" form with email input

### 2. Request Reset Link
- [ ] Enter a registered email address
- [ ] Click "Send Reset Link"
- [ ] Should see: "Check Your Email" confirmation screen
- [ ] Should see instructions about `data/password_resets.log`

### 3. Get Reset Token
- [ ] Open file: `d:\8th Sem\Projects\SOC 3.1\cyberdefence_v31\data\password_resets.log`
- [ ] Copy the reset URL from the log
- [ ] Example: `http://localhost:5173/reset-password/ABC123xyz...`

### 4. Reset Password
- [ ] Navigate to the reset URL from step 3
- [ ] Should see: "Create New Password" form
- [ ] Enter new password (8+ characters)
- [ ] Confirm password (must match)
- [ ] Click "Reset Password"
- [ ] Should see: Success message
- [ ] Should auto-redirect to login after 2 seconds

### 5. Verify New Password
- [ ] At login page, enter:
  - Email: (the email from step 2)
  - Password: (the new password from step 4)
- [ ] Click "Sign In"
- [ ] Should successfully login and see dashboard

---

## 🧪 Additional Tests (Optional)

### Token Expiration Test
- [ ] Wait 1+ hours after requesting reset link
- [ ] Try using the old token
- [ ] Expected: "Invalid or expired reset token" error

### Token Reuse Prevention
- [ ] Request password reset
- [ ] Complete reset successfully
- [ ] Try using same token again
- [ ] Expected: "Invalid or expired reset token" error

### Invalid Token Test
- [ ] Navigate to: `http://localhost:5173/reset-password/fake-token-12345`
- [ ] Expected: "Invalid or expired reset token" error
- [ ] Should offer link to request new token

### Email Enumeration Protection
- [ ] Request reset for NON-EXISTENT email
- [ ] Should see: "If this email is registered..." (SAME message as real email)
- [ ] Check log: Should have NO entry for fake email

### Password Validation
- [ ] Try password with 7 characters → Error: "at least 8 characters"
- [ ] Try password with 100+ characters → Error: "too long"
- [ ] Try non-matching confirm → Error: "do not match"

---

## 📊 Success Criteria

- [x] All files created/modified as per implementation plan
- [x] Database schema includes reset_token and reset_token_expiry
- [x] Backend endpoints: `/api/auth/forgot-password` and `/api/auth/reset-password`
- [x] Frontend routes: `/forgot-password` and `/reset-password/:token`
- [x] Email logging to `data/password_resets.log` in development mode
- [x] Password validation (8-72 bytes)
- [x] Token hashing with SHA-256
- [x] 1-hour token expiry
- [x] One-time use tokens
- [x] Security: Generic success messages

---

## 🔧 Troubleshooting Quick Links

If you encounter issues:
1. **"Invalid token"** → Check token is copied correctly from log file
2. **"No log file created"** → Check backend is running and has write permissions
3. **"Can't see reset form"** → Check route `/reset-password/:token` in App.jsx
4. **"Password validation error"** → Use 8-72 character password
5. **"Email sending failed"** → Check ENVIRONMENT=development in .env

---

## 📝 Log File Location
`d:\8th Sem\Projects\SOC 3.1\cyberdefence_v31\data\password_resets.log`

Each entry shows:
- Timestamp (ISO format)
- User's email
- User's full name
- Complete reset URL with token

---

## ⏱️ Estimated Test Time
- Quick flow (steps 1-5): **5 minutes**
- All tests (with additional): **15 minutes**

---

**Created for CyberDefence v3.1 - Password Reset Feature**
**Status: Ready for Testing**
