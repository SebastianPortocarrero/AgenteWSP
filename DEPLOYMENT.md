# 🚀 Guía de Despliegue - Tony WhatsApp Assistant

Esta guía te ayudará a desplegar tu aplicación en **Vercel** (Frontend) + **Railway** (Backend) con CI/CD automático.

## 📋 Prerrequisitos

- Cuenta en [GitHub](https://github.com)
- Cuenta en [Vercel](https://vercel.com)
- Cuenta en [Railway](https://railway.app)
- Credenciales de API (OpenAI, Supabase, etc.)

## 🛠️ Paso 1: Preparar el Repositorio

### 1.1 Subir el código a GitHub
```bash
git add .
git commit -m "Preparar para despliegue en Vercel + Railway"
git push origin main
```

## 🚂 Paso 2: Configurar Railway (Backend)

### 2.1 Crear proyecto en Railway
1. Ve a [railway.app](https://railway.app)
2. Haz clic en "New Project"
3. Conecta tu repositorio de GitHub
4. Selecciona el directorio `backend`

### 2.2 Configurar variables de entorno en Railway
En el dashboard de Railway, ve a Variables y agrega:

```env
# Database
SUPABASE_URL=tu_supabase_url
SUPABASE_KEY=tu_supabase_key

# AI
OPENAI_API_KEY=tu_openai_key
SERPAPI_API_KEY=tu_serpapi_key

# WhatsApp
WHATSAPP_ACCESS_TOKEN=tu_whatsapp_token
WHATSAPP_PHONE_NUMBER_ID=tu_phone_id
WHATSAPP_VERIFY_TOKEN=tu_verify_token

# CORS (importante para Vercel)
ALLOWED_ORIGINS=https://tu-app.vercel.app,https://www.tu-dominio.com

# Environment
ENVIRONMENT=production
PORT=8000
```

### 2.3 Configurar dominio personalizado (opcional)
1. En Railway, ve a Settings > Domains
2. Agrega tu dominio personalizado
3. Anota la URL generada (ej: `https://tu-app.railway.app`)

## ⚡ Paso 3: Configurar Vercel (Frontend)

### 3.1 Crear proyecto en Vercel
1. Ve a [vercel.com](https://vercel.com)
2. Importa tu repositorio de GitHub
3. Selecciona el directorio `frontend`
4. Framework: Vite
5. Build Command: `npm run build`
6. Output Directory: `dist`

### 3.2 Configurar variables de entorno en Vercel
En el dashboard de Vercel, ve a Settings > Environment Variables:

```env
VITE_API_BASE_URL=https://tu-backend.railway.app
VITE_NODE_ENV=production
```

### 3.3 Configurar dominio personalizado (opcional)
1. En Vercel, ve a Settings > Domains
2. Agrega tu dominio personalizado

## 🔧 Paso 4: Configurar CI/CD

### 4.1 Obtener tokens necesarios

#### Railway Token:
1. Ve a Railway > Account Settings > Tokens
2. Crea un nuevo token
3. Guárdalo como `RAILWAY_TOKEN`

#### Vercel Token:
1. Ve a Vercel > Settings > Tokens
2. Crea un nuevo token
3. Guárdalo como `VERCEL_TOKEN`

#### Vercel Project IDs:
```bash
# Instalar Vercel CLI
npm i -g vercel

# En la carpeta frontend
cd frontend
vercel login
vercel link

# Obtener IDs
vercel env ls
```

### 4.2 Configurar GitHub Secrets
En tu repositorio de GitHub, ve a Settings > Secrets and Variables > Actions:

```env
# Railway
RAILWAY_TOKEN=tu_railway_token
RAILWAY_SERVICE_NAME=tony-backend

# Vercel
VERCEL_TOKEN=tu_vercel_token
VERCEL_ORG_ID=tu_org_id
VERCEL_PROJECT_ID=tu_project_id

# URLs para testing
VITE_API_BASE_URL_PROD=https://tu-backend.railway.app
VERCEL_DOMAIN=tu-app.vercel.app
RAILWAY_DOMAIN=tu-backend.railway.app
```

## 🚀 Paso 5: Primer Despliegue

### 5.1 Activar el workflow
```bash
git add .
git commit -m "Configurar CI/CD para Vercel + Railway"
git push origin main
```

### 5.2 Monitorear el despliegue
1. Ve a GitHub > Actions
2. Observa el workflow "Deploy to Vercel + Railway"
3. Verifica que todos los pasos se completen exitosamente

## ✅ Paso 6: Verificar el despliegue

### 6.1 Verificar backend
```bash
curl https://tu-backend.railway.app/health
```

### 6.2 Verificar frontend
1. Abre `https://tu-frontend.vercel.app`
2. Verifica que se conecte correctamente al backend
3. Prueba login y funcionalidades básicas

## 🔄 Despliegues Automáticos

Una vez configurado, cada push a `main` disparará automáticamente:
1. ✅ Tests del backend
2. ✅ Tests del frontend
3. 🚀 Despliegue a Railway (backend)
4. 🚀 Despliegue a Vercel (frontend)

## 🐛 Solución de Problemas

### Backend no se conecta
- Verifica variables de entorno en Railway
- Revisa logs en Railway Dashboard
- Confirma que el health endpoint responde

### Frontend no se conecta al backend
- Verifica `VITE_API_BASE_URL` en Vercel
- Confirma CORS configurado en Railway
- Revisa console del navegador

### CI/CD falla
- Verifica GitHub Secrets
- Revisa logs en GitHub Actions
- Confirma que tokens no hayan expirado

## 📚 Recursos Adicionales

- [Railway Docs](https://docs.railway.app)
- [Vercel Docs](https://vercel.com/docs)
- [GitHub Actions Docs](https://docs.github.com/en/actions)

## 🎉 ¡Listo!

Tu aplicación ahora está desplegada con CI/CD automático. Cada cambio en `main` se desplegará automáticamente a producción.

**URLs de tu aplicación:**
- Frontend: `https://tu-app.vercel.app`
- Backend: `https://tu-app.railway.app`
- API Health: `https://tu-app.railway.app/health`