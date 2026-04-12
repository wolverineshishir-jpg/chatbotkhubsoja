from enum import StrEnum


class UserStatus(StrEnum):
    ACTIVE = "active"
    INVITED = "invited"
    DISABLED = "disabled"


class UserRole(StrEnum):
    OWNER = "owner"
    SUPER_ADMIN = "superAdmin"
    ADMIN = "admin"


class MembershipRole(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"


class MembershipStatus(StrEnum):
    ACTIVE = "active"
    INVITED = "invited"
    REVOKED = "revoked"


class PlatformType(StrEnum):
    FACEBOOK_PAGE = "facebook_page"
    WHATSAPP = "whatsapp"


class ConnectionStatus(StrEnum):
    PENDING = "pending"
    CONNECTED = "connected"
    ACTION_REQUIRED = "action_required"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class AIAgentStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class AutomationWorkflowStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class AutomationTriggerType(StrEnum):
    INBOX_MESSAGE_RECEIVED = "inbox_message_received"
    FACEBOOK_COMMENT_CREATED = "facebook_comment_created"
    SCHEDULED_DAILY = "scheduled_daily"


class AutomationActionType(StrEnum):
    GENERATE_INBOX_REPLY = "generate_inbox_reply"
    GENERATE_COMMENT_REPLY = "generate_comment_reply"
    GENERATE_POST_DRAFT = "generate_post_draft"


class PromptType(StrEnum):
    SYSTEM_INSTRUCTION = "system_instruction"
    INBOX_REPLY = "inbox_reply"
    COMMENT_REPLY = "comment_reply"
    POST_GENERATION = "post_generation"


class KnowledgeSourceStatus(StrEnum):
    DRAFT = "draft"
    READY = "ready"
    PROCESSING = "processing"
    ARCHIVED = "archived"


class KnowledgeSourceType(StrEnum):
    FILE = "file"
    URL = "url"
    TEXT = "text"


class ConversationStatus(StrEnum):
    OPEN = "open"
    ASSIGNED = "assigned"
    PAUSED = "paused"
    RESOLVED = "resolved"
    ESCALATED = "escalated"


class SenderType(StrEnum):
    CUSTOMER = "customer"
    LLM_BOT = "llm_bot"
    HUMAN_ADMIN = "human_admin"
    SYSTEM = "system"


class MessageDirection(StrEnum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class MessageDeliveryStatus(StrEnum):
    PENDING = "pending"
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"


class CommentStatus(StrEnum):
    PENDING = "pending"
    REPLIED = "replied"
    IGNORED = "ignored"
    FLAGGED = "flagged"
    NEED_REVIEW = "need_review"


class CommentReplyStatus(StrEnum):
    DRAFT = "draft"
    QUEUED = "queued"
    SENT = "sent"
    FAILED = "failed"


class PostStatus(StrEnum):
    DRAFT = "draft"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"
    REJECTED = "rejected"


class PostGeneratedBy(StrEnum):
    HUMAN_ADMIN = "human_admin"
    LLM_BOT = "llm_bot"
    SYSTEM = "system"


class WebhookEventSource(StrEnum):
    FACEBOOK_PAGE = "facebook_page"
    WHATSAPP = "whatsapp"


class WebhookEventStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    IGNORED = "ignored"


class SyncJobType(StrEnum):
    WEBHOOK_PROCESSING = "webhook_processing"
    AI_REPLY_GENERATION = "ai_reply_generation"
    AUTOMATION_RULE_EXECUTION = "automation_rule_execution"
    SCHEDULED_POST_PUBLISH = "scheduled_post_publish"
    RETRY_FAILED_SEND = "retry_failed_send"
    TOKEN_EXPIRATION = "token_expiration"
    TOKEN_MONTHLY_CREDIT = "token_monthly_credit"


class SyncJobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY_SCHEDULED = "retry_scheduled"
    CANCELED = "canceled"


class ActionUsageType(StrEnum):
    INBOUND_MESSAGE = "inbound_message"
    OUTBOUND_MESSAGE = "outbound_message"
    COMMENT_REPLY = "comment_reply"
    POST_PUBLISH = "post_publish"
    AI_REPLY_GENERATION = "ai_reply_generation"
    TOKEN_CREDIT = "token_credit"
    TOKEN_EXPIRATION = "token_expiration"
    ADMIN_ACTION = "admin_action"


class BillingInterval(StrEnum):
    MONTHLY = "monthly"
    YEARLY = "yearly"


class RoleScope(StrEnum):
    SYSTEM = "system"
    ACCOUNT = "account"


class FeatureValueType(StrEnum):
    BOOLEAN = "boolean"
    INTEGER = "integer"
    DECIMAL = "decimal"
    TOKEN = "token"


class SubscriptionStatus(StrEnum):
    TRIALING = "trialing"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    EXPIRED = "expired"


class TokenWalletStatus(StrEnum):
    ACTIVE = "active"
    FROZEN = "frozen"
    CLOSED = "closed"


class TokenLedgerEntryType(StrEnum):
    CREDIT = "credit"
    DEBIT = "debit"
    RESERVE = "reserve"
    RELEASE = "release"
    EXPIRE = "expire"
    ADJUSTMENT = "adjustment"


class TokenLedgerSourceType(StrEnum):
    SUBSCRIPTION = "subscription"
    TOKEN_PACKAGE = "token_package"
    AI_USAGE = "ai_usage"
    ADMIN = "admin"
    EXPIRATION = "expiration"


class TokenAllocationType(StrEnum):
    MONTHLY_FREE = "monthly_free"
    PURCHASED = "purchased"
    MANUAL = "manual"


class BillingTransactionType(StrEnum):
    SUBSCRIPTION = "subscription"
    TOKEN_PURCHASE = "token_purchase"
    ADJUSTMENT = "adjustment"
    REFUND = "refund"


class BillingTransactionStatus(StrEnum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELED = "canceled"


class AuditActionType(StrEnum):
    ADMIN_ACTION = "admin_action"
    ACCOUNT_CREATED = "account_created"
    ACCOUNT_JOINED = "account_joined"
    ONBOARDING_KEY_CREATED = "onboarding_key_created"
    ONBOARDING_KEY_REVOKED = "onboarding_key_revoked"
    CONNECTION_CREATED = "connection_created"
    CONNECTION_UPDATED = "connection_updated"
    CONNECTION_STATUS_UPDATED = "connection_status_updated"
    CONNECTION_DISCONNECTED = "connection_disconnected"
    CONNECTION_DELETED = "connection_deleted"
    CONVERSATION_ASSIGNED = "conversation_assigned"
    CONVERSATION_STATUS_UPDATED = "conversation_status_updated"
    MESSAGE_REPLY_SENT = "message_reply_sent"
    COMMENT_STATUS_UPDATED = "comment_status_updated"
    COMMENT_REPLY_CREATED = "comment_reply_created"
    POST_CREATED = "post_created"
    POST_UPDATED = "post_updated"
    POST_APPROVED = "post_approved"
    POST_REJECTED = "post_rejected"
    POST_SCHEDULED = "post_scheduled"
    POST_PUBLISH_NOW = "post_publish_now"
    AUTOMATION_WORKFLOW_CREATED = "automation_workflow_created"
    AUTOMATION_WORKFLOW_UPDATED = "automation_workflow_updated"
    AUTOMATION_WORKFLOW_DELETED = "automation_workflow_deleted"
    AUTOMATION_WORKFLOW_TRIGGERED = "automation_workflow_triggered"
    REPORT_VIEWED = "report_viewed"


class AuditResourceType(StrEnum):
    ACCOUNT = "account"
    PLATFORM_CONNECTION = "platform_connection"
    CONVERSATION = "conversation"
    MESSAGE = "message"
    FACEBOOK_COMMENT = "facebook_comment"
    FACEBOOK_COMMENT_REPLY = "facebook_comment_reply"
    SOCIAL_POST = "social_post"
    AUTOMATION_WORKFLOW = "automation_workflow"
    REPORT = "report"
    TEAM = "team"
