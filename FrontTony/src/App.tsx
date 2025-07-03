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
import AdminDashboard from './components/AdminDashboard';
import { mockConversations, quickResponses, mockNotifications } from './data/mockData';
import { Conversation, Message, SenderMode, QuickResponse, ConversationFilters, Notification } from './types';
import apiService from './services/api';
import { BrowserRouter, Routes, Route, useNavigate, Navigate } from 'react-router-dom';
import ConversationMonitor from './components/ConversationMonitor';

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
  const [showDashboard, setShowDashboard] = useState(true);

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

  // Funciones para manejar respuestas pendientes del modo híbrido
  const [isLoadingPendingResponse, setIsLoadingPendingResponse] = useState(false);

  const handleApprovePendingResponse = useCallback(async (conversationId: string) => {
    if (!isConnected) return;
    
    setIsLoadingPendingResponse(true);
    try {
      const message = await apiService.approvePendingResponse(conversationId);
      
      // Actualizar conversaciones: agregar mensaje y limpiar respuesta pendiente
      setConversations(prev => prev.map(conv =>
        conv.id === conversationId
          ? { 
              ...conv, 
              messages: [...conv.messages, message],
              pending_response: null
            }
          : conv
      ));
      
      console.log('Respuesta pendiente aprobada y enviada');
    } catch (error) {
      console.error('Error aprobando respuesta pendiente:', error);
    } finally {
      setIsLoadingPendingResponse(false);
    }
  }, [isConnected]);

  const handleRejectPendingResponse = useCallback(async (conversationId: string) => {
    if (!isConnected) return;
    
    setIsLoadingPendingResponse(true);
    try {
      await apiService.rejectPendingResponse(conversationId);
      
      // Limpiar respuesta pendiente
      setConversations(prev => prev.map(conv =>
        conv.id === conversationId
          ? { ...conv, pending_response: null }
          : conv
      ));
      
      console.log('Respuesta pendiente rechazada');
    } catch (error) {
      console.error('Error rechazando respuesta pendiente:', error);
    } finally {
      setIsLoadingPendingResponse(false);
    }
  }, [isConnected]);

  const handleEditAndApprovePendingResponse = useCallback(async (conversationId: string, newContent: string) => {
    if (!isConnected) return;
    
    setIsLoadingPendingResponse(true);
    try {
      const message = await apiService.editAndApprovePendingResponse(conversationId, newContent);
      
      // Actualizar conversaciones: agregar mensaje editado y limpiar respuesta pendiente
      setConversations(prev => prev.map(conv =>
        conv.id === conversationId
          ? { 
              ...conv, 
              messages: [...conv.messages, message],
              pending_response: null
            }
          : conv
      ));
      
      console.log('Respuesta pendiente editada, aprobada y enviada');
    } catch (error) {
      console.error('Error editando y aprobando respuesta pendiente:', error);
    } finally {
      setIsLoadingPendingResponse(false);
    }
  }, [isConnected]);

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
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 dark:text-gray-100">
        <AppRoutes
          onLogout={handleLogout}
          sidebarOpen={sidebarOpen}
          setSidebarOpen={setSidebarOpen}
          notifications={notifications}
          setNotifications={setNotifications}
          showSettings={showSettings}
          setShowSettings={setShowSettings}
          searchTerm={searchTerm}
          setSearchTerm={setSearchTerm}
          activeFilters={activeFilters}
          setActiveFilters={setActiveFilters}
          activeFiltersCount={activeFiltersCount}
          handleFilterChange={handleFilterChange}
          isConnected={isConnected}
          isLoading={isLoading}
          filteredConversations={filteredConversations}
          conversations={conversations}
          selectedConversationId={selectedConversationId}
          setSelectedConversationId={setSelectedConversationId}
          selectedConversation={selectedConversation}
          quickResponsesData={quickResponsesData}
          handleQuickResponse={handleQuickResponse}
          senderMode={senderMode}
          handleEditPendingResponse={handleEditAndApprovePendingResponse}
          isLoadingPendingResponse={isLoadingPendingResponse}
          handleApprovePendingResponse={handleApprovePendingResponse}
          handleRejectPendingResponse={handleRejectPendingResponse}
          handleSendMessage={handleSendMessage}
          handleEditMessage={handleEditMessage}
          handleDeleteMessage={() => {}}
          handleTagChange={() => {}}
          handleAssignOperator={() => {}}
          handleModeChange={handleModeChange}
          showSettingsPanel={false}
          setShowSettingsPanel={() => {}}
        />
      </div>
    </BrowserRouter>
  );
}

