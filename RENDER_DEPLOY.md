# Render Deployment

## Steps to Deploy on Render.com

### 1. Create Account
- Go to https://render.com
- Sign up with GitHub

### 2. Connect Repository
- Click "New +" → "Web Service"
- Connect your GitHub repo: `kishore-1808/GMC`

### 3. Configure Deployment
Fill in these settings:

- **Name**: `gesture-control`
- **Region**: Choose closest to you
- **Branch**: `main`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python app.py`

### 4. Environment Variables
No environment variables needed.

### 5. Click "Create Web Service"

---

## Important Note

This app requires **camera access** which only works locally. For cloud deployment:
- The website will load
- But camera won't work on cloud servers

**Best Use:**
1. Deploy locally with ngrok for global access
2. Or use on same network via local IP

---

## Quick Deploy Link

Click this to deploy directly:
https://render.com/deploy?repo=https://github.com/kishore-1808/GMC
