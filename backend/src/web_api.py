from quart import Blueprint, request, jsonify
from quart_cors import cors
from orquestador import get_orchestrator_for_user, user_orchestrators, last_activity
import time
import uuid
from typing import Dict, List, Optional
import asyncio

# Blueprint para las APIs web
web_api = Blueprint('web_api', __name__)

# Estructura de datos para manejar conversaciones web
conversations_db = {}  # En memoria por ahora, después se puede migrar a Supabase
operators_queue = {}   # Cola de operadores disponibles
conversation_modes = {}  # Modo de cada conversación: 'auto', 'manual', 'mixed'

class ConversationManager:
    def __init__(self):
        self.conversations = {}
        self.operators = {}
        self.pending_queue = []
    
    def get_conversation(self, conversation_id: str) -> Optional[Dict]:
        return self.conversations.get(conversation_id)
    
    def create_conversation(self, user_phone: str, user_name: str) -> Dict:
        conversation_id = str(uuid.uuid4())
        conversation = {
            "id": conversation_id,
            "user": {
                "id": user_phone,
                "name": user_name,
                "phone": user_phone
            },
            "messages": [],
            "status": "pending",  # pending, in_progress, closed
            "mode": "auto",  # auto, manual, hybrid
            "lastActivity": time.time(),
            "unreadCount": 0,
            "tags": [],
            "assignedOperator": None,
            "created_at": time.time(),
            "pending_response": None  # Para modo híbrido
        }
        self.conversations[conversation_id] = conversation
        return conversation
    
    def add_message(self, conversation_id: str, content: str, sender: str, message_id: str = None, status: str = "sent") -> Dict:
        if conversation_id not in self.conversations:
            return None
        
        message = {
            "id": message_id or str(uuid.uuid4()),
            "content": content,
            "timestamp": time.time(),
            "sender": sender,  # 'user', 'bot', 'operator'
            "edited": False,
            "status": status  # 'sent', 'pending_approval', 'approved', 'rejected'
        }
        
        self.conversations[conversation_id]["messages"].append(message)
        self.conversations[conversation_id]["lastActivity"] = time.time()
        
        # Incrementar contador de no leídos si es del usuario
        if sender == "user":
            self.conversations[conversation_id]["unreadCount"] += 1
            
        return message
    
    def set_conversation_mode(self, conversation_id: str, mode: str, operator_id: str = None):
        if conversation_id in self.conversations:
            self.conversations[conversation_id]["mode"] = mode
            if mode == "manual" and operator_id:
                self.conversations[conversation_id]["assignedOperator"] = operator_id
                self.conversations[conversation_id]["status"] = "in_progress"
    
    def get_conversations_for_operator(self, operator_id: str = None) -> List[Dict]:
        conversations = list(self.conversations.values())
        if operator_id:
            return [c for c in conversations if c.get("assignedOperator") == operator_id]
        return conversations

# Instancia global del manager
conv_manager = ConversationManager()

