import logging
import os
from logging.handlers import RotatingFileHandler
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.admin import setup_admin
from app.auth import auth_router, get_current_user, get_current_active_user, get_current_superuser
from app.config import get_settings
from app.database import create_db_and_tables
from app.models.user_article import UserArticle
from app.routers import articles_router, tts_router
from app.routers.settings import router as settings_router
from app.schemas.article import ArticleRefreshResponse
from app.services import RSSFetcher

# Setup logging
LOGS_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

# Configure logging with file and console handlers
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        RotatingFileHandler(
            os.path.join(LOGS_DIR, "app.log"),
            maxBytes=10 * 1024 * 1024,  # 10MB per file
            backupCount=5,  # Keep 5 backup files
            encoding="utf-8"
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    await create_db_and_tables()
    logger.info("Database tables created")
    # Auto-refresh disabled - user must click "Get My News" to fetch personalized articles

    yield

    # Shutdown
    logger.info("Application shutting down")


# Create FastAPI app
app = FastAPI(
    title="NPR News Summarizer",
    description="A PWA that fetches NPR news, summarizes with Perplexity AI, and reads aloud with Speechify TTS",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include auth router
app.include_router(auth_router)

# Setup SQLAdmin
setup_admin(app)

# Include app routers
app.include_router(articles_router)
app.include_router(tts_router)
app.include_router(settings_router)


# Mount static files (for serving frontend)
static_dir = os.path.join(os.path.dirname(__file__), "..", "..", "frontend")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
