import React from 'react';
import { QuickResponse } from '../types';
import { MessageSquare } from 'lucide-react';

interface QuickResponsesProps {
  quickResponses: QuickResponse[];
  onSelectResponse: (text: string) => void;
}

const QuickResponses: React.FC<QuickResponsesProps> = ({ quickResponses, onSelectResponse }) => {
  const categories = Array.from(new Set(quickResponses.map(qr => qr.category)));

  return (
    <div className="bg-white border rounded-lg p-4">
      <h3 className="text-sm font-medium text-gray-700 mb-3 flex items-center">
        <MessageSquare className="w-4 h-4 mr-2" />
        Respuestas Rápidas
      </h3>
      <div className="space-y-3">
        {categories.map(category => (
          <div key={category}>
            <h4 className="text-xs font-medium text-gray-500 uppercase mb-2">{category}</h4>
            <div className="space-y-1">
              {quickResponses
                .filter(qr => qr.category === category)
                .map(response => (
                  <button
                    key={response.id}
                    onClick={() => onSelectResponse(response.text)}
                    className="w-full text-left text-sm p-2 rounded hover:bg-gray-50 text-gray-700 border border-transparent hover:border-gray-200 transition-all"
                  >
                    {response.text}
                  </button>
                ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default QuickResponses;