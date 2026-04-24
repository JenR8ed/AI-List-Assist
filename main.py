import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from core.database import init_db
from api.routers import analysis, conversation, ebay, categories

# Configure standard logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Lifespan context manager replaces @app.before_first_request
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize the async database connection and tables
    logger.info("Initializing FastAPI Application...")
    await init_db()
    yield
    # Shutdown: Clean up resources
    logger.info("Shutting down application...")

# Initialize FastAPI
app = FastAPI(
    title="AI-List-Assist (FARM Stack)",
    description="Enterprise API for eBay valuation and listing synthesis.",
    version="2.0.0",
    lifespan=lifespan
)

# Replace the manual @app.after_request security headers from Flask
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], # Next.js frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the uploads directory statically
import os
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include all modular routers
app.include_router(analysis.router)
app.include_router(conversation.router)
app.include_router(ebay.router)
app.include_router(categories.router)

@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "healthy", "architecture": "FARM"}

if __name__ == "__main__":
    import uvicorn
    # Replaces app.run() with the high-performance ASGI server
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
