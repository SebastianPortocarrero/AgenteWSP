#!/usr/bin/env python3
"""
Script para iniciar el servidor en modo producción (sin reload)
"""

import uvicorn

if __name__ == "__main__":
    print("🚀 Iniciando Tony WhatsApp Assistant - MODO PRODUCCIÓN")
    print("=" * 60)
    print("📍 Servidor: http://localhost:8000")
    print("📚 Documentación: http://localhost:8000/docs")
    print("🔄 Auto-reload: DESHABILITADO")
    print("💾 Persistencia: HABILITADA")
    print("=" * 60)
    
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Sin reload para estabilidad
        log_level="info",
        access_log=True
    )