from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, ORJSONResponse
from contextlib import asynccontextmanager
import uvicorn
from orquestador import get_orchestrator_for_user, check_and_cleanup_inactive_users, user_orchestrators, last_activity, get_inactive_users, INACTIVITY_TIMEOUT
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from indexador import DocumentIndexer
import time
import uuid
from models import HealthResponse, UserStatsResponse, UserStatsModel
# from web_api import web_api, sync_whatsapp_message, conv_manager  # Temporal: web_api necesita migración a FastAPI

# Implementaciones temporales hasta migrar web_api completamente
class TempConversationManager:
    def __init__(self):
        self.conversations = {}
        self.processed_messages = set()  # Para evitar mensajes duplicados
    
    def get_conversation(self, conversation_id: str):
        return self.conversations.get(conversation_id)
    
    def add_message(self, conversation_id: str, content: str, sender: str):
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = {
                "id": conversation_id,
                "messages": [],
                "mode": "auto",  
                "status": "active",
                "unreadCount": 0,
                "operator_id": None
            }
        
        message = {
            "id": str(uuid.uuid4()),
            "content": content,
            "sender": sender,
            "timestamp": time.time()
        }
        
        self.conversations[conversation_id]["messages"].append(message)
        
        # Incrementar contador de no leídos si es mensaje del usuario
        if sender == "user":
            self.conversations[conversation_id]["unreadCount"] += 1
            
        return message
    
    def mark_as_read(self, conversation_id: str):
        if conversation_id in self.conversations:
            self.conversations[conversation_id]["unreadCount"] = 0
    
    def is_message_processed(self, message_id: str) -> bool:
        return message_id in self.processed_messages
    
    def mark_message_processed(self, message_id: str):
        self.processed_messages.add(message_id)

def sync_whatsapp_message(phone_number: str, message_text: str, sender: str = "user"):
    """Función temporal para sincronizar mensajes de WhatsApp"""
    conversation_id = f"whatsapp_{phone_number}"
    conv_manager.add_message(conversation_id, message_text, sender)
    return conversation_id

# Instancia temporal del manager
conv_manager = TempConversationManager()

# Cargar variables de entorno
load_dotenv("config/.env")

# Configuración de WhatsApp
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID", "508244739043826")
WHATSAPP_API_URL = "https://graph.facebook.com/v17.0/508244739043826/messages"
WEBHOOK_URL = "https://incentive-incl-moment-valium.trycloudflare.com/webhook"
VERIFY_TOKEN = os.getenv("WEBHOOK_VERIFY_TOKEN")

# Inicializar el scheduler
scheduler = AsyncIOScheduler()
scheduler_started = False  # Flag para evitar inicios múltiples

class MessagePreProcessor:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7
        )
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """Tu ÚNICA tarea es corregir errores ortográficos o gramaticales obvios.
            
            REGLAS ESTRICTAS:
            1. NO cambies el significado ni la intención del mensaje original.
            2. NO cambies palabras clave como "curso", "capacitación", "inscrito", etc.
            3. NO reformules ni reinterpretes la pregunta.
            4. Si el mensaje ya es comprensible, NO LO MODIFIQUES EN ABSOLUTO.
            5. Mensajes cortos (menos de 10 palabras) NO deben ser modificados nunca.
            6. Si hay duda, DEJA EL MENSAJE ORIGINAL sin cambios.
            
            EJEMPLOS DE CAMBIOS PERMITIDOS:
            - "kiero" → "quiero" 
            - "nesecito" → "necesito"
            - "en que cursos" → "en qué cursos" (solo tildes y puntuación)
            
            EJEMPLOS PROHIBIDOS:
            ❌ "hola, quisiera saber en que cursos estoy inscrito" → "¿Puedes decirme en qué plataforma estás inscrito?"
            ❌ "como puedo ver mis cursos" → "¿Cómo puedo acceder a la información de mis cursos en el portal?"
            
            IMPORTANTE: Tu trabajo es ÚNICAMENTE corregir errores ortográficos básicos, 
            NO reescribir, NO interpretar, NO expandir el mensaje."""),
            ("human", "{text}")
        ])

    async def process_message(self, text: str) -> str:
        try:
            response = await self.llm.ainvoke(
                self.prompt.format_messages(text=text)
            )
            return response.content.strip()
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return text

