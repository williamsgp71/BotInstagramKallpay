# Plan de Implementación: Chatbot de Instagram (Especialista en Medicina Natural)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Crear un bot en Python/FastAPI con base de datos SQLite y factoría dinámica de LLM compatible con OpenAI/OpenRouter para responder de forma autónoma comentarios y mensajes de Instagram.

**Architecture:** Servidor asíncrono con FastAPI que gestiona webhooks de Meta en segundo plano (`BackgroundTasks`), consulta/almacena conversaciones en SQLite para conservar memoria y utiliza el SDK de OpenAI para realizar llamadas LLM dinámicas basadas en un archivo de configuración YAML.

**Tech Stack:** Python 3.10+, FastAPI, Uvicorn, SQLAlchemy, PyYAML, Pydantic, OpenAI SDK, Pytest.

---

## Estructura del Plan

### Task 1: Configuración Inicial del Entorno y Archivos de Configuración
**Files:**
- Create: `requirements.txt`
- Create: `config.yaml`
- Create: `.env.template`
- Create: `app/__init__.py`
- Create: `app/config.py`
- Test: `tests/test_config.py`

- [ ] **Step 1: Escribir el test fallido para la configuración**
  Crear el archivo `tests/test_config.py` con una prueba para verificar que las configuraciones de variables de entorno y yaml cargan adecuadamente.
  ```python
  # tests/test_config.py
  import os
  import pytest
  from app.config import get_settings

  def test_settings_load():
      os.environ["META_VERIFY_TOKEN"] = "test_token"
      os.environ["OPENROUTER_API_KEY"] = "sk-or-test"
      settings = get_settings()
      assert settings.META_VERIFY_TOKEN == "test_token"
      assert settings.OPENROUTER_API_KEY == "sk-or-test"
  ```
- [ ] **Step 2: Ejecutar el test para comprobar que falla**
  Run: `pytest tests/test_config.py`
  Expected: FAIL con ImportError ya que `app.config` no existe.
- [ ] **Step 3: Crear los archivos de configuración y la implementación mínima**
  Crear `requirements.txt`:
  ```text
  fastapi==0.111.0
  uvicorn==0.30.1
  openai==1.34.0
  pydantic-settings==2.3.3
  pyyaml==6.0.1
  sqlalchemy==2.0.30
  pytest==8.2.2
  pytest-asyncio==0.23.7
  httpx==0.27.0
  ```
  Crear `config.yaml`:
  ```yaml
  active_provider: "openrouter"
  active_model: "meta-llama/llama-3-8b-instruct:free"
  providers:
    openrouter:
      base_url: "https://openrouter.ai/api/v1"
      model: "meta-llama/llama-3-8b-instruct:free"
    deepseek:
      base_url: "https://api.deepseek.com/v1"
      model: "deepseek-chat"
    openai:
      base_url: "https://api.openai.com/v1"
      model: "gpt-4o-mini"
  bot_name: "NaturBot"
  max_history_messages: 10
  temperature: 0.7
  ```
  Crear `.env.template`:
  ```env
  META_VERIFY_TOKEN=verify_token_here
  META_PAGE_ACCESS_TOKEN=access_token_here
  META_APP_SECRET=app_secret_here
  OPENROUTER_API_KEY=key_here
  DEEPSEEK_API_KEY=key_here
  OPENAI_API_KEY=key_here
  ```
  Crear `app/config.py`:
  ```python
  from pydantic_settings import BaseSettings, SettingsConfigDict
  from functools import lru_cache

  class Settings(BaseSettings):
      META_VERIFY_TOKEN: str = "default_token"
      META_PAGE_ACCESS_TOKEN: str = "default_page_token"
      META_APP_SECRET: str = "default_app_secret"
      OPENROUTER_API_KEY: str = "default_or_key"
      DEEPSEEK_API_KEY: str = "default_ds_key"
      OPENAI_API_KEY: str = "default_oa_key"

      model_config = SettingsConfigDict(env_file=".env", extra="ignore")

  @lru_cache()
  def get_settings():
      return Settings()
  ```
