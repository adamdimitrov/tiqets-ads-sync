document.addEventListener('DOMContentLoaded', () => {
    // -------------------------------------------------------------
    // 1. Click ID Persistence & Tiqets Link Decoration Engine (CAPI)
    // -------------------------------------------------------------
    const STORAGE_KEY = 'cd_gclid';
    const EXPIRATION_KEY = 'cd_gclid_exp';
    const EXPIRATION_MS = 90 * 24 * 60 * 60 * 1000; // 90 days in ms
    const COOKIE_MAX_AGE = 90 * 24 * 60 * 60; // 90 days in seconds

    function saveClickId(type, value) {
        if (!value || typeof value !== 'string') return;
        const cleanValue = value.trim();
        if (!cleanValue) return;

        const payload = `${type}:${cleanValue}`;
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
        if (storedVal.startsWith('gclid:')) return { type: 'gclid', value: storedVal.substring(6) };
        if (storedVal.startsWith('wbraid:')) return { type: 'wbraid', value: storedVal.substring(7) };
        if (storedVal.startsWith('gbraid:')) return { type: 'gbraid', value: storedVal.substring(7) };
        return { type: 'fbclid', value: storedVal };
    }

    function getClickId() {
        // Hierarchy 1: URL query parameter
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
                            saveClickId(parsed.type, parsed.value);
                            return parsed;
                        }
                    }
                }
            }
        } catch (e) {}

        return null;
    }

    function decorateLink(link, clickIdObj) {
        if (!link) return;
        try {
            const rawHref = link.getAttribute('href');
            if (!rawHref || !rawHref.includes('tiqets.com')) return;

            const url = new URL(rawHref, window.location.href);
            url.searchParams.set('partner', 'deals.cruisedetective.com');

            if (clickIdObj && clickIdObj.value) {
                const { type, value } = clickIdObj;
                const existingCampaign = url.searchParams.get('tq_campaign') || 'dinner-comparison-bm';
                
                let newCampaign = existingCampaign;
                const match = existingCampaign.match(/--(fbclid|gclid|wbraid|gbraid)-/);
                if (match) {
                    const baseTag = existingCampaign.substring(0, match.index);
                    newCampaign = baseTag ? `${baseTag}--${type}-${value}` : `${type}-${value}`;
                } else {
                    newCampaign = `${existingCampaign}--${type}-${value}`;
                }

                url.searchParams.set('tq_campaign', newCampaign);
                url.searchParams.set(type, value);
                url.searchParams.set('click_id', value);
                url.searchParams.set('subid', `${type}:${value}`);
            }

            link.href = url.toString();
        } catch (e) {
            console.warn('Failed to decorate Tiqets link:', e);
        }
    }

    function scanAndDecorateLinks() {
        const activeClickId = getClickId();
        const links = document.querySelectorAll('a[href*="tiqets.com"]');
        links.forEach(link => decorateLink(link, activeClickId));
    }

    function attachTrackingToButtons() {
        const ctaButtons = document.querySelectorAll('a[href*="tiqets.com"], .cta-button, .table-cta-btn, .btn-sticky-cta');
        ctaButtons.forEach(button => {
            button.addEventListener('click', () => {
                const activeClickId = getClickId();
                if (activeClickId) {
                    decorateLink(button, activeClickId);
                }

                if (typeof window.fbq === 'function') {
                    const text = button.textContent || '';
                    let boatName = 'Bateaux Mouches Romantic Dinner Cruise';
                    let priceVal = 230.00;

                    if (button.href.includes('p974358') || text.includes('Parisiens')) {
                        boatName = 'Bateaux Parisiens Gourmet Dinner Cruise';
                        priceVal = 236.00;
                    } else if (button.href.includes('p1023747') || text.includes('City Vision') || text.includes('Marina')) {
                        boatName = 'Paris City Vision La Marina Dinner Cruise';
                        priceVal = 200.00;
                    } else if (button.href.includes('p1052475') || text.includes('Scène') || text.includes('Scene')) {
                        boatName = 'Paris en Scène Dinner Cruise';
                        priceVal = 138.00;
                    } else if (button.href.includes('p1049009') || text.includes('Diamant')) {
                        boatName = 'Le Diamant Bleu Gourmet Dinner Cruise';
                        priceVal = 218.00;
                    }
                    
                    window.fbq('track', 'InitiateCheckout', {
                        content_name: boatName,
                        content_category: 'Paris Dinner Cruise',
                        currency: 'EUR',
                        value: priceVal
                    });
                }
            });
        });
    }

    // Run link decoration & event tracking
    scanAndDecorateLinks();
    attachTrackingToButtons();

    // -------------------------------------------------------------
    // 2. Dynamic Dates & Year
    // -------------------------------------------------------------
    const dateElement = document.getElementById('dynamic-date');
    const yearElement = document.getElementById('current-year');
    const today = new Date();

    if (yearElement) {
        yearElement.textContent = today.getFullYear();
    }

    if (dateElement) {
        const options = { year: 'numeric', month: 'long', day: 'numeric' };
        dateElement.textContent = today.toLocaleDateString('en-US', options);
    }

    // -------------------------------------------------------------
    // 3. Category Filter Pill Click Handling
    // -------------------------------------------------------------
    const filterPills = document.querySelectorAll('.filter-pill');
    filterPills.forEach(pill => {
        pill.addEventListener('click', (e) => {
            filterPills.forEach(p => p.classList.remove('active'));
            pill.classList.add('active');
        });
    });

    // -------------------------------------------------------------
    // 4. Dynamic Floating Bar: Tracks Current Cruise In View
    // -------------------------------------------------------------
    const stickyBar = document.getElementById('sticky-bar');
    const boatCards = document.querySelectorAll('.boat-card');
    const stickyThumb = document.getElementById('sticky-thumb');
    const stickyRank = document.getElementById('sticky-rank');
    const stickyName = document.getElementById('sticky-name');
    const stickyPrice = document.getElementById('sticky-price');
    const stickyDesc = document.getElementById('sticky-desc');
    const stickyBtn = document.getElementById('sticky-cta-btn');

    let currentActiveBoatId = null;

    function updateFloatingBar() {
        if (!stickyBar || boatCards.length === 0) return;

        const scrollY = window.scrollY;
        // Show only after scrolling past the comparison table (~420px)
        if (scrollY < 420) {
            stickyBar.classList.remove('visible');
            return;
        }

        // Detect which cruise card is currently centered/in reading focus
        const targetLine = window.innerHeight * 0.42;
        let activeCard = null;

        for (let i = 0; i < boatCards.length; i++) {
            const card = boatCards[i];
            const rect = card.getBoundingClientRect();
            if (rect.top <= targetLine && rect.bottom >= targetLine) {
                activeCard = card;
                break;
            }
        }

        // If between cards or at start/end of cards section
        if (!activeCard) {
            for (let i = 0; i < boatCards.length; i++) {
                const card = boatCards[i];
                const rect = card.getBoundingClientRect();
                if (rect.top <= window.innerHeight * 0.75 && rect.bottom > 0) {
                    activeCard = card;
                }
            }
        }

        // Fallback to #1 winner if beyond all cards (e.g. at final verdict)
        if (!activeCard) {
            activeCard = boatCards[0];
        }

        stickyBar.classList.add('visible');

        const boatId = activeCard.dataset.boatId;
        if (boatId && boatId !== currentActiveBoatId) {
            currentActiveBoatId = boatId;

            if (stickyThumb && activeCard.dataset.boatThumb) {
                stickyThumb.src = activeCard.dataset.boatThumb;
            }
            if (stickyRank && activeCard.dataset.boatRank) {
                stickyRank.textContent = activeCard.dataset.boatRank;
                stickyRank.className = `sticky-rank-badge pill-${boatId}`;
            }
            if (stickyName && activeCard.dataset.boatName) {
                stickyName.textContent = activeCard.dataset.boatName;
            }
            if (stickyPrice && activeCard.dataset.boatPrice) {
                stickyPrice.textContent = activeCard.dataset.boatPrice;
            }
            if (stickyDesc && activeCard.dataset.boatDesc) {
                stickyDesc.textContent = activeCard.dataset.boatDesc;
            }
            if (stickyBtn) {
                if (activeCard.dataset.boatBtn) {
                    stickyBtn.textContent = activeCard.dataset.boatBtn;
                }
                if (activeCard.dataset.boatBtnClass) {
                    stickyBtn.className = `btn-sticky-cta ${activeCard.dataset.boatBtnClass}`;
                }
                if (activeCard.dataset.boatUrl) {
                    stickyBtn.href = activeCard.dataset.boatUrl;
                    decorateLink(stickyBtn, getClickId());
                }
            }
        }
    }

    window.addEventListener('scroll', updateFloatingBar, { passive: true });
    window.addEventListener('resize', updateFloatingBar, { passive: true });
    updateFloatingBar();
});
