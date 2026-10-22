from flask import Flask, request, jsonify, send_from_directory
import os
import requests
import time

app = Flask(__name__)

TIQETS_API_KEY = os.environ.get("TIQETS_API_KEY")
META_ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN")
META_PIXEL_ID = os.environ.get("META_PIXEL_ID")
GOOGLE_DEV_TOKEN = os.environ.get("GOOGLE_DEV_TOKEN") or os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN") or "WK-A1HREvXxnsvVLsWELNg"
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID") or os.environ.get("GOOGLE_ADS_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET") or os.environ.get("GOOGLE_ADS_CLIENT_SECRET")
GOOGLE_REFRESH_TOKEN = os.environ.get("GOOGLE_REFRESH_TOKEN") or os.environ.get("GOOGLE_ADS_REFRESH_TOKEN")
GOOGLE_CUSTOMER_ID = (os.environ.get("GOOGLE_CUSTOMER_ID") or os.environ.get("GOOGLE_ADS_CUSTOMER_ID") or "4899321613").replace("-", "").strip()
GOOGLE_CONVERSION_ACTION_ID = os.environ.get("GOOGLE_CONVERSION_ACTION_ID") or os.environ.get("GOOGLE_ADS_CONVERSION_ACTION_ID")

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
        return resp.json().get("access_token"), None
    except Exception as e:
        err_detail = resp.text if ('resp' in locals() and hasattr(resp, 'text') and resp is not None) else str(e)
        return None, err_detail
        print(f"Error fetching Google Access Token: {e}")
        return None

