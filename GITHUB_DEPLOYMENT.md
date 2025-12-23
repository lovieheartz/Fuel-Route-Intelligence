# GitHub Deployment Guide

**Complete guide to push Spotter AI to GitHub and deploy to production.**

---

## 📋 Files Included in GitHub Push

### ✅ WILL BE PUSHED:
- `README.md` - Main project documentation
- `frontend/README.md` - Frontend documentation
- `API_DOCUMENTATION.md` - API endpoint reference
- `PRODUCTION_FEATURES.md` - Production features overview
- `DEPLOYMENT.md` - Deployment instructions
- `fuel-prices-for-be-assessment.csv` - Dataset (6,738 fuel stations)
- `Job title_ Django Developer _ Remote.pdf` - Job description
- `SpotterAI.postman_collection.json` - Postman API collection
- All Python source code (`*.py`)
- All TypeScript/JavaScript code (`*.ts`, `*.tsx`, `*.js`)
- Configuration files (`package.json`, `requirements.txt`, etc.)

### ❌ WILL NOT BE PUSHED:
- `node_modules/` - Frontend dependencies (huge folder)
- `.next/` - Build artifacts
- `__pycache__/` - Python cache
- `db.sqlite3` - Database (will be regenerated)
- `*.log` - Log files
- `.env` files - Secrets
- IDE settings (`.vscode/`, `.idea/`)

---

## 🚀 Step 1: Initialize Git Repository

```bash
cd "r:/Spotter AI"

# Initialize git (if not already done)
git init

# Check current status
git status
```

---

## 📦 Step 2: Stage Files for Commit

```bash
# Add all files (gitignore will filter automatically)
git add .

# Check what will be committed
git status

# You should see:
# - README.md
# - fuel-prices-for-be-assessment.csv
# - Job title_ Django Developer _ Remote.pdf
# - All .py, .ts, .tsx files
# - package.json, requirements.txt
# - etc.

# You should NOT see:
# - node_modules/
# - __pycache__/
# - db.sqlite3
# - .next/
```

---

## 💬 Step 3: Create Initial Commit

```bash
git commit -m "Initial commit: Spotter AI - Fuel Routing Optimization Platform

Features:
- Production-grade Django REST API with 6,738 fuel stations
- Beautiful Next.js 14 frontend with WebGL animated hero
- Smart city autocomplete for 50+ major US cities
- Interactive Leaflet maps with route visualization
- Cost-optimized fuel stop planning
- Rate limiting, caching, and comprehensive error handling
- Full TypeScript type safety
- Responsive design with Tailwind CSS

Tech Stack: Django 4.2, Next.js 14, TypeScript, Leaflet, WebGL
"
```

---

## 🌐 Step 4: Create GitHub Repository

### On GitHub.com:

1. **Go to:** https://github.com/new
2. **Repository name:** `spotter-ai-fuel-routing`
3. **Description:** `Production-grade fuel routing optimization platform with AI-powered route planning`
4. **Visibility:** Choose Public or Private
5. **DON'T** initialize with README (we have one)
6. **Click:** "Create repository"

---

## 🔗 Step 5: Connect Local to GitHub

```bash
# Replace YOUR_USERNAME with your GitHub username
git remote add origin https://github.com/YOUR_USERNAME/spotter-ai-fuel-routing.git

# Verify remote is set
git remote -v

# You should see:
# origin  https://github.com/YOUR_USERNAME/spotter-ai-fuel-routing.git (fetch)
# origin  https://github.com/YOUR_USERNAME/spotter-ai-fuel-routing.git (push)
```

---

## 📤 Step 6: Push to GitHub

```bash
# Push to main branch
git branch -M main
git push -u origin main

# Enter your GitHub credentials when prompted
```

---

## ✅ Verify Push

1. **Go to:** `https://github.com/YOUR_USERNAME/spotter-ai-fuel-routing`
2. **Check:**
   - ✅ README.md displays nicely with formatting
   - ✅ CSV file is present
   - ✅ PDF file is present
   - ✅ All Python/TypeScript files are there
   - ❌ No `node_modules/` folder
   - ❌ No `db.sqlite3` file
   - ❌ No `.next/` folder

---

## 🚀 Deployment Options

### Option 1: Deploy Frontend to Vercel (Recommended)

**Vercel is perfect for Next.js applications!**

#### Method A: Via GitHub Integration

1. **Go to:** https://vercel.com/new
2. **Click:** "Import Git Repository"
3. **Select:** Your `spotter-ai-fuel-routing` repo
4. **Configure:**
   - Framework Preset: Next.js
   - Root Directory: `frontend`
   - Build Command: `npm run build`
   - Output Directory: `.next`
5. **Environment Variables:**
   ```
   NEXT_PUBLIC_API_URL=https://your-backend-url.com/api/v1
   ```
6. **Click:** "Deploy"

#### Method B: Via Vercel CLI

```bash
cd frontend

# Install Vercel CLI
npm install -g vercel

# Login to Vercel
vercel login

# Deploy
vercel --prod

# Follow prompts:
# - Link to existing project? No
# - Project name? spotter-ai-frontend
# - Which directory? frontend
```

**Your frontend will be live at:** `https://spotter-ai-frontend.vercel.app`

---

### Option 2: Deploy Backend to Railway

**Railway is great for Django applications!**

