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

    // Touch Swipe Support (Mobile)
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
        });
    }

    function startAutoplay() {
        if (autoPlayTimer) clearInterval(autoPlayTimer);
        autoPlayTimer = setInterval(() => {
            goToSlide(currentSlide + 1);
        }, 5000);
    }

    function resetAutoplay() {
        if (autoPlayTimer) clearInterval(autoPlayTimer);
        startAutoplay();
    }

    startAutoplay();

    // -------------------------------------------------------------
    // 2. Interactive Package Selector & Guest Calculator
    // -------------------------------------------------------------
    const PACKAGE_PRICES = {
        prestige: { price: 135.00, name: 'Prestige Dinner (20:30)', desc: 'Prestige 3-Course Dinner • Pont de l\'Alma' },
        excellence: { price: 170.00, name: 'Excellence VIP Window (20:30)', desc: 'Excellence Window Table • Pont de l\'Alma' },
        early: { price: 114.00, name: 'Early Sunset (18:00)', desc: 'Early Sunset 3-Course • Pont de l\'Alma' }
    };
    const CHILD_PRICE = 45.00;

    let selectedTier = 'prestige';
    let adultCount = 2; // Default to couple (98% of buyers)
    let childCount = 0;

    const packageOptions = document.querySelectorAll('.package-option');
    const valAdults = document.getElementById('val-adults');
    const valChildren = document.getElementById('val-children');
    const widgetPerPersonPrice = document.getElementById('widget-per-person-price');
    const ticketPriceLabel = document.getElementById('ticket-price-label');
    const totalPriceDisplay = document.getElementById('total-price-display');
    const summaryTierDesc = document.getElementById('summary-tier-desc');
    const stickyPriceDisplay = document.getElementById('sticky-price-display');
    const mainCheckoutBtn = document.getElementById('main-checkout-btn');

    const btnMinusAdult = document.getElementById('btn-minus-adult');
    const btnPlusAdult = document.getElementById('btn-plus-adult');
    const btnMinusChild = document.getElementById('btn-minus-child');
    const btnPlusChild = document.getElementById('btn-plus-child');

    function getAdultPrice() {
        return PACKAGE_PRICES[selectedTier] ? PACKAGE_PRICES[selectedTier].price : 135.00;
    }

    function calculateTotal() {
        return (adultCount * getAdultPrice()) + (childCount * CHILD_PRICE);
    }

    function updateDisplay() {
        const adultPrice = getAdultPrice();
        const total = calculateTotal();
        const formattedTotal = `€${total.toFixed(2)}`;
        const formattedPerPerson = `€${adultPrice.toFixed(2)}`;

        if (widgetPerPersonPrice) widgetPerPersonPrice.textContent = formattedPerPerson;
        if (ticketPriceLabel) ticketPriceLabel.textContent = `${formattedPerPerson} / guest`;
        if (valAdults) valAdults.textContent = adultCount.toString();
        if (valChildren) valChildren.textContent = childCount.toString();
        if (totalPriceDisplay) totalPriceDisplay.textContent = formattedTotal;

        const tierInfo = PACKAGE_PRICES[selectedTier] || PACKAGE_PRICES.prestige;
        let guestDesc = `${adultCount} Adult${adultCount > 1 ? 's' : ''}`;
        if (childCount > 0) {
            guestDesc += `, ${childCount} Child${childCount > 1 ? 'ren' : ''}`;
        }

        if (summaryTierDesc) {
            summaryTierDesc.textContent = `${guestDesc} • ${tierInfo.desc}`;
        }

        // Update button text
        if (mainCheckoutBtn) {
            const mainLine = mainCheckoutBtn.querySelector('.btn-line-main');
            if (mainLine) {
                mainLine.textContent = `RESERVE DINNER TABLE — ${formattedTotal} →`;
            }
        }

        // Update sticky footer
        if (stickyPriceDisplay) {
            stickyPriceDisplay.textContent = `${formattedTotal} (${guestDesc})`;
        }

        updateCheckoutLinks();
    }

    // Package Selector Event Handlers
    packageOptions.forEach(opt => {
        opt.addEventListener('click', () => {
            packageOptions.forEach(o => o.classList.remove('active'));
            opt.classList.add('active');
            const radio = opt.querySelector('input[type="radio"]');
            if (radio) radio.checked = true;
            selectedTier = opt.getAttribute('data-tier') || 'prestige';
            updateDisplay();
        });
    });

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

    // -------------------------------------------------------------
    // 3. Click ID Persistence (Meta fbclid & Google gclid)
    // -------------------------------------------------------------
    const STORAGE_KEY = 'cd_gclid';
    const EXPIRATION_KEY = 'cd_gclid_exp';
    const EXPIRATION_MS = 90 * 24 * 60 * 60 * 1000;

    function getCookieDomain() {
        try {
            const host = window.location.hostname;
            if (host.endsWith('thecruisedetective.com')) {
                return '; domain=.thecruisedetective.com';
            }
        } catch (e) {}
        return '';
    }

    function saveClickId(type, value) {
        if (!value || typeof value !== 'string') return;
        const cleanVal = value.trim();
        if (!cleanVal) return;

        const payload = `${type}:${cleanVal}`;
        const expTime = Date.now() + EXPIRATION_MS;

        try {
            localStorage.setItem(STORAGE_KEY, payload);
            localStorage.setItem(EXPIRATION_KEY, expTime.toString());
        } catch (e) {}

        try {
            document.cookie = `${STORAGE_KEY}=${encodeURIComponent(payload)}; max-age=${90 * 24 * 60 * 60}; path=/${getCookieDomain()}; SameSite=Lax`;
        } catch (e) {}
    }

    function getClickId() {
        // 1. From URL
        try {
            const params = new URLSearchParams(window.location.search);
            for (const key of ['fbclid', 'gclid', 'wbraid', 'gbraid']) {
                const val = params.get(key);
                if (val && val.trim()) {
                    saveClickId(key, val.trim());
                    return { type: key, value: val.trim() };
                }
            }
        } catch (e) {}

        // 2. From localStorage
        try {
            const localVal = localStorage.getItem(STORAGE_KEY);
            const exp = localStorage.getItem(EXPIRATION_KEY);
            if (localVal && (!exp || Date.now() < parseInt(exp, 10))) {
                const parts = localVal.split(':');
                if (parts.length === 2) return { type: parts[0], value: parts[1] };
            }
        } catch (e) {}

        // 3. From cookie
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

    function getFbpCookie() {
        try {
            const m = document.cookie.match(/(?:^|;\s*)_fbp=([^;]+)/);
            return m ? decodeURIComponent(m[1]).trim() : '';
        } catch (e) {
            return '';
        }
    }

    // -------------------------------------------------------------
    // 4. Dynamic URL Decoration & Conversion Tracking
    // -------------------------------------------------------------
    const clickId = getClickId();
    const BASE_TIQETS_URL = 'https://www.tiqets.com/checkout/tickets-for-dinner-cruise-by-bateaux-mouches-p982924/booking_details/';
    const PARTNER_ID = 'thecruisedetective.com-176436';

    function updateCheckoutLinks() {
        const total = calculateTotal();
        const totalTickets = adultCount + childCount;
        const fbpVal = getFbpCookie();

        const targetLinks = [
            document.getElementById('main-checkout-btn'),
            document.getElementById('secondary-checkout-btn'),
            document.getElementById('sticky-checkout-btn')
        ];

        targetLinks.forEach(link => {
            if (!link) return;

            let campaignTag = `bm-dinner-${selectedTier}`;
            if (link.id.includes('bottom') || link.id.includes('secondary')) {
                campaignTag += '-bottom';
            } else if (link.id.includes('sticky')) {
                campaignTag += '-sticky';
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
    }

    // Attach Meta Pixel InitiateCheckout on CTA click
    document.addEventListener('click', (e) => {
        const targetBtn = e.target.closest('#main-checkout-btn, #secondary-checkout-btn, #sticky-checkout-btn');
        if (targetBtn) {
            const total = calculateTotal();
            const totalTickets = adultCount + childCount;
            // Tiqets commission on Bateaux Mouches Dinner averages ~€59.45 / order (approx 16.5% - 20% net)
            const netCommission = Math.round(total * 0.165 * 100) / 100;

            if (typeof window.fbq === 'function') {
                window.fbq('track', 'InitiateCheckout', {
                    content_name: `Bateaux Mouches Dinner Cruise (${selectedTier})`,
                    content_category: 'Paris Dinner River Cruise',
                    value: netCommission,
                    currency: 'EUR',
                    num_items: totalTickets
                });
            }
            if (typeof window.clarity === 'function') {
                window.clarity('event', 'tiqets_outbound_click');
                window.clarity('set', 'dinner_tier', selectedTier);
                window.clarity('set', 'checkout_button', targetBtn.id);
                window.clarity('set', 'basket_eur', total.toFixed(2));
            }
        }
    });

    if (typeof window.clarity === 'function') {
        const sourceType = clickId && clickId.type ? clickId.type : 'direct_or_organic';
        window.clarity('set', 'ad_click_type', sourceType);
        window.clarity('set', 'product_view', 'bateaux_mouches_dinner_982924');
    }

    // -------------------------------------------------------------
    // 5. Sticky Bottom Bar Scroll Visibility Handler
    // -------------------------------------------------------------
    const stickyBar = document.getElementById('sticky-bar');
    const mainBtn = document.getElementById('main-checkout-btn');

    if (stickyBar && mainBtn) {
        window.addEventListener('scroll', () => {
            const rect = mainBtn.getBoundingClientRect();
            if (rect.bottom < 0) {
                stickyBar.style.transform = 'translateY(0)';
                stickyBar.style.opacity = '1';
                stickyBar.style.pointerEvents = 'auto';
            } else {
                stickyBar.style.transform = 'translateY(100%)';
                stickyBar.style.opacity = '0';
                stickyBar.style.pointerEvents = 'none';
            }
        }, { passive: true });

        stickyBar.style.transition = 'transform 0.25s ease, opacity 0.25s ease';
        stickyBar.style.transform = 'translateY(100%)';
        stickyBar.style.opacity = '0';
        stickyBar.style.pointerEvents = 'none';
    }

    // Initial run + delayed re-run after async Meta Pixel sets _fbp cookie
    updateDisplay();
    setTimeout(updateCheckoutLinks, 1500);
});