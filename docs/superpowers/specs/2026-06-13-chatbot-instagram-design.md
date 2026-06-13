# Especificación de Diseño: Chatbot de Instagram (Especialista en Medicina Natural)

**Fecha:** 2026-06-13  
**Estado:** Propuesto  
**Autor:** Antigravity (AI Coding Assistant)  

---

## 1. Introducción y Objetivos
Este proyecto consiste en un backend automatizado para responder comentarios y mensajes privados (DMs) en Instagram de manera automatizada. 

El bot debe encarnar la personalidad de un **especialista en medicina natural y experto en suplementos naturales**, ofreciendo respuestas útiles, informadas y seguras.

### Objetivos Clave:
* **Integración Oficial:** Uso de la API Oficial de Instagram Graph mediante webhooks seguros.
* **Cliente LLM Dinámico:** Utilizar el SDK oficial de OpenAI configurado dinámicamente para alternar de forma transparente entre **OpenRouter** (con el modelo que decida el usuario) y **DeepSeek** u otros proveedores compatibles.
* **Persistencia y Memoria:** Mantener el contexto de conversaciones anteriores con cada usuario en una base de datos SQLite local.
* **Estructura RAG-Ready:** Diseñar e implementar las interfaces y flujos preparados para que, en una fase posterior, se pueda habilitar un sistema RAG (Retrieval-Augmented Generation) basado en archivos Markdown locales.

---

## 2. Pila Tecnológica (Tech Stack)
* **Lenguaje:** Python 3.10+
* **Framework Web:** FastAPI (Asíncrono, de alto rendimiento, autogeneración de documentación OpenAPI/Swagger).
* **Servidor ASGI:** Uvicorn
* **Base de Datos:** SQLite (ligero, embebido) con **SQLAlchemy** como ORM para la persistencia.
* **SDK de IA:** SDK oficial de `openai` para Python (aprovechando la compatibilidad de API de OpenRouter y DeepSeek).
* **Gestión de Configuración:** `pyyaml` (para configuración estructurada de modelos) y `pydantic-settings` (para variables de entorno seguras).

---

## 3. Estructura de Directorios del Proyecto
```text
chatbot_instagram/
├── config.yaml          # Configuración de modelos activos, promts y comportamiento
├── .env                 # API keys y tokens confidenciales (no se sube al control de versiones)
├── main.py              # Punto de entrada y configuración de la app de FastAPI
├── requirements.txt     # Dependencias del proyecto
├── docs/
│   └── superpowers/
│       └── specs/
│           └── 2026-06-13-chatbot-instagram-design.md # Este documento de diseño
└── app/
    ├── __init__.py
    ├── config.py        # Validador de variables de entorno y ajustes
    ├── database.py      # Sesión y motor de base de datos SQLite
    ├── models.py        # Tablas ORM (Conversations, Messages, WebhookLogs)
    ├── webhook/
    │   ├── __init__.py
    │   ├── router.py    # Endpoints de webhook (verificación y recepción de eventos)
    │   └── service.py   # Procesador de lógica de negocio (Comentarios vs DMs)
    ├── llm/
    │   ├── __init__.py
    │   ├── client.py    # Factoría para el cliente de OpenAI compatible
    │   └── prompts.py   # Prompts de sistema y personalidades del bot
    └── knowledge/
        ├── __init__.py
        └── retriever.py # Interfaz puente para el futuro RAG
```

---

## 4. Diseño del Flujo de Datos

### 4.1. Recepción y Validación del Webhook
1. **Verificación de Firma:** Meta envía un header `X-Hub-Signature-256` para verificar que la petición proviene de Meta. El bot validará esta firma usando la `APP_SECRET` de Meta.
2. **Respuesta Rápida (HTTP 200):** FastAPI recibirá la carga útil de Meta, validará que el evento sea válido, responderá HTTP 200 inmediatamente a Meta, e iniciará una `BackgroundTask` para procesar el mensaje en segundo plano.
3. **Control de Duplicidad:** Antes de procesar cualquier evento, se comprobará en la base de datos si el ID del mensaje o comentario ya existe en la tabla `WebhookLog`. Si ya existe, se ignora.

### 4.2. Procesamiento de Mensajes Directos (DMs)
1. Se extrae el `sender_id` (Instagram Scoped User ID) y el texto.
2. Se consultan los últimos 10 mensajes correspondientes a esa conversación en SQLite para mantener el contexto.
3. Se invoca a la interfaz RAG (actualmente vacía, retorna texto vacío).
4. Se arma el prompt de sistema combinando la personalidad del bot y el contexto.
5. Se envía la consulta al LLM configurado a través del cliente dinámico.
6. Se envía la respuesta del LLM a Instagram usando la API de Meta (`/me/messages`).
7. Se guarda el mensaje del usuario y la respuesta del bot en SQLite.

### 4.3. Procesamiento de Comentarios
1. Se extrae el `comment_id`, `media_id` y el texto del comentario.
2. Se genera la respuesta usando el LLM con un prompt enfocado en comentarios (respuestas más directas y concisas).
3. Se envía la respuesta usando la API de Meta (`/{comment_id}/replies`).
4. Se registra el comentario como procesado.

