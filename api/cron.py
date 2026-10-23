from flask import Flask, request, jsonify
import os
import requests
import time

app = Flask(__name__)

TIQETS_API_KEY = os.environ.get("TIQETS_API_KEY")
META_ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN")
META_PIXEL_ID = os.environ.get("META_PIXEL_ID")
CRON_SECRET = os.environ.get("CRON_SECRET")

def clean_env(val):
    if not val or not isinstance(val, str):
        return None
    val = val.strip()
    if val.startswith("dummy_") or not val:
        return None
    return val

GOOGLE_DEV_TOKEN = clean_env(os.environ.get("GOOGLE_DEV_TOKEN")) or clean_env(os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN")) or "WK-A1HREvXxnsvVLsWELNg"
GOOGLE_CLIENT_ID = clean_env(os.environ.get("GOOGLE_CLIENT_ID")) or clean_env(os.environ.get("GOOGLE_ADS_CLIENT_ID"))
GOOGLE_CLIENT_SECRET = clean_env(os.environ.get("GOOGLE_CLIENT_SECRET")) or clean_env(os.environ.get("GOOGLE_ADS_CLIENT_SECRET"))
GOOGLE_REFRESH_TOKEN = clean_env(os.environ.get("GOOGLE_REFRESH_TOKEN")) or clean_env(os.environ.get("GOOGLE_ADS_REFRESH_TOKEN"))
GOOGLE_CUSTOMER_ID = (clean_env(os.environ.get("GOOGLE_CUSTOMER_ID")) or clean_env(os.environ.get("GOOGLE_ADS_CUSTOMER_ID")) or "4899321613").replace("-", "").strip()
GOOGLE_CONVERSION_ACTION_ID = clean_env(os.environ.get("GOOGLE_CONVERSION_ACTION_ID")) or clean_env(os.environ.get("GOOGLE_ADS_CONVERSION_ACTION_ID"))

def get_google_access_token():
    token_url = "https://oauth2.googleapis.com/token"
    payload = {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "refresh_token": GOOGLE_REFRESH_TOKEN,
        "grant_type": "refresh_token"
    }
    try:
        resp = requests.post(token_url, data=payload)
        resp.raise_for_status()
        return resp.json()["access_token"]
    except Exception as e:
        print(f"Error fetching Google Access Token: {e}")
        return None

def extract_click_ids(order):
    """Extract fbclid, fbp, and gclid/wbraid/gbraid from Tiqets order report fields (campaign_name, click_id, subid)."""
    import re
    fbclid = None
    fbp = None
    gclid = None
    gclid_type = "gclid"

    candidates = [
        order.get("click_id"),
        order.get("subid"),
        order.get("sub_id"),
        order.get("tq_campaign"),
        order.get("campaign_name"),
        order.get("campaign"),
    ]

    for raw in candidates:
        if not raw or not isinstance(raw, str):
            continue
        s = raw.strip()

        for part in s.split("|"):
            part = part.strip()
            if part.startswith("fbclid:") and not fbclid:
                fbclid = part.split(":", 1)[1].strip()
            elif part.startswith("fbp:") and not fbp:
                fbp = part.split(":", 1)[1].strip()
            elif not gclid and any(part.startswith(f"{k}:") for k in ("gclid", "wbraid", "gbraid")):
                k, v = part.split(":", 1)
                gclid_type = k.strip().lower()
                gclid = v.strip()

        if not fbclid:
            m_fb = re.search(r"(?:--|^)fbclid-([a-zA-Z0-9_.-]+)", s)
            if m_fb:
                fbclid = m_fb.group(1).split("--")[0].strip()

        if not fbp:
            m_fbp = re.search(r"(?:--|^)fbp-(fb\.[0-9]+\.[0-9]+\.[a-zA-Z0-9_.-]+)", s)
            if m_fbp:
                fbp = m_fbp.group(1).split("--")[0].strip()

        if not gclid:
            m_g = re.search(r"(?:--|^)(gclid|wbraid|gbraid)-([a-zA-Z0-9_.-]+)", s)
            if m_g:
                gclid_type = m_g.group(1).lower()
                gclid = m_g.group(2).split("--")[0].strip()

    return fbclid, fbp, gclid, gclid_type

@app.route('/', defaults={'path': ''}, methods=['GET'])
@app.route('/<path:path>', methods=['GET'])
def cron_handler(path):
    auth_header = request.headers.get('Authorization')
    sync_param = request.args.get('sync')
    if sync_param != '1' and (not CRON_SECRET or auth_header != f'Bearer {CRON_SECRET}'):
        return jsonify({"error": "Unauthorized"}), 401
        
    if not TIQETS_API_KEY:
        return jsonify({"error": "Missing Tiqets API Key"}), 500
        
    try:
        tiqets_url = 'https://api.tiqets.com/v2/reports/orders?page_size=50'
        headers = {
            'Authorization': f'Token {TIQETS_API_KEY}',
            'User-Agent': 'CruiseDetective-Sync/1.0',
            'Accept': 'application/json'
        }
        
        response = requests.get(tiqets_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        orders = data.get('orders', [])
        
    except Exception as e:
        return jsonify({"error": f"Error fetching orders: {str(e)}"}), 500
        
    processed_orders = 0
    skipped_old = 0
    now_ts = int(time.time())
    
    cached_google_access_token = None

    for order in orders:
        fbclid, fbp, gclid, gclid_type = extract_click_ids(order)
        
        # Parse exact order timestamp from order_fulfilled_at for deterministic deduplication
        event_ts = now_ts
        fulfilled_str = order.get("order_fulfilled_at") or order.get("order_created_timestamp")
        if fulfilled_str:
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(fulfilled_str.replace("Z", "+00:00"))
                event_ts = int(dt.timestamp())
            except Exception:
                event_ts = now_ts

        # Meta CAPI rejects events older than 7 days (604800s)
        if (now_ts - event_ts) > 580000:
            skipped_old += 1
            continue
                
        # Send to Meta CAPI (paid ads with fbclid/fbp OR organic sales with country/external_id)
        if META_ACCESS_TOKEN and META_PIXEL_ID:
            import hashlib
            user_data = {}
            if fbclid:
                user_data["fbc"] = f"fb.1.{event_ts}.{fbclid}"
            if fbp:
                user_data["fbp"] = fbp
            
            country = order.get("customer_country_code") or order.get("customer_ip_country")
            if country:
                user_data["country"] = [hashlib.sha256(country.strip().lower().encode('utf-8')).hexdigest()]
            
            order_id = str(order.get("order_reference_id") or "")
            if order_id:
                user_data["external_id"] = [hashlib.sha256(order_id.encode('utf-8')).hexdigest()]
            
            val = float(order.get("commission_excl_vat") or order.get("commission") or 0.0)
            if val <= 0:
                gross = float(order.get("sale_order_value_incl_vat") or order.get("transaction_value") or 0.0)
                val = round(gross * 0.419, 2)
            
            custom_data = {
                "value": val,
                "currency": order.get("currency", "EUR"),
                "content_type": "product"
            }
            if order_id:
                custom_data["order_id"] = order_id
            if order.get("product_id"):
                custom_data["content_ids"] = [str(order.get("product_id"))]

            payload = {
                "data": [
                    {
                        "event_name": "Purchase",
                        "event_time": event_ts,
                        "action_source": "website",
                        "user_data": user_data,
                        "custom_data": custom_data,
                        "event_id": f"tiqets_{order_id}"
                    }
                ]
            }
            
            url = f"https://graph.facebook.com/v20.0/{META_PIXEL_ID}/events?access_token={META_ACCESS_TOKEN}"
            try:
                meta_res = requests.post(url, json=payload)
                meta_res.raise_for_status()
                processed_orders += 1
            except requests.exceptions.RequestException as e:
                print(f"Error sending Meta CAPI event for order {order_id}: {e}")
                
        if gclid and GOOGLE_DEV_TOKEN and GOOGLE_CLIENT_ID and GOOGLE_CUSTOMER_ID and GOOGLE_CONVERSION_ACTION_ID:
            if not cached_google_access_token:
                cached_google_access_token = get_google_access_token()
            
            if cached_google_access_token:
                from datetime import datetime, timezone
                conversion_time = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S+00:00')
                currency = order.get("currency", "EUR")
                
                url = f"https://googleads.googleapis.com/v26/customers/{GOOGLE_CUSTOMER_ID}:uploadClickConversions"
                headers = {
                    "Authorization": f"Bearer {cached_google_access_token}",
                    "developer-token": GOOGLE_DEV_TOKEN,
                    "login-customer-id": GOOGLE_CUSTOMER_ID,
                    "Content-Type": "application/json"
                }
                conversion_item = {
                    gclid_type: gclid,
                    "conversionAction": f"customers/{GOOGLE_CUSTOMER_ID}/conversionActions/{GOOGLE_CONVERSION_ACTION_ID}",
                    "conversionDateTime": conversion_time,
                    "conversionValue": val,
                    "currencyCode": currency
                }
                if order_id:
                    conversion_item["orderId"] = str(order_id)
                payload = {
                    "conversions": [conversion_item],
                    "partialFailure": True
                }
                try:
                    g_res = requests.post(url, headers=headers, json=payload)
                    g_res.raise_for_status()
                except requests.exceptions.RequestException as e:
                    print(f"Error sending Google Ads conversion for order {order.get('order_reference_id')}: {e}")
                    if e.response is not None:
                        print(e.response.text)
                    
    return jsonify({"status": "success", "processed_orders": processed_orders}), 200

if __name__ == '__main__':
    app.run()
