# KhubSoja Chat Automation Platform - Setup & Usage Guide

## Overview

KhubSoja is a multi-tenant SaaS chat automation platform that enables businesses to automate customer interactions across Facebook Messenger, WhatsApp, and other messaging channels using AI-powered workflows.

---

## Quick Start (Local Development)

### Prerequisites
- Docker & Docker Compose
- 4GB RAM minimum

### Step 1: Start the Services

```bash
cd chatbotkhubsoja

# Copy environment files
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# Start all services
docker compose up --build -d
```

### Step 2: Database Setup

```bash
# Run migrations
docker compose exec backend python -m alembic upgrade head

# Seed system data (roles, permissions, features)
docker compose exec backend python scripts/seed_system_data.py

# Seed demo data (admin user)
docker compose exec backend python scripts/seed_local_data.py
```

### Step 3: Access the Application

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |

### Step 4: Login

- **Email**: `admin@khubsoja.com`
- **Password**: `12331233`

---

## Facebook Integration Setup

For Facebook OAuth and webhooks to work, you need to configure ngrok and Facebook Developer App.

### Option A: With ngrok (Recommended for development)

#### 1. Start ngrok

```bash
ngrok http 8000
```

Get your ngrok URL (e.g., `https://abc123.ngrok-free.app`)

#### 2. Update Configuration

Edit `backend/.env`:
```env
FACEBOOK_APP_ID=your_facebook_app_id
FACEBOOK_APP_SECRET=your_facebook_app_secret
FACEBOOK_OAUTH_REDIRECT_URI=https://your-ngrok-url.ngrok-free.app/connections/facebook/callback
```

Edit `frontend/.env`:
```env
VITE_API_BASE_URL=https://your-ngrok-url.ngrok-free.app/api/v1
```

#### 3. Restart Services

```bash
docker compose down
docker compose up -d
```

#### 4. Facebook Developer Dashboard Setup

Go to https://developers.facebook.com/ and configure:

**Facebook Login → Settings:**
- Client OAuth Login: **ON**
- Web OAuth Login: **ON**
- Valid OAuth Redirect URIs:
  ```
  https://your-ngrok-url.ngrok-free.app/connections/facebook/callback
  ```

**Webhooks:**
- Callback URL: `https://your-ngrok-url.ngrok-free.app/api/v1/webhooks/facebook-page`
- Verify Token: `1234` (or any token you configure)

**Required Permissions:**
- `pages_show_list`
- `pages_manage_metadata`
- `pages_messaging`
- `pages_read_engagement`
- `pages_manage_posts`
- `pages_manage_engagement`

### Option B: Manual Connection (No OAuth)

If you don't want to use OAuth, you can connect manually:

