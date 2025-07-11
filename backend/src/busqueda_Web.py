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
        """Recupera datos de la web optimizados para consultas laborales
        
        Args:
            query: Consulta del usuario
            
        Returns:
            Dict con información estructurada de la web (resultados, contenido extraído)
        """
        try:
            print(f"\n🔍 WebSearchAgent: Buscando datos web para: '{query}'")
            
            # 1. Buscar con SerpAPI - optimizado para contenido laboral
            params = {
                "q": f"{query} Perú laboral empleo",
                "api_key": self.serp_api_key,
                "engine": "google",
                "num": 15,  # Más resultados para tener más opciones
                "gl": "pe",  # Geolocalización Perú
                "hl": "es"   # Idioma español
            }
            
            search = GoogleSearch(params)
            results = search.get_dict()
            
            # 2. Procesar resultados - priorizar documentos y contenido relevante
            web_results = []
            pdf_urls = []
            doc_urls = []  # URLs de documentos (.doc, .docx, etc.)
            pdf_contents = {}
            doc_contents = {}
            non_pdf_content = {}
            
            # Extraer resultados orgánicos
            if "organic_results" in results:
                for result in results["organic_results"]:
                    title = result.get("title", "")
                    snippet = result.get("snippet", "")
                    link = result.get("link", "")
                    
                    # Filtrar por relevancia laboral
                    if self._is_laboral_relevant(title, snippet):
                        web_results.append({
                            "title": title,
                            "snippet": snippet,
                            "url": link,
                            "type": "web"
                        })
                        
                        # Identificar documentos
                        if link.lower().endswith(".pdf"):
                            pdf_urls.append(link)
                        elif any(ext in link.lower() for ext in [".doc", ".docx", ".txt", ".rtf"]):
                            doc_urls.append(link)
            
            # 3. Extraer contenido de PDFs (máximo 3 para más información)
            for url in pdf_urls[:3]:
                try:
                    content = self.extract_pdf_content(url)
                    if content and len(content) > 100:
                        pdf_contents[url] = content
                        print(f"✅ PDF procesado: {len(content)} caracteres")
                except Exception as e:
                    print(f"❌ Error procesando PDF {url}: {str(e)}")
            
            # 4. Extraer contenido de páginas web (máximo 3)
            web_count = 0
            for result in web_results:
                if (not result["url"].lower().endswith(".pdf") and 
                    not any(ext in result["url"].lower() for ext in [".doc", ".docx", ".txt", ".rtf"]) and 
                    web_count < 3):
                    try:
                        async with aiohttp.ClientSession() as session:
                            async with session.get(result["url"], timeout=15) as response:
                                if response.status == 200:
                                    html = await response.text()
                                    
                                    # Procesar HTML - más agresivo en limpieza
                                    soup = BeautifulSoup(html, 'html.parser')
                                    # Remover elementos no deseados
                                    for tag in soup(["script", "style", "footer", "header", "nav", "aside", "advertisement", "ads"]):
                                        tag.extract()
                                    
                                    # Buscar contenido principal
                                    main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='content')
                                    if main_content:
                                        text = main_content.get_text(separator="\n", strip=True)
                                    else:
                                        text = soup.get_text(separator="\n", strip=True)
                                    
                                    # Limpiar y procesar texto
                                    lines = [line.strip() for line in text.split("\n") if line.strip() and len(line.strip()) > 10]
                                    text = "\n".join(lines)
                                    
                                    if len(text) > 500:  # Solo contenido sustancial
                                        non_pdf_content[result["url"]] = text[:5000]  # Más contenido
                                        web_count += 1
                                        print(f"✅ Página web procesada: {len(text)} caracteres")
                    except Exception as e:
                        print(f"❌ Error extrayendo contenido web de {result['url']}: {str(e)}")
            
            # 5. Retornar datos estructurados optimizados
            return {
                "web_results": web_results[:8],  # Más resultados principales
                "pdf_contents": pdf_contents,    # Contenido de PDFs
                "web_contents": non_pdf_content, # Contenido de páginas web
                "query": query,                  # Consulta original
                "total_content_chars": sum(len(content) for content in pdf_contents.values()) + 
                                     sum(len(content) for content in non_pdf_content.values())
            }
            
        except Exception as e:
            print(f"❌ Error obteniendo datos web: {str(e)}")
            traceback.print_exc()
            return {"error": str(e)}
    
    def _is_laboral_relevant(self, title: str, snippet: str) -> bool:
        """Verifica si un resultado es relevante para consultas laborales"""
        laboral_keywords = [
            'laboral', 'empleo', 'trabajo', 'contrato', 'sueldo', 'salario', 'vacaciones',
            'permiso', 'licencia', 'beneficio', 'seguridad social', 'essalud', 'onp',
            'afp', 'gratificación', 'cts', 'horario', 'jornada', 'despido', 'renuncia',
            'indemnización', 'sindicato', 'convenio', 'ley', 'norma', 'reglamento',
            'política', 'procedimiento', 'capacitación', 'evaluación', 'ascenso',
            'perú', 'peruano', 'ministerio trabajo', 'sunafil', 'mintra'
        ]
        
        text = f"{title} {snippet}".lower()
        return any(keyword in text for keyword in laboral_keywords)
    
    def extract_pdf_content(self, url):
        """Descarga y extrae el contenido de un PDF optimizado para información laboral"""
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
            response = session.get(url, headers=headers, timeout=20)
            if response.status_code != 200:
                return f"Error descargando PDF: código {response.status_code}"
            
            # Procesar el PDF
            with io.BytesIO(response.content) as f:
                reader = PyPDF2.PdfReader(f)
                text = ""
                
                # Extraer texto de más páginas para obtener más información
                max_pages = min(15, len(reader.pages))  # Hasta 15 páginas
                for i in range(max_pages):
                    page = reader.pages[i]
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n\n"
                
                # Limpiar y procesar el texto
                if text:
                    # Remover líneas muy cortas o repetitivas
                    lines = text.split('\n')
                    cleaned_lines = []
                    for line in lines:
                        line = line.strip()
                        if (len(line) > 5 and 
                            not line.isdigit() and 
                            not line.startswith('Página') and
                            not line.startswith('www.') and
                            len(line) < 200):  # Evitar líneas muy largas
                            cleaned_lines.append(line)
                    
                    text = '\n'.join(cleaned_lines)
                    
                    # Retornar más contenido (hasta 4000 caracteres)
                    return text[:4000] if len(text) > 4000 else text
                else:
                    return "No se pudo extraer texto del PDF"
                
        except Exception as e:
            print(f"❌ Error al procesar PDF: {str(e)}")
            traceback.print_exc()
            return f"Error procesando PDF: {str(e)}" 