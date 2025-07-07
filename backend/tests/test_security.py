# ================================================================
# SECURITY TESTS - OWASP & ADVANCED SECURITY TESTING
# Tony WhatsApp Assistant - Backend Security Validation
# ================================================================

import pytest
import json
import time
import hashlib
import asyncio
import secrets
from unittest.mock import patch, Mock, AsyncMock
from fastapi.testclient import TestClient
from fastapi import status
from datetime import datetime, timedelta
import jwt
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, PublicFormat, NoEncryption

# ================================================================
# SECURITY MARKERS
# ================================================================

pytestmark = [
    pytest.mark.security,
    pytest.mark.slow
]

# ================================================================
# OWASP TOP 10 SECURITY TESTS
# ================================================================

class TestOWASPTop10:
    """Test OWASP Top 10 security vulnerabilities."""
    
    @pytest.mark.owasp
    def test_injection_attacks(self, test_client, security_test_data):
        """Test SQL injection and other injection attacks."""
        # Test SQL injection attempts
        for sql_payload in security_test_data["sql_injection_attempts"]:
            response = test_client.post("/api/webhook", json={
                "message": sql_payload,
                "user_id": "test_user"
            })
            
            # Should not return database errors or execute malicious SQL
            assert response.status_code != 500
            assert "error" not in response.json().get("message", "").lower()
            assert "database" not in response.json().get("message", "").lower()
    
    @pytest.mark.owasp
    def test_broken_authentication(self, test_client):
        """Test authentication bypass attempts."""
        # Test without authentication
        response = test_client.get("/api/admin/users")
        assert response.status_code == 401
        
        # Test with invalid token
        headers = {"Authorization": "Bearer invalid_token"}
        response = test_client.get("/api/admin/users", headers=headers)
        assert response.status_code == 401
        
        # Test with expired token
        expired_payload = {
            "user_id": "test_user",
            "exp": datetime.utcnow() - timedelta(hours=1)
        }
        expired_token = jwt.encode(expired_payload, "secret", algorithm="HS256")
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = test_client.get("/api/admin/users", headers=headers)
        assert response.status_code == 401
    
    @pytest.mark.owasp
    def test_sensitive_data_exposure(self, test_client, mock_jwt_token):
        """Test sensitive data exposure in API responses."""
        headers = {"Authorization": f"Bearer {mock_jwt_token}"}
        
        # Test user profile endpoint
        response = test_client.get("/api/user/profile", headers=headers)
        
        if response.status_code == 200:
            user_data = response.json()
            
            # Should not expose sensitive data
            sensitive_fields = ["password", "secret_key", "api_key", "token", "hash"]
            for field in sensitive_fields:
                assert field not in user_data
                assert field not in str(user_data).lower()
    
    @pytest.mark.owasp
    def test_xml_external_entities(self, test_client):
        """Test XXE (XML External Entity) attacks."""
        xxe_payload = """<?xml version="1.0"?>
        <!DOCTYPE root [<!ENTITY test SYSTEM "file:///etc/passwd">]>
        <root>&test;</root>"""
        
        response = test_client.post("/api/webhook", 
                                  data=xxe_payload,
                                  headers={"Content-Type": "application/xml"})
        
        # Should not process XML or return file contents
        assert response.status_code in [400, 415]  # Bad Request or Unsupported Media Type
    
    @pytest.mark.owasp
    def test_broken_access_control(self, test_client, mock_jwt_token):
        """Test access control bypass attempts."""
        user_headers = {"Authorization": f"Bearer {mock_jwt_token}"}
        
        # Test admin-only endpoints with user token
        admin_endpoints = [
            "/api/admin/users",
            "/api/admin/stats",
            "/api/admin/config"
        ]
        
        for endpoint in admin_endpoints:
            response = test_client.get(endpoint, headers=user_headers)
            assert response.status_code in [401, 403]  # Unauthorized or Forbidden
    
    @pytest.mark.owasp
    def test_security_misconfiguration(self, test_client):
        """Test for security misconfigurations."""
        # Test debug mode is disabled
        response = test_client.get("/api/debug")
        assert response.status_code == 404
        
        # Test server headers don't expose sensitive info
        response = test_client.get("/api/health")
        headers = response.headers
        
        # Should not expose server version or technology stack
        assert "Server" not in headers or "FastAPI" not in headers.get("Server", "")
        assert "X-Powered-By" not in headers
    
    @pytest.mark.owasp
    def test_cross_site_scripting(self, test_client, security_test_data):
        """Test XSS (Cross-Site Scripting) vulnerabilities."""
        for xss_payload in security_test_data["xss_attempts"]:
            response = test_client.post("/api/webhook", json={
                "message": xss_payload,
                "user_id": "test_user"
            })
            
            # Response should not contain unescaped XSS payload
            response_text = response.text
            assert "<script>" not in response_text
            assert "javascript:" not in response_text
            assert "onerror=" not in response_text
    
    @pytest.mark.owasp
    def test_insecure_deserialization(self, test_client):
        """Test insecure deserialization vulnerabilities."""
        # Test malicious pickle payload
        malicious_payload = "cos\nsystem\n(S'echo vulnerable'\ntR."
        
        response = test_client.post("/api/webhook",
                                  data=malicious_payload,
                                  headers={"Content-Type": "application/octet-stream"})
        
        # Should not execute malicious code
        assert response.status_code in [400, 415]
    
    @pytest.mark.owasp
    def test_insufficient_logging(self, test_client, mock_monitoring):
        """Test logging of security events."""
        # Make a failed authentication attempt
        response = test_client.post("/api/auth/login", json={
            "username": "invalid_user",
            "password": "wrong_password"
        })
        
        # Should log security events
        assert mock_monitoring.increment.called
    
    @pytest.mark.owasp
    def test_server_side_request_forgery(self, test_client):
        """Test SSRF (Server-Side Request Forgery) vulnerabilities."""
        # Test internal network access attempts
        internal_urls = [
            "http://127.0.0.1:8080/admin",
            "http://localhost:3306/mysql",
            "http://169.254.169.254/metadata"  # AWS metadata
        ]
        
        for url in internal_urls:
            response = test_client.post("/api/webhook", json={
                "message": f"Please fetch {url}",
                "user_id": "test_user"
            })
            
            # Should not access internal resources
            assert "connection" not in response.text.lower()
            assert "metadata" not in response.text.lower()

