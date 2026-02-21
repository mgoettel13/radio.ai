/**
 * UI Utilities and Components
 */

// Toast notifications
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;

    container.appendChild(toast);

    // Remove after 3 seconds
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(20px)';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Format date
function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;

    // Less than 1 hour
    if (diff < 3600000) {
        const minutes = Math.floor(diff / 60000);
        return minutes < 1 ? 'Just now' : `${minutes}m ago`;
    }

    // Less than 24 hours
    if (diff < 86400000) {
        const hours = Math.floor(diff / 3600000);
        return `${hours}h ago`;
    }

    // Less than 7 days
    if (diff < 604800000) {
        const days = Math.floor(diff / 86400000);
        return `${days}d ago`;
    }

    // Default format
    return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric'
    });
}

// Format full date
function formatFullDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
        month: 'long',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Truncate text
function truncate(text, maxLength = 150) {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength).trim() + '...';
}

// Create article card HTML
function createArticleCard(article) {
    const card = document.createElement('div');
    card.className = `article-card ${article.is_read ? 'read' : ''} ${article.is_favorite ? 'favorite' : ''}`;
    card.dataset.id = article.id;

    const badges = [];
    if (article.has_summary) {
        badges.push('<span class="badge summary">✨ Summary</span>');
    }
    if (article.is_favorite) {
        badges.push('<span class="badge">★</span>');
    }

    card.innerHTML = `
        <div class="article-header">
            <h3 class="article-title">${escapeHtml(article.title)}</h3>
            ${badges.length ? `<div class="article-badges">${badges.join('')}</div>` : ''}
        </div>
        <div class="article-meta">
            <span>${article.author || 'NPR'}</span>
            <span>•</span>
            <span>${formatDate(article.published_at)}</span>
            ${article.category ? `<span>•</span><span>${escapeHtml(article.category)}</span>` : ''}
        </div>
        ${article.description ? `<p class="article-excerpt">${escapeHtml(truncate(article.description))}</p>` : ''}
    `;

    card.addEventListener('click', () => app.openArticle(article));

    return card;
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Create station card HTML
function createStationCard(station) {
    const card = document.createElement('div');
    card.className = 'station-card';
    card.dataset.id = station.id;
    
    const imageHtml = station.image_url 
        ? `<img src="${escapeHtml(station.image_url)}" alt="${escapeHtml(station.name)}">`
        : `<span class="placeholder-icon">🎸</span>`;
    
    const descriptionHtml = station.description 
        ? `<p class="station-card-description">${escapeHtml(station.description)}</p>` 
        : '';
    
    card.innerHTML = `
        <div class="station-card-image">
            ${imageHtml}
            <button class="station-play-btn" title="Generate Playlist">▶️ <span class="play-btn-text">Play</span></button>
        </div>
        <div class="station-card-content">
            <h3 class="station-card-name">${escapeHtml(station.name)}</h3>
            ${descriptionHtml}
            <p class="station-card-duration">⏱️ ${station.duration} hour${station.duration > 1 ? 's' : ''}</p>
        </div>
    `;
    
    // Handle play button click
    const playBtn = card.querySelector('.station-play-btn');
    playBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        app.generatePlaylist(station);
    });
    
    // Handle card click for editing
    card.addEventListener('click', () => app.openStation(station));
    
    return card;
}

// Modal management
class ModalManager {
    constructor(modalId) {
        this.modal = document.getElementById(modalId);
        this.closeBtn = this.modal.querySelector('[id^="close-"]');

        this.closeBtn.addEventListener('click', () => this.close());
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) this.close();
        });
    }

    open() {
        this.modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    }

    close() {
        this.modal.classList.add('hidden');
        document.body.style.overflow = '';
    }
}

// Loading state
function showLoading() {
    document.getElementById('loading').classList.remove('hidden');
    document.getElementById('article-list').classList.add('hidden');
}

function hideLoading() {
    document.getElementById('loading').classList.add('hidden');
}

function showArticleList() {
    document.getElementById('article-list').classList.remove('hidden');
}
