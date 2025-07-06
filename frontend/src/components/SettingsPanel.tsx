import { useState } from 'react';
import { Settings, X, User, Bell, Shield } from 'lucide-react';
import { useTheme } from '../App';

interface SettingsPanelProps {
  onClose: () => void;
  showThemeSelector?: boolean;
}

const SettingsPanel: React.FC<SettingsPanelProps> = ({ onClose, showThemeSelector = false }) => {
  const [settings, setSettings] = useState({
    user: {
      name: 'Operador RRHH',
      email: 'operador@empresa.com',
      role: 'Supervisor'
    },
    notifications: 'enabled',
    autoResponse: 'auto'
  });

  const { theme, setTheme } = useTheme();

  const handleChange = (section: string, key: string, value: string) => {
    if (section === 'user') {
      setSettings(prev => ({
        ...prev,
        user: { ...prev.user, [key]: value }
      }));
    } else {
      setSettings(prev => ({
        ...prev,
        [section]: value
      }));
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-900 rounded-lg shadow-xl w-full max-w-lg max-h-screen flex flex-col overflow-hidden">
        {/* Header */}
        <div className="p-6 border-b bg-gray-50 dark:bg-gray-800">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Settings className="w-6 h-6 text-gray-600" />
              <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">Configuración</h2>
            </div>
            <button
              onClick={onClose}
              title="Cerrar configuración"
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <X className="w-6 h-6" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto flex-1 min-h-0">
          <div className="space-y-8">
            
            {/* User Profile */}
            <div>
              <div className="flex items-center space-x-2 mb-4">
                <User className="w-5 h-5 text-gray-600" />
                <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">Perfil de Usuario</h3>
              </div>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Nombre</label>
                  <input
                    type="text"
                    title="Nombre del operador"
                    value={settings.user.name}
                    onChange={(e) => handleChange('user', 'name', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-gray-100"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Email</label>
                  <input
                    type="email"
                    title="Email del operador"
                    value={settings.user.email}
                    onChange={(e) => handleChange('user', 'email', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-gray-100"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Rol</label>
                  <select
                    title="Rol del operador"
                    value={settings.user.role}
                    onChange={(e) => handleChange('user', 'role', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-gray-100"
                  >
                    <option value="Operador">Operador</option>
                    <option value="Supervisor">Supervisor</option>
                    <option value="Administrador">Administrador</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Notifications */}
            <div>
              <div className="flex items-center space-x-2 mb-4">
                <Bell className="w-5 h-5 text-gray-600" />
                <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">Notificaciones</h3>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Estado de notificaciones</label>
                <select
                  title="Estado de las notificaciones"
                  value={settings.notifications}
                  onChange={(e) => handleChange('notifications', '', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-gray-100"
                >
                  <option value="enabled">Habilitadas</option>
                  <option value="disabled">Deshabilitadas</option>
                  <option value="important_only">Solo importantes</option>
                </select>
              </div>
            </div>

            {/* Theme (solo si showThemeSelector) */}
            {showThemeSelector && (
              <div>
                <div className="flex items-center space-x-2 mb-4">
                  <Shield className="w-5 h-5 text-gray-600" />
                  <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">Tema</h3>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Apariencia</label>
                  <select
                    title="Tema de la aplicación"
                    value={theme}
                    onChange={(e) => setTheme(e.target.value as any)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-gray-100"
                  >
                    <option value="light">Claro</option>
                    <option value="dark">Oscuro</option>
                    <option value="auto">Automático</option>
                  </select>
                </div>
              </div>
            )}

            {/* Auto Response */}
            <div>
              <div className="flex items-center space-x-2 mb-4">
                <Settings className="w-5 h-5 text-gray-600" />
                <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">Respuesta Automática</h3>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Modo por defecto</label>
                <select
                  title="Modo de respuesta por defecto"
                  value={settings.autoResponse}
                  onChange={(e) => handleChange('autoResponse', '', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-gray-100"
                >
                  <option value="auto">Bot automático</option>
                  <option value="manual">Manual solamente</option>
                </select>
              </div>
            </div>

          </div>
        </div>

        {/* Footer */}
        <div className="p-6 border-t bg-gray-50 flex justify-end space-x-3 flex-shrink-0">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          >
            Cancelar
          </button>
          <button
            onClick={onClose}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            Guardar cambios
          </button>
        </div>
      </div>
    </div>
  );
};

export default SettingsPanel; 