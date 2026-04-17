# SaaS Chat Automation Platform - Technical Capacity Report

## Executive Summary

The **KhubSoja Chat Automation Platform** is a production-minded, multi-tenant SaaS chat automation system built with **FastAPI**, **React**, **MySQL**, **SQLAlchemy**, **Celery**, **Redis**, and **Docker**. The platform enables businesses to automate customer interactions across Facebook Messenger, WhatsApp, and other messaging channels using AI-powered workflows.

---

## 1. Backend Architecture & Capacity

### 1.1 Technology Stack

| Component | Technology | Version/Details |
|-----------|------------|-----------------|
| API Framework | FastAPI | Python 3.12 |
| Database | MySQL | 8.4 |
| ORM | SQLAlchemy | 2.x style |
| Migration Tool | Alembic | - |
| Task Queue | Celery | 5.5.1 |
| Cache/Broker | Redis | 7.4 |
| Authentication | JWT | Access + Refresh tokens |
| Containerization | Docker Compose | - |

### 1.2 API Endpoints by Category

#### Authentication (`/api/v1/auth`)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/register` | POST | User registration with account creation |
| `/login` | POST | JWT access + refresh token login |
| `/refresh` | POST | Refresh access token |
| `/logout` | POST | Revoke refresh token |
| `/change-password` | POST | Change user password |
| `/me` | GET | Get current authenticated user |

#### Accounts (`/api/v1/accounts`)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/current` | GET | Get current active account |
| `/current/members` | GET | List team members |
| `` | POST | Create new account |
| `/join` | POST | Join account via onboarding key |
| `/current/onboarding-keys` | POST | Generate onboarding key |
| `/current/onboarding-keys/{key_id}/revoke` | POST | Revoke onboarding key |
| `/current/members/{membership_id}/role` | PATCH | Update member role |

#### Platform Connections (`/api/v1/platform-connections`)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `` | GET | List all connections |
| `` | POST | Create connection |
| `/{connection_id}` | GET | Get connection details |
| `/{connection_id}` | PUT | Update connection |
| `/{connection_id}/status` | PATCH | Update connection status |
| `/facebook/oauth/start` | POST | Start Facebook OAuth |
| `/facebook/oauth/complete` | POST | Complete Facebook OAuth |
| `/facebook/manual-connect` | POST | Manual Facebook connection |
| `/whatsapp/manual-connect` | POST | Manual WhatsApp connection |
| `/{connection_id}/facebook/sync` | POST | Sync Facebook page data |
| `/{connection_id}/facebook/subscribe-webhooks` | POST | Subscribe to webhooks |
| `/{connection_id}/disconnect` | POST | Disconnect platform |
| `/{connection_id}` | DELETE | Delete connection |

#### AI Configuration (`/api/v1/ai`)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/agents` | GET | List AI agents |
| `/agents` | POST | Create AI agent |
| `/agents/{agent_id}` | GET | Get agent details |
| `/agents/{agent_id}` | PUT | Update agent |
| `/agents/{agent_id}` | DELETE | Delete agent |
| `/prompts` | GET | List prompts |
| `/prompts` | POST | Create prompt |
| `/prompts/{prompt_id}` | GET | Get prompt details |
| `/prompts/{prompt_id}` | PUT | Update prompt |
| `/prompts/{prompt_id}` | DELETE | Delete prompt |
| `/prompts/resolve/current` | GET | Resolve active prompt |
| `/knowledge-sources` | GET | List knowledge sources |
| `/knowledge-sources` | POST | Create knowledge source |
| `/knowledge-sources/{source_id}` | PUT | Update knowledge source |
| `/knowledge-sources/{source_id}` | DELETE | Delete knowledge source |
| `/faq` | GET | List FAQs |
| `/faq` | POST | Create FAQ |
| `/faq/{faq_id}` | PUT | Update FAQ |
| `/faq/{faq_id}` | DELETE | Delete FAQ |

#### AI Generation (`/api/v1/ai/generation`)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/inbox-reply` | POST | Generate inbox reply |
| `/comment-reply` | POST | Generate comment reply |
| `/post` | POST | Generate social post |

#### Automation Workflows (`/api/v1/automation/workflows`)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `` | GET | List workflows |
| `` | POST | Create workflow |
| `/{workflow_id}` | GET | Get workflow details |
| `/{workflow_id}` | PUT | Update workflow |
| `/{workflow_id}` | DELETE | Delete workflow |
| `/{workflow_id}/run` | POST | Manual trigger workflow |

