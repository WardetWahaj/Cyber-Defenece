# Deployment Guide

## Deployment Architecture

```
GitHub Repository
    ├── Frontend (React/Vite)
    │   └── Deployed to: Vercel
    │       URL: https://cyberdefence.vercel.app
    │
    └── Backend (FastAPI/Python)
        └── Deployed to: Render.com
            URL: https://cyberdefence-backend.onrender.com
```

---

## Frontend Deployment (Vercel)

### Prerequisites
- GitHub account with repository pushed
- Vercel account (free: https://vercel.com)

### Step 1: Create Vercel Project

1. Go to https://vercel.com/new
2. Click "Import Git Repository"
3. Search for and select `cyberdefence_v31`
4. Click "Import"

### Step 2: Configure Build Settings

In the "Configure Project" screen:

- **Project Name:** `cyberdefence`
- **Framework Preset:** Vite
- **Root Directory:** `frontend` ✅
- **Build Command:** `npm run build` ✅
- **Output Directory:** `dist` ✅
- **Install Command:** `npm install`

### Step 3: Add Environment Variables

Before deploying, add environment variables:

1. Scroll to "Environment Variables"
2. Add:
   - **Name:** `VITE_API_BASE`
   - **Value:** `https://cyberdefence-backend.onrender.com` (after backend deployed)

3. Click "Deploy"

### Step 4: Configure Vercel for Multiple Deploys

Edit `vercel.json` (already created):

```json
{
  "buildCommand": "cd frontend && npm install && npm run build",
  "outputDirectory": "frontend/dist"
}
```

---

## Backend Deployment (Render.com)

### Prerequisites
- GitHub account with repository pushed
- Render.com account (free: https://render.com)
- SMTP credentials (Gmail App Password)
- JWT Secret Key

### Step 1: Create Render Service

1. Go to https://render.com/dashboard
2. Click "New +" → "Web Service"
3. Click "Connect repository" → Select your GitHub repo
4. Select `cyberdefence_v31` repository

### Step 2: Configure Web Service

Fill in the form:

- **Name:** `cyberdefence-backend`
- **Environment:** `Python 3`
- **Region:** Choose closest to you
- **Branch:** `main`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn frontend.backend.api:app --host 0.0.0.0 --port $PORT`

### Step 3: Add Environment Variables

Scroll to "Environment" section and add:

```
ENVIRONMENT=production
FRONTEND_URL=https://cyberdefence.vercel.app
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_EMAIL=your-email@gmail.com
SMTP_PASSWORD=your-16-char-gmail-app-password
SECRET_KEY=generate-with-command-below
```

**Generate SECRET_KEY:**
```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Step 4: Deploy

Click "Create Web Service" and wait for deployment to complete.

The backend URL will be: `https://cyberdefence-backend.onrender.com`

---

## Update Frontend with Backend URL

After backend is deployed on Render:

1. Go to Vercel Dashboard
2. Select `cyberdefence` project
3. Settings → Environment Variables
4. Update `VITE_API_BASE` to: `https://cyberdefence-backend.onrender.com`
5. Vercel will auto-redeploy with new environment

---

## Continuous Deployment (Auto-Deploy on Push)

✅ Already configured! Both Vercel and Render watch your GitHub repository.

Every time you push to `main`:
1. Vercel rebuilds frontend automatically
2. Render rebuilds backend automatically
3. Both deploy to production within 1-2 minutes

---

## Testing Deployed Application

1. Open: `https://cyberdefence.vercel.app`
2. Try signing up / logging in
3. Test password reset (email should work)
4. Create a scan and verify data persists

---

## Troubleshooting

### Frontend Shows 404 for API Calls

**Problem:** Network tab shows 404 errors for API calls

**Solution:**
1. Check Vercel Environment Variables → `VITE_API_BASE` is set correctly
2. Verify backend is running on Render
3. Check backend URL is correct (https://your-backend.onrender.com)
4. Clear browser cache (Ctrl+Shift+Delete) and reload

### Backend Won't Deploy

**Problem:** "Build failed" error on Render

**Solution:**
1. Check requirements.txt has all dependencies
2. Verify Python version is 3.10+
3. Check for missing API keys in .env (config.json setup)
4. View Render logs for specific error

### Email Not Sending in Production

**Problem:** "Email failed to send" error

**Solution:**
1. Verify SMTP credentials are correct in Render environment variables
2. Ensure Gmail App Password (not regular password) is used
3. Check Gmail account has "Less secure apps" enabled OR use App Password
4. Verify SMTP_SERVER=smtp.gmail.com and SMTP_PORT=587

### Database Issues

**Problem:** "Database locked" or "No such table" error

**Solution:**
1. SQLite works but only for single instance; consider PostgreSQL for production
2. To upgrade to PostgreSQL:
   - Use Render PostgreSQL addon
   - Update backend to use PostgreSQL driver
   - Migrate data

---

## Production Checklist

- [ ] Backend deployed on Render
- [ ] Frontend deployed on Vercel
- [ ] Environment variables configured on both platforms
- [ ] FRONTEND_URL points to Vercel in backend .env
- [ ] VITE_API_BASE points to Render in frontend .env
- [ ] Test signup → login → password reset flow
- [ ] Test at least one security scan
- [ ] Verify reports generate correctly
- [ ] Test on mobile device (responsive design)
- [ ] Monitor Render logs for errors

---

## Quick Reference URLs

After deployment, you'll have:

- **Frontend:** https://cyberdefence.vercel.app
- **Backend API:** https://cyberdefence-backend.onrender.com
- **API Docs:** https://cyberdefence-backend.onrender.com/docs
- **GitHub:** https://github.com/WardetWahaj/Cyber-Defenece

---

## Cost Breakdown

| Service | Plan | Cost | Notes |
|---------|------|------|-------|
| Vercel | Pro | Free | $20/mo for hobby projects |
| Render | Free | Free | ⚠️ Spins down after 15 min inactivity |
| Render | Starter | $7/mo | 🟢 Always-on, recommended |
| GitHub | Free | Free | ✅ Unlimited public repos |

**Note:** For production reliability, upgrade Render to Starter plan ($7/mo) to prevent API timeouts.

---

## Advanced: Using GitHub Actions for CI/CD

Optional: Automate testing before deployment

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy

on:
  push:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: python -m pytest tests/

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Vercel
        run: vercel --prod --token ${{ secrets.VERCEL_TOKEN }}
      - name: Deploy to Render
        run: curl ${{ secrets.RENDER_DEPLOY_HOOK }}
```

---

## Support

For deployment issues:
- Vercel Docs: https://vercel.com/docs
- Render Docs: https://render.com/docs
- FastAPI: https://fastapi.tiangolo.com/deployment/
