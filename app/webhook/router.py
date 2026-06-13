# app/webhook/router.py
import hashlib
import hmac
import logging
from fastapi import APIRouter, Request, HTTPException, Depends, BackgroundTasks
from fastapi.responses import Response, PlainTextResponse
from sqlalchemy.orm import Session
from app.config import get_settings
from app.database import get_db
from app.webhook.service import process_incoming_dm, process_incoming_comment

logger = logging.getLogger(__name__)
router = APIRouter()

# GET para la verificación de webhooks de Meta
@router.get("/webhook", response_class=PlainTextResponse)
async def verify_webhook(request: Request):
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")
    
    settings = get_settings()
    if mode == "subscribe" and token == settings.META_VERIFY_TOKEN:
        logger.info("Webhook verificado exitosamente.")
        return challenge
    else:
        logger.warning("Fallo en la verificación del Webhook.")
        raise HTTPException(status_code=403, detail="Verification token mismatch")

# POST para recibir eventos de Instagram
@router.post("/webhook")
async def receive_webhook(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    body = await request.body()
    settings = get_settings()
    
    # Validar firma de Meta si está presente (seguridad adicional)
    signature = request.headers.get("X-Hub-Signature-256")
    if signature and settings.META_APP_SECRET != "default_app_secret":
        sha256_sig = signature.replace("sha256=", "")
        expected_sig = hmac.new(
            settings.META_APP_SECRET.encode("utf-8"),
            body,
            hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(sha256_sig, expected_sig):
            logger.error("Firma de webhook inválida.")
            raise HTTPException(status_code=403, detail="Invalid signature")

    data = await request.json()
    
    # Validar que sea un evento de instagram
    if data.get("object") == "instagram":
        for entry in data.get("entry", []):
            # Mensajes Privados (DMs)
            if "messaging" in entry:
                for messaging_event in entry["messaging"]:
                    sender_id = messaging_event["sender"]["id"]
                    message_id = messaging_event["message"]["mid"]
                    text = messaging_event["message"].get("text")
                    if text:
                        background_tasks.add_task(
                            process_incoming_dm, sender_id, message_id, text, db
                        )
            
            # Comentarios en Posts
            elif "changes" in entry:
                for change in entry["changes"]:
                    if change.get("field") == "comments":
                        value = change.get("value", {})
                        comment_id = value.get("id")
                        text = value.get("text")
                        if comment_id and text:
                            background_tasks.add_task(
                                process_incoming_comment, comment_id, text, db
                            )
                            
    return Response(content="EVENT_RECEIVED", status_code=200)
