# SaaS Chat Automation Platform

-- he he he -- 
## দ্রুত চালানোর নিয়ম

ফ্রন্টেন্ড, বেকেন্ড এবং ডেমো লগইন দ্রুত চালানোর জন্য নিচের ধাপগুলো অনুসরণ করুন।

### অপশন 1: Docker দিয়ে রান করা

সবচেয়ে সহজ উপায়:

```bash
docker compose up --build -d
docker compose exec backend python -m alembic upgrade head
docker compose exec backend python scripts/seed_local_data.py
```

তারপর ব্রাউজারে খুলুন:

- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- Swagger Docs: `http://localhost:8000/docs`

### অপশন 2: লোকাল মেশিনে আলাদা করে রান করা

এই অপশনে `MySQL` এবং `Redis` আগে থেকে চালু থাকতে হবে।

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m alembic upgrade head
python scripts/seed_local_data.py
python -m uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

### লোকাল কনফিগ নোট

- `frontend/.env` এ `VITE_API_BASE_URL=http://localhost:8000/api/v1`
- `backend/.env` এ `DATABASE_URL=mysql+pymysql://root:password@127.0.0.1:3306/automation`
- `backend/.env` এ `REDIS_URL=redis://127.0.0.1:6379/0`
- `backend/.env` এ `CELERY_TASK_ALWAYS_EAGER=true`, তাই লোকাল ডেমোর জন্য আলাদা Celery worker না চালালেও বেসিক ফ্লো কাজ করবে

### ডেমো লগইন

- Email: `admin@khubsoja.com`
- Password: `12331233`

সিড কমান্ড `python scripts/seed_local_data.py` অথবা `docker compose exec backend python scripts/seed_local_data.py` চালালে এই লগইন তৈরি হয়ে যায়।

Production-minded foundation for a multi-tenant SaaS chat automation platform built with FastAPI, React, MySQL, SQLAlchemy, Alembic, Celery, Redis, and Docker.

## MVP Hardening Notes

This codebase now includes a production-minded refinement pass focused on:

- standardized API error envelopes and centralized exception handling
- request-scoped logging with request IDs and process-time headers
- stricter settings validation and safer secret handling
- multi-stage Dockerfiles for development and production targets
- frontend Nginx production serving configuration
- seed script, Makefile shortcuts, and backend Ruff tooling
- rate-limit-ready settings and response header structure for future enforcement

## Architecture

### Backend

- `backend/app/api`: versioned API routers and endpoints
- `backend/app/core`: settings and core configuration
- `backend/app/db`: SQLAlchemy engine and session management
- `backend/app/models`: ORM models for users, accounts, memberships, onboarding keys, refresh tokens, platform connections, AI agents, prompts, knowledge, and FAQs
  plus inbox conversations/messages, Facebook comment moderation records, social post workflow records, and observability records for action usage, LLM token usage, and audit logs
  plus normalized RBAC, billing-feature, token wallet, and billing transaction tables for future pricing and entitlement management
- `backend/app/schemas`: request and response schemas
- `backend/app/services`: business-oriented service layer
- `backend/app/repositories`: repository abstractions
- `backend/app/services/automation_workflow_service.py`: account-scoped automation workflow builder, trigger matching, scheduling, and execution
- `backend/app/utils`: shared helpers including connection token encryption placeholders
- `backend/app/workers`: Celery app and worker entrypoints
- `backend/alembic`: migration configuration and versions

### Frontend

- `frontend/src/routes`: route definitions
- `frontend/src/layouts`: app and auth layouts
- `frontend/src/pages`: auth, dashboard, setup wizard, channel management, AI management, team screens, admin inbox workspace, comments moderation, and post management
- `frontend/src/components`: shared UI pieces
- `frontend/src/lib/api`: API client setup
- `frontend/src/features/auth`: auth API and persisted auth store
- `frontend/src/features/automation`: automation workflow API layer
- `frontend/src/features/accounts`: account API layer
- `frontend/src/features/platformConnections`: connection API layer
- `frontend/src/features/ai`: AI configuration API layer
- `frontend/src/features/reports`: reporting API layer
- `frontend/src/features/observability`: observability API layer
- `frontend/src/shared/types`: shared frontend types

## Automation Workflow Builder

Backend endpoints now also include:

- `GET /api/v1/automation/workflows`
- `POST /api/v1/automation/workflows`
- `GET /api/v1/automation/workflows/{workflow_id}`
- `PUT /api/v1/automation/workflows/{workflow_id}`
- `DELETE /api/v1/automation/workflows/{workflow_id}`
- `POST /api/v1/automation/workflows/{workflow_id}/run`

Implemented business rules:

- Account-scoped automation workflows with optional channel and AI-agent linkage
- Trigger support for inbound inbox messages, inbound Facebook comments, and scheduled daily jobs
- Action support for AI inbox replies, AI comment replies, and scheduled AI post-draft generation
- Keyword and customer-name filters, configurable execution delays, and daily timezone-aware scheduling
- Celery-backed execution via `sync_jobs` so automation runs use the same async foundation as the rest of the platform
- Backward-compatible webhook behavior: if no matching automation rule exists, legacy default AI reply job creation still works
- Frontend workflow builder page for creating, pausing, updating, deleting, and manually running automation rules

