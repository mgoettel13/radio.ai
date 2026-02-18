/**
 * Authentication Manager
 */

class AuthManager {
    constructor() {
        this.user = null;
        this.isAuthenticated = false;
        
        // Login screen elements (full-screen overlay)
        this.loginScreen = document.getElementById('login-screen');
        this.loginScreenForm = document.getElementById('login-screen-auth-form');
        this.loginScreenError = document.getElementById('login-screen-error');
        this.loginScreenSubmitText = document.getElementById('login-screen-submit-text');
        this.loginScreenSwitchText = document.getElementById('login-screen-switch-text');
        this.loginScreenSwitchBtn = document.getElementById('login-screen-switch-btn');

        // Auth modal elements (for forgot password flow)
        this.modal = document.getElementById('auth-modal');
        this.form = document.getElementById('auth-form');
        this.title = document.getElementById('auth-title');
        this.submitText = document.getElementById('auth-submit-text');
        this.switchText = document.getElementById('auth-switch-text');
        this.switchBtn = document.getElementById('auth-switch-btn');
        this.errorDiv = document.getElementById('auth-error');
        this.authBtn = document.getElementById('auth-btn');

        // Forgot password modal elements
        this.forgotModal = document.getElementById('forgot-password-modal');
        this.forgotForm = document.getElementById('forgot-password-form');
        this.forgotError = document.getElementById('forgot-error');
        this.forgotSuccess = document.getElementById('forgot-success');

        // Reset password modal elements
        this.resetModal = document.getElementById('reset-password-modal');
        this.resetForm = document.getElementById('reset-password-form');
        this.resetError = document.getElementById('reset-error');
        this.resetSuccess = document.getElementById('reset-success');

        this.isLoginMode = true;
        this.resetToken = null;

        this.init();
    }

