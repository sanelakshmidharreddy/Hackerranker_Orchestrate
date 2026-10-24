/**
 * Ghost Data Still Exists — Frontend Configuration
 * Connects to Render backend in production and localhost:8000 in development.
 */

(function() {
  const PRODUCTION_BACKEND_URL = "https://hackerranker-orchestrate.onrender.com";
  const LOCAL_BACKEND_URL = "http://localhost:8000";

  const isLocal = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";

  // Check URL query param override if explicitly provided for testing
  const urlParams = new URLSearchParams(window.location.search);
  const paramApi = urlParams.get("api") || urlParams.get("backend");

  // In production (e.g. Vercel), default directly to PRODUCTION_BACKEND_URL
  const defaultUrl = isLocal ? LOCAL_BACKEND_URL : PRODUCTION_BACKEND_URL;

  window.API_BASE = (paramApi || window.BACKEND_URL || defaultUrl).replace(/\/$/, "");
  console.log("[Ghost Data] Connected API Base:", window.API_BASE);
})();