## Auth and RBAC Foundation

Backend endpoints now include:

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`
- `POST /api/v1/accounts`
- `POST /api/v1/accounts/join`
- `GET /api/v1/accounts/current`
- `GET /api/v1/accounts/current/members`
- `POST /api/v1/accounts/current/onboarding-keys`
- `POST /api/v1/accounts/current/onboarding-keys/{key_id}/revoke`
- `PATCH /api/v1/accounts/current/members/{membership_id}/role`

Implemented business rules:

- JWT access tokens and refresh tokens
- Server-side refresh token revocation for logout and refresh rotation
- Password hashing with Passlib
- Multi-tenant account membership model with `owner`, `admin`, and `member` roles
- Permission-checked dependencies for protected routes
- Active account resolution through `X-Account-ID`
- Onboarding key validation for revoked, expired, exhausted, and email-bound keys
- Frontend login, register, protected routing, persisted tokens, current-user bootstrap, and team page integration

## Platform Connections Module

Backend endpoints now also include:

- `GET /api/v1/platform-connections`
- `POST /api/v1/platform-connections`
- `POST /api/v1/platform-connections/facebook/oauth/start`
- `POST /api/v1/platform-connections/facebook/oauth/complete`
- `POST /api/v1/platform-connections/facebook/oauth/connect`
- `POST /api/v1/platform-connections/facebook/manual-connect`
- `POST /api/v1/platform-connections/whatsapp/manual-connect`
- `GET /api/v1/platform-connections/{connection_id}`
- `PUT /api/v1/platform-connections/{connection_id}`
- `PATCH /api/v1/platform-connections/{connection_id}/status`
- `POST /api/v1/platform-connections/{connection_id}/facebook/sync`
- `POST /api/v1/platform-connections/{connection_id}/whatsapp/sync`
- `POST /api/v1/platform-connections/{connection_id}/facebook/subscribe-webhooks`
- `POST /api/v1/platform-connections/{connection_id}/disconnect`
- `DELETE /api/v1/platform-connections/{connection_id}`

Implemented business rules:

- Account-scoped `platform_connections` records for `facebook_page` and `whatsapp`
- Permission-checked connection CRUD using the active account context
- Token storage through an encrypted placeholder utility so real secret-management integration can swap in later
- Webhook configuration fields for URL, secret, verify token, and activation state
- Connection status tracking for `pending`, `connected`, `action_required`, `disconnected`, and `error`
- Facebook Page OAuth and manual connection flows suitable for the admin panel
- WhatsApp Business manual connection flow (phone number ID + Cloud API token) with sync metadata
- Facebook connection sync and subscribed-app actions to refresh Page metadata and webhook health
- Integration summaries for token state, sync state, required permissions, and webhook subscription state
- JSON metadata and settings fields for future AI prompts, inbox automation, comment automation, and post automation
- Frontend setup wizard and admin-friendly channel management page

Where Facebook integration now lives:

- Graph API client abstraction: [backend/app/integrations/facebook/client.py](/h:/WebSite/Automation/backend/app/integrations/facebook/client.py)
- OAuth session storage: [backend/app/integrations/facebook/oauth_sessions.py](/h:/WebSite/Automation/backend/app/integrations/facebook/oauth_sessions.py)
- Connection lifecycle service: [backend/app/integrations/facebook/service.py](/h:/WebSite/Automation/backend/app/integrations/facebook/service.py)
- Webhook payload parsing: [backend/app/integrations/facebook/parsers.py](/h:/WebSite/Automation/backend/app/integrations/facebook/parsers.py)
- Stronger production secret handling can replace [backend/app/utils/crypto.py](/h:/WebSite/Automation/backend/app/utils/crypto.py) with KMS or a secrets service
- Admin connection UI: [frontend/src/pages/ConnectionsPage.tsx](/h:/WebSite/Automation/frontend/src/pages/ConnectionsPage.tsx) and [frontend/src/pages/FacebookConnectionCallbackPage.tsx](/h:/WebSite/Automation/frontend/src/pages/FacebookConnectionCallbackPage.tsx)

## AI Configuration Layer

Backend endpoints now also include:

- `GET /api/v1/ai/agents`
- `POST /api/v1/ai/agents`
- `GET /api/v1/ai/agents/{agent_id}`
- `PUT /api/v1/ai/agents/{agent_id}`
- `DELETE /api/v1/ai/agents/{agent_id}`
- `GET /api/v1/ai/prompts`
- `POST /api/v1/ai/prompts`
- `GET /api/v1/ai/prompts/{prompt_id}`
- `PUT /api/v1/ai/prompts/{prompt_id}`
- `DELETE /api/v1/ai/prompts/{prompt_id}`
- `GET /api/v1/ai/prompts/resolve/current`
- `GET /api/v1/ai/knowledge-sources`
- `POST /api/v1/ai/knowledge-sources`
- `PUT /api/v1/ai/knowledge-sources/{source_id}`
- `DELETE /api/v1/ai/knowledge-sources/{source_id}`
- `GET /api/v1/ai/faq`
- `POST /api/v1/ai/faq`
- `PUT /api/v1/ai/faq/{faq_id}`
- `DELETE /api/v1/ai/faq/{faq_id}`

Implemented business rules:

- Account-scoped AI agents with optional connection linkage and status handling
- Versioned prompts for `system_instruction`, `inbox_reply`, `comment_reply`, and `post_generation`
- Active prompt resolution with hierarchy:
  agent-specific, connection-specific, account-level default
- Knowledge source records prepared for future RAG, with file metadata and structured metadata JSON
- Structured FAQ records that can be tied to an agent or stored at account level
- Frontend pages for AI overview, agents, prompts, knowledge sources, and FAQ management

Where future AI and RAG integrations plug in:

- Prompt hierarchy and active prompt lookup live in [backend/app/services/ai_configuration_service.py](/h:/WebSite/Automation/backend/app/services/ai_configuration_service.py)
- Future retrieval and chunking pipelines can extend [backend/app/models/ai_knowledge_source.py](/h:/WebSite/Automation/backend/app/models/ai_knowledge_source.py) and [backend/app/services/ai_configuration_service.py](/h:/WebSite/Automation/backend/app/services/ai_configuration_service.py)
- File ingestion workers can be added through Celery under [backend/app/workers](/h:/WebSite/Automation/backend/app/workers)
- Provider- or business-specific admin UX can extend [frontend/src/pages/AIPromptsPage.tsx](/h:/WebSite/Automation/frontend/src/pages/AIPromptsPage.tsx), [frontend/src/pages/AIKnowledgePage.tsx](/h:/WebSite/Automation/frontend/src/pages/AIKnowledgePage.tsx), and [frontend/src/pages/AIAgentsPage.tsx](/h:/WebSite/Automation/frontend/src/pages/AIAgentsPage.tsx)

## Inbox and Conversation Management

Backend endpoints now also include:

- `GET /api/v1/inbox/conversations`
- `GET /api/v1/inbox/conversations/{conversation_id}`
- `GET /api/v1/inbox/conversations/{conversation_id}/messages`
- `POST /api/v1/inbox/conversations/{conversation_id}/assign`
- `PATCH /api/v1/inbox/conversations/{conversation_id}/status`
- `POST /api/v1/inbox/conversations/{conversation_id}/reply`

Implemented business rules:

- Account-scoped inbox records for Facebook Page and WhatsApp conversations
- Conversation filters for `status`, `platform`, and customer search by name or external ID
- Sender types for `customer`, `llm_bot`, `human_admin`, and `system`
- Delivery status tracking for outbound messages with `pending`, `queued`, `sent`, `delivered`, and `failed`
- Conversation assignment, pause, resolve, and escalate flows with account membership checks
- Abstract outbound sender service so real provider delivery logic can replace the default sender without changing the API contract
- Celery-backed outbound delivery task that updates message delivery metadata asynchronously
- Frontend inbox workspace with thread list, message pane, reply composer, status controls, assignment UI, and customer info panel

Where future inbox integrations plug in:

- Provider-specific send adapters can extend [backend/app/services/message_sender_service.py](/h:/WebSite/Automation/backend/app/services/message_sender_service.py)
- Webhook ingestion can create inbound conversations and messages through [backend/app/services/inbox_service.py](/h:/WebSite/Automation/backend/app/services/inbox_service.py)
- Background delivery and retry behavior starts in [backend/app/workers/inbox_tasks.py](/h:/WebSite/Automation/backend/app/workers/inbox_tasks.py)
- Admin inbox UX is centered in [frontend/src/pages/InboxPage.tsx](/h:/WebSite/Automation/frontend/src/pages/InboxPage.tsx)

## Facebook Comment Moderation

Backend endpoints now also include:

- `GET /api/v1/comments`
- `GET /api/v1/comments/{comment_id}`
- `PATCH /api/v1/comments/{comment_id}/status`
- `POST /api/v1/comments/{comment_id}/replies`

Implemented business rules:

- Account-scoped Facebook comment records with assignment, moderation notes, flags, and metadata
- Comment lifecycle statuses for `pending`, `replied`, `ignored`, `flagged`, and `need_review`
- Stored reply history for both human replies and AI-generated drafts
- Reply delivery statuses for `draft`, `queued`, `sent`, and `failed`
- Moderation service layer for filtering, detail loading, assignment, status actions, and reply creation
- Abstract outbound sender service so real Facebook comment publishing can replace the stub without changing the moderation API
- Celery-backed reply delivery task prepared for future auto-reply workers and retry logic
- Frontend moderation workspace with comment queue, detail panel, reply editor, status actions, and reply history

Where future comment automation plugs in:

- Provider-specific reply delivery can extend [backend/app/services/comment_reply_sender_service.py](/h:/WebSite/Automation/backend/app/services/comment_reply_sender_service.py)
- Moderation and workflow rules live in [backend/app/services/comment_moderation_service.py](/h:/WebSite/Automation/backend/app/services/comment_moderation_service.py)
- Background reply processing begins in [backend/app/workers/comment_tasks.py](/h:/WebSite/Automation/backend/app/workers/comment_tasks.py)
- Admin moderation UX is centered in [frontend/src/pages/CommentsModerationPage.tsx](/h:/WebSite/Automation/frontend/src/pages/CommentsModerationPage.tsx)

## Facebook Post Automation

Backend endpoints now also include:

- `GET /api/v1/posts`
- `POST /api/v1/posts`
- `GET /api/v1/posts/{post_id}`
- `PUT /api/v1/posts/{post_id}`
- `DELETE /api/v1/posts/{post_id}`
- `POST /api/v1/posts/{post_id}/approve`
- `POST /api/v1/posts/{post_id}/reject`
- `POST /api/v1/posts/{post_id}/schedule`
- `POST /api/v1/posts/{post_id}/publish-now`

Implemented business rules:

- Account-scoped Facebook post records with clean status transitions across `draft`, `approved`, `scheduled`, `published`, `failed`, and `rejected`
- Validation for approval-required posts so they cannot be scheduled or published until approved
- Scheduling validation that enforces future timestamps
- Tracking for `generated_by`, `is_llm_generated`, linked AI agent, linked AI prompt, metadata JSON, media URLs, and approval/rejection audit fields
- Service-based workflow for CRUD, approval, rejection, scheduling, and publish-now actions
- Abstract publisher service and Celery publish task so real Facebook publishing can plug in later without changing the post workflow API
- Frontend post list and post editor pages with workflow actions, status filters, scheduled publish display, and approval controls

Where future post publishing plugs in:

- Provider-specific publishing adapters can extend [backend/app/services/post_publisher_service.py](/h:/WebSite/Automation/backend/app/services/post_publisher_service.py)
- Workflow validation and transitions live in [backend/app/services/post_service.py](/h:/WebSite/Automation/backend/app/services/post_service.py)
- Background publishing starts in [backend/app/workers/post_tasks.py](/h:/WebSite/Automation/backend/app/workers/post_tasks.py)
- Admin post UX is centered in [frontend/src/pages/PostsPage.tsx](/h:/WebSite/Automation/frontend/src/pages/PostsPage.tsx) and [frontend/src/pages/PostEditorPage.tsx](/h:/WebSite/Automation/frontend/src/pages/PostEditorPage.tsx)

## Local Setup

### 1. Create environment files

Copy the examples before running the stack:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

On Windows PowerShell:

```powershell
Copy-Item backend/.env.example backend/.env
Copy-Item frontend/.env.example frontend/.env
```

### 2. Run with Docker Compose

```bash
docker compose up --build
```

For local development, the compose file builds the `development` targets from the backend and frontend Dockerfiles.

Services:

- Backend API: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- Frontend: `http://localhost:5173`
- MySQL: `localhost:3306`
- Redis: `localhost:6379`
- Celery worker: `automation-worker`
- Celery beat scheduler: `automation-beat`

