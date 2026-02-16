/**
 * Settings Manager
 * Handles user profile and news preferences settings.
 */

class SettingsManager {
    constructor() {
        this.modal = document.getElementById('settings-modal');
        this.settingsBtn = document.getElementById('settings-btn');
        
        // Profile elements
        this.profileForm = document.getElementById('profile-form');
        this.profileError = document.getElementById('profile-error');
        this.profileSuccess = document.getElementById('profile-success');
        
        // Preferences elements
        this.preferencesForm = document.getElementById('preferences-form');
        this.prefsError = document.getElementById('prefs-error');
        this.prefsSuccess = document.getElementById('prefs-success');
        
        // Tab elements
        this.tabs = document.querySelectorAll('.settings-tab');
        this.tabContents = document.querySelectorAll('.settings-tab-content');
        
        this.profileLoaded = false;
        this.preferencesLoaded = false;
        
        this.init();
    }
    
    init() {
        // Settings button click
        this.settingsBtn.addEventListener('click', () => this.openModal());
        
        // Close modal
        document.getElementById('close-settings-modal').addEventListener('click', () => this.closeModal());
        
        // Close on backdrop click
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) this.closeModal();
        });
        
        // Tab switching
        this.tabs.forEach(tab => {
            tab.addEventListener('click', () => this.switchTab(tab.dataset.tab));
        });
        
        // Profile form submit
        this.profileForm.addEventListener('submit', (e) => this.handleProfileSubmit(e));
        
        // Preferences form submit
        this.preferencesForm.addEventListener('submit', (e) => this.handlePreferencesSubmit(e));
        
        // Reset password button from settings
        document.getElementById('reset-password-from-settings').addEventListener('click', () => {
            const email = document.getElementById('profile-email').value;
            this.handlePasswordReset(email);
        });
        
        // Listen for auth state changes
        window.addEventListener('auth:stateChanged', (e) => this.onAuthStateChanged(e.detail));
    }
    
    onAuthStateChanged(detail) {
        if (detail && detail.isAuthenticated) {
            this.settingsBtn.classList.remove('hidden');
        } else {
            this.settingsBtn.classList.add('hidden');
            this.closeModal();
        }
    }
    
    // Method to check current auth state (called after initialization)
    checkAuthState() {
        if (typeof authManager !== 'undefined' && authManager.isAuthenticated) {
            this.settingsBtn.classList.remove('hidden');
        } else {
            this.settingsBtn.classList.add('hidden');
        }
    }
    
    checkInitialAuthState() {
        // Check if user is already authenticated (from localStorage token)
        if (api.token) {
            this.settingsBtn.classList.remove('hidden');
        }
    }
    
    openModal() {
        this.modal.classList.remove('hidden');
        this.profileLoaded = false;
        this.preferencesLoaded = false;
        this.loadProfile();
        this.loadPreferences();
    }
    
    closeModal() {
        this.modal.classList.add('hidden');
        this.hideMessages();
    }
    
    switchTab(tabName) {
        // Update tab buttons
        this.tabs.forEach(tab => {
            tab.classList.toggle('active', tab.dataset.tab === tabName);
        });
        
        // Update tab contents
        this.tabContents.forEach(content => {
            content.classList.toggle('active', content.id === `${tabName}-tab`);
        });
    }
    
    async loadProfile() {
        try {
            const profile = await api.getProfile();
            
            document.getElementById('profile-full-name').value = profile.full_name || '';
            document.getElementById('profile-email').value = profile.email || '';
            document.getElementById('profile-age').value = profile.age || '';
            document.getElementById('profile-country').value = profile.country || '';
            document.getElementById('profile-language').value = profile.language || '';
        } catch (error) {
            console.error('Failed to load profile:', error);
            this.showError(this.profileError, 'Failed to load profile');
        }
    }
    
    async loadPreferences() {
        try {
            const prefs = await api.getPreferences();
            
            document.getElementById('prefs-country').value = prefs.country || '';
            document.getElementById('prefs-location').value = prefs.location || '';
            document.getElementById('prefs-keywords').value = (prefs.keywords || []).join(', ');
            
            // Set topic checkboxes
            const topics = prefs.topics || [];
            document.querySelectorAll('input[name="topics"]').forEach(checkbox => {
                checkbox.checked = topics.includes(checkbox.value);
            });
        } catch (error) {
            console.error('Failed to load preferences:', error);
            this.showError(this.prefsError, 'Failed to load preferences');
        }
    }
    
    async handleProfileSubmit(e) {
        e.preventDefault();
        this.hideMessages();
        
        const data = {
            full_name: document.getElementById('profile-full-name').value || null,
            age: document.getElementById('profile-age').value ? parseInt(document.getElementById('profile-age').value) : null,
            country: document.getElementById('profile-country').value || null,
            language: document.getElementById('profile-language').value || null,
        };
        
        // Remove null values
        Object.keys(data).forEach(key => {
            if (data[key] === null || data[key] === '') {
                delete data[key];
            }
        });
        
        try {
            await api.updateProfile(data);
            this.showSuccess(this.profileSuccess, 'Profile saved successfully');
        } catch (error) {
            console.error('Failed to save profile:', error);
            this.showError(this.profileError, error.message || 'Failed to save profile');
        }
    }
    
    async handlePreferencesSubmit(e) {
        e.preventDefault();
        this.hideMessages();
        
        // Get selected topics
        const selectedTopics = [];
        document.querySelectorAll('input[name="topics"]:checked').forEach(checkbox => {
            selectedTopics.push(checkbox.value);
        });
        
        // Parse keywords
        const keywordsStr = document.getElementById('prefs-keywords').value;
        const keywords = keywordsStr
            .split(',')
            .map(k => k.trim())
            .filter(k => k.length > 0);
        
        const data = {
            country: document.getElementById('prefs-country').value || null,
            location: document.getElementById('prefs-location').value || null,
            topics: selectedTopics.length > 0 ? selectedTopics : null,
            keywords: keywords.length > 0 ? keywords : null,
        };
        
        // Remove null values
        Object.keys(data).forEach(key => {
            if (data[key] === null) {
                delete data[key];
            }
        });
        
        try {
            await api.updatePreferences(data);
            this.showSuccess(this.prefsSuccess, 'Preferences saved successfully');
        } catch (error) {
            console.error('Failed to save preferences:', error);
            this.showError(this.prefsError, error.message || 'Failed to save preferences');
        }
    }
    
    async handlePasswordReset(email) {
        if (!email) {
            this.showError(this.profileError, 'No email address found');
            return;
        }
        
        try {
            await api.forgotPassword(email);
            this.showSuccess(this.profileSuccess, 'Password reset email sent. Check your inbox.');
        } catch (error) {
            console.error('Failed to send reset email:', error);
            this.showError(this.profileError, 'Failed to send reset email');
        }
    }
    
    showError(element, message) {
        element.textContent = message;
        element.classList.remove('hidden');
    }
    
    showSuccess(element, message) {
        element.textContent = message;
        element.classList.remove('hidden');
    }
    
    hideMessages() {
        this.profileError.classList.add('hidden');
        this.profileSuccess.classList.add('hidden');
        this.prefsError.classList.add('hidden');
        this.prefsSuccess.classList.add('hidden');
    }
}

// Initialize settings manager when DOM is ready
let settingsManager;
document.addEventListener('DOMContentLoaded', () => {
    settingsManager = new SettingsManager();
    // Check initial auth state after a short delay to allow auth manager to initialize
    setTimeout(() => {
        settingsManager.checkAuthState();
    }, 100);
});
