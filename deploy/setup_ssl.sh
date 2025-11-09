#!/bin/bash
# SSL Setup Script for Azure VM
# This adds HTTPS support using Let's Encrypt (free SSL certificate)

set -e

echo "🔒 Setting up SSL for Truth Quest Backend"
echo "=========================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root: sudo ./setup_ssl.sh"
    exit 1
fi

# Install Certbot
echo "📦 Installing Certbot..."
apt update
apt install -y certbot python3-certbot-nginx

# Get domain name or IP
read -p "Enter your domain name (or press Enter to use IP): " DOMAIN

if [ -z "$DOMAIN" ]; then
    echo "⚠️  No domain provided. You need a domain name for Let's Encrypt."
    echo "Alternative: Use Cloudflare Tunnel (recommended for IP-only setup)"
    exit 1
fi

# Update nginx configuration for SSL
echo "🔧 Updating nginx configuration..."
cat > /etc/nginx/sites-available/truth-quest << EOF
# HTTP - Redirect to HTTPS
server {
    listen 80;
    server_name $DOMAIN;
    
    location / {
        return 301 https://\$server_name\$request_uri;
    }
}

# HTTPS - Main application
server {
    listen 443 ssl http2;
    server_name $DOMAIN;
    
    # SSL certificates (will be added by certbot)
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # Frontend (static files)
    location / {
        root /home/azureuser/truth-quest/frontend/dist;
        try_files \$uri \$uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # Backend API
    location /api/ {
        proxy_pass http://localhost:3001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        
        # CORS headers
        add_header 'Access-Control-Allow-Origin' 'https://truth-quest.web.app' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS' always;
        add_header 'Access-Control-Allow-Headers' 'Content-Type, Authorization' always;
        
        if (\$request_method = 'OPTIONS') {
            return 204;
        }
    }
}
EOF

# Get SSL certificate
echo "🔐 Obtaining SSL certificate..."
certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN

# Enable auto-renewal
echo "🔄 Setting up auto-renewal..."
systemctl enable certbot.timer
systemctl start certbot.timer

# Test nginx configuration
nginx -t

# Restart nginx
systemctl restart nginx

# Update firewall
echo "🔥 Updating firewall..."
ufw allow 443/tcp

echo ""
echo "✅ SSL Setup Complete!"
echo "================================"
echo "Your backend is now accessible via HTTPS:"
echo "https://$DOMAIN/api/health"
echo ""
echo "SSL certificate will auto-renew every 90 days"
echo "================================"
