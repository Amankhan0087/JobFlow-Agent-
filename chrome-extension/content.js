/**
 * JobFlow Agent — Content Script
 * Injects "Add to JobFlow" button on supported job boards.
 * Extracts job data and sends to local JobFlow API.
 */

const JOBFLOW_API = "http://localhost:8000";

// ── Platform detectors ─────────────────────────────────────────────────────

const PLATFORMS = {
  linkedin: {
    match: () => location.hostname.includes("linkedin.com"),
    extract: () => ({
      job_title: qs(".job-details-jobs-unified-top-card__job-title")?.innerText?.trim()
        || qs("h1.t-24")?.innerText?.trim() || "",
      company_name: qs(".job-details-jobs-unified-top-card__company-name")?.innerText?.trim()
        || qs(".topcard__org-name-link")?.innerText?.trim() || "",
      location: qs(".job-details-jobs-unified-top-card__bullet")?.innerText?.trim() || "",
      job_description: qs(".jobs-description__content")?.innerText?.trim()?.slice(0, 2000) || "",
      application_url: location.href,
      platform: "linkedin",
    }),
    insertTarget: () => qs(".job-details-jobs-unified-top-card__primary-description-container")
      || qs(".jobs-apply-button--top-card"),
  },

  indeed: {
    match: () => location.hostname.includes("indeed.com"),
    extract: () => ({
      job_title: qs('[data-testid="jobsearch-JobInfoHeader-title"]')?.innerText?.trim()
        || qs("h1.jobsearch-JobInfoHeader-title")?.innerText?.trim() || "",
      company_name: qs('[data-testid="inlineHeader-companyName"]')?.innerText?.trim()
        || qs(".jobsearch-InlineCompanyRating-companyName")?.innerText?.trim() || "",
      location: qs('[data-testid="job-location"]')?.innerText?.trim() || "",
      job_description: qs("#jobDescriptionText")?.innerText?.trim()?.slice(0, 2000) || "",
      application_url: location.href,
      platform: "indeed",
    }),
    insertTarget: () => qs(".jobsearch-JobInfoHeader-title-container")
      || qs('[data-testid="jobsearch-JobInfoHeader-title"]')?.closest("div"),
  },

  glassdoor: {
    match: () => location.hostname.includes("glassdoor.com"),
    extract: () => ({
      job_title: qs('[data-test="job-title"]')?.innerText?.trim() || qs("h1")?.innerText?.trim() || "",
      company_name: qs('[data-test="employer-name"]')?.innerText?.trim() || "",
      location: qs('[data-test="emp-location"]')?.innerText?.trim() || "",
      job_description: qs(".jobDescriptionContent")?.innerText?.trim()?.slice(0, 2000) || "",
      application_url: location.href,
      platform: "glassdoor",
    }),
    insertTarget: () => qs('[data-test="job-title"]')?.closest("div"),
  },

  bayt: {
    match: () => location.hostname.includes("bayt.com"),
    extract: () => ({
      job_title: qs("h1.jb-title")?.innerText?.trim() || qs("h1")?.innerText?.trim() || "",
      company_name: qs("[class*='company-name']")?.innerText?.trim() || "",
      location: qs("[class*='location']")?.innerText?.trim() || "",
      job_description: qs("[class*='job-description']")?.innerText?.trim()?.slice(0, 2000) || "",
      application_url: location.href,
      platform: "bayt",
    }),
    insertTarget: () => qs("h1.jb-title")?.closest("div") || qs(".jb-header"),
  },

  reed: {
    match: () => location.hostname.includes("reed.co.uk"),
    extract: () => ({
      job_title: qs("h1[itemprop='title']")?.innerText?.trim() || qs("h1")?.innerText?.trim() || "",
      company_name: qs("[itemprop='hiringOrganization'] span")?.innerText?.trim() || "",
      location: qs("[itemprop='jobLocation']")?.innerText?.trim() || "",
      job_description: qs("[itemprop='description']")?.innerText?.trim()?.slice(0, 2000) || "",
      application_url: location.href,
      platform: "reed",
    }),
    insertTarget: () => qs(".apply-button-container") || qs("h1")?.closest("div"),
  },

  stepstone: {
    match: () => location.hostname.includes("stepstone.de"),
    extract: () => ({
      job_title: qs("[data-at='job-title']")?.innerText?.trim() || qs("h1")?.innerText?.trim() || "",
      company_name: qs("[data-at='job-item-company-name']")?.innerText?.trim() || "",
      location: qs("[data-at='job-item-location']")?.innerText?.trim() || "",
      job_description: qs("[class*='JobDescription']")?.innerText?.trim()?.slice(0, 2000) || "",
      application_url: location.href,
      platform: "stepstone",
    }),
    insertTarget: () => qs("[data-at='job-title']")?.closest("div"),
  },
};

function qs(selector) {
  return document.querySelector(selector);
}

function detectPlatform() {
  return Object.values(PLATFORMS).find(p => p.match());
}

