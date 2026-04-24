import requests

payload = {
    'valuation_id': 'testval_123',
    'listing_id': 'testlist_123',
    'title': 'Test Item',
    'category_id': '293',
    'price': 19.99,
    'condition': 'NEW',
    'description': 'A very nice test item'
}

try:
    print('Calling submit-listing API on localhost...')
    response = requests.post('http://localhost:5000/api/ebay/submit-listing', json=payload)
    print(response.status_code, response.text)
except Exception as e:
    print('Failed:', e)