- [ ] **Step 4: Ejecutar el test para comprobar que pasa**
  Run: `pytest tests/test_config.py`
  Expected: PASS
- [ ] **Step 5: Commit**
  ```bash
  git add requirements.txt config.yaml .env.template app/config.py tests/test_config.py
  git commit -m "feat: setup initial config and environment settings"
  ```

---

### Task 2: Base de Datos y Modelos
**Files:**
- Create: `app/database.py`
- Create: `app/models.py`
- Test: `tests/test_database.py`

- [ ] **Step 1: Escribir el test fallido para la base de datos**
  Crear el archivo `tests/test_database.py` para verificar la inserción de registros en SQLite.
  ```python
  # tests/test_database.py
  import pytest
  from app.database import Base, engine, get_db
  from app.models import Conversation, Message, WebhookLog
  from sqlalchemy.orm import Session

  @pytest.fixture(name="db_session")
  def fixture_db_session():
      Base.metadata.create_all(bind=engine)
      db = next(get_db())
      try:
          yield db
      finally:
          db.close()
          Base.metadata.drop_all(bind=engine)

  def test_create_and_retrieve_message(db_session: Session):
      conv = Conversation(id="user_123")
      db_session.add(conv)
      db_session.commit()

      msg = Message(conversation_id="user_123", sender_type="user", content="Hola")
      db_session.add(msg)
      db_session.commit()

      retrieved = db_session.query(Message).first()
      assert retrieved.content == "Hola"
      assert retrieved.sender_type == "user"
  ```
- [ ] **Step 2: Ejecutar el test para comprobar que falla**
  Run: `pytest tests/test_database.py`
  Expected: FAIL con ImportError de `app.database`.
- [ ] **Step 3: Crear los archivos e implementar la base de datos y modelos**
  Crear `app/database.py`:
  ```python
  from sqlalchemy import create_engine
  from sqlalchemy.ext.declarative import declarative_base
  from sqlalchemy.orm import sessionmaker

  SQLALCHEMY_DATABASE_URL = "sqlite:///./instagram_bot.db"

  engine = create_engine(
      SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
  )
  SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

  Base = declarative_base()

  def get_db():
      db = SessionLocal()
      try:
          yield db
      finally:
          db.close()
  ```
  Crear `app/models.py`:
  ```python
  from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
  from sqlalchemy.orm import relationship
  from datetime import datetime
  from app.database import Base

  class WebhookLog(Base):
      __tablename__ = "webhook_logs"
      id = Column(String, primary_key=True, index=True)
      event_type = Column(String, nullable=False)
      processed_at = Column(DateTime, default=datetime.utcnow)

  class Conversation(Base):
      __tablename__ = "conversations"
      id = Column(String, primary_key=True, index=True) # Instagram Scoped User ID (IGID)
      created_at = Column(DateTime, default=datetime.utcnow)
      updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
      messages = relationship("Message", back_populates="conversation")

  class Message(Base):
      __tablename__ = "messages"
      id = Column(Integer, primary_key=True, index=True, autoincrement=True)
      conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
      sender_type = Column(String, nullable=False) # 'user' o 'bot'
      content = Column(String, nullable=False)
      created_at = Column(DateTime, default=datetime.utcnow)
      
      conversation = relationship("Conversation", back_populates="messages")
  ```
- [ ] **Step 4: Ejecutar el test para comprobar que pasa**
  Run: `pytest tests/test_database.py`
  Expected: PASS
- [ ] **Step 5: Commit**
  ```bash
  git add app/database.py app/models.py tests/test_database.py
  git commit -m "feat: implement database connection and models for chat history and webhook logs"
  ```

---

### Task 3: Módulo Bridge de RAG (Lectura de Markdown)
**Files:**
- Create: `app/knowledge/retriever.py`
- Test: `tests/test_retriever.py`

