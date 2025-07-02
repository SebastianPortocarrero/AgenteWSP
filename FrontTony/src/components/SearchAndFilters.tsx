import React, { useState } from 'react';
import { Search, Filter, Calendar, Tag, User } from 'lucide-react';
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

  return (
    <div className="space-y-4">
      {/* Search Bar */}
      <div className="relative">
        <Search className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
        <input
          type="text"
          placeholder="Buscar conversaciones, usuarios, etiquetas..."
          value={searchTerm}
          onChange={(e) => onSearchChange(e.target.value)}
          className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {/* Filters Toggle */}
      <button
        onClick={() => setShowFilters(!showFilters)}
        className="flex items-center space-x-2 text-sm text-gray-600 hover:text-gray-900 transition-colors relative"
      >
        <Filter className="w-4 h-4" />
        <span>Filtros avanzados</span>
        {activeFiltersCount > 0 && (
          <span className="absolute -top-1 -right-1 bg-blue-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
            {activeFiltersCount}
          </span>
        )}
      </button>

      {/* Filters Panel */}
      {showFilters && (
        <div className="bg-gray-50 border rounded-lg p-4 space-y-4">
          {/* Status Filter */}
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-2">Estado</label>
            <select
              value={filters.status}
              onChange={(e) => handleFilterChange('status', e.target.value)}
              title="Filtrar por estado"
              className="w-full p-2 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Todos los estados</option>
              <option value="pending">Pendiente</option>
              <option value="in_progress">En progreso</option>
              <option value="closed">Cerrado</option>
            </select>
          </div>

          {/* Date Range Filter */}
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-2">
              <Calendar className="w-3 h-3 inline mr-1" />
              Rango de fechas
            </label>
            <select
              value={filters.dateRange}
              onChange={(e) => handleFilterChange('dateRange', e.target.value)}
              title="Filtrar por rango de fechas"
              className="w-full p-2 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Todas las fechas</option>
              <option value="today">Hoy</option>
              <option value="yesterday">Ayer</option>
              <option value="last_week">Última semana</option>
              <option value="last_month">Último mes</option>
            </select>
          </div>

          {/* Tags Filter */}
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-2">
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
                      ? 'bg-blue-100 border-blue-500 text-blue-700'
                      : 'bg-white border-gray-300 text-gray-600 hover:border-gray-400'
                  }`}
                >
                  {tag}
                </button>
              ))}
            </div>
          </div>

          {/* Operator Filter */}
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-2">
              <User className="w-3 h-3 inline mr-1" />
              Operador asignado
            </label>
            <select
              value={filters.operator}
              onChange={(e) => handleFilterChange('operator', e.target.value)}
              title="Filtrar por operador asignado"
              className="w-full p-2 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Todos los operadores</option>
              <option value="Ana García">Ana García</option>
              <option value="Carlos López">Carlos López</option>
              <option value="María Rodríguez">María Rodríguez</option>
            </select>
          </div>

          {/* Clear Filters */}
          <button
            onClick={() => {
              setFilters({ status: '', dateRange: '', tags: [], operator: '' });
              onFilterChange({ status: '', dateRange: '', tags: [], operator: '' });
            }}
            className="w-full bg-gray-500 text-white py-2 rounded text-sm hover:bg-gray-600 transition-colors"
          >
            Limpiar filtros
          </button>
        </div>
      )}
    </div>
  );
};

export default SearchAndFilters;