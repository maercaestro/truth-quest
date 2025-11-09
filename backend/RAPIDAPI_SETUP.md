# RapidAPI Setup for YouTube Transcripts

RapidAPI provides a YouTube transcript service that **doesn't require downloading videos** and works for all users, not just you.

## Why RapidAPI?

✅ No video download required  
✅ Works for all users (not tied to your account)  
✅ Bypasses YouTube bot detection  
✅ ~$0.001 per request (very affordable)  
✅ No cookie management needed  

## Setup Steps

### 1. Sign up for RapidAPI
1. Go to [RapidAPI.com](https://rapidapi.com/)
2. Create a free account
3. Verify your email

### 2. Subscribe to YouTube Transcript API
1. Visit: [YouTube Transcripts API](https://rapidapi.com/VideoIndexerV2/api/youtube-transcripts/)
2. Click "Subscribe to Test"
3. Choose a plan:
   - **Basic (Free)**: 100 requests/month
   - **Pro**: More requests based on plan
4. Make sure to test the endpoint in the API playground

### 3. Get Your API Key
1. After subscribing, go to the API page
2. Click on "Endpoints" tab
3. Look for "X-RapidAPI-Key" in the code examples
4. Copy your API key (format: `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`)

### 4. Add to Your Environment

**Local development:**
```bash
# Edit backend/.env
nano /Users/abuhuzaifahbidin/Documents/GitHub/truth-quest/backend/.env

# Add your RapidAPI key:
RAPIDAPI_KEY=your_rapidapi_key_here
```

**Azure VM (via GitHub Actions):**
1. Go to your GitHub repository settings
2. Navigate to: Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Name: `RAPIDAPI_KEY`
5. Value: Your RapidAPI key
6. Click "Add secret"

### 5. Deploy

The GitHub Actions workflow will automatically add the RAPIDAPI_KEY to your Azure VM's .env file on the next deploy.

```bash
cd /Users/abuhuzaifahbidin/Documents/GitHub/truth-quest
git add .
git commit -m "Add RapidAPI YouTube transcript support"
git push origin main
```

## Testing

Once deployed, the transcript fetching order will be:

1. **RapidAPI** (if key configured) ← Works for everyone, no downloads
2. YouTube timedtext API (scraping) ← May be blocked
3. youtube-transcript-api ← May be blocked
4. yt-dlp with cookies ← Only works with your cookies
5. OpenAI Whisper ← Expensive fallback

## Cost Estimation

Assuming 1,000 video analyses per month:
- 1,000 requests × $0.001 = **$1.00/month**

Compare to:
- Whisper: 1,000 videos × 10 min avg × $0.006 = **$60/month**

## Troubleshooting

### "RapidAPI key not configured"
- Make sure RAPIDAPI_KEY is in your .env file
- Restart the backend server

### "RapidAPI returned status 429"
- You've hit your monthly quota
- Upgrade your plan or wait for next month

### "RapidAPI returned status 403"
- Your API key is invalid
- Check you copied the full key correctly
- Verify your subscription is active

## Alternative APIs

If you want to try other services:

1. **YouTube Transcript API** (ytsubsapis on RapidAPI)
   - Similar pricing
   - Different endpoint

2. **Streamline YouTube Captions**
   - Also on RapidAPI
   - May have better rate limits

All of these avoid downloading videos and work for all users!
