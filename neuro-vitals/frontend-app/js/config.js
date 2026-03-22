const CONFIG = {
    // Replace the URL below with your Render/Railway backend URL after deployment
    API_BASE_URL: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
        ? 'http://localhost:8000'
        : 'https://neuro-vitals-api.onrender.com' // Edit this after Step 1
};

// Export for use in other scripts if needed, though most use global CONFIG
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CONFIG;
}