- [ ] **Step 1: Escribir el test fallido para el Retriever**
  Crear el archivo `tests/test_retriever.py` para verificar que el retriever responde con una cadena vacía en esta versión básica pero inicializa de manera correcta.
  ```python
  # tests/test_retriever.py
  import pytest
  from app.knowledge.retriever import KnowledgeRetriever

  @pytest.mark.asyncio
  async def test_knowledge_retriever_empty():
      retriever = KnowledgeRetriever()
      context = await retriever.retrieve_context("consulta de manzanilla")
      assert context == ""
  ```
- [ ] **Step 2: Ejecutar el test para comprobar que falla**
  Run: `pytest tests/test_retriever.py`
  Expected: FAIL con ImportError.
- [ ] **Step 3: Crear el módulo e implementar retriever básico**
  Crear `app/knowledge/__init__.py` y `app/knowledge/retriever.py`:
  ```python
  # app/knowledge/retriever.py
  class KnowledgeRetriever:
      def __init__(self, docs_directory: str = "./knowledge_base"):
          self.docs_directory = docs_directory

      async def retrieve_context(self, query: str) -> str:
          # Fase 1: Retorna vacío. En Fase 2 (RAG) se implementará la búsqueda en Markdowns.
          return ""
  ```
- [ ] **Step 4: Ejecutar el test para comprobar que pasa**
  Run: `pytest tests/test_retriever.py`
  Expected: PASS
- [ ] **Step 5: Commit**
  ```bash
  git add app/knowledge/retriever.py tests/test_retriever.py
  git commit -m "feat: add knowledge retriever interface skeleton for future RAG"
  ```

---

### Task 4: Factoría del Cliente LLM Asíncrono Dinámico
**Files:**
- Create: `app/llm/__init__.py`
- Create: `app/llm/client.py`
- Create: `app/llm/prompts.py`
- Test: `tests/test_llm_client.py`

- [ ] **Step 1: Escribir el test para el LLM Client (usando Mocks)**
  Crear el archivo `tests/test_llm_client.py` que valide el cargado de la factoría y mockee la llamada a la API de OpenAI compatible.
  ```python
  # tests/test_llm_client.py
  import pytest
  from unittest.mock import AsyncMock, patch
  from app.llm.client import get_llm_response

  @pytest.mark.asyncio
  @patch("app.llm.client.AsyncOpenAI")
  async def test_get_llm_response(mock_openai):
      # Configurar mock de respuesta
      mock_client = AsyncMock()
      mock_openai.return_value = mock_client
      
      mock_response = AsyncMock()
      mock_response.choices = [
          AsyncMock(message=AsyncMock(content="Respuesta simulada"))
      ]
      mock_client.chat.completions.create.return_value = mock_response

      response = await get_llm_response(
          prompt_system="Eres un experto",
          prompt_user="Hola",
          history=[]
      )
      assert response == "Respuesta simulada"
  ```
- [ ] **Step 2: Ejecutar el test para comprobar que falla**
  Run: `pytest tests/test_llm_client.py`
  Expected: FAIL con ImportError.