1. Get a Page Access Token from [Facebook Graph API Explorer](https://developers.facebook.com/tools/explorer/)
2. Go to Connections page in the app
3. Click "Manual Connect"
4. Paste the Page Access Token

---

## Connecting a Facebook Page

### Step 1: Go to Connections

Navigate to: http://localhost:5173/connections

### Step 2: Connect Facebook

1. Click **"Connect with Facebook OAuth"**
2. Login to Facebook
3. Authorize the app
4. Select the Page to connect

### Step 3: Configure Webhooks

After connecting, for each connection:
1. Click **"Sync"** to refresh page data
2. Click **"Subscribe"** to subscribe to webhooks

---

## Features & Use Cases

### 1. Multi-Account Management
- Create and manage multiple accounts
- Invite team members via onboarding keys
- Role-based access (owner, admin, member)

### 2. Channel Connections
- Connect Facebook Pages
- Connect WhatsApp Business
- Sync and manage connections

### 3. AI Configuration
- Create AI agents
- Manage prompts (system, inbox, comment, post)
- Add knowledge sources
- Manage FAQs

### 4. Automation Workflows
- Create automated workflows
- Triggers:
  - Inbound messages
  - Inbound comments
  - Scheduled jobs
- Actions:
  - AI inbox reply
  - AI comment reply
  - AI post generation

### 5. Inbox Management
- View conversations
- Filter by platform, status
- Assign to team members
- Send replies

### 6. Comment Moderation
- Review pending comments
- Update status (replied, ignored, flagged)
- AI reply generation

### 7. Post Automation
- Create posts manually or AI-generated
- Approval workflow
- Schedule posts
- Publish immediately

### 8. Billing & Tokens
- View subscription plans
- Purchase token packages
- Track token usage

### 9. Reports & Analytics
- Dashboard summary
- Usage reports
- Audit logs

---

## Environment Variables

### Backend (.env)

```env
# App
PROJECT_NAME=SaaS Chat Automation Platform
DEBUG=false

# Database
MYSQL_USER=app
MYSQL_PASSWORD=app
MYSQL_HOST=mysql
MYSQL_PORT=3306
MYSQL_DATABASE=automation

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# Security
SECRET_KEY=your-secret-key-min-32-chars

# Facebook (required for OAuth)
FACEBOOK_APP_ID=your_app_id
FACEBOOK_APP_SECRET=your_app_secret
FACEBOOK_OAUTH_REDIRECT_URI=http://localhost:5173/connections/facebook/callback

# OpenAI (optional)
OPENAI_API_KEY=your_openai_key
LLM_DEFAULT_PROVIDER=openai
```

### Frontend (.env)

```env
VITE_APP_NAME=SaaS Chat Automation
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_FACEBOOK_OAUTH_ENABLED=true
```

---

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/refresh` - Refresh token
- `POST /api/v1/auth/logout` - Logout

### Accounts
- `GET /api/v1/accounts/current` - Get current account
- `POST /api/v1/accounts` - Create account
- `GET /api/v1/accounts/current/members` - List members

### Platform Connections
- `GET /api/v1/platform-connections` - List connections
- `POST /api/v1/platform-connections/facebook/oauth/start` - Start OAuth
- `POST /api/v1/platform-connections/facebook/manual-connect` - Manual connect

### AI
- `GET /api/v1/ai/agents` - List agents
- `POST /api/v1/ai/agents` - Create agent
- `GET /api/v1/ai/prompts` - List prompts
- `POST /api/v1/ai/generation/inbox-reply` - Generate reply

### Automation
- `GET /api/v1/automation/workflows` - List workflows
- `POST /api/v1/automation/workflows` - Create workflow

### Billing
- `GET /api/v1/billing/plans` - List plans
- `GET /api/v1/billing/wallet` - Get token wallet

Full API documentation available at: http://localhost:8000/docs

---

## Troubleshooting

### "Facebook OAuth is not configured"
- Ensure `FACEBOOK_APP_ID` and `FACEBOOK_APP_SECRET` are set in backend/.env
- Restart the backend container

### Webhook not working
- Use ngrok to expose local server
- Update webhook URL in Facebook Developer Dashboard
- Ensure verify token matches

### Database connection error
- Check MySQL is running: `docker ps`
- Verify DATABASE_URL in .env

### Port already in use
```bash
# Find process using port
lsof -i :8000
# Kill it
kill <PID>
```

---

## Architecture

```
┌─────────────┐     ┌─────────────┐
│   Frontend  │────▶│   Backend   │
│   (React)   │◀────│  (FastAPI)  │
└─────────────┘     └──────┬──────┘
                          │
              ┌───────────┼───────────┐
              ▼           ▼           ▼
         ┌────────┐  ┌────────┐  ┌────────┐
         │  MySQL │  │ Redis  │  │ Celery │
         │   DB   │  │  Queue │  │ Workers│
         └────────┘  └────────┘  └────────┘
```

- **Frontend**: React + Vite
- **Backend**: FastAPI + SQLAlchemy
- **Database**: MySQL 8.4
- **Queue**: Celery + Redis
- **Container**: Docker Compose

---

## Demo Credentials

- **Email**: admin@khubsoja.com
- **Password**: 12331233

---

## Support

For issues and questions, check:
1. Backend logs: `docker compose logs backend`
2. API docs: http://localhost:8000/docs
3. System health: http://localhost:8000/api/v1/health