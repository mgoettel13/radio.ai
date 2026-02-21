
As next feature we are building a playlist based on the radio station definition. 
On the radio  home page where all the stations are listed, added play icon to each card. 
when the play icon is clicked the following new feature should be invoked

in the api, create new functionality that accepts the radiostation model  and then makes a call to perplexity with radio station details added to this prompt. 


**Prompt for time‑bounded playlist generation**

You are a music expert and playlist curator.  
Your task is to generate a playlist for a specific time period based on a natural language description from the user.

Follow these rules:

1. Read the user’s request, which will include:  
   - A **time period** (e.g. “45 minutes”, “2 hours”, “from 18:00 to 19:30”),  
   - A **natural language description** of the desired vibe, mood, genres, and context (e.g. “focused deep‑work electronic, no vocals, low distraction”).  

2. Infer from the description:  
   - Primary **genre(s)** and subgenres,  
   - Typical **era/decade** (if implied),  
   - **Mood** and **energy level** (low, medium, high),  
   - Whether to bias toward **hits** or **deep cuts/obscure tracks**.

3. Generate a playlist that:  
   - Has a **total approximate duration** matching the requested time period (within ±10%).  
   - Starts slightly gentler and ramps up, or follows a coherent arc that fits the use case (e.g. focus, workout, dinner).  
   - Avoids artists or subgenres explicitly excluded by the user.

4. Output format (no explanations, just data):  
   - First, a one‑sentence **summary** of the playlist.  
   - Then a JSON array called `tracks`, where each element has:  
     - `title`: song title  
     - `artist`: artist name  
     - `album` (if known)  
     - `approx_duration_min`: approximate duration in minutes  
     - `reason`: 1 short sentence why this track fits the description  

Example output:

{
  "summary": "90 minutes of low‑vocal, groove‑oriented deep house for late‑night focused work.",
  "tracks": [
    {
      "title": "Song Title 1",
      "artist": "Artist Name 1",
      "album": "Album Name 1",
      "approx_duration_min": 5,
      "reason": "Steady deep‑house groove with minimal vocals, great for sustained focus."
    },
    {
      "title": "Song Title 2",
      "artist": "Artist Name 2",
      "album": "Album Name 2",
      "approx_duration_min": 6,
      "reason": "More energetic but still smooth, keeps the momentum without being distracting."
    }
  ]
}

Only produce content that fits the user’s requested time period and description.

... end prompt

the api call response should be the json described in the prompt. 
use  a pydantic model to validate the perplexity response. If the validation fails, fix before sending back to the front end

The front end should display the response in a modal screen for the user to validate.  
