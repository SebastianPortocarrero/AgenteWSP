import React, { useState } from 'react';
import { Check, X, Edit3, AlertTriangle, Bot } from 'lucide-react';
import { PendingResponse } from '../types';

interface PendingResponseCardProps {
  conversationId: string;
  pendingResponse: PendingResponse;
  onApprove: () => void;
  onReject: () => void;
  onEditAndApprove: (newContent: string) => void;
  isLoading?: boolean;
}

const PendingResponseCard: React.FC<PendingResponseCardProps> = ({
  conversationId,
  pendingResponse,
  onApprove,
  onReject,
  onEditAndApprove,
  isLoading = false
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editedContent, setEditedContent] = useState(pendingResponse.content);

  const handleEditAndApprove = () => {
    if (editedContent.trim()) {
      onEditAndApprove(editedContent.trim());
      setIsEditing(false);
    }
  };

  const handleCancelEdit = () => {
    setEditedContent(pendingResponse.content);
    setIsEditing(false);
  };

  return (
    <div className="bg-gradient-to-r from-purple-50 to-blue-50 border-2 border-purple-200 rounded-lg p-4 mb-4 shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          <div className="p-1.5 bg-purple-100 rounded-full">
            <Bot className="w-4 h-4 text-purple-600" />
          </div>
          <div>
            <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100">
              🤖👤 Respuesta Sugerida por IA
            </h3>
            <p className="text-xs text-gray-500">
              {pendingResponse.is_error ? 'Error generando respuesta' : 'Pendiente de aprobación'}
            </p>
          </div>
        </div>
        
        {pendingResponse.is_error && (
          <div className="flex items-center text-amber-600">
            <AlertTriangle className="w-4 h-4 mr-1" />
            <span className="text-xs">Error</span>
          </div>
        )}
      </div>

      {/* Content */}
      <div className="mb-4">
        {isEditing ? (
          <div className="space-y-3">
            <textarea
              value={editedContent}
              onChange={(e) => setEditedContent(e.target.value)}
              className="w-full p-3 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent text-sm"
              rows={4}
              placeholder="Edita la respuesta..."
            />
            <div className="flex items-center justify-end space-x-2">
              <button
                onClick={handleCancelEdit}
                disabled={isLoading}
                className="px-3 py-1.5 text-xs text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-md transition-colors"
              >
                Cancelar
              </button>
              <button
                onClick={handleEditAndApprove}
                disabled={isLoading || !editedContent.trim()}
                className="px-3 py-1.5 text-xs bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isLoading ? 'Enviando...' : 'Aprobar Editado'}
              </button>
            </div>
          </div>
        ) : (
          <div className="bg-white dark:bg-gray-800 p-3 rounded-lg border border-purple-100 dark:border-purple-700">
            <p className="text-sm text-gray-800 whitespace-pre-wrap">
              {pendingResponse.content}
            </p>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      {!isEditing && (
        <div className="flex items-center justify-between">
          <div className="text-xs text-gray-500">
            💡 Esta respuesta NO se ha enviado a WhatsApp todavía
          </div>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={onReject}
              disabled={isLoading}
              className="flex items-center space-x-1 px-3 py-1.5 text-xs text-red-600 hover:text-red-700 hover:bg-red-50 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <X className="w-3 h-3" />
              <span>Rechazar</span>
            </button>
            
            <button
              onClick={() => setIsEditing(true)}
              disabled={isLoading}
              className="flex items-center space-x-1 px-3 py-1.5 text-xs text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Edit3 className="w-3 h-3" />
              <span>Editar</span>
            </button>
            
            <button
              onClick={onApprove}
              disabled={isLoading}
              className="flex items-center space-x-1 px-3 py-1.5 text-xs bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Check className="w-3 h-3" />
              <span>{isLoading ? 'Enviando...' : 'Aprobar y Enviar'}</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default PendingResponseCard; 