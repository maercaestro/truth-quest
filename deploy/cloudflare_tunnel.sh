#!/bin/bash
# Cloudflare Tunnel Setup (Alternative to SSL - Works with IP addresses)
# This creates a secure HTTPS tunnel without needing a domain or SSL certificate

set -e

echo "🌐 Setting up Cloudflare Tunnel for Truth Quest"
echo "================================================"

# Install cloudflared
echo "📦 Installing Cloudflare Tunnel..."
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared.deb
rm cloudflared.deb

echo ""
echo "✅ Cloudflare Tunnel installed!"
echo ""
echo "📋 Next Steps:"
echo "1. Run: cloudflared tunnel login"
echo "2. Run: cloudflared tunnel create truth-quest"
echo "3. Run: cloudflared tunnel route dns truth-quest api.your-domain.com"
echo "4. Create config file: nano ~/.cloudflared/config.yml"
echo ""
echo "Config file example:"
echo "---"
echo "tunnel: YOUR_TUNNEL_ID"
echo "credentials-file: /home/azureuser/.cloudflared/YOUR_TUNNEL_ID.json"
echo ""
echo "ingress:"
echo "  - hostname: api.your-domain.com"
echo "    service: http://localhost:3001"
echo "  - service: http_status:404"
echo "---"
echo ""
echo "5. Run: cloudflared tunnel run truth-quest"
echo ""
echo "Full guide: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/"
