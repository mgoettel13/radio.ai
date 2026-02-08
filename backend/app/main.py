import asyncio
import logging
import os
import uuid
from logging.handlers import RotatingFileHandler
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi_users import FastAPIUsers, schemas
from fastapi_users.authentication import AuthenticationBackend, BearerTransport, JWTStrategy
from pydantic import BaseModel, EmailStr

from app.admin import setup_admin
from app.config import get_settings
from app.database import User, create_db_and_tables, get_user_db
from app.models.user_article import UserArticle
from app.routers import articles_router, tts_router
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

# Background task for RSS refresh
rss_refresh_task = None


# User schemas for fastapi-users
class UserRead(schemas.BaseUser[uuid.UUID]):
    pass


class UserCreate(schemas.BaseUserCreate):
    def create_update_dict(self):
        """Override to ensure dictionary is returned."""
        return self.model_dump(
            exclude_unset=True,
            exclude={
                "id",
                "is_superuser",
                "is_active",
                "is_verified",
                "oauth_accounts",
            },
        )

    def create_update_dict_superuser(self):
        """Override to ensure dictionary is returned."""
        return self.model_dump(exclude_unset=True, exclude={"id"})


class UserUpdate(schemas.BaseUserUpdate):
    def create_update_dict(self):
        """Override to ensure dictionary is returned."""
        return self.model_dump(
            exclude_unset=True,
            exclude={
                "id",
                "is_superuser",
                "is_active",
                "is_verified",
                "oauth_accounts",
            },
        )

    def create_update_dict_superuser(self):
        """Override to ensure dictionary is returned."""
        return self.model_dump(exclude_unset=True, exclude={"id"})


async def periodic_rss_refresh():
    """Background task to refresh RSS feed every 10 minutes."""
    from app.database import async_session_maker
    from sqlalchemy import select
    from app.models import Article

    while True:
        try:
            await asyncio.sleep(settings.rss_refresh_minutes * 60)

            async with async_session_maker() as session:
                fetcher = RSSFetcher()
                new_articles = await fetcher.fetch_feed()

                new_count = 0
                for article_data in new_articles:
                    result = await session.execute(
                        select(Article).where(Article.guid == article_data.guid)
                    )
                    existing = result.scalar_one_or_none()

                    if not existing:
                        article = Article(
                            guid=article_data.guid,
                            title=article_data.title,
                            link=str(article_data.link),
                            description=article_data.description,
                            published_at=article_data.published_at,
                            author=article_data.author,
                            category=article_data.category
                        )
                        session.add(article)
                        new_count += 1

                await session.commit()
                logger.info(f"Auto-refresh: Added {new_count} new articles")

        except Exception as e:
            logger.error(f"Auto-refresh error: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    await create_db_and_tables()
    logger.info("Database tables created")

    # Start background RSS refresh task
    global rss_refresh_task
    rss_refresh_task = asyncio.create_task(periodic_rss_refresh())
    logger.info(f"Started RSS auto-refresh (every {settings.rss_refresh_minutes} minutes)")

    yield

    # Shutdown
    if rss_refresh_task:
        rss_refresh_task.cancel()
        try:
            await rss_refresh_task
        except asyncio.CancelledError:
            pass
    logger.info("Application shutting down")


# FastAPI Users setup
bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=settings.secret_key, lifetime_seconds=3600)


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_db, [auth_backend])

current_active_user = fastapi_users.current_user(active=True)
current_superuser = fastapi_users.current_user(active=True, superuser=True)


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

# Include fastapi-users auth routes
app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/auth/users",
    tags=["auth"],
)

# Setup SQLAdmin
setup_admin(app)

# Include app routers
app.include_router(articles_router)
app.include_router(tts_router)


# Mount static files (for serving frontend)
static_dir = os.path.join(os.path.dirname(__file__), "..", "..", "frontend")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
