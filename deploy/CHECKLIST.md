# 🚀 Deployment Checklist

Use this checklist to ensure smooth deployment!

---

## Pre-Deployment (One Time)

### 1. GitHub Repository Setup
- [ ] Repository is on GitHub
- [ ] You have admin access
- [ ] Latest code is pushed to `main` branch

### 2. GitHub Secrets Configuration
- [ ] Add `AZURE_VM_HOST` (VM IP address)
- [ ] Add `AZURE_VM_USERNAME` (azureuser)
- [ ] Add `AZURE_VM_SSH_KEY` (private SSH key)
- [ ] Add `OPENAI_API_KEY` (OpenAI API key)
- [ ] Add `BRAVE_API_KEY` (Brave Search API key)
- [ ] Add `YOUTUBE_API_KEY` (YouTube API key)

📖 **Guide**: `/deploy/SECRETS_SETUP.md`

### 3. Azure VM Preparation
- [ ] VM is running (Standard B2s recommended)
- [ ] You can SSH into VM: `ssh azureuser@YOUR_VM_IP`
- [ ] VM has Ubuntu 20.04+ installed
- [ ] Ports 80, 443, 22 are open in Azure Network Security Group

### 4. Initial VM Setup
```bash
# SSH into VM
ssh azureuser@YOUR_VM_IP

# Download and run setup script
curl -o setup.sh https://raw.githubusercontent.com/maercaestro/truth-quest/main/deploy/azure_vm_setup.sh
chmod +x setup.sh
./setup.sh
```

- [ ] Setup script completed successfully
- [ ] No errors during installation

### 5. Upload Firebase Credentials
```bash
# From your LOCAL machine
scp backend/serviceAccountKey.json azureuser@YOUR_VM_IP:/home/azureuser/truth-quest/backend/
```

- [ ] Firebase key uploaded successfully
- [ ] Key is in correct location

### 6. Verify Services
```bash
# On VM
sudo systemctl status truth-quest-backend
sudo systemctl status nginx
```

- [ ] Backend service is running
- [ ] Nginx service is running
- [ ] No errors in logs

---

## First Deployment

### 1. Push to GitHub
```bash
# On your LOCAL machine
cd /path/to/truth-quest
git add .
git commit -m "Initial deployment"
git push origin main
```

- [ ] Code pushed successfully to `main` branch

### 2. Monitor Deployment
- [ ] Go to GitHub → Actions tab
- [ ] Watch deployment workflow
- [ ] Workflow completes successfully (green checkmark)

### 3. Test Your Application

Visit your VM's public IP:

```bash
Frontend: http://YOUR_VM_IP
Backend:  http://YOUR_VM_IP:3001/api/health
```

- [ ] Frontend loads correctly
- [ ] Can sign in with Google/GitHub/Email
- [ ] Can analyze a YouTube video
- [ ] Results display correctly
- [ ] No console errors in browser (F12)

---

## Post-Deployment Testing

### Authentication Test
- [ ] Google sign-in works
- [ ] GitHub sign-in works  
- [ ] Email/password sign-in works
- [ ] User profile displays
- [ ] Sign out works

### Feature Test
- [ ] Can paste YouTube URL
- [ ] "Sample Check" mode works (~30-60 seconds)
- [ ] "Full Check" mode works (~2-5 minutes)
- [ ] Results show grade (A-F)
- [ ] Verified facts display
- [ ] Sources are clickable
- [ ] Video embed works

### Usage Limit Test
- [ ] Usage counter appears after sign-in
- [ ] Counter increments after each analysis
- [ ] Daily limit (10) is enforced
- [ ] Error message shows when limit reached

### Donation Button Test
- [ ] "Buy me a coffee" button visible
- [ ] Links to correct Buy Me a Coffee page
- [ ] Opens in new tab

---

## Ongoing Maintenance

### Daily Usage
```bash
# Make changes locally
# Test locally first!
git add .
git commit -m "Your changes"
git push origin main

# Wait ~2 minutes
# Check GitHub Actions for deployment status
# Visit site to verify changes
```

- [ ] CI/CD pipeline deploys automatically
- [ ] Changes appear on live site
- [ ] No deployment errors

### Weekly Checks
- [ ] Check VM resource usage: `htop`
- [ ] Check disk space: `df -h`
- [ ] Review backend logs: `sudo journalctl -u truth-quest-backend -n 100`
- [ ] Check for OS updates: `sudo apt update && sudo apt upgrade`

### Monthly Checks
- [ ] Review API usage and costs
- [ ] Rotate API keys if needed
- [ ] Check for package updates
- [ ] Review user feedback

---

## Troubleshooting Checklist

### Deployment Fails
- [ ] Check GitHub Actions logs
- [ ] Verify all 6 secrets are added
- [ ] Test SSH connection manually
- [ ] Check VM has enough disk space

### Backend Won't Start
- [ ] Check backend logs: `sudo journalctl -u truth-quest-backend -n 50`
- [ ] Verify `.env` file exists with correct keys
- [ ] Verify `serviceAccountKey.json` exists
- [ ] Check if port 3001 is in use: `sudo lsof -i :3001`

### Frontend Shows 404
- [ ] Check if frontend was built: `ls /home/azureuser/truth-quest/frontend/dist`
- [ ] Rebuild manually: `cd frontend && npm run build`
- [ ] Restart nginx: `sudo systemctl restart nginx`
- [ ] Check nginx logs: `sudo tail -f /var/log/nginx/error.log`

### API Calls Fail
- [ ] Check CORS settings in `server.py`
- [ ] Verify API keys are valid
- [ ] Test backend directly: `curl http://localhost:3001/api/health`
- [ ] Check firewall allows port 3001

---

## Rollback Procedure

If deployment breaks production:

```bash
# 1. Revert the commit
git revert HEAD
git push origin main

# OR restore to previous working commit
git reset --hard <previous-commit-hash>
git push --force origin main

# 2. CI/CD will auto-deploy the reverted version

# 3. OR manually rollback on VM
ssh azureuser@YOUR_VM_IP
cd /home/azureuser/truth-quest
git checkout <previous-commit-hash>
cd backend && source venv/bin/activate && pip install -r requirements.txt
cd ../frontend && npm install && npm run build
sudo systemctl restart truth-quest-backend nginx
```

---

## Success Criteria

Your deployment is successful when:

✅ Frontend loads at `http://YOUR_VM_IP`  
✅ Users can sign in and analyze videos  
✅ CI/CD deploys automatically on push  
✅ All services are running and stable  
✅ No errors in logs  
✅ Resource usage is healthy  

---

## Get Help

- 📖 **Full deployment guide**: `/deploy/DEPLOYMENT.md`
- 🔐 **Secrets setup**: `/deploy/SECRETS_SETUP.md`
- ⚡ **Quick commands**: `/deploy/QUICK_START.md`
- 🐛 **Check logs**: `sudo journalctl -u truth-quest-backend -f`
- 💬 **GitHub Issues**: Report problems on GitHub

---

**Status**: [ ] Not Started | [ ] In Progress | [ ] ✅ Complete

**Deployed URL**: http://____________________

**Deployment Date**: ____________________

**Last Updated**: ____________________
