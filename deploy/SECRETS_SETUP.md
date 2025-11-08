# 🔐 GitHub Secrets Setup Guide

## Overview

Your app uses **GitHub Secrets** to securely store API keys and credentials. They're injected during deployment - never committed to your repository!

---

## Required Secrets

Go to: **GitHub Repository → Settings → Secrets and variables → Actions → New repository secret**

### 1. Azure VM Connection (3 secrets)

#### `AZURE_VM_HOST`
- **Value**: Your VM's public IP address or domain
- **Example**: `20.123.456.78` or `truthquest.example.com`
- **How to find**:
  ```bash
  # In Azure Portal → Your VM → Overview → Public IP address
  # OR on your VM:
  curl ifconfig.me
  ```

#### `AZURE_VM_USERNAME`
- **Value**: `azureuser` (default Azure VM username)
- **If you changed it**: Use your custom username

#### `AZURE_VM_SSH_KEY`
- **Value**: Your private SSH key (entire key including headers)
- **How to get**:
  ```bash
  # On your LOCAL machine (not VM)
  cat ~/.ssh/id_rsa
  
  # Copy EVERYTHING including:
  # -----BEGIN OPENSSH PRIVATE KEY-----
  # ... (all the key content) ...
  # -----END OPENSSH PRIVATE KEY-----
  ```
- **⚠️ IMPORTANT**: This is your PRIVATE key, keep it secret!

---

### 2. API Keys (3 secrets)

#### `OPENAI_API_KEY`
- **Value**: Your OpenAI API key
- **Format**: `sk-proj-...` or `sk-...`
- **Get it from**: https://platform.openai.com/api-keys
- **Used for**: GPT-4 analysis and Whisper transcription

#### `BRAVE_API_KEY`
- **Value**: Your Brave Search API key  
- **Format**: `BSA...`
- **Get it from**: https://brave.com/search/api/
- **Used for**: Fact verification web searches

#### `YOUTUBE_API_KEY`
- **Value**: Your YouTube Data API key
- **Format**: `AIza...`
- **Get it from**: https://console.cloud.google.com/apis/credentials
- **Used for**: Video metadata (though yt-dlp is primary)
- **Note**: Can be optional if yt-dlp handles everything

---

## Firebase Service Account (Special Case)

Firebase credentials use a JSON file, not an environment variable.

### Option 1: Manual Upload (Recommended)
```bash
# From your LOCAL machine
scp backend/serviceAccountKey.json azureuser@YOUR_VM_IP:/home/azureuser/truth-quest/backend/

# The CI/CD will use this file automatically
```

### Option 2: Add as GitHub Secret (Advanced)
```bash
# 1. Base64 encode the file
cat backend/serviceAccountKey.json | base64

# 2. Add as GitHub secret named: FIREBASE_SERVICE_ACCOUNT_BASE64
# 3. Update deploy.yml to decode and save it during deployment
```

---

## Complete Setup Checklist

- [ ] 1. Add `AZURE_VM_HOST` to GitHub secrets
- [ ] 2. Add `AZURE_VM_USERNAME` to GitHub secrets  
- [ ] 3. Add `AZURE_VM_SSH_KEY` to GitHub secrets
- [ ] 4. Add `OPENAI_API_KEY` to GitHub secrets
- [ ] 5. Add `BRAVE_API_KEY` to GitHub secrets
- [ ] 6. Add `YOUTUBE_API_KEY` to GitHub secrets
- [ ] 7. Upload `serviceAccountKey.json` to VM manually

---

## Step-by-Step: Adding Secrets to GitHub

1. **Go to your repository**: https://github.com/maercaestro/truth-quest

2. **Click**: Settings (top right)

3. **Sidebar**: Secrets and variables → Actions

4. **Click**: "New repository secret" (green button)

5. **For each secret**:
   - **Name**: Exactly as shown above (e.g., `OPENAI_API_KEY`)
   - **Secret**: Paste the value
   - **Click**: "Add secret"

6. **Repeat** for all 6 secrets

---

## Verification

After adding all secrets, you should see:

```
Secrets (6)
✓ AZURE_VM_HOST
✓ AZURE_VM_USERNAME  
✓ AZURE_VM_SSH_KEY
✓ OPENAI_API_KEY
✓ BRAVE_API_KEY
✓ YOUTUBE_API_KEY
```

---

## Testing

### Test SSH Connection
```bash
# From your local machine
ssh -i ~/.ssh/id_rsa azureuser@YOUR_VM_IP

# Should connect without asking for password
# If it asks for password, your SSH key isn't configured correctly
```

### Test API Keys
```bash
# After deployment, check logs
ssh azureuser@YOUR_VM_IP
sudo journalctl -u truth-quest-backend -n 50

# Should NOT see errors like:
# - "OPENAI_API_KEY not found"
# - "Authentication failed"
```

---

## Security Best Practices

✅ **DO**:
- Keep secrets in GitHub Secrets (never in code)
- Use different keys for dev/staging/production
- Rotate keys periodically
- Use VM firewall (only open ports 80, 443, 22)

❌ **DON'T**:
- Commit `.env` files to git
- Share your SSH private key
- Use the same API keys across multiple projects
- Log sensitive values

---

## Troubleshooting

### "Context access might be invalid" warnings
- ✅ These are normal until you add the secrets
- They'll disappear once secrets are added

### CI/CD fails with "Permission denied"
- Check: `AZURE_VM_SSH_KEY` is the PRIVATE key (id_rsa)
- Check: Key includes header/footer lines
- Check: VM allows SSH on port 22

### Backend starts but API calls fail
- Check: All 3 API keys are added correctly
- Check: No extra spaces in secret values
- Check: Keys are valid (not expired/revoked)

### Firebase authentication fails
- Check: `serviceAccountKey.json` uploaded to VM
- Check: File path in `.env` is correct: `./serviceAccountKey.json`
- Check: JSON file is valid (not corrupted during upload)

---

## Updating Secrets

If you need to change a secret (e.g., rotate API key):

1. **Update in GitHub**: Settings → Secrets → Click secret name → Update

2. **Trigger deployment**:
   ```bash
   git commit --allow-empty -m "Rotate API keys"
   git push origin main
   ```

3. **Or manually on VM**:
   ```bash
   ssh azureuser@YOUR_VM_IP
   cd /home/azureuser/truth-quest/backend
   nano .env  # Edit the file
   sudo systemctl restart truth-quest-backend
   ```

---

## Cost Considerations

Your API usage will be:
- **OpenAI**: ~$0.01-0.10 per analysis (GPT-4 + Whisper)
- **Brave Search**: Free tier covers ~2000 searches/month
- **YouTube API**: Free 10,000 quota/day (rarely hit with yt-dlp)
- **Firebase**: Free tier sufficient for authentication

**Total estimated cost**: $10-30/month (depends on usage)

---

## Need Help?

If secrets aren't working:
1. Check GitHub Actions logs: Repo → Actions → Latest workflow
2. Check VM logs: `sudo journalctl -u truth-quest-backend -f`
3. Verify secrets exist: GitHub → Settings → Secrets
4. Test SSH: `ssh azureuser@YOUR_VM_IP`

---

## Summary

```bash
# 1. Add 6 secrets to GitHub
# 2. Upload serviceAccountKey.json to VM
# 3. Push to main branch
# 4. CI/CD auto-deploys with secrets!
```

🎉 Your secrets are now managed securely and automatically! 🔒
