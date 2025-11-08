# 🚀 READY TO START - Action Items

## What's Already Done ✅

All code is implemented and ready to use:
- ✅ Backend authentication with Firebase Admin SDK
- ✅ Token verification middleware
- ✅ Usage tracking with Firestore
- ✅ Frontend authentication UI (Google, GitHub, Email)
- ✅ Protected API endpoints
- ✅ Rate limiting (10/day, 100/month)

## What You Need to Do 📋

### Step 1: Generate Firebase Service Account Key (5 minutes)

1. **Open Firebase Console:**
   - Go to https://console.firebase.google.com/
   - Select "truth-quest" project

2. **Navigate to Service Accounts:**
   - Click the gear icon ⚙️ next to "Project Overview"
   - Select "Project settings"
   - Go to "Service accounts" tab

3. **Generate Key:**
   - Click "Generate new private key" button
   - Click "Generate key" to confirm
   - A JSON file will download: `truth-quest-firebase-adminsdk-xxxxx.json`

4. **Save the Key:**
   ```bash
   # Move the downloaded file to your backend folder
   mv ~/Downloads/truth-quest-firebase-adminsdk-*.json \
      ~/Documents/GitHub/truth-quest/backend/serviceAccountKey.json
   ```

   ⚠️ **IMPORTANT:** Never commit this file to Git! It's already in .gitignore.

### Step 2: Update Backend Environment Variables (2 minutes)

Edit your `backend/.env` file and add this line:

```bash
# Existing keys (keep these)
OPENAI_API_KEY=your_existing_key
BRAVE_API_KEY=your_existing_key
YOUTUBE_API_KEY=your_existing_key

# Add this line (NEW)
GOOGLE_APPLICATION_CREDENTIALS=./serviceAccountKey.json
```

### Step 3: Enable Firestore (2 minutes)

1. **Open Firebase Console:**
   - Go to https://console.firebase.google.com/
   - Select "truth-quest" project