### 3. Apply database migrations

In a second terminal:

```bash
docker compose exec backend python -m alembic upgrade head
```

### 4. Seed system data

Run the safe idempotent bootstrap seed first:

```bash
docker compose exec backend python scripts/seed_system_data.py
```

This seeds:

- default system roles
- default permissions and role-permission mappings
- default feature catalog entries
- default token purchase packages
- token wallets for existing accounts
- `account_users` links for existing memberships

### 5. Seed local data

Optional local seed:

```bash
docker compose exec backend python scripts/seed_local_data.py
```

### 6. Health check

```bash
curl http://localhost:8000/api/v1/health
```

### 7. Try the auth flow

Open the frontend at `http://localhost:5173`, then:

1. Sign in with `admin@khubsoja.com / 12331233`.
2. Open the Users page and create a `superAdmin`.
3. Sign in as that `superAdmin` and create one or more `admin` users.

### 8. Try the connection setup flow

After account setup:

1. Open `http://localhost:5173/setup` to review setup progress.
2. Open `http://localhost:5173/connections` to add a Facebook Page or WhatsApp connection.
3. For Facebook, either start OAuth or manually connect with a Page token.
4. Use the `Sync` and `Subscribe` actions to refresh Page state and subscribe the Page to app webhooks.
5. Use disconnect and edit actions to confirm account-scoped channel management.

