from typing import Dict, Any
import traceback
import asyncio
import nest_asyncio
from langchain_openai import ChatOpenAI
from langchain.tools import Tool
from langchain_openai import ChatOpenAI
from langchain.prompts import MessagesPlaceholder, ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
from indexador import  IndexerAgent
from busqueda_Web import WebSearchAgent
from memoria import get_memory
from langchain.agents import AgentType, initialize_agent
import time
from datetime import datetime
from langchain.schema import HumanMessage, AIMessage

# Aplicar nest_asyncio para permitir loops anidados
nest_asyncio.apply()

# Diccionario global para mantener las instancias de orquestadores por usuario
user_orchestrators = {}
# Diccionario para seguir la última actividad de cada usuario
last_activity = {}

# Tiempo de inactividad en segundos antes de limpiar la memoria (1 hora)
INACTIVITY_TIMEOUT = 3600  # 1 hora en segundos


def get_inactive_users(current_time: float = None) -> list:
    """
    Identifica usuarios inactivos basado en el tiempo de inactividad
    
    Args:
        current_time: Timestamp actual (opcional, usa time.time() si no se proporciona)
    
    Returns:
        Lista de user_ids que están inactivos
    """
    if current_time is None:
        current_time = time.time()
    
    inactive_users = []
    for user_id, last_active in last_activity.items():
        if current_time - last_active > INACTIVITY_TIMEOUT:
            inactive_users.append(user_id)
    
    return inactive_users


def get_orchestrator_for_user(user_id):
    """Obtiene o crea un orquestador para un usuario específico"""
    # Verificar si debemos limpiar alguna memoria por inactividad
    check_and_cleanup_inactive_users()
    
    if user_id not in user_orchestrators:
        user_orchestrators[user_id] = MainOrchestrator()
    
    # Actualizar timestamp de último acceso
    last_activity[user_id] = time.time()
    
    return user_orchestrators[user_id]


def check_and_cleanup_inactive_users():
    """Verifica y limpia la memoria de usuarios inactivos"""
    inactive_users = get_inactive_users()
    
    # Limpiar memoria de usuarios inactivos
    for user_id in inactive_users:
        if user_id in user_orchestrators:
            print(f"Limpiando memoria de usuario inactivo: {user_id}")
            user_orchestrators[user_id].clear_memory()
    
    # Registrar actividad de limpieza
    if inactive_users:
        print(f"Se limpió la memoria de {len(inactive_users)} usuarios inactivos")


