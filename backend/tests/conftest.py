# ================================================================
# PYTEST CONFIGURATION AND FIXTURES
# Advanced Testing Setup for Tony WhatsApp Assistant
# ================================================================

import asyncio
import os
import tempfile
import pytest
import warnings
from unittest.mock import Mock, AsyncMock, patch
from typing import AsyncGenerator, Generator, Any, Dict
from faker import Faker
from freezegun import freeze_time
from datetime import datetime, timedelta
import fakeredis
import httpx
from fastapi.testclient import TestClient
from pathlib import Path
import json
import uuid

# Import your app modules
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from main import app  # Adjust import path as needed

# Configure Faker
fake = Faker(['es_ES', 'en_US'])  # Spanish and English locales
Faker.seed(12345)  # Reproducible fake data

# ================================================================
# PYTEST CONFIGURATION FIXTURES
# ================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment for all tests."""
    # Suppress warnings during tests
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    warnings.filterwarnings("ignore", category=PendingDeprecationWarning)
    
    # Set test environment variables
    os.environ["TESTING"] = "true"
    os.environ["LOG_LEVEL"] = "INFO"
    
    yield
    
    # Cleanup
    os.environ.pop("TESTING", None)

# ================================================================
# APPLICATION FIXTURES
# ================================================================

@pytest.fixture(scope="function")
def test_client():
    """Create a test client for the FastAPI app."""
    with TestClient(app) as client:
        yield client

@pytest.fixture(scope="function")
async def async_client():
    """Create an async test client for the FastAPI app."""
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        yield client

# ================================================================
# DATABASE FIXTURES
# ================================================================

@pytest.fixture(scope="function")
def mock_redis():
    """Create a fake Redis instance for testing."""
    fake_redis = fakeredis.FakeStrictRedis()
    with patch('redis.Redis', return_value=fake_redis):
        yield fake_redis

@pytest.fixture(scope="function")
def mock_database():
    """Mock database connection and operations."""
    mock_db = Mock()
    
    # Mock common database operations
    mock_db.execute = AsyncMock(return_value=Mock(rowcount=1))
    mock_db.fetch = AsyncMock(return_value=[])
    mock_db.fetchrow = AsyncMock(return_value=None)
    mock_db.transaction = AsyncMock()
    
    with patch('src.database_manager.DatabaseManager', return_value=mock_db):
        yield mock_db

# ================================================================
# WHATSAPP FIXTURES
# ================================================================

@pytest.fixture
def whatsapp_webhook_payload():
    """Generate a realistic WhatsApp webhook payload."""
    return {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": fake.random_number(digits=10),
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "+1234567890",
                                "phone_number_id": fake.random_number(digits=10)
                            },
                            "messages": [
                                {
                                    "from": fake.phone_number(),
                                    "id": fake.uuid4(),
                                    "timestamp": str(int(datetime.now().timestamp())),
                                    "text": {"body": fake.text(max_nb_chars=100)},
                                    "type": "text"
                                }
                            ]
                        },
                        "field": "messages"
                    }
                ]
            }
        ]
    }

@pytest.fixture
def whatsapp_message_data():
    """Generate WhatsApp message data for testing."""
    return {
        "phone_number": fake.phone_number(),
        "message": fake.text(max_nb_chars=200),
        "user_id": fake.uuid4(),
        "timestamp": datetime.now().isoformat(),
        "message_type": "text"
    }

# ================================================================
# AUTHENTICATION FIXTURES
# ================================================================

@pytest.fixture
def mock_jwt_token():
    """Generate a mock JWT token for testing."""
    from jose import jwt
    
    payload = {
        "user_id": fake.uuid4(),
        "username": fake.user_name(),
        "exp": datetime.utcnow() + timedelta(hours=1),
        "iat": datetime.utcnow(),
        "roles": ["user"]
    }
    
    # Mock secret key for testing
    secret_key = "test-secret-key-not-for-production"
    return jwt.encode(payload, secret_key, algorithm="HS256")

@pytest.fixture
def auth_headers(mock_jwt_token):
    """Generate authorization headers for API testing."""
    return {
        "Authorization": f"Bearer {mock_jwt_token}",
        "Content-Type": "application/json"
    }

# ================================================================
# AI/LLM FIXTURES
# ================================================================