    init() {
        // Login screen event listeners
        this.loginScreenForm.addEventListener('submit', (e) => this.handleLoginScreenSubmit(e));
        this.loginScreenSwitchBtn.addEventListener('click', () => this.toggleLoginScreenMode());
        document.getElementById('login-screen-forgot-btn').addEventListener('click', () => this.openForgotModal());

        // Auth modal event listeners
        this.authBtn.addEventListener('click', () => this.logout());
        document.getElementById('close-auth-modal').addEventListener('click', () => this.closeModal());
        this.switchBtn.addEventListener('click', () => this.toggleMode());
        this.form.addEventListener('submit', (e) => this.handleSubmit(e));

        // Forgot password event listeners
        document.getElementById('forgot-password-btn').addEventListener('click', () => this.openForgotModal());
        document.getElementById('close-forgot-modal').addEventListener('click', () => this.closeForgotModal());
        document.getElementById('back-to-login-btn').addEventListener('click', () => {
            this.closeForgotModal();
            this.openModal();
        });
        this.forgotForm.addEventListener('submit', (e) => this.handleForgotSubmit(e));

        // Reset password event listeners
        document.getElementById('close-reset-modal').addEventListener('click', () => this.closeResetModal());
        this.resetForm.addEventListener('submit', (e) => this.handleResetSubmit(e));

        // Close modals on backdrop click
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) this.closeModal();
        });
        this.forgotModal.addEventListener('click', (e) => {
            if (e.target === this.forgotModal) this.closeForgotModal();
        });
        this.resetModal.addEventListener('click', (e) => {
            if (e.target === this.resetModal) this.closeResetModal();
        });

        // Listen for auth required events
        window.addEventListener('auth:required', () => {
            this.showError('Please login to continue');
            this.openModal();
        });

        // Check for reset token in URL
        this.checkResetToken();

        // Check existing session
        this.checkSession();
    }

    checkResetToken() {
        const urlParams = new URLSearchParams(window.location.search);
        const resetToken = urlParams.get('reset_token');
        
        if (resetToken) {
            this.resetToken = resetToken;
            // Clear the URL parameter
            window.history.replaceState({}, document.title, window.location.pathname);
            // Open reset password modal
            this.openResetModal();
        }
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
                this.showLoginScreen();
            }
        } else {
            this.showLoginScreen();
        }
    }

    showLoginScreen() {
        this.loginScreen.classList.remove('hidden');
    }

    hideLoginScreen() {
        this.loginScreen.classList.add('hidden');
    }

    toggleLoginScreenMode() {
        this.isLoginMode = !this.isLoginMode;
        if (this.isLoginMode) {
            this.loginScreenSubmitText.textContent = 'Login';
            this.loginScreenSwitchText.textContent = "Don't have an account?";
            this.loginScreenSwitchBtn.textContent = 'Register';
        } else {
            this.loginScreenSubmitText.textContent = 'Register';
            this.loginScreenSwitchText.textContent = 'Already have an account?';
            this.loginScreenSwitchBtn.textContent = 'Login';
        }
        this.loginScreenError.classList.add('hidden');
    }

    async handleLoginScreenSubmit(e) {
        e.preventDefault();
        this.loginScreenError.classList.add('hidden');

        const email = document.getElementById('login-screen-email').value;
        const password = document.getElementById('login-screen-password').value;

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
            this.hideLoginScreen();
            showToast('Welcome!', 'success');

        } catch (error) {
            this.loginScreenError.textContent = error.message;
            this.loginScreenError.classList.remove('hidden');
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

    openForgotModal() {
        this.closeModal();
        this.forgotModal.classList.remove('hidden');
        this.forgotError.classList.add('hidden');
        this.forgotSuccess.classList.add('hidden');
        this.forgotForm.reset();
    }

    closeForgotModal() {
        this.forgotModal.classList.add('hidden');
        this.forgotError.classList.add('hidden');
        this.forgotSuccess.classList.add('hidden');
    }

    openResetModal() {
        this.resetModal.classList.remove('hidden');
        this.resetError.classList.add('hidden');
        this.resetSuccess.classList.add('hidden');
        this.resetForm.reset();
    }

    closeResetModal() {
        this.resetModal.classList.add('hidden');
        this.resetError.classList.add('hidden');
        this.resetSuccess.classList.add('hidden');
        this.resetToken = null;
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

        } catch (error) {
            this.showError(error.message);
        }
    }

    async handleForgotSubmit(e) {
        e.preventDefault();
        this.forgotError.classList.add('hidden');
        this.forgotSuccess.classList.add('hidden');

        const email = document.getElementById('forgot-email').value;

        try {
            await api.forgotPassword(email);
            
            // Show success message
            this.forgotSuccess.textContent = 'If the email exists, a reset link has been sent.';
            this.forgotSuccess.classList.remove('hidden');
            this.forgotForm.reset();
            
        } catch (error) {
            this.forgotError.textContent = error.message;
            this.forgotError.classList.remove('hidden');
        }
    }

    async handleResetSubmit(e) {
        e.preventDefault();
        this.resetError.classList.add('hidden');
        this.resetSuccess.classList.add('hidden');

        const password = document.getElementById('new-password').value;
        const confirmPassword = document.getElementById('confirm-password').value;

        // Validate passwords match
        if (password !== confirmPassword) {
            this.resetError.textContent = 'Passwords do not match';
            this.resetError.classList.remove('hidden');
            return;
        }

        // Validate password length
        if (password.length < 8) {
            this.resetError.textContent = 'Password must be at least 8 characters';
            this.resetError.classList.remove('hidden');
            return;
        }

        try {
            await api.resetPassword(this.resetToken, password);
            
            // Show success message
            this.resetSuccess.textContent = 'Password has been reset successfully! You can now login with your new password.';
            this.resetSuccess.classList.remove('hidden');
            
            // Close modal after 2 seconds and show login screen
            setTimeout(() => {
                this.closeResetModal();
                this.showLoginScreen();
            }, 2000);
            
        } catch (error) {
            this.resetError.textContent = error.message;
            this.resetError.classList.remove('hidden');
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
        
        // Dispatch auth state change event for other components
        window.dispatchEvent(new CustomEvent('auth:stateChanged', {
            detail: {
                isAuthenticated: this.isAuthenticated,
                user: this.user
            }
        }));
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

        // Show login screen instead of refreshing articles
        this.showLoginScreen();
    }
}

// Initialize auth manager
let authManager;
document.addEventListener('DOMContentLoaded', () => {
    authManager = new AuthManager();
});
