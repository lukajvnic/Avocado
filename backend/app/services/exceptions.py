"""
Custom exceptions for the application.
"""


class SupadataAPIError(Exception):
    """Raised when Supadata API returns an error."""
    
    def __init__(self, message: str, status_code: int = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class SupadataAuthError(SupadataAPIError):
    """Raised when API key is invalid or unauthorized."""
    
    def __init__(self, message: str = "Invalid or missing Supadata API key"):
        super().__init__(message, status_code=401)


class SupadataCreditsExhausted(SupadataAPIError):
    """Raised when Supadata API credits are exhausted."""
    
    def __init__(self, message: str = "Supadata API credits exhausted"):
        super().__init__(message, status_code=402)


class InvalidTikTokURLError(Exception):
    """Raised when the provided URL is not a valid TikTok URL."""
    
    def __init__(self, url: str):
        self.url = url
        super().__init__(f"Invalid TikTok URL: {url}")


class TranscriptNotAvailableError(Exception):
    """Raised when no transcript is available for a video (not an error, expected behavior)."""
    pass
<<<<<<< HEAD


class GeminiAPIError(Exception):
    """Raised when Gemini API returns an error."""
    
    def __init__(self, message: str, original_error: Exception = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)


class GeminiAuthError(GeminiAPIError):
    """Raised when Gemini API key is invalid or unauthorized."""
    
    def __init__(self, message: str = "Invalid or missing Gemini API key", original_error: Exception = None):
        super().__init__(message, original_error)


class GeminiRateLimitError(GeminiAPIError):
    """Raised when Gemini API rate limit is exceeded."""
    
    def __init__(self, message: str = "Gemini API rate limit exceeded", original_error: Exception = None):
        super().__init__(message, original_error)


class GeminiQuotaExceededError(GeminiAPIError):
    """Raised when Gemini API quota is exceeded."""
    
    def __init__(self, message: str = "Gemini API quota exceeded", original_error: Exception = None):
        super().__init__(message, original_error)
=======
>>>>>>> e3a170794cde3694b6b37418dc29f8e715387011