---

## 5. Modelo de Datos (Esquema SQLite)

El esquema de base de datos tendrá tres tablas principales:

```sql
-- Tabla para registrar eventos procesados y evitar duplicados por reintentos de Meta
CREATE TABLE webhook_logs (
    id TEXT PRIMARY KEY,          -- message_id o comment_id recibido
    event_type TEXT NOT NULL,     -- 'message' o 'comment'
    processed_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tabla para agrupar chats privados por usuario
CREATE TABLE conversations (
    id TEXT PRIMARY KEY,          -- Instagram Sender ID (IGID)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tabla para guardar el historial de mensajes (Memoria del chat)
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT NOT NULL,
    sender_type TEXT NOT NULL,    -- 'user' o 'bot'
    content TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(conversation_id) REFERENCES conversations(id)
);
```

---

## 6. Configuración e Integración Dinámica del LLM

### 6.1. Variables de Entorno (`.env`)
```bash
# Meta / Instagram Config
META_VERIFY_TOKEN="tu_token_de_verificacion_para_webhook"
META_PAGE_ACCESS_TOKEN="tu_page_access_token_de_facebook"
META_APP_SECRET="tu_app_secret_para_firma"

# LLM Providers Keys
OPENROUTER_API_KEY="sk-or-..."
DEEPSEEK_API_KEY="sk-..."
OPENAI_API_KEY="sk-..."
```

### 6.2. Configuración Estructurada del Bot (`config.yaml`)
```yaml
# Configuración de ejecución del LLM
active_provider: "openrouter" # "openrouter" | "deepseek" | "openai"
active_model: "meta-llama/llama-3-8b-instruct:free"

# Opciones por proveedor
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

# Ajustes de personalidad
bot_name: "NaturBot"
max_history_messages: 10
temperature: 0.7
```

### 6.3. Factoría de Cliente en `app/llm/client.py`
El módulo instanciará un cliente asíncrono configurado al vuelo según el proveedor seleccionado:

```python
from openai import AsyncOpenAI
from app.config import settings
import yaml

def load_yaml_config():
    with open("config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

async def get_llm_response(prompt_system: str, prompt_user: str, history: list = None) -> str:
    config = load_yaml_config()
    provider_name = config.get("active_provider", "openrouter")
    
    # Resolver credenciales y URLs
    if provider_name == "openrouter":
        base_url = config["providers"]["openrouter"]["base_url"]
        api_key = settings.OPENROUTER_API_KEY
        model = config["active_model"] or config["providers"]["openrouter"]["model"]
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
    
    # Crear cliente compatible
    client = AsyncOpenAI(api_key=api_key, base_url=base_url)
    
    # Preparar mensajes
    messages = [{"role": "system", "content": prompt_system}]
    if history:
        for msg in history:
            messages.append({"role": "user" if msg.sender_type == "user" else "assistant", "content": msg.content})
    messages.append({"role": "user", "content": prompt_user})
    
    # Llamada al API
    response = await client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=config.get("temperature", 0.7)
    )
    return response.choices[0].message.content
```

---

## 7. Preparación para RAG (Módulo de Conocimiento)
Para permitir mejoras futuras sin modificar el núcleo de procesamiento de mensajes, el archivo `app/knowledge/retriever.py` se estructurará de la siguiente forma:

```python
class KnowledgeRetriever:
    """
    Componente encargado de recuperar información de archivos Markdown locales.
    Fase 1: Retorna cadena vacía (bypass de RAG).
    Fase 2 (Futura): Carga documentos markdown, genera embeddings, los almacena 
            en una base vectorial ligera y realiza búsquedas de similitud.
    """
    def __init__(self, docs_directory: str = "./knowledge_base"):
        self.docs_directory = docs_directory

    async def retrieve_context(self, query: str) -> str:
        # En la Fase 1, no hace nada y retorna un string vacío
        return ""
```

---

## 8. Gestión de Errores e Inconvenientes Técnicos
* **Timeouts de API:** Si OpenRouter o DeepSeek experimentan latencias altas, se configurará un timeout de 15 segundos en el cliente OpenAI. Si se agota el tiempo, se reintentará una vez. Si falla de nuevo, se devolverá un mensaje genérico.
* **Fallas del Webhook:** Si el API de Instagram devuelve un código de error al enviar la respuesta, el error se registrará detalladamente en la consola y un archivo de logs rotativo para depuración sin interrumpir el servidor FastAPI.

---

## 9. Pruebas y Depuración Local
* **Endpoint de prueba manual `/test-chat`:**
  Permitirá enviar un JSON con `message` y `sender_id` a través de la interfaz interactiva de Swagger `/docs` de FastAPI para probar la respuesta del bot y la persistencia del historial en SQLite sin tener que interactuar con la API oficial de Instagram.
* **Pruebas Automatizadas:** 
  Uso de `pytest` y `pytest-asyncio` con mocks para probar la factoría de LLM y el flujo de los endpoints de webhook.
