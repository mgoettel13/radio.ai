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
        this.radioScript = null;

        this.init();
    }

    init() {
        console.log('App.init() called');
        // Event listeners
        document.getElementById('summarize-btn').addEventListener('click', () => this.summarizeCurrentArticle());
        document.getElementById('listen-btn').addEventListener('click', () => this.listenToSummary());
        document.getElementById('get-my-news-btn').addEventListener('click', () => this.getPersonalizedNews());
        document.getElementById('my-radio-news-btn').addEventListener('click', () => this.getRadioNews());

        // Listen for auth state changes
        window.addEventListener('auth:stateChanged', (e) => this.onAuthStateChanged(e.detail));

        // Don't load articles on init - only load when user clicks "Get My News"
        this.articles = [];
    }

    onAuthStateChanged(detail) {
        if (detail && detail.isAuthenticated) {
            this.showGetMyNewsButton();
            this.showMyRadioNewsButton();
        } else {
            this.hideGetMyNewsButton();
            this.hideMyRadioNewsButton();
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
