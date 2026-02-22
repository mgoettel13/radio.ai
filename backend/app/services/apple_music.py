"""
Apple Music service for searching and resolving songs.
"""

import httpx
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.config import get_settings
from app.services.apple_music_token import generate_apple_music_token, is_token_valid


class AppleMusicService:
    """Service for interacting with Apple Music API."""
    
    def __init__(self):
        self.settings = get_settings()
        self._token: Optional[str] = None
        self.base_url = "https://api.music.apple.com/v1"
        self.storefront = self.settings.apple_music_storefront or "us"
    
    def _get_token(self) -> str:
        """Get or generate bearer token."""
        if not self._token or not is_token_valid(self._token):
            self._token = generate_apple_music_token()
        return self._token
    
    async def search_song(self, artist: str, title: str) -> Optional[Dict[str, Any]]:
        """
        Search for a song by artist and title.
        
        Args:
            artist: Artist name
            title: Song title
        
        Returns:
            Song data dict or None if not found
        """
        token = self._get_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        # Clean up search term
        term = f"{artist} {title}".strip()
        url = f"{self.base_url}/catalog/{self.storefront}/search"
        params = {"term": term, "types": "songs", "limit": 5}
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=headers, params=params, timeout=10.0)
                
                if response.status_code != 200:
                    return None
                
                data = response.json()
                songs = data.get("results", {}).get("songs", {}).get("data", [])
                
                if songs:
                    # Return first match
                    return songs[0]
                return None
            except httpx.RequestError:
                return None
    
    async def resolve_playlist(
        self, 
        songs: List[Dict[str, str]],
        skip_not_found: bool = True
    ) -> Dict[str, Any]:
        """
        Resolve playlist songs to Apple Music IDs.
        
        Args:
            songs: List of dicts with 'artist' and 'title' keys
            skip_not_found: If True, remove songs not found from result
        
        Returns:
            Dict with resolved songs, removed songs, and counts
        """
        resolved_songs = []
        removed_songs = []
        
        for song in songs:
            artist = song.get("artist", "")
            title = song.get("title", "")
            
            result = await self.search_song(artist, title)
            
            if result:
                attrs = result.get("attributes", {})
                song_data = {
                    "artist": artist,
                    "title": title,
                    "apple_music_id": result.get("id"),
                    "name": attrs.get("name"),
                    "duration_ms": attrs.get("durationInMillis"),
                    "artwork": attrs.get("artwork"),
                    "playback_url": attrs.get("url"),
                    "album_name": attrs.get("albumName"),
                    "genre": attrs.get("genreNames", [None])[0] if attrs.get("genreNames") else None,
                }
                resolved_songs.append(song_data)
            else:
                # Song not found
                removed_songs.append({"artist": artist, "title": title})
        
        return {
            "original_count": len(songs),
            "resolved_count": len(resolved_songs),
            "removed_count": len(removed_songs),
            "songs": resolved_songs,
            "removed": removed_songs if not skip_not_found else [],
        }
    
    async def get_song_by_id(self, song_id: str) -> Optional[Dict[str, Any]]:
        """
        Get song details by Apple Music ID.
        
        Args:
            song_id: Apple Music song ID
        
        Returns:
            Song data dict or None if not found
        """
        token = self._get_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        url = f"{self.base_url}/catalog/{self.storefront}/songs/{song_id}"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=headers, timeout=10.0)
                
                if response.status_code != 200:
                    return None
                
                data = response.json()
                songs = data.get("data", [])
                
                if songs:
                    return songs[0]
                return None
            except httpx.RequestError:
                return None


# Singleton instance
apple_music_service = AppleMusicService()


async def get_apple_music_service() -> AppleMusicService:
    """Dependency for FastAPI."""
    return apple_music_service
