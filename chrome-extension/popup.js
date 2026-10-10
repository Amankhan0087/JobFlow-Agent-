const API = "http://localhost:8000";

async function checkHealth() {
  try {
    const r = await fetch(`${API}/health`, { signal: AbortSignal.timeout(3000) });
    return r.ok;
  } catch { return false; }
}

async function loadStats() {
  try {
    const r = await fetch(`${API}/api/dashboard`, { signal: AbortSignal.timeout(4000) });
    const d = await r.json();
    document.getElementById("statApplied").textContent = d.total_applications ?? "—";
    document.getElementById("statInterviews").textContent =
      Math.round((d.total_applications || 0) * (d.interview_rate || 0) / 100);
    document.getElementById("statScraped").textContent = d.jobs_scraped ?? "—";
    document.getElementById("statOffers").textContent = d.offers_received ?? "—";
  } catch {
    ["statApplied","statInterviews","statScraped","statOffers"]
      .forEach(id => { document.getElementById(id).textContent = "—"; });
  }
}

async function startAgent(agent) {
  try {
    await fetch(`${API}/api/agents/start`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ agent }),
    });
  } catch (e) {
    alert("JobFlow API is offline. Start the backend first:\npython -m uvicorn jobflow.api.main:app");
  }
}

async function init() {
  const online = await checkHealth();

  // Update status indicators
  document.getElementById("statusDot").classList.toggle("online", online);
  document.getElementById("statusDot2").classList.toggle("online", online);
  document.getElementById("statusText").textContent = online ? "API Online" : "API Offline";
  document.getElementById("statusText").className = "status-text " + (online ? "online" : "");

  if (online) loadStats();

  // Button actions
  document.getElementById("btnScrape").addEventListener("click", () => {
    startAgent("scraper");
    document.getElementById("btnScrape").textContent = "⏳ Running...";
  });
  document.getElementById("btnMatch").addEventListener("click", () => {
    startAgent("matcher");
    document.getElementById("btnMatch").textContent = "⏳ Scoring...";
  });
  document.getElementById("btnApply").addEventListener("click", () => {
    startAgent("bot");
    document.getElementById("btnApply").textContent = "⏳ Applying...";
  });
  document.getElementById("btnFollowup").addEventListener("click", () => {
    startAgent("followup");
    document.getElementById("btnFollowup").textContent = "⏳ Sending...";
  });

  // Open dashboard
  document.getElementById("openDashboard").addEventListener("click", (e) => {
    e.preventDefault();
    chrome.tabs.create({ url: "http://localhost:3000" });
  });
}

init();
