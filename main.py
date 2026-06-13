# main.py
import logging
from fastapi import FastAPI
from app.database import engine, Base
from app.webhook.router import router as webhook_router

logging.basicConfig(level=logging.INFO)

# Inicializar la base de datos (crear tablas si no existen)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Instagram Chatbot - Especialista Medicina Natural")

app.include_router(webhook_router)

@app.get("/")
def read_root():
    return {"status": "running", "bot": "NaturBot"}
