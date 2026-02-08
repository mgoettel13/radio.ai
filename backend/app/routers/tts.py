from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.tts import TTSRequest, TTSResponse
from app.services import SpeechifyClient

router = APIRouter(prefix="/api/tts", tags=["tts"])


@router.post("/speak", response_model=TTSResponse)
async def text_to_speech(
    request: TTSRequest
):
    """Convert text to speech using Speechify."""
    client = SpeechifyClient()

    try:
        audio_url, duration = await client.text_to_speech(
            text=request.text,
            voice_id=request.voice_id or "oliver"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"TTS generation failed: {str(e)}"
        )

    return TTSResponse(
        audio_url=audio_url,
        duration_seconds=duration
    )


@router.get("/voices")
async def list_voices():
    """List available TTS voices."""
    client = SpeechifyClient()

    try:
        voices = await client.list_voices()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to fetch voices: {str(e)}"
        )

    return {"voices": voices}