# Inicializar el pre-procesador junto con el agente
preprocessor = MessagePreProcessor()

async def send_whatsapp_message(phone_number: str, response_data: dict):
    """Envía un mensaje de WhatsApp usando la API de Meta """
    try:
        print(f"\n Intentando enviar mensaje a {phone_number}")
        
        token = WHATSAPP_TOKEN
        
        # URL de la API
        url = f"https://graph.facebook.com/v17.0/{WHATSAPP_PHONE_ID}/messages"

        # Datos a enviar
        data = {
            "messaging_product": "whatsapp",
            "to": phone_number,
            "type": "text",
            "text": {
                "body": response_data["response"]  # Enviamos solo la respuesta como cadena
            }
        }
                
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=data)
                print(f" Respuesta de WhatsApp API: {response.status_code}")
                print(f" Contenido de respuesta: {response.text}")
                
                if response.status_code != 200:
                    print(f"⚠️ Headers de respuesta: {dict(response.headers)}")
                
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"❌ Error enviando mensaje: {str(e)}")
            print(f"❌ Detalles del error: {type(e).__name__}")
            return None
    except Exception as e:
        print(f"❌ Error enviando mensaje: {str(e)}")
        return None

async def run_indexer():
    """Ejecuta la indexación de documentos"""
    print("📂 Indexando documentos...")
    try:
        # Crear una instancia del indexador
        indexer = DocumentIndexer()
        # Ejecutar la indexación optimizada
        await indexer.index_documents()
        print("✅ Indexación completada")
    except Exception as e:
        print(f"❌ Error en indexación: {str(e)}")

async def startup_tasks():
    """Tareas de inicio del servidor"""
    global scheduler_started
    
    # Evitar inicialización múltiple del scheduler
    if scheduler_started:
        print("⚠️ Scheduler ya iniciado, saltando inicialización...")
        return
    
    print("🚀 Iniciando tareas de arranque...")
    
    # Indexar inmediatamente al arrancar
    await run_indexer()
    
    # Programar indexación cada 60 minutos
    scheduler.add_job(run_indexer, "interval", minutes=60, id="indexer_job")
    
    # Programar limpieza de memoria cada 15 minutos
    scheduler.add_job(check_memory_cleanup, "interval", minutes=15, id="memory_cleanup_job")
    
    # Iniciar scheduler solo una vez
    if not scheduler.running:
        scheduler.start()
        scheduler_started = True
        print("✅ Scheduler iniciado correctamente")
    else:
        print("⚠️ Scheduler ya estaba corriendo")

async def check_memory_cleanup():
    """Verifica y limpia memorias inactivas"""
    print("📋 Verificando usuarios inactivos para limpiar memoria...")
    check_and_cleanup_inactive_users()

async def shutdown_tasks():
    """Tareas de cierre del servidor"""
    print("🔌 Cerrando servidor...")
    
    # Cerrar scheduler
    if scheduler.running:
        scheduler.shutdown()
        print("✅ Scheduler cerrado")

# Context manager para el ciclo de vida de la aplicación
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await startup_tasks()
    yield
    # Shutdown
    await shutdown_tasks()

