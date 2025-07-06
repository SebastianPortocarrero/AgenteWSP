# ================================================================
# PERFORMANCE TESTS - BENCHMARKING & LOAD TESTING
# Tony WhatsApp Assistant - Backend Performance Validation
# ================================================================

import pytest
import time
import asyncio
import statistics
from unittest.mock import patch, Mock, AsyncMock
from concurrent.futures import ThreadPoolExecutor, as_completed
import psutil
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any

# ================================================================
# PERFORMANCE MARKERS
# ================================================================

pytestmark = [
    pytest.mark.performance,
    pytest.mark.slow
]

# ================================================================
# BENCHMARK CONFIGURATION
# ================================================================

PERFORMANCE_THRESHOLDS = {
    "api_response_time": 0.5,    # 500ms max
    "webhook_processing": 1.0,    # 1s max
    "database_query": 0.1,       # 100ms max
    "ai_processing": 3.0,        # 3s max
    "concurrent_requests": 10,    # 10 concurrent max
    "memory_usage": 100,         # 100MB max increase
    "cpu_usage": 80              # 80% max CPU
}

# ================================================================
# API PERFORMANCE TESTS
# ================================================================

class TestAPIPerformance:
    """Test API endpoint performance."""
    
    @pytest.mark.benchmark
    def test_health_endpoint_performance(self, test_client, benchmark):
        """Benchmark health endpoint performance."""
        def health_check():
            return test_client.get("/api/health")
        
        result = benchmark(health_check)
        
        # Should respond quickly
        assert result.status_code == 200
        assert benchmark.stats.mean < PERFORMANCE_THRESHOLDS["api_response_time"]
    
    @pytest.mark.benchmark
    def test_webhook_endpoint_performance(self, test_client, benchmark, whatsapp_webhook_payload):
        """Benchmark webhook endpoint performance."""
        def webhook_request():
            return test_client.post("/api/webhook", json=whatsapp_webhook_payload)
        
        result = benchmark(webhook_request)
        
        # Should process webhook within threshold
        assert result.status_code in [200, 202]
        assert benchmark.stats.mean < PERFORMANCE_THRESHOLDS["webhook_processing"]
    
    @pytest.mark.benchmark
    async def test_async_endpoint_performance(self, async_client, benchmark):
        """Benchmark async endpoint performance."""
        async def async_request():
            return await async_client.get("/api/health")
        
        result = await benchmark(async_request)
        
        assert result.status_code == 200
        assert benchmark.stats.mean < PERFORMANCE_THRESHOLDS["api_response_time"]

# ================================================================
# LOAD TESTING
# ================================================================

class TestLoadTesting:
    """Test system under load."""
    
    @pytest.mark.load
    def test_concurrent_webhook_requests(self, test_client, whatsapp_webhook_payload):
        """Test handling of concurrent webhook requests."""
        num_requests = 20
        max_workers = 10
        
        def make_request(request_id):
            payload = whatsapp_webhook_payload.copy()
            payload["entry"][0]["changes"][0]["value"]["messages"][0]["id"] = f"msg_{request_id}"
            
            start_time = time.time()
            response = test_client.post("/api/webhook", json=payload)
            end_time = time.time()
            
            return {
                "request_id": request_id,
                "status_code": response.status_code,
                "response_time": end_time - start_time,
                "response_size": len(response.content)
            }
        
        # Execute concurrent requests
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(make_request, i) for i in range(num_requests)]
            results = [future.result() for future in as_completed(futures)]
        
        total_time = time.time() - start_time
        
        # Analyze results
        response_times = [r["response_time"] for r in results]
        status_codes = [r["status_code"] for r in results]
        success_codes = [code for code in status_codes if code in [200, 202]]
        
        # Performance assertions
        assert len(success_codes) >= num_requests * 0.8  # 80% success rate
        assert statistics.mean(response_times) < PERFORMANCE_THRESHOLDS["webhook_processing"]
        assert max(response_times) < PERFORMANCE_THRESHOLDS["webhook_processing"] * 2
        assert total_time < PERFORMANCE_THRESHOLDS["webhook_processing"] * 2
    
    @pytest.mark.load
    def test_sustained_load(self, test_client):
        """Test sustained load over time."""
        duration = 30  # 30 seconds
        requests_per_second = 5
        
        results = []
        start_time = time.time()
        
        while time.time() - start_time < duration:
            batch_start = time.time()
            
            # Make batch of requests
            for _ in range(requests_per_second):
                request_start = time.time()
                response = test_client.get("/api/health")
                request_end = time.time()
                
                results.append({
                    "timestamp": request_start,
                    "response_time": request_end - request_start,
                    "status_code": response.status_code
                })
            
            # Wait for next batch
            batch_duration = time.time() - batch_start
            if batch_duration < 1.0:
                time.sleep(1.0 - batch_duration)
        
        # Analyze sustained performance
        response_times = [r["response_time"] for r in results]
        success_rate = len([r for r in results if r["status_code"] == 200]) / len(results)
        
        assert success_rate >= 0.95  # 95% success rate
        assert statistics.mean(response_times) < PERFORMANCE_THRESHOLDS["api_response_time"]
        assert statistics.stdev(response_times) < 0.1  # Low variance

