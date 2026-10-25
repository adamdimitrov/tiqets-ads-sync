document.addEventListener('DOMContentLoaded', () => {
    // -------------------------------------------------------------
    // 1. Click ID Capture & Storage (Meta fbclid / Google gclid)
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
    // 2. Dynamic URL Decoration & Conversion Tracking
    // -------------------------------------------------------------
    const clickId = getClickId();
    const BASE_TIQETS_URL = 'https://www.tiqets.com/things-to-do-in-paris-c66746/tickets-for-sightseeing-cruise-on-the-seine-p973977';
    const PARTNER_ID = 'deals.cruisedetective.com';

    function updateCheckoutLinks() {
        const fbpVal = getFbpCookie();
        const targetLinks = [
            document.getElementById('main-checkout-btn'),
            document.getElementById('sticky-checkout-btn')
        ];

        targetLinks.forEach(link => {
            if (!link) return;

            let campaignTag = 'family-compare-bridge';
            if (link.id.includes('sticky')) {
                campaignTag = 'family-compare-sticky';
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
        const targetBtn = e.target.closest('#main-checkout-btn, #sticky-checkout-btn');
        if (targetBtn) {
            // Standard family basket proxy: 2 adults (€36) + 2 kids (€18) = €54, net commission = €22.63
            const netCommission = 22.63;

            if (typeof window.fbq === 'function') {
                window.fbq('track', 'InitiateCheckout', {
                    content_name: 'Bateaux Parisiens Family Compare Bridge',
                    content_category: 'Family River Cruise',
                    value: netCommission,
                    currency: 'EUR',
                    num_items: 4
                });
            }

            if (typeof window.clarity === 'function') {
                window.clarity('event', 'tiqets_compare_click');
                window.clarity('set', 'checkout_button', targetBtn.id);
                window.clarity('set', 'bridge_angle', 'box_office_vs_pass');
            }
        }
    });

    if (typeof window.clarity === 'function') {
        const sourceType = clickId && clickId.type ? clickId.type : 'direct_or_organic';
        window.clarity('set', 'ad_click_type', sourceType);
    }

    // -------------------------------------------------------------
    // 3. Mobile Sticky Bottom Bar (Always Active on Mobile)
    // -------------------------------------------------------------
    const stickyBar = document.getElementById('sticky-bar');
    if (stickyBar) {
        stickyBar.style.transform = 'translateY(0)';
        stickyBar.style.opacity = '1';
        stickyBar.style.pointerEvents = 'auto';
    }

    // Initialize Links
    updateCheckoutLinks();
    setTimeout(updateCheckoutLinks, 1500);
});
