import { useState, useEffect } from 'react';
import { MessageCircle, Users, LogOut } from 'lucide-react';

interface AdminDashboardProps {
  onLogout: () => void;
  onNavigate: (route: string) => void;
}

const AdminDashboard: React.FC<AdminDashboardProps> = ({ onLogout, onNavigate }) => {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 dark:text-gray-100">
      {/* Header */}
      <header className="bg-white dark:bg-gray-950 shadow-sm border-b border-gray-200 dark:border-gray-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                Panel de Administración
              </h1>
            </div>
            <button
              onClick={onLogout}
              className="flex items-center px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md transition-colors duration-200"
            >
              <LogOut className="w-4 h-4 mr-2" />
              Cerrar sesión
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Tarjeta Mensajería Masiva */}
          <div
            onClick={() => onNavigate('/mensajeria-masiva')}
            className="bg-white dark:bg-gray-900 rounded-lg shadow-sm border border-gray-200 dark:border-gray-800 p-6 cursor-pointer hover:shadow-md transition-shadow duration-200 hover:border-blue-300 dark:hover:border-blue-500 group"
          >
            <div className="flex items-center mb-4">
              <div className="flex-shrink-0">
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center group-hover:bg-blue-200 transition-colors duration-200">
                  <MessageCircle className="w-6 h-6 text-blue-600" />
                </div>
              </div>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
              Mensajería Masiva
            </h3>
            <p className="text-gray-600 dark:text-gray-300 text-sm">
              Enviar mensajes a todos los contactos a la vez
            </p>
          </div>

          {/* Tarjeta Visor de Conversaciones */}
          <div
            onClick={() => onNavigate('/visor-conversaciones')}
            className="bg-white dark:bg-gray-900 rounded-lg shadow-sm border border-gray-200 dark:border-gray-800 p-6 cursor-pointer hover:shadow-md transition-shadow duration-200 hover:border-green-300 dark:hover:border-green-500 group"
          >
            <div className="flex items-center mb-4">
              <div className="flex-shrink-0">
                <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center group-hover:bg-green-200 transition-colors duration-200">
                  <Users className="w-6 h-6 text-green-600" />
                </div>
              </div>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
              Visor de Conversaciones
            </h3>
            <p className="text-gray-600 dark:text-gray-300 text-sm">
              Monitorear y ver todas las conversaciones de usuarios
            </p>
          </div>
        </div>
      </main>
    </div>
  );
};

export default AdminDashboard; 