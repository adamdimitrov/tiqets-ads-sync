document.addEventListener('DOMContentLoaded', () => {
    // -------------------------------------------------------------
    // 1. Click ID Capture & Cookie Storage (Meta fbclid / Google gclid)
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
        const mainBtn = document.getElementById('main-checkout-btn');

        if (!mainBtn) return;

        let campaignTag = 'couples-pass-bridge';

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

        mainBtn.href = url.toString();
    }

    // Track Outbound Click on Button
    document.addEventListener('click', (e) => {
        const targetBtn = e.target.closest('#main-checkout-btn');
        if (targetBtn) {
            // Standard couples basket proxy: 2 adults (€36), net commission = €15.08
            const netCommission = 15.08;

            if (typeof window.fbq === 'function') {
                window.fbq('track', 'InitiateCheckout', {
                    content_name: 'The Eiffel Tower Couples Pass (Bateaux Parisiens)',
                    content_category: 'Couples River Cruise',
                    value: netCommission,
                    currency: 'EUR',
                    num_items: 2
                });
            }

            if (typeof window.clarity === 'function') {
                window.clarity('event', 'tiqets_bridge_click');
                window.clarity('set', 'checkout_button', targetBtn.id);
                window.clarity('set', 'bridge_angle', 'couples_pass');
            }
        }
    });

    if (typeof window.clarity === 'function') {
        const sourceType = clickId && clickId.type ? clickId.type : 'direct_or_organic';
        window.clarity('set', 'ad_click_type', sourceType);
    }

    // Initialize Links
    updateCheckoutLinks();
    setTimeout(updateCheckoutLinks, 1500);
});
