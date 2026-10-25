/**
 * Ghost Data Still Exists — Frontend Logic
 * Connects to backend API and renders metrics, case lists, and forensic audit details.
 */

function getApiBase() {
  const isLocal = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";
  const defaultUrl = isLocal ? "http://localhost:8000" : "https://hackerranker-orchestrate.onrender.com";

  // Support environment variables (Next.js, Vite, etc.), global overrides, and local storage
  const envApi = (typeof process !== "undefined" && process.env && (process.env.NEXT_PUBLIC_API_URL || process.env.VITE_API_URL))
    || window.NEXT_PUBLIC_API_URL
    || window.VITE_API_URL
    || window.API_BASE
    || window.BACKEND_URL
    || localStorage.getItem("GHOST_DATA_API_BASE");

  return (envApi || defaultUrl).replace(/\/$/, "");
}

let currentStatusFilter = "ALL";
let currentSearchQuery = "";
let allCasesCache = [];

// ── Cold-start / retry state ─────────────────────────────────────────────────
const FETCH_TIMEOUT_MS   = 20_000;  // 20 s per request
const RETRY_INTERVAL_MS  = 5_000;   // retry every 5 s
const RETRY_DEADLINE_MS  = 90_000;  // give up after 90 s total

/**
 * Fetch with an AbortController timeout and automatic cold-start retries.
 * Shows a "Waking up…" banner in #coldStartBanner while retrying.
 * After RETRY_DEADLINE_MS, shows a permanent error with a Retry button.
 *
 * @param {string} url
 * @returns {Promise<Response>}
 */
async function fetchWithRetry(url) {
  const started = Date.now();
  let attempt = 0;

  while (true) {
    attempt++;
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);

    try {
      const res = await fetch(url, { signal: controller.signal });
      clearTimeout(timer);
      hideColdStartBanner();
      hideApiError();
      return res;
    } catch (err) {
      clearTimeout(timer);
      const elapsed = Date.now() - started;

      if (elapsed >= RETRY_DEADLINE_MS) {
        hideColdStartBanner();
        const apiBase = getApiBase();
        showApiError(`Failed to reach the audit server after 90s (${err.name === "AbortError" ? "Request Timeout" : err.message}).`, apiBase);
        throw new Error(`TIMEOUT_FINAL:${url}`);
      }

      // Show / update the waking-up banner
      showColdStartBanner(elapsed);
      // Wait for the retry interval before next attempt
      await new Promise(resolve => setTimeout(resolve, RETRY_INTERVAL_MS));
    }
  }
}

function showColdStartBanner(elapsedMs) {
  let banner = document.getElementById("coldStartBanner");
  if (!banner) {
    banner = document.createElement("div");
    banner.id = "coldStartBanner";
    banner.style.cssText = [
      "position:fixed","top:0","left:0","right:0","z-index:9999",
      "background:#7c3aed","color:#fff","text-align:center",
      "padding:10px 16px","font-size:0.9rem","font-family:inherit"
    ].join(";");
    document.body.prepend(banner);
  }
  const secs = Math.round(elapsedMs / 1000);
  banner.textContent =
    `⏳ Waking up the audit server (up to 60s)… ${secs}s elapsed. Please wait.`;
}

function hideColdStartBanner() {
  const banner = document.getElementById("coldStartBanner");
  if (banner) banner.remove();
}

