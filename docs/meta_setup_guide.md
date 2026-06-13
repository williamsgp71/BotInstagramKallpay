# Manual de Configuración: Credenciales de Meta para el `.env`

Esta guía te guiará paso a paso para obtener las credenciales de Meta (Instagram Graph API) requeridas para configurar las variables de entorno en el archivo `.env`:

```env
META_VERIFY_TOKEN="tu_token_personalizado"
META_PAGE_ACCESS_TOKEN="tu_page_access_token"
META_APP_SECRET="tu_app_secret"
```

---

## Requisitos de Cuenta
Antes de comenzar, asegúrate de contar con:
1. Una cuenta de **Facebook** personal.
2. Una **Página de Facebook** pública (creada desde tu cuenta personal).
3. Una cuenta de **Instagram** configurada como **Cuenta Profesional** (Creador o Empresa).
4. La cuenta de Instagram profesional **vinculada** a tu Página de Facebook. (Puedes hacer esta vinculación en la configuración de la Página de Facebook, pestaña *Cuentas Vinculadas -> Instagram*).

---

## Paso 1: Crear una Cuenta y una App en Meta Developers

1. Ve al portal de [Meta for Developers](https://developers.facebook.com/).
2. Inicia sesión con tu cuenta de Facebook. Si es tu primera vez, regístrate como desarrollador aceptando los términos.
3. Haz clic en **Mis Apps** (My Apps) en la esquina superior derecha y luego en **Crear App** (Create App).
4. Selecciona el tipo de app **Negocios** (Business) o **Consumo** (si no aparece Negocios). Esto es importante para tener acceso a los permisos de Instagram.
5. Completa el nombre de tu aplicación y asóciala con tu cuenta comercial si tienes una (opcional). Haz clic en **Crear App**.

---

## Paso 2: Configurar las Variables Básicas

### 1. `META_APP_SECRET` (Secreto de la Aplicación)
Este valor valida la firma de los webhooks entrantes para asegurar que provienen de Meta y no de un tercero malintencionado.

1. En el menú lateral izquierdo de tu app en Meta Developers, ve a **Configuración** (Settings) -> **Básica** (Basic).
2. Busca la sección **Clave secreta de la app** (App Secret).
3. Haz clic en **Mostrar** (Show) (es posible que te pida reingresar tu contraseña de Facebook por seguridad).
4. Copia este código y pégalo en tu archivo `.env` en la variable `META_APP_SECRET`.

### 2. `META_VERIFY_TOKEN` (Token de Verificación Personalizado)
Este es un token de seguridad que **tú inventas** para que Meta y tu servidor FastAPI acuerden que la conexión del webhook es de confianza.

1. Inventa una frase o código alfanumérico seguro (ej. `MiBotSuperSecreto123!`).
2. Pégalo en tu archivo `.env` en la variable `META_VERIFY_TOKEN`.
3. *Guarda este valor*, ya que lo ingresarás en el portal de Meta al configurar el Webhook.

---

## Paso 3: Agregar los Productos y Obtener el `META_PAGE_ACCESS_TOKEN`

Para interactuar con Instagram, necesitamos configurar la funcionalidad de API de Mensajería.

1. En el menú de Meta Developers, ve a **Agregar producto** (Add Product) en el panel izquierdo.
2. Busca **Messenger** o **Instagram Graph API** y haz clic en **Configurar** (Set Up).
3. Una vez agregado Messenger/Instagram, ve a **Configuración** -> **Configuración de la API** (API Settings).

### Generar el Token de Acceso
1. En la sección **Tokens de acceso**, haz clic en **Agregar o eliminar páginas** (Add or Remove Pages) para asociar tu Página de Facebook (la cual a su vez está vinculada a tu cuenta profesional de Instagram).
2. Sigue el asistente de inicio de sesión de Facebook, selecciona la **Página de Facebook** y la **Cuenta de Instagram Profesional** que vas a usar. Otorga todos los permisos solicitados (administración de mensajes, comentarios, etc.).
3. Una vez vinculada la página, aparecerá en el listado. Haz clic en **Generar Token** (Generate Token) junto al nombre de tu Página de Facebook.
4. Acepta el descargo de responsabilidad y copia el token generado.
5. Pégalo en tu archivo `.env` en la variable `META_PAGE_ACCESS_TOKEN`.

---

## Paso 4: Configurar los Permisos y el Webhook en Meta

Para que Meta sepa a dónde enviar los eventos cuando alguien envíe un DM o comente un post, debes registrar el webhook.

1. Levanta tu túnel de `Ngrok` en tu terminal local para obtener tu dirección pública HTTPS:
   ```bash
   ngrok http 8000
   ```
2. Copia la URL HTTPS que te da Ngrok (ej. `https://1234-56-78.ngrok-free.app`).
3. Vuelve a Meta Developers, ve a **Webhooks** en el menú izquierdo (o dentro de la configuración de Messenger/Instagram).
4. Selecciona **Instagram** en el menú desplegable y haz clic en **Configurar este webhook** (o Editar suscripción).
5. Completa los campos:
   * **Callback URL:** `https://1234-56-78.ngrok-free.app/webhook` (reemplaza con tu URL de Ngrok y asegúrate de agregar `/webhook` al final).
   * **Verify Token:** El token personalizado que inventaste en el **Paso 2.2** (`META_VERIFY_TOKEN`).
6. Haz clic en **Verificar y Guardar**. Meta enviará una solicitud de prueba HTTP GET a tu servidor FastAPI, el cual validará el token y responderá automáticamente.
7. Si todo es correcto, la suscripción se guardará con éxito.

### Suscripción a Campos (Eventos)
Una vez guardado el webhook, suscríbete a los siguientes campos en la tabla de Instagram:
* **`messages`**: Envía eventos cuando un usuario te escribe un mensaje privado (DM).
* **`comments`**: Envía eventos cuando un usuario comenta en alguno de tus posts.

---

## Paso 5: Permisos Avanzados (Paso Crítico)
Mientras tu aplicación esté en modo **Desarrollo** (Development), el bot **solo responderá a cuentas que estén registradas como Administradores, Desarrolladores o Testers (Testers)** dentro de tu panel de Meta Developers (sección *Roles -> Roles*).

Para que responda a cualquier usuario del público:
1. Debes solicitar a Meta los permisos de uso avanzado (`instagram_manage_messages` y `instagram_manage_comments`) mediante el proceso de **App Review** dentro del portal de Meta.
2. Pasar tu App a modo **En Vivo** (Live) en el interruptor de la barra superior una vez aprobada.