@web_api.route('/api/conversations', methods=['GET'])
async def get_conversations():
    """Obtiene todas las conversaciones para el dashboard"""
    try:
        conversations = conv_manager.get_conversations_for_operator()
        
        # Convertir timestamps a formato ISO
        for conv in conversations:
            conv["lastActivity"] = conv["lastActivity"]
            for msg in conv["messages"]:
                msg["timestamp"] = msg["timestamp"]
        
        return jsonify({
            "success": True,
            "conversations": conversations
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@web_api.route('/api/conversations/<conversation_id>', methods=['GET'])
async def get_conversation(conversation_id: str):
    """Obtiene una conversación específica"""
    try:
        conversation = conv_manager.get_conversation(conversation_id)
        if not conversation:
            return jsonify({
                "success": False,
                "error": "Conversación no encontrada"
            }), 404
        
        return jsonify({
            "success": True,
            "conversation": conversation
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@web_api.route('/api/conversations/<conversation_id>/messages', methods=['POST'])
async def send_message(conversation_id: str):
    """Envía un mensaje desde el frontend"""
    try:
        data = await request.get_json()
        content = data.get('content')
        sender_mode = data.get('sender_mode', 'operator')  # 'bot' o 'operator'
        operator_id = data.get('operator_id', 'system')
        
        if not conversation_id or not content:
            return jsonify({
                "success": False,
                "error": "Faltan datos requeridos"
            }), 400
        
        conversation = conv_manager.get_conversation(conversation_id)
        if not conversation:
            return jsonify({
                "success": False,
                "error": "Conversación no encontrada"
            }), 404
        
        # Determinar el sender basado en el modo
        sender = sender_mode  # 'bot' o 'operator'
        
        if sender_mode == 'bot':
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
            response = await user_orchestrator.process_query(content, context)
            
            # Agregar mensaje del usuario
            conv_manager.add_message(conversation_id, content, "user")
            
            # Agregar respuesta del bot
            bot_response = response.get("response", "Lo siento, no pude procesar tu consulta.")
            message = conv_manager.add_message(conversation_id, bot_response, "bot")
            
        else:
            # Respuesta manual del operador
            message = conv_manager.add_message(conversation_id, content, "operator")
            
            # Cambiar el modo a manual si no lo estaba
            conv_manager.set_conversation_mode(conversation_id, "manual", operator_id)
        
        # Enviar mensaje por WhatsApp cuando es del operador
        if sender_mode == 'operator':
            # Importar la función desde main
            from main import send_whatsapp_message
            await send_whatsapp_message(conversation["user"]["phone"], {"response": content})
        
        return jsonify({
            "success": True,
            "message": message
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@web_api.route('/api/conversations/<conversation_id>/mode', methods=['PUT'])
async def change_conversation_mode(conversation_id: str):
    """Cambia el modo de una conversación (auto/manual)"""
    try:
        data = await request.get_json()
        mode = data.get('mode')  # 'auto', 'manual'
        operator_id = data.get('operator_id')
        
        if mode not in ['auto', 'manual', 'hybrid']:
            return jsonify({
                "success": False,
                "error": "Modo inválido. Debe ser: auto, manual o hybrid"
            }), 400
        
        conv_manager.set_conversation_mode(conversation_id, mode, operator_id)
        
        return jsonify({
            "success": True,
            "message": f"Modo cambiado a {mode}"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@web_api.route('/api/messages/<message_id>', methods=['PUT'])
async def edit_message(message_id: str):
    """Edita un mensaje existente"""
    try:
        data = await request.get_json()
        new_content = data.get('content')
        
        if not new_content:
            return jsonify({
                "success": False,
                "error": "Contenido requerido"
            }), 400
        
        # Buscar el mensaje en todas las conversaciones
        for conversation in conv_manager.conversations.values():
            for message in conversation["messages"]:
                if message["id"] == message_id:
                    message["content"] = new_content
                    message["edited"] = True
                    
                    return jsonify({
                        "success": True,
                        "message": message
                    })
        
        return jsonify({
            "success": False,
            "error": "Mensaje no encontrado"
        }), 404
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@web_api.route('/api/quick-responses', methods=['GET'])
async def get_quick_responses():
    """Obtiene respuestas rápidas predefinidas"""
    quick_responses = [
        {
            "id": "1",
            "text": "Hola, ¿en qué puedo ayudarte?",
            "category": "greeting"
        },
        {
            "id": "2", 
            "text": "Gracias por contactarnos. Te responderemos pronto.",
            "category": "acknowledgment"
        },
        {
            "id": "3",
            "text": "¿Podrías proporcionar más detalles sobre tu consulta?",
            "category": "clarification"
        },
        {
            "id": "4",
            "text": "Para consultas sobre nómina, contacta a RRHH.",
            "category": "redirect"
        }
    ]
    
    return jsonify({
        "success": True,
        "quick_responses": quick_responses
    })

@web_api.route('/api/conversations/<conversation_id>/pending-response/approve', methods=['POST'])
async def approve_pending_response(conversation_id: str):
    """Aprueba una respuesta pendiente y la envía a WhatsApp"""
    try:
        conversation = conv_manager.get_conversation(conversation_id)
        if not conversation or not conversation.get("pending_response"):
            return jsonify({
                "success": False,
                "error": "Conversación no encontrada o sin respuesta pendiente"
            }), 404
        
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
        
        return jsonify({
            "success": True,
            "message": message
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@web_api.route('/api/conversations/<conversation_id>/pending-response/reject', methods=['POST'])
async def reject_pending_response(conversation_id: str):
    """Rechaza una respuesta pendiente"""
    try:
        conversation = conv_manager.get_conversation(conversation_id)
        if not conversation or not conversation.get("pending_response"):
            return jsonify({
                "success": False,
                "error": "Conversación no encontrada o sin respuesta pendiente"
            }), 404
        
        # Simplemente limpiar la respuesta pendiente
        conversation["pending_response"] = None
        
        return jsonify({
            "success": True,
            "message": "Respuesta rechazada"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@web_api.route('/api/conversations/<conversation_id>/pending-response/edit-and-approve', methods=['PUT'])
async def edit_and_approve_pending_response(conversation_id: str):
    """Edita una respuesta pendiente y la aprueba"""
    try:
        data = await request.get_json()
        new_content = data.get('content')
        
        if not new_content:
            return jsonify({
                "success": False,
                "error": "Contenido requerido"
            }), 400
        
        conversation = conv_manager.get_conversation(conversation_id)
        if not conversation or not conversation.get("pending_response"):
            return jsonify({
                "success": False,
                "error": "Conversación no encontrada o sin respuesta pendiente"
            }), 404
        
        # Agregar mensaje editado al chat
        message = conv_manager.add_message(
            conversation_id, 
            new_content, 
            "bot"
        )
        
        # Marcar como editado
        message["edited"] = True
        
        # Enviar a WhatsApp
        from main import send_whatsapp_message
        await send_whatsapp_message(
            conversation["user"]["phone"], 
            {"response": new_content}
        )
        
        # Limpiar respuesta pendiente
        conversation["pending_response"] = None
        
        return jsonify({
            "success": True,
            "message": message
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# Función para integrar mensajes de WhatsApp con el sistema web
def sync_whatsapp_message(phone_number: str, message_text: str, sender: str = "user"):
    """Sincroniza mensajes de WhatsApp con el sistema web"""
    # Buscar conversación existente por teléfono
    conversation = None
    for conv in conv_manager.conversations.values():
        if conv["user"]["phone"] == phone_number:
            conversation = conv
            break
    
    # Si no existe, crear nueva conversación
    if not conversation:
        # Obtener nombre del usuario (esto vendría de WhatsApp o base de datos)
        user_name = f"Usuario {phone_number[-4:]}"  # Fallback
        conversation = conv_manager.create_conversation(phone_number, user_name)
    
    # Agregar mensaje
    conv_manager.add_message(conversation["id"], message_text, sender)
    
    return conversation["id"] 