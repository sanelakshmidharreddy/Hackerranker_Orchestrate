/**
 * Ghost Data Still Exists — Frontend Logic
 * Connects to backend API and renders metrics, case lists, and forensic audit details.
 */

const API_BASE = (window.API_BASE || "").replace(/\/$/, "");

let currentStatusFilter = "ALL";
let currentSearchQuery = "";
let allCasesCache = [];

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
      currentStatusFilter = e.target.dataset.status;
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
}

async function fetchSummary() {
  try {
    const res = await fetch(`${API_BASE}/api/summary`);
    if (!res.ok) throw new Error("Failed to load summary");
    const data = await res.json();

    document.getElementById("valTotalCases").textContent = data.total_cases ?? "--";
    document.getElementById("valComplete").textContent = data.complete_count ?? "--";
    document.getElementById("valIncomplete").textContent = data.incomplete_count ?? "--";
    document.getElementById("valFalseComplete").textContent = data.false_complete_discrepancy_count ?? "--";
    document.getElementById("valNotApplicable").textContent = data.not_applicable_count ?? "--";
  } catch (err) {
    console.warn("Could not fetch summary from backend:", err);
  }
}

async function fetchCases() {
  const tbody = document.getElementById("casesTableBody");
  try {
    const res = await fetch(`${API_BASE}/api/cases`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    allCasesCache = await res.json();
    renderCasesTable();
  } catch (err) {
    console.error("Error loading cases:", err);
    tbody.innerHTML = `
      <tr>
        <td colspan="7" style="text-align: center; padding: 40px; color: #fb7185;">
          Unable to connect to backend at <code>${API_BASE || window.location.origin}</code>.<br>
          Please make sure the backend is running: <code>cd backend && uvicorn app:app --port 8000</code>
        </td>
      </tr>
    `;
  }
}

function renderCasesTable() {
  const tbody = document.getElementById("casesTableBody");
  const filtered = allCasesCache.filter(c => {
    // Status filter
    if (currentStatusFilter !== "ALL" && c.deletion_status.toUpperCase() !== currentStatusFilter) {
      return false;
    }
    // Search query
    if (currentSearchQuery) {
      const q = currentSearchQuery.toLowerCase();
      const matchId = (c.case_id || "").toLowerCase().includes(q);
      const matchEmail = (c.email || "").toLowerCase().includes(q);
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
    const statusBadge = getStatusBadge(c.deletion_status);
    const claimBadge = getClaimBadge(c.reported_status, c.deletion_status);
    const findingsBadge = c.n_findings > 0 
      ? `<span class="badge badge-findings">${c.n_findings} VIOLATIONS</span>` 
      : `<span style="color: var(--text-dim); font-size: 0.75rem;">0</span>`;

    const cutoffFormatted = c.audit_at ? c.audit_at.replace("T", " ").replace("Z", "") : "--";

    return `
      <tr>
        <td class="case-id-cell">${escapeHtml(c.case_id)}</td>
        <td class="email-cell">${escapeHtml(c.email)}</td>
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
  if (status === "COMPLETE") {
    return `<span class="badge badge-complete">COMPLETE</span>`;
  } else if (status === "INCOMPLETE") {
    return `<span class="badge badge-incomplete">INCOMPLETE</span>`;
  } else if (status === "NOT_APPLICABLE") {
    return `<span class="badge badge-na">NOT APPLICABLE</span>`;
  }
  return `<span class="badge badge-na">${escapeHtml(status)}</span>`;
}

function getClaimBadge(claimed, audited) {
  if (claimed === "COMPLETE" && audited === "INCOMPLETE") {
    return `<span class="badge badge-warning" title="False Claim: Claimed COMPLETE, but data survived">CLAIM: COMPLETE ⚠️</span>`;
  }
  return `<span style="color: var(--text-muted); font-size: 0.75rem; font-family: 'JetBrains Mono', monospace;">${escapeHtml(claimed)}</span>`;
}

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
    const res = await fetch(`${API_BASE}/api/cases/${caseId}`);
    if (!res.ok) throw new Error("Failed to load case detail");
    const c = await res.json();

    title.textContent = `Case ${c.case_id}`;
    email.textContent = c.email || "No email associated";

    let html = `
      <!-- Status Badges Banner -->
      <div style="display: flex; gap: 10px; align-items: center; margin-bottom: 20px;">
        <div>
          <span style="font-size: 0.75rem; color: var(--text-dim); display: block; margin-bottom: 4px;">AUDITED STATE:</span>
          ${getStatusBadge(c.deletion_status)}
        </div>
        <div>
          <span style="font-size: 0.75rem; color: var(--text-dim); display: block; margin-bottom: 4px;">WORKFLOW CLAIM:</span>
          ${getClaimBadge(c.reported_status, c.deletion_status)}
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
          <div class="meta-item-val">${escapeHtml(c.audit_at || "N/A")}</div>
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
    if (c.findings && c.findings.length > 0) {
      html += `
        <div class="detail-section">
          <h4>🚨 Findings (Data Survives at audit_at)</h4>
          ${c.findings.map(s => renderStepCard(s, "finding-card")).join("")}
        </div>
      `;
    }

    // Recommended plan section
    if (c.plan && c.plan.length > 0) {
      html += `
        <div class="detail-section">
          <h4>🛠️ ${escapeHtml(c.plan_label || "Recommended plan (not executed)")}</h4>
          <div class="disclaimer-banner">
            <span>ℹ️</span>
            <span>Remediation steps are independent auditor recommendations and are <strong>never executed</strong> on datasets.</span>
          </div>
          ${c.plan.map(s => renderStepCard(s, "plan-card")).join("")}
        </div>
      `;
    }

    // Verification checks section
    if (c.checks && c.checks.length > 0) {
      const isComplete = c.deletion_status === "COMPLETE";
      const checkTitle = isComplete 
        ? "✅ Evidence-Backed Verification Proving Complete State" 
        : "🔍 Verification Checks (Required After Remediation)";

      html += `
        <div class="detail-section">
          <h4>${checkTitle}</h4>
          ${c.checks.map(s => renderStepCard(s, "check-card")).join("")}
        </div>
      `;
    }

    if (!c.findings?.length && !c.plan?.length && !c.checks?.length) {
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