#### Inbox (`/api/v1/inbox`)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/conversations` | GET | List conversations |
| `/conversations/{conversation_id}` | GET | Get conversation details |
| `/conversations/{conversation_id}/messages` | GET | Get conversation messages |
| `/conversations/{conversation_id}/assign` | POST | Assign conversation |
| `/conversations/{conversation_id}/status` | PATCH | Update conversation status |
| `/conversations/{conversation_id}/reply` | POST | Send reply |

#### Comments (`/api/v1/comments`)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `` | GET | List comments |
| `/{comment_id}` | GET | Get comment details |
| `/{comment_id}/status` | PATCH | Update comment status |
| `/{comment_id}/replies` | POST | Create reply |

#### Posts (`/api/v1/posts`)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `` | GET | List posts |
| `` | POST | Create post |
| `/{post_id}` | GET | Get post details |
| `/{post_id}` | PUT | Update post |
| `/{post_id}` | DELETE | Delete post |
| `/{post_id}/approve` | POST | Approve post |
| `/{post_id}/reject` | POST | Reject post |
| `/{post_id}/schedule` | POST | Schedule post |
| `/{post_id}/publish-now` | POST | Publish immediately |

#### Billing (`/api/v1/billing`)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/plans` | GET | List billing plans |
| `/plans/seed` | POST | Seed default plans |
| `/features` | GET | List features |
| `/subscription` | GET | Get current subscription |
| `/subscription` | POST | Create subscription |
| `/subscription` | PUT | Update subscription |
| `/wallet` | GET | Get token wallet |
| `/transactions` | GET | List billing transactions |
| `/token-ledger` | GET | List token ledger entries |
| `/token-packages` | GET | List token packages |
| `/token-packages` | POST | Create token package |
| `/token-purchases` | POST | Purchase tokens |

#### Observability (`/api/v1/observability`)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/action-usage-logs` | GET/POST | Action usage logs |
| `/llm-token-usage` | GET/POST | LLM token usage |
| `/audit-logs` | GET | Audit logs |

#### Reports (`/api/v1/reports`)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/dashboard-summary` | GET | Dashboard summary |
| `/token-usage-summary` | GET | Token usage summary |
| `/billing-summary` | GET | Billing summary |
| `/conversation-stats` | GET | Conversation statistics |
| `/comment-stats` | GET | Comment statistics |
| `/post-stats` | GET | Post statistics |

#### Webhooks (`/api/v1/webhooks`)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/facebook-page` | GET | Facebook webhook verification |
| `/facebook-page` | POST | Facebook webhook handler |
| `/whatsapp` | GET | WhatsApp webhook verification |
| `/whatsapp` | POST | WhatsApp webhook handler |

### 1.3 Database Models (37 Models)

#### Core Entities
| Model | Purpose |
|-------|---------|
| `User` | Platform users with hierarchy columns |
| `Account` | Multi-tenant accounts with token balance |
| `Membership` | User-Account relationship with roles |
| `OnboardingKey` | Account invitation keys |
| `RefreshToken` | JWT refresh tokens with revocation |

#### Platform Connections
| Model | Purpose |
|-------|---------|
| `PlatformConnection` | Facebook Page & WhatsApp connections |
| `FacebookComment` | Comment moderation records |
| `FacebookCommentReply` | Comment reply history |

#### AI & Content
| Model | Purpose |
|-------|---------|
| `AIAgent` | AI agent configuration |
| `AIPrompt` | Versioned prompts (system, inbox, comment, post) |
| `AIKnowledgeSource` | RAG-ready knowledge sources |
| `FAQKnowledge` | Structured FAQs |

#### Communication
| Model | Purpose |
|-------|---------|
| `Conversation` | Inbox conversations |
| `Message` | Individual messages |
| `SocialPost` | Facebook posts with workflow |

#### Automation
| Model | Purpose |
|-------|---------|
| `AutomationWorkflow` | Account-scoped automation rules |

#### Workflow & Async
| Model | Purpose |
|-------|---------|
| `WebhookEvent` | Durable webhook storage |
| `SyncJob` | Background job orchestration |

#### Observability
| Model | Purpose |
|-------|---------|
| `ActionUsageLog` | Action consumption tracking |
| `LLMTokenUsage` | LLM token usage tracking |
| `AuditLog` | Admin action auditing |