### 9. Try the AI configuration flow

After connecting or creating account-level defaults:

1. Open `http://localhost:5173/ai` for the AI overview.
2. Open `http://localhost:5173/ai/agents` to create an AI agent.
3. Open `http://localhost:5173/ai/prompts` to create prompt versions by scope.
4. Open `http://localhost:5173/ai/knowledge` to register knowledge sources.
5. Open `http://localhost:5173/ai/faq` to add structured FAQs.

To use OpenAI as the active provider in local development, set these values in `backend/.env` first:

```env
OPENAI_API_KEY=your_rotated_openai_key
LLM_DEFAULT_PROVIDER=openai
LLM_DEFAULT_MODEL=gpt-5.4-nano
OPENAI_REPLY_PRIMARY_MODEL=gpt-5.4-nano
OPENAI_REPLY_FALLBACK_MODEL=gpt-5.4-mini
OPENAI_REPLY_CONFIDENCE_THRESHOLD=0.55
```

Optional OpenAI settings:

- `OPENAI_BASE_URL`
- `OPENAI_ORGANIZATION_ID`
- `OPENAI_PROJECT_ID`
- `OPENAI_TIMEOUT_SECONDS`

### 10. Try the inbox flow

After creating an account and at least one channel:

1. Apply the latest migration so the `conversations` and `messages` tables exist.
2. Create or ingest conversation data into the inbox tables.
3. Open `http://localhost:5173/inbox` to review threads for the active account.
4. Filter by status or platform, assign a thread, change status, and send a reply.
5. Run a Celery worker if you want outbound delivery tasks to process immediately.

