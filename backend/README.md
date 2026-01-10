# Avocado TikTok Fact Checker - Backend

FastAPI backend service for analyzing TikTok video credibility using Supadata API and Google Gemini via OpenRouter.

## Features

- ✅ **Async TikTok Data Scraping**: Parallel fetching of metadata and transcripts
- ✅ **Supadata API Integration**: Native support for TikTok video analysis
- ✅ **Gemini AI via OpenRouter**: AI-powered credibility analysis with flexible model selection
- ✅ **URL Handling**: Automatic resolution of shortened TikTok URLs
- ✅ **Error Handling**: Comprehensive error handling with custom exceptions
- ✅ **Pydantic Validation**: Type-safe data models for all requests/responses
- ✅ **Caching & Retry Logic**: Built-in caching and exponential backoff for API calls
- ✅ **Multi-Model Support**: Easy switching between AI models via OpenRouter

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── deps.py          # API dependencies
│   │   └── v1/
│   │       └── check.py     # Main /check endpoint
│   ├── core/
│   │   └── config.py        # Configuration management
│   ├── schemas/
│   │   ├── tiktok.py        # TikTok data models
│   │   └── result.py        # API response models
│   ├── services/
│   │   ├── scraper.py       # Supadata API integration ✅
│   │   ├── exceptions.py    # Custom exceptions
│   │   └── fact_checker.py  # Gemini AI fact-checking ✅
│   ├── utils/
│   │   └── url_utils.py     # URL cleaning & validation
│   └── main.py              # FastAPI application
├── tests/
├── .env.example
├── .gitignore
└── requirements.txt
```

## Installation

### 1. Create Virtual Environment

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Create a `.env` file in the `backend` directory:

```env
# Required API Keys
SUPADATA_API_KEY=your_supadata_api_key_here
OPENROUTER_API_KEY=sk-or-v1-your_key_here

# Optional: Model Configuration
OPENROUTER_MODEL=google/gemini-flash-1.5
OPENROUTER_TEMPERATURE=0.3
OPENROUTER_MAX_TOKENS=2048
```

**Get your API keys:**
- **Supadata**: https://supadata.ai/
- **OpenRouter**: https://openrouter.ai/keys (add credits at https://openrouter.ai/credits)

## Running the Server

### Test Your Setup (Recommended First Step)

```bash
python test_api_setup.py
```

This will verify that both Supadata and Gemini API keys are configured correctly.

### Development Mode

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Documentation

Once running, access:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### POST /api/v1/check

Check the credibility of a TikTok video.

**Request:**
```json
{
  "url": "https://www.tiktok.com/@username/video/1234567890"
}
```

**Response:**
```json
{
  "video_url": "https://www.tiktok.com/@username/video/1234567890",
  "credibility_score": 0.75,
  "credibility_level": "medium",
  "summary": "The video makes verifiable claims about health benefits but lacks cited sources. Some sensational language is used to attract attention.",
  "concerns": [
    "No credible sources cited for health claims",
    "Use of sensational language",
    "Potential confirmation bias in presentation"
  ],
  "strengths": [
    "Video has native captions/transcript",
    "High engagement: 500,000 views",
    "Creator mentions personal experience"
  ],
  "has_transcript": true,
  "analyzed_text": "Full transcript text...",
  "processing_time_ms": 2500
}
```

**Credibility Levels:**
- `high` (0.8-1.0): Well-sourced, factual, minimal concerns
- `medium` (0.5-0.79): Some concerns but not clearly misleading  
- `low` (0.0-0.49): Significant misinformation or misleading claims
- `unknown`: Cannot assess due to insufficient content

### GET /api/v1/health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "avocado-fact-checker"
}
```

## Implementation Details

### Scraper Service (`services/scraper.py`)

The scraper service implements the core TikTok data fetching logic:

1. **URL Validation**: Cleans and validates TikTok URLs
2. **Short URL Resolution**: Follows redirects for `vm.tiktok.com` links
3. **Parallel Fetching**: Uses `asyncio.gather()` to fetch metadata and transcript simultaneously
4. **Caching**: TTL-based caching (1 hour default) to reduce API calls
5. **Retry Logic**: Exponential backoff for rate limit errors
6. **Error Handling**: Distinguishes between different API errors (401, 402, 404, 429, etc.)

