import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import sys
import os

# Agregar el directorio src al path para importar módulos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

from main import app

@pytest.fixture
def client():
    """Cliente de prueba para FastAPI"""
    return TestClient(app)

@pytest.fixture
def mock_env_vars():
    """Mock de variables de entorno para tests"""
    env_vars = {
        'OPENAI_API_KEY': 'test-key',
        'SUPABASE_URL': 'http://localhost:54321',
        'SUPABASE_KEY': 'test-key',
        'WHATSAPP_TOKEN': 'test-token',
        'REDIS_URL': 'redis://localhost:6379'
    }
    
    with patch.dict(os.environ, env_vars):
        yield env_vars

class TestHealthEndpoint:
    """Tests para el endpoint de health check"""
    
    def test_health_endpoint_returns_200(self, client):
        """El endpoint de health debe retornar 200"""
        response = client.get("/health")
        assert response.status_code == 200
    
    def test_health_endpoint_returns_correct_structure(self, client):
        """El endpoint de health debe retornar la estructura correcta"""
        response = client.get("/health")
        data = response.json()
        
        assert "status" in data
        assert "uptime" in data
        assert "version" in data
        assert data["status"] == "ok"
        assert data["version"] == "2.0.0"
    
    def test_health_endpoint_uptime_is_number(self, client):
        """El uptime debe ser un número"""
        response = client.get("/health")
        data = response.json()
        
        assert isinstance(data["uptime"], (int, float))
        assert data["uptime"] > 0

class TestUserStatsEndpoint:
    """Tests para el endpoint de estadísticas de usuarios"""
    
    def test_users_stats_endpoint_returns_200(self, client):
        """El endpoint de stats debe retornar 200"""
        response = client.get("/users/stats")
        assert response.status_code == 200
    
    def test_users_stats_returns_correct_structure(self, client):
        """El endpoint de stats debe retornar la estructura correcta"""
        response = client.get("/users/stats")
        data = response.json()
        
        assert "success" in data
        assert "active_users" in data
        assert "total_users" in data
        assert data["success"] is True
        assert isinstance(data["active_users"], list)
        assert isinstance(data["total_users"], int)

class TestWebhookEndpoint:
    """Tests para el endpoint de webhook"""
    
    def test_webhook_verify_with_correct_token(self, client, mock_env_vars):
        """Verificación de webhook con token correcto"""
        with patch.dict(os.environ, {'WEBHOOK_VERIFY_TOKEN': 'test-verify-token'}):
            response = client.get(
                "/webhook",
                params={
                    "hub.mode": "subscribe",
                    "hub.challenge": "1234567890",
                    "hub.verify_token": "test-verify-token"
                }
            )
            assert response.status_code == 200
            assert response.text == "1234567890"
    
    def test_webhook_verify_with_incorrect_token(self, client, mock_env_vars):
        """Verificación de webhook con token incorrecto"""
        with patch.dict(os.environ, {'WEBHOOK_VERIFY_TOKEN': 'test-verify-token'}):
            response = client.get(
                "/webhook",
                params={
                    "hub.mode": "subscribe",
                    "hub.challenge": "1234567890",
                    "hub.verify_token": "wrong-token"
                }
            )
            assert response.status_code == 403
    
    @patch('main.sync_whatsapp_message')
    @patch('main.get_orchestrator_for_user')
    def test_webhook_post_processes_whatsapp_message(self, mock_orchestrator, mock_sync, client, mock_env_vars):
        """El webhook debe procesar mensajes de WhatsApp correctamente"""
        # Mock del orquestador
        mock_orch_instance = MagicMock()
        mock_orch_instance.process_query.return_value = {"response": "Test response"}
        mock_orchestrator.return_value = mock_orch_instance
        
        # Mock de sync_whatsapp_message
        mock_sync.return_value = "whatsapp_1234567890"
        
        # Datos de webhook de WhatsApp
        webhook_data = {
            "object": "whatsapp_business_account",
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "from": "1234567890",
                            "type": "text",
                            "text": {"body": "Hola"}
                        }],
                        "contacts": [{
                            "profile": {"name": "Test User"}
                        }]
                    }
                }]
            }]
        }
        
        with patch('main.send_whatsapp_message') as mock_send:
            response = client.post("/webhook", json=webhook_data)
            
            assert response.status_code == 200
            mock_orchestrator.assert_called_once()
            mock_send.assert_called_once()

class TestMessagePreProcessor:
    """Tests para el preprocessor de mensajes"""
    
    @pytest.mark.asyncio
    async def test_message_preprocessor_corrects_spelling(self):
        """El preprocessor debe corregir errores ortográficos básicos"""
        from main import MessagePreProcessor
        
        with patch('main.ChatOpenAI') as mock_llm_class:
            # Mock del LLM
            mock_llm = MagicMock()
            mock_response = MagicMock()
            mock_response.content = "quiero información sobre cursos"
            mock_llm.ainvoke.return_value = mock_response
            mock_llm_class.return_value = mock_llm
            
            preprocessor = MessagePreProcessor()
            result = await preprocessor.process_message("kiero informacion sobre cursos")
            
            assert result == "quiero información sobre cursos"
    
    @pytest.mark.asyncio
    async def test_message_preprocessor_handles_errors(self):
        """El preprocessor debe manejar errores y retornar el texto original"""
        from main import MessagePreProcessor
        
        with patch('main.ChatOpenAI') as mock_llm_class:
            # Mock del LLM que lanza excepción
            mock_llm = MagicMock()
            mock_llm.ainvoke.side_effect = Exception("API Error")
            mock_llm_class.return_value = mock_llm
            
            preprocessor = MessagePreProcessor()
            original_text = "texto de prueba"
            result = await preprocessor.process_message(original_text)
            
            assert result == original_text

@pytest.mark.integration
class TestIntegrationFlow:
    """Tests de integración para el flujo completo"""
    
    @patch('main.get_orchestrator_for_user')
    @patch('main.send_whatsapp_message')
    def test_complete_whatsapp_flow(self, mock_send, mock_orchestrator, client, mock_env_vars):
        """Test del flujo completo desde webhook hasta respuesta"""
        # Setup mocks
        mock_orch_instance = MagicMock()
        mock_orch_instance.process_query.return_value = {
            "response": "Información sobre tus cursos disponibles"
        }
        mock_orchestrator.return_value = mock_orch_instance
        
        # Datos del webhook
        webhook_data = {
            "object": "whatsapp_business_account",
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "from": "51987654321",
                            "type": "text",
                            "text": {"body": "¿En qué cursos estoy inscrito?"}
                        }],
                        "contacts": [{
                            "profile": {"name": "Juan Pérez"}
                        }]
                    }
                }]
            }]
        }
        
        # Ejecutar request
        response = client.post("/webhook", json=webhook_data)
        
        # Verificaciones
        assert response.status_code == 200
        mock_orchestrator.assert_called_once_with("51987654321")
        mock_orch_instance.process_query.assert_called_once()
        mock_send.assert_called_once()
        
        # Verificar que se llamó con los datos correctos
        call_args = mock_send.call_args
        assert call_args[0][0] == "51987654321"  # phone_number
        assert "response" in call_args[0][1]  # response_data 