- [ ] **Step 3: Crear los archivos e implementar el cliente y prompts**
  Crear `app/llm/prompts.py`:
  ```python
  # app/llm/prompts.py
  SYSTEM_PROMPT_NATURAL_MEDICINE = (
      "Eres un especialista calificado en medicina natural y un experto en suplementos naturales. "
      "Respondes a las consultas de los usuarios con un tono empático, informativo, respetuoso y profesional. "
      "Utilizas tu conocimiento para explicar los beneficios y usos tradicionales de plantas medicinales, "
      "suplementos alimenticios, vitaminas y terapias naturales. "
      "Siempre enfatizas que tus recomendaciones no reemplazan la opinión de un profesional de la salud calificado "
      "y que el usuario debe consultar a su médico antes de iniciar cualquier tratamiento nuevo."
  )
  ```
  Crear `app/llm/client.py`:
  ```python
  # app/llm/client.py
  import yaml
  from openai import AsyncOpenAI
  from app.config import get_settings

  def load_yaml_config():
      with open("config.yaml", "r", encoding="utf-8") as f:
          return yaml.safe_load(f)

  async def get_llm_response(prompt_system: str, prompt_user: str, history: list = None) -> str:
      config = load_yaml_config()
      settings = get_settings()
      provider_name = config.get("active_provider", "openrouter")
      
      # Resolver endpoint y API Key
      if provider_name == "openrouter":
          base_url = config["providers"]["openrouter"]["base_url"]
          api_key = settings.OPENROUTER_API_KEY
          model = config.get("active_model") or config["providers"]["openrouter"]["model"]
      elif provider_name == "deepseek":
          base_url = config["providers"]["deepseek"]["base_url"]
          api_key = settings.DEEPSEEK_API_KEY
          model = config["providers"]["deepseek"]["model"]
      elif provider_name == "openai":
          base_url = config["providers"]["openai"]["base_url"]
          api_key = settings.OPENAI_API_KEY
          model = config["providers"]["openai"]["model"]
      else:
          raise ValueError(f"Proveedor no soportado: {provider_name}")
      
      client = AsyncOpenAI(api_key=api_key, base_url=base_url)
      
      messages = [{"role": "system", "content": prompt_system}]
      if history:
          for msg in history:
              role = "user" if msg.sender_type == "user" else "assistant"
              messages.append({"role": role, "content": msg.content})
      
      messages.append({"role": "user", "content": prompt_user})
      
      response = await client.chat.completions.create(
          model=model,
          messages=messages,
          temperature=config.get("temperature", 0.7)
      )
      return response.choices[0].message.content
  ```
- [ ] **Step 4: Ejecutar el test para comprobar que pasa**
  Run: `pytest tests/test_llm_client.py`
  Expected: PASS
- [ ] **Step 5: Commit**
  ```bash
  git add app/llm/prompts.py app/llm/client.py tests/test_llm_client.py
  git commit -m "feat: implement dynamic openai-compatible LLM client and system prompt"
  ```

---

### Task 5: Procesamiento de Webhooks y Lógica de Negocio
**Files:**
- Create: `app/webhook/service.py`
- Test: `tests/test_webhook_service.py`

- [ ] **Step 1: Escribir el test para el servicio de webhooks (usando Mocks)**
  Crear `tests/test_webhook_service.py` para validar la lógica del servicio y mocks de las APIs externas (Meta y LLM).
  ```python
  # tests/test_webhook_service.py
  import pytest
  from unittest.mock import AsyncMock, patch, MagicMock
  from app.webhook.service import process_incoming_dm, process_incoming_comment
  from app.database import Base, engine
  from sqlalchemy.orm import Session

  @pytest.fixture(name="db_session")
  def fixture_db_session():
      Base.metadata.create_all(bind=engine)
      db = Session(bind=engine)
      try:
          yield db
      finally:
          db.close()
          Base.metadata.drop_all(bind=engine)

  @pytest.mark.asyncio
  @patch("app.webhook.service.get_llm_response", new_callable=AsyncMock)
  @patch("app.webhook.service.send_meta_dm", new_callable=AsyncMock)
  async def test_process_incoming_dm(mock_send_dm, mock_llm_response, db_session):
      mock_llm_response.return_value = "Respuesta bot"
      
      await process_incoming_dm(
          sender_id="user_test",
          message_id="msg_123",
          text="¿Manzanilla?",
          db=db_session
      )
      
      mock_send_dm.assert_called_once_with("user_test", "Respuesta bot")
      mock_llm_response.assert_called_once()
  ```
- [ ] **Step 2: Ejecutar el test para comprobar que falla**
  Run: `pytest tests/test_webhook_service.py`
  Expected: FAIL con ImportError.
- [ ] **Step 3: Crear los archivos e implementar la lógica de negocio y las llamadas HTTP a Meta**
  Crear `app/webhook/__init__.py` y `app/webhook/service.py`:
  ```python
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
  ```
- [ ] **Step 4: Ejecutar el test para comprobar que pasa**
  Run: `pytest tests/test_webhook_service.py`
  Expected: PASS
- [ ] **Step 5: Commit**
  ```bash
  git add app/webhook/service.py tests/test_webhook_service.py
  git commit -m "feat: implement message and comment routing, deduplication, and sending to Meta API"
  ```

---

