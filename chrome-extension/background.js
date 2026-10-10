/**
 * JobFlow Agent — Service Worker (Background)
 * Handles icon badge updates and API health checks.
 */

const JOBFLOW_API = "http://localhost:8000";

// Check API health and update badge
async function checkApiHealth() {
  try {
    const resp = await fetch(`${JOBFLOW_API}/health`, { signal: AbortSignal.timeout(3000) });
    if (resp.ok) {
      chrome.action.setBadgeText({ text: "ON" });
      chrome.action.setBadgeBackgroundColor({ color: "#10B981" });
    } else {
      throw new Error("not ok");
    }
  } catch {
    chrome.action.setBadgeText({ text: "OFF" });
    chrome.action.setBadgeBackgroundColor({ color: "#EF4444" });
  }
}

// Check on install and every 30 seconds
chrome.runtime.onInstalled.addListener(checkApiHealth);
setInterval(checkApiHealth, 30000);

// Listen for messages from popup
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === "CHECK_HEALTH") {
    checkApiHealth().then(() => sendResponse({ ok: true }));
    return true;
  }
});