### 11. Try the Facebook comments moderation flow

After connecting a Facebook Page and applying the latest migration:

1. Create or ingest records into the `facebook_comments` table.
2. Open `http://localhost:5173/comments` to review the moderation queue for the active account.
3. Filter by status, assign a moderator, and update status to ignored, flagged, replied, or needs review.
4. Save AI reply drafts or send manual replies and review the stored reply history.
5. Run a Celery worker if you want queued reply sends to process immediately.

### 12. Try the Facebook post automation flow

After connecting a Facebook Page and applying the latest migration:

1. Open `http://localhost:5173/posts` to review the post queue.
2. Create a post from `http://localhost:5173/posts/new` with manual content or AI-linked metadata.
3. Mark posts as approval-required when needed, then approve or reject them from the list or editor page.
4. Schedule a post for future publishing or trigger publish-now to queue the publish task immediately.
5. Run a Celery worker if you want queued publish tasks to process immediately.

## Running Without Docker

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Useful backend commands:

```bash
make backend-test
make backend-lint
make migrate
make seed
python scripts/seed_system_data.py
```

If you are not using Docker Compose, update `backend/.env` first so database and Redis point to local services instead of the compose hostnames:

```env
DATABASE_URL=mysql+pymysql://app:app@127.0.0.1:3306/automation
REDIS_URL=redis://127.0.0.1:6379/0
```

Windows PowerShell:

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Run the worker in a second terminal:

```bash
cd backend
source .venv/bin/activate
python -m celery -A app.workers.celery_app.celery_app worker --loglevel=info --queues=default,webhooks,sync,maintenance,messages,comments,posts
```

Windows PowerShell:

```powershell
cd backend
.venv\Scripts\Activate.ps1
python -m celery -A app.workers.celery_app.celery_app worker --loglevel=info --queues=default,webhooks,sync,maintenance,messages,comments,posts
```

Run the scheduler in a third terminal:

```bash
cd backend
source .venv/bin/activate
python -m celery -A app.workers.celery_app.celery_app beat --loglevel=info
```

Windows PowerShell:

