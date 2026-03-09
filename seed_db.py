import os
import time
import requests
import json
import psycopg2
import redis

# Wait for DB to be really ready
print("Waiting for databases...")
time.sleep(15)

# Connect to Redis
r = redis.Redis(host='localhost', port=6379, db=0)
print("Connected to Redis!")

# Connect to Postgres
conn = None
for i in range(5):
    try:
        conn = psycopg2.connect(
            dbname="ebay_market_data",
            user="ai_user",
            password="ai_password",
            host="localhost",
            port=5432
        )
        break
    except Exception as e:
        print(f"PG connection failed, retrying in 5s... ({e})")
        time.sleep(5)

if not conn:
    print("Failed to connect to PG.")
    exit(1)

cur = conn.cursor()

# Create table if not exists
cur.execute('''
    CREATE TABLE IF NOT EXISTS market_trends (
        id SERIAL PRIMARY KEY,
        query TEXT,
        trends_data TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')
conn.commit()
print("Postgres table created or already exists!")

perplexity_key = os.environ.get("PERPLEXITY_API_KEY", "mock_key_if_missing")

print(f"Using PERPLEXITY_API_KEY: [REDACTED]")

if perplexity_key and perplexity_key != "mock_key_if_missing":
    try:
        url = "https://api.perplexity.ai/chat/completions"
        payload = {
            "model": "sonar",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful assistant."
                },
                {
                    "role": "user",
                    "content": "Return current eBay market trends, inventory levels, and pricing data for electronics in JSON format only."
                }
            ]
        }
        headers = {
            "Authorization": f"Bearer {perplexity_key}",
            "Content-Type": "application/json"
        }
        print("Calling Perplexity API...")
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        content = data['choices'][0]['message']['content']

        # Save to PG
        cur.execute("INSERT INTO market_trends (query, trends_data) VALUES (%s, %s)", ("electronics_trends", content))
        conn.commit()

        # Save to Redis
        r.set("latest_ebay_trends", content)
        print("Data successfully seeded into Postgres and Redis!")
    except Exception as e:
        print(f"Error fetching/seeding data: {e}")
        print("Falling back to mock data.")
        mock_data = '{"electronics": {"trend": "up", "inventory": "low", "average_price": 199.99}}'
        cur.execute("INSERT INTO market_trends (query, trends_data) VALUES (%s, %s)", ("electronics_trends", mock_data))
        conn.commit()
        r.set("latest_ebay_trends", mock_data)
        print("Mock Data successfully seeded into Postgres and Redis!")

cur.close()
conn.close()