#### RBAC
| Model | Purpose |
|-------|---------|
| `Role` | System roles (owner, admin, member) |
| `Permission` | Granular permissions |
| `RolePermission` | Role-permission mapping |
| `AccountUser` | Account-user links |

#### Billing
| Model | Purpose |
|-------|---------|
| `BillingPlan` | Subscription plans |
| `FeatureCatalog` | Feature definitions |
| `PlanFeatures` | Plan-feature mapping |
| `AccountSubscription` | Account subscriptions |
| `AccountSubscriptionFeatureSnapshot` | Feature entitlements |
| `TokenPurchasePackage` | Token packages |
| `TokenWallet` | Account token balance |
| `TokenLedger` | Token transaction history |
| `BillingTransaction` | Billing history |

### 1.4 Services (38 Services)

| Service | Function |
|---------|----------|
| `AuthService` | Registration, login, token management |
| `AccountService` | Account CRUD, team management, onboarding |
| `PlatformConnectionService` | Connection lifecycle management |
| `AIContfigurationService` | Agent, prompt, knowledge, FAQ management |
| `InboxService` | Conversation and message management |
| `CommentModerationService` | Comment filtering, status, replies |
| `PostService` | Post CRUD, approval, scheduling |
| `AutomationWorkflowService` | Workflow builder, triggers, execution |
| `BillingService` | Plans, subscriptions, transactions |
| `TokenWalletService` | Token balance management |
| `TokenLedgerService` | Token transaction tracking |
| `TokenConsumptionService` | Token debit on AI usage |
| `TokenMaintenanceService` | Token expiration handling |
| `WebhookIngestionService` | Webhook storage and deduplication |
| `WebhookProcessingService` | Inbound event processing |
| `SyncJobService` | Background job orchestration |
| `MessageSenderService` | Outbound message delivery |
| `CommentReplySenderService` | Comment reply delivery |
| `PostPublisherService` | Post publishing |
| `ReportingService` | Dashboard and report aggregation |
| `ObservabilityService` | Usage and metrics tracking |
| `AuditLogService` | Admin action logging |
| `HealthService` | Health check endpoint |

#### AI Services
| Service | Function |
|---------|----------|
| `OrchestrationService` | AI reply/post generation |
| `PromptResolutionService` | Active prompt hierarchy lookup |
| `KnowledgeContextService` | RAG context building |
| `ReplyRoutingService` | AI response routing |
| `ProviderRegistry` | AI provider abstraction |
| `InternalProvider` | Internal AI provider |
| `OpenAIProvider` | OpenAI integration |

### 1.5 Background Workers (Celery)

| Task | Function |
|------|----------|
| `process_webhook_event` | Process stored webhooks |
| `deliver_outbound_message` | Deliver inbox messages |
| `deliver_comment_reply` | Deliver comment replies |
| `publish_social_post` | Publish scheduled posts |
| `execute_sync_job` | Execute sync jobs |
| `scan_due_scheduled_posts` | Scan due scheduled posts |
| `dispatch_due_sync_jobs` | Dispatch due sync jobs |
| `scan_due_automation_workflows` | Scan due automation triggers |
| `issue_monthly_token_credits` | Monthly token credit issuance |
| `expire_tokens` | Expire monthly tokens |

### 1.6 Integrations

#### Facebook Integration
- Graph API client abstraction
- OAuth session storage
- Webhook payload parsing
- Messenger & comment processing

#### WhatsApp Integration
- Cloud API integration
- Webhook handling
- Message delivery

---

## 2. Frontend Architecture & Capacity

### 2.1 Technology Stack

| Component | Technology |
|-----------|------------|
| Framework | React |
| Build Tool | Vite |
| Routing | React Router |
| State | Zustand (persist) |
| HTTP Client | Axios |
| UI | Custom components |

### 2.2 Pages (25 Pages)