```powershell
cd backend
.venv\Scripts\Activate.ps1
python -m celery -A app.workers.celery_app.celery_app beat --loglevel=info
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Useful frontend commands:

```bash
cd frontend
npm run typecheck
npm run build
```

## Database and Queue Notes

- SQLAlchemy 2.x style session management is configured in `backend/app/db/session.py`.
- Alembic now includes migrations for accounts, users, memberships, onboarding keys, refresh tokens, platform connections, and AI configuration tables.
- Alembic now also includes inbox conversation/message tables, Facebook comment moderation tables, and social post workflow tables.
- Alembic now also includes `webhook_events` for durable webhook intake and `sync_jobs` for orchestrating background jobs and retries.
- Alembic now also includes observability tables for action usage, LLM token usage, and audit logs.
- Alembic now also includes normalized RBAC tables (`roles`, `permissions`, `role_permissions`, `account_users`) and billing extensions (`feature_catalog`, `plan_features`, `account_subscription_feature_snapshot`, `token_purchase_packages`, `token_wallets`, `token_ledger`, `billing_transactions`).
- The Alembic migration chain is production-targeted for MySQL. For local verification, run migrations against Docker Compose MySQL or another MySQL instance instead of SQLite.
- Token wallet accounting is centralized through billing services so monthly free credits can expire after 30 days while purchased tokens remain non-expiring.
- Celery uses Redis as both broker and result backend.
- Celery beat schedules due post scans, sync-job dispatching, monthly token credits, and token expiration cleanup.
- API error responses are standardized through centralized exception handlers and include a request ID for debugging.
- Request processing adds `X-Request-ID`, `X-Process-Time-MS`, and a rate-limit-ready policy header when rate limiting is not yet configured.
- The foundation is multi-tenant through the `accounts` and `memberships` relationship.
- For compatibility with the current application layer, `memberships`, `facebook_comments`, `facebook_comment_replies`, and `social_posts` continue to power runtime flows while the new normalized tables are available for future migration and billing/RBAC expansion.

## Async Processing Foundation

Backend endpoints now also include:

- `GET /api/v1/webhooks/facebook-page`
- `POST /api/v1/webhooks/facebook-page`
- `GET /api/v1/webhooks/whatsapp`
- `POST /api/v1/webhooks/whatsapp`

Implemented business rules:

- Webhooks are stored first in `webhook_events`, then acknowledged quickly with `202 Accepted`
- Webhook receipt and processing are separated so incoming provider requests stay fast
- Incoming Facebook Page and WhatsApp webhook payloads are deduplicated with a durable event key
- Facebook GET verification uses account-scoped verify tokens and POST deliveries can validate `X-Hub-Signature-256` when the app secret is configured
- WhatsApp GET verification uses account-scoped verify tokens and POST deliveries can validate `X-Hub-Signature-256` when enabled
- Facebook webhook payloads are normalized through a dedicated parser for Messenger and comment/feed events
- WhatsApp webhook payloads are normalized through a dedicated parser for inbound message events
- Inbound processors create inbox messages and Facebook comment moderation records for supported events
- `sync_jobs` provide a reusable background-job structure for AI reply generation, scheduled post publishing, retrying failed sends, and future integrations
- Scheduled Celery jobs scan due posts, dispatch due sync jobs, apply monthly account token credits, and expire stale tokens
- Worker tasks include shared logging hooks and basic retry/backoff behavior for transient failures

Where the async foundation lives:

- Celery app and beat schedule: [backend/app/workers/celery_app.py](/h:/WebSite/Automation/backend/app/workers/celery_app.py)
- Shared task logging and retry base: [backend/app/workers/base.py](/h:/WebSite/Automation/backend/app/workers/base.py)
- Webhook ingestion API: [backend/app/api/v1/endpoints/webhooks.py](/h:/WebSite/Automation/backend/app/api/v1/endpoints/webhooks.py)
- Webhook storage and dedupe service: [backend/app/services/webhook_ingestion_service.py](/h:/WebSite/Automation/backend/app/services/webhook_ingestion_service.py)
- Placeholder inbound processors: [backend/app/services/webhook_processing_service.py](/h:/WebSite/Automation/backend/app/services/webhook_processing_service.py)
- Sync-job orchestration: [backend/app/services/sync_job_service.py](/h:/WebSite/Automation/backend/app/services/sync_job_service.py)
- Scheduled maintenance tasks: [backend/app/workers/maintenance_tasks.py](/h:/WebSite/Automation/backend/app/workers/maintenance_tasks.py)

## Facebook Page Integration Setup

### Required backend settings

Set these values in `backend/.env`:

- `FACEBOOK_APP_ID`
- `FACEBOOK_APP_SECRET`
- `FACEBOOK_OAUTH_REDIRECT_URI`

Optional:

- `FACEBOOK_GRAPH_API_VERSION`
- `FACEBOOK_HTTP_TIMEOUT_SECONDS`

Frontend flag:

- `VITE_FACEBOOK_OAUTH_ENABLED=true`

### Meta app setup

1. Add the Facebook Login product used by your app.
2. Add the redirect URI from `FACEBOOK_OAUTH_REDIRECT_URI`.
3. Configure the Page webhook callback URL as `http://localhost:8000/api/v1/webhooks/facebook-page` for local development.
4. Use the connection verify token when setting up the webhook challenge.
5. Subscribe the app to the Page fields you need for Messenger and comment/feed automation.

### Requested Facebook permissions

- `pages_show_list`
- `pages_manage_metadata`
- `pages_messaging`
- `pages_read_engagement`
- `pages_manage_posts`
- `pages_manage_engagement`

### Current provider-backed capabilities

- Connect Facebook Pages through OAuth or manual Page token flow
- Verify and process Messenger plus comment/feed webhook events
- Send Messenger replies
- Reply to comments
- Publish Page feed posts

## WhatsApp Integration Setup

### Required backend settings

Set these values in `backend/.env`:

- `WHATSAPP_GRAPH_API_BASE_URL`
- `WHATSAPP_GRAPH_API_VERSION`
- `WHATSAPP_HTTP_TIMEOUT_SECONDS`
- `WHATSAPP_VERIFY_SIGNATURE`
- `FACEBOOK_APP_SECRET` (used for Meta webhook signature validation)

### Meta app setup

1. Add WhatsApp to your Meta app and create a Cloud API access token.
2. Capture the `phone_number_id` and optional `business_account_id`.
3. In platform connections, use WhatsApp manual connect.
4. Configure webhook callback URL as `http://localhost:8000/api/v1/webhooks/whatsapp`.
5. Use the connection verify token for Meta webhook challenge verification.
6. Enable webhook fields for WhatsApp message delivery and inbound messages.

