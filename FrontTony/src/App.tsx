import React, { useState, useCallback, useEffect } from 'react';
import { MessageCircle, Settings, Bell, Menu, X, Wifi, WifiOff, LogOut } from 'lucide-react';
import ConversationList from './components/ConversationList';
import ChatArea from './components/ChatArea';
import SenderModeToggle from './components/SenderModeToggle';
import ConversationModeToggle from './components/ConversationModeToggle';
import QuickResponses from './components/QuickResponses';
import SearchAndFilters from './components/SearchAndFilters';
import NotificationPanel from './components/NotificationPanel';
import SettingsPanel from './components/SettingsPanel';
import LoginForm from './components/LoginForm';
import { mockConversations, quickResponses, mockNotifications } from './data/mockData';
import { Conversation, Message, SenderMode, QuickResponse, ConversationFilters, Notification } from './types';
import apiService from './services/api';

function App() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConversationId, setSelectedConversationId] = useState<string | null>(null);
  const [senderMode, setSenderMode] = useState<SenderMode>('operator');
  const [searchTerm, setSearchTerm] = useState('');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [notifications, setNotifications] = useState<Notification[]>(mockNotifications);
  const [showSettings, setShowSettings] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loginError, setLoginError] = useState('');
  const [isLoggingIn, setIsLoggingIn] = useState(false);
  const [quickResponsesData, setQuickResponsesData] = useState<QuickResponse[]>(quickResponses);
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [activeFilters, setActiveFilters] = useState<ConversationFilters>({
    status: '',
    dateRange: '',
    tags: [],
    operator: ''
  });

  const selectedConversation = selectedConversationId 
    ? conversations.find(c => c.id === selectedConversationId) || null
    : null;

  // Función para filtrar conversaciones
  const filterConversations = (convs: Conversation[]): Conversation[] => {
    return convs.filter(conv => {
      // Filtro por estado
      if (activeFilters.status && conv.status !== activeFilters.status) {
        return false;
      }

      // Filtro por operador
      if (activeFilters.operator && conv.assignedOperator !== activeFilters.operator) {
        return false;
      }

      // Filtro por etiquetas
      if (activeFilters.tags.length > 0) {
        const hasMatchingTag = activeFilters.tags.some(tag => conv.tags.includes(tag));
        if (!hasMatchingTag) return false;
      }

      // Filtro por rango de fechas
      if (activeFilters.dateRange) {
        const now = new Date();
        const conversationDate = conv.lastActivity;
        
        switch (activeFilters.dateRange) {
          case 'today':
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            if (conversationDate < today) return false;
            break;
            
          case 'yesterday':
            const yesterday = new Date();
            yesterday.setDate(yesterday.getDate() - 1);
            yesterday.setHours(0, 0, 0, 0);
            const yesterdayEnd = new Date(yesterday);
            yesterdayEnd.setHours(23, 59, 59, 999);
            if (conversationDate < yesterday || conversationDate > yesterdayEnd) return false;
            break;
            
          case 'last_week':
            const lastWeek = new Date();
            lastWeek.setDate(lastWeek.getDate() - 7);
            if (conversationDate < lastWeek) return false;
            break;
            
          case 'last_month':
            const lastMonth = new Date();
            lastMonth.setMonth(lastMonth.getMonth() - 1);
            if (conversationDate < lastMonth) return false;
            break;
        }
      }

      // Filtro por término de búsqueda
      if (searchTerm) {
        const searchLower = searchTerm.toLowerCase();
        const matchesName = conv.user.name.toLowerCase().includes(searchLower);
        const matchesTags = conv.tags.some(tag => tag.toLowerCase().includes(searchLower));
        const matchesMessages = conv.messages.some(msg => 
          msg.content.toLowerCase().includes(searchLower)
        );
        
        if (!matchesName && !matchesTags && !matchesMessages) return false;
      }

      return true;
    });
  };

  // Conversaciones filtradas
  const filteredConversations = filterConversations(conversations);

  // Contar filtros activos
  const activeFiltersCount = [
    activeFilters.status,
    activeFilters.dateRange,
    activeFilters.operator,
    activeFilters.tags.length > 0 ? 'tags' : ''
  ].filter(Boolean).length;

  // Verificar autenticación al cargar
  useEffect(() => {
    const token = localStorage.getItem('tony-auth-token');
    if (token) {
      setIsAuthenticated(true);
    }
  }, []);

  // Función de login
  const handleLogin = async (credentials: { username: string; password: string }) => {
    setIsLoggingIn(true);
    setLoginError('');

    try {
      // Simular delay de autenticación
      await new Promise(resolve => setTimeout(resolve, 1000));

      // Credenciales de prueba
      if (credentials.username === 'admin' && credentials.password === 'admin123') {
        localStorage.setItem('tony-auth-token', 'demo-token-123');
        setIsAuthenticated(true);
      } else {
        setLoginError('Usuario o contraseña incorrectos');
      }
    } catch (error) {
      setLoginError('Error al iniciar sesión. Inténtalo de nuevo.');
    } finally {
      setIsLoggingIn(false);
    }
  };

  // Función de logout
  const handleLogout = () => {
    localStorage.removeItem('tony-auth-token');
    setIsAuthenticated(false);
    setSelectedConversationId(null);
    setSearchTerm('');
    setActiveFilters({ status: '', dateRange: '', tags: [], operator: '' });
  };

  // Cargar datos iniciales y configurar polling
  useEffect(() => {
    const loadInitialData = async () => {
      try {
        setIsLoading(true);
        
        // Verificar conexión con el backend
        await apiService.healthCheck();
        setIsConnected(true);
        
        // Cargar conversaciones
        const conversationsData = await apiService.getConversations();
        setConversations(conversationsData);
        
        // Cargar respuestas rápidas
        const quickResponsesData = await apiService.getQuickResponses();
        setQuickResponsesData(quickResponsesData);
        
        // Las notificaciones se mantienen como están inicialmente
        
      } catch (error) {
        console.error('Error loading initial data:', error);
        setIsConnected(false);
        // Usar datos mock como fallback
        setConversations(mockConversations);
      } finally {
        setIsLoading(false);
      }
    };

    if (isAuthenticated) {
      loadInitialData();
    }
  }, [isAuthenticated]);

  // Polling para actualizar conversaciones cada 5 segundos
  useEffect(() => {
    if (!isConnected || !isAuthenticated) return;

    const interval = setInterval(async () => {
      try {
        const conversationsData = await apiService.getConversations();
        setConversations(conversationsData);
        
        // Las notificaciones del polling se mantienen como están
      } catch (error) {
        console.error('Error updating conversations:', error);
        setIsConnected(false);
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [isConnected, isAuthenticated]);

  const handleSendMessage = useCallback(async (content: string, sender: SenderMode) => {
    if (!selectedConversationId || !isConnected) return;

    try {
      const message = await apiService.sendMessage(selectedConversationId, content, sender, 'operator1');
      
      // Actualizar la conversación localmente
      setConversations(prev => prev.map(conv => 
        conv.id === selectedConversationId
          ? {
              ...conv,
              messages: [...conv.messages, message],
              lastActivity: new Date(),
              status: sender === 'operator' ? 'in_progress' : conv.status
            }
          : conv
      ));
    } catch (error) {
      console.error('Error sending message:', error);
      // Fallback: actualizar localmente
      const newMessage: Message = {
        id: Date.now().toString(),
        content,
        timestamp: new Date(),
        sender,
        status: 'sent'
      };

      setConversations(prev => prev.map(conv => 
        conv.id === selectedConversationId
          ? {
              ...conv,
              messages: [...conv.messages, newMessage],
              lastActivity: new Date(),
              status: sender === 'operator' ? 'in_progress' : conv.status
            }
          : conv
      ));
    }
  }, [selectedConversationId, isConnected]);

  const handleEditMessage = useCallback(async (messageId: string, newContent: string) => {
    if (!isConnected) return;

    try {
      const updatedMessage = await apiService.editMessage(messageId, newContent);
      
      setConversations(prev => prev.map(conv =>
        conv.id === selectedConversationId
          ? {
              ...conv,
              messages: conv.messages.map(msg =>
                msg.id === messageId
                  ? { ...updatedMessage, edited: true }
                  : msg
              )
            }
          : conv
      ));
    } catch (error) {
      console.error('Error editing message:', error);
      // Fallback: editar localmente
      setConversations(prev => prev.map(conv =>
        conv.id === selectedConversationId
          ? {
              ...conv,
              messages: conv.messages.map(msg =>
                msg.id === messageId
                  ? { ...msg, content: newContent, edited: true }
                  : msg
              )
            }
          : conv
      ));
    }
  }, [selectedConversationId, isConnected]);

  const handleModeChange = useCallback(async (mode: 'auto' | 'manual') => {
    if (!selectedConversationId || !isConnected) return;

    try {
      await apiService.changeConversationMode(selectedConversationId, mode, 'operator1');
      
      // Actualizar el modo localmente
      setConversations(prev => prev.map(conv =>
        conv.id === selectedConversationId
          ? { ...conv, mode }
          : conv
      ));
    } catch (error) {
      console.error('Error changing conversation mode:', error);
    }
  }, [selectedConversationId, isConnected]);

  const handleQuickResponse = (text: string) => {
    handleSendMessage(text, senderMode);
  };

  const handleFilterChange = (filters: ConversationFilters) => {
    console.log('Filters applied:', filters);
    setActiveFilters(filters);
  };

  // Mostrar login si no está autenticado
  if (!isAuthenticated) {
    return (
      <LoginForm 
        onLogin={handleLogin} 
        isLoading={isLoggingIn} 
        error={loginError} 
      />
    );
  }

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <div className={`bg-white border-r transition-all duration-300 ${
        sidebarOpen ? 'w-80' : 'w-0'
      } overflow-hidden`}>
        <div className="h-full flex flex-col">
          {/* Header */}
          <div className="p-4 border-b">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center">
                  <MessageCircle className="w-5 h-5 text-white" />
                </div>
                <h1 className="text-xl font-bold text-gray-900">TONY</h1>
              </div>
              <div className="flex items-center space-x-2">
                <NotificationPanel
                  notifications={notifications}
                  onMarkAsRead={(id) => setNotifications(prev => 
                    prev.map(n => n.id === id ? { ...n, read: true } : n)
                  )}
                  onMarkAllAsRead={() => setNotifications(prev => 
                    prev.map(n => ({ ...n, read: true }))
                  )}
                  onDeleteNotification={(id) => setNotifications(prev => 
                    prev.filter(n => n.id !== id)
                  )}
                  onGoToConversation={(conversationId) => {
                    setSelectedConversationId(conversationId);
                  }}
                />
                <button
                  onClick={() => setShowSettings(true)}
                  title="Configuración"
                  className="p-2 text-gray-600 hover:text-gray-900 transition-colors"
                >
                  <Settings className="w-5 h-5" />
                </button>
                <button
                  onClick={handleLogout}
                  title="Cerrar sesión"
                  className="p-2 text-gray-600 hover:text-red-600 transition-colors"
                >
                  <LogOut className="w-5 h-5" />
                </button>
              </div>
            </div>
            <SearchAndFilters
              searchTerm={searchTerm}
              onSearchChange={setSearchTerm}
              onFilterChange={handleFilterChange}
              activeFiltersCount={activeFiltersCount}
            />
          </div>

          {/* Conversations List */}
          <div className="flex-1 overflow-y-auto p-4">
            {/* Resultado de filtros */}
            {(activeFiltersCount > 0 || searchTerm) && (
              <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-blue-800">
                    Mostrando {filteredConversations.length} de {conversations.length} conversaciones
                  </span>
                  {activeFiltersCount > 0 && (
                    <button
                      type="button"
                      onClick={() => {
                        setActiveFilters({ status: '', dateRange: '', tags: [], operator: '' });
                        setSearchTerm('');
                      }}
                      className="text-blue-600 hover:text-blue-800 underline"
                    >
                      Limpiar filtros
                    </button>
                  )}
                </div>
              </div>
            )}
            
            <ConversationList
              conversations={filteredConversations}
              selectedConversation={selectedConversationId || undefined}
              onSelectConversation={setSelectedConversationId}
              searchTerm=""
            />
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Top Bar */}
        <div className="bg-white border-b px-4 py-3 flex items-center justify-between">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
          <div className="flex items-center space-x-4">
            <div className="text-sm text-gray-500">
              Asistente RRHH - Dashboard de Conversaciones
            </div>
            <div className={`flex items-center space-x-1 text-xs px-2 py-1 rounded-full ${
              isConnected ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
            }`}>
              {isConnected ? <Wifi className="w-3 h-3" /> : <WifiOff className="w-3 h-3" />}
              <span>{isConnected ? 'Conectado' : 'Desconectado'}</span>
            </div>
          </div>
        </div>

        <div className="flex-1 flex">
          {/* Chat Area */}
          <div className="flex-1">
            {isLoading ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <div className="animate-spin mx-auto mb-4 h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full"></div>
                  <p className="text-gray-600">Cargando conversaciones...</p>
                </div>
              </div>
            ) : (
              <ChatArea
                conversation={selectedConversation}
                senderMode={senderMode}
                onSendMessage={handleSendMessage}
                onEditMessage={handleEditMessage}
              />
            )}
          </div>

          {/* Right Panel */}
          {selectedConversation && (
            <div className="w-80 bg-gray-50 border-l p-4 space-y-4 overflow-y-auto">
              <ConversationModeToggle
                currentMode={selectedConversation.mode}
                conversationId={selectedConversation.id}
                onModeChange={handleModeChange}
                disabled={!isConnected}
              />
              <SenderModeToggle
                mode={senderMode}
                onModeChange={setSenderMode}
              />
              <QuickResponses
                quickResponses={quickResponsesData}
                onSelectResponse={handleQuickResponse}
              />
              
              {/* Conversation Info */}
              <div className="bg-white border rounded-lg p-4">
                <h3 className="text-sm font-medium text-gray-700 mb-3">Información de la conversación</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-500">Usuario:</span>
                    <span className="text-gray-900">{selectedConversation.user.name}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Estado:</span>
                    <span className="text-gray-900 capitalize">
                      {selectedConversation.status.replace('_', ' ')}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Modo:</span>
                    <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                      selectedConversation.mode === 'auto' ? 'bg-blue-100 text-blue-800' :
                      'bg-green-100 text-green-800'
                    }`}>
                      {selectedConversation.mode === 'auto' ? 'Bot' : 'Persona'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Mensajes:</span>
                    <span className="text-gray-900">{selectedConversation.messages.length}</span>
                  </div>
                  {selectedConversation.assignedOperator && (
                    <div className="flex justify-between">
                      <span className="text-gray-500">Operador:</span>
                      <span className="text-gray-900">{selectedConversation.assignedOperator}</span>
                    </div>
                  )}
                </div>
                
                {/* Tags */}
                {selectedConversation.tags.length > 0 && (
                  <div className="mt-3">
                    <span className="text-xs font-medium text-gray-500 block mb-2">Etiquetas:</span>
                    <div className="flex flex-wrap gap-1">
                      {selectedConversation.tags.map(tag => (
                        <span
                          key={tag}
                          className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
      
      {/* Settings Panel */}
      {showSettings && (
        <SettingsPanel onClose={() => setShowSettings(false)} />
      )}
    </div>
  );
}

export default App;