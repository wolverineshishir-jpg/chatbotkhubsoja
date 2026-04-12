from fastapi import APIRouter

from app.api.v1.endpoints.ai_configuration import router as ai_configuration_router
from app.api.v1.endpoints.ai_generation import router as ai_generation_router
from app.api.v1.endpoints.accounts import router as accounts_router
from app.api.v1.endpoints.automation import router as automation_router
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.billing import router as billing_router
from app.api.v1.endpoints.comments import router as comments_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.inbox import router as inbox_router
from app.api.v1.endpoints.platform_connections import router as platform_connections_router
from app.api.v1.endpoints.posts import router as posts_router
from app.api.v1.endpoints.observability import router as observability_router
from app.api.v1.endpoints.reports import router as reports_router
from app.api.v1.endpoints.users import router as users_router
from app.api.v1.endpoints.webhooks import router as webhooks_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(accounts_router, prefix="/accounts", tags=["accounts"])
api_router.include_router(automation_router, prefix="/automation", tags=["automation"])
api_router.include_router(ai_configuration_router, prefix="/ai", tags=["ai"])
api_router.include_router(ai_generation_router, prefix="/ai", tags=["ai-generation"])
api_router.include_router(comments_router, prefix="/comments", tags=["comments"])
api_router.include_router(inbox_router, prefix="/inbox", tags=["inbox"])
api_router.include_router(platform_connections_router, prefix="/platform-connections", tags=["platform-connections"])
api_router.include_router(billing_router, prefix="/billing", tags=["billing"])
api_router.include_router(posts_router, prefix="/posts", tags=["posts"])
api_router.include_router(observability_router, prefix="/observability", tags=["observability"])
api_router.include_router(reports_router, prefix="/reports", tags=["reports"])
api_router.include_router(webhooks_router, prefix="/webhooks", tags=["webhooks"])
api_router.include_router(health_router, prefix="/health", tags=["health"])
