# Implementation Plan: News Feature Integration with Music Playlist

## Overview

This plan outlines combining the news feature with the music playlist feature in the radio station system. The implementation adds news playback capabilities to radio stations with configurable options for when and how often news is played.

## Requirements Summary

1. **Expand Radio Station Model**: Add fields for:
   - A. `play_news` (boolean) - Enable/disable news playback
   - B. `play_news_at_start` (boolean) - Play news at stream start
   - C. `news_interval_minutes` (integer) - Interval for news: 15, 30, or 60 minutes

2. **UI Extension**: Add form fields in station create/edit modal with conditional enable logic

3. **Backend Abstraction**: Make news generation independent from UI, reusable by stations

4. **Stream Integration**: Insert news at beginning or intervals during music playback

5. **Controls Research**: Unified controls vs toggle controls

---

## Research: Point 5 - Playback Controls

### Current Architecture

- **Apple Music**: Uses MusicKit SDK (`MusicKit.getInstance()`) for playback control
- **TTS News**: Generates audio URL via Speechify, played in HTML `<audio>` element

### Analysis

| Approach | Description | Feasibility |
|----------|-------------|-------------|
| **Unified Controls** | Single play/pause/skip that handles both news and music seamlessly | ✅ Recommended |
| **Toggle Controls** | Separate "News" and "Music" buttons that switch context | ⚠️ Less elegant |
| **Queue Insertion** | Insert TTS audio into Apple Music queue | ❌ Not possible |

### Recommendation: Unified Controls

**Implementation Strategy:**
1. Create a `RadioPlayer` wrapper class that manages both Apple Music and TTS playback
2. Pre-generate news TTS 5 minutes before it's needed (background task)
3. When news time arrives:
   - Pause Apple Music
   - Play TTS audio
   - On TTS completion, resume Apple Music from where it left off
4. Unified controls (play/pause/skip) work for both sources

**Technical Approach:**
```
User clicks "Play" on station
    ↓
Generate playlist (existing)
    ↓
If station.play_news:
    Pre-generate news TTS audio
    Start music playback
    ↓
    Monitor elapsed time
    ↓
    At news interval:
        Pause music
        Play TTS audio
        On complete: Resume music
```

---

## Implementation Steps

### Phase 1: Database & Backend Models

#### 1.1 Expand Station Model
**File:** `backend/app/models/station.py`

Add new columns:
```python
# News configuration
play_news: Mapped[bool] = mapped_column(Boolean, default=False)
play_news_at_start: Mapped[bool] = mapped_column(Boolean, default=False)
news_interval_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 15, 30, or 60
```

#### 1.2 Update Station Schema
**File:** `backend/app/schemas/station.py`

Add to `StationCreate`, `StationUpdate`, and `StationRead`:
```python
play_news: bool = False
play_news_at_start: bool = False
news_interval_minutes: Optional[int] = None
```

#### 1.3 Database Migration
**File:** `backend/migrations/add_news_columns.sql`
```sql
ALTER TABLE station ADD COLUMN play_news BOOLEAN DEFAULT FALSE;
ALTER TABLE station ADD COLUMN play_news_at_start BOOLEAN DEFAULT FALSE;
ALTER TABLE station ADD COLUMN news_interval_minutes INTEGER;
```

#### 1.4 Update Router to Return New Fields
**File:** `backend/app/routers/stations.py`

Update `StationRead` creation to include new fields.

---

### Phase 2: Backend - News Generation Service

#### 2.1 Create News Generation Service
**File:** `backend/app/services/news_generator.py` (new)

Reuse existing `PerplexityClient.create_radio_script()` and TTS logic:
```python
class NewsGenerator:
    """Service for generating news audio for radio stations."""
    
    async def generate_news_for_station(
        self,
        user_id: UUID,
        session: AsyncSession
    ) -> dict:
        """
        Generate news audio for a station.
        Uses user preferences to get personalized news.
        Returns dict with radio_script, audio_url, duration_seconds
        """
        # 1. Get personalized news (reuse existing logic from /radio-news)
        # 2. Generate radio script using Perplexity
        # 3. Generate TTS audio
        # 4. Cache result with timestamp
        # Return: { script, audio_url, duration_seconds, generated_at }
```

#### 2.2 Add Caching Logic
- Store generated news with timestamp
- Check if cached news is still valid (e.g., less than 1 hour old)
- Optional: Trigger pre-generation 5 minutes before needed

