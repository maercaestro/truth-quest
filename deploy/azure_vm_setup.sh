#!/bin/bash
# Initial deployment script for Azure VM
# Run this ONCE on your Azure VM to set everything up

set -e  # Exit on error

echo "🚀 Truth Quest - Initial Azure VM Setup"
echo "========================================"
echo ""

# Variables
APP_DIR="/home/azureuser/truth-quest"
BACKEND_SERVICE="truth-quest-backend"
FRONTEND_BUILD_DIR="$APP_DIR/frontend/dist"

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    echo "❌ Please don't run as root. Run as azureuser."
    exit 1
fi

echo "📦 Installing system dependencies..."
sudo apt update
sudo apt install -y python3-pip python3-venv nginx git curl

# Install Node.js 20.x LTS
echo "📦 Installing Node.js 20.x LTS..."
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

echo "✅ System dependencies installed!"
echo ""

# Clone repository if not exists
if [ ! -d "$APP_DIR" ]; then
    echo "📥 Cloning repository..."
    cd /home/azureuser
    git clone https://github.com/maercaestro/truth-quest.git
else
    echo "📥 Repository exists, pulling latest..."
    cd $APP_DIR
    git pull origin main
fi

cd $APP_DIR

# Setup Backend
echo "🔧 Setting up backend..."
cd backend

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt

# Note: .env will be created by CI/CD from GitHub secrets
# serviceAccountKey.json needs to be uploaded manually once
if [ ! -f "serviceAccountKey.json" ]; then
    echo "⚠️  Firebase serviceAccountKey.json not found!"
    echo "📝 You'll need to upload it manually after setup:"
    echo "    scp backend/serviceAccountKey.json azureuser@your-vm-ip:/home/azureuser/truth-quest/backend/"
    echo ""
    echo "Creating placeholder for now..."
    echo '{}' > serviceAccountKey.json
fi

echo "✅ Backend setup complete!"
echo ""

# Setup Frontend
echo "🔧 Setting up frontend..."
cd ../frontend

# Update API endpoint for production
if [ ! -f "src/config.js" ]; then
    echo "Creating production config..."
    cat > src/config.js << 'EOF'
export const API_URL = window.location.hostname === 'localhost' 
  ? 'http://localhost:3001'
  : 'http://' + window.location.hostname + ':3001';
EOF
fi

npm install
npm run build

echo "✅ Frontend built!"
echo ""

# Setup systemd service for backend
echo "🔧 Creating systemd service..."
sudo tee /etc/systemd/system/$BACKEND_SERVICE.service > /dev/null << EOF
[Unit]
Description=Truth Quest Backend API
After=network.target

[Service]
Type=simple
User=azureuser
WorkingDirectory=$APP_DIR/backend
Environment="PATH=$APP_DIR/backend/venv/bin"
ExecStart=$APP_DIR/backend/venv/bin/python server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Setup nginx
echo "🔧 Configuring nginx..."
sudo tee /etc/nginx/sites-available/truth-quest > /dev/null << 'EOF'
server {
    listen 80;
    server_name _;

    # Frontend
    location / {
        root /home/azureuser/truth-quest/frontend/dist;
        try_files $uri $uri/ /index.html;
        add_header Cache-Control "no-cache";
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:3001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Increase timeout for long-running analysis
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
        proxy_read_timeout 300;
    }
}
EOF

# Enable nginx site
sudo ln -sf /etc/nginx/sites-available/truth-quest /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test nginx config
sudo nginx -t

# Open firewall ports
echo "🔧 Configuring firewall..."
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp
sudo ufw --force enable

# Start services
echo "🚀 Starting services..."
sudo systemctl daemon-reload
sudo systemctl enable $BACKEND_SERVICE
sudo systemctl start $BACKEND_SERVICE
sudo systemctl restart nginx

echo ""
echo "✅ ============================================"
echo "✅ Initial setup complete!"
echo "✅ ============================================"
echo ""
echo "📋 Service Status:"
sudo systemctl status $BACKEND_SERVICE --no-pager -l
echo ""
echo "🌐 Your app should be running at:"
echo "   http://$(curl -s ifconfig.me)"
echo ""
echo "📝 Useful commands:"
echo "   Check backend logs:  sudo journalctl -u $BACKEND_SERVICE -f"
echo "   Check nginx logs:    sudo tail -f /var/log/nginx/error.log"
echo "   Restart backend:     sudo systemctl restart $BACKEND_SERVICE"
echo "   Restart nginx:       sudo systemctl restart nginx"
echo ""
echo "🔄 CI/CD is now active! Push to main branch to auto-deploy."