@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response for testing."""
    return {
        "id": fake.uuid4(),
        "object": "chat.completion",
        "created": int(datetime.now().timestamp()),
        "model": "gpt-4",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": fake.text(max_nb_chars=500)
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": fake.random_int(min=10, max=100),
            "completion_tokens": fake.random_int(min=20, max=200),
            "total_tokens": fake.random_int(min=50, max=300)
        }
    }

@pytest.fixture
def mock_llm_service():
    """Mock LLM service for testing."""
    mock_service = Mock()
    mock_service.generate_response = AsyncMock(return_value=fake.text(max_nb_chars=200))
    mock_service.process_message = AsyncMock(return_value=fake.text(max_nb_chars=150))
    
    with patch('src.llm_service.LLMService', return_value=mock_service):
        yield mock_service

# ================================================================
# EXTERNAL SERVICES FIXTURES
# ================================================================

@pytest.fixture
def mock_google_drive():
    """Mock Google Drive service for testing."""
    mock_drive = Mock()
    mock_drive.upload_file = AsyncMock(return_value={"id": fake.uuid4()})
    mock_drive.download_file = AsyncMock(return_value=fake.binary())
    mock_drive.list_files = AsyncMock(return_value=[])
    
    with patch('src.google_drive_service.GoogleDriveService', return_value=mock_drive):
        yield mock_drive

@pytest.fixture
def mock_email_service():
    """Mock email service for testing."""
    mock_email = Mock()
    mock_email.send_email = AsyncMock(return_value=True)
    mock_email.send_notification = AsyncMock(return_value=True)
    
    with patch('src.email_service.EmailService', return_value=mock_email):
        yield mock_email

# ================================================================
# PERFORMANCE FIXTURES
# ================================================================

@pytest.fixture
def benchmark_config():
    """Configuration for benchmark tests."""
    return {
        "max_time": 1.0,  # Maximum execution time in seconds
        "min_rounds": 5,   # Minimum number of rounds
        "max_rounds": 100  # Maximum number of rounds
    }

# ================================================================
# SECURITY FIXTURES
# ================================================================

@pytest.fixture
def security_test_data():
    """Generate data for security testing."""
    return {
        "sql_injection_attempts": [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "' UNION SELECT * FROM users --"
        ],
        "xss_attempts": [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>"
        ],
        "large_payloads": [
            "A" * 10000,  # Large string
            {"data": "B" * 5000},  # Large JSON
        ],
        "malformed_data": [
            {"incomplete": "json"},
            "not_json_at_all",
            None,
            "",
            []
        ]
    }

# ================================================================
# REGRESSION FIXTURES
# ================================================================

@pytest.fixture
def regression_test_data():
    """Data for regression testing."""
    return {
        "previous_responses": {
            "greeting": "¡Hola! Soy Tony, tu asistente de WhatsApp.",
            "help": "Puedo ayudarte con consultas, enviar emails y gestionar archivos.",
            "error": "Lo siento, ocurrió un error. Por favor, intenta de nuevo."
        },
        "expected_formats": {
            "json_response": {"status": "success", "data": None},
            "error_response": {"status": "error", "message": str}
        }
    }

# ================================================================
# SNAPSHOT FIXTURES
# ================================================================

@pytest.fixture
def snapshot_config():
    """Configuration for snapshot testing."""
    return {
        "update_snapshots": os.getenv("UPDATE_SNAPSHOTS", "false").lower() == "true",
        "snapshot_dir": Path(__file__).parent / "snapshots"
    }

# ================================================================
# TEMPORARY FILES FIXTURES
# ================================================================

@pytest.fixture
def temp_file():
    """Create a temporary file for testing."""
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as f:
        f.write(fake.text())
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    try:
        os.unlink(temp_path)
    except FileNotFoundError:
        pass

@pytest.fixture
def temp_directory():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

# ================================================================
# MONITORING FIXTURES
# ================================================================

@pytest.fixture
def mock_monitoring():
    """Mock monitoring and metrics collection."""
    mock_metrics = Mock()
    mock_metrics.increment = Mock()
    mock_metrics.timing = Mock()
    mock_metrics.gauge = Mock()
    
    with patch('src.monitoring.metrics', mock_metrics):
        yield mock_metrics

# ================================================================
# CLEANUP FIXTURES
# ================================================================

@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Cleanup after each test."""
    yield
    
    # Clear any global state
    # Reset mocks
    # Clear caches
    pass 