### Fact Checker Service (`services/fact_checker.py`)

The fact checker uses Google's Gemini via OpenRouter to analyze video credibility:

1. **Prompt Construction**: Creates detailed prompts with video metadata and transcript
2. **OpenRouter API**: Uses OpenRouter for flexible model access (Gemini, Claude, GPT-4, etc.)
3. **Structured Output**: Parses AI responses into standardized JSON format
4. **Scoring**: Calculates credibility scores (0.0-1.0) and categorical levels
5. **Multi-Model Support**: Easy switching between different AI models

**Analysis Criteria:**
- Content accuracy and verifiable claims
- Source reliability indicators
- Red flags (sensationalism, conspiracy theories)
- Context and balanced presentation
- Engagement patterns

### Error Handling

Custom exceptions for different failure scenarios:

**Supadata API:**
- `InvalidTikTokURLError`: Malformed URLs
- `SupadataAuthError`: Invalid API key (401)
- `SupadataCreditsExhausted`: Out of API credits (402)
- `SupadataAPIError`: General API failures (429, 5xx)

**Gemini API:**
- `GeminiAuthError`: Invalid API key
- `GeminiQuotaExceededError`: Quota exhausted
- `GeminiRateLimitError`: Rate limit exceeded
- `GeminiAPIError`: General API failures

### Configuration

All settings managed via Pydantic Settings in `core/config.py`:
- API keys loaded from environment
- Configurable timeouts and retry logic
- CORS settings for browser extension support

## Testing

Run tests with pytest:

```bash
pytest tests/
```

## Development Checklist

- [x] Backend folder structure created
- [x] httpx installed and used for all API calls
- [x] Service returns audio_url as fallback when transcript is null
- [x] No hardcoded strings; all URLs and keys in config.py or .env
- [x] Parallel execution with asyncio.gather
- [x] Short link resolution implemented
- [x] Pydantic schema integration
- [x] Comprehensive error handling
- [x] Caching with TTL (1 hour)
- [x] Retry logic with exponential backoff
- [x] Gemini AI integration for fact-checking
- [x] Structured credibility scoring
- [ ] Unit tests for fact checker service
- [ ] Integration tests for API endpoints
- [ ] Rate limiting middleware

## Next Steps

1. **Testing**: Write comprehensive test suite for scraper and fact checker
2. **Rate Limiting**: Implement request rate limiting middleware
3. **Authentication**: Add API key authentication for Chrome extension
4. **Monitoring**: Add logging and metrics collection (Sentry, DataDog, etc.)
5. **Optimization**: Fine-tune Gemini prompts for better accuracy
6. **Caching**: Consider Redis for distributed caching in production

## Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `SUPADATA_API_KEY` | Your Supadata API key | Yes | - |
| `OPENROUTER_API_KEY` | Your OpenRouter API key | Yes | - |
| `OPENROUTER_MODEL` | Model to use (e.g., `google/gemini-flash-1.5`) | No | `google/gemini-flash-1.5` |
| `OPENROUTER_TEMPERATURE` | AI response temperature (0.0-1.0) | No | `0.3` |
| `OPENROUTER_MAX_TOKENS` | Max tokens in AI response | No | `2048` |
| `OPENROUTER_SITE_URL` | Your site URL (for OpenRouter tracking) | No | `None` |
| `OPENROUTER_SITE_NAME` | Your site name | No | `Avocado TikTok Fact Checker` |
| `DEBUG` | Enable debug mode | No | `False` |
| `REQUEST_TIMEOUT` | API request timeout (seconds) | No | `30` |
| `MAX_RETRIES` | Max retry attempts for rate limits | No | `3` |
| `RETRY_DELAY` | Initial retry delay (seconds) | No | `2.0` |
| `RETRY_BACKOFF` | Exponential backoff multiplier | No | `2.0` |
| `CACHE_TTL` | Cache time-to-live (seconds) | No | `3600` |
| `CACHE_MAX_SIZE` | Max cached items | No | `1000` |
| `CORS_ORIGINS` | Allowed CORS origins | No | `["*"]` |

## License

MIT

## Support

For issues or questions, please open an issue on GitHub.