| Page | Route | Purpose |
|------|-------|---------|
| LoginPage | `/login` | User authentication |
| NotFoundPage | `/*` | 404 handling |
| DashboardPage | `/dashboard` | Overview & summary |
| SetupWizardPage | `/setup` | Onboarding wizard |
| ConnectionsPage | `/connections` | Channel management |
| FacebookConnectionCallbackPage | `/connections/facebook/callback` | OAuth callback |
| AIOverviewPage | `/ai` | AI configuration overview |
| AIAgentsPage | `/ai/agents` | AI agent management |
| AIPromptsPage | `/ai/prompts` | Prompt management |
| AIKnowledgePage | `/ai/knowledge` | Knowledge sources |
| AIFAQPage | `/ai/faq` | FAQ management |
| AutomationWorkflowsPage | `/automation` | Workflow builder |
| InboxPage | `/inbox` | Conversation management |
| CommentsModerationPage | `/comments` | Comment moderation |
| PostsPage | `/posts` | Post management |
| PostEditorPage | `/posts/new`, `/posts/{id}` | Post editor |
| TeamPage | `/team` | Team management |
| BillingPage | `/billing` | Subscription overview |
| BillingPlansPage | `/billing/plans` | Plan catalog |
| BillingHistoryPage | `/billing/history` | Transaction history |
| TokenWalletPage | `/billing/wallet` | Token balance |
| TokenPackagesPage | `/billing/tokens` | Token packages |
| UsageReportPage | `/reports/usage` | Usage analytics |
| AuditLogPage | `/reports/audit` | Audit trail |
| ChangePasswordPage | `/settings/password` | Password change |

### 2.3 Feature Modules

| Feature | Purpose |
|---------|---------|
| `auth` | Authentication API, persisted store |
| `accounts` | Account API layer |
| `automation` | Workflow API |
| `ai` | AI configuration API |
| `platformConnections` | Connection API |
| `reports` | Reporting API |
| `observability` | Observability API |

### 2.4 Frontend Capabilities

- **Authentication**: Login, registration, token management
- **Multi-account**: Account switching, team management
- **Channel Setup**: Facebook & WhatsApp connection flows
- **AI Management**: Agents, prompts, knowledge, FAQs
- **Workflow Builder**: Visual automation rule creation
- **Inbox Workspace**: Conversation threads, messaging
- **Moderation Queue**: Comment management
- **Post Editor**: Content creation, scheduling
- **Billing**: Plans, subscriptions, tokens
- **Reporting**: Dashboard, usage, audit logs

---

## 3. Use Cases

### 3.1 Multi-Tenant SaaS

**Use Cases:**
- Create new accounts with unique slug and name
- Invite team members via onboarding keys
- Role-based access control (owner, admin, member)
- Account-scoped data isolation
- Switch between multiple accounts

**Endpoints:** `POST /api/v1/accounts`, `POST /api/v1/accounts/join`, `GET /api/v1/accounts/current/members`

### 3.2 Authentication & Security

**Use Cases:**
- User registration with automatic account creation
- JWT-based authentication (access + refresh tokens)
- Token refresh with rotation
- Secure logout (server-side token revocation)
- Password change

**Endpoints:** `POST /api/v1/auth/register`, `POST /api/v1/auth/login`, `POST /api/v1/auth/refresh`, `POST /api/v1/auth/logout`

### 3.3 Platform Connections

**Use Cases:**
- Connect Facebook Page via OAuth
- Connect Facebook Page manually (page token)
- Connect WhatsApp manually (phone number ID + token)
- Sync connection metadata
- Subscribe to webhooks
- Disconnect platforms

**Endpoints:** `/api/v1/platform-connections/*`

**Supported Platforms:**
- Facebook Pages (Messenger, comments)
- WhatsApp Business

### 3.4 AI Configuration

**Use Cases:**
- Create AI agents with connection linkage
- Versioned prompts for different contexts:
  - System instructions
  - Inbox reply
  - Comment reply
  - Post generation
- Active prompt resolution (agent → connection → account default)
- Knowledge source management (future RAG)
- FAQ management

**Endpoints:** `/api/v1/ai/agents`, `/api/v1/ai/prompts`, `/api/v1/ai/knowledge-sources`, `/api/v1/ai/faq`

### 3.5 AI Generation & Orchestration

**Use Cases:**
- Generate AI inbox reply
- Generate AI comment reply
- Generate AI social post
- Context assembly (FAQ + knowledge)
- Usage tracking and token debiting
- Human approval workflow

**Endpoints:** `/api/v1/ai/generation/*`

### 3.6 Automation Workflows

**Use Cases:**
- Create account-scoped workflows
- Trigger types:
  - Inbound inbox messages
  - Inbound Facebook comments
  - Scheduled daily jobs
- Action types:
  - AI inbox reply
  - AI comment reply
  - AI post-draft generation
