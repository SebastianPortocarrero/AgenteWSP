#!/usr/bin/env python3
"""
Script para iniciar el servidor en modo desarrollo (con reload)
"""

import uvicorn

if __name__ == "__main__":
    print("🔧 Iniciando Tony WhatsApp Assistant - MODO DESARROLLO")
    print("=" * 60)
    print("📍 Servidor: http://localhost:8000")
    print("📚 Documentación: http://localhost:8000/docs")
    print("🔄 Auto-reload: HABILITADO")
    print("⚠️  Solo para desarrollo - no usar en producción")
    print("=" * 60)
    
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="debug",
        reload_excludes=[
            "*.db", 
            "*.log", 
            "test_*.py", 
            "*_test.py",
            "memory_data/*",
            "messages.db",
            "__pycache__/*",
            "*.pyc"
        ]
    )