### Task 6: Rutas Webhook y Entrada de la Aplicación (FastAPI)
**Files:**
- Create: `app/webhook/router.py`
- Create: `main.py`
- Test: `tests/test_router.py`

- [ ] **Step 1: Escribir el test de los endpoints de Webhooks**
  Crear `tests/test_router.py` para simular llamadas GET y POST al webhook usando `httpx` de pruebas en FastAPI.
  ```python
  # tests/test_router.py
  import pytest
  from fastapi.testclient import TestClient
  from main import app
  from app.config import get_settings

  client = TestClient(app)

  def test_verify_webhook_success():
      settings = get_settings()
      settings.META_VERIFY_TOKEN = "token_de_prueba"
      
      response = client.get("/webhook?hub.mode=subscribe&hub.verify_token=token_de_prueba&hub.challenge=123456")
      assert response.status_code == 200
      assert response.text == "123456"

  def test_verify_webhook_fail():
      response = client.get("/webhook?hub.mode=subscribe&hub.verify_token=invalid_token&hub.challenge=123456")
      assert response.status_code == 403
  ```
- [ ] **Step 2: Ejecutar el test para comprobar que falla**
  Run: `pytest tests/test_router.py`
  Expected: FAIL con ImportError.
- [ ] **Step 3: Crear los archivos e implementar el router y main**
  Crear `app/webhook/router.py`:
  ```python
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
  ```
  Crear `main.py`:
  ```python
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
  ```
- [ ] **Step 4: Ejecutar el test para comprobar que pasa**
  Run: `pytest tests/test_router.py`
  Expected: PASS
- [ ] **Step 5: Commit**
  ```bash
  git add app/webhook/router.py main.py tests/test_router.py
  git commit -m "feat: setup FastAPI routes and entrypoint for receiving webhooks"
  ```

---

### Task 7: Endpoint de Prueba Local y Verificación Final
**Files:**
- Modify: `main.py`
- Test: `tests/test_local_chat.py`

- [ ] **Step 1: Escribir el test fallido para el chat de prueba local**
  Crear `tests/test_local_chat.py` para probar el endpoint manual `/test-chat` con un usuario de pruebas.
  ```python
  # tests/test_local_chat.py
  import pytest
  from fastapi.testclient import TestClient
  from main import app
  from unittest.mock import patch, AsyncMock

  client = TestClient(app)

  @pytest.mark.asyncio
  @patch("app.webhook.service.get_llm_response", new_callable=AsyncMock)
  async def test_local_chat_endpoint(mock_llm_response):
      mock_llm_response.return_value = "Hola desde el bot de prueba"
      
      response = client.post("/test-chat", json={"sender_id": "test_local_user", "message": "recomiéndame algo para dormir"})
      assert response.status_code == 200
      data = response.json()
      assert data["reply"] == "Hola desde el bot de prueba"
  ```
- [ ] **Step 2: Ejecutar el test para comprobar que falla**
  Run: `pytest tests/test_local_chat.py`
  Expected: FAIL con HTTP 404 (endpoint `/test-chat` no implementado).
- [ ] **Step 3: Añadir el endpoint de prueba en `main.py`**
  Modificar `main.py` para incorporar el endpoint `/test-chat`:
  ```python
  # main.py (Modificar para agregar el endpoint de prueba)
  import logging
  from fastapi import FastAPI, Depends
  from pydantic import BaseModel
  from sqlalchemy.orm import Session
  from app.database import engine, Base, get_db
  from app.webhook.router import router as webhook_router
  from app.webhook.service import process_incoming_dm
  from app.models import Message

  logging.basicConfig(level=logging.INFO)

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
  ```
- [ ] **Step 4: Ejecutar el test para comprobar que pasa**
  Run: `pytest tests/test_local_chat.py`
  Expected: PASS
- [ ] **Step 5: Ejecutar la suite completa de pruebas**
  Run: `pytest`
  Expected: Todos los tests pasan con éxito.
- [ ] **Step 6: Commit**
  ```bash
  git add main.py tests/test_local_chat.py
  git commit -m "feat: implement test-chat endpoint for local validation and verification"
  ```
