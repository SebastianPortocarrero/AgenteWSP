import os
from pathlib import Path
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import json
import re
from typing import Dict, Any, Optional
import requests
# Determinar la ruta base del proyecto (un nivel arriba de src)
BASE_DIR = Path(__file__).resolve().parent.parent

# Cargar variables de entorno con mejor manejo de errores
env_path = BASE_DIR / "config" / ".env"

# Cargar el archivo .env e imprimir confirmación
load_dotenv(dotenv_path=env_path)
print(f"✅ Archivo .env cargado desde: {env_path}")

# Verificar que las claves API esenciales estén presentes
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


# Resto de variables de entorno
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_TABLE = "tfinal"
GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
SERP_API_KEY = os.getenv("SERP_API_KEY")

def get_google_drive_service():
    """Obtiene el servicio de Google Drive utilizando credenciales guardadas o autenticación OOB."""
    creds = None
    
    # Definir la ruta para token.json
    token_path = BASE_DIR / "config" / "token.json"
    
    # Intentar cargar el archivo token.json
    if token_path.exists():
        try:
            with open(token_path, 'r') as token_file:
                creds_data = json.load(token_file)
            creds = Credentials.from_authorized_user_info(creds_data)
            print(f"✅ Token cargado desde: {token_path}")
        except Exception as e:
            print(f"❌ Error cargando token.json desde {token_path}: {e}")
            creds = None

    # Verificar la validez de las credenciales
    if not creds or not creds.valid:
        # Si las credenciales están expiradas y se puede refrescar, intentamos refrescarlas
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"❌ Error refrescando token: {e}")
                creds = None

        # Si no se obtuvieron credenciales válidas, iniciar el flujo de autenticación OOB
        if not creds:
            # Definir la ruta para client_secret.json
            client_secret_path = BASE_DIR / "config" / "client_secret.json"
            
            # Verificar que el archivo client_secret.json existe
            if not client_secret_path.exists():
                raise FileNotFoundError(f"No se encontró el archivo client_secret.json en: {client_secret_path}")
            
            client_secret_file = str(client_secret_path)

            print(f"📂 Usando archivo de credenciales: {client_secret_file}")

            # Crear el flujo con redirect_uri configurado para OOB
            flow = InstalledAppFlow.from_client_secrets_file(
                client_secret_file, 
                scopes=['https://www.googleapis.com/auth/drive.readonly'],
                redirect_uri='urn:ietf:wg:oauth:2.0:oob'
            )

            # Generar la URL de autorización y pedir al usuario que ingrese el código
            auth_url, _ = flow.authorization_url(prompt='consent')
            print("1) Abre esta URL en tu navegador:\n", auth_url)
            code = input("2) Ingresa el código de autorización que te dio Google: ")

            # Intercambiar el código por credenciales
            flow.fetch_token(code=code)
            creds = flow.credentials

            # Guardar las credenciales en config/token.json
            token_path = BASE_DIR / "config" / "token.json"
            with open(token_path, 'w') as token_file:
                token_file.write(creds.to_json())

            print(f"✅ ¡Éxito! Se ha creado el archivo token.json en {token_path}")

    # Crear el servicio de Google Drive con las credenciales obtenidas
    service = build('drive', 'v3', credentials=creds)
    return service


def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """Extrae un objeto JSON válido de un texto, incluso si hay contenido adicional."""
    try:
        # Intentar primero parsear directamente
        return json.loads(text)
    except:
        # Si falla, intentar extraer usando regex
        try:
            json_pattern = r'(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})'
            matches = re.findall(json_pattern, text, re.DOTALL)
            
            if matches:
                for potential_json in matches:
                    try:
                        return json.loads(potential_json)
                    except:
                        continue
        except:
            pass
    
    return None

def get_supabase_headers() -> Dict[str, str]:
    """
    Genera headers estándar para peticiones a Supabase.
    Centraliza la configuración y elimina repetición de código.
    
    Returns:
        Dict con headers necesarios para Supabase
    """
    return {
        "Content-Type": "application/json",
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }

def make_supabase_request(method: str, endpoint: str, data: Dict = None, params: Dict = None) -> requests.Response:
    """
    Realiza peticiones HTTP a Supabase de forma simplificada.
    
    Args:
        method: Método HTTP (GET, POST, PUT, DELETE, etc.)
        endpoint: Endpoint relativo (ej: 'tfinal', 'chat_history')
        data: Datos para el body (opcional)
        params: Parámetros de query (opcional)
    
    Returns:
        requests.Response object
    """
    url = f"{SUPABASE_URL}/rest/v1/{endpoint}"
    headers = get_supabase_headers()
    
    return requests.request(
        method=method,
        url=url,
        headers=headers,
        json=data,
        params=params
    )