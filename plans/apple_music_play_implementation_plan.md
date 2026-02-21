# Apple Music Play Functionality Implementation Plan

## Research Summary

### Key Findings

**Approach Selected: Option A - Direct Queue (Lookup Each Song Individually)**

The implementation will:
1. For each song in the generated playlist (artist + title)
2. Search Apple Music catalog to get Apple Music ID
3. If song not found → remove from playlist
4. Add valid songs to playback queue
5. Play sequentially

**Error Handling:**
- If a song is not found on Apple Music or cannot be located → **remove it from the playlist**
- Continue with remaining songs

---

## Architecture

```mermaid
graph TD
    A[Generated Playlist: Artist + Title] --> B[For each song]
    B --> C[Search Apple Music: /v1/catalog/us/search?term={artist}+{title}&types=songs]
    C --> D{Song Found?}
    D -->|Yes| E[Get Apple Music song ID]
    D -->|No| F[Remove song from playlist - log warning]
    E --> G[Add to valid songs list]
    G --> H{More songs?}
    H -->|Yes| B
    H -->|No| I[music.setQueue validSongIds]
    I --> J[music.play()]
```

---

## Implementation Steps

### Phase 1: Backend - Apple Music Service (FastAPI)

Create a dedicated Apple Music service, **separate from playlist functionality**.

#### 1.1 Add Configuration to `backend/app/config.py`
```python
class Settings(BaseSettings):
    # Apple Music API Configuration
    apple_music_team_id: str = "DH3467C58U"
    apple_music_key_id: str = "3CXU6RHQ6R"
    apple_music_key_path: str = "C:/shared/Dev/kilo_ai/RSS_Feed/Apple/AuthKey_3CXU6RHQ6R.p8"
```

#### 1.2 Add Dependencies in `backend/app/main.py`
- Add `PyJWT` to `requirements.txt`
- Add `httpx` to `requirements.txt`

#### 1.3 Create Token Generator (based on [`Apple/apple_token_and_test.py`](Apple/apple_token_and_test.py))
Create `backend/app/services/apple_music_token.py`:
```python
import jwt
import time
from pathlib import Path

def generate_apple_music_token(key_path: str, key_id: str, team_id: str) -> str:
    """Generate JWT bearer token for Apple Music API."""
    with open(key_path, "r") as f:
        private_key = f.read()
    
    payload = {
        "iss": team_id,
        "iat": int(time.time()),
        "exp": int(time.time()) + (3600 * 24 * 30),  # 30 days max
    }
    return jwt.encode(
        payload,
        private_key,
        algorithm="ES256",
        headers={"kid": key_id},
    )
```

#### 1.4 Create Apple Music Service in `backend/app/services/apple_music.py`
```python
import httpx
from typing import Optional, List, Dict
from backend.app.config import get_settings
from backend.app.services.apple_music_token import generate_apple_music_token

class AppleMusicService:
    def __init__(self):
        self.settings = get_settings()
        self._token = None
        self.base_url = "https://api.music.apple.com/v1"
    
    def _get_token(self) -> str:
        """Get or generate bearer token."""
        if not self._token:
            self._token = generate_apple_music_token(
                key_path=self.settings.apple_music_key_path,
                key_id=self.settings.apple_music_key_id,
                team_id=self.settings.apple_music_team_id
            )
        return self._token
    
    async def search_song(self, artist: str, title: str) -> Optional[Dict]:
        """Search for a song by artist and title. Returns song data or None if not found."""
        token = self._get_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        term = f"{artist} {title}".strip()
        url = f"{self.base_url}/catalog/us/search"
        params = {"term": term, "types": "songs", "limit": 1}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            songs = data.get("results", {}).get("songs", {}).get("data", [])
            
            if songs:
                return songs[0]  # Return first match
            return None
    
    async def resolve_playlist(self, songs: List[Dict]) -> List[Dict]:
        """
        Resolve playlist songs to Apple Music IDs.
        Removes songs that cannot be found.
        
        Input: [{"artist": "...", "title": "..."}, ...]
        Output: [{"artist": "...", "title": "...", "apple_music_id": "...", "playback_url": "..."}, ...]
        """
        resolved_songs = []
        
        for song in songs:
            artist = song.get("artist")
            title = song.get("title")
            
            result = await self.search_song(artist, title)
            
            if result:
                song_data = {
                    "artist": artist,
                    "title": title,
                    "apple_music_id": result.get("id"),
                    "name": result.get("attributes", {}).get("name"),
                    "duration_ms": result.get("attributes", {}).get("durationInMillis"),
                    "artwork": result.get("attributes", {}).get("artwork"),
                    "playback_url": result.get("attributes", {}).get("url"),
                }
                resolved_songs.append(song_data)
            else:
                # Song not found - log warning and skip
                print(f"⚠️ Song not found on Apple Music: {artist} - {title}")
        
        return resolved_songs
```

