import time
import json
import sqlite3
import pickle
import gzip
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from threading import Lock, Timer
from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
from utilidades import SUPABASE_URL, SUPABASE_KEY, get_supabase_headers, make_supabase_request
# ============================================================================
# 💾 CAPA DE PERSISTENCIA LOCAL
# ============================================================================

class LocalMemoryPersistence:
    """Capa de persistencia local para memoria de largo plazo"""
    
    def __init__(self, base_path: str = "memory_data"):
        self.base_path = base_path
        self.db_path = os.path.join(base_path, "memory.db")
        self.lock = Lock()
        self._ensure_directory()
        self._init_local_db()
    
    def _ensure_directory(self):
        """Crear directorio si no existe"""
        os.makedirs(self.base_path, exist_ok=True)
    
    def _init_local_db(self):
        """Inicializar base de datos local SQLite"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Tabla para memoria episódica
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS episodic_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    message_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    synced_to_remote BOOLEAN DEFAULT FALSE
                )
            """)
            
            # Tabla para memoria semántica
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS semantic_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    concept TEXT NOT NULL,
                    knowledge TEXT NOT NULL,
                    category TEXT DEFAULT 'general',
                    confidence REAL DEFAULT 1.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    synced_to_remote BOOLEAN DEFAULT FALSE
                )
            """)
            
            # Tabla para memoria procedimental
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS procedural_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    procedure_name TEXT NOT NULL,
                    steps TEXT NOT NULL,
                    context TEXT DEFAULT '',
                    success_rate REAL DEFAULT 1.0,
                    usage_count INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    synced_to_remote BOOLEAN DEFAULT FALSE
                )
            """)
            
            # Tabla para metadatos de sesión
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS session_metadata (
                    session_id TEXT PRIMARY KEY,
                    last_activity TIMESTAMP,
                    total_messages INTEGER DEFAULT 0,
                    compressed_backup TEXT,
                    backup_timestamp TIMESTAMP
                )
            """)
            
            # Crear índices
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_episodic_session ON episodic_memory(session_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_semantic_session ON semantic_memory(session_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_procedural_session ON procedural_memory(session_id)")
            
            conn.commit()
    
    def save_episodic_message(self, session_id: str, message_type: str, content: str, metadata: Dict = None) -> int:
        """Guardar mensaje episódico localmente"""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO episodic_memory (session_id, message_type, content, metadata)
                    VALUES (?, ?, ?, ?)
                """, (session_id, message_type, content, json.dumps(metadata or {})))
                
                message_id = cursor.lastrowid
                self._update_session_activity(session_id, cursor)
                conn.commit()
                return message_id
    
    def save_semantic_knowledge(self, session_id: str, concept: str, knowledge: str, 
                               category: str = "general", confidence: float = 1.0) -> int:
        """Guardar conocimiento semántico localmente"""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO semantic_memory 
                    (session_id, concept, knowledge, category, confidence, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (session_id, concept, knowledge, category, confidence, datetime.now()))
                
                knowledge_id = cursor.lastrowid
                conn.commit()
                return knowledge_id
    
    def save_procedural_knowledge(self, session_id: str, procedure_name: str, steps: List[str],
                                 context: str = "", success_rate: float = 1.0) -> int:
        """Guardar procedimiento localmente"""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO procedural_memory 
                    (session_id, procedure_name, steps, context, success_rate, last_used)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (session_id, procedure_name, json.dumps(steps), context, success_rate, datetime.now()))
                
                proc_id = cursor.lastrowid
                conn.commit()
                return proc_id
    
    def get_episodic_messages(self, session_id: str, limit: int = None) -> List[Dict]:
        """Recuperar mensajes episódicos"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM episodic_memory WHERE session_id = ? ORDER BY created_at ASC"
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query, (session_id,))
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_semantic_knowledge(self, session_id: str, concept: str = None, category: str = None) -> List[Dict]:
        """Recuperar conocimiento semántico"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM semantic_memory WHERE session_id = ?"
            params = [session_id]
            
            if concept:
                query += " AND concept LIKE ?"
                params.append(f"%{concept}%")
            if category:
                query += " AND category = ?"
                params.append(category)
            
            cursor.execute(query, params)
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_procedural_knowledge(self, session_id: str, procedure_name: str = None) -> List[Dict]:
        """Recuperar conocimiento procedimental"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM procedural_memory WHERE session_id = ?"
            params = [session_id]
            
            if procedure_name:
                query += " AND procedure_name LIKE ?"
                params.append(f"%{procedure_name}%")
            
            cursor.execute(query, params)
            columns = [description[0] for description in cursor.description]
            results = []
            for row in cursor.fetchall():
                data = dict(zip(columns, row))
                data['steps'] = json.loads(data['steps'])
                results.append(data)
            return results
    
    def create_compressed_backup(self, session_id: str) -> str:
        """Crear backup comprimido de una sesión"""
        session_data = {
            'episodic': self.get_episodic_messages(session_id),
            'semantic': self.get_semantic_knowledge(session_id),
            'procedural': self.get_procedural_knowledge(session_id),
            'timestamp': datetime.now().isoformat()
        }
        
        # Comprimir datos
        compressed_data = gzip.compress(pickle.dumps(session_data))
        
        # Guardar en metadatos
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO session_metadata 
                (session_id, compressed_backup, backup_timestamp)
                VALUES (?, ?, ?)
            """, (session_id, compressed_data, datetime.now()))
            conn.commit()
        
        return f"Backup creado: {len(compressed_data)} bytes"
    
    def restore_from_backup(self, session_id: str) -> bool:
        """Restaurar sesión desde backup"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT compressed_backup FROM session_metadata WHERE session_id = ?",
                (session_id,)
            )
            result = cursor.fetchone()
            
            if not result or not result[0]:
                return False
            
            # Descomprimir y restaurar
            try:
                session_data = pickle.loads(gzip.decompress(result[0]))
                
                # Restaurar datos (solo si no existen)
                for msg in session_data['episodic']:
                    self.save_episodic_message(
                        session_id, msg['message_type'], msg['content'], 
                        json.loads(msg['metadata'])
                    )
                
                for knowledge in session_data['semantic']:
                    self.save_semantic_knowledge(
                        session_id, knowledge['concept'], knowledge['knowledge'],
                        knowledge['category'], knowledge['confidence']
                    )
                
                for proc in session_data['procedural']:
                    self.save_procedural_knowledge(
                        session_id, proc['procedure_name'], proc['steps'],
                        proc['context'], proc['success_rate']
                    )
                
                return True
            except Exception as e:
                print(f"Error restaurando backup: {e}")
                return False
    
    def _update_session_activity(self, session_id: str, cursor):
        """Actualizar actividad de sesión"""
        cursor.execute("""
            INSERT OR REPLACE INTO session_metadata 
            (session_id, last_activity, total_messages)
            VALUES (?, ?, COALESCE(
                (SELECT total_messages FROM session_metadata WHERE session_id = ?), 0
            ) + 1)
        """, (session_id, datetime.now(), session_id))
    
    def cleanup_old_sessions(self, days_old: int = 30) -> int:
        """Limpiar sesiones antiguas"""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Obtener sesiones a limpiar
            cursor.execute(
                "SELECT session_id FROM session_metadata WHERE last_activity < ?",
                (cutoff_date,)
            )
            old_sessions = [row[0] for row in cursor.fetchall()]
            
            # Crear backups antes de limpiar
            for session_id in old_sessions:
                self.create_compressed_backup(session_id)
            
            # Limpiar datos
            cursor.execute("DELETE FROM episodic_memory WHERE session_id IN ({})".format(
                ','.join(['?' for _ in old_sessions])), old_sessions)
            cursor.execute("DELETE FROM semantic_memory WHERE session_id IN ({})".format(
                ','.join(['?' for _ in old_sessions])), old_sessions)
            cursor.execute("DELETE FROM procedural_memory WHERE session_id IN ({})".format(
                ','.join(['?' for _ in old_sessions])), old_sessions)
            
            conn.commit()
            return len(old_sessions)

# ============================================================================
# 📚 MEMORIA EPISÓDICA - Conversaciones y eventos temporales
# ============================================================================

class EpisodicMemory:
    """Memoria episódica: almacena conversaciones completas con contexto temporal"""
    
    def __init__(self, session_id: str, table_name: str = "chat_history", local_persistence: LocalMemoryPersistence = None):
        self.session_id = session_id
        self.table_name = table_name
        self.local_persistence = local_persistence or LocalMemoryPersistence()
        self._message_cache = {}
        self._cache_ttl = 300  # 5 minutos
    
    @property
    def messages(self) -> List[BaseMessage]:
        """Obtiene todos los mensajes episódicos para esta sesión con fallback local"""
        cache_key = f"messages_{self.session_id}"
        current_time = time.time()
        
        # Verificar caché
        if cache_key in self._message_cache:
            cached_data, cache_time = self._message_cache[cache_key]
            if current_time - cache_time < self._cache_ttl:
                return cached_data
        
        messages = []
        
        # Intentar obtener desde Supabase primero
        try:
            response = make_supabase_request(
                method="GET",
                endpoint=self.table_name,
                params={
                    "session_id": f"eq.{self.session_id}",
                    "order": "created_at.asc"
                }
            )
            
            if response.status_code == 200:
                records = response.json()
                for record in records:
                    message_data = record.get('content', {})
                    message_type = record.get('message_type', 'human')
                    
                    if message_type == 'human':
                        messages.append(HumanMessage(content=message_data.get('content', '')))
                    elif message_type == 'ai':
                        messages.append(AIMessage(content=message_data.get('content', '')))
                    elif message_type == 'system':
                        messages.append(SystemMessage(content=message_data.get('content', '')))
                
                # Guardar en caché
                self._message_cache[cache_key] = (messages, current_time)
                return messages
                
        except Exception as e:
            print(f"Error conectando con Supabase, usando backup local: {str(e)}")
        
        # Fallback a persistencia local
        try:
            local_messages = self.local_persistence.get_episodic_messages(self.session_id)
            for record in local_messages:
                message_type = record['message_type']
                content = record['content']
                
                if message_type == 'human':
                    messages.append(HumanMessage(content=content))
                elif message_type == 'ai':
                    messages.append(AIMessage(content=content))
                elif message_type == 'system':
                    messages.append(SystemMessage(content=content))
            
            # Guardar en caché
            self._message_cache[cache_key] = (messages, current_time)
            return messages
            
        except Exception as e:
            print(f"Error en fallback local: {str(e)}")
            return []
    
    def add_message(self, message: BaseMessage, context: Dict = None) -> None:
        """Añade un mensaje episódico con contexto temporal y persistencia dual"""
        # Determinar el tipo de mensaje
        if isinstance(message, HumanMessage):
            message_type = 'human'
        elif isinstance(message, AIMessage):
            message_type = 'ai'
        elif isinstance(message, SystemMessage):
            message_type = 'system'
        else:
            message_type = 'unknown'
        
        # Metadata episódica enriquecida
        episodic_metadata = {
            "timestamp": datetime.now().isoformat(),
            "context": context or {},
            "message_length": len(message.content),
            "session_id": self.session_id
        }
        
        # Guardar localmente SIEMPRE primero
        try:
            self.local_persistence.save_episodic_message(
                self.session_id, message_type, message.content, episodic_metadata
            )
        except Exception as e:
            print(f"Error guardando mensaje local: {str(e)}")
        
        # Intentar guardar en Supabase
        try:
            data = {
                "session_id": self.session_id,
                "message_type": message_type,
                "content": {"content": message.content},
                "metadata": episodic_metadata,
                "created_at": datetime.now().isoformat()
            }
            
            response = make_supabase_request(
                method="POST",
                endpoint=self.table_name,
                data=data
            )
            
            if response.status_code != 201:
                print(f"Error guardando mensaje en Supabase: {response.status_code}, usando solo local")
                
        except Exception as e:
            print(f"Error conectando con Supabase: {str(e)}, mensaje guardado localmente")
        
        # Invalidar caché
        cache_key = f"messages_{self.session_id}"
        if cache_key in self._message_cache:
            del self._message_cache[cache_key]
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Obtiene un resumen de la conversación episódica"""
        messages = self.messages
        if not messages:
            return {"total_messages": 0, "summary": "Sin conversaciones"}
        
        return {
            "total_messages": len(messages),
            "first_message_time": messages[0].additional_kwargs.get('timestamp') if messages else None,
            "last_message_time": messages[-1].additional_kwargs.get('timestamp') if messages else None,
            "human_messages": len([m for m in messages if isinstance(m, HumanMessage)]),
            "ai_messages": len([m for m in messages if isinstance(m, AIMessage)])
        }
    
    def clear(self) -> None:
        """Limpia la memoria episódica"""
        try:
            response = make_supabase_request(
                method="DELETE",
                endpoint=self.table_name,
                params={"session_id": f"eq.{self.session_id}"}
            )
            
            if response.status_code not in [200, 204]:
                print(f"Error limpiando memoria episódica: {response.status_code}")
                
        except Exception as e:
            print(f"Error en clear episódico: {str(e)}")

