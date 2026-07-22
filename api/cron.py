from flask import Flask, request, jsonify
import os
import requests
import time

app = Flask(__name__)

TIQETS_API_KEY = os.environ.get("TIQETS_API_KEY")
META_ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN")
META_PIXEL_ID = os.environ.get("META_PIXEL_ID")
CRON_SECRET = os.environ.get("CRON_SECRET")

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
    
    for order in orders:
        click_id = order.get('click_id') or ''
        if click_id and 'fbclid:' in click_id:
            fbclid = None
            for part in click_id.split('|'):
                if part.startswith('fbclid:'):
                    fbclid = part.split(':')[1]
                    break
                    
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
                                "value": float(order.get("commission_excl_vat") or order.get("sale_order_value_incl_vat") or 0),
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
                    
    return jsonify({"status": "success", "processed_orders": processed_orders}), 200

if __name__ == '__main__':
    app.run()
