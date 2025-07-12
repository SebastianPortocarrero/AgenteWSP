#!/usr/bin/env python3
"""
Script para explorar las bases de datos SQLite de Tony
Muestra estadísticas, contenido y estructura de las bases de datos
"""

import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path

def format_size(size_bytes):
    """Formatear tamaño en bytes a formato legible"""
    if size_bytes == 0:
        return "0 B"
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.2f} {size_names[i]}"

def get_db_info(db_path):
    """Obtener información básica de una base de datos"""
    if not os.path.exists(db_path):
        return None
    
    file_size = os.path.getsize(db_path)
    modified_time = datetime.fromtimestamp(os.path.getmtime(db_path))
    
    return {
        'path': db_path,
        'size': file_size,
        'size_formatted': format_size(file_size),
        'modified': modified_time,
        'exists': True
    }

def explore_messages_db():
    """Explorar la base de datos de mensajes"""
    print("🔍 EXPLORANDO BASE DE DATOS DE MENSAJES (messages.db)")
    print("=" * 60)
    
    db_info = get_db_info("messages.db")
    if not db_info:
        print("❌ No se encontró messages.db")
        return
    
    print(f"📁 Archivo: {db_info['path']}")
    print(f"📊 Tamaño: {db_info['size_formatted']}")
    print(f"🕒 Última modificación: {db_info['modified']}")
    print()
    
    try:
        conn = sqlite3.connect("messages.db")
        cursor = conn.cursor()
        
        # Obtener tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print("📋 TABLAS ENCONTRADAS:")
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  • {table_name}: {count} registros")
        
        print()
        
        # Estadísticas de conversaciones
        cursor.execute("""
            SELECT 
                COUNT(*) as total_conversations,
                COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending,
                COUNT(CASE WHEN status = 'active' THEN 1 END) as active,
                COUNT(CASE WHEN status = 'closed' THEN 1 END) as closed,
                COUNT(CASE WHEN mode = 'auto' THEN 1 END) as auto_mode,
                COUNT(CASE WHEN mode = 'manual' THEN 1 END) as manual_mode
            FROM conversations
        """)
        stats = cursor.fetchone()
        
        print("💬 ESTADÍSTICAS DE CONVERSACIONES:")
        print(f"  • Total: {stats[0]}")
        print(f"  • Pendientes: {stats[1]}")
        print(f"  • Activas: {stats[2]}")
        print(f"  • Cerradas: {stats[3]}")
        print(f"  • Modo automático: {stats[4]}")
        print(f"  • Modo manual: {stats[5]}")
        print()
        
        # Estadísticas de mensajes
        cursor.execute("""
            SELECT 
                COUNT(*) as total_messages,
                COUNT(CASE WHEN sender_type = 'user' THEN 1 END) as user_messages,
                COUNT(CASE WHEN sender_type = 'assistant' THEN 1 END) as assistant_messages,
                COUNT(CASE WHEN status = 'read' THEN 1 END) as read_messages,
                COUNT(CASE WHEN status = 'sent' THEN 1 END) as sent_messages
            FROM messages
        """)
        msg_stats = cursor.fetchone()
        
        print("💭 ESTADÍSTICAS DE MENSAJES:")
        print(f"  • Total: {msg_stats[0]}")
        print(f"  • Del usuario: {msg_stats[1]}")
        print(f"  • Del asistente: {msg_stats[2]}")
        print(f"  • Leídos: {msg_stats[3]}")
        print(f"  • Enviados: {msg_stats[4]}")
        print()
        
        # Últimas conversaciones
        cursor.execute("""
            SELECT user_name, status, mode, updated_at, 
                   (SELECT COUNT(*) FROM messages WHERE conversation_id = conversations.id) as message_count
            FROM conversations 
            ORDER BY updated_at DESC 
            LIMIT 5
        """)
        recent_convs = cursor.fetchall()
        
        print("🕐 ÚLTIMAS 5 CONVERSACIONES:")
        for conv in recent_convs:
            print(f"  • {conv[0]} - {conv[1]} ({conv[2]}) - {conv[4]} mensajes - {conv[3]}")
        
        print()
        
        # Operadores
        cursor.execute("SELECT name, email, status FROM operators")
        operators = cursor.fetchall()
        
        if operators:
            print("👥 OPERADORES:")
            for op in operators:
                print(f"  • {op[0]} ({op[1]}) - {op[2]}")
        else:
            print("👥 No hay operadores registrados")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error explorando messages.db: {e}")

def explore_memory_db():
    """Explorar la base de datos de memoria"""
    print("\n🧠 EXPLORANDO BASE DE DATOS DE MEMORIA (memory_data/memory.db)")
    print("=" * 60)
    
    db_info = get_db_info("memory_data/memory.db")
    if not db_info:
        print("❌ No se encontró memory_data/memory.db")
        return
    
    print(f"📁 Archivo: {db_info['path']}")
    print(f"📊 Tamaño: {db_info['size_formatted']}")
    print(f"🕒 Última modificación: {db_info['modified']}")
    print()
    
    try:
        conn = sqlite3.connect("memory_data/memory.db")
        cursor = conn.cursor()
        
        # Obtener tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print("📋 TABLAS ENCONTRADAS:")
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  • {table_name}: {count} registros")
        
        print()
        
        # Estadísticas de memoria episódica
        cursor.execute("""
            SELECT 
                COUNT(*) as total_messages,
                COUNT(DISTINCT session_id) as unique_sessions,
                COUNT(CASE WHEN message_type = 'human' THEN 1 END) as human_messages,
                COUNT(CASE WHEN message_type = 'ai' THEN 1 END) as ai_messages,
                COUNT(CASE WHEN message_type = 'system' THEN 1 END) as system_messages
            FROM episodic_memory
        """)
        episodic_stats = cursor.fetchone()
        
        print("🧠 ESTADÍSTICAS DE MEMORIA EPISÓDICA:")
        print(f"  • Total mensajes: {episodic_stats[0]}")
        print(f"  • Sesiones únicas: {episodic_stats[1]}")
        print(f"  • Mensajes humanos: {episodic_stats[2]}")
        print(f"  • Mensajes AI: {episodic_stats[3]}")
        print(f"  • Mensajes sistema: {episodic_stats[4]}")
        print()
        
        # Estadísticas de memoria semántica
        cursor.execute("""
            SELECT 
                COUNT(*) as total_concepts,
                COUNT(DISTINCT session_id) as unique_sessions,
                COUNT(DISTINCT category) as unique_categories,
                AVG(confidence) as avg_confidence
            FROM semantic_memory
        """)
        semantic_stats = cursor.fetchone()
        
        print("📚 ESTADÍSTICAS DE MEMORIA SEMÁNTICA:")
        print(f"  • Total conceptos: {semantic_stats[0]}")
        print(f"  • Sesiones únicas: {semantic_stats[1]}")
        print(f"  • Categorías únicas: {semantic_stats[2]}")
        print(f"  • Confianza promedio: {semantic_stats[3]:.2f}")
        print()
        
        # Estadísticas de memoria procedimental
        cursor.execute("""
            SELECT 
                COUNT(*) as total_procedures,
                COUNT(DISTINCT session_id) as unique_sessions,
                AVG(success_rate) as avg_success_rate,
                SUM(usage_count) as total_usage
            FROM procedural_memory
        """)
        procedural_stats = cursor.fetchone()
        
        print("⚙️ ESTADÍSTICAS DE MEMORIA PROCEDIMENTAL:")
        print(f"  • Total procedimientos: {procedural_stats[0]}")
        print(f"  • Sesiones únicas: {procedural_stats[1]}")
        print(f"  • Tasa de éxito promedio: {procedural_stats[2]:.2f}")
        print(f"  • Total usos: {procedural_stats[3]}")
        print()
        
        # Últimas sesiones activas
        cursor.execute("""
            SELECT session_id, last_activity, total_messages
            FROM session_metadata 
            ORDER BY last_activity DESC 
            LIMIT 5
        """)
        recent_sessions = cursor.fetchall()
        
        if recent_sessions:
            print("🕐 ÚLTIMAS 5 SESIONES ACTIVAS:")
            for session in recent_sessions:
                print(f"  • {session[0]} - {session[2]} mensajes - {session[1]}")
        else:
            print("🕐 No hay sesiones registradas")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error explorando memory.db: {e}")

def show_sample_data():
    """Mostrar muestras de datos"""
    print("\n📄 MUESTRAS DE DATOS")
    print("=" * 60)
    
    # Muestra de conversaciones
    try:
        conn = sqlite3.connect("messages.db")
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT user_name, status, mode, updated_at
            FROM conversations 
            ORDER BY updated_at DESC 
            LIMIT 3
        """)
        conversations = cursor.fetchall()
        
        if conversations:
            print("💬 MUESTRA DE CONVERSACIONES:")
            for conv in conversations:
                print(f"  • Usuario: {conv[0]}")
                print(f"    Estado: {conv[1]}, Modo: {conv[2]}")
                print(f"    Última actividad: {conv[3]}")
                print()
        
        # Muestra de mensajes
        cursor.execute("""
            SELECT sender_type, content, timestamp
            FROM messages 
            ORDER BY timestamp DESC 
            LIMIT 3
        """)
        messages = cursor.fetchall()
        
        if messages:
            print("💭 MUESTRA DE MENSAJES:")
            for msg in messages:
                content_preview = msg[1][:50] + "..." if len(msg[1]) > 50 else msg[1]
                print(f"  • {msg[0]}: {content_preview}")
                print(f"    {msg[2]}")
                print()
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error mostrando muestras: {e}")

def main():
    """Función principal"""
    print("🔍 EXPLORADOR DE BASES DE DATOS SQLITE - TONY")
    print("=" * 60)
    print()
    
    # Explorar ambas bases de datos
    explore_messages_db()
    explore_memory_db()
    show_sample_data()
    
    print("\n✅ Exploración completada!")
    print("\n💡 CONSEJOS:")
    print("  • Las bases de datos se crean automáticamente al usar la aplicación")
    print("  • Los datos persisten entre reinicios del servidor")
    print("  • Puedes usar herramientas como DB Browser for SQLite para explorar visualmente")
    print("  • Los archivos .db se pueden respaldar copiándolos")

if __name__ == "__main__":
    main() 