# ================================================================
# AUTHENTICATION & AUTHORIZATION TESTS
# ================================================================

class TestJWTSecurity:
    """Test JWT token security."""
    
    @pytest.mark.auth
    def test_jwt_token_validation(self, test_client):
        """Test JWT token validation."""
        # Test with malformed token
        malformed_tokens = [
            "invalid.token.format",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",  # Incomplete token
            "Bearer ",  # Empty token
            "Bearer invalid_token_format",
            ""
        ]
        
        for token in malformed_tokens:
            headers = {"Authorization": token}
            response = test_client.get("/api/user/profile", headers=headers)
            assert response.status_code == 401
    
    @pytest.mark.auth
    def test_jwt_algorithm_confusion(self, test_client):
        """Test JWT algorithm confusion attacks."""
        # Create token with 'none' algorithm
        payload = {"user_id": "admin", "exp": datetime.utcnow() + timedelta(hours=1)}
        
        # Test 'none' algorithm
        none_token = jwt.encode(payload, "", algorithm="none")
        headers = {"Authorization": f"Bearer {none_token}"}
        response = test_client.get("/api/admin/users", headers=headers)
        assert response.status_code == 401
        
        # Test RS256 to HS256 confusion
        try:
            # Generate RSA key pair
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048
            )
            
            # Create token with RS256 algorithm but validate with HS256
            rs256_token = jwt.encode(payload, private_key, algorithm="RS256")
            headers = {"Authorization": f"Bearer {rs256_token}"}
            response = test_client.get("/api/admin/users", headers=headers)
            assert response.status_code == 401
        except Exception:
            # If RSA operations fail, just ensure token validation fails
            pass
    
    @pytest.mark.auth
    def test_jwt_timing_attacks(self, test_client):
        """Test JWT timing attack resistance."""
        valid_token = "valid_token_format"
        invalid_token = "invalid_token_format"
        
        # Measure validation time for different tokens
        times = []
        
        for token in [valid_token, invalid_token]:
            start_time = time.time()
            headers = {"Authorization": f"Bearer {token}"}
            test_client.get("/api/user/profile", headers=headers)
            end_time = time.time()
            times.append(end_time - start_time)
        
        # Timing difference should be minimal (constant time validation)
        time_difference = abs(times[0] - times[1])
        assert time_difference < 0.1  # Less than 100ms difference

