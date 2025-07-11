from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from orquestador import get_orchestrator_for_user, user_orchestrators, last_activity
from database_manager import message_db
from models import *
import time
import uuid
from typing import Dict, List, Optional
import asyncio

# Router para las APIs web (equivalente a Blueprint en Quart)
web_api = APIRouter(prefix="/api", tags=["conversations"])

class ConversationManager:
    def __init__(self):
        # Cargar conversaciones existentes desde la base de datos al inicializar
        self.conversations = {}
        self.operators = {}
        self.pending_queue = []
        self.processed_messages = set()  # Para evitar mensajes duplicados
        self._load_conversations_from_db()
    
    def _load_conversations_from_db(self):
        """Carga todas las conversaciones existentes desde la base de datos"""
        try:
            db_conversations = message_db.get_conversations()
            for db_conv in db_conversations:
                conversation = self._convert_db_to_conversation(db_conv)
                self.conversations[conversation["id"]] = conversation
            print(f"✅ Cargadas {len(self.conversations)} conversaciones desde la base de datos")
        except Exception as e:
            print(f"❌ Error cargando conversaciones: {e}")
    
    def _convert_db_to_conversation(self, db_conv: Dict) -> Dict:
        """Convierte formato de DB a formato de conversación"""
        # Obtener mensajes de la conversación
        messages = message_db.get_messages(db_conv['id'])
        
        # Convertir mensajes a formato frontend
        formatted_messages = []
        for msg in messages:
            # Manejo seguro de timestamps
            timestamp = msg['timestamp']
            if isinstance(timestamp, str):
                try:
                    # Intentar diferentes formatos de fecha
                    if '.' in timestamp:
                        # Formato con microsegundos
                        timestamp = timestamp.split('.')[0]  # Quitar microsegundos
                    timestamp = time.mktime(time.strptime(timestamp, "%Y-%m-%d %H:%M:%S"))
                except ValueError:
                    timestamp = time.time()  # Fallback a tiempo actual
            
            formatted_messages.append({
                "id": msg['id'],
                "content": msg['content'],
                "timestamp": timestamp,
                "sender": msg['sender_type'],
                "edited": msg['edited'],
                "status": msg['status']
            })
        
        # Manejo seguro de timestamps de conversación
        def safe_timestamp_conversion(ts_str, fallback=None):
            if fallback is None:
                fallback = time.time()
            if isinstance(ts_str, str):
                try:
                    if '.' in ts_str:
                        ts_str = ts_str.split('.')[0]  # Quitar microsegundos
                    return time.mktime(time.strptime(ts_str, "%Y-%m-%d %H:%M:%S"))
                except ValueError:
                    return fallback
            return ts_str if ts_str else fallback
        
        return {
            "id": db_conv['id'],
            "user": {
                "id": db_conv['user_phone'],
                "name": db_conv['user_name'],
                "phone": db_conv['user_phone']
            },
            "messages": formatted_messages,
            "status": db_conv['status'],
            "mode": db_conv['mode'],
            "lastActivity": safe_timestamp_conversion(db_conv['updated_at']),
            "unreadCount": db_conv.get('unread_count', 0),
            "tags": db_conv.get('tags', []),
            "assignedOperator": db_conv.get('assigned_operator'),
            "created_at": safe_timestamp_conversion(db_conv['created_at']),
            "pending_response": None
        }
    
    def get_conversation(self, conversation_id: str) -> Optional[Dict]:
        return self.conversations.get(conversation_id)
    
    def create_conversation(self, user_phone: str, user_name: str) -> Dict:
        # Primero verificar si ya existe una conversación para este usuario
        for conv in self.conversations.values():
            if conv["user"]["phone"] == user_phone:
                return conv
        
        # Crear nueva conversación en la base de datos
        conversation_id = message_db.save_conversation(
            whatsapp_chat_id=user_phone,  # Usamos el teléfono como chat_id
            user_phone=user_phone,
            user_name=user_name
        )
        
        conversation = {
            "id": conversation_id,
            "user": {
                "id": user_phone,
                "name": user_name,
                "phone": user_phone
            },
            "messages": [],
            "status": "pending",
            "mode": "auto",
            "lastActivity": time.time(),
            "unreadCount": 0,
            "tags": [],
            "assignedOperator": None,
            "created_at": time.time(),
            "pending_response": None,
            "last_read_timestamp": 0
        }
        
        # Guardar en memoria para acceso rápido
        self.conversations[conversation_id] = conversation
        return conversation
    
    def add_message(self, conversation_id: str, content: str, sender: str, message_id: str = None, status: str = "sent") -> Dict:
        if conversation_id not in self.conversations:
            return None
        
        # Generar ID si no se proporciona
        if not message_id:
            message_id = str(uuid.uuid4())
        
        # Guardar mensaje en la base de datos
        try:
            db_message_id = message_db.save_message(
                conversation_id=conversation_id,
                content=content,
                sender_type=sender,
                whatsapp_message_id=message_id
            )
        except Exception as e:
            print(f"❌ Error guardando mensaje en BD: {e}")
            # Continuar con la operación en memoria aunque falle la BD
        
        message = {
            "id": message_id,
            "content": content,
            "timestamp": time.time(),
            "sender": sender,
            "edited": False,
            "status": status
        }
        
        # Agregar a memoria para acceso rápido
        self.conversations[conversation_id]["messages"].append(message)
        self.conversations[conversation_id]["lastActivity"] = time.time()
        
        # Incrementar contador de no leídos si es del usuario
        if sender == "user":
            self.conversations[conversation_id]["unreadCount"] += 1
            
        return message
    
    def set_conversation_mode(self, conversation_id: str, mode: str, operator_id: str = None):
        if conversation_id in self.conversations:
            # Actualizar en memoria
            self.conversations[conversation_id]["mode"] = mode
            if mode == "manual" and operator_id:
                self.conversations[conversation_id]["assignedOperator"] = operator_id
                self.conversations[conversation_id]["status"] = "in_progress"
            
            # Actualizar en base de datos
            try:
                message_db.update_conversation_mode(conversation_id, mode)
            except Exception as e:
                print(f"❌ Error actualizando modo en BD: {e}")
    
    def get_conversations_for_operator(self, operator_id: str = None) -> List[Dict]:
        conversations = list(self.conversations.values())
        if operator_id:
            return [c for c in conversations if c.get("assignedOperator") == operator_id]
        return conversations
    
    def mark_as_read(self, conversation_id: str):
        """Marca una conversación como leída"""
        if conversation_id in self.conversations:
            import time
            current_timestamp = time.time()
            self.conversations[conversation_id]["unreadCount"] = 0
            self.conversations[conversation_id]["last_read_timestamp"] = current_timestamp
            try:
                message_db.mark_messages_as_read(conversation_id)
            except Exception as e:
                print(f"❌ Error marcando mensajes como leídos en BD: {e}")
    
    def is_message_processed(self, message_id: str) -> bool:
        """Verifica si un mensaje ya fue procesado"""
        return message_id in self.processed_messages
    
    def mark_message_processed(self, message_id: str):
        """Marca un mensaje como procesado"""
        self.processed_messages.add(message_id)

