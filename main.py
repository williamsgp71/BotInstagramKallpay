# main.py
import logging
from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import engine, Base, get_db
from app.webhook.router import router as webhook_router
from app.webhook.service import process_incoming_dm
from app.models import Message

logging.basicConfig(level=logging.INFO)

# Inicializar la base de datos (crear tablas si no existen)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Instagram Chatbot - Especialista Medicina Natural")
app.include_router(webhook_router)

class ChatRequest(BaseModel):
    sender_id: str
    message: str

@app.post("/test-chat")
async def test_chat(payload: ChatRequest, db: Session = Depends(get_db)):
    # Generar un ID de mensaje único ficticio para la prueba
    fake_message_id = f"test_{payload.sender_id}_{len(payload.message)}"
    
    # Ejecutar el procesamiento directamente
    await process_incoming_dm(
        sender_id=payload.sender_id,
        message_id=fake_message_id,
        text=payload.message,
        db=db
    )
    
    # Buscar la respuesta guardada
    last_msg = db.query(Message).filter(
        Message.conversation_id == payload.sender_id,
        Message.sender_type == "bot"
    ).order_by(Message.created_at.desc()).first()
    
    return {"sender_id": payload.sender_id, "reply": last_msg.content if last_msg else "No reply generated"}

@app.get("/")
def read_root():
    return {"status": "running", "bot": "NaturBot"}

