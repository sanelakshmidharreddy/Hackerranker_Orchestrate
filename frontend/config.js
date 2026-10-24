/**
 * Ghost Data Still Exists — Frontend Configuration
 * Connects to Render backend in production and localhost:8000 in development.
 */

(function() {
  const PRODUCTION_BACKEND_URL = "https://hackerranker-orchestrate.onrender.com";
  const LOCAL_BACKEND_URL = "http://localhost:8000";

  const isLocal = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";
  const defaultBase = isLocal ? LOCAL_BACKEND_URL : PRODUCTION_BACKEND_URL;

  const urlParams = new URLSearchParams(window.location.search);
  const paramApi = urlParams.get("api") || urlParams.get("backend");
  if (paramApi) {
    try {
      localStorage.setItem("GHOST_DATA_API_BASE", paramApi.replace(/\/$/, ""));
    } catch (e) {}
  }

  const storedApi = (function() {
    try {
      const val = localStorage.getItem("GHOST_DATA_API_BASE");
      return (val && val.trim()) ? val.trim() : null;
    } catch (e) {
      return null;
    }
  })();

  // Use explicit environment/param/stored override if present, otherwise automatic environment default
  window.API_BASE = (window.BACKEND_URL || paramApi || storedApi || window.API_BASE || defaultBase).replace(/\/$/, "");
})();