# Instancia global del manager
conv_manager = ConversationManager()

@web_api.get('/conversations', response_model=ConversationsResponse)
async def get_conversations():
    """Obtiene todas las conversaciones para el dashboard"""
    try:
        # Primero recargar conversaciones desde BD para asegurar datos actualizados
        conv_manager._load_conversations_from_db()
        
        conversations = conv_manager.get_conversations_for_operator()
        
        # Convertir timestamps a formato ISO
        for conv in conversations:
            conv["lastActivity"] = conv["lastActivity"]
            for msg in conv["messages"]:
                msg["timestamp"] = msg["timestamp"]
        
        return ConversationsResponse(
            success=True,
            conversations=conversations
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@web_api.post('/conversations/refresh', response_model=ConversationsResponse)
async def refresh_conversations():
    """Recarga todas las conversaciones desde la base de datos"""
    try:
        conv_manager._load_conversations_from_db()
        conversations = conv_manager.get_conversations_for_operator()
        
        return ConversationsResponse(
            success=True,
            message=f"Conversaciones recargadas desde BD",
            conversations=conversations
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@web_api.get('/conversations/{conversation_id}', response_model=ConversationResponse)
async def get_conversation(conversation_id: str):
    """Obtiene una conversación específica"""
    try:
        conversation = conv_manager.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversación no encontrada")
        
        return ConversationResponse(
            success=True,
            conversation=conversation
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@web_api.post('/conversations/{conversation_id}/messages', response_model=MessageResponse)
async def send_message(conversation_id: str, request: SendMessageRequest):
    """Envía un mensaje desde el frontend"""
    try:
        if not conversation_id or not request.content:
            raise HTTPException(status_code=400, detail="Faltan datos requeridos")
        
        conversation = conv_manager.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversación no encontrada")
        
        # Determinar el sender basado en el modo
        sender = request.sender_mode.value  # 'bot' o 'operator'
        
        if request.sender_mode == MessageSender.BOT:
            # Usar el orquestador para generar respuesta AI
            user_phone = conversation["user"]["phone"]
            user_name = conversation["user"]["name"]
            
            context = {
                "phone_number": user_phone,
                "user_name": user_name,
                "nombre": user_name
            }
            
            # Obtener orquestador para este usuario
            user_orchestrator = get_orchestrator_for_user(user_phone)
            response = await user_orchestrator.process_query(request.content, context)
            
            # Agregar mensaje del usuario
            conv_manager.add_message(conversation_id, request.content, "user")
            
            # Agregar respuesta del bot
            bot_response = response.get("response", "Lo siento, no pude procesar tu consulta.")
            message = conv_manager.add_message(conversation_id, bot_response, "bot")
            
        else:
            # Respuesta manual del operador
            message = conv_manager.add_message(conversation_id, request.content, "operator")
            
            # Cambiar el modo a manual si no lo estaba
            conv_manager.set_conversation_mode(conversation_id, "manual", request.operator_id)
        
        # Enviar mensaje por WhatsApp cuando es del operador
        if request.sender_mode == MessageSender.OPERATOR:
            # Importar la función desde main
            from main import send_whatsapp_message
            await send_whatsapp_message(conversation["user"]["phone"], {"response": request.content})
        
        return MessageResponse(
            success=True,
            message=message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@web_api.put('/conversations/{conversation_id}/mode', response_model=ApiResponse)
async def change_conversation_mode(conversation_id: str, request: SetModeRequest):
    """Cambia el modo de una conversación (auto/manual)"""
    try:
        conv_manager.set_conversation_mode(conversation_id, request.mode.value, request.operator_id)
        
        return ApiResponse(
            success=True,
            message=f"Modo cambiado a {request.mode.value}"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@web_api.put('/messages/{message_id}', response_model=MessageResponse)
async def edit_message(message_id: str, request: EditMessageRequest):
    """Edita un mensaje existente"""
    try:
        # Buscar el mensaje en todas las conversaciones
        for conversation in conv_manager.conversations.values():
            for message in conversation["messages"]:
                if message["id"] == message_id:
                    message["content"] = request.content
                    message["edited"] = True
                    
                    return MessageResponse(
                        success=True,
                        message=message
                    )
        
        raise HTTPException(status_code=404, detail="Mensaje no encontrado")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@web_api.get('/quick-responses', response_model=QuickResponsesResponse)
async def get_quick_responses():
    """Obtiene respuestas rápidas predefinidas"""
    quick_responses = [
        "Hola, ¿en qué puedo ayudarte?",
        "Gracias por contactarnos. Te responderemos pronto.",
        "¿Podrías proporcionar más detalles sobre tu consulta?",
        "Para consultas sobre nómina, contacta a RRHH."
    ]
    
    return QuickResponsesResponse(
        success=True,
        quick_responses=quick_responses
    )

@web_api.post('/conversations/{conversation_id}/pending-response/approve', response_model=MessageResponse)
async def approve_pending_response(conversation_id: str, request: ApproveResponseRequest):
    """Aprueba una respuesta pendiente y la envía a WhatsApp"""
    try:
        conversation = conv_manager.get_conversation(conversation_id)
        if not conversation or not conversation.get("pending_response"):
            raise HTTPException(status_code=404, detail="Conversación no encontrada o sin respuesta pendiente")
        
        pending = conversation["pending_response"]
        
        # Agregar mensaje al chat
        message = conv_manager.add_message(
            conversation_id, 
            pending["content"], 
            "bot"
        )
        
        # Enviar a WhatsApp
        from main import send_whatsapp_message
        await send_whatsapp_message(
            conversation["user"]["phone"], 
            {"response": pending["content"]}
        )
        
        # Limpiar respuesta pendiente
        conversation["pending_response"] = None
        
        return MessageResponse(
            success=True,
            message=message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@web_api.post('/conversations/{conversation_id}/pending-response/reject', response_model=ApiResponse)
async def reject_pending_response(conversation_id: str, request: RejectResponseRequest):
    """Rechaza una respuesta pendiente"""
    try:
        conversation = conv_manager.get_conversation(conversation_id)
        if not conversation or not conversation.get("pending_response"):
            raise HTTPException(status_code=404, detail="Conversación no encontrada o sin respuesta pendiente")
        
        # Simplemente limpiar la respuesta pendiente
        conversation["pending_response"] = None
        
        return ApiResponse(
            success=True,
            message="Respuesta rechazada"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@web_api.put('/conversations/{conversation_id}/pending-response/edit-and-approve', response_model=MessageResponse)
async def edit_and_approve_pending_response(conversation_id: str, request: EditAndApproveRequest):
    """Edita una respuesta pendiente y la aprueba"""
    try:
        conversation = conv_manager.get_conversation(conversation_id)
        if not conversation or not conversation.get("pending_response"):
            raise HTTPException(status_code=404, detail="Conversación no encontrada o sin respuesta pendiente")
        
        # Agregar mensaje editado al chat
        message = conv_manager.add_message(
            conversation_id, 
            request.content, 
            "bot"
        )
        
        # Marcar como editado
        message["edited"] = True
        
        # Enviar a WhatsApp
        from main import send_whatsapp_message
        await send_whatsapp_message(
            conversation["user"]["phone"], 
            {"response": request.content}
        )
        
        # Limpiar respuesta pendiente
        conversation["pending_response"] = None
        
        return MessageResponse(
            success=True,
            message=message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Función para integrar mensajes de WhatsApp con el sistema web
def sync_whatsapp_message(phone_number: str, message_text: str, sender: str = "user", user_name: str = None):
    """Sincroniza mensajes de WhatsApp con el sistema web y base de datos"""
    # Buscar conversación existente por teléfono
    conversation = None
    for conv in conv_manager.conversations.values():
        if conv["user"]["phone"] == phone_number:
            conversation = conv
            break
    
    # Si no existe, crear nueva conversación
    if not conversation:
        # Usar nombre proporcionado o generar uno por defecto
        if not user_name:
            user_name = f"Usuario {phone_number[-4:]}"
        conversation = conv_manager.create_conversation(phone_number, user_name)
        print(f"✅ Nueva conversación creada para {phone_number}")
    
    # Agregar mensaje (se guarda automáticamente en BD)
    message = conv_manager.add_message(conversation["id"], message_text, sender)
    print(f"💬 Mensaje sincronizado: {phone_number} -> {message_text[:50]}...")
    
    return conversation["id"]

# Función para obtener conversaciones al iniciar el frontend
def get_all_persisted_conversations():
    """Obtiene todas las conversaciones persistidas para cargar en el frontend"""
    return conv_manager.get_conversations_for_operator() 