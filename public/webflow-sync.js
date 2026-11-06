(function() {
    // Hosted ratings.json path:
    const RATINGS_JSON_URL = "https://raw.githubusercontent.com/adamdimitrov/cruisedetective/refs/heads/main/ratings.json";

    function cleanUrl(url) {
        if (!url) return "";
        try {
            const u = new URL(url);
            return (u.origin + u.pathname).replace(/\/$/, "").toLowerCase();
        } catch(e) {
            return url.split('?')[0].replace(/\/$/, "").toLowerCase();
        }
    }

    // Helper to recursively find and update the dateModified field inside a JSON-LD object
    function updateSchemaDates(obj, dateStr) {
        let updated = false;
        if (typeof obj === 'object' && obj !== null) {
            if ('dateModified' in obj) {
                obj['dateModified'] = dateStr;
                updated = true;
            }
            // Recursively search child dictionaries and arrays
            for (let key in obj) {
                if (updateSchemaDates(obj[key], dateStr)) {
                    updated = true;
                }
            }
        }
        return updated;
    }

    // Helper to format raw duration text (e.g. "1h" -> "1 hour", "1.5h" -> "1.5 hours")
    function formatDuration(text) {
        const clean = text.replace("⏳ Duration:", "").replace("⏳", "").replace("Duration:", "").trim().toLowerCase();
        if (clean === "1h" || clean === "1 hour" || clean === "60 min" || clean === "60 minutes" || clean === "60 min.") {
            return "1 hour";
        }
        if (clean === "1.5h" || clean === "1.5 hours" || clean === "90 min" || clean === "90 minutes" || clean === "90 min.") {
            return "1.5 hours";
        }
        if (clean === "2h" || clean === "2 hours" || clean === "120 min") {
            return "2 hours";
        }
        return clean;
    }

    // Helper to dynamically update the price value inside a text block (e.g. "25€ / 1 hour", "10-32€")
    function updatePriceText(oldText, newPrice) {
        // Clean double € typos if present
        const cleanedText = oldText.replace(/€€/g, "€").trim();
        // Regex to find a number preceding a '-' or '€' (e.g. "10-32€" or "25€")
        const match = cleanedText.match(/(\d+)(?:-(\d+))?\s*€/);
        if (match) {
            const oldMin = match[1];
            const oldMax = match[2];
            if (oldMax) {
                // Keep max price in a range, update min price
                return cleanedText.replace(`${oldMin}-${oldMax}€`, `${newPrice}-${oldMax}€`)
                                  .replace(`${oldMin}-${oldMax} €`, `${newPrice}-${oldMax} €`);
            } else {
                // Update single price
                return cleanedText.replace(`${oldMin}€`, `${newPrice}€`)
                                  .replace(`${oldMin} €`, `${newPrice} €`);
            }
        }
        return newPrice + "€";
    }

    async function initRatingsSync() {
        console.log("Initializing Cruise Detective Ratings, Price & Duration Sync...");
        try {
            const response = await fetch(`${RATINGS_JSON_URL}?t=${new Date().getTime()}`).catch(() => null);
            if (!response || !response.ok) {
                return;
            }
            const ratingsDb = await response.json();
            console.log("Successfully loaded ratings database.");

            // 1. Update the visual Last Updated date and Google Schema dateModified
            const timestamp = ratingsDb["_timestamp"];
            if (timestamp) {
                const syncDate = new Date(timestamp);
                const isoDateStr = syncDate.toISOString().split('T')[0]; // Format: YYYY-MM-DD
                
                // Format date visually (e.g. "Jul 19, 2026")
                const options = { year: 'numeric', month: 'short', day: 'numeric' };
                const formattedDate = syncDate.toLocaleDateString('en-US', options);

                // Update visual text element containing "Last updated:"
                // Safely search only <p> elements to avoid wiping out parent containers
                const lastUpdatedElement = Array.from(document.querySelectorAll("p")).find(el => el.textContent.includes("Last updated:"));
                if (lastUpdatedElement) {
                    lastUpdatedElement.innerHTML = `<strong>Last updated:</strong> ${formattedDate}`;
                    console.log(`Updated visual 'Last updated' text to: ${formattedDate}`);
                }

                // Update dateModified inside Google JSON-LD schema
                const schemaScripts = document.querySelectorAll('script[type="application/ld+json"]');
                let schemaUpdated = false;
                schemaScripts.forEach(script => {
                    try {
                        const data = JSON.parse(script.textContent);
                        if (updateSchemaDates(data, isoDateStr)) {
                            script.textContent = JSON.stringify(data, null, 2);
                            schemaUpdated = true;
                        }
                    } catch(e) {}
                });
                
                if (schemaUpdated) {
                    console.log(`Updated Google Schema dateModified to: ${isoDateStr}`);
                }
            }

            // 2. Find all cumulative rating cells on the page
            const ratingCells = [];
            document.querySelectorAll(".star-ratings, .star-ratings-2").forEach(starEl => {
                const cell = starEl.closest("[class*='grid-cell-']");
                if (cell && !ratingCells.includes(cell)) {
                    ratingCells.push(cell);
                }
            });
            let updatedRatingsCount = 0;
            let updatedPricesCount = 0;

            ratingCells.forEach((gridCell4) => {
                const row = gridCell4.closest(".w-layout-grid");
                if (!row) return;

                // Find the corresponding detailed section below by matching the row index
                let detailedSection = null;
                const rowCountEl = row.querySelector(".row-count-2, .row-count");
                if (rowCountEl) {
                    const index = rowCountEl.textContent.trim();
                    if (index) {
                        const allH2s = document.querySelectorAll("h2");
                        const targetH2 = Array.from(allH2s).find(h2 => h2.textContent.trim().startsWith(`${index}. `));
                        if (targetH2) {
                            detailedSection = targetH2.closest(".container, .w-container") || targetH2.parentElement.parentElement;
                        }
                    }
                }

                const cruiseRatingsList = [];

                const reviewsBlocks = [];
                row.querySelectorAll(".reviews, .reviews-3, .reviews-4, .reviews-5").forEach(el => reviewsBlocks.push(el));
                if (detailedSection) {
                    detailedSection.querySelectorAll(".reviews, .reviews-3, .reviews-4, .reviews-5").forEach(el => reviewsBlocks.push(el));
                }

                const allLinks = [];
                row.querySelectorAll("a").forEach(el => allLinks.push(el));
                
                // IMPORTANT FIX: Grab the sibling buy buttons and links outside the row on CruiseDetective
                let sibling = row.nextElementSibling;
                while (sibling && !sibling.classList.contains("w-layout-grid") && !sibling.classList.contains("divider")) {
                    sibling.querySelectorAll("a").forEach(el => allLinks.push(el));
                    sibling = sibling.nextElementSibling;
                }

                if (detailedSection) {
                    detailedSection.querySelectorAll("a").forEach(el => allLinks.push(el));
                }

                const processedUrls = new Set();
                
                const processLink = (link, blockToUpdate) => {
                    if (!link) return;

                    let rawUrl = link.getAttribute("href");
                    if (!rawUrl) return;

                    if (rawUrl.includes("tp.media") && rawUrl.includes("u=")) {
                        try {
                            const uMatch = rawUrl.match(/[?&]u=([^&]+)/);
                            if (uMatch) {
                                rawUrl = decodeURIComponent(uMatch[1]);
                            }
                        } catch(e) {}
                    }

                    const cleaned = cleanUrl(rawUrl);
                    
                    const isPartner = ['getyourguide', 'viator', 'tripadvisor', 'tp.st', 'booking.com', 'hostelworld', 'tiqets', 'tp.media'].some(domain => rawUrl.includes(domain));
                    if (!isPartner) return;

                    if (processedUrls.has(cleaned)) return;

                    const data = ratingsDb[rawUrl] || ratingsDb[cleaned];

                    if (data) {
                        processedUrls.add(cleaned);
                        const parsedRating = parseFloat(data.rating);
                        const parsedReviews = parseInt(data.reviews.replace(/[^0-9]/g, ""), 10);

                        if (!isNaN(parsedRating) && !isNaN(parsedReviews)) {
                            const isOutOf10 = rawUrl.includes("booking.com") || rawUrl.includes("hostelworld.com") || cleaned.includes("booking.com") || cleaned.includes("hostelworld.com");
                            
                            cruiseRatingsList.push({
                                rating: isOutOf10 ? (parsedRating / 2) : parsedRating,
                                reviews: parsedReviews
                            });

                            if (blockToUpdate) {
                                const spans = blockToUpdate.querySelectorAll("span");
                                spans.forEach((span) => {
                                    const text = span.textContent;
                                    if (text.includes("reviews")) {
                                        if (text.includes("/10")) {
                                            span.textContent = `${parsedRating.toFixed(1)}/10 +${parsedReviews.toLocaleString()} reviews `;
                                        } else {
                                            span.textContent = `+${parsedReviews.toLocaleString()} reviews `;
                                        }
                                    }
                                });

                                const ratingContainer = blockToUpdate.querySelector(".price-2-copy");
                                if (ratingContainer) {
                                    const ratingSpan = ratingContainer.querySelector("span") || ratingContainer;
                                    ratingSpan.textContent = parsedRating.toFixed(1);
                                }
                            }
                            
                            updatedRatingsCount++;
                        }

                    } else if (blockToUpdate) {
                        const spans = blockToUpdate.querySelectorAll("span");
                        let existingReviews = 0;
                        spans.forEach((span) => {
                            const reviewMatch = span.textContent.match(/\+?([\d,]+)\s*reviews/);
                            if (reviewMatch) {
                                existingReviews = parseInt(reviewMatch[1].replace(/,/g, ""), 10);
                            }
                        });
                        const ratingContainer = blockToUpdate.querySelector(".price-2-copy");
                        let existingRating = 0;
                        if (ratingContainer) {
                            existingRating = parseFloat((ratingContainer.querySelector("span") || ratingContainer).textContent) || 0;
                        }
                        if (existingReviews > 0 && existingRating > 0) {
                            const isOutOf10 = rawUrl.includes("booking.com") || rawUrl.includes("hostelworld.com");
                            cruiseRatingsList.push({
                                rating: isOutOf10 ? (existingRating / 2) : existingRating,
                                reviews: existingReviews
                            });
                        }
                    }
                };

                reviewsBlocks.forEach((block) => {
                    const link = block.querySelector("a");
                    processLink(link, block);
                });

                allLinks.forEach((link) => {
                    processLink(link, null);
                });

                // 4. Compute and update cumulative stats for this cruise
                if (cruiseRatingsList.length > 0) {
                    let totalReviews = 0;
                    let weightedRatingSum = 0;

                    cruiseRatingsList.forEach((item) => {
                        totalReviews += item.reviews;
                        weightedRatingSum += (item.rating * item.reviews);
                    });

                    const weightedRating = totalReviews > 0 ? (weightedRatingSum / totalReviews) : 0;

                    const cumulativeRatingContainer = gridCell4.querySelector(".price-2-copy");
                    if (cumulativeRatingContainer) {
                        const ratingSpan = cumulativeRatingContainer.querySelector("span") || cumulativeRatingContainer;
                        ratingSpan.textContent = weightedRating.toFixed(1);
                    }

                    let cumulativeReviewsContainer = null;
                    const possibleReviewContainers = gridCell4.querySelectorAll('[class*="price-"]');
                    possibleReviewContainers.forEach(container => {
                        if (container.textContent.toLowerCase().includes('reviews')) {
                            cumulativeReviewsContainer = container;
                        }
                    });
                    
                    if (!cumulativeReviewsContainer) {
                        const fallbackCandidates = gridCell4.querySelectorAll(".price-5, .price-6, .price-2, .price-3");
                        cumulativeReviewsContainer = Array.from(fallbackCandidates).find(c => c.textContent.toLowerCase().includes('reviews'));
                    }
                    if (cumulativeReviewsContainer) {
                        const reviewsSpan = cumulativeReviewsContainer.querySelector("span") || cumulativeReviewsContainer;
                        reviewsSpan.textContent = `+${totalReviews.toLocaleString()} reviews`;
                    }
                }
            });

            console.log(`Sync complete! Updated ${updatedRatingsCount} ratings.`);
        } catch (error) {
            console.error("Ratings Sync Error:", error);
        }
    }

    // ==========================================
    // Cruise Detective Click ID Capture Tracking (R1)
    // ==========================================

    const STORAGE_KEY = 'cd_gclid';
    const EXPIRATION_KEY = 'cd_gclid_exp';
    const EXPIRATION_MS = 90 * 24 * 60 * 60 * 1000; // 90 days in ms (7,776,000,000)
    const COOKIE_MAX_AGE = 90 * 24 * 60 * 60; // 90 days in seconds (7,776,000)

    function saveClickId(type, value) {
        if (!value || typeof value !== 'string') return;
        const cleanValue = value.trim();
        if (!cleanValue) return;

        const payload = type === 'gclid' ? cleanValue : `${type}:${cleanValue}`;
        const expTime = Date.now() + EXPIRATION_MS;

        try {
            if (typeof localStorage !== 'undefined') {
                localStorage.setItem(STORAGE_KEY, payload);
                localStorage.setItem(EXPIRATION_KEY, expTime.toString());
            }
        } catch (e) {}

        try {
            if (typeof document !== 'undefined') {
                document.cookie = `${STORAGE_KEY}=${encodeURIComponent(payload)}; max-age=${COOKIE_MAX_AGE}; path=/; SameSite=Lax`;
            }
        } catch (e) {}
    }

    function parseStoredId(storedVal) {
        if (!storedVal) return null;
        if (storedVal.startsWith('fbclid:')) return { type: 'fbclid', value: storedVal.substring(7) };
        if (storedVal.startsWith('wbraid:')) return { type: 'wbraid', value: storedVal.substring(7) };
        if (storedVal.startsWith('gbraid:')) return { type: 'gbraid', value: storedVal.substring(7) };
        if (storedVal.startsWith('gclid:')) return { type: 'gclid', value: storedVal.substring(6) };
        return { type: 'gclid', value: storedVal };
    }

    function getClickId() {
        // Hierarchy 1: URL parameter
        try {
            if (typeof window !== 'undefined' && window.location && window.location.search) {
                const urlParams = new URLSearchParams(window.location.search);
                for (const type of ['fbclid', 'gclid', 'wbraid', 'gbraid']) {
                    const val = urlParams.get(type);
                    if (val && val.trim()) {
                        const cleanVal = val.trim();
                        saveClickId(type, cleanVal);
                        return { type, value: cleanVal };
                    }
                }
            }
        } catch (e) {}

        // Hierarchy 2: localStorage
        try {
            if (typeof localStorage !== 'undefined') {
                const localVal = localStorage.getItem(STORAGE_KEY);
                const exp = localStorage.getItem(EXPIRATION_KEY);
                if (localVal) {
                    if (exp) {
                        const expTime = parseInt(exp, 10);
                        if (!isNaN(expTime) && Date.now() < expTime) {
                            return parseStoredId(localVal);
                        }
                    } else {
                        localStorage.setItem(EXPIRATION_KEY, (Date.now() + EXPIRATION_MS).toString());
                        return parseStoredId(localVal);
                    }
                }
            }
        } catch (e) {}

        // Hierarchy 3: Cookie
        try {
            if (typeof document !== 'undefined' && document.cookie) {
                const cookies = document.cookie.split(';');
                for (let i = 0; i < cookies.length; i++) {
                    const cookie = cookies[i].trim();
                    if (cookie.startsWith(`${STORAGE_KEY}=`)) {
                        const cookieVal = decodeURIComponent(cookie.substring(STORAGE_KEY.length + 1));
                        if (cookieVal) {
                            const parsed = parseStoredId(cookieVal);
                            saveClickId(parsed.type, parsed.value); // Repopulate localStorage
                            return parsed;
                        }
                    }
                }
            }
        } catch (e) {}

        return null;
    }

    function formatTqCampaign(existingCampaign, clickIdObj) {
        const { type, value } = clickIdObj;
        if (!existingCampaign) {
            return `${type}-${value}`;
        }
        const match = existingCampaign.match(/--(fbclid|gclid|wbraid|gbraid)-/);
        if (match) {
            const baseTag = existingCampaign.substring(0, match.index);
            return baseTag ? `${baseTag}--${type}-${value}` : `${type}-${value}`;
        }
        if (existingCampaign === value) {
            return value;
        }
        return `${existingCampaign}--${type}-${value}`;
    }

    function decorateLink(link, clickIdObj) {
        if (!link || !clickIdObj || !clickIdObj.value) return;
        const { type, value } = clickIdObj;
        try {
            const rawHref = link.getAttribute('href');
            if (!rawHref || !rawHref.includes('tiqets.com')) return;

            const baseUrl = (typeof window !== 'undefined' && window.location && window.location.href) ? window.location.href : 'http://localhost';
            const url = new URL(rawHref, baseUrl);

            if (url.protocol !== 'http:' && url.protocol !== 'https:') return;
            if (url.hostname !== 'tiqets.com' && !url.hostname.endsWith('.tiqets.com')) return;

            const existingCampaign = url.searchParams.get('tq_campaign');
            const newCampaign = formatTqCampaign(existingCampaign, clickIdObj);

            url.searchParams.set('tq_campaign', newCampaign);
            url.searchParams.set(type, value);
            url.searchParams.set('click_id', value);
            
            const existingSubid = url.searchParams.get('subid');
            if (existingSubid) {
                if (!existingSubid.includes(`${type}:`)) {
                    url.searchParams.set('subid', existingSubid + `|${type}:${value}`);
                }
            } else {
                url.searchParams.set('subid', `${type}:${value}`);
            }

            link.href = url.toString();
        } catch (e) {
            // Ignore malformed or unparseable URLs
        }
    }

    function scanAndDecorate(container) {
        const activeClickId = getClickId();
        if (!activeClickId || typeof document === 'undefined') return;

        try {
            const root = container || document;
            if (!root || !root.querySelectorAll) return;
            const links = root.querySelectorAll('a[href*="tiqets.com"]');
            links.forEach(link => decorateLink(link, activeClickId));
        } catch (e) {}
    }

    let mutationObserverInstance = null;

    function setupMutationObserver() {
        if (typeof MutationObserver === 'undefined' || typeof document === 'undefined') return null;
        const target = document.body || document.documentElement;
        if (!target) return null;

        try {
            if (!mutationObserverInstance) {
                mutationObserverInstance = new MutationObserver((mutations) => {
                    const activeClickId = getClickId();
                    if (!activeClickId) return;

                    mutations.forEach((mutation) => {
                        mutation.addedNodes.forEach((node) => {
                            if (node.nodeType === 1) { // Node.ELEMENT_NODE
                                if (node.matches && node.matches('a[href*="tiqets.com"]')) {
                                    decorateLink(node, activeClickId);
                                }
                                if (node.querySelectorAll) {
                                    const links = node.querySelectorAll('a[href*="tiqets.com"]');
                                    links.forEach(link => decorateLink(link, activeClickId));
                                }
                            }
                        });
                    });
                });
                mutationObserverInstance.observe(target, { childList: true, subtree: true });
            }
        } catch (e) {}

        return mutationObserverInstance;
    }

    let clickListenerAttached = false;

    function setupClickInterceptor() {
        if (typeof document === 'undefined' || clickListenerAttached) return;

        try {
            document.addEventListener('click', (e) => {
                const activeClickId = getClickId();
                if (!activeClickId) return;

                const path = e.composedPath ? e.composedPath() : (e.target ? [e.target] : []);
                for (let i = 0; i < path.length; i++) {
                    const el = path[i];
                    if (el && el.nodeType === 1 && el.tagName === 'A') {
                        const href = el.getAttribute && el.getAttribute('href');
                        if (href && href.includes('tiqets.com')) {
                            decorateLink(el, activeClickId);
                        }
                    }
                }
            }, true); // Capture phase listener
            clickListenerAttached = true;
        } catch (e) {}
    }

    function initTiqetsTracking() {
        const clickIdObj = getClickId();
        scanAndDecorate();
        setupMutationObserver();
        setupClickInterceptor();
        return clickIdObj;
    }

    const CruiseDetectiveTracking = {
        saveGclid: saveClickId, // Kept for backwards compatibility
        getGclid: getClickId,   // Kept for backwards compatibility
        saveClickId: saveClickId,
        getClickId: getClickId,
        formatTqCampaign: formatTqCampaign,
        decorateLink: decorateLink,
        scanAndDecorate: scanAndDecorate,
        setupMutationObserver: setupMutationObserver,
        setupClickInterceptor: setupClickInterceptor,
        init: initTiqetsTracking
    };

    if (typeof window !== 'undefined') {
        window.CruiseDetectiveTracking = CruiseDetectiveTracking;
    }

    // Run on DOM load
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", () => {
            initRatingsSync();
            initTiqetsTracking();
        });
    } else {
        initRatingsSync();
        initTiqetsTracking();
    }
})();

