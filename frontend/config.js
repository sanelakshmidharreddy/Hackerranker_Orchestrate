/**
 * Ghost Data Still Exists — Frontend Configuration
 * Resolves the backend API base URL from multiple flexible sources:
 * 1. window.BACKEND_URL (e.g. injected or declared in index.html)
 * 2. URL Query parameter (?api=https://... or ?backend=https://...)
 * 3. LocalStorage persistence (allows one-time configuration in browser)
 * 4. Localhost default (http://localhost:8000)
 */

(function() {
  const urlParams = new URLSearchParams(window.location.search);
  const paramApi = urlParams.get("api") || urlParams.get("backend");
  if (paramApi) {
    try {
      localStorage.setItem("GHOST_DATA_API_BASE", paramApi.replace(/\/$/, ""));
    } catch (e) {}
  }

  const storedApi = (function() {
    try {
      return localStorage.getItem("GHOST_DATA_API_BASE");
    } catch (e) {
      return null;
    }
  })();

  const defaultLocal = (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1")
    ? "http://localhost:8000"
    : "";

  window.API_BASE = window.BACKEND_URL || paramApi || storedApi || window.API_BASE || defaultLocal;
})();