# ============================================================================
# 🧠 MEMORIA SEMÁNTICA - Conocimiento y conceptos aprendidos
# ============================================================================

class SemanticMemory:
    """Memoria semántica: almacena conocimiento, hechos y conceptos aprendidos"""
    
    def __init__(self, session_id: str, table_name: str = "semantic_memory", local_persistence: LocalMemoryPersistence = None):
        self.session_id = session_id
        self.table_name = table_name
        self.local_persistence = local_persistence or LocalMemoryPersistence()
        self._knowledge_cache = {}
        self._cache_ttl = 600  # 10 minutos
    
    def store_knowledge(self, concept: str, knowledge: str, category: str = "general", confidence: float = 1.0) -> None:
        """Almacena conocimiento semántico con persistencia dual"""
        # Guardar localmente SIEMPRE primero
        try:
            self.local_persistence.save_semantic_knowledge(
                self.session_id, concept, knowledge, category, confidence
            )
        except Exception as e:
            print(f"Error guardando conocimiento local: {str(e)}")
        
        # Intentar guardar en Supabase
        try:
            data = {
                "session_id": self.session_id,
                "concept": concept,
                "knowledge": knowledge,
                "category": category,
                "confidence": confidence,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            response = make_supabase_request(
                method="POST",
                endpoint=self.table_name,
                data=data
            )
            
            if response.status_code == 201:
                print(f"🧠 Conocimiento semántico guardado: {concept}")
            else:
                print(f"Error guardando en Supabase: {response.status_code}, usando solo local")
                
        except Exception as e:
            print(f"Error conectando con Supabase: {str(e)}, conocimiento guardado localmente")
        
        # Invalidar caché
        self._knowledge_cache.clear()
    
    def get_knowledge(self, concept: str = None, category: str = None) -> List[Dict]:
        """Recupera conocimiento semántico"""
        try:
            params = {"session_id": f"eq.{self.session_id}"}
            if concept:
                params["concept"] = f"ilike.%{concept}%"
            if category:
                params["category"] = f"eq.{category}"
            
            response = make_supabase_request(
                method="GET",
                endpoint=self.table_name,
                params=params
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error obteniendo conocimiento semántico: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"Error en get_knowledge: {str(e)}")
            return []
    
    def update_knowledge(self, concept: str, new_knowledge: str, confidence: float = None) -> None:
        """Actualiza conocimiento existente"""
        existing = self.get_knowledge(concept=concept)
        if existing:
            # Actualizar conocimiento existente
            knowledge_id = existing[0]['id']
            try:
                update_data = {
                    "knowledge": new_knowledge,
                    "updated_at": datetime.now().isoformat()
                }
                if confidence is not None:
                    update_data["confidence"] = confidence
                
                # Construir endpoint con filtro
                endpoint = f"{self.table_name}?id=eq.{knowledge_id}"
                response = make_supabase_request(
                    method="PATCH",
                    endpoint=endpoint,
                    data=update_data
                )
                
                if response.status_code == 204:
                    print(f"🧠 Conocimiento actualizado: {concept}")
                    
            except Exception as e:
                print(f"Error actualizando conocimiento: {str(e)}")
        else:
            # Crear nuevo conocimiento
            self.store_knowledge(concept, new_knowledge, confidence=confidence or 1.0)
    
    def extract_and_store_from_conversation(self, messages: List[BaseMessage]) -> None:
        """Extrae conocimiento semántico de una conversación"""
        # Análisis simple de patrones para extraer conocimiento
        user_info = {}
        topics_discussed = set()
        
        for message in messages:
            if isinstance(message, HumanMessage):
                content = message.content.lower()
                
                # Extraer información personal
                if "mi nombre es" in content or "soy" in content:
                    # Extraer nombre
                    words = content.split()
                    if "mi nombre es" in content:
                        idx = words.index("nombre") + 2
                        if idx < len(words):
                            name = words[idx].replace(",", "").replace(".", "")
                            user_info["name"] = name
                    
                    # Extraer profesión/trabajo
                    if "trabajo en" in content or "soy" in content:
                        if "trabajo en" in content:
                            idx = content.find("trabajo en") + len("trabajo en")
                            profession = content[idx:].split()[0:3]
                            user_info["profession"] = " ".join(profession)
                
                # Identificar temas discutidos
                keywords = ["reglamento", "laboral", "empresa", "trabajo", "empleado", "normas"]
                for keyword in keywords:
                    if keyword in content:
                        topics_discussed.add(keyword)
        
        # Guardar información extraída
        if user_info:
            for key, value in user_info.items():
                self.store_knowledge(
                    concept=f"user_{key}",
                    knowledge=value,
                    category="user_profile",
                    confidence=0.8
                )
        
        if topics_discussed:
            self.store_knowledge(
                concept="discussed_topics",
                knowledge=", ".join(topics_discussed),
                category="conversation_topics",
                confidence=0.9
            )

# ============================================================================
# ⚙️ MEMORIA PROCEDIMENTAL - Procedimientos y workflows
# ============================================================================

class ProceduralMemory:
    """Memoria procedimental: almacena procedimientos, workflows y patrones de resolución"""
    
    def __init__(self, session_id: str, table_name: str = "procedural_memory", local_persistence: LocalMemoryPersistence = None):
        self.session_id = session_id
        self.table_name = table_name
        self.local_persistence = local_persistence or LocalMemoryPersistence()
        self._procedure_cache = {}
        self._cache_ttl = 600  # 10 minutos
    
    def store_procedure(self, procedure_name: str, steps: List[str], context: str = "", success_rate: float = 1.0) -> None:
        """Almacena un procedimiento o workflow"""
        try:
            data = {
                "session_id": self.session_id,
                "procedure_name": procedure_name,
                "steps": json.dumps(steps),
                "context": context,
                "success_rate": success_rate,
                "usage_count": 1,
                "created_at": datetime.now().isoformat(),
                "last_used": datetime.now().isoformat()
            }
            
            response = make_supabase_request(
                method="POST",
                endpoint=self.table_name,
                data=data
            )
            
            if response.status_code == 201:
                print(f"⚙️ Procedimiento guardado: {procedure_name}")
            else:
                print(f"Error guardando procedimiento: {response.status_code}")
                
        except Exception as e:
            print(f"Error en store_procedure: {str(e)}")
    
    def get_procedure(self, procedure_name: str = None, context: str = None) -> List[Dict]:
        """Recupera procedimientos"""
        try:
            params = {"session_id": f"eq.{self.session_id}"}
            if procedure_name:
                params["procedure_name"] = f"ilike.%{procedure_name}%"
            if context:
                params["context"] = f"ilike.%{context}%"
            
            response = make_supabase_request(
                method="GET",
                endpoint=self.table_name,
                params=params
            )
            
            if response.status_code == 200:
                procedures = response.json()
                # Parsear los steps de JSON
                for proc in procedures:
                    if proc.get('steps'):
                        proc['steps'] = json.loads(proc['steps'])
                return procedures
            else:
                print(f"Error obteniendo procedimientos: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"Error en get_procedure: {str(e)}")
            return []
    
    def update_procedure_success(self, procedure_name: str, success: bool) -> None:
        """Actualiza la tasa de éxito de un procedimiento"""
        procedures = self.get_procedure(procedure_name=procedure_name)
        if procedures:
            proc = procedures[0]
            current_success_rate = proc.get('success_rate', 1.0)
            usage_count = proc.get('usage_count', 1)
            
            # Calcular nueva tasa de éxito
            new_usage_count = usage_count + 1
            if success:
                new_success_rate = ((current_success_rate * usage_count) + 1) / new_usage_count
            else:
                new_success_rate = (current_success_rate * usage_count) / new_usage_count
            
            try:
                update_data = {
                    "success_rate": new_success_rate,
                    "usage_count": new_usage_count,
                    "last_used": datetime.now().isoformat()
                }
                
                endpoint = f"{self.table_name}?id=eq.{proc['id']}"
                response = make_supabase_request(
                    method="PATCH",
                    endpoint=endpoint,
                    data=update_data
                )
                
                if response.status_code == 204:
                    print(f"⚙️ Procedimiento actualizado: {procedure_name} (éxito: {success})")
                    
            except Exception as e:
                print(f"Error actualizando procedimiento: {str(e)}")
    
    def learn_from_interaction(self, query: str, tools_used: List[str], success: bool) -> None:
        """Aprende patrones procedimentales de las interacciones"""
        # Crear un resumen más útil de la consulta
        query_summary = self._create_query_summary(query)
        procedure_name = f"consulta_{query_summary.replace(' ', '_')}"
        
        # Crear un contexto más descriptivo
        context = f"Consulta sobre: {query_summary}"
        
        # Crear pasos más descriptivos basados en las herramientas usadas
        steps = []
        if "buscar_documentos" in tools_used:
            steps.append("Búsqueda en documentos internos")
        if "buscar_web" in tools_used:
            steps.append("Búsqueda complementaria en web")
        if "respuesta_directa" in tools_used:
            steps.append("Respuesta directa sin herramientas")
        if "error_handling" in tools_used:
            steps.append("Manejo de error en el procesamiento")
        
        # Agregar resultado
        if success:
            steps.append("Consulta resuelta exitosamente")
        else:
            steps.append("Consulta no resuelta")
        
        # Verificar si ya existe un procedimiento similar
        existing = self.get_procedure(context=query_summary[:30])
        if existing:
            # Actualizar procedimiento existente
            self.update_procedure_success(existing[0]['procedure_name'], success)
        else:
            # Crear nuevo procedimiento
            self.store_procedure(
                procedure_name=procedure_name,
                steps=steps,
                context=context,
                success_rate=1.0 if success else 0.0
            )
    
    def _create_query_summary(self, query: str) -> str:
        """Crea un resumen útil de la consulta del usuario"""
        # Palabras clave comunes en consultas laborales
        keywords_map = {
            "vacaciones": "vacaciones",
            "permiso": "permisos",
            "sueldo": "remuneracion",
            "salario": "remuneracion", 
            "horario": "horarios",
            "trabajo": "condiciones_laborales",
            "contrato": "contrato",
            "despido": "terminacion_laboral",
            "licencia": "licencias",
            "beneficio": "beneficios",
            "reglamento": "normativas",
            "ley": "normativas",
            "derecho": "derechos_laborales",
            "obligacion": "obligaciones",
            "falta": "faltas_disciplinarias",
            "sancion": "sanciones"
        }
        
        query_lower = query.lower()
        
        # Buscar palabras clave
        for keyword, category in keywords_map.items():
            if keyword in query_lower:
                return category
        
        # Si no encuentra palabras clave específicas, crear resumen genérico
        if len(query) > 50:
            return query[:47] + "..."
        else:
            return query
    
    def cleanup_old_patterns(self) -> int:
        """Limpia patrones antiguos poco útiles de la memoria procedimental"""
        try:
            # Eliminar registros con nombres de procedimiento que contengan "query_pattern_"
            params = {
                "session_id": f"eq.{self.session_id}",
                "procedure_name": "like.query_pattern_%"
            }
            
            response = make_supabase_request(
                method="DELETE",
                endpoint=self.table_name,
                params=params
            )
            
            if response.status_code in [200, 204]:
                print(f"🧹 Registros antiguos limpiados de memoria procedimental")
                return 1
            else:
                print(f"Error limpiando registros antiguos: {response.status_code}")
                return 0
                
        except Exception as e:
            print(f"Error en cleanup_old_patterns: {str(e)}")
            return 0

# ============================================================================
# 🎯 SISTEMA HÍBRIDO COMPLETO - Integra los 3 tipos de memoria
# ============================================================================

class AdvancedMemorySystem:
    """Sistema avanzado que integra memoria episódica, semántica y procedimental con persistencia mejorada"""
    
    def __init__(self, session_id: str, short_term_k: int = 10):
        self.session_id = session_id
        self.short_term_k = short_term_k
        
        # Capa de persistencia compartida
        self.local_persistence = LocalMemoryPersistence()
        
        # Memoria a corto plazo (RAM) - compatible con langchain 0.1.14
        self.short_term_memory = ConversationBufferWindowMemory(
            memory_key="chat_history",
            input_key="input",
            output_key="output", 
            return_messages=True,
            k=short_term_k
        )
        
        # Memorias a largo plazo especializadas con persistencia compartida
        self.episodic_memory = EpisodicMemory(session_id, local_persistence=self.local_persistence)
        self.semantic_memory = SemanticMemory(session_id, local_persistence=self.local_persistence)
        self.procedural_memory = ProceduralMemory(session_id, local_persistence=self.local_persistence)
        
        # Sistema de backup automático
        self._setup_auto_backup()
        
        # Restaurar desde backup si es necesario
        self._restore_if_needed()
        
        # Cargar mensajes existentes
        self._load_recent_messages()
        
        print(f"🧠 Sistema de memoria avanzado inicializado:")
        print(f"  📚 Memoria Episódica: Conversaciones y eventos")
        print(f"  🧠 Memoria Semántica: Conocimiento y conceptos")
        print(f"  ⚙️ Memoria Procedimental: Workflows y procedimientos")
        print(f"  💾 Persistencia Local: Backup automático habilitado")
    
    def _setup_auto_backup(self):
        """Configurar backup automático cada 30 minutos"""
        def create_backup():
            try:
                result = self.local_persistence.create_compressed_backup(self.session_id)
                print(f"🔄 Backup automático creado: {result}")
                # Programar siguiente backup
                Timer(1800, create_backup).start()  # 30 minutos
            except Exception as e:
                print(f"Error en backup automático: {e}")
                # Reintentar en 5 minutos
                Timer(300, create_backup).start()
        
        # Iniciar primer backup en 30 segundos
        Timer(30, create_backup).start()
    
    def _restore_if_needed(self):
        """Restaurar desde backup si no hay datos recientes"""
        try:
            messages = self.local_persistence.get_episodic_messages(self.session_id, limit=1)
            if not messages:
                # No hay mensajes, intentar restaurar desde backup
                if self.local_persistence.restore_from_backup(self.session_id):
                    print(f"🔄 Sesión {self.session_id} restaurada desde backup")
        except Exception as e:
            print(f"Error verificando necesidad de restauración: {e}")
    
    def _load_recent_messages(self):
        """Carga los mensajes más recientes en la memoria a corto plazo"""
        try:
            all_messages = self.episodic_memory.messages
            recent_messages = all_messages[-self.short_term_k:] if len(all_messages) > self.short_term_k else all_messages
            
            for message in recent_messages:
                if isinstance(message, HumanMessage):
                    self.short_term_memory.chat_memory.add_user_message(message.content)
                elif isinstance(message, AIMessage):
                    self.short_term_memory.chat_memory.add_ai_message(message.content)
                    
        except Exception as e:
            print(f"Error cargando mensajes recientes: {str(e)}")
    
    def add_message(self, message: BaseMessage, context: Dict = None, tools_used: List[str] = None, success: bool = True) -> None:
        """Añade un mensaje y actualiza todas las memorias"""
        # 1. Memoria a corto plazo
        if isinstance(message, HumanMessage):
            self.short_term_memory.chat_memory.add_user_message(message.content)
        elif isinstance(message, AIMessage):
            self.short_term_memory.chat_memory.add_ai_message(message.content)
        
        # 2. Memoria episódica
        self.episodic_memory.add_message(message, context)
        
        # 3. Actualizar memoria semántica si es mensaje del usuario
        if isinstance(message, HumanMessage):
            recent_messages = self.get_recent_messages()
            self.semantic_memory.extract_and_store_from_conversation(recent_messages[-5:])  # Últimos 5 mensajes
        
        # 4. Actualizar memoria procedimental si se usaron herramientas
        if isinstance(message, HumanMessage) and tools_used:
            self.procedural_memory.learn_from_interaction(message.content, tools_used, success)
    
    def get_recent_messages(self) -> List[BaseMessage]:
        """Obtiene mensajes recientes de la memoria a corto plazo"""
        return self.short_term_memory.chat_memory.messages
    
    def get_all_messages(self) -> List[BaseMessage]:
        """Obtiene todos los mensajes de la memoria episódica"""
        return self.episodic_memory.messages
    
    def search_memory(self, query: str, limit: int = 5) -> List[BaseMessage]:
        """Busca en la memoria episódica"""
        all_messages = self.get_all_messages()
        relevant_messages = []
        
        query_lower = query.lower()
        for message in all_messages:
            if query_lower in message.content.lower():
                relevant_messages.append(message)
                if len(relevant_messages) >= limit:
                    break
        
        return relevant_messages
    
    def get_user_profile(self) -> Dict[str, Any]:
        """Obtiene el perfil del usuario desde la memoria semántica"""
        user_knowledge = self.semantic_memory.get_knowledge(category="user_profile")
        profile = {}
        for item in user_knowledge:
            concept = item['concept'].replace('user_', '')
            profile[concept] = item['knowledge']
        return profile
    
    def get_learned_procedures(self) -> List[Dict]:
        """Obtiene procedimientos aprendidos"""
        return self.procedural_memory.get_procedure()
    
    def get_memory_summary(self) -> Dict[str, Any]:
        """Obtiene un resumen completo del estado de la memoria"""
        episodic_summary = self.episodic_memory.get_conversation_summary()
        semantic_knowledge = self.semantic_memory.get_knowledge()
        procedures = self.procedural_memory.get_procedure()
        
        return {
            "session_id": self.session_id,
            "episodic": episodic_summary,
            "semantic": {
                "total_concepts": len(semantic_knowledge),
                "categories": list(set([item.get('category', 'general') for item in semantic_knowledge]))
            },
            "procedural": {
                "total_procedures": len(procedures),
                "avg_success_rate": sum([p.get('success_rate', 0) for p in procedures]) / len(procedures) if procedures else 0
            },
            "short_term_messages": len(self.get_recent_messages())
        }
    
    def clear(self) -> None:
        """Limpia todas las memorias"""
        self.short_term_memory.clear()
        self.episodic_memory.clear()
        print("🧠 Todas las memorias limpiadas")
    
    def cleanup_old_procedural_patterns(self) -> int:
        """Limpia patrones procedimentales antiguos poco útiles"""
        return self.procedural_memory.cleanup_old_patterns()

# ============================================================================
# 🎮 GESTOR PRINCIPAL Y FUNCIONES DE UTILIDAD
# ============================================================================

class AdvancedMemoryManager:
    """Gestor avanzado de memoria que maneja múltiples sesiones con persistencia mejorada"""
    
    def __init__(self):
        self.active_sessions: Dict[str, AdvancedMemorySystem] = {}
        self.last_activity: Dict[str, float] = {}
        self.cleanup_interval = 7200  # 2 horas (aumentado)
        self.local_persistence = LocalMemoryPersistence()
        
        # Configurar limpieza automática
        self._setup_periodic_cleanup()
    
    def _setup_periodic_cleanup(self):
        """Configurar limpieza periódica de sesiones"""
        def periodic_cleanup():
            try:
                # Limpiar sesiones inactivas de RAM
                self.cleanup_inactive_sessions()
                
                # Limpiar datos antiguos de base local
                cleaned = self.local_persistence.cleanup_old_sessions(30)
                if cleaned > 0:
                    print(f"🧹 Limpieza automática: {cleaned} sesiones archivadas")
                
                # Programar siguiente limpieza
                Timer(3600, periodic_cleanup).start()  # 1 hora
            except Exception as e:
                print(f"Error en limpieza periódica: {e}")
                Timer(1800, periodic_cleanup).start()  # Reintentar en 30 min
        
        # Iniciar primera limpieza en 1 hora
        Timer(3600, periodic_cleanup).start()
    
    def get_memory_for_session(self, session_id: str, short_term_k: int = 10) -> AdvancedMemorySystem:
        """Obtiene o crea un sistema de memoria avanzado para una sesión"""
        if session_id not in self.active_sessions:
            self.active_sessions[session_id] = AdvancedMemorySystem(
                session_id=session_id,
                short_term_k=short_term_k
            )
        
        self.last_activity[session_id] = time.time()
        return self.active_sessions[session_id]
    
    def cleanup_inactive_sessions(self):
        """Limpia sesiones inactivas de RAM (los datos persisten localmente)"""
        current_time = time.time()
        inactive_sessions = []
        
        for session_id, last_active in self.last_activity.items():
            if current_time - last_active > self.cleanup_interval:
                inactive_sessions.append(session_id)
        
        for session_id in inactive_sessions:
            if session_id in self.active_sessions:
                # Crear backup antes de limpiar de RAM
                try:
                    self.active_sessions[session_id].local_persistence.create_compressed_backup(session_id)
                    print(f"🧹 Sesión {session_id} guardada y removida de RAM")
                except Exception as e:
                    print(f"Error creando backup para {session_id}: {e}")
                
                del self.active_sessions[session_id]
                del self.last_activity[session_id]
        
        return len(inactive_sessions)

# Instancia global del gestor avanzado
advanced_memory_manager = AdvancedMemoryManager()

def get_memory(llm, session_id: str = None, short_term_k: int = 10):
    """
    Función principal para obtener memoria avanzada (episódica, semántica, procedimental)
    """
    if not session_id:
        session_id = f"session_{int(time.time())}"
    
    # Limpiar sesiones inactivas periódicamente
    advanced_memory_manager.cleanup_inactive_sessions()
    
    # Obtener sistema de memoria avanzado
    memory_system = advanced_memory_manager.get_memory_for_session(session_id, short_term_k)
    
    print(f"🎯 Sistema de memoria avanzado listo para: {session_id}")
    
    return memory_system