#### 2.3 Create Station Play Endpoint
**File:** `backend/app/routers/stations.py`

Add new endpoint:
```python
@router.post("/{station_id}/play")
async def play_station(
    station_id: UUID,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Prepare station for playback.
    Returns playlist + optional news config for frontend to handle.
    """
```

---

### Phase 3: Frontend UI

#### 3.1 Update Station Modal Form
**File:** `frontend/index.html`

Add new form fields after duration selector:
```html
<!-- News Section -->
<div class="form-group station-news-section">
    <label class="checkbox-label">
        <input type="checkbox" id="station-play-news" name="play_news">
        📰 Play News
    </label>
    
    <div class="news-options" id="news-options">
        <label class="checkbox-label">
            <input type="checkbox" id="station-news-at-start" name="play_news_at_start">
            Play news at start of stream
        </label>
        
        <div class="form-group">
            <label for="station-news-interval">News interval</label>
            <select id="station-news-interval" name="news_interval_minutes">
                <option value="">Select interval</option>
                <option value="15">Every 15 minutes</option>
                <option value="30">Every 30 minutes</option>
                <option value="60">Every 60 minutes</option>
            </select>
        </div>
    </div>
</div>
```

#### 3.2 Add Conditional Enable Logic
**File:** `frontend/js/app.js`

```javascript
// In saveStation() - when populating form
document.getElementById('station-play-news').addEventListener('change', (e) => {
    const newsOptions = document.getElementById('news-options');
    const startCheckbox = document.getElementById('station-news-at-start');
    const intervalSelect = document.getElementById('station-news-interval');
    
    if (e.target.checked) {
        newsOptions.classList.remove('hidden');
    } else {
        newsOptions.classList.add('hidden');
        startCheckbox.checked = false;
        intervalSelect.value = '';
    }
});
```

#### 3.3 Update Station Card Display
**File:** `frontend/js/ui.js`

Add news indicator to station card:
```javascript
// In createStationCard()
const newsBadge = station.play_news 
    ? `<span class="station-badge" title="News enabled">📰</span>` 
    : '';
```

---

### Phase 4: Frontend - Unified Player

#### 4.1 Create RadioPlayer Wrapper
**File:** `frontend/js/radioPlayer.js` (new)

```javascript
class RadioPlayer {
    constructor(appleMusicService) {
        this.appleMusic = appleMusicService;
        this.newsAudio = new Audio();
        this.isPlayingNews = false;
        this.newsInterval = null;
        this.currentStation = null;
        this.playlist = [];
        this.currentIndex = 0;
        this.elapsedTime = 0; // seconds
    }
    
    async playStation(station, playlist) {
        this.currentStation = station;
        this.playlist = playlist;
        this.currentIndex = 0;
        this.elapsedTime = 0;
        
        // Generate news if needed
        if (station.play_news) {
            await this.prepareNews();
            
            if (station.play_news_at_start) {
                await this.playNewsFirst();
            } else if (station.news_interval_minutes) {
                this.startNewsInterval(station.news_interval_minutes);
            }
        }
        
        // Start music playback
        await this.appleMusic.playPlaylistAndRecord(
            this.playlist.map(s => s.apple_music_id),
            station.id
        );
    }
    
    async playNewsFirst() {
        this.isPlayingNews = true;
        await this.appleMusic.pause();
        
        const newsAudio = await this.fetchNewsAudio();
        this.newsAudio.src = newsAudio.audio_url;
        await this.newsAudio.play();
        
        this.newsAudio.onended = async () => {
            this.isPlayingNews = false;
            await this.appleMusic.resume();
            // Now start interval if configured
            if (this.currentStation.news_interval_minutes) {
                this.startNewsInterval(this.currentStation.news_interval_minutes);
            }
        };
    }
    
    startNewsInterval(minutes) {
        const intervalMs = minutes * 60 * 1000;
        this.newsInterval = setInterval(async () => {
            await this.playNewsSegment();
        }, intervalMs);
    }
    
    async playNewsSegment() {
        // Pause music, play news, resume
    }
    
    // Unified controls
    async play() {
        if (this.isPlayingNews) {
            await this.newsAudio.play();
        } else {
            await this.appleMusic.resume();
        }
    }
    
    async pause() {
        if (this.isPlayingNews) {
            await this.newsAudio.pause();
        } else {
            await this.appleMusic.pause();
        }
    }
    
    async togglePlayPause() {
        if (this.isPlayingNews) {
            if (this.newsAudio.paused) await this.newsAudio.play();
            else await this.newsAudio.pause();
        } else {
            await this.appleMusic.togglePlayPause();
        }
    }
}
```

