import traceback
from bs4 import BeautifulSoup
import aiohttp
import requests
import urllib3
from utilidades import SERP_API_KEY
from serpapi import GoogleSearch
import io
import PyPDF2


# Desactivar warnings SSL para sitios con certificados problemáticos
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class WebSearchAgent:
    """Agente para buscar información en la web y recuperar datos estructurados"""
    
    def __init__(self):
        """Inicializa el agente de búsqueda web"""
        self.serp_api_key = SERP_API_KEY
    
    async def get_web_data(self, query):
        """Recupera datos de la web sin generar respuestas
        
        Args:
            query: Consulta del usuario
            
        Returns:
            Dict con información estructurada de la web (resultados, contenido extraído)
        """
        try:
            print(f"\n🔍 WebSearchAgent: Buscando datos web para: '{query}'")
            
            # 1. Buscar con SerpAPI
            params = {
                "q": query,
                "api_key": self.serp_api_key,
                "engine": "google",
                "num": 10
            }
            
            search = GoogleSearch(params)
            results = search.get_dict()
            
            # 2. Procesar resultados
            web_results = []
            pdf_urls = []
            pdf_contents = {}
            non_pdf_content = {}
            
            # Extraer resultados orgánicos
            if "organic_results" in results:
                for result in results["organic_results"]:
                    title = result.get("title", "")
                    snippet = result.get("snippet", "")
                    link = result.get("link", "")
                    
                    web_results.append({
                        "title": title,
                        "snippet": snippet,
                        "url": link,
                        "type": "web"
                    })
                    
                    # Identificar PDFs
                    if link.lower().endswith(".pdf"):
                        pdf_urls.append(link)
            
            # Añadir Knowledge Graph si existe
            if "knowledge_graph" in results:
                kg = results["knowledge_graph"]
                if "title" in kg:
                    web_results.append({
                        "title": kg.get("title", ""),
                        "snippet": kg.get("description", ""),
                        "url": kg.get("website", ""),
                        "type": "knowledge_graph"
                    })
            
            # 3. Extraer contenido de PDFs (máximo 2)
            for url in pdf_urls[:2]:
                try:
                    content = self.extract_pdf_content(url)
                    if content and len(content) > 100:
                        pdf_contents[url] = content
                except Exception as e:
                    print(f"Error procesando PDF {url}: {str(e)}")
            
            # 4. Extraer contenido de páginas web (máximo 2)
            for result in web_results:
                if not result["url"].lower().endswith(".pdf") and len(non_pdf_content) < 2:
                    try:
                        async with aiohttp.ClientSession() as session:
                            async with session.get(result["url"], timeout=10) as response:
                                if response.status == 200:
                                    html = await response.text()
                                    
                                    # Procesar HTML
                                    soup = BeautifulSoup(html, 'html.parser')
                                    for tag in soup(["script", "style", "footer", "header", "nav"]):
                                        tag.extract()
                                    
                                    text = soup.get_text(separator="\n", strip=True)
                                    lines = [line.strip() for line in text.split("\n") if line.strip()]
                                    text = "\n".join(lines)
                                    
                                    if len(text) > 200:
                                        non_pdf_content[result["url"]] = text[:3000]
                    except Exception as e:
                        print(f"Error extrayendo contenido web de {result['url']}: {str(e)}")
            
            # 5. Retornar datos estructurados sin generar respuesta
            return {
                "web_results": web_results[:5],  # Resultados principales
                "pdf_contents": pdf_contents,    # Contenido de PDFs
                "web_contents": non_pdf_content, # Contenido de páginas web
                "query": query                   # Consulta original
            }
            
        except Exception as e:
            print(f"Error obteniendo datos web: {str(e)}")
            traceback.print_exc()
            return {"error": str(e)}
    
    def extract_pdf_content(self, url):
        """Descarga y extrae el contenido de un PDF"""
        try:
            
            print(f"📄 Descargando PDF: {url}")
            
            # Configurar la solicitud para ignorar errores SSL si es necesario
            session = requests.Session()
            session.verify = False  # Desactivar verificación SSL para sitios problemáticos
            
            # Añadir headers para evitar bloqueos
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            
            # Descargar el PDF
            response = session.get(url, headers=headers, timeout=15)
            if response.status_code != 200:
                return f"Error descargando PDF: código {response.status_code}"
            
            # Procesar el PDF
            with io.BytesIO(response.content) as f:
                reader = PyPDF2.PdfReader(f)
                text = ""
                # Extraer texto de las primeras 10 páginas (o menos si el PDF es más corto)
                max_pages = min(10, len(reader.pages))
                for i in range(max_pages):
                    page = reader.pages[i]
                    text += page.extract_text() + "\n\n"
                    
                summary = text[:2000]  # Limitar a 2000 caracteres para la respuesta
                return summary
                
        except Exception as e:
            print(f"Error al procesar PDF: {str(e)}")
            traceback.print_exc()
            return f"Error procesando PDF: {str(e)}" 