---

### Phase 2: Backend - Apple Music Router

#### 2.1 Create Router in `backend/app/routers/apple_music.py`
```python
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from backend.app.schemas.apple_music import (
    PlaylistResolveRequest,
    PlaylistResolveResponse,
    ResolvedSong
)
from backend.app.services.apple_music import AppleMusicService
from backend.app.auth.dependencies import get_current_active_user

router = APIRouter(prefix="/api/apple-music", tags=["Apple Music"])

@router.post("/resolve-playlist", response_model=PlaylistResolveResponse)
async def resolve_playlist(
    request: PlaylistResolveRequest,
    current_user = Depends(get_current_active_user)
):
    """
    Resolve a playlist of songs to Apple Music IDs.
    Songs not found on Apple Music will be removed from the list.
    """
    service = AppleMusicService()
    
    # Convert request to list of dicts
    songs = [{"artist": s.artist, "title": s.title} for s in request.songs]
    
    resolved = await service.resolve_playlist(songs)
    
    return PlaylistResolveResponse(
        original_count=len(request.songs),
        resolved_count=len(resolved),
        songs=resolved
    )
```

#### 2.2 Create Schemas in `backend/app/schemas/apple_music.py`
```python
from pydantic import BaseModel, Field
from typing import List, Optional

class SongInput(BaseModel):
    artist: str = Field(..., description="Artist name")
    title: str = Field(..., description="Song title")

class PlaylistResolveRequest(BaseModel):
    songs: List[SongInput] = Field(..., description="List of songs to resolve")

class ResolvedSong(BaseModel):
    artist: str
    title: str
    apple_music_id: str
    name: Optional[str] = None
    duration_ms: Optional[int] = None
    artwork: Optional[dict] = None
    playback_url: Optional[str] = None

class PlaylistResolveResponse(BaseModel):
    original_count: int
    resolved_count: int
    songs: List[ResolvedSong]
```

#### 2.3 Register Router in `backend/app/main.py`
```python
from backend.app.routers import apple_music
app.include_router(apple_music.router)
```

---

### Phase 3: Frontend - MusicKit Integration

#### 3.1 Add MusicKit JS to `frontend/index.html`
```html
<script src="https://js-cdn.music.apple.com/musickit/v3/musickit.js"></script>
```

#### 3.2 Create AppleMusicService in `frontend/js/services/appleMusic.js`
```javascript
class AppleMusicService {
    constructor() {
        this.music = null;
        this.authorized = false;
    }

    async init() {
        this.music = MusicKit.getInstance();
        // Configure with your MusicKit token if needed
    }

    async authorize() {
        if (!this.music) await this.init();
        try {
            await this.music.authorize();
            this.authorized = true;
            return true;
        } catch (error) {
            console.error('Authorization failed:', error);
            return false;
        }
    }

    async resolvePlaylist(songs, authToken) {
        const response = await fetch('/api/apple-music/resolve-playlist', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ songs })
        });
        
        if (!response.ok) {
            throw new Error('Failed to resolve playlist');
        }
        
        return response.json();
    }

    async playSong(appleMusicId) {
        await this.music.setQueue({ songs: [appleMusicId] });
        await this.music.play();
    }

    async playPlaylist(appleMusicIds) {
        await this.music.setQueue({ songs: appleMusicIds });
        await this.music.play();
    }
}
```

---

### Phase 4: Frontend - Playlist Player UI

#### 4.1 Update Playlist Modal
- Add Play button for each song
- Add "Play All" button
- Show resolved songs (with Apple Music info)
- Show removed songs warning

#### 4.2 Add Player Controls
- Play/Pause button
- Next/Previous buttons
- Progress bar
- Current song display

