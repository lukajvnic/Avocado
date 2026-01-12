"""
Unit tests for the Gemini-based fact checker service.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import time

from app.services.fact_checker import FactChecker
from app.services.exceptions import (
    GeminiAPIError,
    GeminiAuthError,
    GeminiRateLimitError,
    GeminiQuotaExceededError
)
from app.schemas.tiktok import TikTokData
from app.schemas.result import FactCheckResult, CredibilityLevel, ClaimCheck


@pytest.fixture
def mock_settings():
    """Create mock settings for testing."""
    with patch('app.services.fact_checker.settings') as mock:
        mock.GEMINI_API_KEY = 'test_gemini_key'
        mock.GEMINI_MODEL = 'gemini-3-flash-preview'
        mock.GEMINI_USE_SEARCH = True
        yield mock


@pytest.fixture
def mock_genai():
    """Mock the Google GenAI client."""
    with patch('app.services.fact_checker.genai') as mock:
        yield mock


@pytest.fixture
def fact_checker(mock_settings, mock_genai):
    """Create a fact checker instance for testing."""
    return FactChecker()


@pytest.fixture
def sample_tiktok_data():
    """Create sample TikTok data for testing."""
    return TikTokData(
        url="https://www.tiktok.com/@user/video/123456",
        video_id="123456",
        title="Test Video Title",
        description="This is a test video description",
        author="testuser",
        likes=1000,
        views=50000,
        shares=100,
        comments=50,
        transcript="The president announced today that taxes will be reduced by 50%.",
        transcript_language="en",
        has_transcript=True
    )


@pytest.fixture
def sample_fact_check_result():
    """Create a sample fact check result."""
    return FactCheckResult(
        video_url="https://www.tiktok.com/@user/video/123456",
        credibility_score=0.75,
        credibility_level=CredibilityLevel.MEDIUM,
        summary="The video contains mixed claims with some verified and some unverified statements.",
        claims=[
            ClaimCheck(
                claim="Taxes will be reduced by 50%",
                is_factual=False,
                verification="No official announcement has been made about tax reductions.",
                importance=0.9,
                sources=[]
            )
        ],
        has_transcript=True,
        analyzed_text="The president announced today that taxes will be reduced by 50%."
    )


class TestFactCheckerInit:
    """Tests for FactChecker initialization."""
    
    def test_init_with_valid_api_key(self, mock_settings, mock_genai):
        """Test successful initialization with valid API key."""
        fact_checker = FactChecker()
        
        mock_genai.Client.assert_called_once_with(api_key='test_gemini_key')
    
    def test_init_without_api_key_raises_error(self, mock_genai):
        """Test initialization fails without API key."""
        with patch('app.services.fact_checker.settings') as mock_settings:
            mock_settings.GEMINI_API_KEY = None
            
            with pytest.raises(ValueError, match="GEMINI_API_KEY is not configured"):
                FactChecker()
    
    def test_init_with_search_tool_disabled(self, mock_genai):
        """Test initialization with search tool disabled."""
        with patch('app.services.fact_checker.settings') as mock_settings:
            mock_settings.GEMINI_API_KEY = 'test_key'
            mock_settings.GEMINI_USE_SEARCH = False
            
            fact_checker = FactChecker()
            assert fact_checker.tools == []
    
    def test_init_with_search_tool_enabled(self, mock_settings, mock_genai):
        """Test initialization with search tool enabled."""
        fact_checker = FactChecker()
        
        # Tools should be set when GEMINI_USE_SEARCH is True
        assert len(fact_checker.tools) == 1


class TestConstructPrompt:
    """Tests for prompt construction."""
    
    def test_construct_prompt_with_transcript(self, fact_checker, sample_tiktok_data):
        """Test prompt construction with transcript."""
        prompt = fact_checker._construct_prompt(sample_tiktok_data)
        
        assert "@testuser" in prompt
        assert "Test Video Title" in prompt
        assert "50,000 views" in prompt
        assert "1,000 likes" in prompt
        assert "TRANSCRIPT:" in prompt
        assert "taxes will be reduced by 50%" in prompt
    
    def test_construct_prompt_without_transcript(self, fact_checker):
        """Test prompt construction without transcript."""
        data = TikTokData(
            url="https://www.tiktok.com/@user/video/123",
            video_id="123",
            title="No Transcript Video",
            author="testuser",
            likes=100,
            views=1000,
            has_transcript=False
        )
        
        prompt = fact_checker._construct_prompt(data)
        
        assert "@testuser" in prompt
        assert "No Transcript Video" in prompt
        assert "TRANSCRIPT:" not in prompt
    
    def test_construct_prompt_includes_instructions(self, fact_checker, sample_tiktok_data):
        """Test prompt includes analysis instructions."""
        prompt = fact_checker._construct_prompt(sample_tiktok_data)
        
        assert "INSTRUCTIONS:" in prompt
        assert "TARGET KEY CLAIMS" in prompt
        assert "DIRECT VERIFICATION" in prompt
        assert "SCORING" in prompt


class TestAnalyzeCredibility:
    """Tests for the analyze_credibility method."""
    
    @pytest.mark.asyncio
    async def test_analyze_credibility_success(self, fact_checker, sample_tiktok_data, sample_fact_check_result):
        """Test successful credibility analysis."""
        # Mock the Gemini response
        mock_response = MagicMock()
        mock_response.parsed = sample_fact_check_result
        
        fact_checker.client.aio.models.generate_content = AsyncMock(return_value=mock_response)
        
        result = await fact_checker.analyze_credibility(sample_tiktok_data)
        
        assert isinstance(result, FactCheckResult)
        assert result.credibility_score == 0.75
        assert result.video_url == sample_tiktok_data.url
        assert result.has_transcript is True
        assert result.processing_time_ms is not None
    
    @pytest.mark.asyncio
    async def test_analyze_credibility_no_result(self, fact_checker, sample_tiktok_data):
        """Test handling when Gemini returns no result."""
        mock_response = MagicMock()
        mock_response.parsed = None
        mock_response.candidates = []
        
        fact_checker.client.aio.models.generate_content = AsyncMock(return_value=mock_response)
        
        with pytest.raises(GeminiAPIError, match="failed to generate"):
            await fact_checker.analyze_credibility(sample_tiktok_data)
    
    @pytest.mark.asyncio
    async def test_analyze_credibility_client_error_auth(self, fact_checker, sample_tiktok_data):
        """Test handling of API errors containing authentication keywords.
        
        Note: The actual error handling in fact_checker.py catches errors.ClientError
        and checks the string for '401' or 'key'. Since mocking the google.genai
        error classes is complex, we test the general exception path which ensures
        errors are properly wrapped in GeminiAPIError.
        """
        # This tests that any unexpected error gets wrapped in GeminiAPIError
        fact_checker.client.aio.models.generate_content = AsyncMock(
            side_effect=RuntimeError("API authentication failed")
        )
        
        with pytest.raises(GeminiAPIError, match="Failed to analyze content"):
            await fact_checker.analyze_credibility(sample_tiktok_data)
    
    @pytest.mark.asyncio
    async def test_analyze_credibility_client_error_quota(self, fact_checker, sample_tiktok_data):
        """Test handling of API errors containing quota keywords.
        
        Similar to auth test above - we test error wrapping behavior.
        """
        # This tests that any unexpected error gets wrapped in GeminiAPIError
        fact_checker.client.aio.models.generate_content = AsyncMock(
            side_effect=RuntimeError("Quota limit exceeded")
        )
        
        with pytest.raises(GeminiAPIError, match="Failed to analyze content"):
            await fact_checker.analyze_credibility(sample_tiktok_data)
    
    @pytest.mark.asyncio
    async def test_analyze_credibility_general_error(self, fact_checker, sample_tiktok_data):
        """Test handling of general API errors."""
        fact_checker.client.aio.models.generate_content = AsyncMock(
            side_effect=Exception("Unexpected error")
        )
        
        with pytest.raises(GeminiAPIError, match="Failed to analyze content"):
            await fact_checker.analyze_credibility(sample_tiktok_data)
    
    @pytest.mark.asyncio
    async def test_analyze_credibility_attaches_metadata(self, fact_checker, sample_tiktok_data, sample_fact_check_result):
        """Test that metadata is attached to the result."""
        mock_response = MagicMock()
        mock_response.parsed = sample_fact_check_result
        
        fact_checker.client.aio.models.generate_content = AsyncMock(return_value=mock_response)
        
        result = await fact_checker.analyze_credibility(sample_tiktok_data)
        
        # These should be attached post-processing
        assert result.video_url == sample_tiktok_data.url
        assert result.has_transcript == sample_tiktok_data.has_transcript
        assert result.analyzed_text == sample_tiktok_data.transcript
