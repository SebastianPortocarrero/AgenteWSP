# 🚀 Despliegue Local con Docker - Tony WhatsApp Assistant

Este documento explica cómo hostear tu agente de WhatsApp (backend) y el frontend en producción usando Docker, sin necesidad de pagar por servicios en la nube.

## 📋 Requisitos Previos

### 1. Instalar Docker
- **Windows**: Descargar [Docker Desktop](https://www.docker.com/products/docker-desktop)
- **macOS**: Descargar [Docker Desktop](https://www.docker.com/products/docker-desktop)
- **Linux**: Seguir las [instrucciones oficiales](https://docs.docker.com/engine/install/)

### 2. Verificar Instalación
```bash
docker --version
docker-compose --version
```

## 🏗️ Arquitectura del Sistema

El sistema está compuesto por 4 servicios principales:

```
┌─────────────────┐    ┌─────────────────┐
│     Nginx       │    │    Frontend     │
│  (Proxy Reverso)│    │    (React)      │
│   Puerto 80     │    │   Puerto 3000   │
└─────────────────┘    └─────────────────┘
         │                       │
         └───────────────────────┘
                    │
    ┌─────────────────┐    ┌─────────────────┐
    │     Backend     │    │     Redis       │
    │   (FastAPI)     │    │    (Cache)      │
    │   Puerto 8000   │    │   Puerto 6379   │
    └─────────────────┘    └─────────────────┘
```

## 🚀 Despliegue Rápido

### Opción 1: Script Automático (Recomendado)

#### Para Linux/macOS:
```bash
chmod +x deploy-local.sh
./deploy-local.sh
```

#### Para Windows (PowerShell):
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\deploy-local.ps1
```

### Opción 2: Despliegue Manual

#### 1. Preparar el entorno
```bash
# Crear directorio SSL
mkdir -p AgenteTony/ssl

# Cambiar al directorio del backend
cd AgenteTony
```

#### 2. Levantar los servicios
```bash
# Construir y levantar en segundo plano
docker-compose -f docker-compose.prod.yml up --build -d

# Ver logs en tiempo real
docker-compose -f docker-compose.prod.yml logs -f
```

## 📱 Acceso a los Servicios

Una vez desplegado, tendrás acceso a:

| Servicio | URL | Descripción |
|----------|-----|-------------|
| **Frontend** | http://localhost | Interfaz de usuario React |
| **Backend API** | http://localhost/api | API endpoints |
| **Documentación** | http://localhost/api/docs | Swagger UI |
| **Health Check** | http://localhost/health | Estado del sistema |
| **Estadísticas** | http://localhost/users/stats | Métricas de usuarios |

### Puertos Internos (si necesitas acceso directo):
- **Redis**: `localhost:6379`
- **Backend**: `localhost:8000`
- **Frontend**: `localhost:3000`

## 🔧 Gestión de Servicios

### Ver Estado de los Servicios
```bash
cd AgenteTony
docker-compose -f docker-compose.prod.yml ps
```

### Ver Logs
```bash
# Todos los servicios
docker-compose -f docker-compose.prod.yml logs -f

# Solo backend
docker-compose -f docker-compose.prod.yml logs -f backend

# Solo frontend
docker-compose -f docker-compose.prod.yml logs -f frontend

# Solo nginx
docker-compose -f docker-compose.prod.yml logs -f nginx
```

### Reiniciar Servicios
```bash
# Reiniciar todos
docker-compose -f docker-compose.prod.yml restart

# Reiniciar servicio específico
docker-compose -f docker-compose.prod.yml restart backend
```

### Parar Servicios
```bash
# Parar todos los servicios
docker-compose -f docker-compose.prod.yml down

# Parar y eliminar volúmenes
docker-compose -f docker-compose.prod.yml down -v
```

### Actualizar Servicios
```bash
# Reconstruir y actualizar
docker-compose -f docker-compose.prod.yml up --build -d
```

## 🔒 Configuración de SSL (Opcional)

Para habilitar HTTPS:

### 1. Obtener Certificados SSL
```bash
# Usando Let's Encrypt (ejemplo)
certbot certonly --standalone -d tudominio.com
```

### 2. Copiar Certificados
```bash
# Copiar a la carpeta ssl
cp /etc/letsencrypt/live/tudominio.com/fullchain.pem AgenteTony/ssl/
cp /etc/letsencrypt/live/tudominio.com/privkey.pem AgenteTony/ssl/
```

### 3. Actualizar nginx.conf
Descomenta y ajusta las líneas SSL en `AgenteTony/nginx.conf`:
```nginx
ssl_certificate /etc/nginx/ssl/fullchain.pem;
ssl_certificate_key /etc/nginx/ssl/privkey.pem;
```

## 🌐 Configuración de Dominio

### 1. Configurar DNS
Apunta tu dominio a la IP de tu servidor:
```
A  @  123.456.789.123
A  www  123.456.789.123
```

### 2. Actualizar Variables de Entorno
En `AgenteTony/docker-compose.prod.yml`:
```yaml
environment:
  DOMAIN: tudominio.com
```

### 3. Actualizar Nginx
Modifica `server_name` en `AgenteTony/nginx.conf`:
```nginx
server_name tudominio.com www.tudominio.com;
```

## 🐛 Solución de Problemas

### Error: Puerto ya en uso
```bash
# Ver qué está usando el puerto 80
sudo netstat -tulnp | grep :80

# Parar Apache/Nginx local si está corriendo
sudo systemctl stop apache2
sudo systemctl stop nginx
```

### Error: Docker no puede construir
```bash
# Limpiar cache de Docker
docker system prune -a

# Reconstruir sin cache
docker-compose -f docker-compose.prod.yml build --no-cache
```

### Error: Servicios no responden
```bash
# Verificar logs
docker-compose -f docker-compose.prod.yml logs

# Verificar salud de contenedores
docker-compose -f docker-compose.prod.yml ps
```

### Error: Frontend no carga
```bash
# Verificar configuración de API
# El frontend busca el backend en http://localhost/api
# Asegúrate de que Nginx esté redirigiendo correctamente
```

## 📊 Monitoreo

### Verificar Recursos
```bash
# Uso de recursos por contenedor
docker stats

# Espacio en disco
docker system df
```

### Logs de Sistema
```bash
# Logs del sistema Docker
journalctl -u docker.service

# Logs de contenedores específicos
docker logs <container_id>
```

## 💡 Optimizaciones para Producción

### 1. Limitar Recursos
En `docker-compose.prod.yml`:
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '0.50'
          memory: 512M
```

### 2. Configurar Backups
```bash
# Backup de Redis
docker exec redis redis-cli BGSAVE

# Backup de configuración
tar -czf backup-$(date +%Y%m%d).tar.gz AgenteTony/config/
```

### 3. Configurar Rotación de Logs
```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

## 🔄 Actualizaciones

### Proceso de Actualización
1. Hacer backup de configuración
2. Parar servicios: `docker-compose down`
3. Actualizar código
4. Reconstruir: `docker-compose up --build -d`
5. Verificar funcionamiento

### Rollback
```bash
# Usar imagen anterior
docker-compose down
docker-compose up -d
```

## 📞 Soporte

Si encuentras problemas:
1. Revisar logs: `docker-compose logs -f`
2. Verificar configuración de puertos
3. Comprobar variables de entorno
4. Verificar que Docker tiene suficientes recursos

---

## 🎯 Resumen

Con esta configuración tienes:
- ✅ **Backend FastAPI** con tu agente de WhatsApp
- ✅ **Frontend React** para gestión
- ✅ **Redis** para cache y persistencia
- ✅ **Nginx** como proxy reverso
- ✅ **SSL ready** para cuando quieras HTTPS
- ✅ **Escalable** y **mantenible**

¡Todo funcionando en tu propia máquina sin costos de nube! 🚀 