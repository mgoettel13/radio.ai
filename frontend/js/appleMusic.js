/**
 * Apple Music Service
 * Handles Apple Music integration, authorization, and playback
 * 
 * IMPORTANT: Chrome autoplay policies require that play() is called
 * directly from a user gesture (click/touchend). To comply:
 * 1. MusicKit must be pre-initialized before the user clicks play
 * 2. setQueue() must complete before play() is called
 * 3. We listen for mediaCanPlay event to ensure media is ready
 */

class AppleMusicService {
    constructor() {
        this.music = null;
        this.authorized = false;
        this._initialized = false;
        this._initializing = false;
        this._playbackReady = false;
        this._onPlaybackStateChange = null;
        this._onMediaItemChange = null;
    }

    /**
     * Initialize MusicKit (can be called early to pre-initialize)
     */
    async init() {
        if (this._initialized) return;
        if (this._initializing) {
            // Wait for existing initialization to complete
            while (this._initializing) {
                await new Promise(resolve => setTimeout(resolve, 100));
            }
            return;
        }
        
        this._initializing = true;
        console.log('AppleMusic: Starting init...');
        
        // Wait for MusicKit to be loaded
        if (typeof MusicKit === 'undefined') {
            console.error('AppleMusic: MusicKit not loaded yet');
            this._initializing = false;
            throw new Error('MusicKit not loaded. Please refresh the page.');
        }

        try {
            // Configure MusicKit with developer token
            console.log('AppleMusic: Getting developer token...');
            const developerToken = await this._getDeveloperToken();
            
            if (!developerToken) {
                console.error('AppleMusic: Failed to get developer token');
                throw new Error('Failed to get Apple Music developer token');
            }
            
            console.log('AppleMusic: Configuring MusicKit with token...');
            
            await MusicKit.configure({
                developerToken: developerToken,
                app: {
                    name: 'RSS Feed Radio',
                    build: '1.0.0'
                }
            });

            this.music = MusicKit.getInstance();
            this._initialized = true;
            this._initializing = false;
            
            // Set up event listeners for playback state
            this._setupEventListeners();
            
            console.log('AppleMusic: Initialized successfully');
        } catch (error) {
            console.error('AppleMusic: Failed to initialize MusicKit:', error);
            this._initializing = false;
            throw error;
        }
    }

    /**
     * Set up MusicKit event listeners
     */
    _setupEventListeners() {
        if (!this.music) return;

        // Listen for mediaCanPlay event - this fires when media is ready to play
        this.music.addEventListener('mediaCanPlay', () => {
            console.log('AppleMusic: mediaCanPlay event received');
            this._playbackReady = true;
        });

        // Listen for playback state changes
        this.music.addEventListener('playbackStateDidChange', (event) => {
            console.log('AppleMusic: playbackStateDidChange', event?.state);
            if (this._onPlaybackStateChange) {
                this._onPlaybackStateChange(event);
            }
        });

        // Listen for media item changes (song changes)
        this.music.addEventListener('mediaItemDidChange', (event) => {
            console.log('AppleMusic: mediaItemDidChange');
            if (this._onMediaItemChange) {
                this._onMediaItemChange(event);
            }
        });

        // Listen for errors
        this.music.addEventListener('playbackError', (error) => {
            console.error('AppleMusic: playbackError', error);
        });
    }

    /**
     * Set callback for playback state changes
     */
    onPlaybackStateChange(callback) {
        this._onPlaybackStateChange = callback;
    }

    /**
     * Set callback for media item changes
     */
    onMediaItemChange(callback) {
        this._onMediaItemChange = callback;
    }

    /**
     * Get developer token from backend
     */
    async _getDeveloperToken() {
        try {
            console.log('AppleMusic: Fetching developer token from /api/apple-music/token');
            const response = await fetch('/api/apple-music/token');
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error('AppleMusic: Token endpoint error:', response.status, errorText);
                throw new Error(`Token endpoint failed: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('AppleMusic: Got developer token, length:', data.token?.length);
            return data.token;
        } catch (error) {
            console.error('AppleMusic: Failed to get developer token:', error);
            throw error;
        }
    }

    /**
     * Authorize user with Apple Music
     */
    async authorize() {
        if (!this.music) {
            await this.init();
        }

        if (!this.music) {
            throw new Error('MusicKit not initialized');
        }

        try {
            await this.music.authorize();
            this.authorized = true;
            return true;
        } catch (error) {
            console.error('Authorization failed:', error);
            this.authorized = false;
            return false;
        }
    }

    /**
     * Check if user is authorized
     */
    isAuthorized() {
        return this.authorized;
    }

    /**
     * Check if MusicKit is initialized
     */
    isInitialized() {
        return this._initialized;
    }

    /**
     * Resolve playlist songs to Apple Music IDs
     */
    async resolvePlaylist(songs) {
        const response = await fetch('/api/apple-music/resolve-playlist', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${api.token}`
            },
            body: JSON.stringify({ songs })
        });

        if (!response.ok) {
            throw new Error('Failed to resolve playlist');
        }

