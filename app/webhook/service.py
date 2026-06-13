# app/webhook/service.py
import httpx
import logging
from sqlalchemy.orm import Session
from app.config import get_settings
from app.models import Conversation, Message, WebhookLog
from app.llm.client import get_llm_response
from app.llm.prompts import SYSTEM_PROMPT_NATURAL_MEDICINE
from app.knowledge.retriever import KnowledgeRetriever

logger = logging.getLogger(__name__)
retriever = KnowledgeRetriever()

async def send_meta_dm(recipient_id: str, text: str):
    settings = get_settings()
    url = f"https://graph.facebook.com/v17.0/me/messages?access_token={settings.META_PAGE_ACCESS_TOKEN}"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text}
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        if response.status_code != 200:
            logger.error(f"Error al enviar mensaje a Meta: {response.text}")

async def send_meta_comment_reply(comment_id: str, text: str):
    settings = get_settings()
    url = f"https://graph.facebook.com/v17.0/{comment_id}/replies?access_token={settings.META_PAGE_ACCESS_TOKEN}"
    payload = {"message": text}
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        if response.status_code != 200:
            logger.error(f"Error al responder comentario en Meta: {response.text}")

async def process_incoming_dm(sender_id: str, message_id: str, text: str, db: Session):
    # Verificar duplicidad
    log = db.query(WebhookLog).filter(WebhookLog.id == message_id).first()
    if log:
        return
    
    # Registrar procesado
    new_log = WebhookLog(id=message_id, event_type="message")
    db.add(new_log)
    db.commit()

    # Buscar o crear conversación
    conversation = db.query(Conversation).filter(Conversation.id == sender_id).first()
    if not conversation:
        conversation = Conversation(id=sender_id)
        db.add(conversation)
        db.commit()

    # Guardar mensaje del usuario
    user_msg = Message(conversation_id=sender_id, sender_type="user", content=text)
    db.add(user_msg)
    db.commit()

    # Obtener historial reciente (últimos 10 mensajes)
    history = db.query(Message).filter(Message.conversation_id == sender_id).order_by(Message.created_at.asc()).all()[-10:]

    # RAG Context
    rag_context = await retriever.retrieve_context(text)
    
    # System Prompt con RAG
    system_prompt = SYSTEM_PROMPT_NATURAL_MEDICINE
    if rag_context:
        system_prompt += f"\n\nContexto relevante de soporte:\n{rag_context}"

    try:
        # Llamar LLM
        bot_reply = await get_llm_response(prompt_system=system_prompt, prompt_user=text, history=history[:-1])
    except Exception as e:
        logger.exception("Error llamando al proveedor de LLM.")
        bot_reply = "Lo siento, tengo un inconveniente técnico temporal. Por favor, reintenta en un momento."

    # Enviar a Instagram
    await send_meta_dm(sender_id, bot_reply)

    # Guardar mensaje del bot
    bot_msg = Message(conversation_id=sender_id, sender_type="bot", content=bot_reply)
    db.add(bot_msg)
    db.commit()

async def process_incoming_comment(comment_id: str, text: str, db: Session):
    # Verificar duplicidad
    log = db.query(WebhookLog).filter(WebhookLog.id == comment_id).first()
    if log:
        return

    # Registrar procesado
    new_log = WebhookLog(id=comment_id, event_type="comment")
    db.add(new_log)
    db.commit()

    # Contexto de RAG
    rag_context = await retriever.retrieve_context(text)
    system_prompt = SYSTEM_PROMPT_NATURAL_MEDICINE
    if rag_context:
        system_prompt += f"\n\nContexto de soporte:\n{rag_context}"
    system_prompt += "\nPor favor, responde de forma extremadamente concisa y directa (máximo 2 oraciones), apta para comentarios en redes sociales."

    try:
        bot_reply = await get_llm_response(prompt_system=system_prompt, prompt_user=text)
    except Exception as e:
        logger.exception("Error llamando al proveedor de LLM.")
        bot_reply = "¡Hola! Gracias por comentar. Escríbenos al privado para darte información detallada."

    # Responder en Instagram
    await send_meta_comment_reply(comment_id, bot_reply)
