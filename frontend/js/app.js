/**
 * Main Application Logic
 */

class App {
    constructor() {
        this.articles = [];
        this.currentArticle = null;
        this.summary = null;
        this.articleModal = new ModalManager('article-modal');
        this.personalizedNewsModal = new ModalManager('personalized-news-modal');

        this.init();
    }

    init() {
        // Event listeners
        document.getElementById('refresh-btn').addEventListener('click', () => this.refreshArticles());
        document.getElementById('empty-refresh-btn').addEventListener('click', () => this.refreshArticles());
        document.getElementById('summarize-btn').addEventListener('click', () => this.summarizeCurrentArticle());
        document.getElementById('listen-btn').addEventListener('click', () => this.listenToSummary());
        document.getElementById('get-my-news-btn').addEventListener('click', () => this.getPersonalizedNews());
        document.getElementById('close-personalized-modal').addEventListener('click', () => this.closePersonalizedModal());

        // Listen for auth state changes
        window.addEventListener('auth:stateChanged', (e) => this.onAuthStateChanged(e.detail));

        // Don't load articles on init - wait for authentication
        // Articles will be loaded after successful login via auth.js
    }

    onAuthStateChanged(detail) {
        if (detail && detail.isAuthenticated) {
            this.showGetMyNewsButton();
        } else {
            this.hideGetMyNewsButton();
        }
    }

    async loadArticles() {
        showLoading();

        try {
            const data = await api.getArticles();
            this.articles = data.items || [];

            this.renderArticles();
            this.updateLastUpdated(data.last_updated);

            hideLoading();

            if (this.articles.length === 0) {
                showEmptyState();
            } else {
                showArticleList();
            }
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

    async refreshArticles() {
        const btn = document.getElementById('refresh-btn');
        btn.disabled = true;
        btn.textContent = '⏳';

        try {
            const result = await api.refreshArticles();
            showToast(`Added ${result.new_articles} new articles`, 'success');
            await this.loadArticles();
        } catch (error) {
            showToast('Failed to refresh articles', 'error');
            console.error('Refresh error:', error);
        } finally {
            btn.disabled = false;
            btn.textContent = '🔄';
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
            this.renderPersonalizedNews(data.articles);
            this.personalizedNewsModal.open();
            showToast('Personalized news loaded!', 'success');
        } catch (error) {
            showToast('Failed to get personalized news: ' + error.message, 'error');
            console.error('Get personalized news error:', error);
        } finally {
            btn.disabled = false;
            btn.textContent = '🎯 Get My News';
        }
    }

    renderPersonalizedNews(articles) {
        const list = document.getElementById('personalized-news-list');
        list.innerHTML = '';

        articles.forEach((article, index) => {
            const item = document.createElement('div');
            item.className = 'personalized-news-item';
            item.innerHTML = `
                <div class="personalized-rank">#${index + 1}</div>
                <div class="personalized-content">
                    <h3 class="personalized-title">${escapeHtml(article.title)}</h3>
                    <div class="personalized-meta">
                        <span>${article.author || 'NPR'}</span>
                        <span>•</span>
                        <span>${formatDate(article.published_at)}</span>
                    </div>
                    ${article.description ? `<p class="personalized-description">${escapeHtml(truncate(article.description, 200))}</p>` : ''}
                    <a href="${escapeHtml(article.link)}" target="_blank" rel="noopener" class="personalized-link">Read More →</a>
                </div>
            `;
            list.appendChild(item);
        });
    }

    closePersonalizedModal() {
        this.personalizedNewsModal.close();
    }

    showGetMyNewsButton() {
        document.getElementById('get-my-news-btn').classList.remove('hidden');
    }

    hideGetMyNewsButton() {
        document.getElementById('get-my-news-btn').classList.add('hidden');
    }
}

// Initialize app
let app;
document.addEventListener('DOMContentLoaded', () => {
    app = new App();
});
