"""
Main check endpoint for TikTok video fact checking.
"""
from fastapi import APIRouter, HTTPException, status
from typing import Dict
import time
import logging

from app.schemas.result import CheckRequest, FactCheckResult, CredibilityLevel
from app.schemas.tiktok import TikTokData
from app.services.scraper import fetch_tiktok_data
<<<<<<< HEAD
from app.services.fact_checker import fact_checker
=======
>>>>>>> e3a170794cde3694b6b37418dc29f8e715387011
from app.services.exceptions import (
    InvalidTikTokURLError,
    SupadataAuthError,
    SupadataCreditsExhausted,
<<<<<<< HEAD
    SupadataAPIError,
    GeminiAPIError,
    GeminiAuthError,
    GeminiRateLimitError,
    GeminiQuotaExceededError
=======
    SupadataAPIError
>>>>>>> e3a170794cde3694b6b37418dc29f8e715387011
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/check", response_model=FactCheckResult, status_code=status.HTTP_200_OK)
async def check_video(request: CheckRequest) -> FactCheckResult:
    """
    Check the credibility of a TikTok video.
    
    This endpoint:
    1. Fetches video metadata and transcript from Supadata
    2. (Future) Analyzes the content using LLM
    3. Returns a credibility score and assessment
    
    Currently implements Step 1 (data fetching) only.
    """
    start_time = time.time()
    
    try:
        # Step 1: Fetch TikTok data (metadata + transcript)
        logger.info(f"Processing check request for URL: {request.url}")
        tiktok_data: TikTokData = await fetch_tiktok_data(request.url)
        
<<<<<<< HEAD
        # Step 2: Analyze the content using Gemini
        logger.info(f"Starting fact-check analysis for: {tiktok_data.video_id}")
        fact_check_result: FactCheckResult = await fact_checker.analyze_credibility(tiktok_data)
        
        return fact_check_result
=======
        # Step 2: Analyze the data (PLACEHOLDER - Future implementation)
        # This is where you'll integrate the LLM fact-checking logic
        # For now, return a basic response with the scraped data
        
        # Placeholder credibility assessment
        credibility_score = 0.5  # Neutral score
        credibility_level = CredibilityLevel.UNKNOWN
        
        # Determine what text we have to work with
        analyzed_text = None
        concerns = []
        strengths = []
        
        if tiktok_data.has_transcript:
            analyzed_text = tiktok_data.transcript
            strengths.append("Video has native captions/transcript")
        else:
            concerns.append("No native transcript available")
            if tiktok_data.audio_url:
                strengths.append("Audio URL available for transcription")
        
        # Additional metadata-based indicators
        if tiktok_data.views and tiktok_data.views > 100000:
            strengths.append(f"High engagement: {tiktok_data.views:,} views")
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return FactCheckResult(
            video_url=tiktok_data.url,
            credibility_score=credibility_score,
            credibility_level=credibility_level,
            summary="Data successfully fetched. Full fact-checking analysis pending implementation.",
            concerns=concerns,
            strengths=strengths,
            has_transcript=tiktok_data.has_transcript,
            analyzed_text=analyzed_text,
            processing_time_ms=processing_time
        )
>>>>>>> e3a170794cde3694b6b37418dc29f8e715387011
        
    except InvalidTikTokURLError as e:
        logger.warning(f"Invalid TikTok URL: {request.url}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid TikTok URL: {str(e)}"
        )
    
    except SupadataAuthError as e:
        logger.error("Supadata authentication failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API authentication failed. Please check server configuration."
        )
    
    except SupadataCreditsExhausted as e:
        logger.error("Supadata API credits exhausted")
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="API credits exhausted. Please contact administrator."
        )
    
    except SupadataAPIError as e:
        logger.error(f"Supadata API error: {e}")
        
        # Special handling for rate limit errors
        if e.status_code == 429:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    "Rate limit exceeded. The video data has been cached and will be served "
                    "from cache for the next hour. If this persists, consider upgrading your "
                    "Supadata plan at https://supadata.ai/pricing"
                )
            )
        
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"External API error: {str(e)}"
        )
    
<<<<<<< HEAD
    except GeminiAuthError as e:
        logger.error("Gemini API authentication failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI service authentication failed. Please check server configuration."
        )
    
    except GeminiQuotaExceededError as e:
        logger.error("Gemini API quota exceeded")
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="AI service quota exceeded. Please contact administrator."
        )
    
    except GeminiRateLimitError as e:
        logger.error("Gemini API rate limit exceeded")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="AI service rate limit exceeded. Please try again in a few moments."
        )
    
    except GeminiAPIError as e:
        logger.error(f"Gemini API error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI service error: {str(e)}"
        )
    
=======
>>>>>>> e3a170794cde3694b6b37418dc29f8e715387011
    except Exception as e:
        logger.error(f"Unexpected error in check_video: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing your request."
        )


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> Dict[str, str]:
    """Simple health check endpoint."""
    return {
        "status": "healthy",
        "service": "avocado-fact-checker"
    }
