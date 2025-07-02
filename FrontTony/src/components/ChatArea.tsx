import React, { useState, useRef, useEffect } from 'react';
import { Conversation, Message, SenderMode } from '../types';
import { Bot, User, Edit3, Send, Check, Clock } from 'lucide-react';

interface ChatAreaProps {
  conversation: Conversation | null;
  senderMode: SenderMode;
  onSendMessage: (content: string, sender: SenderMode) => void;
  onEditMessage: (messageId: string, newContent: string) => void;
}

const ChatArea: React.FC<ChatAreaProps> = ({
  conversation,
  senderMode,
  onSendMessage,
  onEditMessage
}) => {
  const [newMessage, setNewMessage] = useState('');
  const [editingMessage, setEditingMessage] = useState<string | null>(null);
  const [editContent, setEditContent] = useState('');
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

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('es-ES', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const getSenderIcon = (sender: string) => {
    switch (sender) {
      case 'bot':
        return <Bot className="w-4 h-4" />;
      case 'operator':
        return <User className="w-4 h-4" />;
      default:
        return null;
    }
  };

  const getSenderColor = (sender: string) => {
    switch (sender) {
      case 'user':
        return 'bg-gray-100 text-gray-900';
      case 'bot':
        return 'bg-blue-500 text-white';
      case 'operator':
        return 'bg-green-500 text-white';
      default:
        return 'bg-gray-100 text-gray-900';
    }
  };

  const getStatusIcon = (status?: string) => {
    switch (status) {
      case 'sent':
        return <Check className="w-3 h-3 text-gray-400" />;
      case 'delivered':
        return <Check className="w-3 h-3 text-blue-400" />;
      case 'read':
        return <Check className="w-3 h-3 text-green-400" />;
      default:
        return <Clock className="w-3 h-3 text-gray-300" />;
    }
  };

  if (!conversation) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500">
        <div className="text-center">
          <Bot className="w-16 h-16 mx-auto mb-4 text-gray-300" />
          <p className="text-lg">Selecciona una conversación para comenzar</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="bg-white border-b px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="w-10 h-10 bg-gray-300 rounded-full flex items-center justify-center">
              <User className="w-5 h-5 text-gray-600" />
            </div>
            <div>
              <h2 className="font-semibold text-gray-900">{conversation.user.name}</h2>
              <p className="text-sm text-gray-500">
                {conversation.assignedOperator && `Atendido por: ${conversation.assignedOperator}`}
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <span className={`px-3 py-1 rounded-full text-xs font-medium ${
              conversation.status === 'pending' ? 'bg-orange-100 text-orange-800' :
              conversation.status === 'in_progress' ? 'bg-blue-100 text-blue-800' :
              'bg-green-100 text-green-800'
            }`}>
              {conversation.status.replace('_', ' ')}
            </span>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {conversation.messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.sender === 'user' ? 'justify-start' : 'justify-end'}`}
          >
            <div className={`max-w-xs lg:max-w-md ${message.sender === 'user' ? 'order-1' : 'order-2'}`}>
              <div className={`rounded-lg px-4 py-2 ${getSenderColor(message.sender)}`}>
                {editingMessage === message.id ? (
                  <div className="space-y-2">
                    <textarea
                      value={editContent}
                      onChange={(e) => setEditContent(e.target.value)}
                      placeholder="Editar mensaje..."
                      className="w-full p-2 border rounded text-gray-900 text-sm"
                      rows={3}
                    />
                    <div className="flex space-x-2">
                      <button
                        type="button"
                        onClick={handleSaveEdit}
                        className="bg-green-500 text-white px-3 py-1 rounded text-xs hover:bg-green-600"
                      >
                        Guardar
                      </button>
                      <button
                        type="button"
                        onClick={handleCancelEdit}
                        className="bg-gray-500 text-white px-3 py-1 rounded text-xs hover:bg-gray-600"
                      >
                        Cancelar
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="relative group">
                    <p className="text-sm">{message.content}</p>
                    {message.sender !== 'user' && (
                      <button
                        type="button"
                        title="Editar mensaje"
                        onClick={() => handleEditMessage(message.id, message.content)}
                        className="absolute -right-8 top-1 opacity-0 group-hover:opacity-100 transition-opacity bg-white rounded-full p-1 shadow-md"
                      >
                        <Edit3 className="w-3 h-3 text-gray-600" />
                      </button>
                    )}
                  </div>
                )}
              </div>
              <div className={`flex items-center mt-1 space-x-2 ${
                message.sender === 'user' ? 'justify-start' : 'justify-end'
              }`}>
                {message.sender !== 'user' && (
                  <div className="flex items-center space-x-1">
                    {getSenderIcon(message.sender)}
                    <span className="text-xs text-gray-500 capitalize">{message.sender}</span>
                  </div>
                )}
                <span className="text-xs text-gray-500">{formatTime(message.timestamp)}</span>
                {message.edited && (
                  <span className="text-xs text-gray-400">(editado)</span>
                )}
                {message.status && getStatusIcon(message.status)}
              </div>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="bg-white border-t p-4">
        <div className="flex items-end space-x-4">
          <div className="flex-1">
            <textarea
              value={newMessage}
              onChange={(e) => setNewMessage(e.target.value)}
              placeholder={`Escribir como ${senderMode === 'bot' ? 'Bot' : 'Operador'}...`}
              className="w-full p-3 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={2}
              onKeyPress={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
            />
          </div>
          <button
            type="button"
            title="Enviar mensaje"
            onClick={handleSendMessage}
            disabled={!newMessage.trim()}
            className="bg-blue-500 text-white p-3 rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatArea;