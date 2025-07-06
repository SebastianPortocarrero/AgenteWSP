import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional
import uuid

class MessageDatabase:
    def __init__(self, db_path="messages.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Inicializar las tablas de la base de datos"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabla de conversaciones
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                whatsapp_chat_id TEXT UNIQUE,
                user_phone TEXT,
                user_name TEXT,
                status TEXT DEFAULT 'pending',
                mode TEXT DEFAULT 'auto',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                assigned_operator TEXT,
                tags TEXT DEFAULT '[]'
            )
        ''')
        
        # Tabla de mensajes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT,
                whatsapp_message_id TEXT UNIQUE,
                sender_type TEXT,
                content TEXT,
                message_type TEXT DEFAULT 'text',
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                edited BOOLEAN DEFAULT FALSE,
                status TEXT DEFAULT 'sent',
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
            )
        ''')
        
        # Tabla de operadores
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS operators (
                id TEXT PRIMARY KEY,
                name TEXT,
                email TEXT,
                status TEXT DEFAULT 'offline'
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_conversation(self, whatsapp_chat_id: str, user_phone: str, user_name: str) -> str:
        """Guardar o actualizar una conversación"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Verificar si ya existe
        cursor.execute(
            "SELECT id FROM conversations WHERE whatsapp_chat_id = ?",
            (whatsapp_chat_id,)
        )
        existing = cursor.fetchone()
        
        if existing:
            conversation_id = existing[0]
            # Actualizar nombre si cambió
            cursor.execute(
                "UPDATE conversations SET user_name = ?, updated_at = ? WHERE id = ?",
                (user_name, datetime.now(), conversation_id)
            )
        else:
            # Crear nueva conversación
            conversation_id = str(uuid.uuid4())
            cursor.execute(
                """INSERT INTO conversations 
                   (id, whatsapp_chat_id, user_phone, user_name) 
                   VALUES (?, ?, ?, ?)""",
                (conversation_id, whatsapp_chat_id, user_phone, user_name)
            )
        
        conn.commit()
        conn.close()
        return conversation_id
    
    def save_message(self, conversation_id: str, content: str, sender_type: str, 
                    whatsapp_message_id: str = None) -> str:
        """Guardar un mensaje en la base de datos"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        message_id = str(uuid.uuid4())
        
        cursor.execute(
            """INSERT INTO messages 
               (id, conversation_id, whatsapp_message_id, sender_type, content) 
               VALUES (?, ?, ?, ?, ?)""",
            (message_id, conversation_id, whatsapp_message_id, sender_type, content)
        )
        
        # Actualizar timestamp de la conversación
        cursor.execute(
            "UPDATE conversations SET updated_at = ? WHERE id = ?",
            (datetime.now(), conversation_id)
        )
        
        conn.commit()
        conn.close()
        return message_id
    
    def get_conversations(self) -> List[Dict]:
        """Obtener todas las conversaciones con el último mensaje"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                c.*,
                m.content as last_message,
                m.timestamp as last_message_time,
                COUNT(CASE WHEN m.status != 'read' AND m.sender_type = 'user' THEN 1 END) as unread_count
            FROM conversations c
            LEFT JOIN messages m ON c.id = m.conversation_id
            WHERE m.timestamp = (
                SELECT MAX(timestamp) 
                FROM messages 
                WHERE conversation_id = c.id
            ) OR m.timestamp IS NULL
            GROUP BY c.id
            ORDER BY c.updated_at DESC
        ''')
        
        conversations = []
        for row in cursor.fetchall():
            conversations.append({
                'id': row[0],
                'whatsapp_chat_id': row[1],
                'user_phone': row[2],
                'user_name': row[3],
                'status': row[4],
                'mode': row[5],
                'created_at': row[6],
                'updated_at': row[7],
                'assigned_operator': row[8],
                'tags': json.loads(row[9] or '[]'),
                'last_message': row[10],
                'last_message_time': row[11],
                'unread_count': row[12]
            })
        
        conn.close()
        return conversations
    
    def get_messages(self, conversation_id: str) -> List[Dict]:
        """Obtener todos los mensajes de una conversación"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            """SELECT * FROM messages 
               WHERE conversation_id = ? 
               ORDER BY timestamp ASC""",
            (conversation_id,)
        )
        
        messages = []
        for row in cursor.fetchall():
            messages.append({
                'id': row[0],
                'conversation_id': row[1],
                'whatsapp_message_id': row[2],
                'sender_type': row[3],
                'content': row[4],
                'message_type': row[5],
                'timestamp': row[6],
                'edited': bool(row[7]),
                'status': row[8]
            })
        
        conn.close()
        return messages
    
    def update_conversation_mode(self, conversation_id: str, mode: str):
        """Actualizar el modo de una conversación"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE conversations SET mode = ?, updated_at = ? WHERE id = ?",
            (mode, datetime.now(), conversation_id)
        )
        
        conn.commit()
        conn.close()
    
    def mark_messages_as_read(self, conversation_id: str):
        """Marcar todos los mensajes de una conversación como leídos"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE messages SET status = 'read' WHERE conversation_id = ? AND sender_type = 'user'",
            (conversation_id,)
        )
        
        conn.commit()
        conn.close()

# Instancia global
message_db = MessageDatabase() 