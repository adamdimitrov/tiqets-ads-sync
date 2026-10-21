import os

path = '/Users/adamdimitrov/Development/tiqets-ads-sync/api/index.py'
with open(path, 'r') as f:
    content = f.read()

# Replace the try/except block to return the error
old_code = """            try:
                response = requests.post(url, json=payload)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                print(f"Error sending Meta CAPI event: {e}")"""

new_code = """            try:
                response = requests.post(url, json=payload)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                error_msg = str(e)
                if e.response is not None:
                    error_msg += " | " + e.response.text
                return jsonify({"status": "error", "message": error_msg}), 400"""

content = content.replace(old_code, new_code)

with open(path, 'w') as f:
    f.write(content)
