document.addEventListener('DOMContentLoaded', function() {
    const websiteInput = document.getElementById('website');
    const checkCurrentButton = document.getElementById('check-current');
    const checkManualButton = document.getElementById('check-manual');
    const resultDiv = document.getElementById('result');
    const currentDomainDiv = document.getElementById('current-domain');
    const currentDomainText = document.getElementById('current-domain-text');
    const loadingDiv = document.getElementById('loading');
    const resultContent = document.getElementById('result-content');

    // Load response.json data
    let responseData = null;

    // Function to load response.json
    async function loadResponseData() {
        // Try multiple methods to load the JSON file
        const methods = [
            // Method 1: chrome.runtime.getURL (standard for extensions)
            async () => {
                const jsonUrl = chrome.runtime.getURL('response.json');
                console.log('Method 1: Attempting to load from:', jsonUrl);
                const response = await fetch(jsonUrl);
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                return await response.json();
            },
            // Method 2: Relative path
            async () => {
                console.log('Method 2: Trying relative path...');
                const response = await fetch('./response.json');
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                return await response.json();
            },
            // Method 3: Absolute path from extension root
            async () => {
                console.log('Method 3: Trying absolute path...');
                const response = await fetch('/response.json');
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                return await response.json();
            }
        ];

        // Try each method in sequence
        for (let i = 0; i < methods.length; i++) {
            try {
                responseData = await methods[i]();
                console.log(`Successfully loaded response.json using method ${i + 1}:`, responseData);
                return; // Success, exit function
            } catch (error) {
                console.warn(`Method ${i + 1} failed:`, error.message);
                // Continue to next method
            }
        }

        // If all methods failed, use fallback
        console.error('All methods failed to load response.json');
        responseData = {
            "Risk Level": "Unknown",
            "Rationale": ["Unable to load analysis data. Please ensure response.json exists in the extension folder and reload the extension."],
            "Confidence Level": 0
        };
    }

    // Function to extract domain from URL
    function extractDomain(url) {
        if (!url) return null;
        
        let domain = url.trim().toLowerCase();
        // Remove protocol
        domain = domain.replace(/^https?:\/\//, '');
        // Remove www
        domain = domain.replace(/^www\./, '');
        // Remove path and query
        domain = domain.split('/')[0].split('?')[0];
        // Remove port
        domain = domain.split(':')[0];
        
        return domain;
    }

    // Function to get current tab URL
    async function getCurrentTabUrl() {
        try {
            const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
            return tab.url;
        } catch (error) {
            console.error('Error getting current tab:', error);
            return null;
        }
    }

    // Function to show high risk popup
    function showHighRiskPopup() {
        const popupOverlay = document.getElementById('risk-popup-overlay');
        if (popupOverlay) {
            popupOverlay.classList.add('show');
        }
    }

    // Function to close high risk popup
    function closeHighRiskPopup() {
        const popupOverlay = document.getElementById('risk-popup-overlay');
        if (popupOverlay) {
            popupOverlay.classList.remove('show');
        }
    }

    // Function to display results
    function displayResults(data) {
        const riskLevel = document.getElementById('risk-level');
        const confidenceValue = document.getElementById('confidence-value');
        const confidenceFill = document.getElementById('confidence-fill');
        const explanationText = document.getElementById('explanation-text');
        const redFlagsDiv = document.getElementById('red-flags');

        // Set risk level
        const riskLevelValue = data["Risk Level"] || "Unknown";
        riskLevel.textContent = `Risk Level: ${riskLevelValue}`;
        riskLevel.className = 'risk-level ' + riskLevelValue.toLowerCase();

        // Set confidence score (already a percentage in the new format)
        const confidencePercent = data["Confidence Level"] || 0;
        confidenceValue.textContent = `${confidencePercent}%`;
        confidenceFill.style.width = `${confidencePercent}%`;

        // Set rationale (array of strings)
        const rationale = data["Rationale"] || [];
        if (Array.isArray(rationale) && rationale.length > 0) {
            // Create a formatted list of rationale points
            explanationText.innerHTML = '';
            rationale.forEach((point, index) => {
                const p = document.createElement('p');
                p.style.marginBottom = index < rationale.length - 1 ? '12px' : '0';
                p.textContent = point;
                explanationText.appendChild(p);
            });
        } else {
            explanationText.textContent = 'No rationale available.';
        }

        // Hide red flags section since it's not in the new structure
        redFlagsDiv.innerHTML = '';

        // Show results FIRST - ensure they're visible
        loadingDiv.style.display = 'none';
        resultContent.style.display = 'block';
        resultDiv.classList.add('show');

        // THEN show red popup if risk level is High (after a brief delay to ensure results are rendered)
        if (riskLevelValue.toLowerCase() === 'high') {
            // Small delay to ensure results are displayed first
            setTimeout(() => {
                showHighRiskPopup();
            }, 100);
        }
    }

    // Function to check website
    async function checkWebsite(domain) {
        if (!domain) {
            alert('Please enter a website URL');
            return;
        }

        // Show loading
        loadingDiv.style.display = 'block';
        resultContent.style.display = 'none';
        resultDiv.classList.add('show');

        // Ensure response data is loaded
        if (!responseData) {
            await loadResponseData();
        }

        // Simulate API call delay (in real implementation, you'd call your API here)
        setTimeout(() => {
            // For now, use the response.json data
            // In production, you'd fetch this from an API based on the domain
            if (responseData) {
                console.log('Displaying results with data:', responseData);
                displayResults(responseData);
            } else {
                console.error('No response data available');
                alert('Error: Could not load analysis data. Please check the console for details.');
            }
        }, 1000);
    }

    // Check current website
    checkCurrentButton.addEventListener('click', async function() {
        const currentUrl = await getCurrentTabUrl();
        if (currentUrl) {
            const domain = extractDomain(currentUrl);
            if (domain) {
                websiteInput.value = domain;
                currentDomainText.textContent = domain;
                currentDomainDiv.style.display = 'block';
                await checkWebsite(domain);
            } else {
                alert('Could not extract domain from current page');
            }
        } else {
            alert('Could not access current tab. Please enter the URL manually.');
        }
    });

    // Check manual input
    checkManualButton.addEventListener('click', async function() {
        const website = websiteInput.value.trim();
        const domain = extractDomain(website);
        if (domain) {
            currentDomainText.textContent = domain;
            currentDomainDiv.style.display = 'block';
            await checkWebsite(domain);
        } else {
            alert('Please enter a valid website URL');
        }
    });

    // Allow Enter key to trigger manual check
    websiteInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            checkManualButton.click();
        }
    });

    // Close popup button event listener
    const closePopupButton = document.getElementById('close-popup');
    if (closePopupButton) {
        closePopupButton.addEventListener('click', closeHighRiskPopup);
    }

    // Close popup when clicking outside
    const popupOverlay = document.getElementById('risk-popup-overlay');
    if (popupOverlay) {
        popupOverlay.addEventListener('click', function(e) {
            if (e.target === popupOverlay) {
                closeHighRiskPopup();
            }
        });
    }

    // Auto-detect current website on load and automatically check it
    async function init() {
        // Load response data first
        await loadResponseData();
        
        // Debug: Check if data loaded
        if (responseData) {
            console.log('Response data loaded successfully:', responseData);
        } else {
            console.error('Failed to load response data');
        }

        // Try to get current tab and auto-check
        const currentUrl = await getCurrentTabUrl();
        if (currentUrl) {
            const domain = extractDomain(currentUrl);
            if (domain) {
                // Auto-fill the input
                websiteInput.value = domain;
                currentDomainText.textContent = domain;
                currentDomainDiv.style.display = 'block';
                
                // Automatically check the website
                console.log('Auto-checking website:', domain);
                await checkWebsite(domain);
            }
        }
    }

    // Initialize
    init();
});
