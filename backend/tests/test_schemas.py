"""
Unit tests for Pydantic schemas.
"""
import pytest
from pydantic import ValidationError

from app.schemas.tiktok import TikTokMetadata, TikTokTranscript, TikTokData
from app.schemas.result import (
    CredibilityLevel,
    ReliableSource,
    ClaimCheck,
    FactCheckResult,
    CheckRequest
)


class TestTikTokMetadata:
    """Tests for TikTokMetadata schema."""
    
    def test_create_with_all_fields(self):
        """Test creating metadata with all fields."""
        metadata = TikTokMetadata(
            title="Test Video",
            description="Test description",
            audio_url="https://audio.example.com/file.mp3",
            author="testuser",
            likes=1000,
            views=50000,
            shares=100,
            comments=50
        )
        
        assert metadata.title == "Test Video"
        assert metadata.author == "testuser"
        assert metadata.likes == 1000
    
    def test_create_with_optional_fields_none(self):
        """Test creating metadata with optional fields as None."""
        metadata = TikTokMetadata()
        
        assert metadata.title is None
        assert metadata.description is None
        assert metadata.author is None
        assert metadata.likes is None


class TestTikTokTranscript:
    """Tests for TikTokTranscript schema."""
    
    def test_create_with_text(self):
        """Test creating transcript with text."""
        transcript = TikTokTranscript(
            text="This is the transcript text.",
            language="en"
        )
        
        assert transcript.text == "This is the transcript text."
        assert transcript.language == "en"
    
    def test_create_empty_transcript(self):
        """Test creating empty transcript."""
        transcript = TikTokTranscript()
        
        assert transcript.text is None
        assert transcript.language is None


class TestTikTokData:
    """Tests for TikTokData schema."""
    
    def test_create_with_required_fields(self):
        """Test creating TikTokData with required fields."""
        data = TikTokData(url="https://www.tiktok.com/@user/video/123")
        
        assert data.url == "https://www.tiktok.com/@user/video/123"
        assert data.has_transcript is False
    
    def test_create_with_all_fields(self):
        """Test creating TikTokData with all fields."""
        data = TikTokData(
            url="https://www.tiktok.com/@user/video/123",
            video_id="123",
            title="Test Video",
            description="Test description",
            author="testuser",
            likes=1000,
            views=50000,
            shares=100,
            comments=50,
            transcript="This is the transcript",
            transcript_language="en",
            has_transcript=True
        )
        
        assert data.video_id == "123"
        assert data.title == "Test Video"
        assert data.has_transcript is True
        assert data.transcript == "This is the transcript"
    
    def test_url_is_required(self):
        """Test that URL is required."""
        with pytest.raises(ValidationError):
            TikTokData()


class TestCredibilityLevel:
    """Tests for CredibilityLevel enum."""
    
    def test_credibility_levels(self):
        """Test all credibility level values."""
        assert CredibilityLevel.HIGH == "high"
        assert CredibilityLevel.MEDIUM == "medium"
        assert CredibilityLevel.LOW == "low"
        assert CredibilityLevel.UNKNOWN == "unknown"


class TestReliableSource:
    """Tests for ReliableSource schema."""
    
    def test_create_reliable_source(self):
        """Test creating a reliable source."""
        source = ReliableSource(
            title="Tax Policy Changes Announced",
            source="Reuters"
        )
        
        assert source.title == "Tax Policy Changes Announced"
        assert source.source == "Reuters"
    
    def test_computed_url(self):
        """Test that URL is automatically computed."""
        source = ReliableSource(
            title="Breaking News: Market Update",
            source="AP News"
        )
        
        # URL should be a Google search URL
        assert "google.com/search" in source.url
        assert "Breaking" in source.url or "Breaking%20News" in source.url.replace("+", "%20")
        assert "btnI=1" in source.url  # I'm Feeling Lucky parameter
    
    def test_title_is_required(self):
        """Test that title is required."""
        with pytest.raises(ValidationError):
            ReliableSource(source="Reuters")
    
    def test_source_is_required(self):
        """Test that source is required."""
        with pytest.raises(ValidationError):
            ReliableSource(title="Article Title")


class TestClaimCheck:
    """Tests for ClaimCheck schema."""
    
    def test_create_claim_check(self):
        """Test creating a claim check."""
        claim = ClaimCheck(
            claim="The economy grew by 5%",
            is_factual=True,
            verification="Verified by official statistics.",
            importance=0.8,
            sources=[
                ReliableSource(title="GDP Report Q4", source="Bureau of Economics")
            ]
        )
        
        assert claim.claim == "The economy grew by 5%"
        assert claim.is_factual is True
        assert claim.importance == 0.8
        assert len(claim.sources) == 1
    
    def test_importance_validation(self):
        """Test that importance must be between 0 and 1."""
        with pytest.raises(ValidationError):
            ClaimCheck(
                claim="Test claim",
                verification="Test verification",
                importance=1.5  # Invalid - must be <= 1.0
            )
    
    def test_is_factual_optional(self):
        """Test that is_factual can be None."""
        claim = ClaimCheck(
            claim="Unclear claim",
            verification="Cannot be verified",
            importance=0.5
        )
        
        assert claim.is_factual is None
    
    def test_empty_sources_by_default(self):
        """Test that sources default to empty list."""
        claim = ClaimCheck(
            claim="Test claim",
            verification="Test verification",
            importance=0.5
        )
        
        assert claim.sources == []


class TestFactCheckResult:
    """Tests for FactCheckResult schema."""
    
    def test_create_fact_check_result(self):
        """Test creating a fact check result."""
        result = FactCheckResult(
            video_url="https://www.tiktok.com/@user/video/123",
            credibility_score=0.75,
            credibility_level=CredibilityLevel.MEDIUM,
            summary="Mixed credibility",
            claims=[],
            has_transcript=True,
            analyzed_text="Sample text",
            processing_time_ms=1500
        )
        
        assert result.credibility_score == 0.75
        assert result.credibility_level == CredibilityLevel.MEDIUM
        assert result.has_transcript is True
    
    def test_credibility_score_validation(self):
        """Test that credibility score must be between 0 and 1."""
        with pytest.raises(ValidationError):
            FactCheckResult(
                video_url="https://www.tiktok.com/@user/video/123",
                credibility_score=1.5,  # Invalid
                credibility_level=CredibilityLevel.HIGH,
                has_transcript=False
            )
    
    def test_negative_credibility_score_validation(self):
        """Test that negative credibility scores are invalid (except -1 for timeout)."""
        # Note: The schema allows >= 0 normally, but the API uses -1 for timeout
        # This test documents expected validation behavior
        with pytest.raises(ValidationError):
            FactCheckResult(
                video_url="https://www.tiktok.com/@user/video/123",
                credibility_score=-2.0,  # Invalid
                credibility_level=CredibilityLevel.UNKNOWN,
                has_transcript=False
            )


class TestCheckRequest:
    """Tests for CheckRequest schema."""
    
    def test_create_check_request(self):
        """Test creating a check request."""
        request = CheckRequest(url="https://www.tiktok.com/@user/video/123")
        
        assert request.url == "https://www.tiktok.com/@user/video/123"
    
    def test_url_is_required(self):
        """Test that URL is required."""
        with pytest.raises(ValidationError):
            CheckRequest()
    
    def test_empty_url_is_invalid(self):
        """Test that empty URL is invalid."""
        with pytest.raises(ValidationError):
            CheckRequest(url="")
