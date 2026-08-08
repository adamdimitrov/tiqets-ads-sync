from flask import Flask, request, jsonify
import os
import requests
import time

app = Flask(__name__)

TIQETS_API_KEY = os.environ.get("TIQETS_API_KEY")
META_ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN")
META_PIXEL_ID = os.environ.get("META_PIXEL_ID")
CRON_SECRET = os.environ.get("CRON_SECRET")
GOOGLE_DEV_TOKEN = os.environ.get("GOOGLE_DEV_TOKEN")
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
GOOGLE_REFRESH_TOKEN = os.environ.get("GOOGLE_REFRESH_TOKEN")
GOOGLE_CUSTOMER_ID = os.environ.get("GOOGLE_CUSTOMER_ID")
GOOGLE_CONVERSION_ACTION_ID = os.environ.get("GOOGLE_CONVERSION_ACTION_ID")

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

@app.route('/', defaults={'path': ''}, methods=['GET'])
@app.route('/<path:path>', methods=['GET'])
def cron_handler(path):
    auth_header = request.headers.get('Authorization')
    if not CRON_SECRET or auth_header != f'Bearer {CRON_SECRET}':
        return jsonify({"error": "Unauthorized"}), 401
        
    if not TIQETS_API_KEY:
        return jsonify({"error": "Missing Tiqets API Key"}), 500
        
    try:
        tiqets_url = 'https://api.tiqets.com/v2/reports/orders'
        headers = {
            'Authorization': f'Token {TIQETS_API_KEY}'
        }
        
        response = requests.get(tiqets_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        orders = data.get('orders', [])
        
    except Exception as e:
        return jsonify({"error": f"Error fetching orders: {str(e)}"}), 500
        
    processed_orders = 0
    
    cached_google_access_token = None

    for order in orders:
        click_id = order.get('click_id') or ''
        if click_id and ('fbclid:' in click_id or 'gclid:' in click_id):
            fbclid = None
            gclid = None
            for part in click_id.split('|'):
                if part.startswith('fbclid:'):
                    fbclid = part.split(':')[1]
                elif part.startswith('gclid:'):
                    gclid = part.split(':')[1]
                    
            if fbclid and META_ACCESS_TOKEN and META_PIXEL_ID:
                timestamp = int(time.time())
                fbc = f"fb.1.{timestamp}.{fbclid}"
                
                payload = {
                    "data": [
                        {
                            "event_name": "Purchase",
                            "event_time": timestamp,
                            "action_source": "website",
                            "user_data": {
                                "fbc": fbc
                            },
                            "custom_data": {
                                "value": float(order.get("commission") or order.get("commission_excl_vat") or order.get("transaction_value") or order.get("sale_order_value_incl_vat") or 0),
                                "currency": order.get("currency", "EUR")
                            },
                            "event_id": order.get("order_reference_id")
                        }
                    ]
                }
                
                url = f"https://graph.facebook.com/v20.0/{META_PIXEL_ID}/events?access_token={META_ACCESS_TOKEN}"
                try:
                    meta_res = requests.post(url, json=payload)
                    meta_res.raise_for_status()
                    processed_orders += 1
                except requests.exceptions.RequestException as e:
                    print(f"Error sending Meta CAPI event for order {order.get('order_reference_id')}: {e}")
                    
            if gclid and GOOGLE_DEV_TOKEN and GOOGLE_CLIENT_ID and GOOGLE_CUSTOMER_ID:
                if not cached_google_access_token:
                    cached_google_access_token = get_google_access_token()
                
                if cached_google_access_token:
                    from datetime import datetime, timezone
                    conversion_time = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S+00:00')
                    value = float(order.get("commission") or order.get("commission_excl_vat") or order.get("transaction_value") or order.get("sale_order_value_incl_vat") or 0)
                    currency = order.get("currency", "EUR")
                    
                    url = f"https://googleads.googleapis.com/v17/customers/{GOOGLE_CUSTOMER_ID}:uploadClickConversions"
                    headers = {
                        "Authorization": f"Bearer {cached_google_access_token}",
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
                        g_res.raise_for_status()
                    except requests.exceptions.RequestException as e:
                        print(f"Error sending Google Ads conversion for order {order.get('order_reference_id')}: {e}")
                        if e.response is not None:
                            print(e.response.text)
                    
    return jsonify({"status": "success", "processed_orders": processed_orders}), 200

if __name__ == '__main__':
    app.run()