function detectCountry() {
  const host = location.hostname;
  if (host.includes("ae.indeed") || host.includes("bayt.com") || host.includes("naukrigulf")) return "UAE";
  if (host.includes("sa.indeed") || host.includes("tanqeeb")) return "SA";
  if (host.includes("uk.indeed") || host.includes("reed.co.uk")) return "UK";
  if (host.includes("de.indeed") || host.includes("stepstone.de")) return "Germany";
  if (host.includes("glassdoor") || (host.includes("indeed") && !host.match(/^(ae|sa|uk|de)\./))) return "USA";
  if (host.includes("linkedin")) {
    const loc = document.querySelector("[class*='location']")?.innerText || "";
    if (loc.match(/UAE|Dubai|Abu Dhabi/i)) return "UAE";
    if (loc.match(/Saudi|Riyadh|Jeddah/i)) return "SA";
    if (loc.match(/UK|London|Manchester/i)) return "UK";
    if (loc.match(/Germany|Berlin|Munich/i)) return "Germany";
    return "USA";
  }
  return "UAE";
}

// ── Button UI ──────────────────────────────────────────────────────────────

function createButton(state = "idle") {
  const btn = document.createElement("button");
  btn.id = "jobflow-add-btn";
  btn.className = "jobflow-btn";

  const states = {
    idle: { text: "⚡ Add to JobFlow", bg: "#2DD4BF", color: "#0A0F1E" },
    loading: { text: "⏳ Adding...", bg: "#374151", color: "#9CA3AF" },
    success: { text: "✓ Added to Pipeline", bg: "#10B981", color: "#fff" },
    error: { text: "✗ Failed — Retry", bg: "#EF4444", color: "#fff" },
    duplicate: { text: "Already in Pipeline", bg: "#6B7280", color: "#fff" },
  };

  const s = states[state];
  btn.textContent = s.text;
  Object.assign(btn.style, {
    background: s.bg,
    color: s.color,
    border: "none",
    borderRadius: "8px",
    padding: "10px 20px",
    fontSize: "13px",
    fontWeight: "700",
    cursor: state === "loading" ? "not-allowed" : "pointer",
    marginTop: "12px",
    marginBottom: "4px",
    display: "inline-flex",
    alignItems: "center",
    gap: "6px",
    fontFamily: "system-ui, -apple-system, sans-serif",
    boxShadow: "0 2px 8px rgba(45,212,191,0.3)",
    transition: "all 0.2s ease",
    zIndex: "9999",
  });

  return btn;
}

function injectButton(platform) {
  if (document.getElementById("jobflow-add-btn")) return;

  const target = platform.insertTarget();
  if (!target) return;

  const btn = createButton("idle");

  btn.addEventListener("click", async () => {
    btn.replaceWith(createButton("loading"));
    const loadingBtn = document.getElementById("jobflow-add-btn");
    if (!loadingBtn) return;

    try {
      const jobData = platform.extract();
      const country = detectCountry();

      const payload = {
        platform: jobData.platform,
        country,
        job_title: jobData.job_title || "Unknown Role",
        company_name: jobData.company_name || "Unknown Company",
        job_description: jobData.job_description || "",
        application_url: jobData.application_url,
        location: jobData.location || "",
        source: "chrome_extension",
      };

      const resp = await fetch(`${JOBFLOW_API}/api/jobs/add`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const result = await resp.json();

      loadingBtn.replaceWith(createButton(result.duplicate ? "duplicate" : "success"));
      showToast(result.duplicate ? "Already in your pipeline!" : `Added: ${payload.job_title}`, result.duplicate ? "info" : "success");

      // Auto reset after 4 seconds
      setTimeout(() => {
        const current = document.getElementById("jobflow-add-btn");
        if (current) current.replaceWith(createButton("idle"));
      }, 4000);

    } catch (err) {
      const lb = document.getElementById("jobflow-add-btn");
      if (lb) lb.replaceWith(createButton("error"));
      showToast("JobFlow API offline — is it running?", "error");
    }
  });

  target.appendChild(btn);
}

// ── Toast notification ─────────────────────────────────────────────────────

function showToast(message, type = "success") {
  const existing = document.getElementById("jobflow-toast");
  if (existing) existing.remove();

  const toast = document.createElement("div");
  toast.id = "jobflow-toast";
  const colors = { success: "#10B981", error: "#EF4444", info: "#6366F1" };
  Object.assign(toast.style, {
    position: "fixed",
    bottom: "24px",
    right: "24px",
    background: colors[type] || "#10B981",
    color: "#fff",
    padding: "12px 20px",
    borderRadius: "10px",
    fontSize: "13px",
    fontWeight: "600",
    fontFamily: "system-ui, sans-serif",
    zIndex: "999999",
    boxShadow: "0 4px 20px rgba(0,0,0,0.3)",
    animation: "jobflow-slide-in 0.3s ease",
  });
  toast.textContent = `⚡ JobFlow: ${message}`;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3500);
}

// ── Init ───────────────────────────────────────────────────────────────────

function init() {
  const platform = detectPlatform();
  if (!platform) return;

  // Inject immediately if DOM ready, otherwise wait
  if (document.readyState === "complete" || document.readyState === "interactive") {
    setTimeout(() => injectButton(platform), 800);
  } else {
    document.addEventListener("DOMContentLoaded", () => setTimeout(() => injectButton(platform), 800));
  }

  // Re-inject on SPA navigation (LinkedIn uses pushState)
  let lastUrl = location.href;
  const observer = new MutationObserver(() => {
    if (location.href !== lastUrl) {
      lastUrl = location.href;
      const old = document.getElementById("jobflow-add-btn");
      if (old) old.remove();
      setTimeout(() => injectButton(detectPlatform() || platform), 1200);
    }
  });
  observer.observe(document.body, { childList: true, subtree: true });
}

init();