# ================================================================
# MEMORY PERFORMANCE TESTS
# ================================================================

class TestMemoryPerformance:
    """Test memory usage and leaks."""
    
    @pytest.mark.memory
    def test_memory_usage_under_load(self, test_client):
        """Test memory usage under load."""
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Generate load
        for i in range(100):
            response = test_client.post("/api/webhook", json={
                "message": f"Memory test message {i}",
                "user_id": f"user_{i}"
            })
            
            # Check memory every 10 requests
            if i % 10 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_increase = current_memory - initial_memory
                
                # Memory increase should be reasonable
                assert memory_increase < PERFORMANCE_THRESHOLDS["memory_usage"]
        
        # Final memory check
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        total_increase = final_memory - initial_memory
        
        assert total_increase < PERFORMANCE_THRESHOLDS["memory_usage"]
    
    @pytest.mark.memory
    def test_memory_leak_detection(self, test_client):
        """Test for memory leaks over repeated operations."""
        process = psutil.Process()
        memory_samples = []
        
        for i in range(50):
            # Perform operations
            test_client.post("/api/webhook", json={
                "message": f"Leak test {i}",
                "user_id": "leak_test_user"
            })
            
            # Sample memory every 5 iterations
            if i % 5 == 0:
                memory_mb = process.memory_info().rss / 1024 / 1024
                memory_samples.append(memory_mb)
        
        # Check for memory leak pattern
        if len(memory_samples) > 3:
            # Calculate trend
            x_values = list(range(len(memory_samples)))
            y_values = memory_samples
            
            # Simple linear regression to detect trend
            n = len(x_values)
            sum_x = sum(x_values)
            sum_y = sum(y_values)
            sum_xy = sum(x * y for x, y in zip(x_values, y_values))
            sum_x2 = sum(x * x for x in x_values)
            
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
            
            # Slope should be close to 0 (no significant memory growth)
            assert abs(slope) < 1.0  # Less than 1MB per iteration trend

# ================================================================
# CPU PERFORMANCE TESTS
# ================================================================

class TestCPUPerformance:
    """Test CPU usage and efficiency."""
    
    @pytest.mark.cpu
    def test_cpu_usage_under_load(self, test_client):
        """Test CPU usage under load."""
        # Monitor CPU usage
        cpu_samples = []
        
        def monitor_cpu():
            for _ in range(10):
                cpu_percent = psutil.cpu_percent(interval=1)
                cpu_samples.append(cpu_percent)
        
        # Start CPU monitoring in background
        import threading
        monitor_thread = threading.Thread(target=monitor_cpu)
        monitor_thread.start()
        
        # Generate CPU load
        for i in range(50):
            test_client.post("/api/webhook", json={
                "message": f"CPU test message {i}",
                "user_id": f"user_{i}"
            })
        
        monitor_thread.join()
        
        # Analyze CPU usage
        if cpu_samples:
            avg_cpu = statistics.mean(cpu_samples)
            max_cpu = max(cpu_samples)
            
            # CPU usage should be reasonable
            assert avg_cpu < PERFORMANCE_THRESHOLDS["cpu_usage"]
            assert max_cpu < PERFORMANCE_THRESHOLDS["cpu_usage"] + 10

# ================================================================
# DATABASE PERFORMANCE TESTS
# ================================================================

class TestDatabasePerformance:
    """Test database performance."""
    
    @pytest.mark.database
    @pytest.mark.benchmark
    def test_database_query_performance(self, benchmark, mock_database):
        """Benchmark database query performance."""
        def query_operation():
            # Mock database operation
            return mock_database.fetchrow("SELECT * FROM users WHERE id = $1", "test_user")
        
        result = benchmark(query_operation)
        
        # Database queries should be fast
        assert benchmark.stats.mean < PERFORMANCE_THRESHOLDS["database_query"]
    
    @pytest.mark.database
    def test_database_connection_pooling(self, mock_database):
        """Test database connection pooling efficiency."""
        # Simulate multiple database operations
        operations = []
        
        for i in range(20):
            start_time = time.time()
            mock_database.fetchrow("SELECT * FROM users WHERE id = $1", f"user_{i}")
            end_time = time.time()
            operations.append(end_time - start_time)
        
        # Connection pooling should provide consistent performance
        avg_time = statistics.mean(operations)
        max_time = max(operations)
        
        assert avg_time < PERFORMANCE_THRESHOLDS["database_query"]
        assert max_time < PERFORMANCE_THRESHOLDS["database_query"] * 2

# ================================================================
# AI/LLM PERFORMANCE TESTS
# ================================================================

