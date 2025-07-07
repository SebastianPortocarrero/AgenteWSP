import { MessageCircle, User } from 'lucide-react';
import { Conversation } from '../types';

interface ConversationListProps {
  conversations: Conversation[];
  selectedConversation?: string;
  onSelectConversation: (id: string) => void;
  searchTerm: string;
}

const ConversationList = ({
  conversations,
  selectedConversation,
  onSelectConversation,
}: ConversationListProps) => {
  // Validación defensiva
  const safeConversations = Array.isArray(conversations) ? conversations : [];

  const formatTime = (date: Date) => {
    if (!date || !(date instanceof Date)) return '';
    
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const diffDays = Math.floor(diff / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) {
      return date.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' });
    } else if (diffDays === 1) {
      return 'Ayer';
    } else if (diffDays < 7) {
      return date.toLocaleDateString('es-ES', { weekday: 'short' });
    } else {
      return date.toLocaleDateString('es-ES', { day: '2-digit', month: '2-digit' });
    }
  };

  const getLastMessage = (conversation: Conversation) => {
    if (!conversation?.messages || !Array.isArray(conversation.messages) || conversation.messages.length === 0) {
      return 'Sin mensajes';
    }
    
    const lastMessage = conversation.messages[conversation.messages.length - 1];
    if (!lastMessage || !lastMessage.content) return 'Sin mensajes';
    
    const prefix = lastMessage.sender === 'user' ? '' : 
                  lastMessage.sender === 'bot' ? '🤖 ' : '👤 ';
    
    return prefix + (lastMessage.content.length > 50 
      ? lastMessage.content.substring(0, 50) + '...' 
      : lastMessage.content);
  };

  const getUserInitials = (name: string) => {
    if (!name || typeof name !== 'string') return '?';
    return name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
  };

  const getAvatarColor = (name: string) => {
    const colors = [
      'bg-red-500', 'bg-blue-500', 'bg-green-500', 'bg-yellow-500', 
      'bg-purple-500', 'bg-pink-500', 'bg-indigo-500', 'bg-teal-500'
    ];
    if (!name || typeof name !== 'string') return colors[0];
    const hash = name.split('').reduce((a, b) => a + b.charCodeAt(0), 0);
    return colors[hash % colors.length];
  };

  if (safeConversations.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        <div className="text-center">
          <MessageCircle className="w-12 h-12 mx-auto mb-3 text-gray-300" />
          <p className="text-sm">No hay conversaciones</p>
        </div>
      </div>
    );
  }

  return (
    <div className="divide-y divide-gray-100">
      {safeConversations.map((conversation) => {
        if (!conversation || !conversation.id) return null;
        
        const userName = conversation.user?.name || 'Usuario desconocido';
        const userInitials = getUserInitials(userName);
        const avatarColor = getAvatarColor(userName);
        const lastActivity = conversation.lastActivity || new Date();
        const unreadCount = conversation.unreadCount || 0;
        const status = conversation.status || 'active';
        const mode = conversation.mode || 'auto';
        const tags = Array.isArray(conversation.tags) ? conversation.tags : [];
        const assignedOperator = conversation.assignedOperator;

        return (
          <div
            key={conversation.id}
            onClick={() => onSelectConversation(conversation.id)}
            className={`p-4 cursor-pointer transition-all duration-200 hover:bg-gray-50 dark:hover:bg-gray-800 relative ${
              selectedConversation === conversation.id 
                ? 'bg-green-50 border-r-4 border-green-500' 
                : ''
            }`}
          >
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0">
                <div className={`w-12 h-12 rounded-full flex items-center justify-center text-white font-medium text-sm ${avatarColor}`}>
                  {userInitials}
                </div>
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-1">
                  <h3 className={`font-medium truncate ${
                    selectedConversation === conversation.id
                      ? 'text-green-700 dark:text-green-400'
                      : 'text-gray-900 dark:text-gray-200'
                  }`}>
                    {userName}
                  </h3>
                  <div className="flex items-center space-x-2 ml-2">
                    <span className={`text-xs ${
                      unreadCount > 0 ? 'text-green-600 font-medium' : 'text-gray-500'
                    }`}>
                      {formatTime(lastActivity)}
                    </span>
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <p className={`text-sm truncate ${
                    unreadCount > 0 ? 'text-gray-600 font-medium' : 'text-gray-500'
                  }`}>
                    {getLastMessage(conversation)}
                  </p>
                  
                  <div className="flex items-center space-x-1 ml-2">
                    {unreadCount > 0 && (
                      <span className="bg-green-500 text-white text-xs font-medium px-2 py-1 rounded-full min-w-[20px] text-center">
                        {unreadCount > 99 ? '99+' : unreadCount}
                      </span>
                    )}
                  </div>
                </div>

                <div className="flex items-center justify-between mt-2">
                  <div className="flex items-center space-x-1">
                    {tags.slice(0, 2).map((tag, index) => (
                      <span
                        key={index}
                        className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded-full"
                      >
                        {tag}
                      </span>
                    ))}
                    {tags.length > 2 && (
                      <span className="text-xs text-gray-400">
                        +{tags.length - 2}
                      </span>
                    )}
                  </div>

                  <div className="flex items-center space-x-1">
                    <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                      mode === 'auto' 
                        ? 'bg-blue-100 text-blue-700' 
                        : 'bg-green-100 text-green-700'
                    }`}>
                      {mode === 'auto' ? '🤖' : '👤'}
                    </span>

                    <div className={`w-3 h-3 rounded-full border-2 ${
                      status === 'pending' ? 'bg-orange-400 border-orange-200' :
                      status === 'in_progress' ? 'bg-blue-400 border-blue-200' :
                      'bg-green-400 border-green-200'
                    }`} title={
                      status === 'pending' ? 'Pendiente' :
                      status === 'in_progress' ? 'En progreso' :
                      'Cerrado'
                    }></div>
                  </div>
                </div>

                {assignedOperator && (
                  <div className="mt-2 flex items-center text-xs text-gray-500">
                    <User className="w-3 h-3 mr-1" />
                    <span>Atendido por {assignedOperator}</span>
                  </div>
                )}
              </div>
            </div>

            {selectedConversation === conversation.id && (
              <div className="absolute right-0 top-1/2 transform -translate-y-1/2 w-1 h-8 bg-green-500 rounded-l"></div>
            )}
          </div>
        );
      })}
    </div>
  );
};

export default ConversationList;