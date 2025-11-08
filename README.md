# Truth Quest 🔍

An AI-powered YouTube fact-checking tool with OAuth2 authentication and usage limits.

## Features

✨ **Smart Fact-Checking**
- Extracts facts from YouTube videos using OpenAI GPT-4o
- Verifies claims using Brave Search API
- Fast grading: A/B/C/D system with smart sampling
- Central thesis verification that acts as master check

🎨 **Modern UI**
- Glassmorphism design with brand colors
- Real-time progress tracking
- Sample (7 facts, 30-60s) vs Full (all facts, 2-5min) check modes
- Animated results with color-coded grades

🔐 **Authentication & Limits**
- Firebase OAuth2 (Google, GitHub, Email/Password)
- Per-user usage tracking
- **Free tier limits:**
  - 10 analyses per day
  - 100 analyses per month

## Architecture

### Backend (Python Flask)
- **Transcription:** yt-dlp (primary) + OpenAI Whisper (fallback)
- **AI Analysis:** GPT-4o for fact extraction, GPT-5-mini for verification
- **Search:** Brave Search API for web verification
- **Auth:** Firebase Admin SDK for token verification
- **Database:** Firestore for usage tracking

### Frontend (React + Vite)
- React with Tailwind CSS v4
- Firebase SDK for client authentication
- Lucide React icons
- Real-time progress updates

## Setup Instructions

### Prerequisites
- Python 3.9+
- Node.js 16+
- Firebase project (see setup below)
- API Keys: OpenAI, Brave Search, YouTube Data API v3

### 1. Firebase Setup

#### Create Firebase Project
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create new project: "truth-quest"
3. Enable **Authentication** → Sign-in methods:
   - Google
   - GitHub
   - Email/Password
4. Enable **Firestore Database** (Start in test mode)

#### Generate Service Account Key
1. Project Settings → Service accounts
2. Click "Generate new private key"
3. Save as `serviceAccountKey.json` in the backend folder
4. **DO NOT commit this file to Git!**

#### Get Firebase Config
1. Project Settings → General
2. Scroll to "Your apps" → Web app
3. Copy config object (apiKey, authDomain, projectId, etc.)
4. Add to `frontend/src/firebase.js` (already configured for truth-quest)

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << EOL
# API Keys
OPENAI_API_KEY=your_openai_key
BRAVE_API_KEY=your_brave_key
YOUTUBE_API_KEY=your_youtube_key

# Firebase Admin (path to service account key)
GOOGLE_APPLICATION_CREDENTIALS=./serviceAccountKey.json
EOL

# Start server
python server.py
```

Backend runs on `http://localhost:3001`

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend runs on `http://localhost:5173`

### 4. Test Authentication

1. Open `http://localhost:5173`
2. Click "Sign In" button
3. Try any auth method:
   - Google OAuth
   - GitHub OAuth
   - Email/Password signup
4. Enter a YouTube URL and click "Analyze"
5. Check usage limits in Firestore Console

## Usage Limits

### Free Tier
- **Daily:** 10 analyses per day
- **Monthly:** 100 analyses per month
- Limits reset automatically

### Customize Limits
Edit `backend/server.py`:
```python
DAILY_LIMIT = 10
MONTHLY_LIMIT = 100
```

### View Usage Data
Firebase Console → Firestore → `usage` collection:
```json
{
  "user_uid": {
    "daily_count": 5,
    "monthly_count": 23,
    "last_used_date": "2025-01-15",
    "current_month": "2025-01",
    "last_used_at": "timestamp"
  }
}
```

## API Endpoints

### `POST /api/analyze`
Analyze a YouTube video for fact accuracy.

**Headers:**
```json
{
  "Content-Type": "application/json",
  "Authorization": "Bearer <firebase_id_token>"
}
```

**Body:**
```json
{
  "youtubeUrl": "https://youtube.com/watch?v=...",
  "checkMode": "sample"  // or "full"
}
```

**Response:**
```json
{
  "success": true,
  "videoId": "dQw4w9WgXcQ",
  "videoTitle": "Video Title",
  "grade": "A",
  "score": 85.5,
  "verifiedFacts": [...],
  "centralThesis": {
    "thesis": "Main claim",
    "verdict": "supported"
  },
  "checkMode": "sample"
}
```

**Error Responses:**
- `401`: Invalid/expired token
- `429`: Usage limit exceeded
- `400`: Invalid YouTube URL
- `500`: Server error

## Grading System

### Letter Grades
- **A (80-100%)**: High Truth - Most claims well-supported
- **B (60-79%)**: Needs Verification - Some claims need checking
- **C (40-59%)**: Read Other Sources - Many unverified claims
- **D (0-39%)**: Don't Believe - Most claims questionable

### Central Thesis Multiplier
The main thesis verification acts as a master check:
- **Refuted:** Score capped at 40% (Grade D)
- **Partially True:** Score multiplied by 0.75
- **Supported:** No penalty (100%)

### Check Modes
- **Sample Mode:** Randomly selects 7 facts, ~30-60 seconds
- **Full Mode:** Checks all extracted facts, ~2-5 minutes

## Security

### Environment Variables
Never commit these files:
- `.env` (API keys)
- `serviceAccountKey.json` (Firebase admin)
- Any `*.json` credentials

### Firebase Rules
Update Firestore security rules:
```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /usage/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
  }
}
```

### Rate Limiting
Currently enforced per-user via Firestore. Consider adding:
- IP-based rate limiting (Flask-Limiter)
- Redis for distributed rate limiting
- Cloudflare for DDoS protection

## Troubleshooting

### "Firebase Admin SDK initialization error"
- Set `GOOGLE_APPLICATION_CREDENTIALS` to absolute path
- Verify JSON key file is valid
- Check Firebase project permissions

### "Invalid or expired token"
- Refresh page to get new token
- Check token expiration (1 hour default)
- Verify Firebase config matches project

### "Usage limit exceeded"
- Wait until next day (daily limit)
- Wait until next month (monthly limit)
- Check Firestore for current usage count

### Video transcription fails
- yt-dlp may need updating: `pip install -U yt-dlp`
- Check if video has captions/subtitles
- Try Whisper fallback (automatic if yt-dlp fails)

## Development

### Tech Stack
- **Backend:** Flask 3.0.0, firebase-admin 7.1.0, openai 2.7.1, yt-dlp 2025.10.22
- **Frontend:** React 18, Vite 6, Tailwind CSS 4, Firebase SDK 11.1.0
- **Database:** Firestore (NoSQL)
- **Auth:** Firebase Authentication (OAuth2)

### File Structure
```
truth-quest/
├── backend/
│   ├── server.py          # Main Flask app
│   ├── requirements.txt   # Python dependencies
│   ├── .env              # API keys (not in Git)
│   └── serviceAccountKey.json  # Firebase admin (not in Git)
├── frontend/
│   ├── src/
│   │   ├── App.jsx           # Main React component
│   │   ├── firebase.js       # Firebase config
│   │   ├── contexts/
│   │   │   └── AuthContext.jsx  # Auth provider
│   │   └── components/
│   │       └── AuthModal.jsx    # Login/signup UI
│   ├── package.json
│   └── vite.config.js
├── FIREBASE_SETUP.md     # Detailed Firebase guide
└── README.md             # This file
```

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -am 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Submit pull request

## License

MIT License - feel free to use for personal or commercial projects

## Support

For issues or questions:
- Check existing GitHub issues
- Review troubleshooting section
- Create new issue with error logs

---

Built with ❤️ using OpenAI GPT-4o, Firebase, and Brave Search
