import base64
import logging
from typing import Optional

from speechify import Speechify

from app.config import get_settings

logger = logging.getLogger(__name__)


class SpeechifyClient:
    """Speechify TTS client using the official Python SDK."""

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.speechify_api_key
        print("Speechify API Key:", self.api_key)
        self._client = Speechify(token=self.api_key)

    async def text_to_speech(
        self,
        text: str,
        voice_id: str = "oliver",
        audio_format: str = "mp3"
    ) -> tuple[str, Optional[float]]:
        """
        Convert text to speech using Speechify SDK.

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

        try:
            # Use SDK for TTS request
            logger.debug(f"Calling SDK with text={text[:50]}..., voice_id={voice_id}")
            response = self._client.tts.audio.speech(
             #   input="The death toll from the January 1, 2026, fire at Le Constellation bar in Crans-Montana, Switzerland, has risen to 41 after an 18-year-old Swiss national died from injuries in a Zurich hospital on January 31.[1][4] The blaze, which started in the crowded basement during New Year's celebrations when sparklers on champagne bottles ignited flammable ceiling insulation, injured over 100 people, many with severe burns, amid reports of a blocked emergency exit and inadequate fire safety measures.[2][3] Swiss prosecutors have launched a criminal investigation into the bar owners for negligent homicide, bodily harm, and arson, with one co-owner under bail and his wife under house arrest.[3][4]",
                input=str(text),
                voice_id="oliver",
                audio_format="mp3"  
            )
            
            logger.info("Speechify SDK response received")

            # SDK returns an object with audio_data (base64 string or bytes)
            if hasattr(response, 'audio_data'):
                audio_data = response.audio_data
                if isinstance(audio_data, bytes):
                    # Convert bytes to base64 data URL
                    audio_b64 = base64.b64encode(audio_data).decode('utf-8')
                    audio_url = f"data:audio/{audio_format};base64,{audio_b64}"
                elif isinstance(audio_data, str):
                    # audio_data is already base64 encoded string
                    audio_url = f"data:audio/{audio_format};base64,{audio_data}"
                else:
                    raise SpeechifyError(f"Unexpected audio_data type: {type(audio_data)}")
            else:
                raise SpeechifyError("Response missing audio_data attribute")

            # Get duration from response metadata if available
            duration = getattr(response, 'duration', None)

            logger.info(f"Generated TTS audio, duration: {duration}")
            return audio_url, duration

        except Exception as e:
            logger.error(f"Speechify SDK error: {type(e).__name__}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise SpeechifyError(f"SDK error: {str(e)}")

    async def list_voices(self) -> list[dict]:
        """List available voices from Speechify SDK."""
        if not self.api_key:
            raise SpeechifyError("Speechify API key not configured")

        try:
            voices_response = self._client.tts.voices.list()

            # SDK returns list of voice objects
            return [
                {
                    "id": v.id if hasattr(v, 'id') else v.get('id'),
                    "name": v.display_name if hasattr(v, 'display_name') else v.get('display_name', v.get('id')),
                    "gender": v.gender if hasattr(v, 'gender') else v.get('gender', 'unknown'),
                    "language": v.locale if hasattr(v, 'locale') else v.get('locale', 'en')
                }
                for v in voices_response
            ]

        except Exception as e:
            logger.error(f"Speechify SDK error: {e}")
            raise SpeechifyError(f"SDK error: {str(e)}")


class SpeechifyError(Exception):
    """Raised when Speechify API request fails."""
    pass
