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

        // Listen for auth state changes
        window.addEventListener('auth:stateChanged', (e) => this.onAuthStateChanged(e.detail));

        // Don't load articles on init - only load when user clicks "Get My News"
        this.articles = [];
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
        this.clearStationImagePreview();
        document.getElementById('station-error').classList.add('hidden');
        
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
            image_url: imageUrl || null
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

    displayPlaylistModal(playlist) {
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

        // Setup close button
        const closeBtn = document.getElementById('playlist-close-btn');
        closeBtn.onclick = () => this.playlistModal.close();

        this.playlistModal.open();
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
