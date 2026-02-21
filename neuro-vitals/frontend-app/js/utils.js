// Global state management
const state = {
    currentUser: null,
    isAuthenticated: false
};

// Initialize auth state
function initAuth() {
    const user = localStorage.getItem('neurovitals_currentUser');
    if (user) {
        state.currentUser = JSON.parse(user);
        state.isAuthenticated = true;
    }
    return state.isAuthenticated;
}

// Check if user is logged in and has completed onboarding
function requireAuth() {
    if (!initAuth()) {
        window.location.href = 'index.html';
        return false;
    }

    if (!state.currentUser.onboardingComplete) {
        window.location.href = 'onboarding.html';
        return false;
    }

    return true;
}

// Get current user's name
function getUserName() {
    return state.currentUser?.profile?.name || state.currentUser?.name || 'User';
}

// Get user profile
function getUserProfile() {
    return state.currentUser?.profile || {};
}

// Logout function
function logout() {
    localStorage.removeItem('neurovitals_currentUser');
    window.location.href = 'index.html';
}

// API configuration
const API_BASE = 'http://localhost:8000/api';

// API helper functions
async function apiCall(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });

        if (!response.ok) {
            throw new Error(`API call failed: ${response.statusText}`);
        }

        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// Show loading state
function showLoading(containerId) {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = `
            <div class="flex flex-col items-center justify-center py-16">
                <div class="spinner mb-4"></div>
                <p class="text-slate-400">Loading...</p>
            </div>
        `;
    }
}

// Show error state
function showError(containerId, message) {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = `
            <div class="flex flex-col items-center justify-center py-16 text-center">
                <span class="material-symbols-outlined text-5xl text-red-400 mb-4">error</span>
                <p class="text-red-400 font-bold mb-2">Error</p>
                <p class="text-slate-400">${message}</p>
            </div>
        `;
    }
}

// Simple toast notification
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `fixed top-6 right-6 z-[9999] px-6 py-4 rounded-xl shadow-2xl animate-slide-in ${type === 'success' ? 'bg-green-500' : 'bg-red-500'
        } text-white font-bold`;
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100px)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Add spinner CSS if not already present
if (!document.querySelector('style#global-spinner')) {
    const style = document.createElement('style');
    style.id = 'global-spinner';
    style.textContent = `
        .spinner {
            border: 3px solid rgba(255, 255, 255, 0.1);
            border-top-color: #667eea;
            border-radius: 50%;
            width: 32px;
            height: 32px;
            animation: spin 1s linear infinite;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        @keyframes slide-in {
            from { opacity: 0; transform: translateX(100px); }
            to { opacity: 1; transform: translateX(0); }
        }
        .animate-slide-in {
            animation: slide-in 0.3s ease;
        }
    `;
    document.head.appendChild(style);
}
