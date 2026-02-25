/**
 * Main Application Logic
 */

class App {
    constructor() {
        this.articles = [];
        this.currentArticle = null;
        this.summary = null;
        this.articleModal = new ModalManager('article-modal');
        this.radioNewsModal = new ModalManager('radio-news-modal');
        this.stationModal = new ModalManager('station-modal');
        this.playlistModal = new ModalManager('playlist-modal');
        this.radioScript = null;
        this.stations = [];
        this.currentSection = 'news'; // 'news' or 'radio'
        this.currentPlaylist = null; // Store current playlist for playback
        this.resolvedPlaylist = null; // Store resolved Apple Music songs
        this.currentlyPlayingCard = null; // Track the currently playing station card

        this.init();
    }

    init() {
        console.log('App.init() called');
        // Event listeners
        document.getElementById('summarize-btn').addEventListener('click', () => this.summarizeCurrentArticle());
        document.getElementById('listen-btn').addEventListener('click', () => this.listenToSummary());
        document.getElementById('get-my-news-btn').addEventListener('click', () => this.getPersonalizedNews());
        document.getElementById('my-radio-news-btn').addEventListener('click', () => this.getRadioNews());
        
        // Navigation menu
        this.setupNavigation();
        
        // Hide the get news section initially (will show when News menu is clicked)
        const getNewsSection = document.querySelector('.get-news-section');
        if (getNewsSection) {
            getNewsSection.classList.add('hidden');
        }
        
        // Station event listeners
        this.setupStationListeners();

        // Playlist modal event listeners
        this.setupPlaylistListeners();

        // Listen for auth state changes
        window.addEventListener('auth:stateChanged', (e) => this.onAuthStateChanged(e.detail));

        // Don't load articles on init - only load when user clicks "Get My News"
        this.articles = [];
    }

    setupPlaylistListeners() {
        // Play button
        const playBtn = document.getElementById('playlist-play-btn');
        if (playBtn) {
            playBtn.addEventListener('click', (e) => {
                console.log('DEBUG: Play button clicked!', e);
                this.playPlaylist();
            });
        } else {
            console.warn('DEBUG: Play button not found!');
        }
        
        // Resolve button
        const resolveBtn = document.getElementById('playlist-resolve-btn');
        if (resolveBtn) {
            resolveBtn.addEventListener('click', () => this.resolvePlaylist());
        }
        
        // Playback controls
        this.setupPlaybackControls();
    }

    /**
     * Set up playback control buttons
     */
    setupPlaybackControls() {
        // Play/Pause button
        const playPauseBtn = document.getElementById('btn-play-pause');
        if (playPauseBtn) {
            playPauseBtn.addEventListener('click', () => this.togglePlayPause());
        }
        
        // Stop button
        const stopBtn = document.getElementById('btn-stop');
        if (stopBtn) {
            stopBtn.addEventListener('click', () => this.stopPlayback());
        }
        
        // Next button
        const nextBtn = document.getElementById('btn-next');
        if (nextBtn) {
            nextBtn.addEventListener('click', () => this.skipToNext());
        }
        
        // Previous button
        const prevBtn = document.getElementById('btn-prev');
        if (prevBtn) {
            prevBtn.addEventListener('click', () => this.skipToPrevious());
        }
    }

    setupNavigation() {
        const navMenu = document.getElementById('nav-menu');
        if (!navMenu) return;
        
        const navItems = navMenu.querySelectorAll('.nav-item');
        navItems.forEach(item => {
            item.addEventListener('click', () => {
                const section = item.dataset.section;
                this.navigateToSection(section);
            });
        });
    }

    navigateToSection(section) {
        this.currentSection = section;
        
        // Update nav menu
        const navItems = document.querySelectorAll('.nav-item');
        navItems.forEach(item => {
            if (item.dataset.section === section) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });
        
        // Show/hide content
        const articleList = document.getElementById('article-list');
        const stationList = document.getElementById('station-list');
        
        // Get the button containers
        const getNewsSection = document.querySelector('.get-news-section');
        
        if (section === 'news') {
            articleList.classList.remove('hidden');
            stationList.classList.add('hidden');
            // Show Get My News and My Radio News buttons in news section
            if (getNewsSection) {
                getNewsSection.classList.remove('hidden');
            }
        } else if (section === 'radio') {
            articleList.classList.add('hidden');
            stationList.classList.remove('hidden');
            // Hide Get My News and My Radio News buttons in radio section
            if (getNewsSection) {
                getNewsSection.classList.add('hidden');
            }
            this.loadStations();
        }
    }

    showNavMenu() {
        document.getElementById('nav-menu').classList.remove('hidden');
    }

    hideNavMenu() {
        document.getElementById('nav-menu').classList.add('hidden');
    }