def extract_click_ids(data):
    """Extract fbclid and gclid from all possible Tiqets webhook/order fields."""
    import re
    fbclid = None
    gclid = None

    # 1. Direct fields
    if isinstance(data.get("fbclid"), str) and data.get("fbclid").strip():
        fbclid = data.get("fbclid").strip()
    for g_key in ("gclid", "wbraid", "gbraid"):
        if isinstance(data.get(g_key), str) and data.get(g_key).strip():
            gclid = data.get(g_key).strip()
            break

    # 2. Candidate strings (subid, click_id, tq_campaign, campaign_name, campaign)
    candidates = [
        data.get("subid"),
        data.get("sub_id"),
        data.get("click_id"),
        data.get("tq_campaign"),
        data.get("campaign_name"),
        data.get("campaign"),
    ]

    for raw in candidates:
        if not raw or not isinstance(raw, str):
            continue
        s = raw.strip()

        # Pipe-delimited format: fbclid:<val>|gclid:<val>
        for part in s.split("|"):
            part = part.strip()
            if part.startswith("fbclid:") and not fbclid:
                fbclid = part.split(":", 1)[1].strip()
            elif (part.startswith("gclid:") or part.startswith("wbraid:") or part.startswith("gbraid:")) and not gclid:
                gclid = part.split(":", 1)[1].strip()

        # Composite tq_campaign format: <base>--fbclid-<val> or <base>--gclid-<val>
        if not fbclid:
            m_fb = re.search(r"(?:--|^)fbclid-([a-zA-Z0-9_.-]+)", s)
            if m_fb:
                fbclid = m_fb.group(1).split("--")[0].strip()

        if not gclid:
            m_g = re.search(r"(?:--|^)(?:gclid|wbraid|gbraid)-([a-zA-Z0-9_.-]+)", s)
            if m_g:
                gclid = m_g.group(1).split("--")[0].strip()

    return fbclid, gclid

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST'])
@app.route('/<path:path>', methods=['GET', 'POST'])
def webhook_handler(path):
    if request.method == 'POST':
        data = request.get_json() or {}
        fbclid, gclid = extract_click_ids(data)
        
        meta_result = None
        google_result = None

        # Ensure conversion value is NET COMMISSION, not gross revenue
        value = 0.0
        financials = data.get("financials") if isinstance(data.get("financials"), dict) else {}
        raw_commission = (
            data.get("commission") or 
            data.get("commission_excl_vat") or 
            data.get("commission_incl_vat") or
            financials.get("commission_amount") or
            financials.get("commission") or
            financials.get("commission_excl_vat")
        )
        if raw_commission is not None:
            try:
                value = float(raw_commission)
            except (ValueError, TypeError):
                value = 0.0

        # If Tiqets only provided gross revenue, calculate 41.9% net commission
        if value <= 0:
            raw_gross = (
                data.get("transaction_value") or 
                data.get("sale_order_value_incl_vat") or 
                data.get("sale_order_value_excl_vat") or
                financials.get("total_price") or
                financials.get("total_amount")
            )
            if raw_gross is not None:
                try:
                    value = round(float(raw_gross) * 0.419, 2)
                except (ValueError, TypeError):
                    value = 0.0

        currency = data.get("currency", "EUR")
        order_id = str(data.get("order_reference_id") or data.get("order_id") or data.get("basket_reference_id") or "")

        # Meta CAPI Integration
        if fbclid and META_ACCESS_TOKEN and META_PIXEL_ID:
            timestamp = int(time.time())
            fbc = f"fb.1.{timestamp}.{fbclid}"

            user_data = {
                "fbc": fbc
            }
            client_ip = request.headers.get("x-forwarded-for", request.remote_addr)
            if client_ip:
                user_data["client_ip_address"] = client_ip.split(",")[0].strip()
            client_ua = request.headers.get("user-agent")
            if client_ua:
                user_data["client_user_agent"] = client_ua

            # If Tiqets forwards customer details, hash with SHA-256 for better Event Match Quality
            email = data.get("customer_email") or data.get("email")
            if email:
                import hashlib
                user_data["em"] = hashlib.sha256(email.strip().lower().encode('utf-8')).hexdigest()

            country = data.get("customer_country_code") or data.get("customer_ip_country")
            if country:
                import hashlib
                user_data["country"] = hashlib.sha256(country.strip().lower().encode('utf-8')).hexdigest()

            custom_data = {
                "value": value,
                "currency": currency,
                "content_type": "product"
            }
            if order_id:
                custom_data["order_id"] = order_id
            if data.get("product_id"):
                custom_data["content_ids"] = [str(data.get("product_id"))]

            event_payload = {
                "event_name": "Purchase",
                "event_time": timestamp,
                "action_source": "website",
                "user_data": user_data,
                "custom_data": custom_data
            }
            if order_id:
                event_payload["event_id"] = order_id
            
            payload = {
                "data": [event_payload]
            }
            
            test_code = data.get("test_event_code")
            if test_code:
                payload["test_event_code"] = test_code
            
            url = f"https://graph.facebook.com/v20.0/{META_PIXEL_ID}/events?access_token={META_ACCESS_TOKEN}"
            try:
                response = requests.post(url, json=payload)
                response.raise_for_status()
                meta_result = response.json()
            except requests.exceptions.RequestException as e:
                error_msg = str(e)
                if e.response is not None:
                    error_msg += " | " + e.response.text
                return jsonify({"status": "error", "message": error_msg}), 400
            
        # Google Ads API Integration
        if gclid:
            google_config = {
                "GOOGLE_DEV_TOKEN": bool(GOOGLE_DEV_TOKEN),
                "GOOGLE_CLIENT_ID": bool(GOOGLE_CLIENT_ID),
                "GOOGLE_CLIENT_SECRET": bool(GOOGLE_CLIENT_SECRET),
                "GOOGLE_REFRESH_TOKEN": bool(GOOGLE_REFRESH_TOKEN),
                "GOOGLE_CUSTOMER_ID": bool(GOOGLE_CUSTOMER_ID),
                "GOOGLE_CONVERSION_ACTION_ID": bool(GOOGLE_CONVERSION_ACTION_ID)
            }
            missing_google = [k for k, v in google_config.items() if not v]
            if missing_google:
                google_result = {
                    "status": "config_missing",
                    "missing_variables": missing_google,
                    "message": "Google Ads API requires developer token, OAuth credentials, customer ID, and conversion action ID."
                }
            else:
                access_token, token_err = get_google_access_token()
                if not access_token:
                    google_result = {
                        "status": "auth_error",
                        "message": "Failed to obtain Google OAuth access token from refresh token.",
                        "details": token_err
                    }
                else:
                    from datetime import datetime, timezone
                    conversion_time = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S+00:00')
                    
                    url = f"https://googleads.googleapis.com/v26/customers/{GOOGLE_CUSTOMER_ID}:uploadClickConversions"
                    headers = {
                        "Authorization": f"Bearer {access_token}",
                        "developer-token": GOOGLE_DEV_TOKEN,
                        "login-customer-id": GOOGLE_CUSTOMER_ID,
                        "Content-Type": "application/json"
                    }
                    payload = {
                        "conversions": [
                            {
                                "gclid": gclid,
                                "conversionAction": f"customers/{GOOGLE_CUSTOMER_ID}/conversionActions/{GOOGLE_CONVERSION_ACTION_ID}",
                                "conversionDateTime": conversion_time,
                                "conversionValue": value,
                                "currencyCode": currency
                            }
                        ],
                        "partialFailure": True
                    }
                    
                    try:
                        g_res = requests.post(url, headers=headers, json=payload)
                        google_result = {
                            "status": "submitted",
                            "http_status": g_res.status_code,
                            "response": g_res.json() if g_res.content else {}
                        }
                    except requests.exceptions.RequestException as e:
                        err_text = e.response.text if (hasattr(e, 'response') and e.response is not None) else str(e)
                        google_result = {
                            "status": "error",
                            "message": str(e),
                            "details": err_text
                        }
            
        return jsonify({
            "status": "success",
            "fbclid": fbclid,
            "gclid": gclid,
            "commission_value": value,
            "currency": currency,
            "pixel_id": META_PIXEL_ID,
            "meta_result": meta_result,
            "google_result": google_result
        }), 200

    # GET requests: Serve landing page or assets
    public_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'public')
    clean_path = (path or '').strip('/')
    if not clean_path or clean_path in ['family-bateaux-parisiens-sightseeing-cruise', 'family-cruise', 'paris-family-cruise']:
        index_file = os.path.join(public_dir, 'index.html')
        if os.path.exists(index_file):
            return send_from_directory(public_dir, 'index.html')
    elif clean_path in ['styles.css', 'script.js']:
        asset_file = os.path.join(public_dir, clean_path)
        if os.path.exists(asset_file):
            return send_from_directory(public_dir, clean_path)

    return jsonify({"message": "Tiqets Ads Sync Webhook is running."}), 200

if __name__ == '__main__':
    app.run()
