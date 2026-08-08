from flask import Flask, request, jsonify
import os
import requests
import time

app = Flask(__name__)

TIQETS_API_KEY = os.environ.get("TIQETS_API_KEY")
META_ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN")
META_PIXEL_ID = os.environ.get("META_PIXEL_ID")
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

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST'])
@app.route('/<path:path>', methods=['GET', 'POST'])
def webhook_handler(path):
    if request.method == 'POST':
        data = request.get_json() or {}
        # Tiqets payload parsing for subid
        subid = data.get("subid", "")
        
        fbclid = None
        gclid = None
        
        if subid:
            for part in subid.split('|'):
                if part.startswith('fbclid:'):
                    fbclid = part.split(':')[1]
                elif part.startswith('gclid:'):
                    gclid = part.split(':')[1]
        
        # Meta CAPI Integration
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
                            "value": float(data.get("commission", data.get("transaction_value", 0))),
                            "currency": data.get("currency", "EUR")
                        }
                    }
                ]
            }
            
            test_code = data.get("test_event_code")
            if test_code:
                payload["test_event_code"] = test_code
            
            url = f"https://graph.facebook.com/v20.0/{META_PIXEL_ID}/events?access_token={META_ACCESS_TOKEN}"
            try:
                response = requests.post(url, json=payload)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                error_msg = str(e)
                if e.response is not None:
                    error_msg += " | " + e.response.text
                return jsonify({"status": "error", "message": error_msg}), 400
            
        # Google API Integration
        if gclid and GOOGLE_DEV_TOKEN and GOOGLE_CLIENT_ID and GOOGLE_CUSTOMER_ID:
            access_token = get_google_access_token()
            if access_token:
                from datetime import datetime, timezone
                conversion_time = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S+00:00')
                value = float(data.get("commission", data.get("transaction_value", 0)))
                currency = data.get("currency", "EUR")
                
                url = f"https://googleads.googleapis.com/v17/customers/{GOOGLE_CUSTOMER_ID}:uploadClickConversions"
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
                    g_res.raise_for_status()
                except requests.exceptions.RequestException as e:
                    print(f"Error sending Google Ads conversion: {e}")
                    if e.response is not None:
                        print(e.response.text)
            
        return jsonify({"status": "success", "fbclid": fbclid, "gclid": gclid}), 200
        
    return jsonify({"message": "Tiqets Ads Sync Webhook is running."}), 200

if __name__ == '__main__':
    app.run()