        return response.json();
    }

    /**
     * Play a single song by ID
     * IMPORTANT: This must be called directly from a user gesture handler
     */
    async playSong(appleMusicId) {
        if (!this.music) {
            throw new Error('MusicKit not initialized. Call init() first.');
        }

        this._playbackReady = false;
        
        // Set queue and wait for it to be ready
        await this.music.setQueue({ songs: [appleMusicId] });
        
        // Wait for mediaCanPlay event (with timeout)
        await this._waitForMediaReady();
        
        // Now play - this should work because we're still in the user gesture context
        await this.music.play();
    }

    /**
     * Play a playlist of songs
     * IMPORTANT: This must be called directly from a user gesture handler
     * Following the pattern: setQueue().then(() => play())
     */
    async playPlaylist(appleMusicIds) {
        if (!this.music) {
            throw new Error('MusicKit not initialized. Call init() first.');
        }

        console.log('AppleMusic: Setting queue with', appleMusicIds.length, 'songs');
        
        // Set queue and immediately play - following the developer's example pattern
        // music.setQueue({ url: '...' }).then(() => { music.play(); })
        await this.music.setQueue({ songs: appleMusicIds });
        
        console.log('AppleMusic: Queue set, starting playback immediately');
        
        // Call play() immediately after setQueue() - don't wait for mediaCanPlay
        // This follows the developer's example pattern
        await this.music.play();
        
        console.log('AppleMusic: play() called successfully');
    }

    /**
     * Wait for media to be ready to play
     * Returns a promise that resolves when mediaCanPlay fires or timeout
     */
    async _waitForMediaReady(timeout = 10000) {
        return new Promise((resolve, reject) => {
            const timeoutId = setTimeout(() => {
                console.warn('AppleMusic: Timeout waiting for mediaCanPlay, attempting play anyway');
                resolve();
            }, timeout);

            const checkReady = () => {
                if (this._playbackReady) {
                    clearTimeout(timeoutId);
                    resolve();
                } else {
                    // Check again in 100ms
                    setTimeout(checkReady, 100);
                }
            };

            // Also check if MusicKit reports ready state
            if (this.music && this.music.isReady) {
                clearTimeout(timeoutId);
                resolve();
                return;
            }

            checkReady();
        });
    }

    /**
     * Play a song and record it to database
     */
    async playAndRecord(appleMusicId, artist, title, stationId = null) {
        // Start playback
        await this.playSong(appleMusicId);

        // Record play in database
        try {
            await fetch('/api/played-music', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${api.token}`
                },
                body: JSON.stringify({
                    song_id: appleMusicId,
                    artist: artist,
                    title: title,
                    station_id: stationId
                })
            });
        } catch (error) {
            console.error('Failed to record play:', error);
        }
    }

    /**
     * Play a playlist and record all songs
     * IMPORTANT: This must be called directly from a user gesture handler
     */
    async playPlaylistAndRecord(songs, stationId = null) {
        if (!songs || songs.length === 0) {
            throw new Error('No songs to play');
        }

        const appleMusicIds = songs.map(s => s.apple_music_id);

        // Play the playlist (this handles the queue setup properly)
        await this.playPlaylist(appleMusicIds);

        // Record the first song
        const firstSong = songs[0];
        try {
            await fetch('/api/played-music', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${api.token}`
                },
                body: JSON.stringify({
                    song_id: firstSong.apple_music_id,
                    artist: firstSong.artist,
                    title: firstSong.title,
                    station_id: stationId
                })
            });
        } catch (error) {
            console.error('Failed to record play:', error);
        }
    }

    /**
     * Pause playback
     */
    async pause() {
        if (this.music) {
            await this.music.pause();
        }
    }

    /**
     * Resume playback
     */
    async resume() {
        if (this.music) {
            await this.music.play();
        }
    }

    /**
     * Stop playback
     */
    async stop() {
        if (this.music) {
            await this.music.stop();
        }
    }

    /**
     * Toggle play/pause
     */
    async togglePlayPause() {
        if (!this.music) return;
        
        if (this.isPlaying()) {
            await this.music.pause();
        } else {
            await this.music.play();
        }
    }

    /**
     * Check if currently playing
     */
    isPlaying() {
        if (!this.music) return false;
        return this.music.playbackState === MusicKit.PlaybackStates.playing;
    }

    /**
     * Skip to next track
     */
    async skipToNext() {
        if (this.music) {
            await this.music.skipToNextItem();
        }
    }

    /**
     * Skip to previous track
     */
    async skipToPrevious() {
        if (this.music) {
            await this.music.skipToPreviousItem();
        }
    }

    /**
     * Get current playback state
     */
    getPlaybackState() {
        if (!this.music) return null;
        return this.music.playbackState;
    }

    /**
     * Get current song
     */
    getCurrentSong() {
        if (!this.music) return null;
        const item = this.music.nowPlayingItem;
        console.log('DEBUG getCurrentSong - nowPlayingItem:', item);
        if (item) {
            console.log('DEBUG getCurrentSong - item.attributes:', item.attributes);
            console.log('DEBUG getCurrentSong - item.attributes.artwork:', item.attributes?.artwork);
        }
        return item;
    }

    /**
     * Seek to position
     */
    async seekToPosition(position) {
        if (this.music) {
            await this.music.seekToTime(position);
        }
    }
}

// Global instance
const appleMusic = new AppleMusicService();
