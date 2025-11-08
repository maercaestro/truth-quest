# 🔥 Firebase Hosting Deployment Guide

## Quick Deploy (Manual)

```bash
cd frontend
npm run build
firebase deploy --only hosting
```

Your app will be live at: **https://truth-quest.web.app**

---

## Setup (One-Time)

### 1. Get Firebase Service Account Key

1. Go to: https://console.firebase.google.com/project/truth-quest/settings/serviceaccounts/adminsdk
2. Click **"Generate new private key"**
3. Download the JSON file
4. Copy the **entire JSON content**

### 2. Add to GitHub Secrets

Go to: https://github.com/maercaestro/ahead/settings/secrets/actions/new

**Secret Name**: `FIREBASE_SERVICE_ACCOUNT`

**Secret Value**: Paste the entire JSON content from step 1

### 3. Verify Other Secrets

Make sure you have:
- ✅ `AZURE_VM_HOST` - Your Azure VM IP address
- ✅ `FIREBASE_SERVICE_ACCOUNT` - Firebase service account JSON

---

## How It Works

### Automatic Deployment (CI/CD)

When you push changes to `frontend/` folder:

1. GitHub Actions triggers
2. Builds the frontend with production API URL
3. Deploys to Firebase Hosting
4. Available at: https://truth-quest.web.app

### Manual Deployment

```bash
# Build with production settings
cd frontend
npm run build

# Deploy to Firebase
firebase deploy --only hosting

# Deploy to a preview channel (for testing)
firebase hosting:channel:deploy preview
```

---

## Architecture

```
┌─────────────────────┐
│  Firebase Hosting   │  ← Frontend (React + Vite)
│  truth-quest.web.app│
└──────────┬──────────┘
           │
           │ API Calls
           ▼
┌─────────────────────┐
│    Azure VM B2s     │  ← Backend (Flask API)
│   YOUR_VM_IP:3001   │
└─────────────────────┘
```

### URLs:
- **Frontend**: https://truth-quest.web.app
- **Backend API**: http://YOUR_AZURE_VM_IP:3001
- **Health Check**: http://YOUR_AZURE_VM_IP:3001/api/health

---

## Environment Configuration

### Development (localhost)
```javascript
API_URL = 'http://localhost:3001'
```

### Production (Firebase)
```javascript
API_URL = 'http://YOUR_AZURE_VM_IP:3001'  // From VITE_API_URL env var
```

---

## Useful Commands

```bash
# Local development
npm run dev

# Build for production
npm run build

# Preview production build locally
npm run preview

# Deploy to Firebase
firebase deploy --only hosting

# Create preview channel
firebase hosting:channel:deploy staging

# View live site
firebase open hosting:site

# View deployment history
firebase hosting:channel:list
```

---

## Troubleshooting

### ❌ CORS Errors

**Problem**: Frontend can't connect to backend

**Solution**: Backend CORS is already configured for:
- `https://truth-quest.web.app`
- `https://truth-quest.firebaseapp.com`
- All Firebase preview channels

### ❌ API URL Not Set

**Problem**: Frontend shows "Network Error"

**Check**:
```bash
# Verify API URL in build
cat frontend/.env.production
# Should show: VITE_API_URL=http://YOUR_VM_IP:3001
```

### ❌ Build Fails

**Problem**: npm run build fails

**Solution**:
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

### ❌ Firebase Deploy Permission Denied

**Problem**: `firebase deploy` says permission denied

**Solution**:
```bash
firebase login --reauth
firebase use truth-quest
firebase deploy --only hosting
```

---

## Cost

Firebase Hosting **Free Tier**:
- ✅ 10 GB storage
- ✅ 360 MB/day bandwidth
- ✅ Custom domain
- ✅ SSL certificate (automatic)

Your usage: ~50 MB static files
**Cost**: $0/month 🎉

---

## Next Steps

### Add Custom Domain (Optional)

1. Go to: https://console.firebase.google.com/project/truth-quest/hosting/main
2. Click "Add custom domain"
3. Follow DNS setup instructions
4. SSL certificate added automatically

### Preview Channels (Staging)

```bash
# Deploy to staging channel
firebase hosting:channel:deploy staging

# Deploy to PR preview
firebase hosting:channel:deploy pr-123

# Delete channel when done
firebase hosting:channel:delete staging
```

---

## CI/CD Workflow

Every push to `main` that changes `frontend/`:

1. ✅ Checkout code
2. ✅ Install Node.js 20
3. ✅ Install dependencies (`npm ci`)
4. ✅ Create `.env.production` with `VITE_API_URL`
5. ✅ Build frontend (`npm run build`)
6. ✅ Deploy to Firebase Hosting
7. ✅ Live at https://truth-quest.web.app

Check deployment status: https://github.com/maercaestro/ahead/actions

---

## Support

- 📖 Firebase Docs: https://firebase.google.com/docs/hosting
- 🐛 Backend logs: `ssh azureuser@YOUR_VM_IP "sudo journalctl -u truth-quest-backend -f"`
- 🔍 Test API: `curl http://YOUR_VM_IP:3001/api/health`
