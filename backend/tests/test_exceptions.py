"""
Unit tests for custom exceptions.
"""
import pytest

from app.services.exceptions import (
    SupadataAPIError,
    SupadataAuthError,
    SupadataCreditsExhausted,
    InvalidTikTokURLError,
    TranscriptNotAvailableError,
    GeminiAPIError,
    GeminiAuthError,
    GeminiRateLimitError,
    GeminiQuotaExceededError
)


class TestSupadataExceptions:
    """Tests for Supadata API exceptions."""
    
    def test_supadata_api_error(self):
        """Test SupadataAPIError initialization."""
        error = SupadataAPIError("API error occurred", status_code=500)
        
        assert str(error) == "API error occurred"
        assert error.message == "API error occurred"
        assert error.status_code == 500
    
    def test_supadata_api_error_without_status_code(self):
        """Test SupadataAPIError without status code."""
        error = SupadataAPIError("Generic error")
        
        assert error.status_code is None
    
    def test_supadata_auth_error(self):
        """Test SupadataAuthError default message."""
        error = SupadataAuthError()
        
        assert "Invalid or missing Supadata API key" in str(error)
        assert error.status_code == 401
    
    def test_supadata_auth_error_custom_message(self):
        """Test SupadataAuthError with custom message."""
        error = SupadataAuthError("Custom auth error message")
        
        assert str(error) == "Custom auth error message"
        assert error.status_code == 401
    
    def test_supadata_credits_exhausted(self):
        """Test SupadataCreditsExhausted default message."""
        error = SupadataCreditsExhausted()
        
        assert "credits exhausted" in str(error)
        assert error.status_code == 402
    
    def test_supadata_credits_exhausted_custom_message(self):
        """Test SupadataCreditsExhausted with custom message."""
        error = SupadataCreditsExhausted("No more credits available")
        
        assert str(error) == "No more credits available"
        assert error.status_code == 402


class TestTikTokExceptions:
    """Tests for TikTok-related exceptions."""
    
    def test_invalid_tiktok_url_error(self):
        """Test InvalidTikTokURLError initialization."""
        url = "https://invalid-url.com"
        error = InvalidTikTokURLError(url)
        
        assert error.url == url
        assert "Invalid TikTok URL" in str(error)
        assert url in str(error)
    
    def test_transcript_not_available_error(self):
        """Test TranscriptNotAvailableError."""
        error = TranscriptNotAvailableError("No transcript")
        
        assert str(error) == "No transcript"


class TestGeminiExceptions:
    """Tests for Gemini API exceptions."""
    
    def test_gemini_api_error(self):
        """Test GeminiAPIError initialization."""
        original = Exception("Original error")
        error = GeminiAPIError("Gemini failed", original_error=original)
        
        assert str(error) == "Gemini failed"
        assert error.message == "Gemini failed"
        assert error.original_error == original
    
    def test_gemini_api_error_without_original(self):
        """Test GeminiAPIError without original error."""
        error = GeminiAPIError("Simple error")
        
        assert error.original_error is None
    
    def test_gemini_auth_error(self):
        """Test GeminiAuthError default message."""
        error = GeminiAuthError()
        
        assert "Invalid or missing Gemini API key" in str(error)
    
    def test_gemini_auth_error_with_original(self):
        """Test GeminiAuthError with original error."""
        original = Exception("401 Unauthorized")
        error = GeminiAuthError(original_error=original)
        
        assert error.original_error == original
    
    def test_gemini_rate_limit_error(self):
        """Test GeminiRateLimitError default message."""
        error = GeminiRateLimitError()
        
        assert "rate limit exceeded" in str(error)
    
    def test_gemini_quota_exceeded_error(self):
        """Test GeminiQuotaExceededError default message."""
        error = GeminiQuotaExceededError()
        
        assert "quota exceeded" in str(error)
    
    def test_exception_inheritance(self):
        """Test that exceptions inherit correctly."""
        assert issubclass(SupadataAuthError, SupadataAPIError)
        assert issubclass(SupadataCreditsExhausted, SupadataAPIError)
        assert issubclass(GeminiAuthError, GeminiAPIError)
        assert issubclass(GeminiRateLimitError, GeminiAPIError)
        assert issubclass(GeminiQuotaExceededError, GeminiAPIError)
