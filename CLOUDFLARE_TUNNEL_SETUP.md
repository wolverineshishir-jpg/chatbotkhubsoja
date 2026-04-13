# Cloudflare Tunnel Setup Guide for KhubSoja

This guide explains how to set up **Cloudflare Tunnel** to expose your local KhubSoja Chat Automation Platform to the internet. This replaces the need for ngrok and provides a stable, persistent URL.

---

## Why Cloudflare Tunnel?

| Feature | ngrok (Free) | Cloudflare Tunnel |
|---------|--------------|-------------------|
| URL Stability | Changes on restart | Permanent (your domain) |
| Cost | Limited free tier | Free (Cloudflare Zero Trust) |
| SSL | Auto-provided | Auto-provided |
| Bandwidth | Limited | Unlimited |
| Custom Domain | Paid feature | Free |

---

## Prerequisites

1. **Cloudflare Account** - Sign up at https://cloudflare.com
2. **Domain on Cloudflare** - Add your domain to Cloudflare (free domain works)
3. **Access to Cloudflare Zero Trust** - For tunnel management
4. **Docker & Docker Compose** - Running KhubSoja locally

---

## Step 1: Create a Cloudflare Tunnel

### Option A: Via Cloudflare Dashboard (Recommended)

1. **Go to Cloudflare Zero Trust**
   - Navigate to: https://dash.teams.cloudflare.com/
   - Or from Cloudflare Dashboard → Zero Trust

2. **Create a New Tunnel**
   - Go to **Networks** → **Tunnels**
   - Click **Add Tunnel**
   - Select **Cloudflared** as the connector
   - Name your tunnel: `khubsoja-dev`

3. **Copy the Tunnel Token**
   - After creating, you'll see a token like:
     ```
     eyJhIjoiZXhhbXBsZSIsInQiOiIxMjM0NTY3ODkwYWJjZGVmIn0...
     ```
   - **Save this token** - you'll need it later

### Option B: Via API (Advanced)

```bash
# Replace with your actual account ID
ACCOUNT_ID="your_account_id"

# Create tunnel
curl -X POST "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/cfd_tunnel" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  --data '{"name": "khubsoja-dev", "meta": {"config_source": "dashboard"}}'
```

---

## Step 2: Run the Cloudflare Tunnel (Docker)

Create a `docker-compose.tunnel.yml` file in your project root:

```yaml
version: '3.8'

services:
  cloudflared:
    image: cloudflare/cloudflared:2025.11.1
    container_name: cloudflared
    restart: unless-stopped
    command: tunnel --no-autoupdate run --token ${TUNNEL_TOKEN}
    environment:
      - TUNNEL_TOKEN=${TUNNEL_TOKEN}
    networks:
      - tunnel

networks:
  tunnel:
    name: tunnel
```

### Create a `.env.tunnel` file

```env
# Your Cloudflare Tunnel token (from Step 1)
TUNNEL_TOKEN=eyJhIjoiZXhhbXBsZSIsInQiOiIxMjM0NTY3ODkwYWJjZGVmIn0...
```

### Start the Tunnel

```bash
# Start only the tunnel
docker compose -f docker-compose.tunnel.yml --env-file .env.tunnel up -d

# Or add to existing docker-compose.yml
docker compose up -d
```

### Verify the Tunnel is Connected

```bash
# Check container status
docker ps | grep cloudflared

# Check logs
docker logs cloudflared
```

You should see: `Connection registered` and `Registered tunnel connection`

---

## Step 3: Configure Public Hostnames

Now you need to route traffic to your services. You can do this via:

### Option A: Dashboard Configuration (Recommended)

1. Go to **Networks** → **Tunnels** → Select your tunnel
2. Click **Add Public Hostname**
3. Configure for **Backend API**:
   - **Subdomain**: `api` (or `backend`)
   - **Domain**: `yourdomain.com` (your Cloudflare domain)
   - **Service Type**: `HTTP`
   - **URL**: `automation-backend:8000` (Docker container name)
4. Configure for **Frontend**:
   - **Subdomain**: `app` (or leave empty for root)
   - **Domain**: `yourdomain.com`
   - **Service Type**: `HTTP`
   - **URL**: `automation-frontend:5173`
