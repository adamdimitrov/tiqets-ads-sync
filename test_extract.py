import requests

TIQETS_API_KEY = "tqat-riUgqzjZAhtdw09J2G8rOUgTvNBKBGQC"
url = 'https://api.tiqets.com/v2/reports/orders'
headers = {'Authorization': f'Token {TIQETS_API_KEY}'}
response = requests.get(url, headers=headers)
data = response.json()

for order in data.get('orders', []):
    if order.get('order_reference_id') == '1015543946':
        print(order)
        value = float(order.get("commission") or order.get("commission_excl_vat") or order.get("transaction_value") or order.get("sale_order_value_incl_vat") or 0)
        print("COMPUTED VALUE:", value)