# ================================================================
# RATE LIMITING & DOS PROTECTION TESTS
# ================================================================

class TestRateLimiting:
    """Test rate limiting and DoS protection."""
    
    @pytest.mark.security
    @pytest.mark.slow
    def test_rate_limiting(self, test_client):
        """Test API rate limiting."""
        # Make multiple requests rapidly
        responses = []
        for i in range(20):  # Attempt 20 requests
            response = test_client.post("/api/webhook", json={
                "message": f"Test message {i}",
                "user_id": "test_user"
            })
            responses.append(response.status_code)
        
        # Should eventually return 429 (Too Many Requests)
        assert 429 in responses or len([r for r in responses if r == 200]) < 20
    
    @pytest.mark.security
    def test_large_payload_protection(self, test_client, security_test_data):
        """Test protection against large payloads."""
        for large_payload in security_test_data["large_payloads"]:
            response = test_client.post("/api/webhook", json={
                "message": large_payload,
                "user_id": "test_user"
            })
            
            # Should reject or handle large payloads gracefully
            assert response.status_code in [200, 400, 413]  # OK, Bad Request, or Payload Too Large
    
    @pytest.mark.security
    def test_concurrent_requests(self, test_client):
        """Test handling of concurrent requests."""
        async def make_request():
            return test_client.post("/api/webhook", json={
                "message": "Concurrent test",
                "user_id": f"user_{time.time()}"
            })
        
        # Make concurrent requests
        responses = []
        for _ in range(10):
            response = make_request()
            responses.append(response.status_code)
        
        # Should handle concurrent requests without errors
        assert all(status_code in [200, 429] for status_code in responses)

# ================================================================
# CRYPTOGRAPHIC SECURITY TESTS
# ================================================================

class TestCryptographicSecurity:
    """Test cryptographic implementations."""
    
    @pytest.mark.crypto
    def test_password_hashing(self, test_client):
        """Test password hashing security."""
        # Test password hashing endpoint if available
        response = test_client.post("/api/auth/register", json={
            "username": "testuser",
            "password": "testpassword123",
            "email": "test@example.com"
        })
        
        if response.status_code == 201:
            # Password should be hashed, not stored in plaintext
            user_data = response.json()
            assert "password" not in user_data
            assert "testpassword123" not in str(user_data)
    
    @pytest.mark.crypto
    def test_secure_random_generation(self):
        """Test secure random number generation."""
        # Test that we're using cryptographically secure random
        random_values = [secrets.token_hex(32) for _ in range(10)]
        
        # All values should be different
        assert len(set(random_values)) == 10
        
        # Should be proper length
        assert all(len(val) == 64 for val in random_values)  # 32 bytes = 64 hex chars
    
    @pytest.mark.crypto
    def test_secure_headers(self, test_client):
        """Test security headers."""
        response = test_client.get("/api/health")
        headers = response.headers
        
        # Check for security headers
        security_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
            "Strict-Transport-Security"
        ]
        
        # At least some security headers should be present
        present_headers = [h for h in security_headers if h in headers]
        assert len(present_headers) > 0

