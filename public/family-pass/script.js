document.addEventListener('DOMContentLoaded', () => {
    // -------------------------------------------------------------
    // 1. Ticket Calculator State & Event Handlers
    // -------------------------------------------------------------
    const ADULT_PRICE = 18.00;
    const CHILD_PRICE = 9.00;
    const INFANT_PRICE = 0.00;

    let adultCount = 2;
    let childCount = 2;
    let infantCount = 0;

    const displayAdults = document.getElementById('display-adults');
    const displayChildren = document.getElementById('display-children');
    const displayInfants = document.getElementById('display-infants');

    const minusAdult = document.getElementById('minus-adult');
    const plusAdult = document.getElementById('plus-adult');
    const minusChild = document.getElementById('minus-child');
    const plusChild = document.getElementById('plus-child');
    const minusInfant = document.getElementById('minus-infant');
    const plusInfant = document.getElementById('plus-infant');

    const totalPriceAmount = document.getElementById('total-price-amount');
    const basketDesc = document.getElementById('basket-composition-text');
    const btnCalcText = document.getElementById('btn-calc-text');
    const stickyPriceDisplay = document.getElementById('sticky-price-display');

    function calculateTotal() {
        return (adultCount * ADULT_PRICE) + (childCount * CHILD_PRICE) + (infantCount * INFANT_PRICE);
    }

    function updateCalculator() {
        if (displayAdults) displayAdults.textContent = adultCount;
        if (displayChildren) displayChildren.textContent = childCount;
        if (displayInfants) displayInfants.textContent = infantCount;

        const total = calculateTotal();
        const formattedTotal = `€${total.toFixed(2)}`;

        if (totalPriceAmount) {
            totalPriceAmount.textContent = formattedTotal;
        }

        if (btnCalcText) {
            btnCalcText.textContent = `RESERVE FAMILY TICKETS — ${formattedTotal} →`;
        }

        if (basketDesc) {
            const parts = [];
            if (adultCount > 0) parts.push(`${adultCount} ${adultCount === 1 ? 'Adult' : 'Adults'}`);
            if (childCount > 0) parts.push(`${childCount} ${childCount === 1 ? 'Child' : 'Children'}`);
            if (infantCount > 0) parts.push(`${infantCount} ${infantCount === 1 ? 'Infant' : 'Infants'}`);
            basketDesc.textContent = `${parts.join(' + ')} • Dock Line Bypassed`;
        }

        if (stickyPriceDisplay) {
            stickyPriceDisplay.textContent = `Family Pass: ${formattedTotal} • Skip Line`;
        }

        updateCheckoutLinks();
    }

    if (minusAdult) {
        minusAdult.addEventListener('click', () => {
            if (adultCount > 1) {
                adultCount--;
                updateCalculator();
            }
        });
    }

    if (plusAdult) {
        plusAdult.addEventListener('click', () => {
            if (adultCount < 10) {
                adultCount++;
                updateCalculator();
            }
        });
    }

    if (minusChild) {
        minusChild.addEventListener('click', () => {
            if (childCount > 0) {
                childCount--;
                updateCalculator();
            }
        });
    }

    if (plusChild) {
        plusChild.addEventListener('click', () => {
            if (childCount < 10) {
                childCount++;
                updateCalculator();
            }
        });
    }

    if (minusInfant) {
        minusInfant.addEventListener('click', () => {
            if (infantCount > 0) {
                infantCount--;
                updateCalculator();
            }
        });
    }

    if (plusInfant) {
        plusInfant.addEventListener('click', () => {
            if (infantCount < 6) {
                infantCount++;
                updateCalculator();
            }
        });
    }

    // -------------------------------------------------------------
    // 2. Click ID Capture & Cookie Storage (Meta fbclid / Google gclid)
    // -------------------------------------------------------------
    const STORAGE_KEY = 'cd_gclid';

    function saveClickId(type, value) {
        try {
            if (typeof localStorage !== 'undefined') {
                localStorage.setItem(STORAGE_KEY, `${type}:${value}`);
            }
            const date = new Date();
            date.setTime(date.getTime() + (90 * 24 * 60 * 60 * 1000));
            document.cookie = `${STORAGE_KEY}=${encodeURIComponent(type + ':' + value)};expires=${date.toUTCString()};path=/;SameSite=Lax`;
        } catch (e) {}
    }

    function getClickId() {
        try {
            const urlParams = new URLSearchParams(window.location.search);
            const clickIdParams = ['fbclid', 'gclid', 'msclkid', 'ttclid'];
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
                if (stored) {
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

    function getFbpCookie() {
        try {
            const m = document.cookie.match(/(?:^|;\s*)_fbp=([^;]+)/);
            return m ? decodeURIComponent(m[1]).trim() : '';
        } catch (e) {
            return '';
        }
    }

    // -------------------------------------------------------------
    // 3. Dynamic URL Decoration & Conversion Tracking
    // -------------------------------------------------------------
    const clickId = getClickId();
    const BASE_TIQETS_URL = 'https://www.tiqets.com/checkout/tickets-for-seine-river-cruise-by-bateaux-parisiens-p973977/booking_details/';
    const PARTNER_ID = 'thecruisedetective.com-176436';

    function updateCheckoutLinks() {
        const fbpVal = getFbpCookie();

        const targetLinks = [
            document.getElementById('main-checkout-btn'),
            document.getElementById('secondary-checkout-btn'),
            document.getElementById('sticky-checkout-btn')
        ];

        targetLinks.forEach(link => {
            if (!link) return;

            let campaignTag = 'family-pass-bp-top';
            if (link.id.includes('secondary')) {
                campaignTag = 'family-pass-bp-mid';
            } else if (link.id.includes('sticky')) {
                campaignTag = 'family-pass-bp-sticky';
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

    // Track Outbound Click on Buttons
    document.addEventListener('click', (e) => {
        const targetBtn = e.target.closest('#main-checkout-btn, #secondary-checkout-btn, #sticky-checkout-btn');
        if (targetBtn) {
            const total = calculateTotal();
            const totalTickets = adultCount + childCount + infantCount;
            const netCommission = Math.round(total * 0.419 * 100) / 100;

            if (typeof window.fbq === 'function') {
                window.fbq('track', 'InitiateCheckout', {
                    content_name: 'Paris Family Seine Cruise Pass (Bateaux Parisiens)',
                    content_category: 'Family River Cruise',
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

    // -------------------------------------------------------------
    // 4. Sticky Bottom Bar Scroll Visibility Handler
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
    }

    // Initialize Calculator & Links
    updateCalculator();
    setTimeout(updateCheckoutLinks, 1500);
});
