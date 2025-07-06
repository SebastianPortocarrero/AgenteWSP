from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
import time

class MessageSender(str, Enum):
    """Tipos de remitente de mensaje"""
    USER = "user"
    BOT = "bot"
    OPERATOR = "operator"

class MessageStatus(str, Enum):
    """Estados de mensaje"""
    SENT = "sent"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"

class ConversationStatus(str, Enum):
    """Estados de conversación"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"

class ConversationMode(str, Enum):
    """Modos de conversación"""
    AUTO = "auto"
    MANUAL = "manual"
    HYBRID = "hybrid"

class UserModel(BaseModel):
    """Modelo de usuario"""
    id: str
    name: str
    phone: str

class MessageModel(BaseModel):
    """Modelo de mensaje"""
    id: str
    content: str
    timestamp: float = Field(default_factory=time.time)
    sender: MessageSender
    edited: bool = False
    status: MessageStatus = MessageStatus.SENT

class ConversationModel(BaseModel):
    """Modelo de conversación"""
    id: str
    user: UserModel
    messages: List[MessageModel] = []
    status: ConversationStatus = ConversationStatus.PENDING
    mode: ConversationMode = ConversationMode.AUTO
    lastActivity: float = Field(default_factory=time.time)
    unreadCount: int = 0
    tags: List[str] = []
    assignedOperator: Optional[str] = None
    created_at: float = Field(default_factory=time.time)
    pending_response: Optional[str] = None

# Request Models
class SendMessageRequest(BaseModel):
    """Request para enviar mensaje"""
    content: str
    sender_mode: MessageSender = MessageSender.OPERATOR
    operator_id: str = "system"

class SetModeRequest(BaseModel):
    """Request para cambiar modo de conversación"""
    mode: ConversationMode
    operator_id: Optional[str] = None

class EditMessageRequest(BaseModel):
    """Request para editar mensaje"""
    content: str

class ApproveResponseRequest(BaseModel):
    """Request para aprobar respuesta"""
    operator_id: str = "system"

class RejectResponseRequest(BaseModel):
    """Request para rechazar respuesta"""
    operator_id: str = "system"
    reason: Optional[str] = None

class EditAndApproveRequest(BaseModel):
    """Request para editar y aprobar"""
    content: str
    operator_id: str = "system"

# Response Models
class ApiResponse(BaseModel):
    """Respuesta base de la API"""
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None

class ConversationsResponse(ApiResponse):
    """Respuesta para listar conversaciones"""
    conversations: Optional[List[ConversationModel]] = None

class ConversationResponse(ApiResponse):
    """Respuesta para una conversación específica"""
    conversation: Optional[ConversationModel] = None

class MessageResponse(ApiResponse):
    """Respuesta para operaciones de mensaje"""
    message: Optional[MessageModel] = None

class QuickResponsesResponse(ApiResponse):
    """Respuesta para respuestas rápidas"""
    quick_responses: Optional[List[str]] = None

class UserStatsModel(BaseModel):
    """Modelo para estadísticas de usuario"""
    user_id: str
    last_activity_minutes_ago: float
    has_orchestrator: bool
    is_active: bool

class UserStatsResponse(ApiResponse):
    """Respuesta para estadísticas de usuarios"""
    active_users: Optional[List[UserStatsModel]] = None
    total_users: Optional[int] = None

class HealthResponse(BaseModel):
    """Respuesta del health check"""
    status: str = "ok"
    uptime: Optional[float] = None
    version: Optional[str] = None

# Webhook Models
class WhatsAppWebhookEntry(BaseModel):
    """Modelo para entries del webhook de WhatsApp"""
    id: str
    changes: List[Dict[str, Any]]

class WhatsAppWebhookData(BaseModel):
    """Modelo para datos del webhook de WhatsApp"""
    object: str
    entry: List[WhatsAppWebhookEntry] 