document.addEventListener('DOMContentLoaded', () => {
    // -------------------------------------------------------------
    // 1. 10-Photo Interactive Touch Slider & Carousel Engine
    // -------------------------------------------------------------
    const sliderTrack = document.getElementById('slider-track');
    const slides = document.querySelectorAll('#slider-track .slide');
    const prevBtn = document.getElementById('slider-prev');
    const nextBtn = document.getElementById('slider-next');
    const counterPill = document.getElementById('slider-counter');
    const thumbChips = document.querySelectorAll('.thumb-chip');
    const totalSlides = slides.length;
    let currentSlide = 0;
    let autoPlayTimer = null;

    function goToSlide(index) {
        if (index < 0) index = totalSlides - 1;
        if (index >= totalSlides) index = 0;
        currentSlide = index;

        if (sliderTrack) {
            sliderTrack.style.transform = `translateX(-${currentSlide * 100}%)`;
        }

        if (counterPill) {
            counterPill.textContent = `${currentSlide + 1} / ${totalSlides}`;
        }

        thumbChips.forEach((chip, i) => {
            if (i === currentSlide) {
                chip.classList.add('active');
            } else {
                chip.classList.remove('active');
            }
        });

        const thumbStrip = document.getElementById('thumb-strip');
        if (thumbStrip && thumbChips[currentSlide]) {
            const activeChip = thumbChips[currentSlide];
            const targetLeft = activeChip.offsetLeft - (thumbStrip.clientWidth / 2) + (activeChip.clientWidth / 2);
            thumbStrip.scrollTo({ left: Math.max(0, targetLeft), behavior: 'smooth' });
        }
    }

    if (prevBtn) {
        prevBtn.addEventListener('click', () => {
            resetAutoplay();
            goToSlide(currentSlide - 1);
        });
    }

    if (nextBtn) {
        nextBtn.addEventListener('click', () => {
            resetAutoplay();
            goToSlide(currentSlide + 1);
        });
    }

    thumbChips.forEach(chip => {
        chip.addEventListener('click', () => {
            resetAutoplay();
            const idx = parseInt(chip.getAttribute('data-index') || '0', 10);
            goToSlide(idx);
        });
    });

    let startX = 0;
    let startY = 0;
    let currentX = 0;
    let currentY = 0;
    let isSwiping = false;

    if (sliderTrack) {
        sliderTrack.addEventListener('touchstart', (e) => {
            if (e.touches.length > 0) {
                startX = e.touches[0].clientX;
                startY = e.touches[0].clientY;
                currentX = startX;
                currentY = startY;
                isSwiping = true;
                resetAutoplay();
            }
        }, { passive: true });

        sliderTrack.addEventListener('touchmove', (e) => {
            if (!isSwiping || e.touches.length === 0) return;
            currentX = e.touches[0].clientX;
            currentY = e.touches[0].clientY;
        }, { passive: true });

        sliderTrack.addEventListener('touchend', () => {
            if (!isSwiping) return;
            isSwiping = false;
            const diffX = startX - currentX;
            const diffY = startY - currentY;
            if (Math.abs(diffX) > 35 && Math.abs(diffX) > Math.abs(diffY)) {
                if (diffX > 0) {
                    goToSlide(currentSlide + 1);
                } else {
                    goToSlide(currentSlide - 1);
                }
            }
        }, { passive: true });
    }

    function resetAutoplay() {
        if (autoPlayTimer) clearInterval(autoPlayTimer);
        autoPlayTimer = setInterval(() => {
            goToSlide(currentSlide + 1);
        }, 6000);
    }
    resetAutoplay();

    // -------------------------------------------------------------
    // 2. Ticket Counter Logic
    // -------------------------------------------------------------
    let adultCount = 2;
    let childCount = 0;
    let infantCount = 0;

    const ADULT_PRICE = 18.00;
    const CHILD_PRICE = 9.00;

    const valAdults = document.getElementById('val-adults');
    const valChildren = document.getElementById('val-children');
    const valInfants = document.getElementById('val-infants');
    const totalPriceDisplay = document.getElementById('total-price-display');
    const summaryFamilyDesc = document.getElementById('summary-family-desc');
    const mainCheckoutBtn = document.getElementById('main-checkout-btn');
    const stickyPriceDisplay = document.getElementById('sticky-price-display');

    const btnMinusAdult = document.getElementById('btn-minus-adult');
    const btnPlusAdult = document.getElementById('btn-plus-adult');
    const btnMinusChild = document.getElementById('btn-minus-child');
    const btnPlusChild = document.getElementById('btn-plus-child');
    const btnMinusInfant = document.getElementById('btn-minus-infant');
    const btnPlusInfant = document.getElementById('btn-plus-infant');

    function calculateTotal() {
        return (adultCount * ADULT_PRICE) + (childCount * CHILD_PRICE);
    }

    function updateDisplay() {
        if (valAdults) valAdults.textContent = adultCount;
        if (valChildren) valChildren.textContent = childCount;
        if (valInfants) valInfants.textContent = infantCount;

        const total = calculateTotal();
        const formattedTotal = `${total.toFixed(2).replace('.', ',')} €`;

        if (totalPriceDisplay) {
            totalPriceDisplay.textContent = formattedTotal;
        }

        let compParts = [];
        if (adultCount > 0) compParts.push(`${adultCount} Adulte${adultCount > 1 ? 's' : ''}`);
        if (childCount > 0) compParts.push(`${childCount} Enfant${childCount > 1 ? 's' : ''}`);
        if (infantCount > 0) compParts.push(`${infantCount} Bébé${infantCount > 1 ? 's' : ''}`);
        const compText = compParts.join(' + ') || 'Aucun billet';

        if (summaryFamilyDesc) {
            summaryFamilyDesc.textContent = `${compText} • File de caisse évitée`;
        }

        if (valAdults && mainCheckoutBtn) {
            const mainLine = mainCheckoutBtn.querySelector('.btn-line-main');
            if (mainLine) {
                mainLine.textContent = `RÉSERVER MES BILLETS — ${formattedTotal} →`;
            }
        }

        if (valAdults && stickyPriceDisplay) {
            stickyPriceDisplay.textContent = `${formattedTotal} (${compText})`;
        }

        updateCheckoutLinks();
    }

    if (btnMinusAdult) {
        btnMinusAdult.addEventListener('click', () => {
            if (adultCount > 1) {
                adultCount--;
                updateDisplay();
            }
        });
    }

    if (btnPlusAdult) {
        btnPlusAdult.addEventListener('click', () => {
            if (adultCount < 10) {
                adultCount++;
                updateDisplay();
            }
        });
    }

    if (btnMinusChild) {
        btnMinusChild.addEventListener('click', () => {
            if (childCount > 0) {
                childCount--;
                updateDisplay();
            }
        });
    }

    if (btnPlusChild) {
        btnPlusChild.addEventListener('click', () => {
            if (childCount < 10) {
                childCount++;
                updateDisplay();
            }
        });
    }

    if (btnMinusInfant) {
        btnMinusInfant.addEventListener('click', () => {
            if (infantCount > 0) {
                infantCount--;
                updateDisplay();
            }
        });
    }

    if (btnPlusInfant) {
        btnPlusInfant.addEventListener('click', () => {
            if (infantCount < 6) {
                infantCount++;
                updateDisplay();
            }
        });
    }

    // -------------------------------------------------------------
    // 3. Click ID Persistence (Meta fbclid & Google gclid)
    // -------------------------------------------------------------
    const STORAGE_KEY = 'cd_gclid';
    const EXPIRATION_KEY = 'cd_gclid_exp';
    const EXPIRATION_MS = 90 * 24 * 60 * 60 * 1000; // 90 days

    function getCookieDomain() {
        try {
            const host = window.location.hostname;
            if (host === 'localhost' || host === '127.0.0.1') return '';
            const parts = host.split('.');
            if (parts.length >= 2) {
                return '.' + parts.slice(-2).join('.');
            }
            return '';
        } catch (e) {
            return '';
        }
    }

    function saveClickId(type, value) {
        try {
            const now = Date.now();
            if (typeof localStorage !== 'undefined') {
                localStorage.setItem(STORAGE_KEY, `${type}:${value}`);
                localStorage.setItem(EXPIRATION_KEY, (now + EXPIRATION_MS).toString());
            }
            const date = new Date();
            date.setTime(now + EXPIRATION_MS);
            const domain = getCookieDomain();
            const domainAttr = domain ? `;domain=${domain}` : '';
            document.cookie = `${STORAGE_KEY}=${encodeURIComponent(type + ':' + value)};expires=${date.toUTCString()};path=/${domainAttr};SameSite=Lax`;
        } catch (e) {}
    }

    function getClickId() {
        try {
            const urlParams = new URLSearchParams(window.location.search);
            const clickIdParams = ['gclid', 'wbraid', 'gbraid', 'fbclid', 'msclkid', 'ttclid'];
            for (const param of clickIdParams) {
                const val = urlParams.get(param);
                if (val) {
                    saveClickId(param, val);
                    return { type: param, value: val };
                }
            }
        } catch (e) {}

        try {
            if (typeof localStorage !== 'undefined') {
                const stored = localStorage.getItem(STORAGE_KEY);
                const exp = localStorage.getItem(EXPIRATION_KEY);
                if (stored && exp && Date.now() < parseInt(exp, 10)) {
                    const parts = stored.split(':');
                    if (parts.length === 2) return { type: parts[0], value: parts[1] };
                }
            }
        } catch (e) {}

        try {
            if (typeof document !== 'undefined' && document.cookie) {
                const cookies = document.cookie.split(';');
                for (let i = 0; i < cookies.length; i++) {
                    const cookie = cookies[i].trim();
                    if (cookie.startsWith(`${STORAGE_KEY}=`)) {
                        const cookieVal = decodeURIComponent(cookie.substring(STORAGE_KEY.length + 1));
                        if (cookieVal) {
                            const parts = cookieVal.split(':');
                            if (parts.length === 2) {
                                saveClickId(parts[0], parts[1]);
                                return { type: parts[0], value: parts[1] };
                            }
                        }
                    }
                }
            }
        } catch (e) {}

        return null;
    }

    // -------------------------------------------------------------
    // 4. Dynamic URL Decoration & Conversion Tracking
    // -------------------------------------------------------------
    const clickId = getClickId();
    const BASE_TIQETS_URL = 'https://www.tiqets.com/fr/activites-attractions-paris-c66746/billets-pour-seine-croisiere-en-bateaux-parisiens-p973977/';
    const PARTNER_ID = 'deals.cruisedetective.com';

    function getFbpCookie() {
        try {
            const m = document.cookie.match(/(?:^|;\s*)_fbp=([^;]+)/);
            return m ? decodeURIComponent(m[1]).trim() : '';
        } catch (e) {
            return '';
        }
    }

    function updateCheckoutLinks() {
        const fbpVal = getFbpCookie();

        const targetLinks = [
            document.getElementById('main-checkout-btn'),
            document.getElementById('secondary-checkout-btn'),
            document.getElementById('sticky-checkout-btn')
        ];

        targetLinks.forEach(link => {
            if (!link) return;

            let campaignTag = 'bateaux-parisiens-fr-t1';
            if (link.id.includes('bottom') || link.id.includes('secondary')) {
                campaignTag = 'bateaux-parisiens-fr-t1-bottom';
            } else if (link.id.includes('sticky')) {
                campaignTag = 'bateaux-parisiens-fr-t1-sticky';
            }

            if (clickId && clickId.value) {
                campaignTag += `--${clickId.type}-${clickId.value}`;
            }
            if (fbpVal) {
                campaignTag += `--fbp-${fbpVal}`;
            }

            const url = new URL(BASE_TIQETS_URL);
            url.searchParams.set('partner', PARTNER_ID);
            url.searchParams.set('tq_campaign', campaignTag);

            if (clickId && clickId.value) {
                url.searchParams.set(clickId.type, clickId.value);
                url.searchParams.set('click_id', clickId.value);
                url.searchParams.set('subid', `${clickId.type}:${clickId.value}`);
            }

            link.href = url.toString();
        });

        const reviewLinks = document.querySelectorAll('.tiqets-review-link');
        reviewLinks.forEach(link => {
            if (!link) return;
            try {
                const u = new URL(link.href);
                let cTag = 'bateaux-parisiens-fr-t1-reviews';
                if (clickId && clickId.value) cTag += `--${clickId.type}-${clickId.value}`;
                if (fbpVal) cTag += `--fbp-${fbpVal}`;
                u.searchParams.set('tq_campaign', cTag);
                if (clickId && clickId.value) {
                    u.searchParams.set(clickId.type, clickId.value);
                    u.searchParams.set('click_id', clickId.value);
                    u.searchParams.set('subid', `${clickId.type}:${clickId.value}`);
                }
                link.href = u.toString();
            } catch(e) {}
        });
    }

    // Attach Meta Pixel InitiateCheckout + Microsoft Clarity Custom Events on CTA click
    document.addEventListener('click', (e) => {
        const targetBtn = e.target.closest('#main-checkout-btn, #secondary-checkout-btn, #sticky-checkout-btn');
        if (targetBtn) {
            const total = calculateTotal();
            const totalTickets = adultCount + childCount + infantCount;
            const netCommission = Math.round(total * 0.419 * 100) / 100;
            if (typeof window.fbq === 'function') {
                window.fbq('track', 'InitiateCheckout', {
                    content_name: 'Bateaux Parisiens Croisière Seine Pass (FR)',
                    content_category: 'Paris River Cruise',
                    value: netCommission,
                    currency: 'EUR',
                    num_items: totalTickets
                });
            }
            if (typeof window.clarity === 'function') {
                window.clarity('event', 'tiqets_outbound_click');
                window.clarity('set', 'checkout_button', targetBtn.id);
                window.clarity('set', 'basket_composition', `${adultCount}A_${childCount}C_${infantCount}I`);
                window.clarity('set', 'basket_eur', total.toFixed(2));
            }
        }
    });

    if (typeof window.clarity === 'function') {
        const sourceType = clickId && clickId.type ? clickId.type : 'direct_or_organic';
        window.clarity('set', 'ad_click_type', sourceType);
    }

    const stickyBar = document.getElementById('sticky-bar');
    if (stickyBar) {
        stickyBar.style.transform = 'translateY(0)';
        stickyBar.style.opacity = '1';
        stickyBar.style.pointerEvents = 'auto';
    }

    updateDisplay();
    setTimeout(updateCheckoutLinks, 1500);
});
