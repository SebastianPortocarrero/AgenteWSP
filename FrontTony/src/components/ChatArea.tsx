import React, { useState, useRef, useEffect } from 'react';
import { Conversation, Message, SenderMode } from '../types';
import { Bot, User, Edit3, Send, Check, Clock, CheckCheck, Smile, Paperclip } from 'lucide-react';
import EmojiPicker from './EmojiPicker';
import FileUpload from './FileUpload';
import PendingResponseCard from './PendingResponseCard';

interface ChatAreaProps {
  conversation: Conversation | null;
  senderMode: SenderMode;
  onSendMessage: (content: string, sender: SenderMode) => void;
  onEditMessage: (messageId: string, newContent: string) => void;
  onApprovePendingResponse?: (conversationId: string) => void;
  onRejectPendingResponse?: (conversationId: string) => void;
  onEditAndApprovePendingResponse?: (conversationId: string, newContent: string) => void;
  isLoadingPendingResponse?: boolean;
}

const ChatArea: React.FC<ChatAreaProps> = ({
  conversation,
  senderMode,
  onSendMessage,
  onEditMessage,
  onApprovePendingResponse,
  onRejectPendingResponse,
  onEditAndApprovePendingResponse,
  isLoadingPendingResponse = false
}) => {
  const [newMessage, setNewMessage] = useState('');
  const [editingMessage, setEditingMessage] = useState<string | null>(null);
  const [editContent, setEditContent] = useState('');
  const [showEmojiPicker, setShowEmojiPicker] = useState(false);
  const [showFileUpload, setShowFileUpload] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [conversation?.messages]);

  const handleSendMessage = () => {
    if (newMessage.trim()) {
      onSendMessage(newMessage.trim(), senderMode);
      setNewMessage('');
    }
  };

  const handleEditMessage = (messageId: string, content: string) => {
    setEditingMessage(messageId);
    setEditContent(content);
  };

  const handleSaveEdit = () => {
    if (editingMessage && editContent.trim()) {
      onEditMessage(editingMessage, editContent.trim());
      setEditingMessage(null);
      setEditContent('');
    }
  };

  const handleCancelEdit = () => {
    setEditingMessage(null);
    setEditContent('');
  };

  const handleEmojiSelect = (emoji: string) => {
    setNewMessage(prev => prev + emoji);
    setShowEmojiPicker(false);
  };

  const handleFileSelect = (file: File, type: 'image' | 'document' | 'other') => {
    // Crear un mensaje con información del archivo
    const fileMessage = type === 'image' 
      ? `📷 Imagen: ${file.name}`
      : type === 'document'
      ? `📄 Documento: ${file.name}`
      : `📎 Archivo: ${file.name}`;
    
    onSendMessage(fileMessage, senderMode);
    setShowFileUpload(false);
    
    // Aquí podrías implementar la lógica para subir el archivo al servidor
    console.log('Archivo seleccionado:', file, 'Tipo:', type);
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('es-ES', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const getSenderIcon = (sender: string) => {
    switch (sender) {
      case 'bot':
        return <Bot className="w-3 h-3" />;
      case 'operator':
        return <User className="w-3 h-3" />;
      default:
        return null;
    }
  };

  const getMessageStyle = (sender: string) => {
    switch (sender) {
      case 'user':
        return 'bg-white border border-gray-200 text-gray-900 ml-12';
      case 'bot':
        return 'bg-blue-500 text-white mr-12';
      case 'operator':
        return 'bg-green-500 text-white mr-12';
      default:
        return 'bg-gray-100 text-gray-900';
    }
  };

  const getStatusIcon = (status?: string) => {
    switch (status) {
      case 'sent':
        return <Check className="w-3 h-3 text-gray-400" />;
      case 'delivered':
        return <CheckCheck className="w-3 h-3 text-gray-400" />;
      case 'read':
        return <CheckCheck className="w-3 h-3 text-blue-400" />;
      default:
        return <Clock className="w-3 h-3 text-gray-300" />;
    }
  };

  // Cerrar popups cuando se hace click fuera
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Element;
      if (!target.closest('.emoji-picker-container') && !target.closest('.emoji-button')) {
        setShowEmojiPicker(false);
      }
      if (!target.closest('.file-upload-container') && !target.closest('.file-button')) {
        setShowFileUpload(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  if (!conversation) {
    return (
      <div className="flex items-center justify-center h-full bg-gray-50">
        <div className="text-center">
          <Bot className="w-16 h-16 mx-auto mb-4 text-gray-300" />
          <p className="text-lg text-gray-500">Selecciona una conversación para comenzar</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* Área de mensajes */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3" style={{
        backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23f0f0f0' fill-opacity='0.1'%3E%3Ccircle cx='30' cy='30' r='2'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`
      }}>
        {conversation.messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.sender === 'user' ? 'justify-start' : 'justify-end'}`}
          >
            <div className={`max-w-lg ${message.sender === 'user' ? 'order-1' : 'order-2'}`}>
              <div className={`rounded-lg px-4 py-2 shadow-sm relative group ${getMessageStyle(message.sender)}`}>
                {editingMessage === message.id ? (
                  <div className="space-y-3">
                    <textarea
                      value={editContent}
                      onChange={(e) => setEditContent(e.target.value)}
                      placeholder="Editar mensaje..."
                      className="w-full p-3 border border-gray-300 rounded-lg text-gray-900 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-green-500"
                      rows={3}
                    />
                    <div className="flex space-x-2">
                      <button
                        type="button"
                        onClick={handleSaveEdit}
                        className="bg-green-500 text-white px-3 py-1 rounded-lg text-xs hover:bg-green-600 transition-colors"
                      >
                        Guardar
                      </button>
                      <button
                        type="button"
                        onClick={handleCancelEdit}
                        className="bg-gray-500 text-white px-3 py-1 rounded-lg text-xs hover:bg-gray-600 transition-colors"
                      >
                        Cancelar
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="relative">
                    <p className="text-sm leading-relaxed">{message.content}</p>
                    {message.sender !== 'user' && (
                      <button
                        type="button"
                        title="Editar mensaje"
                        onClick={() => handleEditMessage(message.id, message.content)}
                        className="absolute -right-2 -top-2 opacity-0 group-hover:opacity-100 transition-opacity bg-white rounded-full p-1 shadow-md border border-gray-200"
                      >
                        <Edit3 className="w-3 h-3 text-gray-600" />
                      </button>
                    )}
                  </div>
                )}
              </div>
              
              {/* Información del mensaje */}
              <div className={`flex items-center mt-1 space-x-2 text-xs ${
                message.sender === 'user' ? 'justify-start' : 'justify-end'
              }`}>
                {message.sender !== 'user' && (
                  <div className="flex items-center space-x-1 text-gray-500">
                    {getSenderIcon(message.sender)}
                    <span className="capitalize">
                      {message.sender === 'bot' ? 'Bot' : 'Operador'}
                    </span>
                  </div>
                )}
                <span className="text-gray-500">{formatTime(message.timestamp)}</span>
                {message.edited && (
                  <span className="text-gray-400">(editado)</span>
                )}
                {message.sender !== 'user' && message.status && (
                  <div className="flex items-center">
                    {getStatusIcon(message.status)}
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Respuesta Pendiente (Modo Híbrido) */}
      {conversation.pending_response && (
        <div className="px-4 pb-2">
          <PendingResponseCard
            conversationId={conversation.id}
            pendingResponse={conversation.pending_response}
            onApprove={() => onApprovePendingResponse?.(conversation.id)}
            onReject={() => onRejectPendingResponse?.(conversation.id)}
            onEditAndApprove={(newContent) => onEditAndApprovePendingResponse?.(conversation.id, newContent)}
            isLoading={isLoadingPendingResponse}
          />
        </div>
      )}

      {/* Área de input */}
      <div className="bg-white border-t border-gray-200 p-4">
        <div className="flex items-end space-x-3">
          {/* Botón de archivos adjuntos */}
          <div className="relative file-upload-container">
            <button
              type="button"
              title="Adjuntar archivo"
              className={`file-button p-3 rounded-full transition-colors ${
                showFileUpload 
                  ? 'text-green-600 bg-green-100' 
                  : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
              }`}
              onClick={() => {
                setShowFileUpload(!showFileUpload);
                setShowEmojiPicker(false);
              }}
            >
              <Paperclip className="w-5 h-5" />
            </button>
            
            {showFileUpload && (
              <FileUpload
                onFileSelect={handleFileSelect}
                onClose={() => setShowFileUpload(false)}
              />
            )}
          </div>

          {/* Input de mensaje */}
          <div className="flex-1 bg-gray-50 rounded-lg border border-gray-200 focus-within:border-green-500 transition-colors">
            <textarea
              value={newMessage}
              onChange={(e) => setNewMessage(e.target.value)}
              placeholder={`Escribir como ${senderMode === 'bot' ? 'Bot' : 'Operador'}...`}
              className="w-full p-3 bg-transparent resize-none focus:outline-none text-sm max-h-32"
              rows={1}
              onKeyPress={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
              style={{ minHeight: '44px' }}
            />
          </div>

          {/* Botón de emoji */}
          <div className="relative emoji-picker-container">
            <button
              type="button"
              title="Emoji"
              className={`emoji-button p-3 rounded-full transition-colors ${
                showEmojiPicker 
                  ? 'text-green-600 bg-green-100' 
                  : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
              }`}
              onClick={() => {
                setShowEmojiPicker(!showEmojiPicker);
                setShowFileUpload(false);
              }}
            >
              <Smile className="w-5 h-5" />
            </button>
            
            {showEmojiPicker && (
              <EmojiPicker
                onEmojiSelect={handleEmojiSelect}
                onClose={() => setShowEmojiPicker(false)}
              />
            )}
          </div>

          {/* Botón de enviar */}
          <button
            type="button"
            title="Enviar mensaje"
            onClick={handleSendMessage}
            disabled={!newMessage.trim()}
            className={`p-3 rounded-full transition-all ${
              newMessage.trim() 
                ? 'bg-green-500 text-white hover:bg-green-600 shadow-lg' 
                : 'bg-gray-200 text-gray-400 cursor-not-allowed'
            }`}
          >
            <Send className="w-5 h-5" />
          </button>
        </div>

        {/* Indicador de modo */}
        <div className="mt-2 flex items-center justify-center">
          <span className={`text-xs px-3 py-1 rounded-full ${
            senderMode === 'bot' 
              ? 'bg-blue-100 text-blue-700' 
              : 'bg-green-100 text-green-700'
          }`}>
            {senderMode === 'bot' 
              ? '🤖 Modo Bot - El AI responde automáticamente' 
              : '👤 Modo Operador - Solo tú puedes responder'
            }
          </span>
        </div>
      </div>
    </div>
  );
};

export default ChatArea;