#### 4.2 Update App Integration
**File:** `frontend/js/app.js`

Replace direct `appleMusic.playPlaylistAndRecord` calls with `radioPlayer.playStation()`.

#### 4.3 Add News Pre-generation
**File:** `frontend/js/radioPlayer.js`

```javascript
async prepareNews() {
    // Trigger news generation in background
    // This can be called before playback starts
    try {
        const response = await fetch(`/api/stations/${this.currentStation.id}/generate-news`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${api.token}` }
        });
        this.cachedNews = await response.json();
    } catch (error) {
        console.error('Failed to pre-generate news:', error);
    }
}
```

---

### Phase 5: Backend - News Generation Endpoint

#### 5.1 Add Station News Endpoint
**File:** `backend/app/routers/stations.py`

```python
@router.post("/{station_id}/generate-news", response_model=StationNewsResponse)
async def generate_station_news(
    station_id: UUID,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Generate news audio for a station.
    Uses user preferences to get personalized news.
    Can be called in advance to pre-cache the news.
    """
```

Add response schema:
```python
class StationNewsResponse(BaseModel):
    radio_script: str
    audio_url: str
    duration_seconds: int
    generated_at: datetime
```

---

## File Changes Summary

### New Files
| File | Description |
|------|-------------|
| `backend/app/services/news_generator.py` | Service for generating news audio |
| `backend/migrations/add_news_columns.sql` | Database migration for new columns |
| `frontend/js/radioPlayer.js` | Unified player wrapper class |

### Modified Files
| File | Changes |
|------|---------|
| `backend/app/models/station.py` | Add news columns |
| `backend/app/schemas/station.py` | Add news fields to schemas |
| `backend/app/routers/stations.py` | Add play endpoint, update read |
| `backend/app/routers/articles.py` | Refactor for reuse |
| `frontend/index.html` | Add news form fields |
| `frontend/js/app.js` | Add conditional logic, integrate player |
| `frontend/js/ui.js` | Add news badge to cards |
| `frontend/js/api.js` | Add station news endpoint |

---

## API Endpoints

```
GET    /api/stations                           - List stations (includes news config)
POST   /api/stations                           - Create station (with news config)
GET    /api/stations/{id}                      - Get station (includes news config)
PUT    /api/stations/{id}                      - Update station (with news config)
POST   /api/stations/{id}/generate-playlist    - Generate playlist (existing)
POST   /api/stations/{id}/generate-news        - Generate/pre-cache news audio (NEW)
POST   /api/stations/{id}/play                 - Prepare station for playback (NEW)
```

---

## Data Model

### Station Table (Updated)
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | UUID | Yes | Primary key |
| user_id | UUID | Yes | Foreign key to user |
| name | String(255) | Yes | Station name |
| description | Text | No | Music description |
| example_songs | JSON | No | Array of song examples |
| duration | Integer | Yes | Playlist duration (1-24) |
| image_url | String(500) | No | Station image URL |
| play_news | Boolean | No | Enable news playback (default: false) |
| play_news_at_start | Boolean | No | Play news at stream start (default: false) |
| news_interval_minutes | Integer | No | News interval: 15, 30, or 60 |
| created_at | DateTime | Yes | Creation timestamp |
| updated_at | DateTime | Yes | Last update timestamp |

---

## Implementation Order

1. **Database**: Add migration, update model and schemas
2. **Backend**: Add news generation service, update router
3. **Frontend API**: Add endpoint methods
4. **Frontend UI**: Add form fields with conditional logic
5. **Frontend Player**: Create RadioPlayer wrapper
6. **Integration**: Wire up player to station playback
7. **Testing**: Test all scenarios

---

## Acceptance Criteria

1. ✅ Station can be created/edited with news options
2. ✅ News options only enabled when "Play News" is checked
3. ✅ News uses existing user preferences (not UI-dependent)
4. ✅ News plays at start if configured
5. ✅ News plays at intervals (15/30/60 min) if configured
6. ✅ Music resumes after news segment completes
7. ✅ Unified controls work for both news and music
8. ✅ News can be pre-generated/cached for smoother playback
