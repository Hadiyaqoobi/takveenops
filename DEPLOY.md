# TakvenOps Deployment Guide

Deploy TakvenOps so your team can access it from anywhere.

**Stack:**
- **Frontend** → Vercel (free)
- **Backend** → Railway (free tier) or Render
- **Database** → Neon PostgreSQL (free tier)

---

## Step 1: Set Up Neon Database

1. Go to [neon.tech](https://neon.tech) and create a free account
2. Create a new project (name it "takvenops")
3. Copy the **connection string** — it looks like:
   ```
   postgresql://username:password@ep-something.region.aws.neon.tech/neondb?sslmode=require
   ```
4. Save this — you'll need it for the backend

---

## Step 2: Deploy Backend to Railway

1. Go to [railway.app](https://railway.app) and sign in with GitHub
2. Click **"New Project"** → **"Deploy from GitHub Repo"**
3. Select your TakvenOps repository
4. Set the **Root Directory** to `backend`
5. Add these **environment variables** in Railway settings:

   | Variable | Value |
   |----------|-------|
   | `DATABASE_URL` | Your Neon connection string from Step 1 |
   | `FRONTEND_URL` | `https://your-app.vercel.app` (set after Step 3) |
   | `PORT` | `8001` (Railway usually sets this automatically) |

6. Railway will auto-detect the Procfile and deploy
7. Copy your Railway backend URL (e.g., `https://takvenops-backend.up.railway.app`)

---

## Step 3: Deploy Frontend to Vercel

1. Go to [vercel.com](https://vercel.com) and sign in with GitHub
2. Click **"Add New Project"** → import your TakvenOps repository
3. Set the **Root Directory** to `frontend`
4. Set **Framework Preset** to `Vite`
5. Add this **environment variable**:

   | Variable | Value |
   |----------|-------|
   | `VITE_API_URL` | Your Railway backend URL from Step 2 (e.g., `https://takvenops-backend.up.railway.app`) |

6. Click **Deploy**
7. Copy your Vercel URL and go back to Railway to set `FRONTEND_URL`

---

## Step 4: Configure AI Agents

For Claude Code / Antigravity to use the deployed TakvenOps, set the API URL:

```bash
# Add to your shell profile (.bashrc, .zshrc, etc.)
export TAKVENOPS_API_URL=https://takvenops-backend.up.railway.app

# Or set it per-command
TAKVENOPS_API_URL=https://takvenops-backend.up.railway.app python ops.py board
```

Update the `CLAUDE.md` file to reference the deployed URL.

---

## Environment Variables Summary

### Backend (Railway)
| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | Neon PostgreSQL connection string | `postgresql://user:pass@host/db?sslmode=require` |
| `FRONTEND_URL` | Vercel frontend URL (for CORS) | `https://takvenops.vercel.app` |

### Frontend (Vercel)
| Variable | Description | Example |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API URL | `https://takvenops-backend.up.railway.app` |

### CLI (ops.py)
| Variable | Description | Example |
|----------|-------------|---------|
| `TAKVENOPS_API_URL` | Backend API URL | `https://takvenops-backend.up.railway.app` |

---

## Local Development

No environment variables needed — defaults to SQLite + localhost:

```bash
# Backend
cd backend && python -m uvicorn backend.main:app --port 8001

# Frontend
cd frontend && npm run dev
```

---

## Employee Access

Once deployed, employees can:
1. Open the Vercel URL in their browser
2. Register an account (or use admin/admin123)
3. Start managing tasks on the board

AI agents can interact via `ops.py` with `TAKVENOPS_API_URL` set.
