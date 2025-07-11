#!/usr/bin/env python3
"""
Script para limpiar la base de datos de pruebas
"""

import os
import sys

# Agregar el directorio src al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database_manager import message_db

def clean_test_database():
    """Limpia la base de datos de pruebas"""
    print("🧹 Limpiando base de datos de pruebas...")
    
    try:
        # Eliminar archivo de base de datos si existe
        db_path = message_db.db_path
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"   ✅ Archivo de BD eliminado: {db_path}")
        
        # Reinicializar la base de datos
        message_db.init_database()
        print("   ✅ Base de datos reinicializada")
        
        # Verificar que está vacía
        conversations = message_db.get_conversations()
        print(f"   📊 Conversaciones en BD: {len(conversations)}")
        
        if len(conversations) == 0:
            print("   ✅ Base de datos limpia y lista para pruebas")
            return True
        else:
            print("   ❌ La base de datos no está completamente limpia")
            return False
            
    except Exception as e:
        print(f"   ❌ Error limpiando BD: {e}")
        return False

if __name__ == "__main__":
    success = clean_test_database()
    exit(0 if success else 1)