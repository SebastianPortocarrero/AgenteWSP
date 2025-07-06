import tempfile
import os
from googleapiclient.http import MediaIoBaseDownload
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
import requests
from utilidades import *
from typing import Dict, List
import traceback
import numpy as np
from datetime import datetime
import asyncio
import aiohttp
import concurrent.futures
from markitdown import MarkItDown
from pathlib import Path

# Importes completados - indexador tradicional optimizado

class DocumentIndexer:
    """Clase para indexar documentos de Google Drive en Supabase"""
    
    def __init__(self, max_hilos=10, lote=5):
        """Inicializa el indexador con los servicios necesarios"""
        self.drive_service = get_google_drive_service()
        self.embeddings_model = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
        self.markitdown = MarkItDown()
        
        # Configuración de chunks
        self.chunk_size = 900
        self.chunk_overlap = 300
        
        # Configuración de optimización
        self.max_hilos = max_hilos  # Número máximo de hilos
        self.batch_size = lote    # Número de chunks por lote

    def download_file_from_drive(self, file_id: str, mime_type: str) -> str:
        """
        Descarga un archivo de Google Drive y lo guarda en un archivo temporal.
        
        Args:
            file_id: ID del archivo en Google Drive
            mime_type: Tipo MIME del archivo
            
        Returns:
            str: Ruta al archivo temporal descargado
        """
        try:
            # Para archivos de Google Docs/Sheets, necesitamos exportarlos
            if 'google-apps' in mime_type:
                if 'document' in mime_type:
                    request = self.drive_service.files().export_media(
                        fileId=file_id,
                        mimeType='application/pdf'
                    )
                elif 'spreadsheet' in mime_type:
                    request = self.drive_service.files().export_media(
                        fileId=file_id,
                        mimeType='application/pdf'
                    )
                else:
                    raise ValueError(f"Formato de Google Apps no soportado: {mime_type}")
            else:
                # Para otros tipos de archivos, usar get_media
                request = self.drive_service.files().get_media(fileId=file_id)

            # Crear archivo temporal con la extensión correcta
            extension = self._get_file_extension(mime_type)
            fh = tempfile.NamedTemporaryFile(delete=False, suffix=extension)
            downloader = MediaIoBaseDownload(fh, request)
            
            # Descargar el archivo
            done = False
            while not done:
                _, done = downloader.next_chunk()
            
            fh.close()
            return fh.name
            
        except Exception as e:
            print(f"❌ Error descargando archivo: {str(e)}")
            raise

    def _get_file_extension(self, mime_type: str) -> str:
        """Obtiene la extensión de archivo apropiada basada en el tipo MIME"""
        mime_to_ext = {
            'application/pdf': '.pdf',
            'application/vnd.google-apps.document': '.pdf',
            'application/vnd.google-apps.spreadsheet': '.pdf',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
            'text/plain': '.txt',
            'text/csv': '.csv'
        }
        return mime_to_ext.get(mime_type, '.tmp')

    def extract_text(self, file_id: str, mime_type: str) -> str:
        """
        Extrae texto de un archivo usando MarkItDown
        
        Args:
            file_id: ID del archivo en Google Drive
            mime_type: Tipo MIME del archivo
            
        Returns:
            str: Texto extraído del archivo
        """
        try:
            # 1. Descargar el archivo a un archivo temporal
            temp_file = self.download_file_from_drive(file_id, mime_type)
            print(f"📥 Archivo descargado temporalmente en: {temp_file}")
            
            try:
                # 2. Convertir a Markdown usando MarkItDown
                print(f"🔄 Convirtiendo archivo a Markdown...")
                # Crear URI del archivo
                file_uri = Path(temp_file).absolute().as_uri()
                # Convertir usando MarkItDown
                result = self.markitdown.convert_uri(file_uri)
                markdown_text = result.markdown
                
                if not markdown_text or markdown_text.strip() == "":
                    raise ValueError("No se pudo extraer texto del archivo")
                    
                print(f"✅ Texto extraído exitosamente ({len(markdown_text)} caracteres)")
                return markdown_text
                
            except Exception as e:
                print(f"❌ Error convirtiendo a Markdown: {str(e)}")
                # Si falla la conversión a Markdown, intentar leer el archivo directamente
                try:
                    with open(temp_file, 'r', encoding='utf-8') as f:
                        text = f.read()
                        if text and text.strip():
                            print("✅ Texto extraído directamente del archivo")
                            return text
                except:
                    raise e
                
            finally:
                # 3. Limpiar: eliminar el archivo temporal
                try:
                    os.remove(temp_file)
                    print(f"🧹 Archivo temporal eliminado: {temp_file}")
                except Exception as e:
                    print(f"⚠️ No se pudo eliminar el archivo temporal: {str(e)}")
                
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            print(f"❌ {error_msg}")
            return error_msg
    
    def split_text(self, text):
        """Divide el texto en chunks"""
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )
        return text_splitter.split_text(text)
    
    def _process_file(self, file):
        """Procesa un archivo y lo indexa en Supabase"""
        try:
            print(f"\n📄 Procesando: {file['name']}")
            
            # 1. Extraer texto
            text = self.extract_text(file['id'], file['mimeType'])
            if text.startswith("Error:"):
                print(f"❌ {text}")
                return
            
            # 2. Dividir en chunks
            chunks = self.split_text(text)
            total_chunks = len(chunks)
            print(f"📦 Total chunks: {total_chunks}")
            
            # 3. Procesar cada chunk
            for i, chunk in enumerate(chunks, 1):
                try:
                    # Generar embedding
                    embedding = self.embeddings_model.embed_query(chunk)
                    
                    # Metadata del chunk
                    chunk_metadata = {
                        'file_id': file['id'],
                        'file_name': file['name'],
                        'file_type': file['mimeType'],
                        'chunk_number': i,
                        'total_chunks': total_chunks,
                        'modifiedTime': file.get('modifiedTime', ''),
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    # Crear registro para Supabase
                    data = {
                        "content": chunk,
                        "embedding": embedding,
                        "metadata": chunk_metadata
                    }
                    
                    # Insertar en Supabase usando helper
                    response = make_supabase_request(
                        method="POST",
                        endpoint="tfinal",
                        data=data
                    )
                    
                    if response.status_code == 201:
                        print(f"  ✅ Chunk {i}/{total_chunks} indexado")
                    else:
                        print(f"  ❌ Error en chunk {i}/{total_chunks}: {response.text}")
                        
                except Exception as e:
                    print(f"  ❌ Error en chunk {i}/{total_chunks}: {str(e)}")
                
        except Exception as e:
            print(f"❌ Error procesando archivo {file['name']}: {str(e)}")
    
    async def index_documents(self):
        """Indexa documentos utilizando procesamiento optimizado con async y multihilo"""
        print("🚀 Iniciando indexación optimizada de documentos...")
        
        # Obtener ID de la carpeta desde variables de entorno
        folder_id = GOOGLE_DRIVE_FOLDER_ID
        if not folder_id:
            print("❌ Error: No se especificó GOOGLE_DRIVE_FOLDER_ID en las variables de entorno")
            return
        
        try:
            # 1. Listar archivos en la carpeta
            files = self.drive_service.files().list(
                q=f"'{folder_id}' in parents",
                fields="files(id, name, mimeType, modifiedTime)"
            ).execute().get('files', [])

            query = (
                f"'{folder_id}' in parents "
                "and mimeType!='application/vnd.google-apps.folder' "
                "and trashed=false"
            )

            files = self.drive_service.files().list(
                q=query,
                fields="files(id, name, mimeType, modifiedTime)"
                ).execute().get('files', [])
            
            print(f"📂 Encontrados {len(files)} archivos en Drive")
            
            # Procesar cada archivo
            for file in files:
                file_id = file['id']
                file_name = file['name']
                
                # 2.1 Verificar si el archivo existe en Supabase usando helper
                response = make_supabase_request(
                    method="GET",
                    endpoint="tfinal",
                    params={
                        "select": "metadata",
                        "metadata->>file_id": f"eq.{file_id}",
                        "limit": "1"
                    }
                )
                
                file_exists_in_supabase = False
                needs_update = True
                
                if response.status_code == 200 and response.json():
                    file_exists_in_supabase = True
                    # Verificar si el documento ha cambiado (comparando timestamps)
                    supabase_file = response.json()[0]
                    supabase_modified_time = supabase_file.get('metadata', {}).get('modifiedTime', '')
                    drive_modified_time = file.get('modifiedTime', '')
                    
                    if supabase_modified_time == drive_modified_time:
                        needs_update = False
                        print(f"⏭️ Sin cambios: {file_name}")
                    else:
                        print(f"🔄 Cambios detectados: {file_name}, actualizando...")
                else:
                    print(f"📄 Nuevo documento: {file_name}")
                
                # 2.2 Si no existe en Supabase o necesita actualización, procesarlo
                if not file_exists_in_supabase or needs_update:
                    await self._process_file_async(file)
                else:
                    # Verificar si hay contenido en Supabase usando helper
                    count_response = make_supabase_request(
                        method="GET",
                        endpoint="tfinal",
                        params={
                            "select": "count",
                            "metadata->>file_id": f"eq.{file_id}"
                        }
                    )
                    
                    if count_response.status_code == 200:
                        count_data = count_response.json()
                        if count_data and not count_data[0].get('count', 0) > 0:
                            print(f"⚠️ Archivo {file_name} está registrado pero sin contenido en Supabase. Reindexando...")
                            await self._process_file_async(file)
                        else:
                            print(f"✅ Archivo {file_name} ya indexado con {count_data[0].get('count', 0)} chunks")
            
            print("✅ Proceso de indexación completado")
            
        except Exception as e:
            print(f"❌ Error en indexación: {str(e)}")
            traceback.print_exc()
    
    async def process_file_async(self, file):
        """Procesa un archivo de forma asíncrona"""
        try:
            print(f"\n📄 Procesando: {file['name']}")
            
            # Verificar si el archivo ya está indexado (opcional)
            # Código de verificación aquí si es necesario
            
            # Extraer texto (esto es sincrónico porque usa la API de Drive)
            loop = asyncio.get_running_loop()
            text = await loop.run_in_executor(
                None, 
                lambda: self.extract_text(file['id'], file['mimeType'])
            )
            
            if not text or text.startswith("Error:"):
                print(f"❌ {text if text else 'No se pudo extraer texto'}")
                return
                
            # Dividir en chunks
            chunks = await loop.run_in_executor(
                None,
                lambda: self.split_text(text)
            )
            
            total_chunks = len(chunks)
            print(f"📦 Total chunks: {total_chunks}")
            
            # Procesar chunks en lotes para reducir llamadas a API
            tasks = []
            for i in range(0, total_chunks, self.batch_size):
                batch = chunks[i:i+self.batch_size]
                batch_indices = list(range(i+1, i+len(batch)+1))
                tasks.append(self.process_chunk_batch(batch, batch_indices, file, total_chunks))
            
            # Ejecutar procesamiento de lotes en paralelo
            await asyncio.gather(*tasks)
            
        except Exception as e:
            print(f"❌ Error procesando archivo {file['name']}: {str(e)}")
            traceback.print_exc()
    
    async def process_chunk_batch(self, chunks, indices, file, total_chunks):
        """Procesa un lote de chunks de forma asíncrona"""
        try:
            print(f"  🔄 Procesando lote {min(indices)}-{max(indices)} de {total_chunks}")
            
            # Generar embeddings (esto es sincrónico porque la API de OpenAI no es async)
            loop = asyncio.get_running_loop()
            embeddings = []
            
            # Usar un ThreadPoolExecutor para paralelizar las llamadas a la API de OpenAI
            with concurrent.futures.ThreadPoolExecutor(max_workers=len(chunks)) as executor:
                # Crear tareas para generar embeddings
                embed_tasks = [
                    loop.run_in_executor(
                        executor,
                        self.embeddings_model.embed_query,
                        chunk
                    )
                    for chunk in chunks
                ]
                
                # Esperar a que se completen todas las tareas
                embeddings = await asyncio.gather(*embed_tasks)
            
            # Crear los registros para Supabase
            records = []
            for i, (chunk, embedding, chunk_index) in enumerate(zip(chunks, embeddings, indices)):
                chunk_metadata = {
                    'file_id': file['id'],
                    'file_name': file['name'],
                    'file_type': file['mimeType'],
                    'chunk_number': chunk_index,
                    'total_chunks': total_chunks,
                    'modifiedTime': file.get('modifiedTime', ''),
                    'timestamp': datetime.now().isoformat()
                }
                
                records.append({
                    "content": chunk,
                    "embedding": embedding,
                    "metadata": chunk_metadata
                })
            
            # Insertar en Supabase (asíncrono)
            headers = {
                "Content-Type": "application/json",
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}"
            }
            
            async with aiohttp.ClientSession() as session:
                for record in records:
                    async with session.post(
                        f"{SUPABASE_URL}/rest/v1/tfinal",
                    headers=headers,
                        json=record
                    ) as response:
                        if response.status == 201:
                            print(f"    ✅ Chunk {record['metadata']['chunk_number']}/{total_chunks} indexado")
                        else:
                            error_text = await response.text()
                            print(f"    ❌ Error en chunk {record['metadata']['chunk_number']}: {error_text}")
                
        except Exception as e:
            print(f"  ❌ Error procesando lote {min(indices)}-{max(indices)}: {str(e)}")
            traceback.print_exc()

    async def _process_file_async(self, file):
        """Wrapper asíncrono para procesar un archivo"""
        await self.process_file_async(file)


