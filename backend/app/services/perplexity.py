import logging
from typing import Optional

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


class PerplexityError(Exception):
    """Raised when Perplexity API request fails."""
    pass
