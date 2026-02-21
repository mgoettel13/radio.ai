# Playlist Generation Implementation Plan

## Overview
Add functionality to generate playlists for radio stations using Perplexity AI. When users click a play button on a station card, the system will call the Perplexity API to generate a time-bounded playlist based on the station's definition.

## Architecture

```mermaid
graph TD
    A[User clicks play icon on station card] --> B[Frontend calls API /api/stations/{id}/generate-playlist]
    B --> C[Backend retrieves station from database]
    C --> D[Backend calls Perplexity with station details]
    D --> E[Perplexity returns JSON playlist]
    E --> F[Pydantic validates response - retry if invalid]
    F --> G[Return playlist to frontend]
    G --> H[Display playlist in modal for user validation]
```

## Implementation Steps

### Phase 1: Backend - Add Perplexity Playlist Method

**1.1 Add `generate_playlist` method to `backend/app/services/perplexity.py`**
- Create new method `generate_playlist(station_data: dict, duration_hours: int) -> dict`
- Use the prompt from `plans/mg_playlistGeneration.md`:
  ```
  Generate a playlist of songs for a {duration_hours}-hour radio station based on these preferences:
  - Station name: {name}
  - Description: {description}
  - Example songs: {example_songs}
  
  Return ONLY a JSON object with the following structure (no other text):
  {{
    "station_name": "string",
    "total_duration_hours": number,
    "songs": [
      {{"artist": "string", "title": "string", "year": number|null, "genre": "string", "why_this_song": "string"}}
    ]
  }}
  ```
- Implement retry logic: if JSON validation fails, call Perplexity again with a corrected prompt
- Return the validated playlist data

### Phase 2: Backend - Add API Schema

**2.1 Create new schema `backend/app/schemas/playlist.py`**
```python
class PlaylistSong(BaseModel):
    artist: str
    title: str
    year: Optional[int] = None
    genre: str
    why_this_song: str

class PlaylistResponse(BaseModel):
    station_name: str
    total_duration_hours: int
    songs: List[PlaylistSong]
```

### Phase 3: Backend - Add API Endpoint

**3.1 Add endpoint to `backend/app/routers/stations.py`**
- New POST endpoint: `/api/stations/{station_id}/generate-playlist`
- Requires authentication (use `get_current_active_user` dependency)
- Validates station belongs to current user
- Calls Perplexity service to generate playlist
- Returns `PlaylistResponse`

### Phase 4: Frontend - Add API Method

**4.1 Add method to `frontend/js/api.js`**
```javascript
async generatePlaylist(stationId) {
    return this.request(`/api/stations/${stationId}/generate-playlist`, {
        method: 'POST'
    });
}
```

### Phase 5: Frontend - Add Play Button to Station Cards

**5.1 Update `frontend/js/ui.js` - `createStationCard()` function**
- Add a play button icon (▶️) to each station card
- Position: alongside the station name or in a button area
- Add click handler that calls `app.generatePlaylist(station)`

### Phase 6: Frontend - Add Playlist Display Modal

**6.1 Add modal HTML to `frontend/index.html`**
- New modal: `playlist-modal`
- Display station name
- Display generated playlist as a list of songs
- Each song shows: artist, title, year, genre, "why this song"
- Add "Close" button

**6.2 Add modal manager in `frontend/js/app.js`**
- Add `this.playlistModal = new ModalManager('playlist-modal');` in constructor
- Add `generatePlaylist(station)` method

### Phase 7: Frontend - Add CSS Styles

**7.1 Add styles to `frontend/css/styles.css`**
- Style for play button on station cards
- Style for playlist modal content
- Style for song list display

## Files to Modify/Create

| File | Action |
|------|--------|
| `backend/app/services/perplexity.py` | Add `generate_playlist()` method |
| `backend/app/schemas/playlist.py` | Create new file with playlist schemas |
| `backend/app/routers/stations.py` | Add `POST /{station_id}/generate-playlist` endpoint |
| `frontend/js/api.js` | Add `generatePlaylist()` method |
| `frontend/js/ui.js` | Update `createStationCard()` with play button |
| `frontend/js/app.js` | Add playlist modal and `generatePlaylist()` handler |
| `frontend/index.html` | Add playlist modal HTML |
| `frontend/css/styles.css` | Add styles for new components |

## Testing Checklist

- [ ] Clicking play icon on station card triggers API call
- [ ] API validates station belongs to current user
- [ ] Perplexity is called with correct station data
- [ ] JSON response is validated by Pydantic
- [ ] Invalid JSON triggers retry logic
- [ ] Playlist displays correctly in modal
- [ ] Modal can be closed
- [ ] Error handling works for failed API calls
