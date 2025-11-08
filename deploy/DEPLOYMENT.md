# Azure VM Deployment Guide

## Prerequisites
- Azure VM (Standard B2s) running Ubuntu 20.04 or later
- SSH access to the VM
- GitHub repository access
- Domain/Public IP for your VM

## Step-by-Step Deployment

### 1️⃣ Setup GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions

Add these secrets:

```
AZURE_VM_HOST         = your.vm.public.ip.or.domain
AZURE_VM_USERNAME     = azureuser
AZURE_VM_SSH_KEY      = (your private SSH key - see below)
```

**Getting your SSH key:**
```bash
# On your local machine
cat ~/.ssh/id_rsa

# Copy the ENTIRE output including:
# -----BEGIN OPENSSH PRIVATE KEY-----
# ... key content ...
# -----END OPENSSH PRIVATE KEY-----
```

### 2️⃣ Initial VM Setup (ONE TIME ONLY)

SSH into your Azure VM:

```bash
ssh azureuser@your-vm-ip
```

Run the setup script:

```bash
# Download the setup script
curl -o setup.sh https://raw.githubusercontent.com/maercaestro/truth-quest/main/deploy/azure_vm_setup.sh

# Make it executable
chmod +x setup.sh

# Run it
./setup.sh
```

This will:
- ✅ Install all dependencies (Python, Node.js, nginx)
- ✅ Clone your repository
- ✅ Setup virtual environment
- ✅ Build frontend
- ✅ Create systemd service for backend
- ✅ Configure nginx as reverse proxy
- ✅ Open firewall ports
- ✅ Start all services

### 3️⃣ Configure Environment Variables

Edit your backend `.env` file on the VM:

```bash
cd /home/azureuser/truth-quest/backend
nano .env
```

Add your actual API keys:

```env
OPENAI_API_KEY=sk-...your-actual-key...
BRAVE_API_KEY=BSA...your-actual-key...
YOUTUBE_API_KEY=AIza...your-actual-key...
GOOGLE_APPLICATION_CREDENTIALS=./serviceAccountKey.json
PORT=3001
```

### 4️⃣ Add Firebase Service Account Key

Upload your Firebase key to the VM:

```bash
# From your local machine
scp backend/serviceAccountKey.json azureuser@your-vm-ip:/home/azureuser/truth-quest/backend/
```

### 5️⃣ Restart Services

```bash
ssh azureuser@your-vm-ip
sudo systemctl restart truth-quest-backend
sudo systemctl restart nginx
```

### 6️⃣ Test Your Deployment

Visit: `http://your-vm-ip`

You should see the Truth Quest frontend!

---

## 🚀 Using CI/CD (Auto-Deploy)

After initial setup, every time you push to `main` branch:

```bash
git add .
git commit -m "Update features"
git push origin main
```

GitHub Actions will automatically:
1. ✅ Pull latest code on VM
2. ✅ Install dependencies
3. ✅ Build frontend
4. ✅ Restart services
5. ✅ Your site is updated!

Watch deployment progress: GitHub → Actions tab

---

## 🔧 Useful Commands

### Check Service Status
```bash
sudo systemctl status truth-quest-backend
sudo systemctl status nginx
```

### View Logs
```bash
# Backend logs (live)
sudo journalctl -u truth-quest-backend -f

# Nginx error logs
sudo tail -f /var/log/nginx/error.log

# Nginx access logs
sudo tail -f /var/log/nginx/access.log
```

### Restart Services
```bash
sudo systemctl restart truth-quest-backend
sudo systemctl restart nginx
```

### Update Manually (without CI/CD)
```bash
cd /home/azureuser/truth-quest
git pull origin main
cd backend
source venv/bin/activate
pip install -r requirements.txt
cd ../frontend
npm install
npm run build
sudo systemctl restart truth-quest-backend
sudo systemctl restart nginx
```

### Check Resource Usage
```bash
# CPU and Memory
htop

# Disk usage
df -h

# Backend process
ps aux | grep python
```

---

## 🔒 Security Improvements (Optional)

### Setup SSL with Let's Encrypt (HTTPS)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### Setup Firewall
```bash
sudo ufw status
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp
sudo ufw enable
```

---

## 🐛 Troubleshooting

### Backend won't start
```bash
# Check logs
sudo journalctl -u truth-quest-backend -n 50

# Common issues:
# - Missing .env file
# - Missing serviceAccountKey.json
# - Wrong Python version
# - Port 3001 already in use
```

### Frontend shows 404
```bash
# Check nginx config
sudo nginx -t

# Rebuild frontend
cd /home/azureuser/truth-quest/frontend
npm run build
sudo systemctl restart nginx
```

### API calls fail
```bash
# Check if backend is running
curl http://localhost:3001/api/health

# Check CORS settings in server.py
# Make sure CORS allows your domain
```

### CI/CD not deploying
- Check GitHub Actions logs
- Verify SSH key is correct
- Test SSH connection: `ssh -i ~/.ssh/id_rsa azureuser@your-vm-ip`
- Check VM firewall allows SSH (port 22)

---

## 📊 Monitoring

### Setup Basic Monitoring
```bash
# Install monitoring tools
sudo apt install htop iotop nethogs

# Check system resources
htop

# Check disk I/O
sudo iotop

# Check network usage
sudo nethogs
```

### Log Rotation
nginx logs are auto-rotated. For backend:

```bash
sudo nano /etc/logrotate.d/truth-quest
```

Add:
```
/var/log/truth-quest/*.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
}
```

---

## 🎉 You're Done!

Your Truth Quest app is now:
- ✅ Running on Azure VM
- ✅ Auto-deploying via CI/CD
- ✅ Production-ready
- ✅ Easy to maintain

Push to main → Auto-deployed in ~2 minutes! 🚀
