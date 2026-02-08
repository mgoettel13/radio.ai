/**
 * Authentication Manager
 */

class AuthManager {
    constructor() {
        this.user = null;
        this.isAuthenticated = false;
        this.modal = document.getElementById('auth-modal');
        this.form = document.getElementById('auth-form');
        this.title = document.getElementById('auth-title');
        this.submitText = document.getElementById('auth-submit-text');
        this.switchText = document.getElementById('auth-switch-text');
        this.switchBtn = document.getElementById('auth-switch-btn');
        this.errorDiv = document.getElementById('auth-error');
        this.authBtn = document.getElementById('auth-btn');

        this.isLoginMode = true;

        this.init();
    }

    init() {
        // Event listeners
        this.authBtn.addEventListener('click', () => this.openModal());
        document.getElementById('close-auth-modal').addEventListener('click', () => this.closeModal());
        this.switchBtn.addEventListener('click', () => this.toggleMode());
        this.form.addEventListener('submit', (e) => this.handleSubmit(e));

        // Close on backdrop click
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) this.closeModal();
        });

        // Listen for auth required events
        window.addEventListener('auth:required', () => {
            this.showError('Please login to continue');
            this.openModal();
        });

        // Check existing session
        this.checkSession();
    }

    async checkSession() {
        if (api.token) {
            try {
                this.user = await api.getCurrentUser();
                this.isAuthenticated = true;
                this.updateUI();
            } catch (error) {
                console.log('Session expired');
                api.setToken(null);
            }
        }
    }

    openModal() {
        this.modal.classList.remove('hidden');
        this.errorDiv.classList.add('hidden');
        this.form.reset();
    }

    closeModal() {
        this.modal.classList.add('hidden');
        this.errorDiv.classList.add('hidden');
    }

    toggleMode() {
        this.isLoginMode = !this.isLoginMode;
        this.updateMode();
    }

    updateMode() {
        if (this.isLoginMode) {
            this.title.textContent = 'Login';
            this.submitText.textContent = 'Login';
            this.switchText.textContent = "Don't have an account?";
            this.switchBtn.textContent = 'Register';
        } else {
            this.title.textContent = 'Register';
            this.submitText.textContent = 'Register';
            this.switchText.textContent = 'Already have an account?';
            this.switchBtn.textContent = 'Login';
        }
        this.errorDiv.classList.add('hidden');
    }

    showError(message) {
        this.errorDiv.textContent = message;
        this.errorDiv.classList.remove('hidden');
    }

    async handleSubmit(e) {
        e.preventDefault();
        this.errorDiv.classList.add('hidden');

        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;

        try {
            if (this.isLoginMode) {
                await api.login(email, password);
            } else {
                await api.register(email, password);
                // Auto-login after registration
                await api.login(email, password);
            }

            // Get user info
            this.user = await api.getCurrentUser();
            this.isAuthenticated = true;

            this.updateUI();
            this.closeModal();
            showToast('Welcome!', 'success');

            // Refresh articles to get user-specific data
            app.loadArticles();

        } catch (error) {
            this.showError(error.message);
        }
    }

    updateUI() {
        if (this.isAuthenticated && this.user) {
            this.authBtn.textContent = 'Logout';
            this.authBtn.onclick = () => this.logout();
        } else {
            this.authBtn.textContent = 'Login';
            this.authBtn.onclick = () => this.openModal();
        }
    }

    async logout() {
        try {
            await api.logout();
        } catch (error) {
            console.log('Logout error:', error);
        }

        this.user = null;
        this.isAuthenticated = false;
        api.setToken(null);
        this.updateUI();
        showToast('Logged out', 'success');

        // Refresh articles without user data
        app.loadArticles();
    }
}

// Initialize auth manager
let authManager;
document.addEventListener('DOMContentLoaded', () => {
    authManager = new AuthManager();
});
