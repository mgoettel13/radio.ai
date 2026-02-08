import base64
import logging
from typing import Optional

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


class SpeechifyClient:
    BASE_URL = "https://api.sws.speechify.com"

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.speechify_api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def text_to_speech(
        self,
        text: str,
        voice_id: str = "oliver"
    ) -> tuple[str, Optional[float]]:
        """
        Convert text to speech using Speechify API.

        Returns:
            Tuple of (audio_url_or_base64, duration_seconds)
        """
        if not self.api_key:
            raise SpeechifyError("Speechify API key not configured")

        # Truncate text if too long (Speechify has limits)
        max_chars = 5000
        if len(text) > max_chars:
            logger.warning(f"Text too long ({len(text)} chars), truncating to {max_chars}")
            text = text[:max_chars] + "..."

        payload = {
            "input": text,
            "voice_id": voice_id,
            "audio_format": "mp3"
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.BASE_URL}/v1/audio/speech",
                    headers=self.headers,
                    json=payload,
                    timeout=60.0
                )
                client.
                response.raise_for_status()
                data = response.json()

            # Speechify returns audio data in different formats depending on the endpoint
            # Check if we got a URL or base64 audio data
            if "audio_data" in data:
                # Base64 encoded audio
                audio_data = data["audio_data"]
                # Create a data URL
                audio_url = f"data:audio/mp3;base64,{audio_data}"
            elif "url" in data:
                audio_url = data["url"]
            else:
                raise SpeechifyError("No audio data in response")

            duration = data.get("duration")

            logger.info(f"Generated TTS audio, duration: {duration}")
            return audio_url, duration

        except httpx.HTTPStatusError as e:
            logger.error(f"Speechify API error: {e.response.status_code} - {e.response.text}")
            raise SpeechifyError(f"API error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Speechify request failed: {e}")
            raise SpeechifyError(f"Request failed: {str(e)}")

    async def list_voices(self) -> list[dict]:
        """List available voices from Speechify."""
        if not self.api_key:
            raise SpeechifyError("Speechify API key not configured")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/v1/voices",
                    headers=self.headers,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()

            voices = data.get("voices", [])
            return [
                {
                    "id": v.get("id"),
                    "name": v.get("display_name", v.get("id")),
                    "gender": v.get("gender", "unknown"),
                    "language": v.get("language", "en")
                }
                for v in voices
            ]

        except httpx.HTTPStatusError as e:
            logger.error(f"Speechify API error: {e.response.status_code}")
            raise SpeechifyError(f"API error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Speechify request failed: {e}")
            raise SpeechifyError(f"Request failed: {str(e)}")


class SpeechifyError(Exception):
    """Raised when Speechify API request fails."""
    pass
