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
from app.services.fact_checker import fact_checker
from app.services.exceptions import (
    InvalidTikTokURLError,
    SupadataAuthError,
    SupadataCreditsExhausted,
    SupadataAPIError,
    GeminiAPIError,
    GeminiAuthError,
    GeminiRateLimitError,
    GeminiQuotaExceededError,
    SupadataAPIError
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/scrape-metadata", response_model=TikTokData, status_code=status.HTTP_200_OK)
async def scrape_metadata(request: CheckRequest) -> TikTokData:
    """
    Step 1: Scrape only the metadata (author, title, transcript, etc.) from a TikTok URL.
    """
    try:
        logger.info(f"Scraping metadata for URL: {request.url}")
        tiktok_data: TikTokData = await fetch_tiktok_data(request.url)
        return tiktok_data
    except InvalidTikTokURLError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except (SupadataAuthError, SupadataAPIError, SupadataCreditsExhausted) as e:
        status_code = getattr(e, 'status_code', 500)
        raise HTTPException(status_code=status_code, detail=str(e))
    except Exception as e:
        logger.error(f"Error scraping metadata: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.post("/fact-check", response_model=FactCheckResult, status_code=status.HTTP_200_OK)
async def fact_check(tiktok_data: TikTokData) -> FactCheckResult:
    """
    Step 2: Perform fact-check on pre-scraped TikTok data.
    """
    try:
        logger.info(f"Starting fact-check analysis for: {tiktok_data.video_id}")
        fact_check_result: FactCheckResult = await fact_checker.analyze_credibility(tiktok_data)
        return fact_check_result
    except (GeminiAuthError, GeminiQuotaExceededError, GeminiRateLimitError, GeminiAPIError) as e:
        status_code = 503 if isinstance(e, GeminiAPIError) else 429 if isinstance(e, GeminiRateLimitError) else 500
        raise HTTPException(status_code=status_code, detail=str(e))
    except Exception as e:
        logger.error(f"Error in fact-check: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.post("/check", response_model=FactCheckResult, status_code=status.HTTP_200_OK)
async def check_video(request: CheckRequest) -> FactCheckResult:
    """
    Check the credibility of a TikTok video.
    
    This endpoint:
    1. Fetches video metadata and transcript from Supadata
    2. Analyzes the content using Gemini LLM
    3. Returns a credibility score and assessment
    """
    start_time = time.time()
    
    try:
        # Step 1: Fetch TikTok data (metadata + transcript)
        logger.info(f"Processing check request for URL: {request.url}")
        tiktok_data: TikTokData = await fetch_tiktok_data(request.url)
        
        # Step 2: Analyze the content using Gemini
        logger.info(f"Starting fact-check analysis for: {tiktok_data.video_id}")
        fact_check_result: FactCheckResult = await fact_checker.analyze_credibility(tiktok_data)
        
        return fact_check_result
        
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
