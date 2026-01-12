"""
Unit tests for API endpoints.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import status
import asyncio

from app.main import app
from app.schemas.tiktok import TikTokData
from app.schemas.result import FactCheckResult, CredibilityLevel, ClaimCheck
from app.services.exceptions import (
    InvalidTikTokURLError,
    SupadataAuthError,
    SupadataCreditsExhausted,
    SupadataAPIError,
    GeminiAPIError,
    GeminiAuthError,
    GeminiQuotaExceededError,
    GeminiRateLimitError
)


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def sample_tiktok_data():
    """Create sample TikTok data."""
    return TikTokData(
        url="https://www.tiktok.com/@user/video/123456",
        video_id="123456",
        title="Test Video",
        author="testuser",
        likes=1000,
        views=50000,
        has_transcript=True,
        transcript="Sample transcript text"
    )


@pytest.fixture
def sample_fact_check_result():
    """Create sample fact check result."""
    return FactCheckResult(
        video_url="https://www.tiktok.com/@user/video/123456",
        credibility_score=0.8,
        credibility_level=CredibilityLevel.HIGH,
        summary="The video appears credible.",
        claims=[],
        has_transcript=True,
        analyzed_text="Sample transcript text",
        processing_time_ms=1500
    )


class TestRootEndpoint:
    """Tests for the root endpoint."""
    
    def test_root_returns_welcome_message(self, client):
        """Test that root endpoint returns welcome message."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Avocado" in data["message"]
        assert "version" in data


class TestHealthEndpoint:
    """Tests for the health check endpoint."""
    
    def test_health_check_returns_healthy(self, client):
        """Test that health endpoint returns healthy status."""
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "avocado-fact-checker"


