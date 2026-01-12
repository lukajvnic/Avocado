"""
Unit tests for the TikTok scraper service.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import Response, Request
import httpx

from app.services.scraper import TikTokScraper
from app.services.exceptions import (
    InvalidTikTokURLError,
    SupadataAuthError,
    SupadataCreditsExhausted,
    SupadataAPIError
)
from app.schemas.tiktok import TikTokMetadata, TikTokTranscript


@pytest.fixture
def mock_settings():
    """Create mock settings for testing."""
    with patch('app.services.scraper.settings') as mock:
        mock.SUPADATA_API_KEY = 'test_key'
        mock.SUPADATA_BASE_URL = 'https://api.supadata.ai/v1'
        mock.SUPADATA_METADATA_ENDPOINT = '/metadata'
        mock.SUPADATA_TRANSCRIPT_ENDPOINT = '/transcript'
        mock.REQUEST_TIMEOUT = 30
        mock.CACHE_MAX_SIZE = 100
        mock.CACHE_TTL = 3600
        mock.MAX_RETRIES = 3
        mock.RETRY_DELAY = 0.1
        mock.RETRY_BACKOFF = 2.0
        yield mock


@pytest.fixture
def scraper(mock_settings):
    """Create a scraper instance for testing."""
    return TikTokScraper()


class TestTikTokScraperInit:
    """Tests for TikTokScraper initialization."""
    
    def test_init_with_valid_api_key(self, mock_settings):
        """Test successful initialization with valid API key."""
        scraper = TikTokScraper()
        assert scraper.api_key == 'test_key'
        assert scraper.base_url == 'https://api.supadata.ai/v1'
    
    def test_init_without_api_key_raises_error(self, mock_settings):
        """Test initialization fails without API key."""
        mock_settings.SUPADATA_API_KEY = None
        with pytest.raises(ValueError, match="SUPADATA_API_KEY is not configured"):
            TikTokScraper()


class TestCacheKey:
    """Tests for cache key generation."""
    
    def test_get_cache_key_returns_hash(self, scraper):
        """Test cache key generation returns consistent MD5 hash."""
        url = "https://www.tiktok.com/@user/video/123"
        key1 = scraper._get_cache_key(url, "metadata")
        key2 = scraper._get_cache_key(url, "metadata")
        
        assert key1 == key2
        assert len(key1) == 32  # MD5 hex digest length
    
    def test_different_endpoints_different_keys(self, scraper):
        """Test different endpoints produce different cache keys."""
        url = "https://www.tiktok.com/@user/video/123"
        metadata_key = scraper._get_cache_key(url, "metadata")
        transcript_key = scraper._get_cache_key(url, "transcript")
        
        assert metadata_key != transcript_key


class TestGetHeaders:
    """Tests for HTTP headers generation."""
    
    def test_get_headers_includes_api_key(self, scraper):
        """Test headers include API key."""
        headers = scraper._get_headers()
        
        assert headers["x-api-key"] == "test_key"
        assert headers["Content-Type"] == "application/json"


class TestFetchMetadata:
    """Tests for metadata fetching."""
    
    @pytest.mark.asyncio
    async def test_fetch_metadata_success(self, scraper):
        """Test successful metadata fetching."""
        mock_response_data = {
            "title": "Test Video Title",
            "description": "Test description",
            "author": {"username": "testuser", "displayName": "Test User"},
            "stats": {
                "likes": 1000,
                "views": 50000,
                "shares": 100,
                "comments": 50
            }
        }
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        
        url = "https://www.tiktok.com/@testuser/video/123456"
        result = await scraper._fetch_metadata(url, mock_client)
        
        assert isinstance(result, TikTokMetadata)
        assert result.title == "Test Video Title"
        assert result.author == "testuser"
        assert result.likes == 1000
        assert result.views == 50000
    
    @pytest.mark.asyncio
    async def test_fetch_metadata_auth_error(self, scraper):
        """Test handling of authentication errors (401)."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        
        url = "https://www.tiktok.com/@testuser/video/123456"
        
        with pytest.raises(SupadataAuthError):
            await scraper._fetch_metadata(url, mock_client)
    
    @pytest.mark.asyncio
    async def test_fetch_metadata_credits_exhausted(self, scraper):
        """Test handling of credits exhausted errors (402)."""
        mock_response = MagicMock()
        mock_response.status_code = 402
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        
        url = "https://www.tiktok.com/@testuser/video/123456"
        
        with pytest.raises(SupadataCreditsExhausted):
            await scraper._fetch_metadata(url, mock_client)
    
    @pytest.mark.asyncio
    async def test_fetch_metadata_rate_limit(self, scraper):
        """Test handling of rate limit errors (429)."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        
        url = "https://www.tiktok.com/@testuser/video/123456"
        
        with pytest.raises(SupadataAPIError) as exc_info:
            await scraper._fetch_metadata(url, mock_client)
        
        assert exc_info.value.status_code == 429
    
    @pytest.mark.asyncio
    async def test_fetch_metadata_uses_cache(self, scraper):
        """Test that metadata is served from cache on second request."""
        mock_response_data = {
            "title": "Test Video",
            "description": "Description",
            "author": {"username": "testuser"},
            "stats": {"likes": 100, "views": 1000, "shares": 10, "comments": 5}
        }
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        
        url = "https://www.tiktok.com/@testuser/video/123456"
        
        # First request
        result1 = await scraper._fetch_metadata(url, mock_client)
        # Second request (should use cache)
        result2 = await scraper._fetch_metadata(url, mock_client)
        
        assert result1.title == result2.title
        # Should only call API once
        assert mock_client.get.call_count == 1


class TestFetchTranscript:
    """Tests for transcript fetching."""
    
    @pytest.mark.asyncio
    async def test_fetch_transcript_success(self, scraper):
        """Test successful transcript fetching."""
        mock_response_data = {
            "content": "This is the transcript text",
            "lang": "en"
        }
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        
        url = "https://www.tiktok.com/@testuser/video/123456"
        result = await scraper._fetch_transcript(url, mock_client)
        
        assert isinstance(result, TikTokTranscript)
        assert result.text == "This is the transcript text"
        assert result.language == "en"
    
    @pytest.mark.asyncio
    async def test_fetch_transcript_not_found(self, scraper):
        """Test handling of missing transcript (404)."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        
        url = "https://www.tiktok.com/@testuser/video/123456"
        result = await scraper._fetch_transcript(url, mock_client)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_fetch_transcript_auth_error(self, scraper):
        """Test handling of authentication errors (401)."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        
        url = "https://www.tiktok.com/@testuser/video/123456"
        
        with pytest.raises(SupadataAuthError):
            await scraper._fetch_transcript(url, mock_client)
    
    @pytest.mark.asyncio
    async def test_fetch_transcript_credits_exhausted(self, scraper):
        """Test handling of credits exhausted errors (402)."""
        mock_response = MagicMock()
        mock_response.status_code = 402
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        
        url = "https://www.tiktok.com/@testuser/video/123456"
        
        with pytest.raises(SupadataCreditsExhausted):
            await scraper._fetch_transcript(url, mock_client)


class TestRetryRequest:
    """Tests for retry logic."""
    
    @pytest.mark.asyncio
    async def test_retry_on_rate_limit(self, scraper):
        """Test that requests are retried on rate limit."""
        call_count = 0
        
        async def mock_request():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise SupadataAPIError("Rate limit", status_code=429)
            return "success"
        
        result = await scraper._retry_request(mock_request, max_retries=3)
        
        assert result == "success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_no_retry_on_other_errors(self, scraper):
        """Test that non-rate-limit errors are not retried."""
        call_count = 0
        
        async def mock_request():
            nonlocal call_count
            call_count += 1
            raise SupadataAPIError("Server error", status_code=500)
        
        with pytest.raises(SupadataAPIError):
            await scraper._retry_request(mock_request, max_retries=3)
        
        assert call_count == 1


class TestFetchTikTokData:
    """Tests for the main fetch_tiktok_data method."""
    
    @pytest.mark.asyncio
    async def test_fetch_tiktok_data_success(self, scraper):
        """Test successful complete data fetching."""
        metadata_response = {
            "title": "Test Video",
            "description": "Test description",
            "author": {"username": "testuser"},
            "stats": {"likes": 100, "views": 1000, "shares": 10, "comments": 5}
        }
        transcript_response = {
            "content": "This is the transcript",
            "lang": "en"
        }
        
        with patch('app.services.scraper.clean_tiktok_url') as mock_clean, \
             patch('app.services.scraper.resolve_short_url', new_callable=AsyncMock) as mock_resolve, \
             patch('app.services.scraper.extract_video_id') as mock_extract, \
             patch('httpx.AsyncClient') as mock_client_class:
            
            mock_clean.return_value = "https://www.tiktok.com/@testuser/video/123"
            mock_resolve.return_value = "https://www.tiktok.com/@testuser/video/123"
            mock_extract.return_value = "123"
            
            # Mock the HTTP responses
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            metadata_resp = MagicMock()
            metadata_resp.status_code = 200
            metadata_resp.json.return_value = metadata_response
            
            transcript_resp = MagicMock()
            transcript_resp.status_code = 200
            transcript_resp.json.return_value = transcript_response
            
            mock_client.get.side_effect = [metadata_resp, transcript_resp]
            
            result = await scraper.fetch_tiktok_data("https://www.tiktok.com/@testuser/video/123")
            
            assert result.title == "Test Video"
            assert result.video_id == "123"
            assert result.has_transcript is True
            assert result.transcript == "This is the transcript"
    
    @pytest.mark.asyncio
    async def test_fetch_tiktok_data_invalid_url(self, scraper):
        """Test handling of invalid URL."""
        with patch('app.services.scraper.clean_tiktok_url') as mock_clean:
            mock_clean.side_effect = ValueError("Invalid URL")
            
            with pytest.raises(InvalidTikTokURLError):
                await scraper.fetch_tiktok_data("https://invalid-url.com/video")