function showApiError(msg, url) {
  const banner = document.getElementById("apiErrorBanner");
  if (banner) {
    banner.style.display = "block";
    banner.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center; gap:16px;">
        <div>
          <strong style="color:#fb7185;">⚠️ Backend Connection Failed:</strong> ${escapeHtml(msg)}<br>
          <span style="font-size:0.85rem; color:var(--text-muted);">Backend Target URL: <code>${escapeHtml(url || getApiBase())}</code></span>
        </div>
        <button onclick="window.location.reload()" style="background:#e11d48; color:#fff; border:none; padding:8px 16px; border-radius:6px; cursor:pointer; font-weight:600;">
          ↺ Retry
        </button>
      </div>
    `;
  }
}

function hideApiError() {
  const banner = document.getElementById("apiErrorBanner");
  if (banner) banner.style.display = "none";
}

// ── Field Normalization & Robust Getters ──────────────────────────────────────

function getSubjectEmail(c) {
  return c.subject_email || c.email || "";
}

function getWorkflowClaim(c) {
  const val = c.workflow_claim || c.reported_status;
  if (!val) {
    console.warn(`[Ghost Data] workflow_claim missing for case: ${c.case_id}`);
    return "UNKNOWN";
  }
  return val.toString().trim().toUpperCase();
}

function getAuditedState(c) {
  let val = c.audited_true_state || c.deletion_status;
  if (!val) {
    console.warn(`[Ghost Data] audited_true_state missing for case: ${c.case_id}`);
    return "UNKNOWN";
  }
  val = val.toString().trim().toUpperCase();

  // Logic Sanity: Cases with workflow_claim NOT_STARTED should never be COMPLETE.
  const claim = getWorkflowClaim(c);
  if (claim === "NOT_STARTED" && val === "COMPLETE") {
    val = "INCOMPLETE";
  }
  return val;
}

function getFindingsCount(c) {
  if (Array.isArray(c.findings)) {
    return c.findings.length;
  }
  if (typeof c.findings_count === "number") {
    return c.findings_count;
  }
  if (typeof c.n_findings === "number") {
    return c.n_findings;
  }
  console.warn(`[Ghost Data] findings_count missing for case: ${c.case_id}`);
  return 0;
}

function getAuditCutoff(c) {
  return c.audit_cutoff || c.audit_at || "";
}

// ── Lifecycle & Setup ────────────────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", () => {
  fetchSummary();
  fetchCases();
  setupEventListeners();
});

function setupEventListeners() {
  // Search input with debounce
  const searchInput = document.getElementById("searchInput");
  let debounceTimeout = null;
  searchInput.addEventListener("input", (e) => {
    clearTimeout(debounceTimeout);
    debounceTimeout = setTimeout(() => {
      currentSearchQuery = e.target.value.trim();
      renderCasesTable();
    }, 200);
  });

  // Filter tabs
  const filterTabs = document.getElementById("filterTabs");
  filterTabs.addEventListener("click", (e) => {
    if (e.target.classList.contains("tab-btn")) {
      document.querySelectorAll(".tab-btn").forEach(btn => btn.classList.remove("active"));
      e.target.classList.add("active");
      currentStatusFilter = e.target.dataset.status.toUpperCase();
      renderCasesTable();
    }
  });

  // Drawer close events
  const closeBtn = document.getElementById("drawerCloseBtn");
  const backdrop = document.getElementById("drawerBackdrop");
  closeBtn.addEventListener("click", closeDrawer);
  backdrop.addEventListener("click", (e) => {
    if (e.target === backdrop) closeDrawer();
  });

  // Escape key to close drawer
  window.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeDrawer();
  });

  // Config backend URL prompt
  const btnConfigApi = document.getElementById("btnConfigApi");
  if (btnConfigApi) {
    btnConfigApi.addEventListener("click", () => {
      const current = window.API_BASE || getApiBase();
      const updated = prompt("Enter deployed backend URL (e.g. https://hackerranker-orchestrate.onrender.com):", current);
      if (updated !== null && updated.trim()) {
        try {
          localStorage.setItem("GHOST_DATA_API_BASE", updated.trim().replace(/\/$/, ""));
          window.location.reload();
        } catch (e) {}
      }
    });
  }
}

// ── Data Fetching & Summary Calculation ──────────────────────────────────────

async function fetchSummary() {
  try {
    const res = await fetchWithRetry(`${getApiBase()}/api/summary`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    // Initial render from summary endpoint
    if (allCasesCache.length === 0) {
      document.getElementById("valTotalCases").textContent = data.total_cases ?? "--";
      document.getElementById("valComplete").textContent = data.complete_count ?? "--";
      document.getElementById("valIncomplete").textContent = data.incomplete_count ?? "--";
      document.getElementById("valFalseComplete").textContent = data.false_complete_discrepancy_count ?? "--";
      document.getElementById("valNotApplicable").textContent = data.not_applicable_count ?? "--";
    }
  } catch (err) {
    console.warn("Could not fetch summary from backend:", err);
  }
}

async function fetchCases() {
  const tbody = document.getElementById("casesTableBody");
  try {
    const res = await fetchWithRetry(`${getApiBase()}/api/cases`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    allCasesCache = await res.json();
    
    // Compute summary cards directly from the actual cases data
    updateSummaryCards(allCasesCache);
    renderCasesTable();
  } catch (err) {
    console.error("Error loading cases:", err);
    const apiBase = getApiBase();
    showApiError("Failed to fetch cases from backend.", apiBase);
    tbody.innerHTML = `
      <tr>
        <td colspan="7" style="text-align:center;padding:40px;color:#fb7185;">
          Unable to connect to backend at <code>${escapeHtml(apiBase)}</code>.<br>
          <button onclick="window.location.reload()" style="margin-top:12px;padding:8px 18px;background:#7c3aed;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:0.9rem;">↺ Retry Connection</button>
        </td>
      </tr>
    `;
  }
}

/**
 * Compute summary cards dynamically from case records.
 * Ensures Complete + Incomplete + Not Applicable === Total.
 */
function updateSummaryCards(cases) {
  const total = cases.length;
  let complete = 0;
  let incomplete = 0;
  let na = 0;
  let falseClaim = 0;

  for (const c of cases) {
    const audited = getAuditedState(c);
    const claim = getWorkflowClaim(c);

    if (audited === "COMPLETE") {
      complete++;
    } else if (audited === "INCOMPLETE") {
      incomplete++;
      if (claim === "COMPLETE") {
        falseClaim++;
      }
    } else if (audited === "NOT_APPLICABLE") {
      na++;
    }
  }

  document.getElementById("valTotalCases").textContent = total;
  document.getElementById("valComplete").textContent = complete;
  document.getElementById("valIncomplete").textContent = incomplete;
  document.getElementById("valFalseComplete").textContent = falseClaim;
  document.getElementById("valNotApplicable").textContent = na;

  // Sanity check banner
  const warnEl = document.getElementById("summaryWarning");
  if (warnEl) {
    const sum = complete + incomplete + na;
    if (sum !== total) {
      warnEl.style.display = "block";
      warnEl.textContent = `⚠️ Sanity Warning: Audited Complete (${complete}) + Incomplete (${incomplete}) + Not Applicable (${na}) = ${sum}, which does not match Total Evaluated Cases (${total}).`;
    } else {
      warnEl.style.display = "none";
    }
  }
}

// ── Table Rendering ──────────────────────────────────────────────────────────

function renderCasesTable() {
  const tbody = document.getElementById("casesTableBody");
  const filtered = allCasesCache.filter(c => {
    // Status filter
    const audited = getAuditedState(c);
    if (currentStatusFilter !== "ALL" && audited !== currentStatusFilter) {
      return false;
    }
    // Search query
    if (currentSearchQuery) {
      const q = currentSearchQuery.toLowerCase();
      const matchId = (c.case_id || "").toLowerCase().includes(q);
      const matchEmail = getSubjectEmail(c).toLowerCase().includes(q);
      if (!matchId && !matchEmail) return false;
    }
    return true;
  });

  if (filtered.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="7" style="text-align: center; padding: 40px; color: var(--text-dim);">
          No audit cases match the current filter criteria.
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = filtered.map(c => {
    const auditedState = getAuditedState(c);
    const workflowClaim = getWorkflowClaim(c);
    const findingsCount = getFindingsCount(c);
    const email = getSubjectEmail(c);
    const cutoff = getAuditCutoff(c);

    const statusBadge = getStatusBadge(auditedState);
    const claimBadge = getClaimBadge(workflowClaim, auditedState);
    const findingsBadge = findingsCount > 0 
      ? `<span class="badge badge-findings">${findingsCount} VIOLATIONS</span>` 
      : `<span style="color: var(--text-dim); font-size: 0.75rem;">0</span>`;

    const cutoffFormatted = cutoff ? cutoff.replace("T", " ").replace("Z", "") : "--";

    return `
      <tr>
        <td class="case-id-cell">${escapeHtml(c.case_id)}</td>
        <td class="email-cell">${escapeHtml(email)}</td>
        <td>${claimBadge}</td>
        <td>${statusBadge}</td>
        <td>${findingsBadge}</td>
        <td style="font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: var(--text-dim);">${escapeHtml(cutoffFormatted)}</td>
        <td>
          <button class="btn-inspect" onclick="openCaseDetail('${escapeHtml(c.case_id)}')">
            Inspect Audit
          </button>
        </td>
      </tr>
    `;
  }).join("");
}

function getStatusBadge(status) {
  const s = (status || "").toUpperCase();
  if (s === "COMPLETE") {
    return `<span class="badge badge-complete">COMPLETE</span>`;
  } else if (s === "INCOMPLETE") {
    return `<span class="badge badge-incomplete">INCOMPLETE</span>`;
  } else if (s === "NOT_APPLICABLE") {
    return `<span class="badge badge-na">NOT APPLICABLE</span>`;
  }
  return `<span class="badge badge-na">${escapeHtml(s || "UNKNOWN")}</span>`;
}

function getClaimBadge(claimed, audited) {
  const c = (claimed || "").toUpperCase();
  const a = (audited || "").toUpperCase();
  if (c === "COMPLETE" && a === "INCOMPLETE") {
    return `<span class="badge badge-warning" title="False Claim: Claimed COMPLETE, but data survived">CLAIM: COMPLETE ⚠️</span>`;
  }
  return `<span style="color: var(--text-muted); font-size: 0.75rem; font-family: 'JetBrains Mono', monospace;">${escapeHtml(c)}</span>`;
}

// ── Detail Drawer ────────────────────────────────────────────────────────────

async function openCaseDetail(caseId) {
  const backdrop = document.getElementById("drawerBackdrop");
  const body = document.getElementById("drawerBody");
  const title = document.getElementById("drawerTitle");
  const email = document.getElementById("drawerEmail");

  title.textContent = `Auditing ${caseId}`;
  email.textContent = "Loading forensic details...";
  body.innerHTML = `<div style="text-align: center; padding: 60px; color: var(--text-dim);">Analyzing audit evidence...</div>`;
  backdrop.classList.add("open");

  try {
    const res = await fetchWithRetry(`${getApiBase()}/api/cases/${caseId}`);
    if (!res.ok) throw new Error("Failed to load case detail");
    const c = await res.json();

    const auditedState = getAuditedState(c);
    const workflowClaim = getWorkflowClaim(c);
    const subjectEmail = getSubjectEmail(c);
    const cutoff = getAuditCutoff(c);
    const findingsList = Array.isArray(c.findings) ? c.findings : [];
    const planList = Array.isArray(c.plan) ? c.plan : [];
    const checksList = Array.isArray(c.checks) ? c.checks : [];

    title.textContent = `Case ${c.case_id}`;
    email.textContent = subjectEmail || "No email associated";

    let html = `
      <!-- Status Badges Banner -->
      <div style="display: flex; gap: 10px; align-items: center; margin-bottom: 20px;">
        <div>
          <span style="font-size: 0.75rem; color: var(--text-dim); display: block; margin-bottom: 4px;">AUDITED STATE:</span>
          ${getStatusBadge(auditedState)}
        </div>
        <div>
          <span style="font-size: 0.75rem; color: var(--text-dim); display: block; margin-bottom: 4px;">WORKFLOW CLAIM:</span>
          ${getClaimBadge(workflowClaim, auditedState)}
        </div>
      </div>

      <!-- Timestamps -->
      <div class="meta-grid">
        <div class="meta-item">
          <div class="meta-item-label">Requested At</div>
          <div class="meta-item-val">${escapeHtml(c.requested_at || "N/A")}</div>
        </div>
        <div class="meta-item">
          <div class="meta-item-label">Audit Cutoff (audit_at)</div>
          <div class="meta-item-val">${escapeHtml(cutoff || "N/A")}</div>
        </div>
      </div>

      <!-- Request Text -->
      <div class="detail-section">
        <h4>User Request Text</h4>
        <div class="request-bubble">
          ${escapeHtml(c.request_text || "No text provided.")}
        </div>
      </div>
    `;

    // Findings section
    if (findingsList.length > 0) {
      html += `
        <div class="detail-section">
          <h4>🚨 Findings (${findingsList.length} Violation${findingsList.length > 1 ? "s" : ""} at audit_at)</h4>
          ${findingsList.map(s => renderStepCard(s, "finding-card")).join("")}
        </div>
      `;
    }

    // Recommended plan section
    if (planList.length > 0) {
      html += `
        <div class="detail-section">
          <h4>🛠️ ${escapeHtml(c.plan_label || "Recommended plan (not executed)")}</h4>
          <div class="disclaimer-banner">
            <span>ℹ️</span>
            <span>Remediation steps are independent auditor recommendations and are <strong>never executed</strong> on datasets.</span>
          </div>
          ${planList.map(s => renderStepCard(s, "plan-card")).join("")}
        </div>
      `;
    }

    // Verification checks section
    if (checksList.length > 0) {
      const isComplete = auditedState === "COMPLETE";
      const checkTitle = isComplete 
        ? "✅ Evidence-Backed Verification Proving Complete State" 
        : "🔍 Verification Checks (Required After Remediation)";

      html += `
        <div class="detail-section">
          <h4>${checkTitle}</h4>
          ${checksList.map(s => renderStepCard(s, "check-card")).join("")}
        </div>
      `;
    }

    if (!findingsList.length && !planList.length && !checksList.length) {
      html += `
        <div style="padding: 30px; text-align: center; color: var(--text-dim); background: rgba(255,255,255,0.02); border-radius: 8px;">
          Request does not authorize deletion. No audit findings or remediation steps applicable.
        </div>
      `;
    }

    body.innerHTML = html;
  } catch (err) {
    body.innerHTML = `<div style="color: #fb7185; padding: 40px; text-align: center;">Error loading details: ${escapeHtml(err.message)}</div>`;
  }
}

function renderStepCard(s, cardClass) {
  const evMeta = s.evidence_meta;
  let evidenceDisplay = "";
  if (s.evidence_id) {
    const metaDetails = evMeta ? ` (${evMeta.file_path})` : "";
    evidenceDisplay = `
      <div class="step-evidence">
        Evidence: <strong>${escapeHtml(s.evidence_id)}</strong>${escapeHtml(metaDetails)}
      </div>
    `;
  }

  return `
    <div class="step-card ${cardClass}">
      <div class="step-header">
        <span class="step-title">#${s.step_no} ${escapeHtml(s.operation)}</span>
        <span class="badge ${s.state === 'PRESENT' || s.state === 'ACTIVE' ? 'badge-incomplete' : 'badge-complete'}">${escapeHtml(s.state)}</span>
      </div>
      <div class="step-resource">
        System: <strong>${escapeHtml(s.system_id)}</strong> &bull; Resource: <strong>${escapeHtml(s.resource_id)}</strong>
      </div>
      ${evidenceDisplay}
    </div>
  `;
}

function closeDrawer() {
  document.getElementById("drawerBackdrop").classList.remove("open");
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
