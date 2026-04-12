from dataclasses import dataclass

from app.integrations.facebook import FacebookGraphAPIError, FacebookIntegrationService
from app.models.facebook_comment import FacebookComment
from app.models.facebook_comment_reply import FacebookCommentReply
from app.models.enums import CommentReplyStatus, PlatformType
from app.models.platform_connection import PlatformConnection


@dataclass(slots=True)
class CommentSendResult:
    reply_status: CommentReplyStatus
    external_reply_id: str | None = None
    error_message: str | None = None


class FacebookCommentProviderSender:
    def send(
        self,
        *,
        comment: FacebookComment,
        reply: FacebookCommentReply,
        connection: PlatformConnection | None,
    ) -> CommentSendResult:
        if connection is None:
            return CommentSendResult(
                reply_status=CommentReplyStatus.FAILED,
                error_message="Facebook Page connection is missing for comment reply.",
            )
        service = FacebookIntegrationService(comment._sa_instance_state.session)
        try:
            response = service.client.reply_to_comment(
                page_access_token=service.get_page_access_token(connection),
                comment_id=comment.external_comment_id,
                text=reply.content,
            )
        except FacebookGraphAPIError as exc:
            service.handle_api_error(connection=connection, exc=exc)
            return CommentSendResult(reply_status=CommentReplyStatus.FAILED, error_message=str(exc))
        return CommentSendResult(
            reply_status=CommentReplyStatus.SENT,
            external_reply_id=response.get("id"),
        )


class CommentReplySenderService:
    def __init__(self) -> None:
        self._providers: dict[PlatformType, FacebookCommentProviderSender] = {
            PlatformType.FACEBOOK_PAGE: FacebookCommentProviderSender(),
        }

    def send_comment_reply(
        self,
        *,
        comment: FacebookComment,
        reply: FacebookCommentReply,
        connection: PlatformConnection | None,
    ) -> CommentSendResult:
        provider = self._providers.get(comment.platform_type)
        if provider is None:
            return CommentSendResult(
                reply_status=CommentReplyStatus.FAILED,
                error_message="No comment reply sender registered for platform.",
            )
        return provider.send(comment=comment, reply=reply, connection=connection)
