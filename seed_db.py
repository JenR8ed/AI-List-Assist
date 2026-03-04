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
redis_host = os.environ.get("REDIS_HOST", "localhost")
redis_port = int(os.environ.get("REDIS_PORT", 6379))
r = redis.Redis(host=redis_host, port=redis_port, db=0)
print(f"Connected to Redis at {redis_host}:{redis_port}!")

# Connect to Postgres
pg_dbname = os.environ.get("POSTGRES_DB", "ebay_market_data")
pg_user = os.environ.get("POSTGRES_USER", "ai_user")
pg_password = os.environ.get("POSTGRES_PASSWORD", "ai_password")
pg_host = os.environ.get("POSTGRES_HOST", "localhost")
pg_port = os.environ.get("POSTGRES_PORT", "5432")

conn = None
for i in range(5):
    try:
        conn = psycopg2.connect(
            dbname=pg_dbname,
            user=pg_user,
            password=pg_password,
            host=pg_host,
            port=pg_port
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
