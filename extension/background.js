// Cache to avoid repeatedly scanning the same URL
let lastCheckedDomain = null;

// Cache results per domain so we can reuse previously-scanned sites
// Use a Map to preserve insertion order for LRU-style eviction
const resultCache = new Map();
const MAX_CACHE_ENTRIES = 200; // keep last 200 results by default

// Pending timers for debouncing tab updates (keyed by tabId)
const pendingChecks = {};
// Domains currently being analyzed (to allow popup to show spinner when opened)
const inProgress = new Set();

// Listen for tab updates (navigation complete)
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  // Debounce multiple quick updates (some pages fire many updates). We
  // schedule a short delay and only perform the check when the timer fires.
  if (changeInfo.status === "complete" && tab && tab.url) {
    // Clear any pending timer for this tab
    if (pendingChecks[tabId]) {
      clearTimeout(pendingChecks[tabId]);
    }

    // Capture the url at the time of the event
    const urlToCheck = tab.url;

  // Schedule the actual check after a short delay (5000ms = 5s)
  pendingChecks[tabId] = setTimeout(() => {
      delete pendingChecks[tabId];

      const domain = extractDomain(urlToCheck);
      if (!domain) return; // ignore non-http(s) or invalid urls

      // Prevent calling the backend repeatedly for same domain
      if (domain === lastCheckedDomain) return;
      lastCheckedDomain = domain;

      console.log("[Background] Auto-checking domain:", domain);

      // Mark domain as in-progress and inform any open popup so UI can show spinner
      inProgress.add(domain);
      safeSendMessage({ action: "analysis_started", domain });

      // Call the backend (your FastAPI service)
      fetch(
        `http://localhost:8000/validate_url?url=${encodeURIComponent(domain)}`
      )
        .then((response) => response.json())
        .then((data) => {
          console.log("[Background] Backend Response:", data);

          // Cache last result per-domain (LRU): move to newest
          if (resultCache.has(domain)) resultCache.delete(domain);
          resultCache.set(domain, data);
          // Evict oldest if over limit
          if (resultCache.size > MAX_CACHE_ENTRIES) {
            const oldestKey = resultCache.keys().next().value;
            resultCache.delete(oldestKey);
          }

          // Determine risk level (normalize to lowercase)
          const risk = (data["Risk Level"] || "").toLowerCase();

          // Update extension badge
          updateBadge(risk);

          // Also show desktop notifications when a result arrives so users
          // get a system-level alert in addition to the popup UI.
          // Map 'critical' -> HIGH and 'mixed' -> MEDIUM to match badge colors.
          if (risk === "high" || risk === "critical") {
            showRiskNotification(domain, "HIGH");
          } else if (risk === "medium" || risk === "mixed") {
            showRiskNotification(domain, "MEDIUM");
          }

          // Send results to popup.js or any active listeners
          safeSendMessage({ action: "risk_result", domain, data });
        })
        .catch((err) => {
          console.error("[Background] Error contacting backend:", err);

          safeSendMessage({
            action: "risk_error",
            domain,
            error: "Unable to reach server",
          });
        })
        .finally(() => {
          // Analysis finished (success or failure)
          inProgress.delete(domain);
        });
    }, 1000);
  }
});

// --- Extract domain from URL ---
function extractDomain(url) {
  try {
    // Use the URL parser and only accept http(s) schemes.
    const parsed = new URL(url);
    if (!["http:", "https:"].includes(parsed.protocol)) {
      // ignore chrome://, about:, chrome-extension://, file://, data:, etc.
      return null;
    }
    // hostname gives the domain without port
    let hostname = parsed.hostname || null;
    if (!hostname) return null;
    // Strip leading www.
    hostname = hostname.replace(/^www\./, "");
    return hostname;
  } catch (e) {
    // If URL constructor fails (invalid URL), ignore
    // console.debug("[Background] Failed to extract domain:", e);
    return null;
  }
}