    setupStationListeners() {
        // Add station button
        const addBtn = document.getElementById('add-station-btn');
        if (addBtn) {
            addBtn.addEventListener('click', () => this.showCreateStationModal());
        }
        
        // Station modal cancel button
        const cancelBtn = document.getElementById('station-cancel-btn');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => this.closeStationModal());
        }
        
        // Station form submission
        const stationForm = document.getElementById('station-form');
        if (stationForm) {
            stationForm.addEventListener('submit', (e) => this.saveStation(e));
        }
        
        // Image upload button
        const imageBtn = document.getElementById('station-image-btn');
        const imageInput = document.getElementById('station-image-input');
        if (imageBtn && imageInput) {
            imageBtn.addEventListener('click', () => imageInput.click());
            imageInput.addEventListener('change', (e) => this.handleStationImageUpload(e));
        }
    }

    async loadStations() {
        try {
            const data = await api.getStations();
            this.stations = data.stations || [];
            this.renderStations();
        } catch (error) {
            console.error('Load stations error:', error);
            showToast('Failed to load stations', 'error');
        }
    }

    renderStations() {
        const container = document.getElementById('stations-container');
        container.innerHTML = '';
        
        if (this.stations.length === 0) {
            container.innerHTML = '<p class="no-stations">No radio stations yet. Click "Add Station" to create one!</p>';
            return;
        }
        
        this.stations.forEach(station => {
            const card = createStationCard(station);
            container.appendChild(card);
        });
    }

    showCreateStationModal() {
        document.getElementById('station-modal-title').textContent = 'Create Radio Station';
        document.getElementById('station-id').value = '';
        document.getElementById('station-name').value = '';
        document.getElementById('station-description').value = '';
        document.getElementById('station-examples').value = '';
        document.getElementById('station-duration').value = '1';
        
        // Reset news fields
        document.getElementById('station-play-news').checked = false;
        document.getElementById('station-news-at-start').checked = false;
        document.getElementById('station-news-interval').value = '';
        document.getElementById('news-options').classList.add('hidden');
        
        this.clearStationImagePreview();
        document.getElementById('station-error').classList.add('hidden');
        
        // Set up news checkbox listener
        this.setupNewsCheckboxListener();
        
        this.stationModal.open();
    }

    openStation(station) {
        // Open the modal in edit mode - populate form with station data
        document.getElementById('station-modal-title').textContent = 'Edit Radio Station';
        document.getElementById('station-id').value = station.id;
        document.getElementById('station-name').value = station.name || '';
        document.getElementById('station-description').value = station.description || '';
        document.getElementById('station-examples').value = (station.example_songs || []).join('\n');
        document.getElementById('station-duration').value = station.duration || 1;
        
        // Populate news fields
        document.getElementById('station-play-news').checked = station.play_news || false;
        document.getElementById('station-news-at-start').checked = station.play_news_at_start || false;
        document.getElementById('station-news-interval').value = station.news_interval_minutes || '';
        
        // Show/hide news options based on play_news
        if (station.play_news) {
            document.getElementById('news-options').classList.remove('hidden');
        } else {
            document.getElementById('news-options').classList.add('hidden');
        }
        
        // Show the existing image in preview
        const previewImg = document.getElementById('station-preview-img');
        const placeholder = document.getElementById('station-preview-placeholder');
        
        if (station.image_url) {
            previewImg.src = station.image_url;
            previewImg.classList.remove('hidden');
            placeholder.classList.add('hidden');
        } else {
            this.clearStationImagePreview();
        }
        
        document.getElementById('station-error').classList.add('hidden');
        
        // Set up news checkbox listener
        this.setupNewsCheckboxListener();
        
        this.stationModal.open();
    }

    closeStationModal() {
        this.stationModal.close();
    }

    handleStationImageUpload(event) {
        const file = event.target.files[0];
        if (!file) return;
        
        const reader = new FileReader();
        reader.onload = (e) => {
            const previewImg = document.getElementById('station-preview-img');
            const placeholder = document.getElementById('station-preview-placeholder');
            
            previewImg.src = e.target.result;
            previewImg.classList.remove('hidden');
            placeholder.classList.add('hidden');
        };
        reader.readAsDataURL(file);
    }

    clearStationImagePreview() {
        const previewImg = document.getElementById('station-preview-img');
        const placeholder = document.getElementById('station-preview-placeholder');
        const imageInput = document.getElementById('station-image-input');
        
        previewImg.src = '';
        previewImg.classList.add('hidden');
        placeholder.classList.remove('hidden');
        if (imageInput) imageInput.value = '';
    }
    
    /**
     * Set up the news checkbox listener to show/hide news options
     */
    setupNewsCheckboxListener() {
        const playNewsCheckbox = document.getElementById('station-play-news');
        const newsOptions = document.getElementById('news-options');
        const startCheckbox = document.getElementById('station-news-at-start');
        const intervalSelect = document.getElementById('station-news-interval');
        
        // Remove any existing listener to avoid duplicates
        playNewsCheckbox.onchange = null;
        
        playNewsCheckbox.addEventListener('change', (e) => {
            if (e.target.checked) {
                newsOptions.classList.remove('hidden');
            } else {
                newsOptions.classList.add('hidden');
                startCheckbox.checked = false;
                intervalSelect.value = '';
            }
        });
    }

    async saveStation(event) {
        event.preventDefault();
        
        const stationId = document.getElementById('station-id').value;
        const name = document.getElementById('station-name').value.trim();
        const description = document.getElementById('station-description').value.trim();
        const examplesText = document.getElementById('station-examples').value.trim();
        const duration = parseInt(document.getElementById('station-duration').value, 10);
        
        // Get image from preview or use default
        const previewImg = document.getElementById('station-preview-img');
        const imageUrl = previewImg.classList.contains('hidden') ? null : previewImg.src;
        
        // Parse example songs
        const example_songs = examplesText 
            ? examplesText.split('\n').map(s => s.trim()).filter(s => s.length > 0)
            : [];
        
        const stationData = {
            name,
            description: description || null,
            example_songs,
            duration,
            image_url: imageUrl || null,
            play_news: document.getElementById('station-play-news').checked,
            play_news_at_start: document.getElementById('station-news-at-start').checked,
            news_interval_minutes: document.getElementById('station-news-interval').value ? parseInt(document.getElementById('station-news-interval').value, 10) : null
        };
        
        console.log('Saving station:', stationData);
        
        const errorEl = document.getElementById('station-error');
        
        try {
            if (stationId) {
                // Update existing station
                await api.updateStation(stationId, stationData);
                showToast('Station updated!', 'success');
            } else {
                // Create new station
                await api.createStation(stationData);
                showToast('Station created!', 'success');
            }
            
            this.closeStationModal();
            
            // Refresh station list
            this.loadStations();
            
        } catch (error) {
            errorEl.textContent = error.message || 'Failed to save station';
            errorEl.classList.remove('hidden');
        }
    }

    async generatePlaylist(station) {
        const btn = document.querySelector(`.station-card[data-id="${station.id}"] .station-play-btn`);
        if (btn) {
            btn.disabled = true;
            btn.textContent = '⏳';
        }

        try {
            const playlist = await api.generatePlaylist(station.id);
            this.displayPlaylistModal(playlist);
            showToast('Playlist generated!', 'success');
        } catch (error) {
            showToast('Failed to generate playlist: ' + error.message, 'error');
            console.error('Generate playlist error:', error);
        } finally {
            if (btn) {
                btn.disabled = false;
                btn.textContent = '▶️';
            }
        }
    }

    /**
     * Generate and play playlist inline - all in one click
     * This replaces the modal-based workflow
     * Uses RadioPlayer when news is enabled
     */
    async generateAndPlayInline(station, cardElement) {
        // Stop any currently playing station first
        if (this.currentlyPlayingCard && this.currentlyPlayingCard !== cardElement) {
            this.stopAndCollapseCard(this.currentlyPlayingCard);
        }
        
        const playBtn = cardElement.querySelector('.station-play-btn');
        
        try {
            // 1. Show loading state
            this.showCardLoading(cardElement, 'Generating playlist...');
            
            // 2. Initialize MusicKit first (needed for authorization)
            if (!appleMusic.isInitialized()) {
                this.updateLoadingText(cardElement, 'Initializing Apple Music...');
                await appleMusic.init();
            }
            
            // 3. Check authorization - if not authorized, show button to authorize
            if (!appleMusic.isAuthorized()) {
                this.showAuthorizationButton(cardElement, station, playBtn);
                return; // Stop here, wait for user to click authorize button
            }
            
            // 4. Generate playlist from Perplexity
            const playlist = await api.generatePlaylist(station.id);
            
            // 5. Update loading text
            this.updateLoadingText(cardElement, 'Resolving songs in Apple Music...');
            
            // 6. Resolve songs to Apple Music IDs
            const songs = playlist.songs.map(s => ({
                artist: s.artist,
                title: s.title
            }));
            const resolved = await appleMusic.resolvePlaylist(songs);
            
            if (!resolved.songs || resolved.songs.length === 0) {
                throw new Error('No songs found in Apple Music');
            }
            
            // 7. Store resolved playlist on card
            cardElement.dataset.resolvedPlaylist = JSON.stringify(resolved.songs);
            cardElement.dataset.stationId = station.id;
            
            // 8. Switch to playing state
            this.showCardPlaying(cardElement, playlist, resolved);
            
            // 9. Initialize radio player if needed
            if (!radioPlayer) {
                radioPlayer = initRadioPlayer(appleMusic);
            }
            
            // 10. Check if news is enabled for this station
            if (station.play_news) {
                // Use RadioPlayer for news integration
                this.updateLoadingText(cardElement, 'Preparing news...');
                await radioPlayer.playStation(station, resolved.songs);
                showToast('Playing ' + resolved.resolved_count + ' songs with news!', 'success');
            } else {
                // Regular playback without news
                await appleMusic.playPlaylistAndRecord(resolved.songs, station.id);
                showToast('Playing ' + resolved.resolved_count + ' songs!', 'success');
            }
            
            // 11. Track this as the currently playing card
            this.currentlyPlayingCard = cardElement;
            
            // 12. Update now playing display
            this.updateCardNowPlaying(cardElement);
            
        } catch (error) {
            this.showCardError(cardElement, error.message);
            showToast('Failed to play: ' + error.message, 'error');
            console.error('Play inline error:', error);
        }
    }

    /**
     * Show loading overlay on card
     */
    showCardLoading(cardElement, message) {
        cardElement.classList.add('loading');
        const overlay = cardElement.querySelector('.loading-overlay');
        const text = overlay.querySelector('.loading-text');
        text.textContent = message;
        
        // Hide authorize button if it was shown
        const authBtn = overlay.querySelector('.authorize-btn');
        if (authBtn) {
            authBtn.remove();
        }
        
        overlay.classList.remove('hidden');
    }

    /**
     * Show authorization button in the card overlay
     * This allows the user to click to authorize Apple Music
     */
    showAuthorizationButton(cardElement, station, playBtn) {
        const overlay = cardElement.querySelector('.loading-overlay');
        const text = overlay.querySelector('.loading-text');
        text.textContent = 'Apple Music authorization required';
        
        // Create authorize button
        const authBtn = document.createElement('button');
        authBtn.className = 'btn btn-primary authorize-btn';
        authBtn.textContent = 'Authorize Apple Music';
        authBtn.style.marginTop = '1rem';
        
        authBtn.addEventListener('click', async (e) => {
            e.stopPropagation();
            authBtn.disabled = true;
            authBtn.textContent = 'Authorizing...';
            
            try {
                const authorized = await appleMusic.authorize();
                if (authorized) {
                    // Continue with the playlist generation
                    await this.continueAfterAuthorization(station, cardElement);
                } else {
                    authBtn.textContent = 'Authorization failed. Click to try again.';
                    authBtn.disabled = false;
                    showToast('Please authorize Apple Music to play songs', 'error');
                }
            } catch (error) {
                console.error('Authorization error:', error);
                authBtn.textContent = 'Error. Click to try again.';
                authBtn.disabled = false;
                showToast('Authorization failed: ' + error.message, 'error');
            }
        });
        
        overlay.appendChild(authBtn);
    }

    /**
     * Continue playlist generation after authorization
     */
    async continueAfterAuthorization(station, cardElement) {
        try {
            // Generate playlist
            this.updateLoadingText(cardElement, 'Generating playlist...');
            const playlist = await api.generatePlaylist(station.id);
            
            // Resolve songs
            this.updateLoadingText(cardElement, 'Resolving songs in Apple Music...');
            const songs = playlist.songs.map(s => ({
                artist: s.artist,
                title: s.title
            }));
            const resolved = await appleMusic.resolvePlaylist(songs);
            
            if (!resolved.songs || resolved.songs.length === 0) {
                throw new Error('No songs found in Apple Music');
            }
            
            // Store resolved playlist
            cardElement.dataset.resolvedPlaylist = JSON.stringify(resolved.songs);
            cardElement.dataset.stationId = station.id;
            
            // Switch to playing state
            this.showCardPlaying(cardElement, playlist, resolved);
            
            // Initialize radio player if needed
            if (!radioPlayer) {
                radioPlayer = initRadioPlayer(appleMusic);
            }
            
            // Check if news is enabled for this station
            if (station.play_news) {
                // Use RadioPlayer for news integration
                this.updateLoadingText(cardElement, 'Preparing news...');
                await radioPlayer.playStation(station, resolved.songs);
                showToast('Playing ' + resolved.resolved_count + ' songs with news!', 'success');
            } else {
                // Regular playback without news
                await appleMusic.playPlaylistAndRecord(resolved.songs, station.id);
                showToast('Playing ' + resolved.resolved_count + ' songs!', 'success');
            }
            
            // Track this as the currently playing card
            this.currentlyPlayingCard = cardElement;
            
            // Update now playing display
            this.updateCardNowPlaying(cardElement);
            
        } catch (error) {
            this.showCardError(cardElement, error.message);
            showToast('Failed to play: ' + error.message, 'error');
            console.error('Continue after authorization error:', error);
        }
    }

    /**
     * Update loading text
     */
    updateLoadingText(cardElement, message) {
        const text = cardElement.querySelector('.loading-text');
        if (text) text.textContent = message;
    }

    /**
     * Switch card to playing state
     */
    showCardPlaying(cardElement, playlist, resolved) {
        // Hide loading overlay
        const overlay = cardElement.querySelector('.loading-overlay');
        overlay.classList.add('hidden');
        
        // Add playing class (triggers CSS to show player, hide image)
        cardElement.classList.remove('loading');
        cardElement.classList.add('playing');
        
        // Update status
        const status = cardElement.querySelector('.station-card-status');
        status.textContent = `🎵 ${resolved.resolved_count} songs • ${playlist.total_duration_hours}h`;
        status.classList.remove('hidden');
    }

    /**
     * Update now playing info in card
     */
    updateCardNowPlaying(cardElement) {
        const song = appleMusic.getCurrentSong();
        if (!song) return;
        
        const attrs = song.attributes || song;
        
        const artworkEl = cardElement.querySelector('.now-playing-artwork');
        const titleEl = cardElement.querySelector('.now-playing-title');
        const artistEl = cardElement.querySelector('.now-playing-artist');
        
        titleEl.textContent = attrs.name || 'Unknown';
        artistEl.textContent = attrs.artistName || 'Unknown Artist';
        
        // Handle artwork URL
        const artwork = attrs.artwork;
        if (artwork) {
            let url = typeof artwork === 'string' ? artwork : artwork.url;
            if (url && url.includes('{w}')) {
                url = url.replace('{w}', '160').replace('{h}', '160');
            }
            artworkEl.src = url;
        }
        
        // Update play/pause button
        const playPauseBtn = cardElement.querySelector('.btn-play-pause');
        playPauseBtn.textContent = appleMusic.isPlaying() ? '⏸️' : '▶️';
    }

    /**
     * Show error on card
     */
    showCardError(cardElement, message) {
        const overlay = cardElement.querySelector('.loading-overlay');
        overlay.classList.add('hidden');
        cardElement.classList.remove('loading');
        
        const status = cardElement.querySelector('.station-card-status');
        status.textContent = `❌ ${message}`;
        status.classList.remove('hidden');
        
        // Auto-hide error after 5 seconds
        setTimeout(() => {
            status.classList.add('hidden');
        }, 5000);
    }

    /**
     * Stop playback and collapse card to idle
     */
    stopAndCollapseCard(cardElement) {
        appleMusic.stop();
        cardElement.classList.remove('playing', 'loading');
        
        const status = cardElement.querySelector('.station-card-status');
        status.classList.add('hidden');
        
        if (this.currentlyPlayingCard === cardElement) {
            this.currentlyPlayingCard = null;
        }
    }

    /**
     * Toggle play/pause for a card
     */
    toggleCardPlayPause(cardElement) {
        appleMusic.togglePlayPause();
        // Update button text
        const btn = cardElement.querySelector('.btn-play-pause');
        btn.textContent = appleMusic.isPlaying() ? '⏸️' : '▶️';
    }

    displayPlaylistModal(playlist) {
        // Store the playlist for playback
        this.currentPlaylist = playlist;
        this.resolvedPlaylist = null;
        
        // Set station info
        const infoEl = document.getElementById('playlist-info');
        infoEl.innerHTML = `
            <h3>${escapeHtml(playlist.station_name)}</h3>
            <p class="playlist-duration">⏱️ ${playlist.total_duration_hours} hour${playlist.total_duration_hours > 1 ? 's' : ''} • ${playlist.songs.length} songs</p>
        `;

        // Render songs list
        const songsEl = document.getElementById('playlist-songs');
        songsEl.innerHTML = playlist.songs.map((song, index) => `
            <div class="playlist-song">
                <div class="song-number">${index + 1}</div>
                <div class="song-details">
                    <div class="song-title">${escapeHtml(song.title)}</div>
                    <div class="song-artist">${escapeHtml(song.artist)}${song.year ? ` • ${song.year}` : ''} • ${escapeHtml(song.genre)}</div>
                    <div class="song-why">"${escapeHtml(song.why_this_song)}"</div>
                </div>
            </div>
        `).join('');

        // Reset buttons
        this.updatePlaylistStatus('', '');
        
        // Enable play button (will resolve first if needed)
        const playBtn = document.getElementById('playlist-play-btn');
        const resolveBtn = document.getElementById('playlist-resolve-btn');
        if (playBtn) {
            playBtn.disabled = false;
            playBtn.innerHTML = '<span>▶️ Play with Apple Music</span>';
        }
        if (resolveBtn) {
            resolveBtn.disabled = false;
            resolveBtn.innerHTML = '<span>🔍 Resolve Songs</span>';
        }

        // Hide now playing section initially
        this.hideNowPlaying();

        // Setup close button
        const closeBtn = document.getElementById('playlist-close-btn');
        closeBtn.onclick = () => this.playlistModal.close();

        // Set up Apple Music callbacks for UI updates
        this.setupAppleMusicCallbacks();

        // Pre-initialize MusicKit AND pre-authorize in the background
        // This ensures MusicKit is ready AND authorized when user clicks play
        this._preInitializeAndAuthorize();

        this.playlistModal.open();
    }

    /**
     * Set up Apple Music callbacks for UI updates
     */
    setupAppleMusicCallbacks() {
        // Remove any existing callbacks first
        appleMusic.onPlaybackStateChange(null);
        appleMusic.onMediaItemChange(null);
        
        // Set up new callbacks
        appleMusic.onPlaybackStateChange((event) => this.handlePlaybackStateChange(event));
        appleMusic.onMediaItemChange((event) => this.handleMediaItemChange(event));
    }

    /**
     * Pre-initialize MusicKit and authorize in the background
     * This is called when the playlist modal opens so that
     * when the user clicks play, everything is ready
     */
    async _preInitializeAndAuthorize() {
        try {
            // Initialize MusicKit if not already done
            if (!appleMusic.isInitialized()) {
                console.log('Pre-initializing MusicKit...');
                await appleMusic.init();
                console.log('MusicKit pre-initialized successfully');
            }
            
            // Check if already authorized
            if (appleMusic.isAuthorized()) {
                console.log('Already authorized with Apple Music');
                
                // Pre-resolve the playlist if we have one
                if (this.currentPlaylist && this.currentPlaylist.songs) {
                    console.log('Pre-resolving playlist...');
                    await this._preResolvePlaylist();
                }
                return;
            }
            
            // Try to authorize silently (check if user has previously authorized)
            // Note: This won't show a popup if the user hasn't authorized before
            // The actual authorization will happen on first play
            console.log('Checking Apple Music authorization status...');
            
        } catch (error) {
            console.warn('Failed to pre-initialize MusicKit:', error);
            // This is not critical - we'll try again when user clicks play
        }
    }

    /**
     * Pre-resolve the playlist in the background
     * This is called when the modal opens and user is already authorized
     */
    async _preResolvePlaylist() {
        if (!this.currentPlaylist || !this.currentPlaylist.songs) {
            return;
        }
        
        try {
            const songs = this.currentPlaylist.songs.map(s => ({
                artist: s.artist,
                title: s.title
            }));
            
            console.log('Pre-resolving', songs.length, 'songs...');
            
            const resolved = await appleMusic.resolvePlaylist(songs);
            
            if (resolved.songs && resolved.songs.length > 0) {
                this.resolvedPlaylist = resolved.songs;
                console.log('Pre-resolved', resolved.resolved_count, 'songs');
                
                // Update the play button to show how many songs are ready
                const playBtn = document.getElementById('playlist-play-btn');
                if (playBtn) {
                    playBtn.innerHTML = `<span>▶️ Play ${resolved.resolved_count} Songs</span>`;
                }
                
                // Update status
                this.updatePlaylistStatus(
                    `Ready to play ${resolved.resolved_count} songs`,
                    'success'
                );
            }
        } catch (error) {
            console.warn('Pre-resolve failed:', error);
            // This is not critical - user can click Resolve button
        }
    }

    /**
     * Pre-initialize MusicKit in the background
     * This is called when the playlist modal opens so that
     * when the user clicks play, MusicKit is already ready
     */
    async _preInitializeMusicKit() {
        try {
            // Only initialize if not already done
            if (!appleMusic.isInitialized()) {
                console.log('Pre-initializing MusicKit...');
                await appleMusic.init();
                console.log('MusicKit pre-initialized successfully');
            }
        } catch (error) {
            console.warn('Failed to pre-initialize MusicKit:', error);
            // This is not critical - we'll try again when user clicks play
        }
    }

    updatePlaylistStatus(message, type) {
        const statusEl = document.getElementById('playlist-status');
        if (!statusEl) return;
        
        if (!message) {
            statusEl.classList.add('hidden');
            return;
        }
        
        statusEl.textContent = message;
        statusEl.className = 'playlist-status ' + type;
        statusEl.classList.remove('hidden');
    }

    async resolvePlaylist() {
        console.log('resolvePlaylist: DEBUG - Starting');
        
        if (!this.currentPlaylist) {
            console.log('resolvePlaylist: DEBUG - No currentPlaylist, returning');
            showToast('No playlist to resolve', 'error');
            return;
        }

        const resolveBtn = document.getElementById('playlist-resolve-btn');
        const playBtn = document.getElementById('playlist-play-btn');
        
        if (resolveBtn) {
            resolveBtn.disabled = true;
            resolveBtn.innerHTML = '<span>⏳ Resolving...</span>';
        }

        this.updatePlaylistStatus('Looking up songs in Apple Music...', 'info');

        try {
            // Convert playlist songs to the format expected by the API
            const songs = this.currentPlaylist.songs.map(s => ({
                artist: s.artist,
                title: s.title
            }));
            
            console.log('resolvePlaylist: DEBUG - Calling appleMusic.resolvePlaylist with', songs.length, 'songs');

            // Call the resolve API
            const resolved = await appleMusic.resolvePlaylist(songs);
            
            console.log('resolvePlaylist: DEBUG - Resolve result:', resolved);
            
            if (resolved.songs && resolved.songs.length > 0) {
                this.resolvedPlaylist = resolved.songs;
                this.updatePlaylistStatus(
                    `Resolved ${resolved.resolved_count} of ${resolved.original_count} songs`,
                    'success'
                );
                
                // Update play button to show ready
                if (playBtn) {
                    playBtn.disabled = false;
                    playBtn.innerHTML = `<span>▶️ Play ${resolved.resolved_count} Songs</span>`;
                }
                
                // Update resolve button
                if (resolveBtn) {
                    resolveBtn.disabled = false;
                    resolveBtn.innerHTML = '<span>🔍 Resolve Again</span>';
                }
                
                showToast(`Found ${resolved.resolved_count} songs in Apple Music!`, 'success');
            } else {
                console.log('resolvePlaylist: DEBUG - No songs found in result');
                this.updatePlaylistStatus('No songs found in Apple Music. Try generating a new playlist.', 'error');
                if (resolveBtn) {
                    resolveBtn.disabled = false;
                    resolveBtn.innerHTML = '<span>🔍 Resolve Songs</span>';
                }
                showToast('No songs found in Apple Music', 'error');
            }
        } catch (error) {
            console.error('Resolve playlist error:', error);
            this.updatePlaylistStatus('Failed to resolve songs: ' + error.message, 'error');
            if (resolveBtn) {
                resolveBtn.disabled = false;
                resolveBtn.innerHTML = '<span>🔍 Resolve Songs</span>';
            }
            showToast('Failed to resolve playlist: ' + error.message, 'error');
        }
    }

    async playPlaylist() {
        console.log('playPlaylist: DEBUG - Starting, user gesture context should be valid here');
        
        const playBtn = document.getElementById('playlist-play-btn');
        
        // Check if we need to resolve first - if so, we need to do it BEFORE disabling the button
        // so the user can click again after resolve completes
        if (!this.resolvedPlaylist || this.resolvedPlaylist.length === 0) {
            console.log('playPlaylist: DEBUG - Need to resolve playlist first');
            this.updatePlaylistStatus('Resolving songs first...', 'info');
            
            try {
                await this.resolvePlaylist();
            } catch (error) {
                console.error('Resolve failed:', error);
                showToast('Failed to resolve songs: ' + error.message, 'error');
                return;
            }
            
            // Check again after resolve
            if (!this.resolvedPlaylist || this.resolvedPlaylist.length === 0) {
                showToast('No songs available to play', 'error');
                return;
            }
            
            // IMPORTANT: After resolve, we've lost the user gesture context
            // Tell the user to click play again
            this.updatePlaylistStatus('Songs resolved! Click Play again to start.', 'info');
            showToast('Songs found! Click Play again to start.', 'success');
            return;
        }

        // Check if MusicKit is initialized
        if (!appleMusic.isInitialized()) {
            console.log('playPlaylist: DEBUG - MusicKit not initialized');
            this.updatePlaylistStatus('Initializing Apple Music...', 'info');
            
            try {
                await appleMusic.init();
            } catch (error) {
                console.error('Init failed:', error);
                showToast('Failed to initialize Apple Music: ' + error.message, 'error');
                return;
            }
            
            // After init, we've lost the user gesture context
            // Tell the user to click play again
            this.updatePlaylistStatus('Apple Music ready! Click Play again.', 'info');
            showToast('Apple Music ready! Click Play again.', 'success');
            return;
        }
        
        // Check if authorized
        if (!appleMusic.isAuthorized()) {
            console.log('playPlaylist: DEBUG - Not authorized');
            this.updatePlaylistStatus('Please authorize Apple Music...', 'info');
            
            try {
                const authorized = await appleMusic.authorize();
                if (!authorized) {
                    showToast('Please authorize Apple Music to play songs', 'error');
                    this.updatePlaylistStatus('Apple Music not authorized', 'error');
                    return;
                }
            } catch (error) {
                console.error('Authorization failed:', error);
                showToast('Authorization failed: ' + error.message, 'error');
                return;
            }
            
            // After authorization, we've lost the user gesture context
            // Tell the user to click play again
            this.updatePlaylistStatus('Authorized! Click Play again to start.', 'info');
            showToast('Authorized! Click Play again to start.', 'success');
            return;
        }

        // At this point, everything is ready and we should still have user gesture context
        // (assuming the user clicked play again after the previous steps)
        
        if (playBtn) {
            playBtn.disabled = true;
            playBtn.innerHTML = '<span>⏳ Starting...</span>';
        }

        try {
            this.updatePlaylistStatus('Starting playback...', 'info');
            
            console.log('playPlaylist: DEBUG - About to call playPlaylistAndRecord');
            
            // Play the playlist
            // IMPORTANT: This must be called directly from the click handler
            await appleMusic.playPlaylistAndRecord(
                this.resolvedPlaylist,
                this.currentPlaylist?.station_id
            );
            
            this.updatePlaylistStatus('Playing! 🎵', 'success');
            showToast('Playing playlist!', 'success');
            
            // Show now playing section with current song
            const currentSong = appleMusic.getCurrentSong();
            if (currentSong) {
                this.updateNowPlaying(currentSong);
            }
            
            // Update play/pause button to show pause icon
            const playPauseBtn = document.getElementById('btn-play-pause');
            if (playPauseBtn) {
                playPauseBtn.innerHTML = '⏸️';
            }
            
            // DON'T close modal - keep it open for playback controls
            
        } catch (error) {
            console.error('Play playlist error:', error);
            this.updatePlaylistStatus('Failed to play: ' + error.message, 'error');
            showToast('Failed to play playlist: ' + error.message, 'error');
        } finally {
            if (playBtn) {
                playBtn.disabled = false;
                playBtn.innerHTML = '<span>▶️ Play with Apple Music</span>';
            }
        }
    }

    /**
     * Toggle play/pause for current playback
     */
    togglePlayPause() {
        appleMusic.togglePlayPause();
    }

    /**
     * Stop playback and hide now playing section
     */
    stopPlayback() {
        appleMusic.stop();
        this.hideNowPlaying();
        this.updatePlaylistStatus('Playback stopped', 'info');
    }

    /**
     * Skip to next track
     */
    skipToNext() {
        appleMusic.skipToNext();
    }

    /**
     * Skip to previous track
     */
    skipToPrevious() {
        appleMusic.skipToPrevious();
    }

    /**
     * Handle playback state changes from Apple Music
     */
    handlePlaybackStateChange(event) {
        // Update modal play/pause button (if modal is open)
        const playPauseBtn = document.getElementById('btn-play-pause');
        if (playPauseBtn) {
            playPauseBtn.innerHTML = appleMusic.isPlaying() ? '⏸️' : '▶️';
        }
        
        // Update inline card play/pause button (if card is playing)
        if (this.currentlyPlayingCard) {
            const cardBtn = this.currentlyPlayingCard.querySelector('.btn-play-pause');
            if (cardBtn) {
                cardBtn.textContent = appleMusic.isPlaying() ? '⏸️' : '▶️';
            }
        }
    }

    /**
     * Handle media item changes (song changes) from Apple Music
     */
    handleMediaItemChange(event) {
        const currentSong = appleMusic.getCurrentSong();
        if (currentSong) {
            // Update modal now playing section
            this.updateNowPlaying(currentSong);
            
            // Update inline card now playing (if card is playing)
            if (this.currentlyPlayingCard) {
                this.updateCardNowPlaying(this.currentlyPlayingCard);
            }
        }
    }

    /**
     * Update the Now Playing section with current song info
     */
    updateNowPlaying(song) {
        const section = document.getElementById('now-playing-section');
        const titleEl = document.getElementById('now-playing-title');
        const artistEl = document.getElementById('now-playing-artist');
        const artworkEl = document.getElementById('now-playing-artwork');
        
        if (section && titleEl && artistEl) {
            // MusicKit uses attributes property for song details
            const attrs = song.attributes || song;
            
            titleEl.textContent = attrs.name || song.title || 'Unknown';
            artistEl.textContent = attrs.artistName || song.artist || 'Unknown Artist';
            
            // Get artwork URL - Apple Music artwork can be a string URL or an object
            if (artworkEl) {
                let artworkUrl = null;
                const artwork = attrs.artwork || song.artwork;
                
                if (artwork) {
                    if (typeof artwork === 'string') {
                        // String URL with template placeholders
                        artworkUrl = artwork.replace('{w}', '120').replace('{h}', '120');
                    } else if (artwork.url) {
                        // Object with url property
                        artworkUrl = artwork.url;
                        if (artworkUrl && artworkUrl.includes('{w}')) {
                            artworkUrl = artworkUrl.replace('{w}', '120').replace('{h}', '120');
                        }
                    }
                }
                
                if (artworkUrl) {
                    artworkEl.src = artworkUrl;
                } else {
                    // Default placeholder if no artwork
                    artworkEl.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y=".9em" font-size="90">🎵</text></svg>';
                }
            }
            
            section.classList.remove('hidden');
        }
    }

    /**
     * Hide the Now Playing section
     */
    hideNowPlaying() {
        const section = document.getElementById('now-playing-section');
        if (section) {
            section.classList.add('hidden');
        }
    }

    onAuthStateChanged(detail) {
        if (detail && detail.isAuthenticated) {
            this.showGetMyNewsButton();
            this.showMyRadioNewsButton();
            this.showNavMenu();
        } else {
            this.hideGetMyNewsButton();
            this.hideMyRadioNewsButton();
            this.hideNavMenu();
        }
    }

    async loadArticles() {
        console.log('loadArticles called from:', new Error().stack);
        showLoading();

        try {
            const data = await api.getArticles();
            this.articles = data.items || [];

            this.renderArticles();
            this.updateLastUpdated(data.last_updated);

            hideLoading();
            showArticleList();
        } catch (error) {
            hideLoading();
            showToast('Failed to load articles', 'error');
            console.error('Load articles error:', error);
        }
    }

    renderArticles() {
        const list = document.getElementById('article-list');
        list.innerHTML = '';

        this.articles.forEach(article => {
            const card = createArticleCard(article);
            list.appendChild(card);
        });
    }

    updateLastUpdated(timestamp) {
        const el = document.getElementById('last-updated');
        if (timestamp) {
            el.textContent = `Last updated: ${formatDate(timestamp)}`;
        } else {
            el.textContent = '';
        }
    }

    openArticle(article) {
        this.currentArticle = article;
        this.summary = null;

        // Populate modal
        document.getElementById('modal-title').textContent = article.title;
        document.getElementById('modal-meta').innerHTML = `
            <span>${article.author || 'NPR'}</span>
            <span>•</span>
            <span>${formatFullDate(article.published_at)}</span>
            ${article.category ? `<span>•</span><span>${article.category}</span>` : ''}
        `;
        document.getElementById('modal-description').textContent = article.description || 'No description available.';
        document.getElementById('read-original').href = article.link;

        // Reset UI state
        document.getElementById('summary-section').classList.add('hidden');
        document.getElementById('audio-section').classList.add('hidden');
        document.getElementById('listen-btn').disabled = true;

        // If article already has summary, show it
        if (article.has_summary) {
            this.loadSummary(article.id);
        }

        // Mark as read if authenticated
        if (authManager?.isAuthenticated) {
            api.markAsRead(article.id).catch(() => {});
        }

        this.articleModal.open();
    }

    async loadSummary(articleId) {
        try {
            const summary = await api.getSummary(articleId);
            this.summary = summary;
            this.displaySummary(summary);
        } catch (error) {
            console.error('Load summary error:', error);
        }
    }

    async summarizeCurrentArticle() {
        if (!this.currentArticle) return;

        const btn = document.getElementById('summarize-btn');
        btn.disabled = true;
        btn.textContent = '⏳ Summarizing...';

        try {
            const summary = await api.getSummary(this.currentArticle.id);
            this.summary = summary;
            this.displaySummary(summary);
            showToast('Summary generated!', 'success');
        } catch (error) {
            showToast('Failed to generate summary', 'error');
            console.error('Summarize error:', error);
        } finally {
            btn.disabled = false;
            btn.textContent = '✨ Summarize';
        }
    }

    displaySummary(summary) {
        document.getElementById('summary-content').textContent = summary.content;
        document.getElementById('summary-meta').textContent =
            `Generated with ${summary.model_used}${summary.tokens_used ? ` • ${summary.tokens_used} tokens` : ''}`;
        document.getElementById('summary-section').classList.remove('hidden');
        document.getElementById('listen-btn').disabled = false;
    }

    async listenToSummary() {
        if (!this.summary) {
            showToast('Please generate a summary first', 'error');
            return;
        }

        const btn = document.getElementById('listen-btn');
        btn.disabled = true;
        btn.textContent = '⏳ Generating audio...';

        try {
            const result = await api.textToSpeech(this.summary.content);

            const audioPlayer = document.getElementById('audio-player');
            audioPlayer.src = result.audio_url;
            audioPlayer.load();

            document.getElementById('audio-section').classList.remove('hidden');

            // Auto-play
            audioPlayer.play().catch(() => {
                // Autoplay blocked, user needs to click
            });

            showToast('Audio ready!', 'success');
        } catch (error) {
            showToast('Failed to generate audio', 'error');
            console.error('TTS error:', error);
        } finally {
            btn.disabled = false;
            btn.textContent = '🔊 Listen';
        }
    }

    async getPersonalizedNews() {
        const btn = document.getElementById('get-my-news-btn');
        btn.disabled = true;
        btn.textContent = '⏳ Processing...';

        try {
            const data = await api.getPersonalizedNews();
            // Store articles and display in main list
            this.articles = data.articles;
            this.renderArticles();
            showArticleList();
            showToast(`Loaded ${data.articles.length} personalized articles!`, 'success');
        } catch (error) {
            showToast('Failed to get personalized news: ' + error.message, 'error');
            console.error('Get personalized news error:', error);
        } finally {
            btn.disabled = false;
            btn.textContent = '🎯 Get My News';
        }
    }

    renderPersonalizedNews(articles) {
        // Now using main article list instead of popup
        this.articles = articles;
        this.renderArticles();
    }

    closePersonalizedModal() {
        // No longer needed - modal removed
    }

    showGetMyNewsButton() {
        document.getElementById('get-my-news-btn').classList.remove('hidden');
    }

    hideGetMyNewsButton() {
        document.getElementById('get-my-news-btn').classList.add('hidden');
    }

    // Radio News Methods
    showMyRadioNewsButton() {
        document.getElementById('my-radio-news-btn').classList.remove('hidden');
    }

    hideMyRadioNewsButton() {
        document.getElementById('my-radio-news-btn').classList.add('hidden');
    }

    async getRadioNews() {
        const btn = document.getElementById('my-radio-news-btn');
        btn.disabled = true;
        btn.textContent = '⏳ Generating...';

        try {
            const data = await api.getRadioNews();
            this.displayRadioNewsModal(data);
            showToast('Radio news ready!', 'success');
        } catch (error) {
            showToast('Failed to generate radio news: ' + error.message, 'error');
            console.error('Get radio news error:', error);
        } finally {
            btn.disabled = false;
            btn.textContent = '📻 My Radio News';
        }
    }

    displayRadioNewsModal(data) {
        // Store the radio script
        this.radioScript = data.radio_script;
        
        // Populate modal with radio script
        document.getElementById('radio-script-content').textContent = data.radio_script;
        
        // Populate articles list
        const articlesList = document.getElementById('radio-articles-list');
        articlesList.innerHTML = '';
        data.articles.forEach(article => {
            const li = document.createElement('li');
            li.innerHTML = `<a href="#" onclick="app.openArticle(app.articles.find(a => a.id === '${article.id}'))">${escapeHtml(article.title)}</a>`;
            articlesList.appendChild(li);
        });
        
        // Reset audio section
        document.getElementById('radio-audio-section').classList.add('hidden');
        
        // Set up play button
        document.getElementById('play-radio-btn').onclick = () => this.playRadioNews();
        
        // Open modal
        this.radioNewsModal.open();
    }

    async playRadioNews() {
        if (!this.radioScript) {
            showToast('No radio script available', 'error');
            return;
        }

        const btn = document.getElementById('play-radio-btn');
        btn.disabled = true;
        btn.textContent = '⏳ Generating audio...';

        try {
            const result = await api.textToSpeech(this.radioScript);

            const audioPlayer = document.getElementById('radio-audio-player');
            audioPlayer.src = result.audio_url;
            audioPlayer.load();

            document.getElementById('radio-audio-section').classList.remove('hidden');

            // Auto-play
            audioPlayer.play().catch(() => {
                // Autoplay blocked, user needs to click
            });

            showToast('Audio ready!', 'success');
        } catch (error) {
            showToast('Failed to generate audio', 'error');
            console.error('Radio TTS error:', error);
        } finally {
            btn.disabled = false;
            btn.textContent = '▶️ Play Radio News';
        }
    }
}

// Initialize app
let app;
document.addEventListener('DOMContentLoaded', () => {
    app = new App();
});