class MainOrchestrator:
    """Orquestador principal basado en LangChain con herramientas extensibles"""
    
    def __init__(self):
        """Inicializa el orquestador con las herramientas necesarias"""
        print(" Inicializando MainOrchestrator con LangChain (Agente)")
        
        # Inicializar LLM (lo necesitamos antes para la memoria)
        self.llm = ChatOpenAI(temperature=0.3, model="gpt-4o-mini")

        # Generar un session_id único para esta instancia
        self.session_id = f"session_{int(time.time())}"
        
        # Inicializar sistema de memoria híbrido completo
        self.memory_system = get_memory(self.llm, self.session_id, short_term_k=10)
        
        # Para compatibilidad con LangChain, usar solo la memoria a corto plazo en el agente
        self.memory = self.memory_system.short_term_memory
        
        # Timestamp de última actividad
        self.last_active = time.time()
        
        # Inicializar las herramientas (tools)
        self.document_indexer = IndexerAgent()
        self.web_search_agent = WebSearchAgent()
        
        # Crear funciones adaptadoras (para manejar async/sync)
        def search_documents_wrapper(query: str) -> str:
            """Adapter para el método asíncrono search_documents"""
            results = self._execute_async_tool(
                "buscar_documentos", 
                self.document_indexer.search_documents, 
                query
            )
            return self._format_document_results(results)
        
        def search_web_wrapper(query: str) -> str:
            """Adapter para el método asíncrono get_web_data"""
            web_data = self._execute_async_tool(
                "buscar_web", 
                self.web_search_agent.get_web_data, 
                query
            )
            return self._format_web_results(web_data)
        
        # Definir las herramientas LangChain
        self.tools = [
            Tool(
                name="buscar_documentos",
                description="Busca información en documentos internos de la empresa sobre temas laborales, legales, normativos y políticas internas. Útil para consultas sobre reglamentos, procedimientos y normativas específicas de la empresa.",
                func=search_documents_wrapper
            ),
            Tool(
                name="buscar_web",
                description="Busca información actualizada en internet sobre temas laborales, legales y normativos. Útil para obtener información general, actualizaciones legales o cuando se necesita información más amplia.",
                func=search_web_wrapper
            )
        ]
        
        # 1. Definir el sistema de mensajes
        system_message = SystemMessage(content="""Eres TONY, un asistente laboral especializado en temas laborales y en necesidades de la empresa. 
        
        HERRAMIENTAS DISPONIBLES:
        - buscar_documentos: Para información en documentos internos de la empresa
        - buscar_web: Para información actualizada de internet
        
        ESTRATEGIA INTELIGENTE:
        - Evalúa cada consulta y decide qué herramientas usar
        - Puedes usar una sola herramienta si es suficiente
        - Puedes usar ambas herramientas si necesitas información más completa
        - Si una herramienta no da resultados útiles, considera usar la otra
        - Usa tu criterio para proporcionar la mejor respuesta posible
        
        FORMATO DE RESPUESTA OBLIGATORIO:
        - SIEMPRE usa 1-2 emojis relacionados con el tema en cada respuesta 😊 👍
        - SIEMPRE organiza tu respuesta en párrafos cortos y separados
        - NUNCA respondas con un solo párrafo largo
        - Usa viñetas o numeración cuando sea apropiado
        - NO RESPONDAS CONSULTAS QUE NO SEAN RELACIONADAS CON EL AREA LABORAL
        
        REGLAS IMPORTANTES:
        1. SIEMPRE responde en el MISMO IDIOMA que usa el usuario en su consulta
        2. Responde de manera estructurada y organizada
        3. Cuando recibas consultas demasiado breves o ambiguas, pide amablemente al usuario que aclare su pregunta
        4. Usa las herramientas de manera inteligente según la consulta
        5. Responde de manera amigable y profesional
        6. Si no encuentras información suficiente, admítelo honestamente
        7. Cuando encuentres documentos, INTERPRETA el contenido considerando el contexto y la consulta del usuario
        8. Proporciona respuestas útiles y completas""")
        
        # Crear el LLM bound con funciones
        # Convertir herramientas a funciones OpenAI compatible con versión actual
        openai_functions = []
        for tool in self.tools:
            openai_functions.append({
                "name": tool.name,
                "description": tool.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "La consulta a buscar"
                        }
                    },
                    "required": ["query"]
                }
            })
        
        
        # 4. Crear prompt personalizado con el orden que quieres
        custom_prompt = ChatPromptTemplate.from_messages([
            ("system", system_message.content),  # 1. PRIMERO: Personalidad
            ("human", "{input}"),                # 2. SEGUNDO: Consulta actual
            ("ai", "{agent_scratchpad}"),        # 3. TERCERO: Información/razonamiento
            MessagesPlaceholder(variable_name="chat_history")  # 4. ÚLTIMO: Contexto/historial
        ])
        
        # Crear el agente con prompt personalizado
        self.agent = initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
            verbose=True,
            memory=self.memory,
            handle_parsing_errors=True,
            max_iterations=10,  
            early_stopping_method="generate", 
            agent_kwargs={
                "prompt": custom_prompt,  # Usar nuestro prompt personalizado
                "input_variables": ["input", "agent_scratchpad", "chat_history"]
            }
        )
        
        # Variable para seguimiento de conversación activa
        self.conversation_active = False
        
        print("\u2705 MainOrchestrator inicializado correctamente con memoria conversacional")
    
    def _execute_async_tool(self, tool_name: str, async_func, *args, **kwargs):
        """Ejecutor genérico para herramientas asíncronas"""
        # 🔧 RASTREAR USO DE HERRAMIENTA
        if not hasattr(self, '_tools_used_in_current_query'):
            self._tools_used_in_current_query = []
        self._tools_used_in_current_query.append(tool_name)
        
        # Mapeo de emojis por herramienta
        emoji_map = {
            "buscar_documentos": "🔍",
            "buscar_web": "🌐"
        }
        emoji = emoji_map.get(tool_name, "🔧")
        print(f"{emoji} Herramienta ejecutada: {tool_name}")
        
        # Ejecutar función asíncrona
        try:
            return asyncio.run(async_func(*args, **kwargs))
        except RuntimeError:
            # Si ya estamos en un event loop, usamos nest_asyncio
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(async_func(*args, **kwargs))
    
    def _format_document_results(self, results):
        """Formatea resultados de documentos"""
        if not results:
            return "No se encontró información específica sobre esta consulta en los documentos internos de la empresa."
        
        formatted_results = []
        for i, doc in enumerate(results[:8], 1):
            metadata = doc.get('metadata', {})
            content = doc.get('content', '').strip()
            formatted_results.append(f"--- Documento {i}: {metadata.get('file_name', 'Sin nombre')} ---\n{content}")
        
        return "\n\n".join(formatted_results)
    
    def _format_web_results(self, web_data):
        """Formatea resultados de búsqueda web"""
        if isinstance(web_data, dict) and web_data.get("error"):
            return f"Error al buscar en la web: {web_data['error']}"
        
        results = []
        
        # Añadir resultados principales
        if web_data.get("web_results"):
            results.append("--- RESULTADOS WEB ---")
            for i, result in enumerate(web_data["web_results"][:3], 1):
                results.append(f"{i}. {result['title']}")
                results.append(f"   {result['snippet']}")
                results.append(f"   URL: {result['url']}")
                results.append("")
        
        # Añadir contenido de PDFs
        if web_data.get("pdf_contents"):
            results.append("--- CONTENIDO DE DOCUMENTOS PDF ---")
            for i, (url, content) in enumerate(list(web_data["pdf_contents"].items())[:2], 1):
                results.append(f"PDF {i}: {url}")
                summary = content[:1000] + "..." if len(content) > 1000 else content
                results.append(summary)
                results.append("")
        
        # Añadir contenido web
        if web_data.get("web_contents"):
            results.append("--- CONTENIDO DE PÁGINAS WEB ---")
            for i, (url, content) in enumerate(list(web_data["web_contents"].items())[:2], 1):
                results.append(f"Página {i}: {url}")
                summary = content[:1000] + "..." if len(content) > 1000 else content
                results.append(summary)
                results.append("")
        
        return "\n".join(results) if results else "No se encontró información relevante en la web."

    def _enrich_query_with_longterm_memory(self, query: str, context: Dict[str, Any] = None) -> str:
        """
        Enriquece la consulta con información de la memoria a largo plazo
        para que el agente tenga más contexto
        """
        try:
            enriched_info = []
            
            # 1. Consultar memoria semántica (perfil del usuario)
            user_profile = self.memory_system.get_user_profile()
            if user_profile:
                profile_info = []
                for key, value in user_profile.items():
                    profile_info.append(f"{key}: {value}")
                if profile_info:
                    enriched_info.append(f"[PERFIL USUARIO: {', '.join(profile_info)}]")
            
            # 2.  Consultar memoria procedimental (mejores herramientas para este tipo de consulta)
            procedures = self.memory_system.procedural_memory.get_procedure()
            if procedures:
                # Buscar procedimientos relevantes basados en palabras clave
                relevant_procedures = []
                query_lower = query.lower()
                for proc in procedures:
                    if any(keyword in query_lower for keyword in ['vacacion', 'permiso', 'sueldo', 'horario', 'contrato']):
                        if proc.get('success_rate', 0) > 0.7:  # Solo procedimientos exitosos
                            relevant_procedures.append(proc)
                
                if relevant_procedures:
                    best_proc = max(relevant_procedures, key=lambda x: x.get('success_rate', 0))
                    if best_proc.get('steps'):
                        steps = ', '.join(best_proc['steps'][:2])  # Primeros 2 pasos
                        enriched_info.append(f"[EXPERIENCIA PREVIA: {steps}]")
            
            # 3. 📚 Buscar conversaciones relevantes (memoria episódica)
            relevant_messages = self.memory_system.search_memory(query, limit=3)
            if relevant_messages:
                recent_context = []
                for msg in relevant_messages[-2:]:  # Últimos 2 mensajes relevantes
                    if isinstance(msg, HumanMessage):
                        snippet = msg.content[:50] + "..." if len(msg.content) > 50 else msg.content
                        recent_context.append(f"Usuario preguntó: {snippet}")
                
                if recent_context:
                    enriched_info.append(f"[CONTEXTO PREVIO: {'; '.join(recent_context)}]")
            
            # 4. Construir consulta enriquecida
            if enriched_info:
                enriched_query = f"{query}\n\n{' '.join(enriched_info)}"
                print(f"🧠 Consulta enriquecida con memoria a largo plazo:")
                for info in enriched_info:
                    print(f"   {info}")
                return enriched_query
            else:
                print("📝 Sin información relevante en memoria a largo plazo")
                return query
                
        except Exception as e:
            print(f"❌ Error consultando memoria a largo plazo: {str(e)}")
            return query

    async def process_query(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Procesa una consulta permitiendo al agente usar su razonamiento completo
        """
        try:
            # Actualizar timestamp de última actividad
            self.last_active = time.time()
            
            print(f"Procesando consulta: '{query}'")
            
            # 🧠 ENRIQUECER CONSULTA CON MEMORIA A LARGO PLAZO
            enriched_query = self._enrich_query_with_longterm_memory(query, context)
            
            # La consulta enriquecida va directamente al prompt (sin duplicar instrucciones)
            formatted_query = enriched_query
            
            # Verificar si la conversacion esta activa
            if hasattr(self.memory, "chat_memory") and self.memory.chat_memory.messages:
                print("Continuando conversacion - Historial de mensajes:", 
                      f"{len(self.memory.chat_memory.messages)//2} intercambios")
            else:
                print("Iniciando nueva conversacion")
            
            # 🧠 GUARDAR MENSAJE DEL USUARIO EN MEMORIA AVANZADA
            user_message = HumanMessage(content=query)
            
            # Inicializar rastreo de herramientas para esta consulta
            self._tools_used_in_current_query = []
            tools_used = []
            success = True
            
            try:
                # Ejecutar el agente
                response = self.agent.run(input=formatted_query)
                
                # Usar las herramientas realmente ejecutadas
                tools_used = getattr(self, '_tools_used_in_current_query', [])
                
                # Si no se ejecutó ninguna herramienta, es una respuesta directa
                if not tools_used:
                    tools_used = ["respuesta_directa"]
                
                print(f"🔧 Herramientas utilizadas: {tools_used}")
                
            except Exception as e:
                response = f"Lo siento, ocurrió un error al procesar tu consulta: {str(e)}"
                success = False
                tools_used = ["error_handling"]
            finally:
                # Limpiar el rastreo para la próxima consulta
                if hasattr(self, '_tools_used_in_current_query'):
                    delattr(self, '_tools_used_in_current_query')
            
            # 🧠 GUARDAR EN SISTEMA DE MEMORIA AVANZADO
            # Incluir contexto enriquecido
            enriched_context = {
                "user_context": context or {},
                "tools_used": tools_used,
                "success": success,
                "response_length": len(response),
                "timestamp": datetime.now().isoformat()
            }
            
            # Guardar mensaje del usuario con contexto y herramientas
            self.memory_system.add_message(
                user_message, 
                context=enriched_context, 
                tools_used=tools_used, 
                success=success
            )
            print(f"💾 Mensaje del usuario guardado en memoria avanzada")
            
            # Guardar respuesta del agente
            ai_message = AIMessage(content=response)
            self.memory_system.add_message(
                ai_message, 
                context=enriched_context, 
                tools_used=tools_used, 
                success=success
            )
            print(f"💾 Respuesta del agente guardada en memoria avanzada")
            
            # 📊 MOSTRAR RESUMEN DE MEMORIA (opcional, para debug)
            if hasattr(self.memory_system, 'get_memory_summary'):
                summary = self.memory_system.get_memory_summary()
                print(f"📊 Resumen de memoria:")
                print(f"  📚 Episódica: {summary.get('episodic', {}).get('total_messages', 0)} mensajes")
                print(f"  🧠 Semántica: {summary.get('semantic', {}).get('total_concepts', 0)} conceptos")
                print(f"  ⚙️ Procedimental: {summary.get('procedural', {}).get('total_procedures', 0)} procedimientos")
            
            # Marcar que hay una conversacion activa
            self.conversation_active = True
            
            return {
                "query": query,
                "response": response,
                "source": "langchain_agent",
                "tools_used": tools_used,
                "success": success
            }
                
        except Exception as e:
            error_msg = f"Lo siento, ocurrio un error al procesar tu consulta: {str(e)}"
            print(f"Error en MainOrchestrator: {error_msg}")
            traceback.print_exc()
            
            return {
                "query": query,
                "response": error_msg,
                "error": str(e),
                "success": False
            }

    def clear_memory(self):
        """Limpia la memoria de conversación"""
        if hasattr(self.memory, "clear"):
            self.memory.clear()
        elif hasattr(self.memory, "chat_memory") and hasattr(self.memory.chat_memory, "clear"):
            self.memory.chat_memory.clear()
        
        # 🧠 LIMPIAR TAMBIÉN LA MEMORIA A LARGO PLAZO
        if hasattr(self, 'memory_system'):
            self.memory_system.clear()
            print("💾 Memoria a largo plazo también limpiada")
            
        self.conversation_active = False
        print("Memoria de conversacion reiniciada") 