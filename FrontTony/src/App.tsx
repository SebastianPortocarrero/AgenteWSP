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
        element={
          <div className="flex items-center justify-center h-screen">
            <h2 className="text-2xl font-bold">Funcionalidad próximamente</h2>
          </div>
        }
      />
      <Route path="*" element={<Navigate to="/dashboard" />} />
    </Routes>
  );
}

export default App;