# Cloudflare CLI - Switch Account

Cloudflare CLI uses **credentials files** instead of login/logout. To switch accounts:

## Option 1: Create New Tunnel (Recommended)

1. Go to: https://dash.teams.cloudflare.com/
2. Login to your new account
3. Go to **Networks** → **Tunnels**
4. Click **Add Tunnel** → Select **Cloudflared**
5. Name: `khubsoja-dev` → Save
6. **Copy the token** shown

## Option 2: Use API Token

Create an API token in your new account:
1. Go to: https://dash.cloudflare.com/profile/api-tokens
2. Create Custom Token with these permissions:
   - Account: Read, Write
   - Zone: Read, Write
3. Use the token with cloudflared

## After Getting New Token

Run:
```bash
# Kill existing tunnel
pkill -f cloudflared

# Run new tunnel
cloudflared tunnel run --token "your_new_token"
```

---

## To find your new token:

In Cloudflare Dashboard:
1. Go to **Networks** → **Tunnels**
2. Click your tunnel
3. Click **Configure** 
4. Under **Install and Run**, copy the token (starts with `eyJh...`)

Once you have the new account and token, paste it here and I'll help you set everything up!