import React from 'react';
import ConversationList from './ConversationList';
import ChatArea from './ChatArea';
import ConversationModeToggle from './ConversationModeToggle';
import QuickResponses from './QuickResponses';
import SearchAndFilters from './SearchAndFilters';
import NotificationPanel from './NotificationPanel';
import SettingsPanel from './SettingsPanel';
import { MessageCircle, Settings, LogOut, Wifi, WifiOff, Menu, X, Search, MoreVertical } from 'lucide-react';

const ConversationMonitor = (props: any) => {
  // Recibe todos los props necesarios desde App.tsx
  // Puedes ajustar los nombres según tu lógica
  const {
    sidebarOpen,
    setSidebarOpen,
    notifications,
    setNotifications,
    showSettings,
    setShowSettings,
    handleLogout,
    searchTerm,
    setSearchTerm,
    activeFilters,
    setActiveFilters,
    activeFiltersCount,
    handleFilterChange,
    isConnected,
    isLoading,
    filteredConversations,
    conversations,
    selectedConversationId,
    setSelectedConversationId,
    selectedConversation,
    quickResponsesData,
    handleQuickResponse,
    senderMode,
    handleEditPendingResponse,
    isLoadingPendingResponse,
    handleApprovePendingResponse,
    handleRejectPendingResponse,
    handleSendMessage,
    handleEditMessage,
    handleDeleteMessage,
    handleTagChange,
    handleAssignOperator,
    handleModeChange,
    showSettingsPanel,
    setShowSettingsPanel
  } = props;

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-900 overflow-hidden">
      {/* Sidebar - Lista de conversaciones */}
      <div className={`bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 transition-all duration-300 flex-shrink-0 ${
        sidebarOpen ? 'w-96' : 'w-0'
      } overflow-hidden`}>
        <div className="h-full flex flex-col">
          {/* Header del Sidebar */}
          <div className="bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-4">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-green-500 rounded-full flex items-center justify-center">
                  <MessageCircle className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h1 className="text-xl font-semibold text-gray-900 dark:text-gray-100">Tony AI</h1>
                  <p className="text-xs text-gray-500">Asistente RRHH</p>
                </div>
              </div>
              <div className="flex items-center space-x-1">
                <NotificationPanel
                  notifications={notifications}
                  onMarkAsRead={(id) => setNotifications((prev: any) => prev.map((n: any) => n.id === id ? { ...n, read: true } : n))}
                  onMarkAllAsRead={() => setNotifications((prev: any) => prev.map((n: any) => ({ ...n, read: true })))}
                  onDeleteNotification={(id) => setNotifications((prev: any) => prev.filter((n: any) => n.id !== id))}
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
                className="w-full pl-10 pr-4 py-2 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent text-sm dark:text-gray-100"
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
      <div className="flex-1 flex flex-col min-w-0 bg-gray-50 dark:bg-gray-900 dark:text-gray-100">
        {/* Top Bar */}
        <div className="bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-4 py-3 flex items-center justify-between flex-shrink-0">
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
                  <h2 className="font-medium text-gray-900 dark:text-gray-100">{selectedConversation.user.name}</h2>
                  <p className="text-sm text-gray-500">
                    {selectedConversation.assignedOperator && `Atendido por: ${selectedConversation.assignedOperator}`}
                  </p>
                </div>
              </>
            )}
          </div>
          {selectedConversation && (
            <div className="flex items-center space-x-2">
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
          <div className="flex-1 min-w-0 bg-white dark:bg-gray-950 dark:text-gray-100">
            <ChatArea
              conversation={selectedConversation}
              senderMode={senderMode}
              quickResponses={quickResponsesData}
              onSendMessage={handleSendMessage}
              onEditMessage={handleEditMessage}
              onDeleteMessage={handleDeleteMessage}
              onQuickResponse={handleQuickResponse}
              onEditPendingResponse={handleEditPendingResponse}
              isLoadingPendingResponse={isLoadingPendingResponse}
              onApprovePendingResponse={handleApprovePendingResponse}
              onRejectPendingResponse={handleRejectPendingResponse}
              showSettingsPanel={showSettingsPanel}
              setShowSettingsPanel={setShowSettingsPanel}
            />
          </div>
          {/* Panel lateral derecho (respuestas rápidas, configuración, etc.) */}
          <div className="hidden lg:block w-80 border-l border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
            <div className="h-full flex flex-col">
              <ConversationModeToggle
                mode={selectedConversation?.mode || 'manual'}
                onModeChange={handleModeChange}
              />
              <QuickResponses
                quickResponses={quickResponsesData}
                onQuickResponse={handleQuickResponse}
              />
              {showSettings && (
                <SettingsPanel
                  isOpen={showSettings}
                  onClose={() => setShowSettings(false)}
                  onTagChange={handleTagChange}
                  onAssignOperator={handleAssignOperator}
                  conversation={selectedConversation}
                />
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ConversationMonitor; 