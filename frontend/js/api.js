/**
 * API Client for NPR News Summarizer
 */

const API_BASE_URL = '';

class API {
    constructor() {
        this.baseUrl = API_BASE_URL;
        this.token = localStorage.getItem('auth_token');
    }

    setToken(token) {
        this.token = token;
        if (token) {
            localStorage.setItem('auth_token', token);
        } else {
            localStorage.removeItem('auth_token');
        }
    }

    getHeaders() {
        const headers = {
            'Content-Type': 'application/json'
        };
        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }
        return headers;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const config = {
            ...options,
            headers: {
                ...this.getHeaders(),
                ...options.headers
            }
        };

        try {
            const response = await fetch(url, config);

            if (response.status === 401) {
                // Token expired or invalid
                this.setToken(null);
                window.dispatchEvent(new CustomEvent('auth:required'));
                throw new Error('Authentication required');
            }

            if (!response.ok) {
                const error = await response.json().catch(() => ({ detail: 'Request failed' }));
                throw new Error(error.detail || `HTTP ${response.status}`);
            }

            // Return null for 204 No Content
            if (response.status === 204) {
                return null;
            }

            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    // Articles
    async getArticles() {
        return this.request('/api/articles');
    }

    async refreshArticles() {
        return this.request('/api/articles/refresh', { method: 'POST' });
    }

    async getArticle(id) {
        return this.request(`/api/articles/${id}`);
    }

    async getSummary(articleId) {
        return this.request(`/api/articles/${articleId}/summary`);
    }

    async markAsRead(articleId) {
        return this.request(`/api/articles/${articleId}/read`, { method: 'POST' });
    }

    async toggleFavorite(articleId) {
        return this.request(`/api/articles/${articleId}/favorite`, { method: 'POST' });
    }

    // TTS
    async textToSpeech(text, voiceId = 'matthew') {
        return this.request('/api/tts/speak', {
            method: 'POST',
            body: JSON.stringify({ text, voice_id: voiceId })
        });
    }

    async getVoices() {
        return this.request('/api/tts/voices');
    }

    // Auth
    async login(email, password) {
        const formData = new URLSearchParams();
        formData.append('username', email);
        formData.append('password', password);

        const response = await fetch(`${this.baseUrl}/auth/jwt/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: formData
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Login failed' }));
            throw new Error(error.detail || 'Login failed');
        }

        const data = await response.json();
        this.setToken(data.access_token);
        return data;
    }

    async register(email, password) {
        return this.request('/auth/register', {
            method: 'POST',
            body: JSON.stringify({ email, password })
        });
    }

    async logout() {
        await this.request('/auth/jwt/logout', { method: 'POST' });
        this.setToken(null);
    }

    async getCurrentUser() {
        return this.request('/auth/me');
    }

    async forgotPassword(email) {
        return this.request('/auth/forgot-password', {
            method: 'POST',
            body: JSON.stringify({ email })
        });
    }

    async resetPassword(token, password) {
        return this.request('/auth/reset-password', {
            method: 'POST',
            body: JSON.stringify({ token, password })
        });
    }

    // Settings - Profile
    async getProfile() {
        return this.request('/api/settings/profile');
    }

    async updateProfile(data) {
        return this.request('/api/settings/profile', {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    // Settings - Preferences
    async getPreferences() {
        return this.request('/api/settings/preferences');
    }

    async updatePreferences(data) {
        return this.request('/api/settings/preferences', {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    // Personalized News
    async getPersonalizedNews() {
        return this.request('/api/articles/personalized', { method: 'POST' });
    }

    // Radio News
    async getRadioNews() {
        return this.request('/api/articles/radio-news', { method: 'POST' });
    }
}

// Create global API instance
const api = new API();
