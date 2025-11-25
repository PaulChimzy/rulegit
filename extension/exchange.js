document.addEventListener("DOMContentLoaded", function () {
  const resultDiv = document.getElementById("result");
  const currentDomainDiv = document.getElementById("current-domain");
  const currentDomainText = document.getElementById("current-domain-text");
  const loadingDiv = document.getElementById("loading");
  const resultContent = document.getElementById("result-content");

  // -------------------------------
  // KEEP: extractDomain() and UI functions
  // -------------------------------

  function extractDomain(url) {
    if (!url) return null;
    let domain = url.trim().toLowerCase();
    domain = domain.replace(/^https?:\/\//, "").replace(/^www\./, "");
    domain = domain.split("/")[0].split("?")[0];
    domain = domain.split(":")[0];
    return domain;
  }

  function displayResults(data) {
    // const riskLevel = document.getElementById("risk-level");
    const confidenceValue = document.getElementById("confidence-value");
    const confidenceFill = document.getElementById("confidence-fill");
    const explanationText = document.getElementById("explanation-text");
    const redFlagsDiv = document.getElementById("red-flags");
    const donut = document.getElementById("risk-donut");
    const donutCircle = document.getElementById("donut-circle");
    const donutText = document.getElementById("donut-text");

    const riskLevelValue = (data["Risk Level"] || "Unknown").toString();
    // riskLevel.textContent = `Risk Level: ${riskLevelValue}`;
    // riskLevel.className = "risk-level " + riskLevelValue.toLowerCase();

    // Update donut appearance
    if (donut) {
      // remove existing level classes (including mixed/critical)
      donut.classList.remove("low", "medium", "high", "mixed", "critical");
      const level = riskLevelValue.toLowerCase();
      // Accept low/medium/high/mixed/critical
      if (["low", "medium", "high", "mixed", "critical"].includes(level)) {
        donut.classList.add(level);
        const cap = level.charAt(0).toUpperCase() + level.slice(1);
        // Use tspans so the label appears on two lines inside the SVG text
        donutText.innerHTML = `<tspan x="50%" dy="-4">${cap}</tspan><tspan x="50%" dy="14" font-size="14">Risk</tspan>`;
      } else {
        donutText.innerHTML = `<tspan x="50%" dy="0">--</tspan>`;
      }
    }

    const confidencePercent = Number(data["Confidence Level"] || 0);
    confidenceValue.textContent = `${confidencePercent}%`;
    confidenceFill.style.width = `${confidencePercent}%`;

    // Fill donut according to confidence (0-100). Use stroke-dashoffset to show fill.
    if (donutCircle) {
      // Use the circle's r attribute so SVG size controls circumference
      const r = Number(donutCircle.getAttribute("r")) || 40;
      const c = 2 * Math.PI * r;
      donutCircle.style.strokeDasharray = `${c}`;

      // Map risk level to a base fill fraction:
      // low  -> 1/4 filled
      // medium -> 1/2 filled
      // high -> 3/4 filled
      const level = (riskLevelValue || "").toLowerCase();
      let baseFraction = null;
      if (level === "low") baseFraction = 0.25;
      else if (level === "medium") baseFraction = 0.5;
      else if (level === "high") baseFraction = 0.75;
      else if (level === "mixed") baseFraction = 0.5; // same as medium
      else if (level === "critical") baseFraction = 1.0; // full circle

      // If we have a baseFraction, use it. Otherwise fall back to confidence percent.
      let fillFraction;
      if (baseFraction !== null) {
        fillFraction = baseFraction;
      } else {
        const pct = Math.max(0, Math.min(100, confidencePercent));
        fillFraction = pct / 100;
      }

      // stroke-dashoffset defines how much of the circle is hidden.
      // To show `fillFraction` of the circle, hide (1 - fillFraction) portion.
      const offset = c * (1 - fillFraction);
      donutCircle.style.strokeDashoffset = `${offset}`;
    }

    const rationale = data["Rationale"] || [];
    explanationText.innerHTML = "";
    rationale.forEach((point) => {
      const p = document.createElement("p");
      p.textContent = point;
      explanationText.appendChild(p);
    });

    loadingDiv.style.display = "none";
    resultContent.style.display = "flex";
    resultDiv.classList.add("show");

    // popup removed: no additional action for high risk in the popup UI
  }

  // -------------------------------
  // NEW: Listen for messages from background.js
  // -------------------------------
  chrome.runtime.onMessage.addListener((msg) => {
    if (msg.action === "analysis_started") {
      // Show spinner & analyzing UI while background fetch runs
      console.log("Popup: analysis started for", msg.domain);
      const currentDomainDiv = document.getElementById("current-domain");
      const currentDomainText = document.getElementById("current-domain-text");
      currentDomainText.textContent = msg.domain || "";
      currentDomainDiv.style.display = "block";
      loadingDiv.style.display = "block";
      resultContent.style.display = "none";
      resultDiv.classList.add("show");
      return;
    }
    if (msg.action === "risk_result") {
      console.log("Popup received:", msg);
      // websiteInput.value = msg.domain;
      currentDomainText.textContent = msg.domain;
      currentDomainDiv.style.display = "block";
      displayResults(msg.data);
    }

    if (msg.action === "clear_results") {
      // Hide/clear popup results when active tab has no cached result
      currentDomainText.textContent = "";
      currentDomainDiv.style.display = "none";
      const resultContent = document.getElementById("result-content");
      const loadingDiv = document.getElementById("loading");
      loadingDiv.style.display = "none";
      resultContent.style.display = "none";
      resultDiv.classList.remove("show");
    }

    if (msg.action === "risk_error") {
      console.error("Backend error:", msg.error);
      alert("Error contacting server.");
    }
  });

  // -------------------------------
  // NEW: Request last cached result from background.js
  // -------------------------------
  chrome.runtime.sendMessage({ action: "get_last_result" }, (response) => {
    if (!response) return;
    // If the background reports the domain is currently being analyzed,
    // show the spinner/analysis UI so the user sees progress even if they
    // opened the popup after analysis started.
    if (response.inProgress) {
      console.log("Popup: domain analysis in progress:", response.domain);
      currentDomainText.textContent = response.domain || "";
      currentDomainDiv.style.display = "block";
      loadingDiv.style.display = "block";
      resultContent.style.display = "none";
      resultDiv.classList.add("show");
      return;
    }
    if (response && response.domain && response.data) {
      console.log("Popup got last cached result:", response);
      // websiteInput.value = response.domain;
      currentDomainText.textContent = response.domain;
      currentDomainDiv.style.display = "block";
      displayResults(response.data);
    }
  });

  // -------------------------------
  // Manual Scan Handler
  // -------------------------------
  async function checkWebsite(domain) {
    if (!domain) return alert("Enter a valid website.");

    loadingDiv.style.display = "block";
    resultContent.style.display = "none";
    resultDiv.classList.add("show");

    try {
      const response = await fetch(
        `http://localhost:8000/validate_url?url=${encodeURIComponent(domain)}`
      );

      if (!response.ok) throw new Error(response.status);

      const data = await response.json();
      displayResults(data);
    } catch (e) {
      console.error("Backend error:", e);
      alert("Could not reach backend.");
      loadingDiv.style.display = "none";
    }
  }
});