---

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `Apple/AuthKey_3CXU6RHQ6R.p8` | Use existing | Private key for token generation |
| `backend/app/config.py` | Modify | Add Apple Music config (team_id, key_id, key_path) |
| `backend/requirements.txt` | Modify | Add PyJWT, httpx |
| `backend/app/services/apple_music_token.py` | Create | Token generator (from example) |
| `backend/app/services/apple_music.py` | Create | Apple Music API service |
| `backend/app/schemas/apple_music.py` | Create | Request/response schemas |
| `backend/app/routers/apple_music.py` | Create | FastAPI router |
| `backend/app/main.py` | Modify | Register Apple Music router |
| `frontend/index.html` | Modify | Add MusicKit JS script |
| `frontend/js/services/appleMusic.js` | Create | Frontend Apple Music service |
| `frontend/js/app.js` | Modify | Integrate player logic |
| `frontend/css/styles.css` | Modify | Player styling |

---

## API Reference

### Backend Endpoint: POST /api/apple-music/resolve-playlist

**Request:**
```json
{
  "songs": [
    {"artist": "Queen", "title": "Bohemian Rhapsody"},
    {"artist": "Unknown Artist", "title": "Nonexistent Song"}
  ]
}
```

**Response:**
```json
{
  "original_count": 2,
  "resolved_count": 1,
  "songs": [
    {
      "artist": "Queen",
      "title": "Bohemian Rhapsody",
      "apple_music_id": "123456789",
      "name": "Bohemian Rhapsody",
      "duration_ms": 354000,
      "playback_url": "https://music.apple.com/..."
    }
  ]
}
```

### Apple Music Search API
```
GET /v1/catalog/us/search?term={artist}+{title}&types=songs&limit=1
Headers: Authorization: Bearer {token}
```

---

## Important Considerations

1. **Bearer Token Generation**: Uses ES256 algorithm with .p8 private key
2. **Certificate Path**: `C:\shared\Dev\kilo_ai\RSS_Feed\Apple\AuthKey_3CXU6RHQ6R.p8`
3. **Token Expiration**: 30 days (max 6 months)
4. **Search Accuracy**: Uses first result - may need fuzzy matching
5. **Rate Limits**: Apple Music API has rate limits
6. **Storefront**: Uses 'us' (can be made configurable)

---

## Token Expiration & Storage

### Token Types

| Token | Purpose | Expiration | Storage |
|-------|---------|------------|--------|
| **Developer Token** | API access (catalog search) | Up to 6 months (we generate it) | Backend config `.env` |
| **Music User Token (MUT)** | User authorization for playback | Managed by MusicKit JS (browser session) | Browser only - NOT stored in DB |

### Important: MUT Cannot Be Stored in Database

The **Music User Token (MUT)** is:
- Tied to the user's browser session
- Managed automatically by MusicKit JS
- Stored in browser's localStorage by MusicKit
- Cannot be transferred between devices or stored server-side

**What we CAN store in DB:**
- Whether user has Apple Music subscription (boolean)
- Last authorization timestamp
- Subscription status (active/inactive)

**Flow:**
1. User clicks "Connect Apple Music" in settings
2. MusicKit JS triggers browser authorization popup
3. User signs in to Apple Music in browser
4. MusicKit stores MUT in browser localStorage
5. We store subscription status in database
6. On return visits, if MUT is valid, no re-auth needed

---

## New Phase: Apple Music Settings Page

### Phase 5: Database - Extend UserPreferences

#### 5.1 Update `backend/app/models/user_preferences.py`
Add Apple Music subscription fields:
```python
class UserPreferences(Base):
    # ... existing fields ...
    
    # Apple Music Subscription
    apple_music_connected: Mapped[bool] = mapped_column(Boolean, default=False)
    apple_music_subscription_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # 'individual', 'family', 'student'
    apple_music_authorized_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    apple_music_storefront: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # 'us', 'gb', etc.
```

#### 5.2 Update `backend/app/schemas/settings.py`
Add Apple Music settings schemas:
```python
class AppleMusicSettings(BaseModel):
    apple_music_connected: bool
    apple_music_subscription_type: Optional[str] = None
    apple_music_authorized_at: Optional[datetime] = None
    apple_music_storefront: Optional[str] = None

class AppleMusicSettingsUpdate(BaseModel):
    apple_music_connected: bool
    apple_music_subscription_type: Optional[str] = None
    apple_music_storefront: Optional[str] = None
```

---

