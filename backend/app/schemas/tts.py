from typing import Optional

from pydantic import BaseModel


class TTSRequest(BaseModel):
    text: str
    voice_id: Optional[str] = "matthew"


class TTSResponse(BaseModel):
    audio_url: str
    duration_seconds: Optional[float] = None
