# Configuración de Google Drive

## Pasos para configurar Google Drive

### 1. Obtener credenciales de Google Cloud

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un proyecto nuevo o selecciona uno existente
3. Habilita la API de Google Drive
4. Ve a "Credenciales" → "Crear credenciales" → "ID de cliente OAuth"
5. Selecciona "Aplicación de escritorio"
6. Descarga el archivo JSON y guárdalo como `config/client_secret.json`

### 2. Estructura de archivos

```
AgenteTony/
├── config/
│   ├── client_secret.json  (descargar desde Google Cloud)
│   └── token.json          (se genera automáticamente)
```

### 3. Primera ejecución

Al ejecutar por primera vez, se abrirá un navegador web para autenticarte:

1. Autoriza la aplicación
2. El archivo `token.json` se creará automáticamente
3. Las siguientes ejecuciones serán automáticas

### 4. Uso

El sistema automáticamente:
- Detecta si Google Drive está configurado
- Usa MCP Google Drive si está disponible
- Fallback a indexación tradicional si hay problemas

### 5. Verificación

Para verificar que funciona:

```bash
cd AgenteTony/src
python indexador.py
```

Si Google Drive está configurado, verás:
```
🚀 Usando Google Drive MCP...
✅ Autenticación con Google Drive exitosa
📄 Procesando: documento.pdf
```

Si no está configurado, usará el método tradicional:
```
📚 Usando indexación tradicional...
``` 