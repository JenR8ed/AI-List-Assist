#!/bin/bash
# agent_bootstrap.sh
# Unified entry point for initializing the agent environment in CI/CD and local testing.

set -e

echo "🚀 Starting Agent Bootstrap Sequence..."

# Dependency Installation
echo "📦 Installing required Python packages..."
pip install -r requirements.txt fastapi sqlmodel pydantic pydantic-settings asyncpg sqlalchemy
echo "✅ Dependencies installed."

# Health Checks
echo "🔍 Performing strict health checks..."
if [ -z "$NEON_DATABASE_URL" ]; then
  echo "❌ Error: NEON_DATABASE_URL environment variable is not set."
  echo "Please provide a valid connection string to proceed."
  /bin/false
fi

# Verify active database connection
echo "📡 Pinging database connection..."
python3 -c "
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from core.config import settings

async def check_connection():
    engine = create_async_engine(settings.async_database_url)
    async with engine.connect() as conn:
        await conn.execute(sqlalchemy.text('SELECT 1'))

asyncio.run(check_connection())
" || { echo "❌ Error: Could not connect to the database."; /bin/false; }

echo "✅ Environment variables and active connection verified."

# Database Migrations
echo "🔄 Synchronizing database schema against Neon Serverless Postgres..."
python3 -c "import asyncio; from core.database import init_db; asyncio.run(init_db())"
echo "✅ Database synchronization complete."

echo "🎉 Agent environment successfully bootstrapped!"
