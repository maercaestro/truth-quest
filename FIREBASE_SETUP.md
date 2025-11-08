# Firebase Admin SDK Setup Guide

## Step 1: Generate Service Account Key

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project: **truth-quest**
3. Click the gear icon ⚙️ next to "Project Overview"
4. Select **Project settings**
5. Go to the **Service accounts** tab
6. Click **Generate new private key**
7. Download the JSON file

## Step 2: Configure Backend

### Option A: Environment Variable (Recommended for Production)

1. Save the downloaded JSON key file to a secure location (DO NOT commit to Git)
2. Add to your `backend/.env` file:
```bash
GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/serviceAccountKey.json
```

### Option B: Direct Initialization (Development Only)

If you prefer, you can place the JSON file in the backend directory and initialize directly:

```python
import firebase_admin
from firebase_admin import credentials

cred = credentials.Certificate('path/to/serviceAccountKey.json')
firebase_admin.initialize_app(cred)
```

## Step 3: Add to .gitignore

Make sure your `.gitignore` includes:
```
# Firebase credentials
*serviceAccountKey*.json
*.json
backend/*.json
```

## Step 4: Test Authentication

1. Start the backend server:
```bash
cd backend
source venv/bin/activate  # or .\venv\Scripts\activate on Windows
python server.py
```

2. Start the frontend:
```bash
cd frontend
npm run dev
```

3. Try signing in with Google, GitHub, or Email

## Troubleshooting

### Error: "Firebase Admin SDK initialization error"
- Make sure `GOOGLE_APPLICATION_CREDENTIALS` environment variable is set correctly
- Verify the path to your service account key file is absolute and correct
- Ensure the JSON file is valid (open it in a text editor to check)

### Error: "Invalid or expired token"
- Token might have expired - refresh the page
- Check that the frontend is sending the token in the `Authorization: Bearer <token>` header
- Verify that the Firebase project ID matches in both frontend and backend

### Error: "Missing or invalid authorization header"
- Make sure you're logged in on the frontend
- Check browser console for any authentication errors
- Verify that `idToken` is being passed correctly in API calls

## Security Notes

⚠️ **NEVER commit your service account key to version control!**

- The service account key has admin privileges to your Firebase project
- Always use environment variables in production
- Rotate keys regularly
- Use Firebase security rules to restrict access
