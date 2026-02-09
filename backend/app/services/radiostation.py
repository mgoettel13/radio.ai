import os
import json
import httpx
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional

# --- Configuration ---
# To use Perplexity (Paid but reliable + web aware):
# API_KEY = os.getenv("PERPLEXITY_API_KEY")
# BASE_URL = "https://api.perplexity.ai"
# MODEL_NAME = "sonar" 

# To use Groq (Free tier available, extremely fast):
# API_KEY = os.getenv("GROQ_API_KEY")
# BASE_URL = "https://api.groq.com/openai/v1"
# MODEL_NAME = "llama3-70b-8192"

router = APIRouter()

# --- Data Models ---
class DJRequest(BaseModel):
    genres: List[str]
    bands: List[str]
    decade: str
    mood: Optional[str] = "energetic"

class Track(BaseModel):
    artist: str
    title: str
    dj_intro: str
    reasoning: str

class DJResponse(BaseModel):
    playlist_title: str
    vibe_description: str
    tracks: List[Track]

# --- The System Prompt ---
SYSTEM_PROMPT = """
You are "The Architect," an expert music curator and radio DJ engine. 
Your goal is to generate a cohesive, continuous stream of music based on specific user constraints.

## YOUR TASK:
1. Analyze the intersection of the input parameters.
2. Select 10 specific songs that perfectly blend these inputs.
   - Include deep cuts (not just top hits).
   - Ensure variety in tempo but consistency in vibe.
   - Include 1-2 "discovery" tracks from artists similar to the seeds but not listed.
3. For each song, generate a short 1-sentence "DJ Intro" that connects the previous song to the current one.

## OUTPUT FORMAT:
You must output ONLY valid JSON. Do not include markdown formatting like ```json.
{
  "playlist_title": "Creative name",
  "vibe_description": "Short description",
  "tracks": [
    {
      "artist": "Exact Artist Name",
      "title": "Exact Song Title",
      "dj_intro": "Spoken intro text",
      "reasoning": "Why this fits"
    }
  ]
}
"""

@router.post("/generate-playlist", response_model=DJResponse)
async def generate_playlist(request: DJRequest):
    """
    Calls the LLM to generate a playlist with DJ commentary.
    """
    
    # Construct the User Prompt
    user_content = f"""
    PARAMS:
    - Genres: {', '.join(request.genres)}
    - Decade: {request.decade}
    - Seed Bands: {', '.join(request.bands)}
    - Mood: {request.mood}
    """

    headers = {
        "Authorization": f"Bearer {os.getenv('PERPLEXITY_API_KEY')}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "sonar", # Use 'sonar' for speed/cost or 'sonar-pro' for better reasoning
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content}
        ],
        "temperature": 0.7,
        "max_tokens": 3000
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://api.perplexity.ai/chat/completions", 
                json=payload, 
                headers=headers,
                timeout=30.0
            )
            response.raise_for_status()
            
            # Parse the response
            data = response.json()
            raw_content = data['choices']['message']['content']
            
            # Clean up potential markdown formatting if the LLM slips up
            clean_json = raw_content.replace("```json", "").replace("```", "").strip()
            
            return json.loads(clean_json)

        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"LLM Provider Error: {e.response.text}")
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="LLM returned invalid JSON. Please try again.")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
