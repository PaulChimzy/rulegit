// Cache to avoid repeatedly scanning the same URL
let lastCheckedDomain = null;

// Cache the latest backend result for popup requests
let lastResult = null;

// Listen for tab updates (navigation complete)
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === "complete" && tab.url) {
    const domain = extractDomain(tab.url);

    if (!domain) return;

    // Prevent calling the backend repeatedly for same domain
    if (domain === lastCheckedDomain) return;
    lastCheckedDomain = domain;

    console.log("[Background] Auto-checking domain:", domain);

    // Call the backend (your FastAPI service)
    fetch(
      `http://localhost:8000/validate_url?url=${encodeURIComponent(domain)}`
    )
      .then((response) => response.json())
      .then((data) => {
        console.log("[Background] Backend Response:", data);

        // Cache last result
        lastResult = { domain, data };

        // Determine risk level
        const risk = (data["Risk Level"] || "").toLowerCase();

        // Update extension badge
        updateBadge(risk);

        // Show desktop notifications based on risk level
        if (risk === "high") {
          showRiskNotification(domain, "HIGH", "red");
        } else if (risk === "medium") {
          showRiskNotification(domain, "MEDIUM", "orange");
        }

        // Send results to popup.js or any active listeners
        safeSendMessage({
          action: "risk_result",
          domain,
          data,
        });
      })
      .catch((err) => {
        console.error("[Background] Error contacting backend:", err);

        safeSendMessage({
          action: "risk_error",
          domain,
          error: "Unable to reach server",
        });
      });
  }
});

// --- Extract domain from URL ---
function extractDomain(url) {
  try {
    let domain = url.replace(/^https?:\/\//, "");
    domain = domain.replace(/^www\./, "");

    domain = domain.split("/")[0].split("?")[0].split("#")[0];
    domain = domain.split(":")[0];

    return domain;
  } catch (e) {
    console.error("[Background] Failed to extract domain:", e);
    return null;
  }
}

// --- Update badge UI indicator ---
function updateBadge(risk) {
  if (risk === "high") {
    chrome.action.setBadgeText({ text: "!" });
    chrome.action.setBadgeBackgroundColor({ color: "red" });
  } else if (risk === "medium") {
    chrome.action.setBadgeText({ text: "!" });
    chrome.action.setBadgeBackgroundColor({ color: "orange" });
  } else {
    chrome.action.setBadgeText({ text: "" });
  }
}

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
    if (lastResult) {
      sendResponse(lastResult);
    } else {
      sendResponse({}); // empty if nothing yet
    }
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
    priority: 2
  });
}
