# 🚀 Quick Deployment Commands

## First Time Setup (On Azure VM)

### Option A: Upload and run setup script
```bash
# 1. From your LOCAL machine, upload the script
scp deploy/azure_vm_setup.sh azureuser@YOUR_VM_IP:~/

# 2. SSH into VM
ssh azureuser@YOUR_VM_IP

# 3. Run the script
chmod +x azure_vm_setup.sh
./azure_vm_setup.sh

# 4. Upload Firebase key (from your local machine in another terminal)
scp backend/serviceAccountKey.json azureuser@YOUR_VM_IP:/home/azureuser/truth-quest/backend/
```

### Option B: Download setup script from GitHub
```bash
# 1. SSH into your VM
ssh azureuser@YOUR_VM_IP

# 2. Download and run setup script
curl -o setup.sh https://raw.githubusercontent.com/maercaestro/ahead/main/deploy/azure_vm_setup.sh
chmod +x setup.sh
./setup.sh

# 3. Upload Firebase key (from your local machine in another terminal)
scp backend/serviceAccountKey.json azureuser@YOUR_VM_IP:/home/azureuser/truth-quest/backend/
```

**Important:** The setup script will:
- Install system dependencies (Python, Node.js, nginx, etc.)
- Clone the repository
- Create Python virtual environment
- Set up systemd service
- Configure nginx
- Open firewall ports

**After setup completes:**
- CI/CD will handle .env file creation automatically (no need to manually create it)
- Just add GitHub Secrets (see below) and push to main branch

## GitHub Secrets to Add

Go to: GitHub Repo → Settings → Secrets and variables → Actions

**Required Secrets (6 total):**

```
Name: AZURE_VM_HOST
Value: your.vm.ip.address

Name: AZURE_VM_USERNAME  
Value: azureuser

Name: AZURE_VM_SSH_KEY
Value: (paste your private SSH key - get it with: cat ~/.ssh/id_rsa)

Name: OPENAI_API_KEY
Value: sk-proj-... (your OpenAI API key)

Name: BRAVE_API_KEY
Value: BSA... (your Brave Search API key)

Name: YOUTUBE_API_KEY
Value: AIza... (your YouTube API key)
```

📖 **Detailed guide**: See `/deploy/SECRETS_SETUP.md`

## Daily Usage (Auto-Deploy)

```bash
# Just push to main - CI/CD handles the rest!
git add .
git commit -m "Your changes"
git push origin main

# Watch deployment at: https://github.com/YOUR_USER/truth-quest/actions
```

## Useful VM Commands

```bash
# Check if services are running
sudo systemctl status truth-quest-backend
sudo systemctl status nginx

# View live logs
sudo journalctl -u truth-quest-backend -f

# Restart services
sudo systemctl restart truth-quest-backend
sudo systemctl restart nginx

# Check resource usage
htop

# Update manually (if needed)
cd /home/azureuser/truth-quest
git pull
cd backend && source venv/bin/activate && pip install -r requirements.txt
cd ../frontend && npm install && npm run build
sudo systemctl restart truth-quest-backend && sudo systemctl restart nginx
```

## Your URLs

- **Frontend**: http://YOUR_VM_IP
- **Backend API**: http://YOUR_VM_IP:3001
- **Health Check**: http://YOUR_VM_IP:3001/api/health

## Troubleshooting

```bash
# Backend not starting?
sudo journalctl -u truth-quest-backend -n 50

# Frontend 404?
cd /home/azureuser/truth-quest/frontend
npm run build
sudo systemctl restart nginx

# Check nginx config
sudo nginx -t
```

## Cost Optimization

Your current setup (B2s):
- 💰 ~$30-35/month
- ✅ Perfect for your needs
- 📊 Monitor with: `htop` and `df -h`

## Need Help?

- 📖 Full guide: `/deploy/DEPLOYMENT.md`
- 🐛 Check logs: `sudo journalctl -u truth-quest-backend -f`
- 🔍 Test API: `curl http://localhost:3001/api/health`