# Crear la aplicación FastAPI
app = FastAPI(
    title="Tony - Asistente de RRHH",
    description="API para el asistente de WhatsApp especializado en temas laborales",
    version="2.0.0",
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar orígenes específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Optimizaciones de rendimiento
# Middleware de compresión
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Usar ORJSONResponse por defecto para mejor rendimiento
app.default_response_class = ORJSONResponse

# Incluir el blueprint de APIs web
# app.register_blueprint(web_api, url_prefix="/api")  # Temporal: web_api necesita migración a FastAPI

@app.get("/health", response_model=HealthResponse)
async def health():
    """Endpoint de health check"""
    return HealthResponse(status="ok", uptime=time.time(), version="2.0.0")

@app.get("/users/stats", response_model=UserStatsResponse)
async def users_stats():
    """Endpoint para ver estadísticas de usuarios activos"""
    
    current_time = time.time()
    active_users = []
    
    # Usar la función utilitaria para obtener usuarios inactivos
    inactive_users = get_inactive_users(current_time)
    
    for user_id, last_active in last_activity.items():
        time_since_last_activity = current_time - last_active
        active_users.append(UserStatsModel(
            user_id=user_id,
            last_activity_minutes_ago=round(time_since_last_activity / 60, 2),
            has_orchestrator=user_id in user_orchestrators,
            is_active=user_id not in inactive_users  # Usar la lógica centralizada
        ))
    
    return UserStatsResponse(
        success=True,
        active_users=active_users,
        total_users=len(active_users)
    )

@app.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_challenge: str = Query(alias="hub.challenge"), 
    hub_verify_token: str = Query(alias="hub.verify_token")
):
    """Verifica el webhook para la API de WhatsApp"""
    print(f"🔐 Verificando webhook - Mode: {hub_mode}, Token: {hub_verify_token}")
    
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        print("✅ Webhook verificado correctamente")
        return int(hub_challenge)
    else:
        print("❌ Error de verificación del webhook")
        raise HTTPException(status_code=403, detail="Token de verificación inválido")