function AppRoutes(props: any) {
  const navigate = useNavigate();
  return (
    <Routes>
      <Route
        path="/dashboard"
        element={
          <AdminDashboard
            onLogout={props.onLogout}
            onNavigate={route => navigate(route)}
          />
        }
      />
      <Route
        path="/visor-conversaciones"
        element={<ConversationMonitor {...props} />}
      />
      <Route
        path="/mensajeria-masiva"
        element={<BulkMessagingTool />}
      />
      <Route path="*" element={<Navigate to="/dashboard" />} />
    </Routes>
  );
}

// Componente BulkMessagingTool (diseño como la imagen adjunta, traducido al español)
function BulkMessagingTool() {
  const [message, setMessage] = useState('');
  const contacts = [
    { name: 'Juan Pérez', phone: '+51 999 111 222' },
    { name: 'Ana López', phone: '+51 999 222 333' },
    { name: 'Carlos Ruiz', phone: '+51 999 333 444' },
    { name: 'María Gómez', phone: '+51 999 444 555' },
    { name: 'Sofía Torres', phone: '+51 999 555 666' },
    { name: 'Pedro Sánchez', phone: '+51 999 666 777' },
  ];
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <div className="flex items-center px-8 py-6 bg-white border-b">
        <button onClick={() => window.history.back()} className="flex items-center text-gray-600 hover:text-blue-600 font-medium mr-6">
          <span className="mr-2">←</span> Volver al Panel
        </button>
        <h1 className="text-2xl font-semibold text-gray-900">Herramienta de Mensajería Masiva</h1>
      </div>
      <div className="flex-1 flex flex-col md:flex-row gap-6 p-8 max-w-6xl w-full mx-auto">
        {/* Redactar Mensaje */}
        <div className="bg-white rounded-xl shadow p-6 flex-1 flex flex-col">
          <div className="flex items-center mb-4">
            <svg className="w-6 h-6 text-blue-500 mr-2" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M3 8l7.89 3.26a2 2 0 001.44 0L21 8m-9 4v8" /></svg>
            <h2 className="text-lg font-semibold">Redactar Mensaje</h2>
          </div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Contenido del mensaje</label>
          <textarea
            className="w-full h-40 border rounded-lg p-3 mb-2 focus:outline-none focus:ring-2 focus:ring-blue-400 resize-none"
            placeholder="Escribe tu mensaje aquí..."
            value={message}
            onChange={e => setMessage(e.target.value)}
          />
          <div className="text-xs text-gray-500 mb-4">Cantidad de caracteres: {message.length}</div>
          <button className="mt-auto bg-blue-400 hover:bg-blue-500 text-white font-medium py-3 rounded-lg flex items-center justify-center transition-colors disabled:opacity-50" disabled={!message.trim()}>
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M3 8l7.89 3.26a2 2 0 001.44 0L21 8m-9 4v8" /></svg>
            Enviar mensaje a todos los contactos
          </button>
        </div>
        {/* Lista de Contactos */}
        <div className="bg-white rounded-xl shadow p-6 w-full md:w-80 flex flex-col">
          <div className="flex items-center mb-4">
            <svg className="w-6 h-6 text-green-500 mr-2" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M17 20h5v-2a4 4 0 00-3-3.87M9 20H4v-2a4 4 0 013-3.87m9-5a4 4 0 11-8 0 4 4 0 018 0z" /></svg>
            <h2 className="text-lg font-semibold text-gray-900">Lista de Contactos</h2>
          </div>
          <div className="text-sm text-gray-600 mb-2">Total de contactos: {contacts.length}</div>
          <div className="flex-1 overflow-y-auto">
            {contacts.map((c, i) => (
              <div key={i} className="flex items-center gap-3 p-2 rounded-lg hover:bg-gray-100 transition-colors">
                <div className="w-10 h-10 rounded-full bg-gray-200 flex items-center justify-center font-bold text-gray-500 text-lg">{c.name.charAt(0)}</div>
                <div>
                  <div className="font-medium text-gray-800">{c.name}</div>
                  <div className="text-xs text-gray-500">{c.phone}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;