# app/webhook/service.py
import httpx
import logging
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.config import get_settings
from app.models import Conversation, Message, WebhookLog
from app.llm.client import get_llm_response, load_yaml_config
from app.llm.prompts import SYSTEM_PROMPT_NATURAL_MEDICINE
from app.knowledge.retriever import KnowledgeRetriever

logger = logging.getLogger(__name__)
retriever = KnowledgeRetriever()

META_GRAPH_BASE_URL = "https://graph.facebook.com/v17.0"
_http_client = httpx.AsyncClient()

async def _post_to_meta(path: str, payload: dict, error_context: str) -> None:
    settings = get_settings()
    url = f"{META_GRAPH_BASE_URL}/{path}?access_token={settings.META_PAGE_ACCESS_TOKEN}"
    response = await _http_client.post(url, json=payload)
    if response.status_code != 200:
        logger.error(f"{error_context}: {response.text}")

async def send_meta_dm(recipient_id: str, text: str):
    await _post_to_meta(
        "me/messages",
        {"recipient": {"id": recipient_id}, "message": {"text": text}},
        "Error al enviar mensaje a Meta",
    )

async def send_meta_comment_reply(comment_id: str, text: str):
    await _post_to_meta(
        f"{comment_id}/replies",
        {"message": text},
        "Error al responder comentario en Meta",
    )

async def process_incoming_dm(sender_id: str, message_id: str, text: str, db: Session):
    # Verificar duplicidad
    log = db.query(WebhookLog).filter(WebhookLog.id == message_id).first()
    if log:
        return

    # Registrar procesado
    new_log = WebhookLog(id=message_id, event_type="message")
    db.add(new_log)
    try:
        db.commit()
    except IntegrityError:
        # Entrega duplicada concurrente del mismo webhook: ya fue registrado por la otra tarea.
        db.rollback()
        return

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

    # Obtener historial reciente (últimos N mensajes, según config.yaml)
    max_history = load_yaml_config().get("max_history_messages", 10)
    history = (
        db.query(Message)
        .filter(Message.conversation_id == sender_id)
        .order_by(Message.created_at.desc())
        .limit(max_history)
        .all()
    )
    history.reverse()

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
    try:
        db.commit()
    except IntegrityError:
        # Entrega duplicada concurrente del mismo webhook: ya fue registrado por la otra tarea.
        db.rollback()
        return

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