5. Configure for **Facebook Webhook**:
   - **Subdomain**: `webhook`
   - **Domain**: `yourdomain.com`
   - **Service Type**: `HTTP`
   - **URL**: `automation-backend:8000`
   - **Path**: `/api/v1/webhooks/facebook-page*`

### Option B: Docker Network Integration

Update your `docker-compose.yml` to connect services to the tunnel network:

```yaml
services:
  backend:
    networks:
      - chatbotkhubsoja_default
      - tunnel
  frontend:
    networks:
      - chatbotkhubsoja_default
      - tunnel
  cloudflared:
    networks:
      - tunnel

networks:
  tunnel:
    external: true
```

---

## Step 4: Update KhubSoja Configuration

Once you have your Cloudflare URL (e.g., `https://yourdomain.com`), update the configuration:

### Backend Configuration (.env)

```env
# Update OAuth redirect URI to use your Cloudflare domain
FACEBOOK_APP_ID=your_facebook_app_id
FACEBOOK_APP_SECRET=your_facebook_app_secret
FACEBOOK_OAUTH_REDIRECT_URI=https://yourdomain.com/connections/facebook/callback
```

### Frontend Configuration (.env)

```env
# Update API base URL to use your Cloudflare domain
VITE_API_BASE_URL=https://yourdomain.com/api/v1
```

### Restart Services

```bash
docker compose down
docker compose up -d
```

---

## Step 5: Facebook Developer Dashboard Update

Now update your Facebook app with your new Cloudflare URLs:

### Valid OAuth Redirect URIs
```
https://yourdomain.com/connections/facebook/callback
```

### Webhook Callback URL
```
https://yourdomain.com/api/v1/webhooks/facebook-page
```

### Verify Token
Use the same token you configured (e.g., `1234`)

---

## Complete Setup Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                     Cloudflare Edge Network                    │
│                                                                 │
│  yourdomain.com ──▶ cloudflared Tunnel ──▶ Docker Network      │
│                                                                 │
│  /                      ──▶ Frontend (5173)                   │
│  /api/*                ──▶ Backend (8000)                     │
│  /api/v1/webhooks/*    ──▶ Backend (8000)                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Troubleshooting

### Tunnel Not Connecting

```bash
# Check logs
docker logs cloudflared

# Verify token is correct
docker exec cloudflared tunnel validate
```

### Service Not Reachable

1. Make sure services are on the same Docker network
2. Use container names (not localhost):
   - `automation-backend` (not `localhost:8000`)
   - `automation-frontend` (not `localhost:5173`)

### SSL Certificate Issues

Cloudflare Tunnel provides SSL automatically. Make sure:
- **SSL/TLS Mode** in Cloudflare Dashboard is set to **Full** or **Flexible**
- Your origin server has a valid certificate (or HTTP is fine for testing)

### Webhook Path Not Matching

Use wildcard routing:
- **URL**: `http://automation-backend:8000`
- **Path**: `/api/v1/webhooks/facebook-page*`

---

## Useful Commands

```bash
# View tunnel status
docker logs cloudflared | grep -i "connection\|healthy"

# Restart tunnel
docker restart cloudflared

# Stop tunnel
docker compose -f docker-compose.tunnel.yml down

# Check all tunnels
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://api.cloudflare.com/client/v4/accounts/YOUR_ACCOUNT_ID/cfd_tunnel"
```

---

## Production Notes

### For Production Use
1. Use a **reserved** subdomain (won't change)
2. Set up **Cloudflare Access** for authentication
3. Enable **Cloudflare WAF** rules
4. Use **Full (Strict)** SSL mode

### Security Best Practices
- Never commit your `TUNNEL_TOKEN` to version control
- Use Cloudflare Access to add authentication if needed
- Keep cloudflared updated

---

## Quick Reference

| Item | Value |
|------|-------|
| Tunnel Name | `khubsoja-dev` |
| Backend URL | `https://yourdomain.com` |
| API URL | `https://yourdomain.com/api/v1` |
| Webhook URL | `https://yourdomain.com/api/v1/webhooks/facebook-page` |
| OAuth Callback | `https://yourdomain.com/connections/facebook/callback` |

---

## Next Steps

After completing this setup:
1. Go to https://yourdomain.com
2. Login with `admin@khubsoja.com` / `12331233`
3. Connect Facebook Page via OAuth
4. Test webhook delivery
5. Your platform is now accessible from anywhere!