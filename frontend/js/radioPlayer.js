/**
 * RadioPlayer - Unified Player Wrapper
 * Manages both Apple Music and TTS News playback
 */

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
        this.cachedNews = null;
        
        // Set up news audio event listeners
        this.newsAudio.addEventListener('ended', () => this._onNewsEnded());
        this.newsAudio.addEventListener('error', (e) => this._onNewsError(e));
    }
    
    /**
     * Play a station with optional news
     * @param {Object} station - Station object with news config
     * @param {Array} playlist - Resolved Apple Music songs
     */
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
                // Start music first, then set up interval
                await this.appleMusic.playPlaylistAndRecord(
                    this.playlist.map(s => s.apple_music_id),
                    station.id
                );
                this.startNewsInterval(station.news_interval_minutes);
            } else {
                // Just play music
                await this.appleMusic.playPlaylistAndRecord(
                    this.playlist.map(s => s.apple_music_id),
                    station.id
                );
            }
        } else {
            // Regular music playback without news
            await this.appleMusic.playPlaylistAndRecord(
                this.playlist.map(s => s.apple_music_id),
                station.id
            );
        }
    }
    
    /**
     * Pre-generate news audio in the background
     */
    async prepareNews() {
        if (!this.currentStation || !this.currentStation.play_news) {
            return;
        }
        
        try {
            const newsData = await api.generateStationNews(this.currentStation.id);
            this.cachedNews = newsData;
            console.log('News pre-generated successfully');
        } catch (error) {
            console.error('Failed to pre-generate news:', error);
        }
    }
    
    /**
     * Play news at the start of the stream
     */
    async playNewsFirst() {
        this.isPlayingNews = true;
        
        // Initialize Apple Music queue BEFORE news plays - within same user gesture
        // This keeps the Apple Music session active so we can resume after news
        const playlistIds = this.playlist.map(s => s.apple_music_id).filter(id => id);
        if (playlistIds.length > 0) {
            console.log('Setting Apple Music queue with', playlistIds.length, 'songs');
            try {
                // Set queue WITHOUT playing - this is different from playPlaylist
                await this.appleMusic.music.setQueue({ songs: playlistIds });
                console.log('Apple Music queue set successfully');
            } catch (error) {
                console.error('Failed to set Apple Music queue:', error);
            }
        }
        
        // Get news audio
        const newsAudio = await this._getNewsAudio();
        if (!newsAudio) {
            console.error('No news audio available');
            this.isPlayingNews = false;
            // Start music anyway
            await this.appleMusic.playPlaylistAndRecord(
                this.playlist.map(s => s.apple_music_id),
                this.currentStation.id
            );
            return;
        }
        
        // Convert base64 data URL to blob URL for CSP compliance
        const audioSrc = this._convertToBlobUrl(newsAudio.audio_url);
        this.newsAudio.src = audioSrc;
        
        try {
            await this.newsAudio.play();
            console.log('Started playing news audio');
        } catch (error) {
            console.error('Failed to play news audio:', error);
            this.isPlayingNews = false;
            // Resume music anyway
            await this.appleMusic.resume();
        }
    }
    
    /**
     * Start the news interval timer
     * @param {number} minutes - Interval in minutes
     */
    startNewsInterval(minutes) {
        // Clear any existing interval
        if (this.newsInterval) {
            clearInterval(this.newsInterval);
        }
        
        const intervalMs = minutes * 60 * 1000;
        this.newsInterval = setInterval(async () => {
            await this.playNewsSegment();
        }, intervalMs);
        
        console.log(`News interval started: every ${minutes} minutes`);
    }
    
    /**
     * Stop the news interval timer
     */
    stopNewsInterval() {
        if (this.newsInterval) {
            clearInterval(this.newsInterval);
            this.newsInterval = null;
        }
    }
    
    /**
     * Play a news segment during music playback
     */
    async playNewsSegment() {
        // Don't interrupt if already playing news
        if (this.isPlayingNews) {
            return;
        }
        
        this.isPlayingNews = true;
        
        // Pause music
        if (this.appleMusic.isPlaying()) {
            await this.appleMusic.pause();
        }
        
        // Get news audio
        const newsAudio = await this._getNewsAudio();
        if (!newsAudio) {
            console.error('No news audio available');
            this.isPlayingNews = false;
            // Resume music anyway
            await this.appleMusic.resume();
            return;
        }
        
        // Convert base64 data URL to blob URL for CSP compliance
        const audioSrc = this._convertToBlobUrl(newsAudio.audio_url);
        this.newsAudio.src = audioSrc;
        
        try {
            await this.newsAudio.play();
            console.log('Started playing news segment');
        } catch (error) {
            console.error('Failed to play news segment:', error);
            this.isPlayingNews = false;
            // Resume music anyway
            await this.appleMusic.resume();
        }
    }
    
    /**
     * Get news audio (from cache or generate new)
     */
    async _getNewsAudio() {
        // Use cached news if available
        if (this.cachedNews) {
            return this.cachedNews;
        }
        
        // Generate new news
        try {
            const newsData = await api.generateStationNews(this.currentStation.id);
            this.cachedNews = newsData;
            return newsData;
        } catch (error) {
            console.error('Failed to get news audio:', error);
            return null;
        }
    }
    
    /**
     * Handle news audio ended event
     */
    async _onNewsEnded() {
        console.log('News audio ended');
        this.isPlayingNews = false;
        
        // Apple Music queue was set in playNewsFirst before news played
        // Just resume playback - no need to set queue again
        console.log('Resuming Apple Music after news');
        await this.appleMusic.resume();
        
        // Refresh news for next interval
        if (this.currentStation && this.currentStation.news_interval_minutes) {
            await this.prepareNews();
        }
    }
    
    /**
     * Convert base64 data URL to blob URL for CSP compliance
     * @param {string} dataUrl - The data URL (e.g., 'data:audio/mp3;base64,...')
     * @returns {string} - Blob URL or original URL if not a data URL
     */
    _convertToBlobUrl(dataUrl) {
        if (!dataUrl || !dataUrl.startsWith('data:')) {
            return dataUrl;
        }
        
        try {
            // Extract MIME type and base64 data
            const matches = dataUrl.match(/^data:([^;]+);base64,(.+)$/);
            if (!matches) {
                return dataUrl;
            }
            
            const mimeType = matches[1];
            const base64Data = matches[2];
            
            // Decode base64 to binary
            const binaryString = atob(base64Data);
            const bytes = new Uint8Array(binaryString.length);
            for (let i = 0; i < binaryString.length; i++) {
                bytes[i] = binaryString.charCodeAt(i);
            }
            
            // Create blob
            const blob = new Blob([bytes], { type: mimeType });
            return URL.createObjectURL(blob);
        } catch (error) {
            console.error('Failed to convert data URL to blob:', error);
            return dataUrl;
        }
    }
    
    /**
     * Handle news audio error event
     */
    _onNewsError(error) {
        console.error('News audio error:', error);
        this.isPlayingNews = false;
    }
    
    // ==================== Unified Controls ====================
    
    /**
     * Play - unified control
     */
    async play() {
        if (this.isPlayingNews) {
            await this.newsAudio.play();
        } else {
            await this.appleMusic.resume();
        }
    }
    
    /**
     * Pause - unified control
     */
    async pause() {
        if (this.isPlayingNews) {
            await this.newsAudio.pause();
        } else {
            await this.appleMusic.pause();
        }
    }
    
    /**
     * Toggle play/pause - unified control
     */
    async togglePlayPause() {
        if (this.isPlayingNews) {
            if (this.newsAudio.paused) {
                await this.newsAudio.play();
            } else {
                await this.newsAudio.pause();
            }
        } else {
            await this.appleMusic.togglePlayPause();
        }
    }
    
    /**
     * Stop - unified control
     */
    async stop() {
        // Stop news
        this.newsAudio.pause();
        this.newsAudio.currentTime = 0;
        this.isPlayingNews = false;
        
        // Stop music
        await this.appleMusic.stop();
        
        // Clear interval
        this.stopNewsInterval();
        
        // Reset state
        this.currentStation = null;
        this.playlist = [];
        this.cachedNews = null;
    }
    
    /**
     * Skip to next track
     */
    async skipToNext() {
        if (!this.isPlayingNews) {
            await this.appleMusic.skipToNext();
        }
    }
    
    /**
     * Skip to previous track
     */
    async skipToPrevious() {
        if (!this.isPlayingNews) {
            await this.appleMusic.skipToPrevious();
        }
    }
    
    /**
     * Check if currently playing
     */
    isPlaying() {
        if (this.isPlayingNews) {
            return !this.newsAudio.paused;
        }
        return this.appleMusic.isPlaying();
    }
    
    /**
     * Get current playback status
     */
    getStatus() {
        return {
            isPlaying: this.isPlaying(),
            isPlayingNews: this.isPlayingNews,
            station: this.currentStation,
            hasNews: this.currentStation ? this.currentStation.play_news : false
        };
    }
}

// Create global instance
// The actual instance will be created in app.js after appleMusic is initialized
let radioPlayer = null;

/**
 * Initialize the radio player
 * @param {AppleMusicService} appleMusicService - The Apple Music service instance
 */
function initRadioPlayer(appleMusicService) {
    radioPlayer = new RadioPlayer(appleMusicService);
    return radioPlayer;
}
