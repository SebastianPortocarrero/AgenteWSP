import React, { useState } from 'react';
import { Filter, Calendar, Tag, User, ChevronDown, X } from 'lucide-react';
import { ConversationFilters } from '../types';

interface SearchAndFiltersProps {
  searchTerm: string;
  onSearchChange: (term: string) => void;
  onFilterChange: (filters: ConversationFilters) => void;
  activeFiltersCount?: number;
}

const SearchAndFilters: React.FC<SearchAndFiltersProps> = ({
  searchTerm,
  onSearchChange,
  onFilterChange,
  activeFiltersCount = 0
}) => {
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState<ConversationFilters>({
    status: '',
    dateRange: '',
    tags: [],
    operator: ''
  });

  const handleFilterChange = (key: string, value: any) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);
    onFilterChange(newFilters);
  };

  const clearAllFilters = () => {
    const clearedFilters = { status: '', dateRange: '', tags: [], operator: '' };
    setFilters(clearedFilters);
    onFilterChange(clearedFilters);
  };

  return (
    <div className="relative">
      {/* Botón de filtros */}
      <button
        onClick={() => setShowFilters(!showFilters)}
        className={`flex items-center justify-between w-full px-3 py-2 text-sm rounded-lg border transition-colors ${
          showFilters 
            ? 'bg-green-50 border-green-200 text-green-700' 
            : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'
        }`}
      >
        <div className="flex items-center space-x-2">
          <Filter className="w-4 h-4" />
          <span>Filtros</span>
          {activeFiltersCount > 0 && (
            <span className="bg-green-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center font-medium">
              {activeFiltersCount}
            </span>
          )}
        </div>
        <ChevronDown className={`w-4 h-4 transition-transform ${showFilters ? 'rotate-180' : ''}`} />
      </button>

      {/* Panel de filtros */}
      {showFilters && (
        <div className="absolute top-full left-0 right-0 mt-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg z-10">
          <div className="p-4 space-y-4">
            
            {/* Estado */}
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-2">Estado</label>
              <select
                value={filters.status}
                onChange={(e) => handleFilterChange('status', e.target.value)}
                title="Filtrar por estado"
                className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
              >
                <option value="">Todos</option>
                <option value="pending">⏳ Pendiente</option>
                <option value="in_progress">🔄 En progreso</option>
                <option value="closed">✅ Cerrado</option>
              </select>
            </div>

            {/* Fecha */}
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-2">
                <Calendar className="w-3 h-3 inline mr-1" />
                Fecha
              </label>
              <select
                value={filters.dateRange}
                onChange={(e) => handleFilterChange('dateRange', e.target.value)}
                title="Filtrar por rango de fechas"
                className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
              >
                <option value="">Todas las fechas</option>
                <option value="today">📅 Hoy</option>
                <option value="yesterday">📅 Ayer</option>
                <option value="last_week">📅 Última semana</option>
                <option value="last_month">📅 Último mes</option>
              </select>
            </div>

            {/* Etiquetas */}
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-2">
                <Tag className="w-3 h-3 inline mr-1" />
                Etiquetas
              </label>
              <div className="flex flex-wrap gap-2">
                {['vacaciones', 'nómina', 'evaluación', 'solicitud', 'consulta', 'acceso'].map(tag => (
                  <button
                    key={tag}
                    onClick={() => {
                      const newTags = filters.tags.includes(tag)
                        ? filters.tags.filter(t => t !== tag)
                        : [...filters.tags, tag];
                      handleFilterChange('tags', newTags);
                    }}
                    className={`px-3 py-1 text-xs rounded-full border transition-all ${
                      filters.tags.includes(tag)
                        ? 'bg-green-100 border-green-500 text-green-700'
                        : 'bg-gray-50 border-gray-200 text-gray-600 hover:border-gray-300'
                    }`}
                  >
                    {tag}
                  </button>
                ))}
              </div>
            </div>

            {/* Operador */}
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-2">
                <User className="w-3 h-3 inline mr-1" />
                Operador
              </label>
              <select
                value={filters.operator}
                onChange={(e) => handleFilterChange('operator', e.target.value)}
                title="Filtrar por operador asignado"
                className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
              >
                <option value="">Todos los operadores</option>
                <option value="Ana García">👤 Ana García</option>
                <option value="Carlos López">👤 Carlos López</option>
                <option value="María Rodríguez">👤 María Rodríguez</option>
              </select>
            </div>

            {/* Botones de acción */}
            <div className="flex space-x-2 pt-2 border-t border-gray-100">
              <button
                onClick={clearAllFilters}
                className="flex-1 flex items-center justify-center space-x-1 px-3 py-2 text-sm text-gray-600 dark:text-gray-300 bg-gray-50 dark:bg-gray-800 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              >
                <X className="w-3 h-3" />
                <span>Limpiar</span>
              </button>
              <button
                onClick={() => setShowFilters(false)}
                className="flex-1 px-3 py-2 text-sm text-white bg-green-500 rounded-lg hover:bg-green-600 transition-colors"
              >
                Aplicar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SearchAndFilters;