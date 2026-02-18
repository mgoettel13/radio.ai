import logging
from typing import Optional, List, Dict, Any

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


class PerplexityClient:
    BASE_URL = "https://api.perplexity.ai"

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.perplexity_api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def summarize_article(
        self,
        title: str,
        description: str,
        article_url: str
    ) -> tuple[str, str, Optional[int]]:
        """
        Summarize a news article using Perplexity AI.

        Returns:
            Tuple of (summary, model_used, tokens_used)
        """
        if not self.api_key:
            raise PerplexityError("Perplexity API key not configured")

        prompt = self._build_prompt(title, description, article_url)

        payload = {
            "model": "sonar-pro",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a journalist who summarizes news articles for the news section for a radio station. Provide a 2-3 sentence summary that captures the key points. not longer than 30 seconds. Do not include any refernces "
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 200,
            "temperature": 0.3
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.BASE_URL}/chat/completions",
                    headers=self.headers,
                    json=payload,
                    timeout=60.0
                )
                response.raise_for_status()
                data = response.json()

            summary = data["choices"][0]["message"]["content"].strip()
            model_used = data.get("model", "sonar-pro")
            tokens_used = data.get("usage", {}).get("total_tokens")

            logger.info(f"Generated summary using {model_used}, tokens: {tokens_used}")
            return summary, model_used, tokens_used

        except httpx.HTTPStatusError as e:
            logger.error(f"Perplexity API error: {e.response.status_code} - {e.response.text}")
            raise PerplexityError(f"API error: {e.response.status_code}")
        except (KeyError, IndexError) as e:
            logger.error(f"Unexpected Perplexity response format: {e}")
            raise PerplexityError("Invalid response format from Perplexity API")
        except Exception as e:
            logger.error(f"Perplexity request failed: {e}")
            raise PerplexityError(f"Request failed: {str(e)}")

    def _build_prompt(self, title: str, description: str, article_url: str) -> str:
        """Build the prompt for article summarization."""
        prompt = f"""Please summarize this news article in 2-3 sentences:

Title: {title}

Description: {description}

Article URL: {article_url}

Provide a concise summary that captures the main points and key information."""

        return prompt

    async def rank_articles(
        self,
        articles: List[Dict[str, Any]],
        preferences: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Rank articles based on user preferences using Perplexity AI.

        Args:
            articles: List of article dicts with 'id', 'title', 'description', 'link'
            preferences: User preferences dict with 'topics', 'keywords', 'location', 'country'

        Returns:
            List of top 5 ranked articles with 'id', 'title', 'description', 'link', 'rank'
        """
        if not self.api_key:
            raise PerplexityError("Perplexity API key not configured")

        if not articles:
            return []

        # Build the prompt for ranking
        prompt = self._build_ranking_prompt(articles, preferences)

        payload = {
            "model": "sonar-pro",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a news curator helping users find the most relevant news articles. Rank articles based on the user's preferences and return only the top 5 in JSON format."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 1000,
            "temperature": 0.3
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.BASE_URL}/chat/completions",
                    headers=self.headers,
                    json=payload,
                    timeout=120.0
                )
                response.raise_for_status()
                data = response.json()

            content = data["choices"][0]["message"]["content"].strip()
            model_used = data.get("model", "sonar-pro")
            tokens_used = data.get("usage", {}).get("total_tokens")

            logger.info(f"Ranked articles using {model_used}, tokens: {tokens_used}")

            # Parse the JSON response to get ranked articles
            ranked_articles = self._parse_ranking_response(content, articles)
            return ranked_articles

        except httpx.HTTPStatusError as e:
            logger.error(f"Perplexity API error: {e.response.status_code} - {e.response.text}")
            raise PerplexityError(f"API error: {e.response.status_code}")
        except (KeyError, IndexError) as e:
            logger.error(f"Unexpected Perplexity response format: {e}")
            raise PerplexityError("Invalid response format from Perplexity API")
        except Exception as e:
            logger.error(f"Perplexity request failed: {e}")
            raise PerplexityError(f"Request failed: {str(e)}")

    def _build_ranking_prompt(
        self,
        articles: List[Dict[str, Any]],
        preferences: Dict[str, Any]
    ) -> str:
        """Build the prompt for article ranking."""
        # Build preference context
        topics = preferences.get("topics", [])
        keywords = preferences.get("keywords", [])
        location = preferences.get("location", "")
        country = preferences.get("country", "")

        preference_text = []
        if topics:
            preference_text.append(f"Interested topics: {', '.join(topics)}")
        if keywords:
            preference_text.append(f"Keywords: {', '.join(keywords)}")
        if location:
            preference_text.append(f"Location: {location}")
        if country:
            preference_text.append(f"Country: {country}")

        preferences_str = "\n".join(preference_text) if preference_text else "No specific preferences set"

        # Build articles list
        articles_text = []
        for i, article in enumerate(articles, 1):
            title = article.get("title", "")
            description = article.get("description", "") or "No description"
            articles_text.append(f"{i}. Title: {title}\n   Description: {description[:200]}...")

        articles_str = "\n\n".join(articles_text)

        prompt = f"""Based on the user's preferences:
{preferences_str}

Rank the following articles from most relevant to least relevant for this user. Return ONLY the top 5 articles in JSON format with the article number (1-{len(articles)}) as the id.

Articles:
{articles_str}

Return JSON in this exact format (no other text):
[{{"id": 1, "rank": 1}}, {{"id": 3, "rank": 2}}, {{"id": 5, "rank": 3}}, {{"id": 2, "rank": 4}}, {{"id": 4, "rank": 5}}]

Only include the top 5 articles. Use the article number as the id."""

        return prompt

    def _parse_ranking_response(
        self,
        content: str,
        articles: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Parse the ranking response from Perplexity."""
        import json

        # Try to extract JSON from the response
        try:
            # Find JSON array in the response
            start_idx = content.find("[")
            end_idx = content.rfind("]") + 1

            if start_idx != -1 and end_idx != 0:
                json_str = content[start_idx:end_idx]
                ranks = json.loads(json_str)
            else:
                # Try parsing the whole response
                ranks = json.loads(content)

            # Create a mapping of article number to rank
            rank_map = {item["id"]: item["rank"] for item in ranks}

            # Get the top 5 ranked articles
            top_5_ids = [item["id"] for item in sorted(ranks, key=lambda x: x["rank"])[:5]]

            # Filter original articles to only include top 5
            result = []
            for article_num in top_5_ids:
                # Article numbers are 1-indexed, list is 0-indexed
                if 0 < article_num <= len(articles):
                    article = articles[article_num - 1].copy()
                    article["rank"] = rank_map[article_num]
                    result.append(article)

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse ranking response: {e}")
            # Fallback: return first 5 articles
            return [{"rank": i + 1, **articles[i]} for i in range(min(5, len(articles)))]

    async def create_radio_script(
        self,
        articles: List[Dict[str, Any]]
    ) -> tuple[str, str, Optional[int]]:
        """
        Create a radio news script from top 5 articles.

        Args:
            articles: List of article dicts with 'title', 'description', 'link'

        Returns:
            Tuple of (radio_script, model_used, tokens_used)
        """
        if not self.api_key:
            raise PerplexityError("Perplexity API key not configured")

        if not articles:
            raise PerplexityError("No articles provided for radio script")

        # Build the prompt for radio script
        prompt = self._build_radio_script_prompt(articles)

        payload = {
            "model": "sonar-pro",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a professional radio news announcer. Create a 60-90 second news broadcast script reading the top 5 news stories. Start with a friendly greeting and intro, then present each story in a clear, engaging manner. End with a smooth closing. Write in a conversational, radio-style format - not bullet points."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 1500,
            "temperature": 0.5
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.BASE_URL}/chat/completions",
                    headers=self.headers,
                    json=payload,
                    timeout=120.0
                )
                response.raise_for_status()
                data = response.json()

            radio_script = data["choices"][0]["message"]["content"].strip()
            model_used = data.get("model", "sonar-pro")
            tokens_used = data.get("usage", {}).get("total_tokens")

            logger.info(f"Generated radio script using {model_used}, tokens: {tokens_used}")
            return radio_script, model_used, tokens_used

        except httpx.HTTPStatusError as e:
            logger.error(f"Perplexity API error: {e.response.status_code} - {e.response.text}")
            raise PerplexityError(f"API error: {e.response.status_code}")
        except (KeyError, IndexError) as e:
            logger.error(f"Unexpected Perplexity response format: {e}")
            raise PerplexityError("Invalid response format from Perplexity API")
        except Exception as e:
            logger.error(f"Perplexity request failed: {e}")
            raise PerplexityError(f"Request failed: {str(e)}")

    def _build_radio_script_prompt(
        self,
        articles: List[Dict[str, Any]]
    ) -> str:
        """Build the prompt for radio script generation."""
        # Build articles list with titles and descriptions
        articles_text = []
        for i, article in enumerate(articles, 1):
            title = article.get("title", "")
            description = article.get("description", "") or "No description available"
            # Truncate description to keep prompt manageable
            description = description[:300] + "..." if len(description) > 300 else description
            articles_text.append(f"Story {i}:\nTitle: {title}\nSummary: {description}")

        articles_str = "\n\n".join(articles_text)

        prompt = f"""Create a radio news broadcast script for the following top 5 stories:

{articles_str}

Write in a natural, radio announcer style. Each story should be 1-2 sentences that capture the essence. Include a brief intro and closing."""

        return prompt


class PerplexityError(Exception):
    """Raised when Perplexity API request fails."""
    pass
