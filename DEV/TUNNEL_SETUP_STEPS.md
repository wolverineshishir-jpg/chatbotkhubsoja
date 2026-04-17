# Cloudflare Tunnel Setup for KhubSoja

## Step 1: Create Tunnel in Cloudflare Dashboard

### 1. Go to Cloudflare Zero Trust
Navigate to: **https://dash.teams.cloudflare.com/**

### 2. Create New Tunnel
1. In the left sidebar, go to **Networks** → **Tunnels**
2. Click **Add Tunnel**
3. Select **Cloudflared** as the connector
4. Name your tunnel: `khubsoja-dev`
5. Click **Save**

### 3. Get Your Token
After creating, you'll see a command like:
```bash
docker run cloudflare/cloudflared:latest tunnel --no-autoupdate run --token eyJh...
```

**Copy the entire token** (it starts with `eyJh...`)

---

## Step 2: Save Your Token

Create a file `.env.tunnel` in the chatbotkhubsoja folder:

```env
TUNNEL_TOKEN=eyJh...paste_your_token_here
```

---

## Step 3: Start the Tunnel

Run this command in the chatbotkhubsoja folder:

```bash
docker run -d \
  --name cloudflared \
  --restart unless-stopped \
  --network host \
  cloudflare/cloudflared:2025.11.1 \
  tunnel --no-autoupdate run --token "$(cat .env.tunnel | grep TUNNEL_TOKEN | cut -d= -f2-)"
```

Or create `docker-compose.tunnel.yml` and use:
```bash
docker compose -f docker-compose.tunnel.yml up -d
```

---

## Step 4: Configure Routes (Public Hostnames)

After the tunnel connects (check with `docker logs cloudflared`), go back to the Cloudflare dashboard:

1. Select your tunnel `khubsoja-dev`
2. Click **Add Public Hostname** (3 times for each service)

### Route 1: Backend API
| Field | Value |
|-------|-------|
| Subdomain | api |
| Domain | yourdomain.com |
| Service | HTTP |
| URL | localhost:8000 |

### Route 2: Frontend
| Field | Value |
|-------|-------|
| Subdomain | (empty) or app |
| Domain | yourdomain.com |
| Service | HTTP |
| URL | localhost:5173 |

### Route 3: Webhook
| Field | Value |
|-------|-------|
| Subdomain | webhook |
| Domain | yourdomain.com |
| Service | HTTP |
| URL | localhost:8000 |
| Path | /api/v1/webhooks/facebook-page* |

---

## Step 5: Update KhubSoja Config

Once you have your URL (e.g., `https://yourdomain.com`), update:

**backend/.env:**
```env
FACEBOOK_OAUTH_REDIRECT_URI=https://yourdomain.com/connections/facebook/callback
```

**frontend/.env:**
```env
VITE_API_BASE_URL=https://yourdomain.com/api/v1
```

Then restart: `docker compose down && docker compose up -d`

---

## Done!

After setup:
- Frontend: `https://yourdomain.com`
- API: `https://yourdomain.com/api/v1`
- Webhook: `https://yourdomain.com/api/v1/webhooks/facebook-page`

Create your tunnel in the Cloudflare dashboard, get your token, and let me know when you have it - I'll help you configure everything else!