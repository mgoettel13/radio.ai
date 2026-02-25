"""
News generator service for radio stations.
Reuses existing Perplexity and TTS logic to generate news audio for stations.
"""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.perplexity import PerplexityClient, PerplexityError
from app.services.speechifyService import SpeechifyClient, SpeechifyError

logger = logging.getLogger(__name__)

# Cache duration in seconds (1 hour)
NEWS_CACHE_DURATION = 3600


class NewsGenerator:
    """Service for generating news audio for radio stations."""
    
    def __init__(self):
        self.perplexity = PerplexityClient()
        self.speechify = SpeechifyClient()
    
    async def generate_news_for_station(
        self,
        user_id: UUID,
        session: AsyncSession,
        cached_news: Optional[dict] = None
    ) -> dict:
        """
        Generate news audio for a station.
        Uses user preferences to get personalized news.
        
        Args:
            user_id: The user's UUID
            session: Database session
            cached_news: Optional cached news data to check validity
            
        Returns:
            dict with radio_script, audio_url, duration_seconds, generated_at
        """
        # Check if cached news is still valid
        if cached_news:
            generated_at = cached_news.get('generated_at')
            if generated_at:
                if isinstance(generated_at, str):
                    generated_at = datetime.fromisoformat(generated_at)
                age = (datetime.utcnow() - generated_at).total_seconds()
                if age < NEWS_CACHE_DURATION:
                    logger.info("Using cached news audio")
                    return cached_news
        
        # Import here to avoid circular imports
        from app.models import Article, UserPreferences, UserPersonalizedNews
        from app.models.user_article import UserArticle
        from app.services.rss_fetcher import RSSFetcher
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        
        # Step 1: Refresh RSS feed
        fetcher = RSSFetcher()
        try:
            new_articles_data = await fetcher.fetch_feed()
        except Exception as e:
            logger.error(f"Failed to fetch RSS feed: {e}")
            raise NewsGenerationError(f"Failed to fetch RSS feed: {str(e)}")
        
        # Save any new articles to database
        for article_data in new_articles_data:
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
        
        await session.commit()
        
        # Step 2: Get user preferences
        result = await session.execute(
            select(UserPreferences).where(UserPreferences.user_id == user_id)
        )
        preferences = result.scalar_one_or_none()
        
        # Build preferences dict
        prefs_dict = {
            "topics": preferences.topics if preferences else [],
            "keywords": preferences.keywords if preferences else [],
            "location": preferences.location if preferences and preferences.location else "",
            "country": preferences.country if preferences and preferences.country else ""
        }
        
        # Step 3: Get articles for ranking (limit to 20 most recent)
        result = await session.execute(
            select(Article)
            .options(selectinload(Article.summary))
            .order_by(Article.published_at.desc())
            .limit(20)
        )
        articles = result.scalars().all()
        
        if not articles:
            raise NewsGenerationError("No articles available for news generation")
        
        # Convert articles to dict format for Perplexity
        articles_data = []
        for article in articles:
            articles_data.append({
                "id": article.id,
                "title": article.title,
                "description": article.description,
                "link": str(article.link)
            })
        
        # Step 4: Use Perplexity to rank articles
        try:
            ranked_articles = await self.perplexity.rank_articles(articles_data, prefs_dict)
        except PerplexityError as e:
            logger.error(f"Perplexity ranking failed: {e}")
            # Fallback: just take first 5 articles
            ranked_articles = [{"rank": i + 1, **articles_data[i]} for i in range(min(5, len(articles_data)))]
        
        # Step 5: Get top 5 articles for radio script
        top_5_articles = ranked_articles[:5]
        
        # Step 6: Create radio script using Perplexity
        try:
            radio_script, model_used, tokens_used = await self.perplexity.create_radio_script(top_5_articles)
        except PerplexityError as e:
            logger.error(f"Failed to create radio script: {e}")
            # Fallback: create a simple script
            radio_script = "Here are your top news stories: " + ". ".join([a["title"] for a in top_5_articles])
        
        # Step 7: Generate TTS audio
        try:
            audio_url, duration = await self.speechify.text_to_speech(
                text=radio_script,
                voice_id="oliver"
            )
        except SpeechifyError as e:
            logger.error(f"Failed to generate TTS audio: {e}")
            raise NewsGenerationError(f"Failed to generate TTS audio: {str(e)}")
        
        # Step 8: Return the result
        result = {
            "radio_script": radio_script,
            "audio_url": audio_url,
            "duration_seconds": int(duration) if duration else 0,
            "generated_at": datetime.utcnow()
        }
        
        return result


class NewsGenerationError(Exception):
    """Raised when news generation fails."""
    pass
