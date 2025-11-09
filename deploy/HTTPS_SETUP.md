# 🔒 HTTPS Setup for Backend API

## Problem

Your frontend is on HTTPS (Firebase: `https://truth-quest.web.app`) but your backend is on HTTP (`http://YOUR_VM_IP:3001`). Browsers block this mixed content.

## Solutions

### **Option 1: Quick Fix - Use ngrok (Free, 5 minutes) ⚡**

Perfect for **immediate testing** without domain or SSL setup.

```bash
# On your Azure VM
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update && sudo apt install ngrok

# Login to ngrok (sign up free at https://ngrok.com)
ngrok config add-authtoken YOUR_AUTHTOKEN

# Start tunnel
ngrok http 3001
```

Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`) and update:

```bash
# In GitHub Secrets
VITE_API_URL=https://abc123.ngrok.io
```

**Pros**: 
- ✅ Works immediately
- ✅ No domain needed
- ✅ Free tier available
- ✅ HTTPS automatic

**Cons**: 
- ❌ URL changes on restart (free tier)
- ❌ Not for production long-term

---

### **Option 2: Cloudflare Tunnel (Free Forever, Recommended) ⭐**

Best for **production** without buying a domain or SSL certificate.

#### Setup Steps:

```bash
# 1. SSH into your Azure VM
ssh azureuser@YOUR_VM_IP

# 2. Install Cloudflare Tunnel
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared.deb

# 3. Login to Cloudflare (opens browser)
cloudflared tunnel login

# 4. Create a tunnel
cloudflared tunnel create truth-quest-api

# 5. Create config file
mkdir -p ~/.cloudflared
nano ~/.cloudflared/config.yml
```

**Config file content:**
```yaml
tunnel: YOUR_TUNNEL_ID_FROM_STEP_4
credentials-file: /home/azureuser/.cloudflared/YOUR_TUNNEL_ID.json

ingress:
  - hostname: truth-quest-api.yourdomain.com  # Or use Cloudflare's free subdomain
    service: http://localhost:3001
  - service: http_status:404
```

```bash
# 6. Route your tunnel
cloudflared tunnel route dns truth-quest-api truth-quest-api.yourdomain.com

# 7. Run the tunnel
cloudflared tunnel run truth-quest-api

# 8. Make it run on startup
sudo cloudflared service install
sudo systemctl enable cloudflared
sudo systemctl start cloudflared
```

**Update GitHub Secrets:**
```bash
VITE_API_URL=https://truth-quest-api.yourdomain.com
```

**Pros**:
- ✅ Free forever
- ✅ Automatic HTTPS
- ✅ Stable URL
- ✅ DDoS protection
- ✅ No SSL certificate management

**Cons**:
- ⚠️ Requires Cloudflare account (free)

---

### **Option 3: Let's Encrypt SSL (Traditional) 📜**

If you have a **domain name** pointed to your Azure VM.

```bash
# SSH into your VM
ssh azureuser@YOUR_VM_IP

# Run the SSL setup script
cd /home/azureuser/truth-quest/deploy
chmod +x setup_ssl.sh
sudo ./setup_ssl.sh
# Enter your domain when prompted
```

**Update GitHub Secrets:**
```bash
VITE_API_URL=https://api.yourdomain.com
```

**Pros**:
- ✅ Traditional SSL setup
- ✅ Full control
- ✅ Auto-renewal

**Cons**:
- ❌ Requires domain name
- ❌ DNS configuration needed
- ❌ More complex setup

---

### **Option 4: Azure Application Gateway (Advanced) 💰**

If you want enterprise-grade setup.

**Cost**: ~$140-180/month

Not recommended for this use case - overkill for a simple API.

---

## Recommended Approach

### For Development/Testing:
**Use ngrok** - Get running in 5 minutes

### For Production:
**Use Cloudflare Tunnel** - Free, stable, automatic HTTPS

---

## Quick Start: ngrok Setup

```bash
# 1. Sign up at https://ngrok.com (free)
# 2. Get your authtoken from dashboard
# 3. SSH into Azure VM
ssh azureuser@YOUR_VM_IP

# 4. Install ngrok
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update && sudo apt install ngrok

# 5. Add your authtoken
ngrok config add-authtoken YOUR_TOKEN_HERE

# 6. Start tunnel
ngrok http 3001
```

**Copy the HTTPS URL** (looks like `https://1234-56-78-90-12.ngrok-free.app`)

**Update in two places:**

1. **GitHub Secret**:
   - Go to: https://github.com/maercaestro/ahead/settings/secrets/actions
   - Edit `VITE_API_URL`
   - Set value: `https://1234-56-78-90-12.ngrok-free.app` (your ngrok URL)

2. **Redeploy frontend**:
   ```bash
   git commit --allow-empty -m "Trigger redeploy with new API URL"
   git push origin main
   ```

**Test it**:
```bash
curl https://YOUR_NGROK_URL/api/health
```

---

## Update Backend CORS (Already Done)

Your backend is already configured to accept HTTPS requests from Firebase:

```python
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "https://truth-quest.web.app",
            "https://truth-quest.firebaseapp.com",
            # ... other origins
        ]
    }
})
```

---

## Troubleshooting

### Still getting mixed content errors?

1. **Check API URL in browser console:**
   ```javascript
   console.log(window.location.hostname);
   // Should be: truth-quest.web.app
   ```

2. **Verify VITE_API_URL secret:**
   - Must start with `https://`
   - Must NOT have trailing slash
   - Example: `https://abc123.ngrok.io`

3. **Clear browser cache:**
   - Hard reload: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)

4. **Check backend CORS:**
   ```bash
   ssh azureuser@YOUR_VM_IP
   sudo journalctl -u truth-quest-backend -n 50
   # Look for CORS errors
   ```

---

## My Recommendation

**Start with ngrok** (5 minutes):
- Get it working immediately
- Test everything
- Free tier is fine for testing

**Then migrate to Cloudflare Tunnel** (30 minutes):
- Stable permanent URL
- Free forever
- Production-ready
- No domain required (can use Cloudflare's subdomain)

---

## Need Help?

- ngrok docs: https://ngrok.com/docs
- Cloudflare Tunnel: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/
- Let's Encrypt: https://letsencrypt.org/getting-started/
