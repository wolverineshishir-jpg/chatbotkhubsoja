from dataclasses import dataclass

from app.integrations.facebook import FacebookGraphAPIError, FacebookIntegrationService
from app.models.platform_connection import PlatformConnection
from app.models.enums import PostStatus, PlatformType
from app.models.social_post import SocialPost


@dataclass(slots=True)
class PublishResult:
    status: PostStatus
    external_post_id: str | None = None
    error_message: str | None = None


class FacebookPostPublisher:
    def publish(self, *, post: SocialPost, connection: PlatformConnection | None) -> PublishResult:
        if connection is None:
            return PublishResult(status=PostStatus.FAILED, error_message="Facebook Page connection is missing for post publishing.")
        service = FacebookIntegrationService(post._sa_instance_state.session)
        metadata = post.metadata_json or {}
        return PublishResult(
            status=PostStatus.PUBLISHED,
            external_post_id=self._publish(post=post, connection=connection, service=service, metadata=metadata),
        )

    @staticmethod
    def _publish(
        *,
        post: SocialPost,
        connection: PlatformConnection,
        service: FacebookIntegrationService,
        metadata: dict,
    ) -> str | None:
        try:
            response = service.client.publish_post(
                page_access_token=service.get_page_access_token(connection),
                page_id=service.page_id(connection),
                message=post.content,
                link=metadata.get("link"),
                published=True,
            )
        except FacebookGraphAPIError as exc:
            service.handle_api_error(connection=connection, exc=exc)
            raise
        return response.get("id")


class SocialPostPublisherService:
    def __init__(self) -> None:
        self._providers: dict[PlatformType, FacebookPostPublisher] = {
            PlatformType.FACEBOOK_PAGE: FacebookPostPublisher(),
        }

    def publish_now(self, *, post: SocialPost, connection: PlatformConnection | None) -> PublishResult:
        provider = self._providers.get(post.platform_type)
        if provider is None:
            return PublishResult(status=PostStatus.FAILED, error_message="No publisher registered for platform.")
        try:
            return provider.publish(post=post, connection=connection)
        except FacebookGraphAPIError as exc:
            return PublishResult(status=PostStatus.FAILED, error_message=str(exc))