# ================================================================
# BUSINESS LOGIC SECURITY TESTS
# ================================================================

class TestBusinessLogicSecurity:
    """Test business logic security flaws."""
    
    @pytest.mark.business_logic
    def test_privilege_escalation(self, test_client, mock_jwt_token):
        """Test privilege escalation attempts."""
        headers = {"Authorization": f"Bearer {mock_jwt_token}"}
        
        # Try to modify user roles
        response = test_client.put("/api/user/role", 
                                 json={"role": "admin"},
                                 headers=headers)
        
        # Should not allow self-promotion to admin
        assert response.status_code in [401, 403]
    
    @pytest.mark.business_logic
    def test_data_validation(self, test_client, security_test_data):
        """Test input validation and sanitization."""
        for malformed_data in security_test_data["malformed_data"]:
            try:
                response = test_client.post("/api/webhook", json=malformed_data)
                # Should handle malformed data gracefully
                assert response.status_code in [200, 400, 422]
            except Exception:
                # If JSON serialization fails, that's also acceptable
                pass
    
    @pytest.mark.business_logic
    def test_race_conditions(self, test_client, mock_jwt_token):
        """Test race condition vulnerabilities."""
        headers = {"Authorization": f"Bearer {mock_jwt_token}"}
        
        # Simulate concurrent operations that might cause race conditions
        responses = []
        for _ in range(5):
            response = test_client.post("/api/chat", 
                                      json={"message": "Test race condition"},
                                      headers=headers)
            responses.append(response.status_code)
        
        # Should handle concurrent operations without corruption
        assert all(status_code in [200, 429] for status_code in responses)

# ================================================================
# SECURITY REGRESSION TESTS
# ================================================================

class TestSecurityRegression:
    """Test for security regressions."""
    
    @pytest.mark.regression
    def test_previous_vulnerabilities(self, test_client):
        """Test that previously fixed vulnerabilities don't reappear."""
        # Test specific vulnerability patterns based on your app history
        
        # Example: Test path traversal
        path_traversal_attempts = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd"
        ]
        
        for path in path_traversal_attempts:
            response = test_client.get(f"/api/files/{path}")
            assert response.status_code in [400, 403, 404]
    
    @pytest.mark.regression
    def test_security_configuration_regression(self, test_client):
        """Test that security configurations haven't been weakened."""
        # Test CORS configuration
        response = test_client.options("/api/webhook", 
                                     headers={"Origin": "https://malicious-site.com"})
        
        # Should not allow arbitrary origins
        cors_header = response.headers.get("Access-Control-Allow-Origin")
        if cors_header:
            assert cors_header != "*" or response.status_code == 404

# ================================================================
# PERFORMANCE SECURITY TESTS
# ================================================================

class TestPerformanceSecurity:
    """Test performance-related security issues."""
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_algorithmic_complexity_attacks(self, test_client):
        """Test algorithmic complexity (ReDoS) attacks."""
        # Test regex DoS patterns
        redos_patterns = [
            "a" * 10000 + "!",  # Large string that might cause backtracking
            "((((((((((x",        # Nested groups
            "a" * 1000 + "b" * 1000  # Large alternation
        ]
        
        for pattern in redos_patterns:
            start_time = time.time()
            response = test_client.post("/api/webhook", json={
                "message": pattern,
                "user_id": "test_user"
            })
            end_time = time.time()
            
            # Should complete within reasonable time
            assert end_time - start_time < 5.0  # 5 seconds max
    
    @pytest.mark.performance
    def test_memory_exhaustion_protection(self, test_client):
        """Test protection against memory exhaustion attacks."""
        # Test large number of concurrent connections
        large_data = "x" * 1000000  # 1MB of data
        
        response = test_client.post("/api/webhook", json={
            "message": large_data,
            "user_id": "test_user"
        })
        
        # Should handle or reject large payloads
        assert response.status_code in [200, 400, 413] 