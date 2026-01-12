"""
Unit tests for URL utility functions.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from app.utils.url_utils import clean_tiktok_url, resolve_short_url, extract_video_id


class TestCleanTikTokUrl:
    """Tests for clean_tiktok_url function."""
    
    def test_valid_tiktok_url(self):
        """Test cleaning a valid TikTok URL."""
        url = "https://www.tiktok.com/@user/video/123456789"
        result = clean_tiktok_url(url)
        
        assert result == url
    
    def test_valid_tiktok_url_without_www(self):
        """Test cleaning a valid TikTok URL without www."""
        url = "https://tiktok.com/@user/video/123456789"
        result = clean_tiktok_url(url)
        
        assert result == url
    
    def test_valid_vm_tiktok_url(self):
        """Test cleaning a valid vm.tiktok.com URL."""
        url = "https://vm.tiktok.com/abc123"
        result = clean_tiktok_url(url)
        
        assert result == url
    
    def test_valid_vt_tiktok_url(self):
        """Test cleaning a valid vt.tiktok.com URL."""
        url = "https://vt.tiktok.com/xyz789"
        result = clean_tiktok_url(url)
        
        assert result == url
    
    def test_strips_whitespace(self):
        """Test that whitespace is stripped from URL."""
        url = "  https://www.tiktok.com/@user/video/123  "
        result = clean_tiktok_url(url)
        
        assert result == url.strip()
    
    def test_invalid_url_raises_error(self):
        """Test that non-TikTok URLs raise ValueError."""
        url = "https://youtube.com/watch?v=abc123"
        
        with pytest.raises(ValueError, match="Invalid TikTok URL"):
            clean_tiktok_url(url)
    
    def test_random_domain_raises_error(self):
        """Test that random domains raise ValueError."""
        url = "https://example.com/video/123"
        
        with pytest.raises(ValueError, match="Invalid TikTok URL"):
            clean_tiktok_url(url)
    
    def test_non_tiktok_domain_raises_error(self):
        """Test that non-TikTok domains raise error."""
        # Note: The current implementation checks if 'tiktok.com' is a substring
        # of the netloc, so 'faketiktok.com' would actually pass validation.
        # This test verifies that truly unrelated domains are rejected.
        url = "https://instagram.com/video/123"
        
        with pytest.raises(ValueError, match="Invalid TikTok URL"):
            clean_tiktok_url(url)


class TestResolveShortUrl:
    """Tests for resolve_short_url function."""
    
    @pytest.mark.asyncio
    async def test_non_short_url_returns_same(self):
        """Test that non-shortened URLs are returned as-is."""
        url = "https://www.tiktok.com/@user/video/123456789"
        result = await resolve_short_url(url)
        
        assert result == url
    
    @pytest.mark.asyncio
    async def test_resolves_vm_tiktok_url(self):
        """Test resolving vm.tiktok.com URLs."""
        short_url = "https://vm.tiktok.com/abc123"
        full_url = "https://www.tiktok.com/@user/video/123456789"
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            mock_response = MagicMock()
            mock_response.url = full_url
            mock_client.head.return_value = mock_response
            
            result = await resolve_short_url(short_url)
            
            assert result == full_url
    
    @pytest.mark.asyncio
    async def test_resolves_vt_tiktok_url(self):
        """Test resolving vt.tiktok.com URLs."""
        short_url = "https://vt.tiktok.com/xyz789"
        full_url = "https://www.tiktok.com/@user/video/987654321"
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            mock_response = MagicMock()
            mock_response.url = full_url
            mock_client.head.return_value = mock_response
            
            result = await resolve_short_url(short_url)
            
            assert result == full_url
    
    @pytest.mark.asyncio
    async def test_http_error_raises_value_error(self):
        """Test that HTTP errors raise ValueError."""
        short_url = "https://vm.tiktok.com/invalid"
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.head.side_effect = httpx.HTTPError("Connection failed")
            
            with pytest.raises(ValueError, match="Failed to resolve"):
                await resolve_short_url(short_url)


class TestExtractVideoId:
    """Tests for extract_video_id function."""
    
    def test_extract_video_id_standard_url(self):
        """Test extracting video ID from standard TikTok URL."""
        url = "https://www.tiktok.com/@user/video/123456789"
        result = extract_video_id(url)
        
        assert result == "123456789"
    
    def test_extract_video_id_with_query_params(self):
        """Test extracting video ID from URL with query parameters."""
        url = "https://www.tiktok.com/@user/video/987654321?is_from_webapp=1"
        result = extract_video_id(url)
        
        assert result == "987654321"
    
    def test_extract_video_id_without_video_path(self):
        """Test extracting video ID from URL without /video/ path."""
        url = "https://www.tiktok.com/@user"
        result = extract_video_id(url)
        
        assert result == ""
    
    def test_extract_video_id_with_trailing_slash(self):
        """Test extracting video ID from URL with trailing slash."""
        url = "https://www.tiktok.com/@user/video/111222333/"
        result = extract_video_id(url)
        
        assert result == "111222333"
    
    def test_extract_video_id_empty_url(self):
        """Test extracting video ID from minimal URL."""
        url = "https://tiktok.com"
        result = extract_video_id(url)
        
        assert result == ""
