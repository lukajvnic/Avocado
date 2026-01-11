// TikTok Fact Checker - Background Service Worker

// Listen for messages from content script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'CHECK_VIDEO') {
        handleFactCheck(message.url)
            .then(response => sendResponse({ success: true, data: response }))
            .catch(error => sendResponse({ success: false, error: error.message }));

        return true; // Keep the message channel open for async response
    }
});

const API_BASE_URL = "http://localhost:8000/api/v1";

async function handleFactCheck(tiktokUrl) {
    try {
        console.log('[Background] Checking URL:', tiktokUrl);

        const response = await fetch(`${API_BASE_URL}/check`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url: tiktokUrl }),
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log('[Background] Success:', data);
        return data;

    } catch (error) {
        console.error('[Background] Error:', error);
        throw error;
    }
}
