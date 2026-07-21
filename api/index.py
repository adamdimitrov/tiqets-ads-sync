from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)

TIQETS_API_KEY = os.environ.get("TIQETS_API_KEY")
META_ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN")
META_PIXEL_ID = os.environ.get("META_PIXEL_ID")
GOOGLE_DEV_TOKEN = os.environ.get("GOOGLE_DEV_TOKEN")

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
            pass # TODO: Implement Meta API call
            
        # Google API Integration
        if gclid and GOOGLE_DEV_TOKEN:
            pass # TODO: Implement Google API call
            
        return jsonify({"status": "success", "fbclid": fbclid, "gclid": gclid}), 200
        
    return jsonify({"message": "Tiqets Ads Sync Webhook is running."}), 200

if __name__ == '__main__':
    app.run()