- Filters: keyword, customer name
- Configurable execution delay
- Timezone-aware scheduling
- Manual workflow trigger

**Endpoints:** `/api/v1/automation/workflows/*`

### 3.7 Inbox Management

**Use Cases:**
- View conversations by platform (Facebook, WhatsApp)
- Filter by status, platform, customer
- Assign conversations to team members
- Status transitions: open, paused, resolved, escalated
- Send replies
- Message delivery tracking

**Endpoints:** `/api/v1/inbox/conversations/*`

### 3.8 Comment Moderation

**Use Cases:**
- Queue Facebook comments for review
- Filter by status (pending, replied, ignored, flagged, need_review)
- Assign to moderators
- Add moderation notes
- Store reply history
- AI reply generation

**Endpoints:** `/api/v1/comments/*`

### 3.9 Post Automation

**Use Cases:**
- Create posts with manual content or AI-generated
- Workflow states: draft → approved → scheduled → published
- Approval-required posts
- Scheduling with future timestamps
- Manual publish
- Linked AI agent and prompts

**Endpoints:** `/api/v1/posts/*`

### 3.10 Billing & Payments

**Use Cases:**
- View available billing plans
- Subscribe to plans (monthly/yearly)
- Update subscription
- Purchase token packages
- View token wallet balance
- Transaction history
- Token ledger tracking

**Endpoints:** `/api/v1/billing/*`

**Token Logic:**
- Monthly free tokens expire after 30 days
- Purchased tokens never expire
- Debits consume expiring tokens first

### 3.11 Reporting & Analytics

**Use Cases:**
- Dashboard summary
- Token usage summary
- Conversation statistics
- Comment statistics
- Post statistics
- Billing summary

**Endpoints:** `/api/v1/reports/*`

### 3.12 Observability

**Use Cases:**
- Action usage logging
- LLM token usage tracking
- Audit log for admin actions

**Endpoints:** `/api/v1/observability/*`

### 3.13 Webhooks

**Use Cases:**
- Facebook Page webhook (Messenger, comments)
- WhatsApp webhook
- Webhook event storage with deduplication
- Async processing
- Verify tokens

**Endpoints:** `/api/v1/webhooks/*`

---

## 4. Technical Specifications

### 4.1 Database

- **Engine**: MySQL 8.4
- **ORM**: SQLAlchemy 2.x with session-per-request
- **Migrations**: Alembic (13 migrations)
- **Tables**: 40+ normalized tables

### 4.2 Caching & Queue

- **Redis**: Cache and Celery broker
- **Celery Queues**: default, webhooks, sync, maintenance, messages, comments, posts
- **Celery Beat**: Scheduled tasks for post scanning, sync job dispatch, token credits, token expiration

### 4.3 API Design

- **Versioning**: `/api/v1/*`
- **Authentication**: JWT (Bearer token)
- **Multi-tenancy**: `X-Account-ID` header
- **Error Handling**: Centralized exception handling
- **Request ID**: Tracking with `X-Request-ID` header
- **Rate Limiting**: Headers ready (not enforced)

### 4.4 Security

- Password hashing (Passlib)
- Server-side refresh token revocation
- Permission-based route protection
- Account-scoped data isolation
- Token encryption placeholders

### 4.5 Docker Services

| Service | Image | Ports |
|---------|-------|-------|
| backend | chatbotkhubsoja-backend | 8000 |
| frontend | chatbotkhubsoja-frontend | 5173 |
| worker | chatbotkhubsoja-worker | - |
| beat | chatbotkhubsoja-beat | - |
| mysql | mysql:8.4 | 3306 |
| redis | redis:7.4-alpine | 6379 |

---

## 5. Deployment Notes

- Multi-stage Dockerfiles (development/production)
- Frontend Nginx production serving
- Environment variables for all configuration
- Secrets management placeholders
- Health check endpoints

---

## 6. Summary

The **KhubSoja Chat Automation Platform** is a comprehensive, production-ready system with:

- **37 database models** for complete data management
- **50+ API endpoints** covering all business functions
- **38 business services** for clean architecture
- **10 background tasks** for async processing
- **25 frontend pages** for complete user experience
- **10+ major use cases** from auth to billing

The platform supports:
- Multi-tenant SaaS with team management
- Facebook & WhatsApp integrations
- AI-powered automation workflows
- Complete billing and token management
- Comprehensive reporting and observability