import React, { useState, useCallback, useEffect } from 'react';
import { MessageCircle, Settings, Bell, Menu, X, Wifi, WifiOff, LogOut, Search, MoreVertical } from 'lucide-react';
import ConversationList from './components/ConversationList';
import ChatArea from './components/ChatArea';
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

  // El senderMode se deriva automáticamente del modo de conversación
  const senderMode: SenderMode = selectedConversation?.mode === 'auto' ? 'bot' : 'operator';

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
      await apiService.editMessage(messageId, newContent);
      
      // Actualizar mensaje localmente
      setConversations(prev => prev.map(conv => ({
        ...conv,
        messages: conv.messages.map(msg => 
          msg.id === messageId 
            ? { ...msg, content: newContent, edited: true }
            : msg
        )
      })));
    } catch (error) {
      console.error('Error editing message:', error);
      // Fallback: actualizar localmente
      setConversations(prev => prev.map(conv => ({
        ...conv,
        messages: conv.messages.map(msg => 
          msg.id === messageId 
            ? { ...msg, content: newContent, edited: true }
            : msg
        )
      })));
    }
  }, [isConnected]);

  const handleModeChange = useCallback(async (mode: 'auto' | 'manual' | 'hybrid') => {
    if (!selectedConversationId) return;

    // Actualizar el modo localmente SIEMPRE
    setConversations(prev => prev.map(conv =>
      conv.id === selectedConversationId
        ? { ...conv, mode }
        : conv
    ));

    // Si está conectado, intentar sincronizar con el backend
    if (isConnected) {
      try {
        await apiService.changeConversationMode(selectedConversationId, mode, 'operator1');
        console.log(`Modo ${mode} sincronizado con el backend`);
      } catch (error) {
        console.error('Error syncing mode with backend:', error);
        // El cambio local ya se aplicó, así que no revertimos
      }
    } else {
      console.log(`Modo ${mode} cambiado localmente (sin conexión)`);
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
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      {/* Sidebar - Lista de conversaciones */}
      <div className={`bg-white border-r border-gray-200 transition-all duration-300 flex-shrink-0 ${
        sidebarOpen ? 'w-96' : 'w-0'
      } overflow-hidden`}>
        <div className="h-full flex flex-col">
          {/* Header del Sidebar */}
          <div className="bg-gray-50 border-b border-gray-200 p-4">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-green-500 rounded-full flex items-center justify-center">
                  <MessageCircle className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h1 className="text-xl font-semibold text-gray-900">Tony AI</h1>
                  <p className="text-xs text-gray-500">Asistente RRHH</p>
                </div>
              </div>
              <div className="flex items-center space-x-1">
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
                  className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-full transition-colors"
                >
                  <Settings className="w-5 h-5" />
                </button>
                <button
                  onClick={handleLogout}
                  title="Cerrar sesión"
                  className="p-2 text-gray-500 hover:text-red-500 hover:bg-red-50 rounded-full transition-colors"
                >
                  <LogOut className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Buscador */}
            <div className="relative mb-3">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Buscar conversaciones..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-white border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent text-sm"
              />
            </div>

            {/* Filtros */}
            <SearchAndFilters
              searchTerm=""
              onSearchChange={() => {}}
              onFilterChange={handleFilterChange}
              activeFiltersCount={activeFiltersCount}
            />
          </div>

          {/* Status de conexión */}
          <div className="px-4 py-2 bg-green-50 border-b border-green-100">
            <div className={`flex items-center space-x-2 text-xs ${
              isConnected ? 'text-green-600' : 'text-red-600'
            }`}>
              {isConnected ? <Wifi className="w-3 h-3" /> : <WifiOff className="w-3 h-3" />}
              <span>{isConnected ? 'Conectado' : 'Sin conexión'}</span>
            </div>
          </div>

          {/* Lista de conversaciones */}
          <div className="flex-1 overflow-y-auto">
            {/* Resultado de filtros */}
            {(activeFiltersCount > 0 || searchTerm) && (
              <div className="mx-4 mt-3 mb-2 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-blue-800">
                    {filteredConversations.length} de {conversations.length} conversaciones
                  </span>
                  {activeFiltersCount > 0 && (
                    <button
                      type="button"
                      onClick={() => {
                        setActiveFilters({ status: '', dateRange: '', tags: [], operator: '' });
                        setSearchTerm('');
                      }}
                      className="text-blue-600 hover:text-blue-800 text-xs underline"
                    >
                      Limpiar
                    </button>
                  )}
                </div>
              </div>
            )}
            
            {isLoading ? (
              <div className="flex items-center justify-center h-32">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-green-500"></div>
              </div>
            ) : (
              <ConversationList
                conversations={filteredConversations}
                selectedConversation={selectedConversationId || undefined}
                onSelectConversation={setSelectedConversationId}
                searchTerm=""
              />
            )}
          </div>
        </div>
      </div>

      {/* Área principal */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top Bar */}
        <div className="bg-gray-50 border-b border-gray-200 px-4 py-3 flex items-center justify-between flex-shrink-0">
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors lg:hidden"
            >
              {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
            
            {selectedConversation && (
              <>
                <div className="w-10 h-10 bg-gray-300 rounded-full flex items-center justify-center">
                  <span className="text-sm font-medium text-gray-600">
                    {selectedConversation.user.name.charAt(0).toUpperCase()}
                  </span>
                </div>
                <div>
                  <h2 className="font-medium text-gray-900">{selectedConversation.user.name}</h2>
                  <p className="text-sm text-gray-500">
                    {selectedConversation.assignedOperator && `Atendido por: ${selectedConversation.assignedOperator}`}
                  </p>
                </div>
              </>
            )}
          </div>

          {selectedConversation && (
            <div className="flex items-center space-x-2">
              {/* Solo mostrar estado básico - los controles están en el panel lateral */}
              <div className={`w-3 h-3 rounded-full ${
                selectedConversation.status === 'pending' ? 'bg-orange-400' :
                selectedConversation.status === 'in_progress' ? 'bg-blue-400' :
                'bg-green-400'
              }`} title={
                selectedConversation.status === 'pending' ? 'Pendiente' :
                selectedConversation.status === 'in_progress' ? 'En progreso' :
                'Cerrado'
              }></div>
              <span className="text-sm text-gray-500">
                {selectedConversation.messages.length} mensajes
              </span>
              <button 
                title="Más opciones"
                className="p-2 hover:bg-gray-100 rounded-full transition-colors"
              >
                <MoreVertical className="w-4 h-4 text-gray-500" />
              </button>
            </div>
          )}
        </div>

        {/* Área de chat y panel lateral */}
        <div className="flex-1 flex min-h-0">
          {/* Chat Area */}
          <div className="flex-1 min-w-0">
            {!selectedConversation ? (
              <div className="flex items-center justify-center h-full bg-gray-50">
                <div className="text-center">
                  <div className="w-20 h-20 bg-gray-200 rounded-full flex items-center justify-center mx-auto mb-4">
                    <MessageCircle className="w-10 h-10 text-gray-400" />
                  </div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">Tony AI Assistant</h3>
                  <p className="text-gray-500">Selecciona una conversación para comenzar</p>
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

          {/* Panel lateral derecho */}
          {selectedConversation && (
            <div className="w-80 bg-white border-l border-gray-200 flex-shrink-0 hidden lg:block">
              <div className="h-full overflow-y-auto p-4 space-y-4">
                {/* Control unificado de modo */}
                <ConversationModeToggle
                  currentMode={selectedConversation.mode}
                  conversationId={selectedConversation.id}
                  onModeChange={handleModeChange}
                  disabled={false}
                />
                
                <QuickResponses
                  quickResponses={quickResponsesData}
                  onSelectResponse={handleQuickResponse}
                />
                
                {/* Info de la conversación */}
                <div className="bg-gray-50 rounded-lg p-4">
                  <h3 className="font-medium text-gray-900 mb-3">Información</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-500">Mensajes:</span>
                      <span className="text-gray-900">{selectedConversation.messages.length}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Sin leer:</span>
                      <span className="text-gray-900">{selectedConversation.unreadCount}</span>
                    </div>
                    {selectedConversation.tags.length > 0 && (
                      <div className="mt-3">
                        <span className="text-gray-500 text-xs block mb-2">Etiquetas:</span>
                        <div className="flex flex-wrap gap-1">
                          {selectedConversation.tags.map(tag => (
                            <span
                              key={tag}
                              className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full"
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
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