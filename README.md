# 🥑 Avocado - TikTok Fact Checker

> **Fight misinformation on TikTok with AI-powered analysis.**

**Avocado** is an open-source tool that helps users verify the credibility of TikTok videos in real-time. It combines a Chrome Extension for seamless UI integration with a robust FastAPI backend that leverages Google Gemini for content analysis.

## ✨ Features

-   **Real-time Analysis**: Instantly analyzes video transcripts and metadata.
-   **AI-Powered Fact Checking**: Uses **Google Gemini** (via OpenRouter) to cross-reference claims with trusted sources.
-   **Seamless Integration**: Injects a non-intrusive "Fact Check" button directly into the TikTok interface.
-   **Detailed Reports**: Provides a credibility score, summary of claims, and specific concerns (e.g., lack of sources, sensationalism).
-   **Robust Backend**: Built with **FastAPI**, featuring caching, rate limiting, and parallel data fetching.

## 🏗️ Architecture

The project consists of two main components:

### 1. Backend (`/backend`)
A Python **FastAPI** service that acts as the brain of the operation.
-   **Scraper**: Fetches video metadata and transcripts using the **Supadata API**.
-   **Analyzer**: Processes content using LLMs (default: Gemini Flash 1.5) via **OpenRouter**.
-   **API**: Exposes REST endpoints (`/api/v1/check`) for the extension to consume.

### 2. Extension (`/extension`)
A **Manifest V3** Chrome extension that provides the user interface.
-   **Content Script**: Detects TikTok videos and injects the "Avocado" button.
-   **Side Panel**: Displays the analysis results in a slide-out drawer.
-   **Note**: The extension is currently configured to use mock data for demonstration purposes.

## 🚀 Getting Started

### Prerequisites

-   Python 3.10 or higher
-   Google Chrome (or Chromium-based browser)
-   **API Keys**:
    -   [Supadata](https://supadata.ai/) (for TikTok scraping)
    -   [OpenRouter](https://openrouter.ai/) (for LLM access)

### 1️⃣ Backend Setup

1.  **Navigate to the backend directory:**
    ```bash
    cd backend
    ```

2.  **Set up a virtual environment:**
    ```bash
    python -m venv venv
    
    # Windows
    venv\Scripts\activate
    
    # macOS/Linux
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables:**
    Create a `.env` file in the `backend` directory based on `.env.example`:
    ```ini
    # backend/.env
    SUPADATA_API_KEY=your_supadata_key
    OPENROUTER_API_KEY=your_openrouter_key
    
    # Optional settings
    OPENROUTER_MODEL=google/gemini-flash-1.5
    DEBUG=True
    ```

5.  **Run the Server:**
    ```bash
    uvicorn app.main:app --reload
    ```
    The API will be live at `http://localhost:8000`. You can view the docs at `http://localhost:8000/docs`.

### 2️⃣ Extension Setup

1.  Open Chrome and navigate to `chrome://extensions/`.
2.  Enable **Developer mode** in the top-right corner.
3.  Click **Load unpacked**.
4.  Select the `extension` folder from this repository.
5.  Go to TikTok.com, and you should see the Avocado button on video pages!

## 🔌 API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/check` | Full analysis: scrapes data and performs fact-check. |
| `POST` | `/api/v1/fact-check` | Performs fact-check on already scraped data. |
| `POST` | `/api/v1/scrape-metadata` | Scrapes metadata/transcript only. |
| `GET` | `/health` | Service health check. |

## 🛠️ Development

-   **Testing**: Run the test suite with `pytest`.
    ```bash
    cd backend
    pytest tests/
    ```
-   **Linting**: use `black` and `flake8` to maintain code quality.