1. **Go to:** https://railway.app/
2. **Click:** "Start a New Project"
3. **Select:** "Deploy from GitHub repo"
4. **Choose:** `spotter-ai-fuel-routing`
5. **Configure:**
   - Root Directory: `/` (root)
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn fuel_routing_api.wsgi`

6. **Environment Variables:**
   ```
   DEBUG=False
   SECRET_KEY=<generate-a-long-random-string>
   ALLOWED_HOSTS=your-app.railway.app
   DISABLE_COLLECTSTATIC=1
   ```

7. **Add Procfile** to project root:
   ```
   web: gunicorn fuel_routing_api.wsgi --log-file -
   release: python manage.py migrate
   ```

8. **Update requirements.txt** to include:
   ```
   gunicorn==21.2.0
   ```

9. **Push changes:**
   ```bash
   git add Procfile requirements.txt
   git commit -m "Add production configuration"
   git push origin main
   ```

**Your backend will be live at:** `https://spotter-ai-backend.railway.app`

---

### Option 3: Deploy Backend to Render

1. **Go to:** https://render.com/
2. **Click:** "New +" → "Web Service"
3. **Connect:** Your GitHub repo
4. **Configure:**
   - Name: `spotter-ai-backend`
   - Runtime: Python 3
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn fuel_routing_api.wsgi:application`

5. **Environment Variables:**
   ```
   PYTHON_VERSION=3.11
   DEBUG=False
   SECRET_KEY=<random-string>
   ALLOWED_HOSTS=spotter-ai-backend.onrender.com
   ```

6. **Click:** "Create Web Service"

---

## 🔧 Post-Deployment Configuration

### Update Frontend API URL

After deploying backend, update frontend environment variable:

**On Vercel:**
1. Go to your project settings
2. Environment Variables
3. Update `NEXT_PUBLIC_API_URL` to your backend URL
4. Redeploy

**Example:**
```
NEXT_PUBLIC_API_URL=https://spotter-ai-backend.railway.app/api/v1
```

### Enable CORS on Backend

Update `fuel_routing_api/settings.py`:

```python
# Add your frontend domain
CORS_ALLOWED_ORIGINS = [
    "https://spotter-ai-frontend.vercel.app",
    "http://localhost:3000",
]
```

Push changes:
```bash
git add fuel_routing_api/settings.py
git commit -m "Update CORS settings for production"
git push origin main
```

---

## 📊 Database Setup (Production)

### For Railway/Render with PostgreSQL:

1. **Add PostgreSQL database** to your project
2. **Install psycopg2:**
   ```bash
   pip install psycopg2-binary
   pip freeze > requirements.txt
   ```

3. **Update settings.py:**
   ```python
   import dj_database_url

   if not DEBUG:
       DATABASES = {
           'default': dj_database_url.config(
               conn_max_age=600,
               conn_health_checks=True,
           )
       }
   ```

4. **Add to requirements.txt:**
   ```
   dj-database-url==2.1.0
   psycopg2-binary==2.9.9
   ```

5. **Migrate database:**
   ```bash
   python manage.py migrate
   python manage.py import_fuel_quick
   ```

---

## 🎯 Testing Deployment

### Test Backend

```bash
# Health check
curl https://your-backend-url.com/api/v1/health/

# Should return:
# {"status":"healthy","database":"connected","fuel_stations_loaded":6738}

# Plan route
curl -X POST https://your-backend-url.com/api/v1/plan/ \
  -H "Content-Type: application/json" \
  -d '{"start_location":"Los Angeles, CA","end_location":"San Francisco, CA"}'
```

### Test Frontend

1. Open `https://your-frontend-url.com`
2. Should see animated WebGL hero
3. Click "Start Planning Routes"
4. Test route planning with autocomplete
5. Verify map displays correctly

---

## 🔒 Security Checklist

Before deploying:

- [ ] `DEBUG=False` in production
- [ ] Strong `SECRET_KEY` generated
- [ ] `ALLOWED_HOSTS` configured
- [ ] CORS properly configured
- [ ] No `.env` files in git
- [ ] No hardcoded credentials
- [ ] HTTPS enabled (automatic on Vercel/Railway/Render)
- [ ] Rate limiting enabled (already implemented)

---

## 📝 GitHub README Updates

After deployment, update README.md with live URLs:

```markdown
## 🌐 Live Demo

- **Frontend:** https://spotter-ai-frontend.vercel.app
- **Backend API:** https://spotter-ai-backend.railway.app/api/v1
- **API Docs:** https://spotter-ai-backend.railway.app/api/docs/
```

Push update:
```bash
git add README.md
git commit -m "Add live demo URLs to README"
git push origin main
```

---

## 🐛 Troubleshooting

### Frontend deployment fails

**Check:**
- Root directory is set to `frontend`
- Node.js version is 18+
- All dependencies in package.json

### Backend deployment fails

**Check:**
- Procfile is in root directory
- gunicorn in requirements.txt
- Environment variables set
- Python version is 3.11+

### Database migration errors

**Run manually:**
```bash
# SSH into your deployment
python manage.py migrate
python manage.py import_fuel_quick
```

### CORS errors in browser

**Update settings.py:**
```python
CORS_ALLOWED_ORIGINS = [
    "https://your-frontend-domain.com",
]
```

---

## 📱 Optional: Custom Domain

### For Vercel (Frontend):
1. Go to Project Settings → Domains
2. Add your custom domain
3. Update DNS records as instructed

### For Railway/Render (Backend):
1. Go to Settings → Domains
2. Add custom domain
3. Update DNS CNAME record

---

## 🎉 Success!

Your Spotter AI platform is now live!

**What you've achieved:**
- ✅ Professional GitHub repository
- ✅ Live frontend with beautiful UI
- ✅ Production backend with API
- ✅ Continuous deployment (auto-deploy on git push)
- ✅ HTTPS security
- ✅ Scalable infrastructure

---

## 📞 Support

If you encounter issues:
1. Check deployment logs on your platform
2. Review environment variables
3. Test API endpoints with curl
4. Check browser console for frontend errors

---

**Good luck with your deployment!** 🚀
