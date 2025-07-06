"""
Tests básicos para verificar que el sistema de testing funciona correctamente.
"""

def test_basic_functionality():
    """Test básico que siempre pasa para verificar el sistema de testing."""
    assert True

def test_math_operations():
    """Test de operaciones matemáticas básicas."""
    assert 2 + 2 == 4
    assert 10 - 5 == 5
    assert 3 * 4 == 12
    assert 8 / 2 == 4

def test_string_operations():
    """Test de operaciones con strings."""
    text = "Hello World"
    assert len(text) == 11
    assert text.lower() == "hello world"
    assert text.upper() == "HELLO WORLD"
    assert "Hello" in text

def test_list_operations():
    """Test de operaciones con listas."""
    items = [1, 2, 3, 4, 5]
    assert len(items) == 5
    assert items[0] == 1
    assert items[-1] == 5
    assert 3 in items

def test_dict_operations():
    """Test de operaciones con diccionarios."""
    data = {"name": "Tony", "type": "assistant"}
    assert len(data) == 2
    assert data["name"] == "Tony"
    assert "type" in data

class TestConfiguration:
    """Clase de tests para verificar configuraciones básicas."""
    
    def test_configuration_exists(self):
        """Verificar que se puede crear configuración básica."""
        config = {
            "database_url": "test://localhost",
            "api_key": "test-key",
            "debug": True
        }
        assert config["debug"] is True
        assert "test" in config["database_url"]
    
    def test_environment_setup(self):
        """Verificar que el entorno de testing está configurado."""
        import os
        # Test que el entorno de Python está funcionando
        assert os.path.exists("/")  # En Unix/Linux systems
        assert hasattr(os, 'environ') 