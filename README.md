# Instagram Chatbot - Especialista en Medicina Natural

Este es un bot en Python/FastAPI diseñado para responder de forma automática a comentarios y mensajes directos (DMs) en Instagram, adoptando la personalidad de un especialista calificado en medicina natural y experto en suplementos. 

El sistema utiliza una factoría dinámica de LLM que permite alternar fácilmente entre **OpenRouter**, **DeepSeek** y **OpenAI** (o cualquier proveedor compatible con la API de OpenAI), guarda el historial de chats en una base de datos local SQLite para mantener memoria contextual y está preparado para futuras integraciones de RAG (búsqueda sobre archivos Markdown locales).

---

## Requisitos Previos

Asegúrate de tener instalado en tu sistema:
* **Python 3.10** o superior (Probado en Python 3.11)
* **Git**
* **Ngrok** (para pruebas de webhooks oficiales de Meta de forma local)

---

## 🛠️ Configuración e Instalación Paso a Paso

### 1. Clonar e Inicializar el Entorno

Abre tu terminal en el directorio del proyecto y ejecuta:

```bash
# Crear un entorno virtual de Python
python -m venv .env

# Activar el entorno virtual
# En Windows (PowerShell):
.env\Scripts\Activate.ps1
# En macOS/Linux:
source .env/bin/activate

# Instalar las dependencias requeridas
pip install -r requirements.txt
```

### 2. Configurar las Variables de Entorno

Copia el archivo de plantilla `.env.template` y renómbralo a `.env`:

```bash
cp .env.template .env
```

Abre el archivo `.env` y rellena las claves correspondientes:

```env
# Configuración del Webhook de Meta / Instagram
META_VERIFY_TOKEN="tu_token_de_verificacion_personalizado"
META_PAGE_ACCESS_TOKEN="tu_token_de_acceso_de_pagina_facebook"
META_APP_SECRET="tu_secreto_de_aplicacion_meta"

# Claves de APIs de Proveedores de LLM
OPENROUTER_API_KEY="tu_clave_de_openrouter"
DEEPSEEK_API_KEY="tu_clave_de_deepseek"
OPENAI_API_KEY="tu_clave_de_openai"
```

### 3. Configurar el Comportamiento del Bot (`config.yaml`)

El archivo `config.yaml` controla qué proveedor de Inteligencia Artificial se utiliza y la configuración del modelo de forma dinámica:

```yaml
active_provider: "openrouter" # Opciones: "openrouter" | "deepseek" | "openai"
active_model: "meta-llama/llama-3-8b-instruct:free" # Deja vacío para usar el modelo por defecto del proveedor

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

---

## 🚀 Ejecución del Servidor

Para levantar la aplicación FastAPI de forma local:

```bash
uvicorn main:app --reload
```

El servidor estará corriendo en: `http://127.0.0.1:8000`

---

## 🧪 Pruebas Locales (Sin depender de Meta)

FastAPI autogenera documentación Swagger interactiva que te permite validar el bot localmente.

1. Abre tu navegador y ve a: **`http://127.0.0.1:8000/docs`**
2. Despliega el endpoint **`POST /test-chat`**.
3. Haz clic en "Try it out".
4. Ingresa un JSON de prueba:
   ```json
   {
     "sender_id": "usuario_de_prueba",
     "message": "Hola, ¿qué me recomiendas para el insomnio y el cansancio?"
   }
   ```
5. Presiona "Execute" y verás la respuesta generada por el bot con su respectiva personalidad.
6. La conversación se almacenará automáticamente en la base de datos SQLite local (`instagram_bot.db`).

---

## 🌐 Configuración e Integración con Meta (Instagram Oficial)

Para que Instagram pueda enviar los mensajes de los usuarios a tu servidor local:

### 1. Crear Túnel HTTPS con Ngrok
Meta requiere obligatoriamente una dirección HTTPS pública para configurar el webhook.
```bash
ngrok http 8000
```
Copia la URL HTTPS generada (ej. `https://xxxx-xx.ngrok-free.app`).

### 2. Configurar Webhooks en Meta Developers Portal
1. Ve a tu App en el panel de **Meta Developers**.
2. Agrega el producto **Webhooks** y selecciona **Instagram**.
3. En **Callback URL**, pega la URL de Ngrok terminada en `/webhook` (ej. `https://xxxx-xx.ngrok-free.app/webhook`).
4. En **Verify Token**, escribe el mismo token que configuraste en tu archivo `.env` (`META_VERIFY_TOKEN`).
5. Haz clic en **Verify and Save**.
6. Suscríbete a los campos `messages` (DMs) y `comments` (Comentarios en Posts).

---

## 🚦 Ejecución de Pruebas Unitarias

Para correr toda la suite de pruebas unitarias y de integración locales configuradas sobre bases de datos en memoria (`sqlite:///:memory:`):

```bash
pytest -v
```
