from dataclasses import dataclass

from app.integrations.facebook import FacebookGraphAPIError, FacebookIntegrationService
from app.integrations.whatsapp import WhatsAppCloudAPIError, WhatsAppIntegrationService
from app.models.conversation import Conversation
from app.models.enums import MessageDeliveryStatus, PlatformType
from app.models.message import Message
from app.models.platform_connection import PlatformConnection


@dataclass(slots=True)
class SendResult:
    delivery_status: MessageDeliveryStatus
    external_message_id: str | None = None
    error_message: str | None = None


class ProviderSender:
    def send(
        self,
        *,
        conversation: Conversation,
        message: Message,
        connection: PlatformConnection | None,
    ) -> SendResult:
        reference = f"{conversation.platform_type.value}-{conversation.id}-{message.id}"
        return SendResult(
            delivery_status=MessageDeliveryStatus.SENT,
            external_message_id=reference,
        )


class FacebookMessengerSender(ProviderSender):
    def send(
        self,
        *,
        conversation: Conversation,
        message: Message,
        connection: PlatformConnection | None,
    ) -> SendResult:
        if connection is None:
            return SendResult(
                delivery_status=MessageDeliveryStatus.FAILED,
                error_message="Facebook Page connection is missing for outbound reply.",
            )
        service = FacebookIntegrationService(conversation._sa_instance_state.session)
        try:
            response = service.client.send_message(
                page_access_token=service.get_page_access_token(connection),
                recipient_id=conversation.customer_external_id,
                text=message.content,
            )
        except FacebookGraphAPIError as exc:
            service.handle_api_error(connection=connection, exc=exc)
            return SendResult(
                delivery_status=MessageDeliveryStatus.FAILED,
                error_message=str(exc),
            )
        return SendResult(
            delivery_status=MessageDeliveryStatus.SENT,
            external_message_id=response.get("message_id"),
        )


class WhatsAppSender(ProviderSender):
    def send(
        self,
        *,
        conversation: Conversation,
        message: Message,
        connection: PlatformConnection | None,
    ) -> SendResult:
        if connection is None:
            return SendResult(
                delivery_status=MessageDeliveryStatus.FAILED,
                error_message="WhatsApp connection is missing for outbound reply.",
            )
        service = WhatsAppIntegrationService(conversation._sa_instance_state.session)
        try:
            response = service.client.send_text_message(
                phone_number_id=service.phone_number_id(connection),
                access_token=service.get_access_token(connection),
                recipient_phone=conversation.customer_external_id,
                text=message.content,
            )
        except WhatsAppCloudAPIError as exc:
            service.handle_api_error(connection=connection, exc=exc)
            return SendResult(
                delivery_status=MessageDeliveryStatus.FAILED,
                error_message=str(exc),
            )

        message_ids = response.get("messages") or []
        external_message_id = None
        if message_ids and isinstance(message_ids, list):
            external_message_id = (message_ids[0] or {}).get("id")
        return SendResult(
            delivery_status=MessageDeliveryStatus.SENT,
            external_message_id=external_message_id,
        )


class MessageSenderService:
    def __init__(self) -> None:
        self._providers: dict[PlatformType, ProviderSender] = {
            PlatformType.FACEBOOK_PAGE: FacebookMessengerSender(),
            PlatformType.WHATSAPP: WhatsAppSender(),
        }

    def send_outbound_message(
        self,
        *,
        conversation: Conversation,
        message: Message,
        connection: PlatformConnection | None,
    ) -> SendResult:
        provider = self._providers.get(conversation.platform_type)
        if provider is None:
            return SendResult(
                delivery_status=MessageDeliveryStatus.FAILED,
                error_message="No outbound sender registered for platform.",
            )
        return provider.send(conversation=conversation, message=message, connection=connection)
