import React, { useState } from 'react';
import { Bot, User, Check, GitMerge } from 'lucide-react';

interface ConversationModeToggleProps {
  currentMode: 'auto' | 'manual' | 'hybrid';
  conversationId: string;
  onModeChange: (mode: 'auto' | 'manual' | 'hybrid') => void;
  disabled?: boolean;
}

const ConversationModeToggle: React.FC<ConversationModeToggleProps> = ({
  currentMode,
  conversationId,
  onModeChange,
  disabled = false
}) => {
  const [isChanging, setIsChanging] = useState(false);

  const handleModeChange = async (newMode: 'auto' | 'manual' | 'hybrid') => {
    if (isChanging || newMode === currentMode) return;
    
    setIsChanging(true);
    try {
      onModeChange(newMode);
    } finally {
      setIsChanging(false);
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100">¿Quién responde en este chat?</h3>
        <div className={`px-2 py-1 rounded-full text-xs font-medium ${
          currentMode === 'auto' 
            ? 'bg-blue-100 text-blue-700' 
            : currentMode === 'manual'
            ? 'bg-green-100 text-green-700'
            : 'bg-purple-100 text-purple-700'
        }`}>
          {currentMode === 'auto' 
            ? '🤖 Bot activo' 
            : currentMode === 'manual'
            ? '👤 Operador activo'
            : '🤖👤 Híbrido activo'
          }
        </div>
      </div>
      
      <div className="space-y-2">
        {/* Modo Bot */}
        <button
          onClick={() => handleModeChange('auto')}
          disabled={disabled || isChanging}
          className={`w-full flex items-center justify-between p-3 rounded-lg border transition-all duration-200 ${
            currentMode === 'auto'
              ? 'bg-blue-50 border-blue-500 text-blue-700'
              : 'bg-white border-gray-200 text-gray-700 hover:border-gray-300 hover:bg-gray-50'
          } ${disabled || isChanging ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
        >
          <div className="flex items-center space-x-3">
            <div className={`p-2 rounded-full ${
              currentMode === 'auto' ? 'bg-blue-100' : 'bg-gray-100'
            }`}>
              <Bot className="w-4 h-4" />
            </div>
            <div className="text-left">
              <div className="font-medium text-sm">🤖 Modo Bot</div>
              <div className="text-xs opacity-75">El AI responde automáticamente por WhatsApp</div>
            </div>
          </div>
          {currentMode === 'auto' && <Check className="w-5 h-5" />}
        </button>

        {/* Modo Manual */}
        <button
          onClick={() => handleModeChange('manual')}
          disabled={disabled || isChanging}
          className={`w-full flex items-center justify-between p-3 rounded-lg border transition-all duration-200 ${
            currentMode === 'manual'
              ? 'bg-green-50 border-green-500 text-green-700'
              : 'bg-white border-gray-200 text-gray-700 hover:border-gray-300 hover:bg-gray-50'
          } ${disabled || isChanging ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
        >
          <div className="flex items-center space-x-3">
            <div className={`p-2 rounded-full ${
              currentMode === 'manual' ? 'bg-green-100' : 'bg-gray-100'
            }`}>
              <User className="w-4 h-4" />
            </div>
            <div className="text-left">
              <div className="font-medium text-sm">👤 Modo Operador</div>
              <div className="text-xs opacity-75">Solo operadores responden desde esta web</div>
            </div>
          </div>
          {currentMode === 'manual' && <Check className="w-5 h-5" />}
        </button>

        {/* Modo Híbrido */}
        <button
          onClick={() => handleModeChange('hybrid')}
          disabled={disabled || isChanging}
          className={`w-full flex items-center justify-between p-3 rounded-lg border transition-all duration-200 ${
            currentMode === 'hybrid'
              ? 'bg-purple-50 border-purple-500 text-purple-700'
              : 'bg-white border-gray-200 text-gray-700 hover:border-gray-300 hover:bg-gray-50'
          } ${disabled || isChanging ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
        >
          <div className="flex items-center space-x-3">
            <div className={`p-2 rounded-full ${
              currentMode === 'hybrid' ? 'bg-purple-100' : 'bg-gray-100'
            }`}>
              <GitMerge className="w-4 h-4" />
            </div>
            <div className="text-left">
              <div className="font-medium text-sm">🤖👤 Modo Híbrido</div>
              <div className="text-xs opacity-75">Bot genera respuesta, operador la aprueba</div>
            </div>
          </div>
          {currentMode === 'hybrid' && <Check className="w-5 h-5" />}
        </button>
      </div>
      
      {/* Estado de cambio */}
      {isChanging && (
        <div className="mt-3 text-center">
          <div className="inline-flex items-center text-sm text-gray-600">
            <div className="animate-spin mr-2 h-4 w-4 border-2 border-gray-300 border-t-blue-500 rounded-full"></div>
            Cambiando modo...
          </div>
        </div>
      )}

      {/* Información adicional */}
      <div className="mt-4 p-3 bg-gray-50 rounded-lg">
        <p className="text-xs text-gray-600">
          {currentMode === 'auto' 
            ? '💡 En modo Bot: Los mensajes de WhatsApp se responden automáticamente. Puedes editar las respuestas desde aquí.'
            : currentMode === 'manual'
            ? '💡 En modo Operador: El Bot no responderá automáticamente. Solo tú puedes enviar mensajes desde esta web.'
            : '💡 En modo Híbrido: El Bot genera respuestas automáticamente pero NO las envía. Tú debes aprobarlas antes de enviar a WhatsApp.'
          }
        </p>
      </div>
    </div>
  );
};

export default ConversationModeToggle; 