async def validate_phone_number(phone_number): #Aun no se usa , pero mas adelante cuando tenga la bd de los empleados se usara.
    """Valida si el número de teléfono está autorizado."""
    clean_number = phone_number.replace('51', '', 1) if phone_number.startswith('51') else phone_number
    
    headers = {
        "Content-Type": "application/json",
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
    
    try:
        print(f"\n Validando número: {phone_number}")
        print(f" Número limpio: {clean_number}")
        
        async with httpx.AsyncClient() as client:
            url = f"{SUPABASE_URL}/rest/v1/empleados"
            params = {
                "select": "dni,nombre",  # Quitamos 'area' porque no existe
                "telefono": f"eq.{clean_number}"
            }
            print(f" URL: {url}")
            print(f" Params: {params}")
            
            response = await client.get(url, headers=headers, params=params)
        
        print(f" Respuesta de validación: {response.status_code}")
        print(f" Contenido de respuesta: {response.text}")
        
        if response.status_code == 200:
            empleados = response.json()
            print(f"📋 Empleados encontrados: {empleados}")
            if empleados:
                empleado = empleados[0]
                print(f"✅ Usuario autorizado: {empleado['nombre']}")
                return True, empleado
            print(f"❌ Número no registrado: {clean_number}")
        return False, None
    except Exception as e:
        print(f"❌ Error validando número: {str(e)}")
        return False, None


@app.post("/webhook")
async def handle_webhook(request: Request):
    """Maneja los webhooks entrantes de WhatsApp"""
    try:
        data = await request.json()
        print(f"📨 Webhook recibido: {data}")
        
        if "object" in data and data["object"] == "whatsapp_business_account":
            for entry in data["entry"]:
                for change in entry["changes"]:
                    if "messages" in change["value"]:
                        for message in change["value"]["messages"]:
                            if message["type"] == "text":
                                # Verificar si el mensaje ya fue procesado
                                message_id = message["id"]
                                if conv_manager.is_message_processed(message_id):
                                    print(f"⚠️ Mensaje {message_id} ya procesado, saltando...")
                                    continue
                                
                                # Marcar mensaje como procesado
                                conv_manager.mark_message_processed(message_id)
                                
                                phone_number = message["from"]
                                message_text = message["text"]["body"]
                                nombre = change["value"]["contacts"][0]["profile"]["name"]
                                
                                print(f"\n👤 Mensaje de {nombre} ({phone_number}): {message_text}")
                                
                                # 1. Sincronizar mensaje con el sistema web
                                conversation_id = sync_whatsapp_message(phone_number, message_text, "user")
                                conversation = conv_manager.get_conversation(conversation_id)
                                
                                # 2. Verificar el modo de la conversación
                                conversation_mode = conversation.get("mode", "auto") if conversation else "auto"
                                
                                print(f"🔧 Modo de conversación: {conversation_mode}")
                                
                                # 3. Solo responder automáticamente si está en modo "auto"
                                if conversation_mode == "auto":
                                    print("🤖 Respondiendo automáticamente...")
                                    
                                    # Procesar mensaje con LLM
                                    processed = await preprocessor.process_message(message_text)
                                    print(f"🔍 Mensaje procesado: {processed}")
                                    
                                    try:
                                        # Construir contexto con los datos del usuario
                                        context = {
                                            "phone_number": phone_number,
                                            "user_name": nombre,
                                            "nombre": nombre
                                        }
                                        
                                        # 🧠 Obtener orquestador personalizado para este usuario
                                        user_orchestrator = get_orchestrator_for_user(phone_number)
                                        response = await user_orchestrator.process_query(processed, context)
                                        
                                        # Obtener respuesta del orquestador
                                        response_text = response.get("response", "Lo siento, no pude procesar tu consulta.")
                                        
                                        # Sincronizar respuesta del bot con el sistema web
                                        if conversation:
                                            conv_manager.add_message(conversation_id, response_text, "bot")
                                        
                                        # Enviar respuesta por WhatsApp
                                        whatsapp_data = {"response": response_text}
                                        await send_whatsapp_message(phone_number, whatsapp_data)
                                        
                                    except Exception as e:
                                        print(f"❌ Error en orquestador: {str(e)}")
                                        error_msg = "Lo siento, hubo un error procesando tu consulta."
                                        error_data = {"response": error_msg}
                                        await send_whatsapp_message(phone_number, error_data)
                                        
                                        # Sincronizar mensaje de error
                                        if conversation:
                                            conv_manager.add_message(conversation_id, error_msg, "bot")
                                            
                                elif conversation_mode == "manual":
                                    print("👨‍💼 Modo manual - Esperando respuesta del operador")
                                    # Solo registrar el mensaje, no responder automáticamente
                                    # El operador verá el mensaje en el frontend
                                    
                                    # Cambiar estado a "pendiente" para alertar al operador
                                    if conversation:
                                        conversation["status"] = "pending"
                                        # Ya se incrementó el unreadCount en add_message
                                        print(f"📬 Mensaje en espera para operador. Total no leídos: {conversation.get('unreadCount', 0)}")
                                        
                                elif conversation_mode == "hybrid":
                                    print("🤖👨‍💼 Modo híbrido - Bot genera respuesta para aprobación")
                                    
                                    # Procesar mensaje con LLM (igual que modo auto)
                                    processed = await preprocessor.process_message(message_text)
                                    print(f"🔍 Mensaje procesado: {processed}")
                                    
                                    try:
                                        # Construir contexto con los datos del usuario
                                        context = {
                                            "phone_number": phone_number,
                                            "user_name": nombre,
                                            "nombre": nombre
                                        }
                                        
                                        # 🧠 Obtener orquestador personalizado para este usuario
                                        user_orchestrator = get_orchestrator_for_user(phone_number)
                                        response = await user_orchestrator.process_query(processed, context)
                                        
                                        # Obtener respuesta del orquestador
                                        response_text = response.get("response", "Lo siento, no pude procesar tu consulta.")
                                        
                                        # Guardar respuesta pendiente SIN agregar al chat todavía
                                        if conversation:
                                            # Solo actualizar el estado de la conversación con la respuesta pendiente
                                            conversation["pending_response"] = {
                                                "content": response_text, 
                                                "timestamp": time.time(),
                                                "id": str(uuid.uuid4())
                                            }
                                            
                                        print(f"✅ Respuesta generada pendiente de aprobación: {response_text[:50]}...")
                                        
                                        # NO enviar a WhatsApp automáticamente
                                        # NO agregar al chat todavía
                                        # El operador debe aprobar primero desde el frontend
                                        
                                    except Exception as e:
                                        print(f"❌ Error en orquestador híbrido: {str(e)}")
                                        # En caso de error, guardar mensaje de error pendiente
                                        error_msg = "Lo siento, hubo un error procesando tu consulta."
                                        if conversation:
                                            conversation["pending_response"] = {
                                                "content": error_msg,
                                                "timestamp": time.time(),
                                                "id": str(uuid.uuid4()),
                                                "is_error": True
                                            }
                                        

                            
                                return {"status": "ok"}
            
            return {"status": "ok"}
            
        print("❌ Objeto no reconocido:", data.get("object"))
        raise HTTPException(status_code=404, detail="Objeto no reconocido")
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error en webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error procesando webhook: {str(e)}")

# ================================================================
# API ENDPOINTS PARA EL FRONTEND
# ================================================================

@app.get("/conversations")
async def get_conversations():
    """Obtiene todas las conversaciones activas"""
    try:
        conversations = []
        current_time = time.time()
        
        for conv_id, conversation in conv_manager.conversations.items():
            # Calcular tiempo desde última actividad
            last_message_time = conversation["messages"][-1]["timestamp"] if conversation["messages"] else current_time
            
            # Contar mensajes no leídos (simulado)
            unread_count = len([msg for msg in conversation["messages"] if msg["sender"] == "user"]) if conversation.get("status") == "pending" else 0
            
            phone_number = conv_id.replace("whatsapp_", "")
            customer_name = phone_number.replace("51", "")
            
            conversations.append({
                "id": conv_id,
                "user": {
                    "id": phone_number,
                    "name": customer_name,
                    "avatar": None
                },
                "messages": conversation["messages"],
                "status": conversation.get("status", "active"),
                "mode": conversation.get("mode", "auto"),
                "lastActivity": last_message_time,
                "unreadCount": unread_count,
                "tags": [],
                "assignedOperator": conversation.get("operator_id"),
                "pending_response": conversation.get("pending_response")
            })
        
        # Si no hay conversaciones, agregar datos de prueba
        if not conversations:
            demo_time = current_time - 3600  # 1 hora atrás
            conversations = [
                {
                    "id": "demo_conversation_1",
                    "user": {
                        "id": "51987654321",
                        "name": "Juan Pérez",
                        "avatar": None
                    },
                    "messages": [
                        {
                            "id": "msg_1",
                            "content": "¡Hola! ¿Podrías ayudarme con información sobre los cursos disponibles?",
                            "sender": "user",
                            "timestamp": demo_time
                        },
                        {
                            "id": "msg_2",
                            "content": "¡Hola Juan! Claro, te puedo ayudar con información sobre nuestros cursos. ¿Hay algún área en particular que te interese?",
                            "sender": "bot",
                            "timestamp": demo_time + 60
                        }
                    ],
                    "status": "active",
                    "mode": "auto",
                    "lastActivity": demo_time,
                    "unreadCount": 0,
                    "tags": ["consultas", "cursos"],
                    "assignedOperator": None,
                    "pending_response": None
                },
                {
                    "id": "demo_conversation_2",
                    "user": {
                        "id": "51976543210",
                        "name": "María García",
                        "avatar": None
                    },
                    "messages": [
                        {
                            "id": "msg_3",
                            "content": "Tengo una consulta sobre las políticas de recursos humanos",
                            "sender": "user",
                            "timestamp": demo_time - 1800
                        },
                        {
                            "id": "msg_4",
                            "content": "Gracias por la información, me parece muy útil.",
                            "sender": "user",
                            "timestamp": demo_time - 1200
                        }
                    ],
                    "status": "pending",
                    "mode": "manual",
                    "lastActivity": demo_time - 1800,
                    "unreadCount": 1,
                    "tags": ["rrhh", "políticas"],
                    "assignedOperator": "operador_1",
                    "pending_response": None
                }
            ]
        
        return {"success": True, "conversations": conversations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Obtiene una conversación específica"""
    try:
        conversation = conv_manager.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversación no encontrada")
        
        current_time = time.time()
        last_message_time = conversation["messages"][-1]["timestamp"] if conversation["messages"] else current_time
        unread_count = len([msg for msg in conversation["messages"] if msg["sender"] == "user"]) if conversation.get("status") == "pending" else 0
        
        phone_number = conversation_id.replace("whatsapp_", "")
        customer_name = phone_number.replace("51", "")
        
        result = {
            "id": conversation_id,
            "user": {
                "id": phone_number,
                "name": customer_name,
                "avatar": None
            },
            "messages": conversation["messages"],
            "status": conversation.get("status", "active"),
            "mode": conversation.get("mode", "auto"),
            "lastActivity": last_message_time,
            "unreadCount": unread_count,
            "tags": [],
            "assignedOperator": conversation.get("operator_id"),
            "pending_response": conversation.get("pending_response")
        }
        
        return {"success": True, "conversation": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/conversations/{conversation_id}/messages")
async def send_message_to_conversation(conversation_id: str, request: Request):
    """Envía un mensaje a una conversación"""
    try:
        data = await request.json()
        content = data.get("content", "")
        sender_mode = data.get("sender_mode", "operator")
        operator_id = data.get("operator_id", "system")
        
        # Crear mensaje
        message = {
            "id": str(uuid.uuid4()),
            "content": content,
            "sender": "operator" if sender_mode == "operator" else "bot",
            "timestamp": time.time(),
            "operator_id": operator_id if sender_mode == "operator" else None
        }
        
        # Agregar mensaje a la conversación
        conversation = conv_manager.get_conversation(conversation_id)
        if not conversation:
            # Crear conversación si no existe
            phone_number = conversation_id.replace("whatsapp_", "")
            conv_manager.add_message(conversation_id, content, "operator")
        else:
            conversation["messages"].append(message)
        
        # Si es mensaje del operador, enviar por WhatsApp
        if sender_mode == "operator":
            phone_number = conversation_id.replace("whatsapp_", "")
            whatsapp_data = {"response": content}
            await send_whatsapp_message(phone_number, whatsapp_data)
        
        return {"success": True, "message": message}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/conversations/{conversation_id}/mode")
async def change_conversation_mode(conversation_id: str, request: Request):
    """Cambia el modo de una conversación"""
    try:
        data = await request.json()
        mode = data.get("mode", "auto")
        operator_id = data.get("operator_id")
        
        conversation = conv_manager.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversación no encontrada")
        
        conversation["mode"] = mode
        if operator_id:
            conversation["operator_id"] = operator_id
        
        # Si cambia a modo manual, marcar como leído por el operador
        if mode == "manual":
            conv_manager.mark_as_read(conversation_id)
            print(f"✅ Conversación {conversation_id} marcada como leída al cambiar a modo manual")
        
        return {"success": True, "message": f"Modo cambiado a {mode}"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/conversations/{conversation_id}/mark-read")
async def mark_conversation_read(conversation_id: str):
    """Marca una conversación como leída"""
    try:
        conversation = conv_manager.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversación no encontrada")
        
        conv_manager.mark_as_read(conversation_id)
        print(f"✅ Conversación {conversation_id} marcada como leída")
        
        return {"success": True, "unreadCount": 0}
    except Exception as e:
        print(f"❌ Error marcando como leída: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/conversations/{conversation_id}/approve-pending")
async def approve_pending_response(conversation_id: str):
    """Aprueba y envía una respuesta pendiente"""
    try:
        conversation = conv_manager.get_conversation(conversation_id)
        if not conversation or not conversation.get("pending_response"):
            raise HTTPException(status_code=404, detail="Respuesta pendiente no encontrada")
        
        pending_response = conversation["pending_response"]
        response_content = pending_response["content"]
        
        # Enviar respuesta por WhatsApp
        phone_number = conversation_id.replace("whatsapp_", "")
        whatsapp_data = {"response": response_content}
        await send_whatsapp_message(phone_number, whatsapp_data)
        
        # Agregar mensaje a la conversación
        message = {
            "id": str(uuid.uuid4()),
            "content": response_content,
            "sender": "bot",
            "timestamp": time.time(),
            "status": "sent"
        }
        conversation["messages"].append(message)
        
        # Limpiar respuesta pendiente
        conversation["pending_response"] = None
        
        print(f"✅ Respuesta pendiente aprobada y enviada para {conversation_id}")
        return {"success": True, "message": "Respuesta aprobada y enviada"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error aprobando respuesta pendiente: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/conversations/{conversation_id}/reject-pending")
async def reject_pending_response(conversation_id: str):
    """Rechaza una respuesta pendiente"""
    try:
        conversation = conv_manager.get_conversation(conversation_id)
        if not conversation or not conversation.get("pending_response"):
            raise HTTPException(status_code=404, detail="Respuesta pendiente no encontrada")
        
        # Limpiar respuesta pendiente
        conversation["pending_response"] = None
        
        print(f"❌ Respuesta pendiente rechazada para {conversation_id}")
        return {"success": True, "message": "Respuesta rechazada"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error rechazando respuesta pendiente: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/conversations/{conversation_id}/edit-and-approve")
async def edit_and_approve_pending_response(conversation_id: str, request: Request):
    """Edita y aprueba una respuesta pendiente"""
    try:
        data = await request.json()
        new_content = data.get("content", "")
        
        if not new_content.strip():
            raise HTTPException(status_code=400, detail="El contenido no puede estar vacío")
        
        conversation = conv_manager.get_conversation(conversation_id)
        if not conversation or not conversation.get("pending_response"):
            raise HTTPException(status_code=404, detail="Respuesta pendiente no encontrada")
        
        # Enviar respuesta editada por WhatsApp
        phone_number = conversation_id.replace("whatsapp_", "")
        whatsapp_data = {"response": new_content}
        await send_whatsapp_message(phone_number, whatsapp_data)
        
        # Agregar mensaje editado a la conversación
        message = {
            "id": str(uuid.uuid4()),
            "content": new_content,
            "sender": "bot",
            "timestamp": time.time(),
            "status": "sent",
            "edited": True
        }
        conversation["messages"].append(message)
        
        # Limpiar respuesta pendiente
        conversation["pending_response"] = None
        
        print(f"✅ Respuesta pendiente editada, aprobada y enviada para {conversation_id}")
        return {"success": True, "message": "Respuesta editada, aprobada y enviada"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error editando y aprobando respuesta pendiente: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/quick-responses")
async def get_quick_responses():
    """Obtiene respuestas rápidas predefinidas"""
    try:
        # Respuestas rápidas de ejemplo para RRHH
        quick_responses = [
            {
                "id": "1",
                "text": "¡Hola! ¿En qué puedo ayudarte hoy?",
                "category": "saludo"
            },
            {
                "id": "2", 
                "text": "He recibido tu consulta. Te responderé en breve.",
                "category": "confirmacion"
            },
            {
                "id": "3",
                "text": "Para poder ayudarte mejor, necesito que me proporciones más información.",
                "category": "solicitud"
            },
            {
                "id": "4",
                "text": "Te voy a derivar con un especialista que podrá ayudarte mejor con tu consulta.",
                "category": "derivacion"
            },
            {
                "id": "5",
                "text": "¡Gracias por contactarnos! Si tienes más dudas, no dudes en escribirnos.",
                "category": "despedida"
            }
        ]
        
        return {"success": True, "quick_responses": quick_responses}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def run_server():
    """Inicia el servidor principal."""
    print("\n🤖 Tony - Asistente de RRHH (FastAPI)")
    print("=" * 40)
    print("🚀 Iniciando servidor...")
    print("📍 Servidor corriendo en http://localhost:8000")
    print("📱 Esperando mensajes...")
    print("🎯 SISTEMA MULTI-USUARIO ACTIVADO")
    print("   • Cada usuario tendrá su propia memoria")
    print("   • Limpieza automática de usuarios inactivos")
    print("   • Estadísticas en: http://localhost:8000/users/stats")
    print("   • Documentación API: http://localhost:8000/docs")
    print("   • Redoc: http://localhost:8000/redoc")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Cambiar a True solo para desarrollo
        log_level="info"
    )

if __name__ == "__main__":
    run_server() 