### Phase 6: Backend - Apple Music Settings Endpoint

#### 6.1 Add endpoint to `backend/app/routers/settings.py`
```python
@router.put("/settings/apple-music", response_model=AppleMusicSettings)
async def update_apple_music_settings(
    settings: AppleMusicSettingsUpdate,
    current_user = Depends(get_current_active_user)
):
    """Update Apple Music subscription settings."""
    # Get or create user preferences
    prefs = await get_or_create_user_preferences(current_user.id)
    
    prefs.apple_music_connected = settings.apple_music_connected
    prefs.apple_music_subscription_type = settings.apple_music_subscription_type
    prefs.apple_music_storefront = settings.apple_music_storefront
    
    if settings.apple_music_connected:
        prefs.apple_music_authorized_at = datetime.utcnow()
    
    await prefs.save()
    
    return AppleMusicSettings(
        apple_music_connected=prefs.apple_music_connected,
        apple_music_subscription_type=prefs.apple_music_subscription_type,
        apple_music_authorized_at=prefs.apple_music_authorized_at,
        apple_music_storefront=prefs.apple_music_storefront
    )
```

---

### Phase 7: Frontend - Apple Music Settings Page

#### 7.1 Add section to Settings in `frontend/index.html`
```html
<section id="apple-music-settings" class="settings-section">
    <h2>Apple Music</h2>
    <div class="setting-group">
        <label>Subscription Status</label>
        <span id="apple-music-status" class="status-badge">Not Connected</span>
    </div>
    <div class="setting-group">
        <button id="btn-connect-apple-music" class="btn-primary">
            Connect Apple Music
        </button>
    </div>
</section>
```

#### 7.2 Add Apple Music settings logic in `frontend/js/settings.js`
```javascript
class AppleMusicSettings {
    constructor() {
        this.music = null;
    }

    async init() {
        this.music = MusicKit.getInstance();
        await this.loadSettings();
    }

    async loadSettings() {
        const response = await api.getSettings();
        this.updateUI(response.apple_music_connected);
    }

    async connect() {
        try {
            // Trigger MusicKit authorization
            await this.music.authorize();
            
            // Update backend with subscription status
            await api.updateAppleMusicSettings({
                apple_music_connected: true,
                apple_music_storefront: this.music.storefrontId
            });
            
            this.updateUI(true);
        } catch (error) {
            console.error('Failed to connect Apple Music:', error);
        }
    }

    updateUI(connected) {
        const statusEl = document.getElementById('apple-music-status');
        const btnEl = document.getElementById('btn-connect-apple-music');
        
        if (connected) {
            statusEl.textContent = 'Connected';
            statusEl.classList.add('connected');
            btnEl.textContent = 'Re-authorize';
        } else {
            statusEl.textContent = 'Not Connected';
            statusEl.classList.remove('connected');
            btnEl.textContent = 'Connect Apple Music';
        }
    }
}
```

---

### Phase 8: Integration - Check Subscription Before Playback

#### 8.1 Update frontend player to check subscription
```javascript
async playPlaylist(songs) {
    // Check if Apple Music is connected
    const settings = await api.getSettings();
    
    if (!settings.apple_music_connected) {
        // Prompt user to connect first
        showModal('Please connect Apple Music in Settings first');
        return;
    }
    
    // Check if MusicKit is authorized
    const music = MusicKit.getInstance();
    try {
        await music.authorize();  // Will resolve if already authorized
        
        // Proceed with playback
        const ids = songs.map(s => s.apple_music_id);
        await music.setQueue({ songs: ids });
        await music.play();
    } catch (error) {
        console.error('Playback failed:', error);
    }
}
```

---

## New Phase: Played Music Tracking

### Phase 9: Database - Create PlayedMusic Table

#### 9.1 Create `backend/app/models/played_music.py`
```python
"""
PlayedMusic model for tracking songs that have been played.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.station import Station


class PlayedMusic(Base):
    """
    Track played songs with play count and date.
    """
    __tablename__ = "played_music"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    station_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("station.id", ondelete="CASCADE"), 
        nullable=True,
        index=True
    )
    song_id: Mapped[str] = mapped_column(String(100), nullable=False)  # Apple Music song ID
    artist: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    play_date: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        nullable=False
    )
    play_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="played_music")
    station: Mapped["Station"] = relationship("Station", back_populates="played_music")
    
    def __repr__(self) -> str:
        return f"<PlayedMusic {self.artist} - {self.title} for user {self.user_id}>"
```