### Current provider-backed capabilities

- Connect WhatsApp phone numbers with account-scoped credentials
- Verify and ingest WhatsApp webhook events
- Map inbound WhatsApp messages to internal conversations/messages
- Send outbound WhatsApp replies through Cloud API
- Sync connection metadata and expose troubleshooting-friendly connection summary

## AI Generation Orchestration

Backend endpoints now also include:

- `POST /api/v1/ai/generation/inbox-reply`
- `POST /api/v1/ai/generation/comment-reply`
- `POST /api/v1/ai/generation/post`

Implemented business rules:

- Dedicated orchestration layer for inbox replies, comment replies, and post generation
- Prompt resolution hierarchy is reused from AI configuration (agent, connection, account default)
- FAQ and knowledge-source context builder is pluggable and included in prompt assembly
- Provider abstraction supports internal provider now, with clean OpenAI provider plug-in point
- Usage tracking writes to `action_usage_logs` and `llm_token_usage`
- Token debit is applied to account token balance when AI generation runs
- Human approval behavior is respected via agent settings (`*_requires_human_approval` and `require_human_approval`)
- Async sync jobs now execute real AI orchestration for inbound conversation/comment flows
- Frontend inbox/comments/posts include AI generate actions with preview/edit-before-send

## Observability and Reporting

Backend endpoints now also include:

- `GET /api/v1/observability/action-usage-logs`
- `POST /api/v1/observability/action-usage-logs`
- `GET /api/v1/observability/llm-token-usage`
- `POST /api/v1/observability/llm-token-usage`
- `GET /api/v1/observability/audit-logs`
- `GET /api/v1/reports/dashboard-summary`
- `GET /api/v1/reports/token-usage-summary`
- `GET /api/v1/reports/billing-summary`
- `GET /api/v1/reports/conversation-stats`
- `GET /api/v1/reports/comment-stats`
- `GET /api/v1/reports/post-stats`

Implemented business rules:

- Account-scoped `action_usage_logs`, `llm_token_usage`, and `audit_logs` tables with reporting-friendly indexed fields
- Reusable audit logging helper so important admin actions can be recorded consistently across modules
- Audit hooks on account, connection, inbox, comment, post, and report-view flows
- Basic visibility into which actions consumed tokens, LLM token usage, and estimated usage cost
- Frontend admin views for dashboard summary, billing summary, token usage reports, and audit logs

Where observability plugs in:

- API endpoints: [backend/app/api/v1/endpoints/observability.py](/h:/WebSite/Automation/backend/app/api/v1/endpoints/observability.py) and [backend/app/api/v1/endpoints/reports.py](/h:/WebSite/Automation/backend/app/api/v1/endpoints/reports.py)
- Logging helpers: [backend/app/services/audit_log_service.py](/h:/WebSite/Automation/backend/app/services/audit_log_service.py) and [backend/app/services/observability_service.py](/h:/WebSite/Automation/backend/app/services/observability_service.py)
- Aggregated reporting logic: [backend/app/services/reporting_service.py](/h:/WebSite/Automation/backend/app/services/reporting_service.py)
- Admin UI: [frontend/src/pages/DashboardPage.tsx](/h:/WebSite/Automation/frontend/src/pages/DashboardPage.tsx), [frontend/src/pages/BillingPage.tsx](/h:/WebSite/Automation/frontend/src/pages/BillingPage.tsx), [frontend/src/pages/UsageReportPage.tsx](/h:/WebSite/Automation/frontend/src/pages/UsageReportPage.tsx), and [frontend/src/pages/AuditLogPage.tsx](/h:/WebSite/Automation/frontend/src/pages/AuditLogPage.tsx)

## Deployment Notes

- The backend Dockerfile now provides `development` and `production` targets.
- The frontend Dockerfile now provides a Vite development target and an Nginx-based production target.
- Set `ENVIRONMENT=production`, `DEBUG=false`, and a strong `SECRET_KEY` before production deployment.
- Consider setting `DOCS_ENABLED=false` in production if public OpenAPI docs are not desired.
- `DATABASE_URL` and `REDIS_URL` can override the composed connection settings for hosted environments.
- Set `FACEBOOK_OAUTH_REDIRECT_URI` and the public Facebook webhook callback URL to your deployed frontend and API domains before enabling production traffic.
- Rate limiting is not enforced yet, but settings and response headers are in place so a limiter can be introduced without changing the API surface.

## Verification

Recommended verification commands:

- Backend lint: `cd backend && python -m ruff check app tests scripts`
- Backend tests: `cd backend && python -m pytest tests -q`
- Frontend checks: `cd frontend && npm run check`
- Migration run against MySQL: `cd backend && python -m alembic upgrade head`
- Seed system data: `cd backend && python scripts/seed_system_data.py`
- Seed local data: `cd backend && python scripts/seed_local_data.py`