class TestScrapeMetadataEndpoint:
    """Tests for the /scrape-metadata endpoint."""
    
    def test_scrape_metadata_success(self, client, sample_tiktok_data):
        """Test successful metadata scraping."""
        with patch('app.api.v1.check.fetch_tiktok_data', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = sample_tiktok_data
            
            response = client.post(
                "/api/v1/scrape-metadata",
                json={"url": "https://www.tiktok.com/@user/video/123456"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["video_id"] == "123456"
            assert data["title"] == "Test Video"
    
    def test_scrape_metadata_invalid_url(self, client):
        """Test handling of invalid URL."""
        with patch('app.api.v1.check.fetch_tiktok_data', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = InvalidTikTokURLError("https://invalid.com")
            
            response = client.post(
                "/api/v1/scrape-metadata",
                json={"url": "https://invalid.com"}
            )
            
            assert response.status_code == 400
    
    def test_scrape_metadata_auth_error(self, client):
        """Test handling of authentication errors."""
        with patch('app.api.v1.check.fetch_tiktok_data', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = SupadataAuthError()
            
            response = client.post(
                "/api/v1/scrape-metadata",
                json={"url": "https://www.tiktok.com/@user/video/123"}
            )
            
            assert response.status_code == 401


class TestFactCheckEndpoint:
    """Tests for the /fact-check endpoint."""
    
    def test_fact_check_success(self, client, sample_tiktok_data, sample_fact_check_result):
        """Test successful fact checking."""
        with patch('app.api.v1.check.fact_checker') as mock_checker:
            mock_checker.analyze_credibility = AsyncMock(return_value=sample_fact_check_result)
            
            response = client.post(
                "/api/v1/fact-check",
                json=sample_tiktok_data.model_dump()
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["credibility_score"] == 0.8
    
    def test_fact_check_gemini_error(self, client, sample_tiktok_data):
        """Test handling of Gemini API errors."""
        with patch('app.api.v1.check.fact_checker') as mock_checker:
            mock_checker.analyze_credibility = AsyncMock(
                side_effect=GeminiAPIError("API Error")
            )
            
            response = client.post(
                "/api/v1/fact-check",
                json=sample_tiktok_data.model_dump()
            )
            
            assert response.status_code == 503


class TestCheckVideoEndpoint:
    """Tests for the main /check endpoint."""
    
    def test_check_video_success(self, client, sample_tiktok_data, sample_fact_check_result):
        """Test successful video check."""
        with patch('app.api.v1.check.fetch_tiktok_data', new_callable=AsyncMock) as mock_fetch, \
             patch('app.api.v1.check.fact_checker') as mock_checker:
            
            mock_fetch.return_value = sample_tiktok_data
            mock_checker.analyze_credibility = AsyncMock(return_value=sample_fact_check_result)
            
            response = client.post(
                "/api/v1/check",
                json={"url": "https://www.tiktok.com/@user/video/123456"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["credibility_score"] == 0.8
            assert data["credibility_level"] == "high"
    
    def test_check_video_invalid_url(self, client):
        """Test handling of invalid TikTok URL."""
        with patch('app.api.v1.check.fetch_tiktok_data', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = InvalidTikTokURLError("https://youtube.com/video")
            
            response = client.post(
                "/api/v1/check",
                json={"url": "https://youtube.com/video"}
            )
            
            assert response.status_code == 400
            assert "Invalid TikTok URL" in response.json()["detail"]
    
    def test_check_video_supadata_auth_error(self, client):
        """Test handling of Supadata auth errors."""
        with patch('app.api.v1.check.fetch_tiktok_data', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = SupadataAuthError()
            
            response = client.post(
                "/api/v1/check",
                json={"url": "https://www.tiktok.com/@user/video/123"}
            )
            
            assert response.status_code == 500
            assert "authentication failed" in response.json()["detail"]
    
    def test_check_video_supadata_credits_exhausted(self, client):
        """Test handling of exhausted API credits."""
        with patch('app.api.v1.check.fetch_tiktok_data', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = SupadataCreditsExhausted()
            
            response = client.post(
                "/api/v1/check",
                json={"url": "https://www.tiktok.com/@user/video/123"}
            )
            
            assert response.status_code == 402
            assert "credits exhausted" in response.json()["detail"]
    
    def test_check_video_supadata_rate_limit(self, client):
        """Test handling of rate limit errors."""
        with patch('app.api.v1.check.fetch_tiktok_data', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = SupadataAPIError("Rate limit exceeded", status_code=429)
            
            response = client.post(
                "/api/v1/check",
                json={"url": "https://www.tiktok.com/@user/video/123"}
            )
            
            assert response.status_code == 429
    
    def test_check_video_gemini_auth_error(self, client, sample_tiktok_data):
        """Test handling of Gemini auth errors."""
        with patch('app.api.v1.check.fetch_tiktok_data', new_callable=AsyncMock) as mock_fetch, \
             patch('app.api.v1.check.fact_checker') as mock_checker:
            
            mock_fetch.return_value = sample_tiktok_data
            mock_checker.analyze_credibility = AsyncMock(side_effect=GeminiAuthError())
            
            response = client.post(
                "/api/v1/check",
                json={"url": "https://www.tiktok.com/@user/video/123"}
            )
            
            assert response.status_code == 500
            assert "AI service authentication failed" in response.json()["detail"]
    
    def test_check_video_gemini_quota_exceeded(self, client, sample_tiktok_data):
        """Test handling of Gemini quota exceeded errors."""
        with patch('app.api.v1.check.fetch_tiktok_data', new_callable=AsyncMock) as mock_fetch, \
             patch('app.api.v1.check.fact_checker') as mock_checker:
            
            mock_fetch.return_value = sample_tiktok_data
            mock_checker.analyze_credibility = AsyncMock(side_effect=GeminiQuotaExceededError())
            
            response = client.post(
                "/api/v1/check",
                json={"url": "https://www.tiktok.com/@user/video/123"}
            )
            
            assert response.status_code == 402
    
    def test_check_video_gemini_rate_limit(self, client, sample_tiktok_data):
        """Test handling of Gemini rate limit errors."""
        with patch('app.api.v1.check.fetch_tiktok_data', new_callable=AsyncMock) as mock_fetch, \
             patch('app.api.v1.check.fact_checker') as mock_checker:
            
            mock_fetch.return_value = sample_tiktok_data
            mock_checker.analyze_credibility = AsyncMock(side_effect=GeminiRateLimitError())
            
            response = client.post(
                "/api/v1/check",
                json={"url": "https://www.tiktok.com/@user/video/123"}
            )
            
            assert response.status_code == 429
    
    def test_check_video_missing_url(self, client):
        """Test handling of missing URL in request."""
        response = client.post(
            "/api/v1/check",
            json={}
        )
        
        assert response.status_code == 422  # Validation error
