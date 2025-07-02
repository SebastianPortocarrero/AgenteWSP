import React from 'react';
import { SenderMode } from '../types';
import { Bot, User } from 'lucide-react';

interface SenderModeToggleProps {
  mode: SenderMode;
  onModeChange: (mode: SenderMode) => void;
}

const SenderModeToggle: React.FC<SenderModeToggleProps> = ({ mode, onModeChange }) => {
  return (
    <div className="bg-white border rounded-lg p-4">
      <h3 className="text-sm font-medium text-gray-700 mb-3">Responder como:</h3>
      <div className="flex space-x-2">
        <button
          onClick={() => onModeChange('bot')}
          className={`flex items-center space-x-2 px-4 py-2 rounded-lg border transition-all ${
            mode === 'bot'
              ? 'bg-blue-50 border-blue-500 text-blue-700'
              : 'bg-gray-50 border-gray-200 text-gray-600 hover:bg-gray-100'
          }`}
        >
          <Bot className="w-4 h-4" />
          <span className="text-sm font-medium">Bot</span>
        </button>
        <button
          onClick={() => onModeChange('operator')}
          className={`flex items-center space-x-2 px-4 py-2 rounded-lg border transition-all ${
            mode === 'operator'
              ? 'bg-green-50 border-green-500 text-green-700'
              : 'bg-gray-50 border-gray-200 text-gray-600 hover:bg-gray-100'
          }`}
        >
          <User className="w-4 h-4" />
          <span className="text-sm font-medium">Operador</span>
        </button>
      </div>
    </div>
  );
};

export default SenderModeToggle;