/**
 * Ghost Data Still Exists — Frontend Configuration
 * Update API_BASE to your deployed Render backend URL when hosted.
 */
window.API_BASE = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
    ? "http://localhost:8000"
    : ""; // When hosted, relative path or backend URL
