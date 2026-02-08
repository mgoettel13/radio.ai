import logging
from datetime import datetime
from typing import List

import feedparser
import httpx

from app.config import get_settings
from app.schemas.article import ArticleCreate

logger = logging.getLogger(__name__)


class RSSFetcher:
    def __init__(self):
        settings = get_settings()
        self.feed_url = settings.npr_feed_url
        self.max_articles = settings.max_articles

    async def fetch_feed(self) -> List[ArticleCreate]:
        """Fetch and parse NPR RSS feed, return list of articles."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.feed_url, timeout=30.0)
                response.raise_for_status()
                feed_content = response.text
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch RSS feed: {e}")
            raise RSSFetchError(f"Failed to fetch RSS feed: {e}")

        # Parse the feed
        feed = feedparser.parse(feed_content)

        if feed.bozo:
            logger.warning(f"RSS feed parsing warning: {feed.bozo_exception}")

        articles = []
        for entry in feed.entries[:self.max_articles]:
            try:
                article = self._parse_entry(entry)
                if article:
                    articles.append(article)
            except Exception as e:
                logger.warning(f"Failed to parse entry: {e}")
                continue

        # Sort by published date (newest first)
        articles.sort(key=lambda x: x.published_at, reverse=True)

        # Limit to max_articles after sorting
        articles = articles[:self.max_articles]

        logger.info(f"Fetched {len(articles)} articles from NPR feed")
        return articles

    def _parse_entry(self, entry) -> ArticleCreate | None:
        """Parse a single RSS entry into ArticleCreate schema."""
        # Get GUID (required)
        guid = entry.get("guid", entry.get("id", entry.get("link")))
        if not guid:
            logger.warning("Entry has no GUID, skipping")
            return None

        # Get title
        title = entry.get("title", "").strip()
        if not title:
            logger.warning(f"Entry {guid} has no title, skipping")
            return None

        # Get link
        link = entry.get("link", "").strip()
        if not link:
            logger.warning(f"Entry {guid} has no link, skipping")
            return None

        # Get published date
        published_at = self._parse_date(entry)
        if not published_at:
            published_at = datetime.utcnow()

        # Get description/summary
        description = entry.get("summary", entry.get("description", ""))
        # Clean up HTML if present
        if description:
            description = self._clean_html(description)

        # Get author
        author = entry.get("author", "")
        if not author:
            # Try to get from dc:creator
            author = entry.get("dc_creator", "")

        # Get category
        category = ""
        if "tags" in entry and entry.tags:
            category = entry.tags[0].get("term", "")
        elif "category" in entry:
            category = entry.category

        return ArticleCreate(
            guid=guid,
            title=title,
            link=link,
            description=description or None,
            published_at=published_at,
            author=author or None,
            category=category or None
        )

    def _parse_date(self, entry) -> datetime | None:
        """Parse published date from entry."""
        date_fields = ["published_parsed", "updated_parsed", "created_parsed"]

        for field in date_fields:
            if hasattr(entry, field) and getattr(entry, field):
                try:
                    time_struct = getattr(entry, field)
                    return datetime(*time_struct[:6])
                except (ValueError, TypeError) as e:
                    logger.warning(f"Failed to parse date from {field}: {e}")
                    continue

        # Try string dates
        date_strings = ["published", "updated", "created"]
        for field in date_strings:
            if hasattr(entry, field) and getattr(entry, field):
                try:
                    from email.utils import parsedate_to_datetime
                    return parsedate_to_datetime(getattr(entry, field))
                except Exception as e:
                    logger.warning(f"Failed to parse date string from {field}: {e}")
                    continue

        return None

    @staticmethod
    def _clean_html(text: str) -> str:
        """Remove HTML tags from text."""
        import re
        clean = re.compile("<.*?>")
        return re.sub(clean, "", text)


class RSSFetchError(Exception):
    """Raised when RSS feed fetch fails."""
    pass