class IndexerAgent:
    """Agente para recuperar documentos relevantes basados en consultas"""
    
    def __init__(self):
        """Inicializa el agente de documentos"""
        self.embeddings_model = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
    
    async def search_documents(self, query: str) -> List[Dict]:
        """
        Busca documentos relevantes para una consulta
        
        Args:
            query: Consulta del usuario
            filters: Filtros opcionales para la búsqueda
            
        Returns:
            Lista de documentos relevantes con sus metadatos
        """
        try:
            print(f"\n🔎 IndexerAgent: Buscando documentos para: '{query}'")
            
            # 1. Generar embedding de la consulta
            query_embedding = await self.embeddings_model.aembed_query(query)
            
            # 2. Buscar documentos similares en Supabase usando RPC
            params = {
                "query_embedding": query_embedding,
                "match_threshold": 0.8,  
                "match_count": 8
            }
            
            print(f"📤 Llamando match_tfinal con parámetros:")
            print(f"   🎯 Threshold: {params['match_threshold']}")
            print(f"   📊 Count: {params['match_count']}")
            print(f"   📏 Embedding dims: {len(query_embedding)}")
            
            # Usar helper para RPC call
            response = make_supabase_request(
                method="POST",
                endpoint="rpc/match_tfinal",
                data=params
            )
            
            # 3. Procesar resultados
            documents = response.json()
            print(f"📄 Documentos encontrados: {len(documents)}")
            print(f"🔍 Respuesta completa de la API: {len(documents)} documentos")
            
            # Debug: mostrar información de cada documento encontrado
            for i, doc in enumerate(documents, 1):
                file_name = doc.get('metadata', {}).get('file_name', 'Sin nombre')
                similarity = doc.get('similarity', 0)
                print(f"  📄 {i}. {file_name} (similitud: {similarity:.3f})")
            
            # 4. Devolver documentos relevantes con su contenido y metadata
            result_docs = []
            for doc in documents:
                    result_docs.append({
                    "content": doc.get("content", ""),
                    "metadata": doc.get("metadata", {}),
                    "similarity": doc.get("similarity", 0)
                    })
            
            return result_docs
        
        except Exception as e:
            print(f"❌ Error buscando documentos: {str(e)}")
            traceback.print_exc()
            return []
    



if __name__ == "__main__":
    # Código para ejecutar la indexación directamente
    print("📚 Ejecutando indexación optimizada de documentos...")
    indexer = DocumentIndexer()
    asyncio.run(indexer.index_documents())