## Next Milestones

- Delivery status reconciliation and retry policies for Facebook outbound sends
- Media attachment support for Messenger and Page publishing
- Richer report filters and export support
- Real provider-backed LLM pricing and reconciliation
- Multi-step workflow templates and richer branching conditions

## Billing Plans and Subscriptions

Backend endpoints now also include:

- `GET /api/v1/billing/plans`
- `GET /api/v1/billing/features`
- `POST /api/v1/billing/plans/seed`
- `GET /api/v1/billing/subscription`
- `POST /api/v1/billing/subscription`
- `PUT /api/v1/billing/subscription`
- `GET /api/v1/billing/wallet`
- `GET /api/v1/billing/transactions`
- `GET /api/v1/billing/token-ledger`
- `GET /api/v1/billing/token-packages`
- `POST /api/v1/billing/token-packages`
- `POST /api/v1/billing/token-purchases`

Implemented business rules:

- Account-scoped subscription records linked to reusable billing plans and feature snapshots
- Plans support both `setup_fee_usd` and recurring monthly or yearly price fields
- Wallet initialization is automatic for accounts and all token changes flow through centralized wallet and ledger services
- Monthly free plan tokens expire after 30 days, purchased tokens do not expire, and debits consume expiring monthly free tokens before purchased balances
- Subscription creation records an internal billing transaction, credits monthly free tokens, and snapshots feature entitlements
- Token package purchases record internal transactions and credit non-expiring purchased tokens
- Billing history and token ledger APIs expose transaction and token movement history for the active account
- Frontend pages now include subscription overview, plans catalog, billing history, token wallet, and token package purchase flows

Token logic summary:

- `monthly_free` credits are issued from subscriptions and stored with an `expires_at` timestamp 30 days in the future
- `purchased` credits never get an expiration timestamp
- Debits allocate tokens by priority:
  first monthly free credits with the soonest expiration, then non-expiring purchased or manual balances
- Expiration scans zero out leftover monthly free credit buckets and append explicit `expire` ledger entries

## Final Architecture

The current MVP architecture follows a modular, account-scoped service pattern:

1. API layer
   - Versioned endpoints in `backend/app/api/v1/endpoints`
   - Authentication, permission checks, and active account context via dependencies
2. Service layer
   - Domain services in `backend/app/services` for accounts, connections, AI orchestration, inbox, comments, posts, billing, and reporting
   - Route handlers remain thin and delegate business logic to services
3. Integration layer
   - Provider-specific modules under `backend/app/integrations` (`facebook`, `whatsapp`)
   - Parsers and API clients are isolated from core domain services
4. Persistence layer
   - SQLAlchemy ORM models in `backend/app/models`
   - Alembic migrations in `backend/alembic/versions`
5. Async orchestration
   - Celery workers in `backend/app/workers`
   - Durable webhook intake and `sync_jobs` for retries and deferred workflows
6. Frontend app
   - Feature-oriented API modules in `frontend/src/features/*/api`
   - Shared strongly typed contracts in `frontend/src/shared/types`
   - Page-level workflows in `frontend/src/pages`

## Sample Local MVP Flow

Use this script-style flow to run a full local setup:

1. Start infrastructure and services
   - `docker compose up --build`
2. Apply migrations
   - `docker compose exec backend python -m alembic upgrade head`
3. Seed local data and billing plans
   - `docker compose exec backend python scripts/seed_local_data.py`
   - `docker compose exec backend python -c "from app.db.session import SessionLocal; from app.services.billing_service import BillingService; db=SessionLocal(); print(BillingService(db).seed_default_plans()); db.close()"`
4. Open app and authenticate
   - Frontend: `http://localhost:5173`
   - Login with `admin@khubsoja.com / 12331233`
5. Verify user hierarchy and RBAC
   - Create a `superAdmin` from the Users page
   - Login as that `superAdmin` and create one or more `admin` users
6. Configure subscription and token wallet
   - Open Billing page
   - Select a plan and update subscription
   - Confirm token balance and monthly credit changes
7. Connect channels
   - Facebook Page: OAuth or manual connect
   - WhatsApp: manual connect with `phone_number_id` + access token
8. Run AI configuration
   - Create AI agent
   - Add prompts for inbox/comment/post
   - Add FAQ and knowledge sources
9. Exercise automation workflows
   - Inbox: generate AI reply draft, edit, send
   - Comments: generate AI comment reply, review, send
   - Posts: generate AI post draft, edit, approve, publish/schedule
10. Validate observability
   - Dashboard, Usage Report, Billing, and Audit Logs should reflect actions and token usage

## External Dependency TODOs

Only external integration dependencies remain intentionally unresolved:

- OpenAI provider execution is exposed through the provider abstraction but requires real credentials and provider wiring.
- Production secret/key management should replace the local token encryption helper.
- Live Meta app configuration and approved permissions are required for real production Facebook/WhatsApp traffic.
