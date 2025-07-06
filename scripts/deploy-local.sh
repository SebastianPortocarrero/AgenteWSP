#!/bin/bash

# Script de despliegue local con Docker - MONOREPO VERSION
# Tony - Asistente de WhatsApp

echo "🚀 Iniciando despliegue local de Tony (Monorepo)"
echo "================================================"

# Colores para mejor legibilidad
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para mostrar mensajes con colores
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar si Docker está instalado
if ! command -v docker &> /dev/null; then
    print_error "Docker no está instalado. Por favor, instala Docker primero."
    exit 1
fi

# Verificar si Docker Compose está instalado
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose no está instalado. Por favor, instala Docker Compose primero."
    exit 1
fi

# Obtener directorio del script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

print_status "Directorio del proyecto: $PROJECT_ROOT"

# Cambiar al directorio del proyecto
cd "$PROJECT_ROOT"

print_status "Verificando estructura del monorepo..."

# Verificar que existan los directorios necesarios
if [ ! -d "backend" ]; then
    print_error "No se encontró el directorio 'backend'"
    exit 1
fi

if [ ! -d "frontend" ]; then
    print_error "No se encontró el directorio 'frontend'"
    exit 1
fi

if [ ! -d "docker" ]; then
    print_error "No se encontró el directorio 'docker'"
    exit 1
fi

print_success "Estructura del monorepo verificada ✓"

# Crear directorio SSL si no existe
print_status "Creando directorio SSL..."
mkdir -p backend/ssl

# Crear archivo .env si no existe
if [ ! -f ".env" ]; then
    print_warning "No se encontró archivo .env, creando uno básico..."
    cat > .env << EOF
# Variables de entorno para Tony WhatsApp Assistant

# OpenAI
OPENAI_API_KEY=tu_clave_openai_aqui

# Supabase
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=tu_clave_supabase_aqui

# WhatsApp
WHATSAPP_TOKEN=tu_token_whatsapp_aqui
WHATSAPP_PHONE_ID=tu_phone_id_aqui
WEBHOOK_VERIFY_TOKEN=tu_verify_token_aqui

# Redis
REDIS_URL=redis://redis:6379

# Domain
DOMAIN=localhost

# Frontend
VITE_API_BASE_URL=http://localhost/api
EOF
    print_warning "⚠️ IMPORTANTE: Edita el archivo .env con tus credenciales reales"
fi

# Parar servicios existentes si están corriendo
print_status "Deteniendo servicios existentes..."
cd docker
docker-compose down --remove-orphans 2>/dev/null || true

# Limpiar imágenes y contenedores antiguos (opcional)
print_status "Limpiando imágenes Docker antiguas..."
docker system prune -f

# Construir y levantar los servicios
print_status "Construyendo y levantando servicios..."
docker-compose --env-file ../.env up --build -d

# Verificar que los servicios estén funcionando
print_status "Verificando servicios (esperando 15 segundos)..."
sleep 15

# Función para verificar servicio
check_service() {
    local service_name=$1
    local container_name=$2
    
    if docker ps --filter "name=$container_name" --filter "status=running" | grep -q "$container_name"; then
        print_success "$service_name está funcionando ✓"
        return 0
    else
        print_error "$service_name no está funcionando ✗"
        return 1
    fi
}

# Verificar servicios
check_service "Redis" "tony-redis"
check_service "Backend" "tony-backend"  
check_service "Frontend" "tony-frontend"
check_service "Nginx" "tony-nginx"

# Mostrar estado de los servicios
print_status "Estado detallado de los servicios:"
docker-compose ps

# Verificar health checks
print_status "Verificando health checks..."
sleep 10

# Función para verificar health check
check_health() {
    local url=$1
    local service_name=$2
    
    if curl -f -s "$url" > /dev/null 2>&1; then
        print_success "$service_name health check ✓"
    else
        print_warning "$service_name health check falló ⚠️"
    fi
}

check_health "http://localhost/health" "Sistema completo"
check_health "http://localhost:8000/health" "Backend directo"
check_health "http://localhost:3000" "Frontend directo"

# Mostrar información de acceso
echo ""
echo "🎉 ¡Despliegue del monorepo completado!"
echo "================================================"
echo ""
echo "📱 Servicios disponibles:"
echo "   • Frontend (React):     http://localhost"
echo "   • Backend API:          http://localhost/api"
echo "   • Documentación API:    http://localhost/docs"
echo "   • Health Check:         http://localhost/health"
echo "   • Estadísticas:         http://localhost/users/stats"
echo ""
echo "🔧 Puertos internos:"
echo "   • Redis:               localhost:6379"
echo "   • Backend directo:     localhost:8000"  
echo "   • Frontend directo:    localhost:3000"
echo ""
echo "📋 Comandos útiles:"
echo "   • Ver logs:            cd docker && docker-compose logs -f"
echo "   • Ver logs Backend:    cd docker && docker-compose logs -f backend"
echo "   • Ver logs Frontend:   cd docker && docker-compose logs -f frontend"
echo "   • Reiniciar:           cd docker && docker-compose restart"
echo "   • Parar:               cd docker && docker-compose down"
echo "   • Actualizar:          cd docker && docker-compose up --build -d"
echo ""
echo "📁 Estructura del monorepo:"
echo "   • backend/             Código del API FastAPI"
echo "   • frontend/            Código de la interfaz React"
echo "   • docker/              Configuraciones Docker"
echo "   • scripts/             Scripts de automatización"
echo "   • tests/               Tests de integración"
echo "   • .github/             CI/CD workflows"
echo ""
echo "💡 Tip: Para desarrollo local:"
echo "   Backend:  cd backend && python src/main.py"
echo "   Frontend: cd frontend && npm run dev"
echo ""

# Mostrar logs de los últimos 50 líneas
print_status "Últimos logs de los servicios:"
docker-compose logs --tail=50 