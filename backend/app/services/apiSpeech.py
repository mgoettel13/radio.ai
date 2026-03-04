"""
Speechify TTS test script - Uses environment variables from .env

This script demonstrates how to use the Speechify API with proper
environment variable configuration.
"""
import os
import sys
import base64

from speechify import Speechify

# Add parent directory to path to import app config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import get_settings


def test_speechify_tts():
    """Test Speechify TTS using API key from environment variables."""
    # Get settings from environment variables
    settings = get_settings()
    api_key = settings.speechify_api_key
    
    if not api_key:
        print("Error: SPEECHIFY_API_KEY not set in environment/.env file", file=sys.stderr)
        sys.exit(1)
    
    # Initialize Speechify client with API key from env
    client = Speechify(token=api_key)
    
    # Test text
    test_text = (
        "The death toll from the January 1, 2026, fire at Le Constellation bar "
        "in Crans-Montana, Switzerland, has risen to 41 after an 18-year-old Swiss "
        "national died from injuries in a Zurich hospital on January 31."
    )
    
    print("Generating speech...", file=sys.stderr)
    
    audio_response = client.tts.audio.speech(
        input=test_text,
        voice_id="oliver",
        audio_format="mp3"
    )
    
    # Save output
    output_file = "output.mp3"
    with open(output_file, "wb") as f:
        print(f"audio_data type: {type(audio_response.audio_data)}", file=sys.stderr)
        print(f"audio_data length: {len(audio_response.audio_data) if hasattr(audio_response.audio_data, '__len__') else 'N/A'}", file=sys.stderr)
        
        # Check if it's a string that needs decoding
        if isinstance(audio_response.audio_data, str):
            print("audio_data is a string, attempting to decode from base64", file=sys.stderr)
            f.write(base64.b64decode(audio_response.audio_data))
        else:
            f.write(audio_response.audio_data)
    
    print(f"Audio saved to {output_file}", file=sys.stderr)
    
    # Play with Windows default player
    os.system(f"start {output_file}")


if __name__ == "__main__":
    test_speechify_tts()