// --- Update badge UI indicator ---
function updateBadge(risk) {
  // Map risk levels to badge appearance. Treat 'critical' same as 'high'
  // and 'mixed' same as 'medium'.
  if (risk === "high" || risk === "critical") {
    chrome.action.setBadgeText({ text: "!" });
    chrome.action.setBadgeBackgroundColor({ color: "red" });
  } else if (risk === "medium" || risk === "mixed") {
    chrome.action.setBadgeText({ text: "!" });
    chrome.action.setBadgeBackgroundColor({ color: "orange" });
  } else {
    chrome.action.setBadgeText({ text: "" });
  }
}

// Clear badge (helper)
function clearBadge() {
  try {
    chrome.action.setBadgeText({ text: "" });
  } catch (e) {
    // ignore in case chrome.action unsupported in environment
  }
}

// When the user activates a different tab, clear the badge unless the
// active tab's domain matches the last checked domain. This avoids the
// badge misleadingly indicating risk for a site on a previous tab.
chrome.tabs.onActivated.addListener((activeInfo) => {
  try {
    chrome.tabs.get(activeInfo.tabId, (tab) => {
      if (!tab || !tab.url) {
        clearBadge();
        // inform popup to clear if open
        safeSendMessage({ action: "clear_results" });
        return;
      }
      const domain = extractDomain(tab.url);
      if (!domain) {
        clearBadge();
        safeSendMessage({ action: "clear_results" });
        return;
      }
      // If analysis is currently running for this domain, tell popup to show spinner
      if (inProgress.has(domain)) {
        safeSendMessage({ action: "analysis_started", domain });
        return;
      }
      // If we have a cached result for this domain, show badge and push cached data
      if (resultCache.has(domain)) {
        // Update recency for LRU: move accessed entry to the end
        const data = resultCache.get(domain);
        resultCache.delete(domain);
        resultCache.set(domain, data);
        const risk = (data["Risk Level"] || "").toLowerCase();
        updateBadge(risk);
        safeSendMessage({ action: "risk_result", domain, data });
        return;
      }
      // Otherwise clear badge and tell popup to clear
      clearBadge();
      safeSendMessage({ action: "clear_results" });
    });
  } catch (e) {
    // ignore errors
  }
});

// Clean up pending timers if a tab is removed
chrome.tabs.onRemoved.addListener((tabId) => {
  if (pendingChecks[tabId]) {
    clearTimeout(pendingChecks[tabId]);
    delete pendingChecks[tabId];
  }
});

function safeSendMessage(msg) {
  try {
    chrome.runtime.sendMessage(msg, () => {
      if (chrome.runtime.lastError) {
        // Popup is closed — ignore
        return;
      }
    });
  } catch (err) {
    // Should never happen, but ignore anyway
  }
}

// --- Respond to popup requesting last result ---
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.action === "get_last_result") {
    // Return the cached result for the currently active tab (if any).
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      const tab = tabs && tabs[0];
      if (!tab || !tab.url) {
        sendResponse({});
        return;
      }
      const domain = extractDomain(tab.url);
      if (!domain) {
        sendResponse({});
        return;
      }
      // If the domain is currently being analyzed, let the popup know so it
      // can show the spinner even if it opened after the analysis_started message.
      if (inProgress.has(domain)) {
        sendResponse({ domain, data: null, inProgress: true });
        return;
      }
      if (!resultCache.has(domain)) {
        sendResponse({});
        return;
      }
      // Update recency for LRU before returning
      const respData = resultCache.get(domain);
      resultCache.delete(domain);
      resultCache.set(domain, respData);
      sendResponse({ domain, data: respData });
    });
    return true; // keep channel open for async
  }
});

// -------------------------------
// Show desktop notifications
// -------------------------------
function showRiskNotification(domain, level, color) {
  chrome.notifications.create({
    type: "basic",
    iconUrl: "integrity.png",
    title: `${level}-Risk Domain Detected`,
    message: `${domain} is classified as ${level} risk!`,
    priority: 2,
  });
}
