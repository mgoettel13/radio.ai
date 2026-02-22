"""
PlayedMusic service for CRUD operations.
"""

import uuid
from typing import Optional, List, Tuple
from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.played_music import PlayedMusic


class PlayedMusicService:
    """Service for managing played music records."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def record_play(
        self, 
        user_id: uuid.UUID, 
        song_id: str, 
        artist: str, 
        title: str,
        station_id: Optional[uuid.UUID] = None
    ) -> PlayedMusic:
        """
        Record a song play. If already played, increment play_count.
        
        Args:
            user_id: User ID
            song_id: Apple Music song ID
            artist: Artist name
            title: Song title
            station_id: Optional station ID
        
        Returns:
            PlayedMusic record
        """
        # Check if song already played by this user
        result = await self.db.execute(
            select(PlayedMusic).where(
                PlayedMusic.user_id == user_id,
                PlayedMusic.song_id == song_id
            )
        )
        existing = result.scalar_one_or_none()
        
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
    ) -> Tuple[List[PlayedMusic], int]:
        """
        Get all plays for a user.
        
        Args:
            user_id: User ID
            limit: Max records to return
            offset: Number of records to skip
        
        Returns:
            Tuple of (list of PlayedMusic, total count)
        """
        # Get total count
        count_result = await self.db.execute(
            select(func.count()).where(PlayedMusic.user_id == user_id)
        )
        total = count_result.scalar() or 0
        
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
    ) -> List[PlayedMusic]:
        """
        Get plays for a specific station.
        
        Args:
            station_id: Station ID
            limit: Max records to return
        
        Returns:
            List of PlayedMusic records
        """
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
    ) -> List[PlayedMusic]:
        """
        Get most played songs for a user.
        
        Args:
            user_id: User ID
            limit: Max records to return
        
        Returns:
            List of PlayedMusic records sorted by play_count
        """
        result = await self.db.execute(
            select(PlayedMusic)
            .where(PlayedMusic.user_id == user_id)
            .order_by(PlayedMusic.play_count.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def delete_play(
        self, 
        user_id: uuid.UUID, 
        play_id: uuid.UUID
    ) -> bool:
        """
        Delete a play record.
        
        Args:
            user_id: User ID
            play_id: Play record ID
        
        Returns:
            True if deleted, False if not found
        """
        result = await self.db.execute(
            select(PlayedMusic).where(
                PlayedMusic.id == play_id,
                PlayedMusic.user_id == user_id
            )
        )
        play = result.scalar_one_or_none()
        
        if play:
            await self.db.delete(play)
            await self.db.commit()
            return True
        return False
