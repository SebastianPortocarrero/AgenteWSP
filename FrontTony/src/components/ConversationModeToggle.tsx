import React, { useState } from 'react';
import { Bot, User, Settings, Check } from 'lucide-react';

interface ConversationModeToggleProps {
  currentMode: 'auto' | 'manual';
  conversationId: string;
  onModeChange: (mode: 'auto' | 'manual') => void;
  disabled?: boolean;
}

const ConversationModeToggle: React.FC<ConversationModeToggleProps> = ({
  currentMode,
  conversationId,
  onModeChange,
  disabled = false
}) => {
  const [isChanging, setIsChanging] = useState(false);

  const handleModeChange = async (newMode: 'auto' | 'manual') => {
    if (isChanging || newMode === currentMode) return;
    
    setIsChanging(true);
    try {
      onModeChange(newMode);
    } finally {
      setIsChanging(false);
    }
  };

  const getModeIcon = (mode: 'auto' | 'manual') => {
    switch (mode) {
      case 'auto':
        return <Bot className="w-4 h-4" />;
      case 'manual':
        return <User className="w-4 h-4" />;
      default:
        return null;
    }
  };

  const getModeColor = (mode: 'auto' | 'manual', isActive: boolean) => {
    const baseClasses = "flex items-center space-x-2 px-3 py-2 rounded-lg border transition-all duration-200";
    
    if (isActive) {
      switch (mode) {
        case 'auto':
          return `${baseClasses} bg-blue-500 text-white border-blue-500`;
        case 'manual':
          return `${baseClasses} bg-green-500 text-white border-green-500`;
        default:
          return baseClasses;
      }
    } else {
      return `${baseClasses} bg-white text-gray-700 border-gray-300 hover:border-gray-400 hover:bg-gray-50`;
    }
  };

  const getModeLabel = (mode: 'auto' | 'manual') => {
    switch (mode) {
      case 'auto':
        return 'Bot';
      case 'manual':
        return 'Persona';
      default:
        return '';
    }
  };

  const getModeDescription = (mode: 'auto' | 'manual') => {
    switch (mode) {
      case 'auto':
        return 'El AI responde automáticamente';
      case 'manual':
        return 'Solo el operador puede responder';
      default:
        return '';
    }
  };

  return (
    <div className="bg-white rounded-lg border p-4 mb-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-medium text-gray-900">Modo de Conversación</h3>
        <div className="flex items-center space-x-1">
          {getModeIcon(currentMode)}
          <span className="text-sm text-gray-600">{getModeLabel(currentMode)}</span>
        </div>
      </div>
      
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {(['auto', 'manual'] as const).map((mode) => (
          <button
            key={mode}
            onClick={() => handleModeChange(mode)}
            disabled={disabled || isChanging}
            className={`${getModeColor(mode, currentMode === mode)} ${
              disabled || isChanging ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'
            }`}
          >
            <div className="flex items-center space-x-2">
              {getModeIcon(mode)}
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium">{getModeLabel(mode)}</div>
                <div className="text-xs opacity-75">{getModeDescription(mode)}</div>
              </div>
              {currentMode === mode && (
                <Check className="w-4 h-4 flex-shrink-0" />
              )}
            </div>
          </button>
        ))}
      </div>
      
      {isChanging && (
        <div className="mt-3 text-center">
          <div className="inline-flex items-center text-sm text-gray-600">
            <div className="animate-spin mr-2 h-4 w-4 border-2 border-gray-300 border-t-blue-500 rounded-full"></div>
            Cambiando modo...
          </div>
        </div>
      )}
    </div>
  );
};

export default ConversationModeToggle; 