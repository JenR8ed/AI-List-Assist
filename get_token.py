import requests
import base64
import os
from dotenv import load_dotenv

load_dotenv()

client_id = os.getenv('EBAY_CLIENT_ID')
client_secret = os.getenv('EBAY_CLIENT_SECRET')

print(f"Client ID: {client_id}")
print(f"Client Secret: {client_secret[:10]}...")

credentials = f"{client_id}:{client_secret}"
encoded = base64.b64encode(credentials.encode()).decode()

# Try basic scope first
response = requests.post(
    "https://api.ebay.com/identity/v1/oauth2/token",
    headers={
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {encoded}"
    },
    data={
        "grant_type": "client_credentials"
    }
)

print(f"Response: {response.status_code}")
print(f"Body: {response.text}")

if response.status_code == 200:
    token = response.json()['access_token']
    print(f"Token: {token}")
    
    # Update .env file
    with open('.env', 'r') as f:
        content = f.read()
    
    if 'EBAY_ACCESS_TOKEN=' in content:
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('EBAY_ACCESS_TOKEN='):
                lines[i] = f'EBAY_ACCESS_TOKEN={token}'
        content = '\n'.join(lines)
    else:
        content += f'\nEBAY_ACCESS_TOKEN={token}'
    
    with open('.env', 'w') as f:
        f.write(content)
    
    print("Updated .env file")