2. **Create Firestore Database:**
   - Click "Firestore Database" in left sidebar
   - Click "Create database"
   - Select "Start in test mode" (we'll secure it later)
   - Choose your region (e.g., us-central1)
   - Click "Enable"

3. **Update Security Rules (Optional but Recommended):**
   In Firestore → Rules tab, paste:
   ```javascript
   rules_version = '2';
   service cloud.firestore {
     match /databases/{database}/documents {
       match /usage/{userId} {
         // Users can only read/write their own usage data
         allow read, write: if request.auth != null && request.auth.uid == userId;
       }
     }
   }
   ```
   Click "Publish"

### Step 4: Verify Authentication Setup (1 minute)

1. **Firebase Console → Authentication:**
   - Make sure these are enabled:
     - ✅ Google (should already be enabled)
     - ✅ GitHub (should already be enabled)
     - ✅ Email/Password (should already be enabled)

2. **If any are disabled:**
   - Click "Get Started" (if first time)
   - Go to "Sign-in method" tab
   - Enable each provider

### Step 5: Start the Application (1 minute)

**Option A: Using the Quick Start Script**
```bash
cd ~/Documents/GitHub/truth-quest
./start.sh
```

**Option B: Manual Start**

Terminal 1 (Backend):
```bash
cd ~/Documents/GitHub/truth-quest/backend
source venv/bin/activate
python server.py
```

Terminal 2 (Frontend):
```bash
cd ~/Documents/GitHub/truth-quest/frontend
npm run dev
```

### Step 6: Test Authentication (2 minutes)

1. **Open the app:**
   - Browser: http://localhost:5173

2. **Sign In:**
   - Click "Sign In" button in top-right
   - Try Google OAuth (easiest)
   - You should see your profile picture/name

3. **Test Analysis:**
   - Enter a YouTube URL (e.g., https://youtube.com/watch?v=dQw4w9WgXcQ)
   - Click "Analyze Video"
   - Should work and show results!

4. **Test Rate Limits:**
   - Try analyzing 11 videos in a row
   - The 11th should show: "Daily limit of 10 analyses reached"

5. **Check Firestore:**
   - Firebase Console → Firestore Database
   - You should see a "usage" collection with your user ID
   - Document shows daily_count, monthly_count, etc.

## Troubleshooting 🔧

### "Firebase Admin SDK initialization error"

**Problem:** Backend can't find the service account key.

**Solution:**
```bash
# Check if file exists
ls backend/serviceAccountKey.json

# If not, go back to Step 1

# Make sure .env has the correct path
cat backend/.env | grep GOOGLE_APPLICATION_CREDENTIALS
# Should show: GOOGLE_APPLICATION_CREDENTIALS=./serviceAccountKey.json
```

### "Invalid or expired token"

**Problem:** Frontend token expired or not being sent.

**Solution:**
1. Refresh the page (forces token refresh)
2. Sign out and sign back in
3. Check browser console for errors:
   - Open DevTools (F12)
   - Look for Firebase auth errors

### "Missing or invalid authorization header"

**Problem:** Frontend not sending token correctly.

**Solution:**
1. Make sure you're signed in (check for profile picture in header)
2. Check Network tab in DevTools:
   - Look for `/api/analyze` request
   - Headers should include: `Authorization: Bearer eyJhbG...`
3. If no Authorization header, try:
   ```bash
   cd frontend
   npm install  # Reinstall dependencies
   ```

### "CORS error" when calling API

**Problem:** Frontend and backend not communicating.

**Solution:**
1. Check backend is running on port 3001
2. Check frontend is running on port 5173
3. Backend should show:
   ```
   * Running on http://127.0.0.1:3001
   ```

### Firestore permission denied

**Problem:** Firestore security rules blocking access.

**Solution:**
1. Go to Firestore → Rules
2. Temporarily use test mode:
   ```javascript
   rules_version = '2';
   service cloud.firestore {
     match /databases/{database}/documents {
       match /{document=**} {
         allow read, write: if request.auth != null;
       }
     }
   }
   ```
3. Click "Publish"

## Verification Checklist ✅

Before using in production, verify:

- [ ] Service account key file exists: `backend/serviceAccountKey.json`
- [ ] Environment variable set: `GOOGLE_APPLICATION_CREDENTIALS` in `.env`
- [ ] Firestore database created and enabled
- [ ] Authentication providers enabled (Google, GitHub, Email)
- [ ] Backend starts without errors
- [ ] Frontend starts without errors
- [ ] Can sign in with Google
- [ ] Can sign in with GitHub
- [ ] Can sign in with Email
- [ ] Can analyze a video when signed in
- [ ] Cannot analyze when signed out (shows sign-in prompt)
- [ ] Rate limit triggers after 10 analyses
- [ ] Usage data appears in Firestore
- [ ] Sign out works correctly

## Quick Reference 📖

**Backend URL:** http://localhost:3001
**Frontend URL:** http://localhost:5173
**Firebase Console:** https://console.firebase.google.com/project/truth-quest

**Usage Limits:**
- Daily: 10 analyses
- Monthly: 100 analyses
- Resets: Automatic at midnight UTC / 1st of month

**Protected Route:**
- POST `/api/analyze` - Requires Bearer token

**Firestore Collections:**
- `usage/{user_uid}` - Usage tracking data

**Files to NEVER Commit:**
- `backend/serviceAccountKey.json` - Firebase admin key
- `backend/.env` - API keys

## Need Help? 🆘

1. **Check logs:**
   - Backend: Look at terminal running `python server.py`
   - Frontend: Check browser console (F12)

2. **Review documentation:**
   - README.md - Full project docs
   - FIREBASE_SETUP.md - Detailed Firebase guide
   - IMPLEMENTATION.md - Technical details
   - AUTH_FLOW.md - Authentication diagrams

3. **Common error messages:**
   - "Invalid token" → Sign in again
   - "Limit exceeded" → Wait for reset (check Firestore)
   - "Initialization error" → Check service account key path

4. **Test Firebase connection:**
   ```python
   # In Python shell
   import firebase_admin
   from firebase_admin import auth
   
   firebase_admin.initialize_app()
   print("✅ Firebase initialized!")
   ```

## Summary 🎯

**Time to Complete:** ~15 minutes

**Critical Steps:**
1. Generate Firebase service account key (Step 1)
2. Add to backend/.env (Step 2)
3. Enable Firestore (Step 3)
4. Start servers (Step 5)
5. Test authentication (Step 6)

**After Setup:**
- Authentication works automatically
- Users sign in before analyzing
- Usage tracked in Firestore
- Rate limits enforced
- Token verification on every request

**You're Ready When:**
✅ Both servers running without errors
✅ Can sign in with any auth method
✅ Video analysis works when logged in
✅ Rate limit shows after 10 analyses
✅ Firestore shows usage data

---

**🎉 Once these steps are complete, your app is fully production-ready with authentication!**