#### 9.2 Update `backend/app/models/__init__.py`
```python
from app.models.played_music import PlayedMusic
```

#### 9.3 Update `backend/app/models/user.py`
Add relationship:
```python
# In User class
played_music: Mapped[list["PlayedMusic"]] = relationship(
    "PlayedMusic", back_populates="user", cascade="all, delete-orphan"
)
```

#### 9.4 Update `backend/app/models/station.py`
Add relationship:
```python
# In Station class
played_music: Mapped[list["PlayedMusic"]] = relationship(
    "PlayedMusic", back_populates="station", cascade="all, delete-orphan"
)
```

---

### Phase 10: Backend - PlayedMusic CRUD

#### 10.1 Create Schemas in `backend/app/schemas/played_music.py`
```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid

class PlayedMusicBase(BaseModel):
    song_id: str = Field(..., description="Apple Music song ID")
    artist: str = Field(..., description="Artist name")
    title: str = Field(..., description="Song title")
    station_id: Optional[uuid.UUID] = Field(None, description="Station ID if applicable")

class PlayedMusicCreate(PlayedMusicBase):
    pass

class PlayedMusicResponse(PlayedMusicBase):
    id: uuid.UUID
    user_id: uuid.UUID
    play_date: datetime
    play_count: int
    
    class Config:
        from_attributes = True

class PlayedMusicUpdate(BaseModel):
    play_count: Optional[int] = None

class PlayedMusicListResponse(BaseModel):
    songs: list[PlayedMusicResponse]
    total: int
```

#### 10.2 Create Service in `backend/app/services/played_music.py`
```python
import uuid
from typing import Optional
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.played_music import PlayedMusic

class PlayedMusicService:
    def __init__(self, db: Session):
        self.db = db
    
    async def record_play(
        self, 
        user_id: uuid.UUID, 
        song_id: str, 
        artist: str, 
        title: str,
        station_id: Optional[uuid.UUID] = None
    ) -> PlayedMusic:
        """Record a song play. If already played, increment play_count."""
        
        # Check if song already played by this user
        existing = await self.db.execute(
            select(PlayedMusic).where(
                PlayedMusic.user_id == user_id,
                PlayedMusic.song_id == song_id
            )
        )
        existing = existing.scalar_one_or_none()
        
        if existing:
            # Increment play count
            existing.play_count += 1
            existing.play_date = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(existing)
            return existing
        
        # Create new record
        played = PlayedMusic(
            user_id=user_id,
            song_id=song_id,
            artist=artist,
            title=title,
            station_id=station_id,
            play_count=1
        )
        self.db.add(played)
        await self.db.commit()
        await self.db.refresh(played)
        return played
    
    async def get_user_plays(
        self, 
        user_id: uuid.UUID, 
        limit: int = 50,
        offset: int = 0
    ) -> tuple[list[PlayedMusic], int]:
        """Get all plays for a user."""
        
        # Get total count
        count_result = await self.db.execute(
            select(func.count()).where(PlayedMusic.user_id == user_id)
        )
        total = count_result.scalar()
        
        # Get paginated results
        result = await self.db.execute(
            select(PlayedMusic)
            .where(PlayedMusic.user_id == user_id)
            .order_by(PlayedMusic.play_date.desc())
            .limit(limit)
            .offset(offset)
        )
        songs = result.scalars().all()
        
        return list(songs), total
    
    async def get_station_plays(
        self, 
        station_id: uuid.UUID, 
        limit: int = 50
    ) -> list[PlayedMusic]:
        """Get plays for a specific station."""
        result = await self.db.execute(
            select(PlayedMusic)
            .where(PlayedMusic.station_id == station_id)
            .order_by(PlayedMusic.play_date.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_most_played(
        self, 
        user_id: uuid.UUID, 
        limit: int = 10
    ) -> list[PlayedMusic]:
        """Get most played songs for a user."""
        result = await self.db.execute(
            select(PlayedMusic)
            .where(PlayedMusic.user_id == user_id)
            .order_by(PlayedMusic.play_count.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
```

