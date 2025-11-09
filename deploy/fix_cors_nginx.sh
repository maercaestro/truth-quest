#!/bin/bash
# Fix nginx CORS configuration for api.oasis-pet.com

echo "🔧 Updating nginx configuration for CORS..."

sudo tee /etc/nginx/sites-available/truth-quest > /dev/null << 'EOF'
server {
    listen 80;
    server_name api.oasis-pet.com;
    
    location / {
        # Handle preflight requests
        if ($request_method = 'OPTIONS') {
            add_header 'Access-Control-Allow-Origin' 'https://truth-quest.web.app' always;
            add_header 'Access-Control-Allow-Origin' 'https://truth-quest.firebaseapp.com' always;
            add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS' always;
            add_header 'Access-Control-Allow-Headers' 'Content-Type, Authorization' always;
            add_header 'Access-Control-Max-Age' 1728000;
            add_header 'Content-Type' 'text/plain charset=UTF-8';
            add_header 'Content-Length' 0;
            return 204;
        }
        
        # Proxy to backend
        proxy_pass http://localhost:3001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
        
        # Don't add CORS headers here - let Flask handle them
        # But hide them if Flask sends duplicates
        proxy_hide_header 'Access-Control-Allow-Origin';
        proxy_hide_header 'Access-Control-Allow-Methods';
        proxy_hide_header 'Access-Control-Allow-Headers';
    }
}
EOF

echo "✅ nginx configuration updated"
echo "🧪 Testing configuration..."
sudo nginx -t

if [ $? -eq 0 ]; then
    echo "🔄 Reloading nginx..."
    sudo systemctl reload nginx
    echo "✅ Done! CORS should now work."
else
    echo "❌ Configuration error. Please check the syntax."
fi
