document.addEventListener('DOMContentLoaded', () => {
    // -------------------------------------------------------------
    // 1. Click ID Capture & Cookie Storage (Meta fbclid / Google gclid)
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

        let campaignTag = 'bateaux-parisiens-de-t2';

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

        const reviewLinks = document.querySelectorAll('.tiqets-review-link');
        reviewLinks.forEach(link => {
            if (!link) return;
            try {
                const u = new URL(link.href);
                let cTag = 'bateaux-parisiens-de-t2-reviews';
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

    // Track button click
    const mainBtn = document.getElementById('main-checkout-btn');
    if (mainBtn) {
        mainBtn.addEventListener('click', () => {
            const avgCommission = 15.08; // Estimated commission on 2 tickets (€36 * 41.9%)
            if (typeof window.fbq === 'function') {
                window.fbq('track', 'InitiateCheckout', {
                    content_name: 'Bateaux Parisiens Seine Rundfahrt Pass (DE)',
                    content_category: 'Paris River Cruise',
                    value: avgCommission,
                    currency: 'EUR',
                    num_items: 2
                });
            }
            if (typeof window.clarity === 'function') {
                window.clarity('event', 'tiqets_outbound_click');
                window.clarity('set', 'checkout_page', 'de-ticket-2-card');
            }
        });
    }

    if (typeof window.clarity === 'function') {
        const sourceType = clickId && clickId.type ? clickId.type : 'direct_or_organic';
        window.clarity('set', 'ad_click_type', sourceType);
    }

    updateCheckoutLinks();
    setTimeout(updateCheckoutLinks, 1500);
});
