import { Conversation, Message, QuickResponse } from '../types';

// Configuración de API con soporte para variables de entorno
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

class ApiService {
  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (!data.success) {
        throw new Error(data.error || 'API request failed');
      }
      
      return data;
    } catch (error) {
      console.error(`API request failed for ${endpoint}:`, error);
      throw error;
    }
  }

  // Conversaciones
  async getConversations(): Promise<Conversation[]> {
    const response = await this.request<{ conversations: any[] }>('/conversations');
    
    // Convertir timestamps de números a Date objects con validación
    return response.conversations.map(conv => ({
      ...conv,
      lastActivity: conv.lastActivity ? new Date(conv.lastActivity * 1000) : new Date(),
      messages: (conv.messages || []).map((msg: any) => ({
        ...msg,
        timestamp: msg.timestamp ? new Date(msg.timestamp * 1000) : new Date()
      }))
    }));
  }

  async getConversation(conversationId: string): Promise<Conversation> {
    const response = await this.request<{ conversation: any }>(`/conversations/${conversationId}`);
    
    // Convertir timestamps
    const conv = response.conversation;
    return {
      ...conv,
      lastActivity: new Date(conv.lastActivity * 1000),
      messages: conv.messages.map((msg: any) => ({
        ...msg,
        timestamp: new Date(msg.timestamp * 1000)
      }))
    };
  }

  async sendMessage(
    conversationId: string, 
    content: string, 
    senderMode: 'bot' | 'operator',
    operatorId: string = 'system'
  ): Promise<Message> {
    const response = await this.request<{ message: any }>(`/conversations/${conversationId}/messages`, {
      method: 'POST',
      body: JSON.stringify({
        conversation_id: conversationId,
        content,
        sender_mode: senderMode,
        operator_id: operatorId
      })
    });

    // Convertir timestamp
    return {
      ...response.message,
      timestamp: new Date(response.message.timestamp * 1000)
    };
  }

  async changeConversationMode(
    conversationId: string, 
    mode: 'auto' | 'manual' | 'hybrid',
    operatorId?: string
  ): Promise<void> {
    await this.request(`/conversations/${conversationId}/mode`, {
      method: 'PUT',
      body: JSON.stringify({
        mode,
        operator_id: operatorId
      })
    });
  }

  async markConversationAsRead(conversationId: string): Promise<void> {
    await this.request(`/conversations/${conversationId}/mark-read`, {
      method: 'POST'
    });
  }

  // Nuevos métodos para el modo híbrido
  async approvePendingResponse(conversationId: string): Promise<Message> {
    const response = await this.request<{ message: any }>(`/conversations/${conversationId}/approve-pending`, {
      method: 'POST'
    });

    return {
      ...response.message,
      timestamp: new Date(response.message.timestamp * 1000)
    };
  }

  async rejectPendingResponse(conversationId: string): Promise<void> {
    await this.request(`/conversations/${conversationId}/reject-pending`, {
      method: 'POST'
    });
  }

  async editAndApprovePendingResponse(conversationId: string, newContent: string): Promise<Message> {
    const response = await this.request<{ message: any }>(`/conversations/${conversationId}/edit-and-approve`, {
      method: 'POST',
      body: JSON.stringify({
        content: newContent
      })
    });

    return {
      ...response.message,
      timestamp: new Date(response.message.timestamp * 1000)
    };
  }

  async editMessage(messageId: string, newContent: string): Promise<Message> {
    const response = await this.request<{ message: any }>(`/messages/${messageId}`, {
      method: 'PUT',
      body: JSON.stringify({
        content: newContent
      })
    });

    return {
      ...response.message,
      timestamp: new Date(response.message.timestamp * 1000)
    };
  }

  // Respuestas rápidas
  async getQuickResponses(): Promise<QuickResponse[]> {
    const response = await this.request<{ quick_responses: QuickResponse[] }>('/quick-responses');
    return response.quick_responses;
  }

  // Health check
  async healthCheck(): Promise<{ status: string }> {
    const response = await fetch(`${API_BASE_URL}/health`);
    return response.json();
  }
}

export const apiService = new ApiService();
export default apiService; 