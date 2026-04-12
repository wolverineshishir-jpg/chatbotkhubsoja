from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.integrations.facebook import FacebookIntegrationService
from app.integrations.whatsapp import WhatsAppIntegrationService
from app.models.enums import PlatformType, WebhookEventSource
from app.schemas.webhooks import WebhookAckResponse
from app.services.webhook_ingestion_service import WebhookIngestionService
from app.workers.webhook_tasks import process_webhook_event

router = APIRouter()


@router.get("/facebook-page", summary="Verify Facebook Page webhook")
async def verify_facebook_page_webhook(
    hub_mode: str | None = Query(default=None, alias="hub.mode"),
    hub_challenge: str | None = Query(default=None, alias="hub.challenge"),
    hub_verify_token: str | None = Query(default=None, alias="hub.verify_token"),
    db: Session = Depends(get_db),
) -> Response:
    verified = WebhookIngestionService(db).verify_webhook(
        platform_type=PlatformType.FACEBOOK_PAGE,
        mode=hub_mode,
        token=hub_verify_token,
    )
    if not verified:
        return Response(status_code=status.HTTP_403_FORBIDDEN)
    return Response(content=hub_challenge or "", media_type="text/plain")


@router.post("/facebook-page", response_model=WebhookAckResponse, status_code=status.HTTP_202_ACCEPTED, summary="Receive Facebook Page webhook")
async def receive_facebook_page_webhook(request: Request, db: Session = Depends(get_db)) -> WebhookAckResponse:
    raw_body = await request.body()
    signature_header = request.headers.get("x-hub-signature-256")
    app_secret = get_settings().facebook_app_secret.get_secret_value()
    if app_secret and not FacebookIntegrationService(db).verify_signature(raw_body=raw_body, signature_header=signature_header):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Facebook webhook signature.")
    try:
        payload = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON payload.") from exc
    event, created = WebhookIngestionService(db).ingest_event(
        source=WebhookEventSource.FACEBOOK_PAGE,
        platform_type=PlatformType.FACEBOOK_PAGE,
        payload=payload,
        headers=dict(request.headers),
    )
    if created:
        try:
            process_webhook_event.delay(event.id)
        except Exception:
            pass
    return WebhookAckResponse(event_id=event.id, status=event.status, queued=created)


@router.get("/whatsapp", summary="Verify WhatsApp webhook")
async def verify_whatsapp_webhook(
    hub_mode: str | None = Query(default=None, alias="hub.mode"),
    hub_challenge: str | None = Query(default=None, alias="hub.challenge"),
    hub_verify_token: str | None = Query(default=None, alias="hub.verify_token"),
    db: Session = Depends(get_db),
) -> Response:
    verified = WebhookIngestionService(db).verify_webhook(
        platform_type=PlatformType.WHATSAPP,
        mode=hub_mode,
        token=hub_verify_token,
    )
    if not verified:
        return Response(status_code=status.HTTP_403_FORBIDDEN)
    return Response(content=hub_challenge or "", media_type="text/plain")


@router.post("/whatsapp", response_model=WebhookAckResponse, status_code=status.HTTP_202_ACCEPTED, summary="Receive WhatsApp webhook")
async def receive_whatsapp_webhook(request: Request, db: Session = Depends(get_db)) -> WebhookAckResponse:
    raw_body = await request.body()
    signature_header = request.headers.get("x-hub-signature-256")
    app_secret = get_settings().facebook_app_secret.get_secret_value()
    if app_secret and not WhatsAppIntegrationService(db).verify_signature(raw_body=raw_body, signature_header=signature_header):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid WhatsApp webhook signature.")
    try:
        payload = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON payload.") from exc
    event, created = WebhookIngestionService(db).ingest_event(
        source=WebhookEventSource.WHATSAPP,
        platform_type=PlatformType.WHATSAPP,
        payload=payload,
        headers=dict(request.headers),
    )
    if created:
        try:
            process_webhook_event.delay(event.id)
        except Exception:
            pass
    return WebhookAckResponse(event_id=event.id, status=event.status, queued=created)