class TestAIPerformance:
    """Test AI/LLM performance."""
    
    @pytest.mark.ai
    @pytest.mark.benchmark
    def test_ai_response_performance(self, benchmark, mock_llm_service):
        """Benchmark AI response generation performance."""
        def ai_processing():
            return mock_llm_service.generate_response("Test message")
        
        result = benchmark(ai_processing)
        
        # AI processing should complete within threshold
        assert benchmark.stats.mean < PERFORMANCE_THRESHOLDS["ai_processing"]
    
    @pytest.mark.ai
    def test_ai_concurrent_processing(self, mock_llm_service):
        """Test AI service under concurrent load."""
        num_requests = 10
        
        async def process_ai_request(message):
            start_time = time.time()
            result = await mock_llm_service.generate_response(message)
            end_time = time.time()
            return end_time - start_time
        
        async def run_concurrent_ai_tests():
            tasks = [
                process_ai_request(f"Test message {i}")
                for i in range(num_requests)
            ]
            return await asyncio.gather(*tasks)
        
        # Run concurrent AI processing
        processing_times = asyncio.run(run_concurrent_ai_tests())
        
        # Analyze performance
        avg_time = statistics.mean(processing_times)
        max_time = max(processing_times)
        
        assert avg_time < PERFORMANCE_THRESHOLDS["ai_processing"]
        assert max_time < PERFORMANCE_THRESHOLDS["ai_processing"] * 1.5

# ================================================================
# NETWORK PERFORMANCE TESTS
# ================================================================

class TestNetworkPerformance:
    """Test network-related performance."""
    
    @pytest.mark.network
    def test_response_compression(self, test_client):
        """Test response compression efficiency."""
        # Request with compression
        headers = {"Accept-Encoding": "gzip, deflate"}
        response = test_client.get("/api/health", headers=headers)
        
        # Should support compression for appropriate responses
        if len(response.content) > 1024:  # Only for larger responses
            assert "gzip" in response.headers.get("Content-Encoding", "")
    
    @pytest.mark.network
    def test_request_timeout_handling(self, test_client):
        """Test request timeout handling."""
        # Test with various timeout scenarios
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.side_effect = asyncio.TimeoutError("Request timeout")
            
            response = test_client.post("/api/webhook", json={
                "message": "Timeout test",
                "user_id": "timeout_user"
            })
            
            # Should handle timeouts gracefully
            assert response.status_code in [200, 408, 500]

# ================================================================
# REGRESSION PERFORMANCE TESTS
# ================================================================

class TestPerformanceRegression:
    """Test for performance regressions."""
    
    @pytest.mark.regression
    def test_performance_baseline(self, test_client, benchmark):
        """Test against performance baseline."""
        def baseline_operation():
            return test_client.get("/api/health")
        
        result = benchmark(baseline_operation)
        
        # Should meet baseline performance
        assert benchmark.stats.mean < PERFORMANCE_THRESHOLDS["api_response_time"]
        assert benchmark.stats.stddev < 0.05  # Low variance
    
    @pytest.mark.regression
    def test_performance_consistency(self, test_client):
        """Test performance consistency across multiple runs."""
        response_times = []
        
        for _ in range(20):
            start_time = time.time()
            response = test_client.get("/api/health")
            end_time = time.time()
            
            response_times.append(end_time - start_time)
            assert response.status_code == 200
        
        # Performance should be consistent
        avg_time = statistics.mean(response_times)
        stddev = statistics.stdev(response_times)
        
        assert avg_time < PERFORMANCE_THRESHOLDS["api_response_time"]
        assert stddev / avg_time < 0.3  # Coefficient of variation < 30%

# ================================================================
# SCALABILITY TESTS
# ================================================================

class TestScalability:
    """Test system scalability."""
    
    @pytest.mark.scalability
    def test_user_scalability(self, test_client):
        """Test handling of multiple users."""
        num_users = 100
        results = []
        
        for user_id in range(num_users):
            start_time = time.time()
            response = test_client.post("/api/webhook", json={
                "message": f"User {user_id} message",
                "user_id": f"user_{user_id}"
            })
            end_time = time.time()
            
            results.append({
                "user_id": user_id,
                "response_time": end_time - start_time,
                "status_code": response.status_code
            })
        
        # Analyze scalability
        response_times = [r["response_time"] for r in results]
        success_rate = len([r for r in results if r["status_code"] in [200, 202]]) / len(results)
        
        assert success_rate >= 0.95  # 95% success rate
        assert statistics.mean(response_times) < PERFORMANCE_THRESHOLDS["webhook_processing"]
    
    @pytest.mark.scalability
    def test_data_volume_scalability(self, test_client):
        """Test handling of increasing data volumes."""
        message_sizes = [100, 500, 1000, 5000, 10000]  # bytes
        
        for size in message_sizes:
            large_message = "x" * size
            
            start_time = time.time()
            response = test_client.post("/api/webhook", json={
                "message": large_message,
                "user_id": "scalability_test"
            })
            end_time = time.time()
            
            response_time = end_time - start_time
            
            # Should handle larger messages reasonably
            assert response.status_code in [200, 202, 413]  # OK, Accepted, or Payload Too Large
            
            if response.status_code in [200, 202]:
                # Response time should scale reasonably with message size
                expected_max_time = PERFORMANCE_THRESHOLDS["webhook_processing"] * (size / 1000)
                assert response_time < expected_max_time 