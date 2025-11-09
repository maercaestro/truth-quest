# YouTube Cookies Setup for yt-dlp

To bypass YouTube's bot detection, you need to provide browser cookies to yt-dlp. This allows the server to access YouTube as if it were a logged-in user.

## Method 1: Using Browser Extension (Recommended)

### Step 1: Install Cookie Extension
Install one of these browser extensions:
- **Chrome/Edge**: [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
- **Firefox**: [cookies.txt](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)

### Step 2: Export Cookies
1. Open YouTube.com in your browser
2. Make sure you're logged in to your Google account
3. Click the extension icon
4. Click "Export" or "Download" to save cookies
5. Save the file as `youtube_cookies.txt`

### Step 3: Upload to Server

**For local development:**
```bash
# Copy the cookies file to the backend directory
cp ~/Downloads/youtube_cookies.txt /Users/abuhuzaifahbidin/Documents/GitHub/truth-quest/backend/
```

**For Azure VM:**
```bash
# Upload cookies to Azure VM
scp youtube_cookies.txt azureuser@172.173.202.235:/home/azureuser/truth-quest/backend/

# SSH to VM and restart service
ssh azureuser@172.173.202.235
sudo systemctl restart truth-quest-backend
```

## Method 2: Using yt-dlp Command (Alternative)

If you have Chrome installed, yt-dlp can extract cookies directly:

```bash
# Extract cookies from Chrome
yt-dlp --cookies-from-browser chrome --cookies youtube_cookies.txt "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Extract cookies from Firefox
yt-dlp --cookies-from-browser firefox --cookies youtube_cookies.txt "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Extract cookies from Safari (macOS)
yt-dlp --cookies-from-browser safari --cookies youtube_cookies.txt "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

Then upload the generated `youtube_cookies.txt` file to the server.

## Method 3: Manual Cookie File Creation

If you're comfortable with browser DevTools:

1. Open YouTube.com and log in
2. Open Developer Tools (F12)
3. Go to Application/Storage tab → Cookies → https://www.youtube.com
4. Create a file `youtube_cookies.txt` with Netscape cookie format:

```
# Netscape HTTP Cookie File
.youtube.com	TRUE	/	TRUE	0	CONSENT	YES+
.youtube.com	TRUE	/	FALSE	1234567890	VISITOR_INFO1_LIVE	xxxxxxxxxxxx
.youtube.com	TRUE	/	TRUE	1234567890	YSC	xxxxxxxxxxxx
```

## Verification

After setting up cookies, you should see in the logs:
```
DEBUG: Using cookies from: ./youtube_cookies.txt
```

If the cookies are working, yt-dlp will successfully download transcripts without bot detection errors.

## Security Notes

⚠️ **IMPORTANT**: 
- Never commit the `youtube_cookies.txt` file to Git (it's already in .gitignore)
- These cookies give access to your YouTube account
- Rotate cookies periodically for security
- Use a dedicated Google account for the server if possible

## Troubleshooting

### "No cookies file found"
- Make sure the file is named exactly `youtube_cookies.txt`
- Check it's in the correct directory: `/home/azureuser/truth-quest/backend/` on Azure VM
- Verify file permissions: `chmod 644 youtube_cookies.txt`

### Cookies expired
- YouTube cookies expire after some time
- Re-export cookies from your browser
- Upload the new file and restart the service

### Still getting bot detection
- Make sure you're logged in to YouTube when exporting cookies
- Try using a different browser
- Some accounts may have additional restrictions
