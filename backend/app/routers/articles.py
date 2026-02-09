import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import get_current_user, get_current_active_user
from app.database import get_async_session
from app.models import Article, Summary, UserArticle
from app.models.user import User
from app.schemas.article import ArticleList, ArticleRead, ArticleRefreshResponse
from app.schemas.summary import SummaryRead
from app.services import PerplexityClient, RSSFetcher

router = APIRouter(prefix="/api/articles", tags=["articles"])


async def get_article_with_user_status(
    session: AsyncSession,
    article: Article,
    user_id: Optional[uuid.UUID] = None
) -> ArticleRead:
    """Convert Article model to ArticleRead schema with user status."""
    data = {
        "id": article.id,
        "guid": article.guid,
        "title": article.title,
        "link": str(article.link),
        "description": article.description,
        "published_at": article.published_at,
        "author": article.author,
        "category": article.category,
        "fetched_at": article.fetched_at,
        "created_at": article.created_at,
        "has_summary": article.summary is not None,
        "is_read": False,
        "is_favorite": False
    }

    if user_id:
        # Check user article status
        result = await session.execute(
            select(UserArticle).where(
                UserArticle.user_id == user_id,
                UserArticle.article_id == article.id
            )
        )
        user_article = result.scalar_one_or_none()
        if user_article:
            data["is_read"] = user_article.is_read
            data["is_favorite"] = user_article.is_favorite

    return ArticleRead(**data)


@router.get("", response_model=ArticleList)
async def list_articles(
    session: AsyncSession = Depends(get_async_session),
    current_user: Optional[User] = Depends(get_current_user)
):
    """List the latest articles (up to 20), sorted by date (newest first)."""
    user_id = current_user.id if current_user else None
    
    result = await session.execute(
        select(Article)
        .options(selectinload(Article.summary))
        .order_by(Article.published_at.desc())
        .limit(20)
    )
    articles = result.scalars().all()

    # Get the most recent fetch time
    last_updated = None
    if articles:
        last_updated = max(a.fetched_at for a in articles)

    # Convert to schemas
    items = []
    for article in articles:
        article_read = await get_article_with_user_status(session, article, user_id)
        items.append(article_read)

    return ArticleList(
        items=items,
        total=len(items),
        last_updated=last_updated
    )


@router.post("/refresh", response_model=ArticleRefreshResponse)
async def refresh_articles(
    session: AsyncSession = Depends(get_async_session)
):
    """Manually refresh articles from NPR RSS feed."""
    fetcher = RSSFetcher()

    try:
        new_articles_data = await fetcher.fetch_feed()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to fetch RSS feed: {str(e)}"
        )

    new_count = 0

    for article_data in new_articles_data:
        # Check if article already exists
        result = await session.execute(
            select(Article).where(Article.guid == article_data.guid)
        )
        existing = result.scalar_one_or_none()

        if not existing:
            # Create new article
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

    # Get total count
    result = await session.execute(select(Article))
    total = len(result.scalars().all())

    return ArticleRefreshResponse(
        new_articles=new_count,
        total_articles=total,
        fetched_at=datetime.utcnow()
    )


@router.get("/{article_id}", response_model=ArticleRead)
async def get_article(
    article_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Get a single article by ID."""
    user_id = current_user.id if current_user else None
    
    result = await session.execute(
        select(Article)
        .options(selectinload(Article.summary))
        .where(Article.id == article_id)
    )
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found"
        )

    return await get_article_with_user_status(session, article, user_id)


@router.get("/{article_id}/summary", response_model=SummaryRead)
async def get_summary(
    article_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session)
):
    """Get the summary for an article (creates one if not exists)."""
    # Get article with summary loaded
    result = await session.execute(
        select(Article).options(selectinload(Article.summary)).where(Article.id == article_id)
    )
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found"
        )

    # Check if summary exists
    if article.summary:
        return SummaryRead.model_validate(article.summary)

    # Generate new summary
    perplexity = PerplexityClient()

    try:
        summary_text, model_used, tokens_used = await perplexity.summarize_article(
            title=article.title,
            description=article.description or "",
            article_url=str(article.link)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to generate summary: {str(e)}"
        )

    # Save summary
    summary = Summary(
        article_id=article.id,
        content=summary_text,
        model_used=model_used,
        tokens_used=tokens_used
    )
    session.add(summary)
    await session.commit()
    await session.refresh(summary)

    return SummaryRead.model_validate(summary)


@router.post("/{article_id}/read")
async def mark_as_read(
    article_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user)
):
    """Mark an article as read."""
    user_id = current_user.id

    # Check if article exists
    result = await session.execute(
        select(Article).where(Article.id == article_id)
    )
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found"
        )

    # Get or create user article record
    result = await session.execute(
        select(UserArticle).where(
            UserArticle.user_id == user_id,
            UserArticle.article_id == article_id
        )
    )
    user_article = result.scalar_one_or_none()

    if not user_article:
        user_article = UserArticle(
            user_id=user_id,
            article_id=article_id,
            is_read=True,
            read_at=datetime.utcnow()
        )
        session.add(user_article)
    else:
        user_article.is_read = True
        user_article.read_at = datetime.utcnow()

    await session.commit()

    return {"status": "marked_as_read"}


@router.post("/{article_id}/favorite")
async def toggle_favorite(
    article_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user)
):
    """Toggle favorite status for an article."""
    user_id = current_user.id

    # Check if article exists
    result = await session.execute(
        select(Article).where(Article.id == article_id)
    )
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found"
        )

    # Get or create user article record
    result = await session.execute(
        select(UserArticle).where(
            UserArticle.user_id == user_id,
            UserArticle.article_id == article_id
        )
    )
    user_article = result.scalar_one_or_none()

    if not user_article:
        user_article = UserArticle(
            user_id=user_id,
            article_id=article_id,
            is_favorite=True
        )
        session.add(user_article)
        new_status = True
    else:
        user_article.is_favorite = not user_article.is_favorite
        new_status = user_article.is_favorite

    await session.commit()

    return {"is_favorite": new_status}
