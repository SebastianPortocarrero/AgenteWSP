# Script de despliegue local con Docker para Windows
# Tony - Asistente de RRHH

Write-Host "🚀 Iniciando despliegue local de Tony (Frontend + Backend)" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

# Función para mostrar mensajes con colores
function Write-Status {
    param($Message)
    Write-Host "[INFO] $Message" -ForegroundColor Blue
}

function Write-Success {
    param($Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Warning {
    param($Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param($Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# Verificar si Docker está instalado
if (!(Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error "Docker no está instalado. Por favor, instala Docker Desktop primero."
    exit 1
}

# Verificar si Docker Compose está instalado
if (!(Get-Command docker-compose -ErrorAction SilentlyContinue)) {
    Write-Error "Docker Compose no está instalado. Por favor, instala Docker Compose primero."
    exit 1
}

# Cambiar al directorio del proyecto
Set-Location $PSScriptRoot

Write-Status "Verificando estructura del proyecto..."

# Verificar que existan los directorios necesarios
if (!(Test-Path "AgenteTony")) {
    Write-Error "No se encontró el directorio 'AgenteTony'"
    exit 1
}

if (!(Test-Path "FrontTony")) {
    Write-Error "No se encontró el directorio 'FrontTony'"
    exit 1
}

Write-Success "Estructura del proyecto verificada ✓"

# Crear directorio SSL si no existe
Write-Status "Creando directorio SSL..."
if (!(Test-Path "AgenteTony\ssl")) {
    New-Item -ItemType Directory -Path "AgenteTony\ssl" -Force
}

# Parar servicios existentes si están corriendo
Write-Status "Deteniendo servicios existentes..."
Set-Location AgenteTony
docker-compose -f docker-compose.prod.yml down --remove-orphans 2>$null

# Limpiar imágenes y contenedores antiguos (opcional)
Write-Status "Limpiando imágenes Docker antiguas..."
docker system prune -f

# Construir y levantar los servicios
Write-Status "Construyendo y levantando servicios..."
docker-compose -f docker-compose.prod.yml up --build -d

# Verificar que los servicios estén funcionando
Write-Status "Verificando servicios..."
Start-Sleep 10

# Verificar servicios
$services = @("redis", "backend", "frontend", "nginx")
foreach ($service in $services) {
    $status = docker-compose -f docker-compose.prod.yml ps $service
    if ($status -match "Up") {
        Write-Success "$service está funcionando ✓"
    } else {
        Write-Error "$service no está funcionando ✗"
    }
}

# Mostrar estado de los servicios
Write-Status "Estado de los servicios:"
docker-compose -f docker-compose.prod.yml ps

# Mostrar información de acceso
Write-Host ""
Write-Host "🎉 ¡Despliegue completado!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "📱 Servicios disponibles:" -ForegroundColor Cyan
Write-Host "   • Frontend (React):     http://localhost" -ForegroundColor White
Write-Host "   • Backend API:          http://localhost/api" -ForegroundColor White
Write-Host "   • Documentación API:    http://localhost/api/docs" -ForegroundColor White
Write-Host "   • Health Check:         http://localhost/health" -ForegroundColor White
Write-Host "   • Estadísticas:         http://localhost/users/stats" -ForegroundColor White
Write-Host ""
Write-Host "🔧 Puertos internos:" -ForegroundColor Cyan
Write-Host "   • Redis:               localhost:6379" -ForegroundColor White
Write-Host "   • Backend directo:     localhost:8000" -ForegroundColor White
Write-Host "   • Frontend directo:    localhost:3000" -ForegroundColor White
Write-Host ""
Write-Host "📋 Comandos útiles:" -ForegroundColor Cyan
Write-Host "   • Ver logs:            docker-compose -f docker-compose.prod.yml logs -f" -ForegroundColor White
Write-Host "   • Ver logs Backend:    docker-compose -f docker-compose.prod.yml logs -f backend" -ForegroundColor White
Write-Host "   • Ver logs Frontend:   docker-compose -f docker-compose.prod.yml logs -f frontend" -ForegroundColor White
Write-Host "   • Reiniciar:           docker-compose -f docker-compose.prod.yml restart" -ForegroundColor White
Write-Host "   • Parar:               docker-compose -f docker-compose.prod.yml down" -ForegroundColor White
Write-Host "   • Actualizar:          docker-compose -f docker-compose.prod.yml up --build -d" -ForegroundColor White
Write-Host ""
Write-Host "💡 Tip: Para ver los logs en tiempo real, usa:" -ForegroundColor Yellow
Write-Host "   docker-compose -f docker-compose.prod.yml logs -f" -ForegroundColor White
Write-Host ""

# Mostrar logs de los últimos 50 líneas
Write-Status "Últimos logs de los servicios:"
docker-compose -f docker-compose.prod.yml logs --tail=50 