#### 10.3 Create Router in `backend/app/routers/played_music.py`
```python
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
import uuid

from app.schemas.played_music import (
    PlayedMusicCreate,
    PlayedMusicResponse,
    PlayedMusicListResponse
)
from app.services.played_music import PlayedMusicService
from app.auth.dependencies import get_current_active_user
from app.models.user import User
from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/played-music", tags=["Played Music"])

@router.post("", response_model=PlayedMusicResponse)
async def record_play(
    play_data: PlayedMusicCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Record a song play. Increments play_count if already played."""
    service = PlayedMusicService(db)
    played = await service.record_play(
        user_id=current_user.id,
        song_id=play_data.song_id,
        artist=play_data.artist,
        title=play_data.title,
        station_id=play_data.station_id
    )
    return played

@router.get("", response_model=PlayedMusicListResponse)
async def get_my_plays(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all songs played by the current user."""
    service = PlayedMusicService(db)
    songs, total = await service.get_user_plays(
        user_id=current_user.id,
        limit=limit,
        offset=offset
    )
    return PlayedMusicListResponse(songs=songs, total=total)

@router.get("/most-played", response_model=list[PlayedMusicResponse])
async def get_most_played(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get most played songs for the current user."""
    service = PlayedMusicService(db)
    songs = await service.get_most_played(
        user_id=current_user.id,
        limit=limit
    )
    return songs

@router.get("/station/{station_id}", response_model=list[PlayedMusicResponse])
async def get_station_plays(
    station_id: uuid.UUID,
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get play history for a specific station."""
    service = PlayedMusicService(db)
    songs = await service.get_station_plays(
        station_id=station_id,
        limit=limit
    )
    return songs
```

#### 10.4 Register Router in `backend/app/main.py`
```python
from backend.app.routers import played_music
app.include_router(played_music.router)
```

---

### Phase 11: Frontend - Played Music Integration

#### 11.1 Add API methods in `frontend/js/api.js`
```javascript
async recordPlay(songData) {
    return this.request('/api/played-music', {
        method: 'POST',
        body: JSON.stringify(songData)
    });
}

async getMyPlays(limit = 50, offset = 0) {
    return this.request(`/api/played-music?limit=${limit}&offset=${offset}`);
}

async getMostPlayed(limit = 10) {
    return this.request(`/api/played-music/most-played?limit=${limit}`);
}

async getStationPlays(stationId, limit = 50) {
    return this.request(`/api/played-music/station/${stationId}?limit=${limit}`);
}
```

#### 11.2 Integrate with Player in `frontend/js/services/appleMusic.js`
```javascript
async playSong(appleMusicId, artist, title, stationId = null) {
    // Start playback
    await this.music.setQueue({ songs: [appleMusicId] });
    await this.music.play();
    
    // Record play in database
    try {
        await api.recordPlay({
            song_id: appleMusicId,
            artist: artist,
            title: title,
            station_id: stationId
        });
    } catch (error) {
        console.error('Failed to record play:', error);
    }
}

async playPlaylist(appleMusicIds, songs, stationId = null) {
    // Play first song
    const firstSong = songs[0];
    await this.playSong(
        firstSong.apple_music_id,
        firstSong.artist,
        firstSong.title,
        stationId
    );
    
    // Queue remaining songs
    const remainingIds = appleMusicIds.slice(1);
    if (remainingIds.length > 0) {
        await this.music.queue.add(remainingIds);
    }
}
```

---

## Updated Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `backend/app/models/played_music.py` | Create | PlayedMusic table model |
| `backend/app/models/__init__.py` | Modify | Export PlayedMusic |
| `backend/app/models/user.py` | Modify | Add played_music relationship |
| `backend/app/models/station.py` | Modify | Add played_music relationship |
| `backend/app/schemas/played_music.py` | Create | CRUD schemas |
| `backend/app/services/played_music.py` | Create | CRUD service |
| `backend/app/routers/played_music.py` | Create | API endpoints |
| `backend/app/main.py` | Modify | Register router |
| `frontend/js/api.js` | Modify | Add played music API methods |
| `frontend/js/services/appleMusic.js` | Modify | Record plays on playback |

---

## Testing Checklist (Updated)

- [ ] Bearer token generates correctly
- [ ] Song search returns correct Apple Music ID
- [ ] Missing songs are removed from playlist
- [ ] Settings page shows Apple Music section
- [ ] User can click "Connect Apple Music"
- [ ] MusicKit authorization popup appears
- [ ] Subscription status saved to database
- [ ] Player checks subscription before playback
