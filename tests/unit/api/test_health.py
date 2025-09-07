"""
Tests for health API endpoint
"""
import pytest
from datetime import datetime

class TestHealthAPI:
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "service" in data
        assert "environment" in data
        assert "version" in data
        
        # Validate timestamp format
        timestamp_str = data["timestamp"]
        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        assert isinstance(timestamp, datetime)

    def test_health_response_structure(self, client):
        """Test health response has all required fields"""
        response = client.get("/api/health")
        data = response.json()
        
        required_fields = ["status", "timestamp", "service", "environment", "version"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

    def test_health_status_values(self, client):
        """Test health status contains expected values"""
        response = client.get("/api/health")
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["service"] == "Agent Platform"
        assert data["version"] == "1.0.0"
        assert data["environment"] in ["development", "testing", "production"]