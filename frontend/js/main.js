// ========== GLOBAL VARIABLES ==========
let currentUser = null;
let API_BASE_URL = 'http://127.0.0.1:5000/api';

// ========== DOM CONTENT LOADED ==========
document.addEventListener('DOMContentLoaded', () => {
    initializeNavigation();
    checkAuthStatus();
    initializeForms();
    initializeModals();
    loadUserData();
});

// ========== NAVIGATION ==========
function initializeNavigation() {
    // Hamburger menu toggle
    const hamburger = document.getElementById('hamburger');
    const navMenu = document.getElementById('navMenu');
    
    if (hamburger && navMenu) {
        hamburger.addEventListener('click', () => {
            navMenu.classList.toggle('active');
            hamburger.classList.toggle('active');
        });
    }
    
    // Close mobile menu when clicking outside
    document.addEventListener('click', (e) => {
        if (navMenu && navMenu.classList.contains('active')) {
            if (!hamburger.contains(e.target) && !navMenu.contains(e.target)) {
                navMenu.classList.remove('active');
            }
        }
    });
    
    renderNavigation();
}

function isPagesDirectory() {
    return window.location.pathname.split('/').includes('pages');
}

function pageLink(file) {
    return `${isPagesDirectory() ? '' : 'pages/'}${file}.html`;
}

function homeLink() {
    return isPagesDirectory() ? '../index.html' : 'index.html';
}

function renderNavigation() {
    const navMenu = document.getElementById('navMenu');
    const currentPage = window.location.pathname.split('/').pop() || 'index.html';
    const publicLinks = [
        ['Home', homeLink(), 'index.html'],
        ['About', pageLink('about'), 'about.html'],
        ['Services', pageLink('services'), 'services.html'],
        ['Awareness', pageLink('awareness'), 'awareness.html'],
        ['Contact', pageLink('contact'), 'contact.html']
    ];
    const appLinks = currentUser ? [
        ['Dashboard', pageLink('dashboard'), 'dashboard.html'],
        ['Report Crime', pageLink('report-crime'), 'report-crime.html'],
        ['My Complaints', pageLink('my-complaints'), 'my-complaints.html'],
        ['AI Insights', pageLink('ai-insights'), 'ai-insights.html']
    ] : [];

    if (navMenu) {
        navMenu.innerHTML = `<ul>${[...publicLinks, ...appLinks].map(([label, href, file]) =>
            `<li><a href="${href}"${currentPage === file ? ' class="active" aria-current="page"' : ''}>${label}</a></li>`
        ).join('')}</ul>`;
    }
}

// ========== AUTHENTICATION ==========
function checkAuthStatus() {
    const token = localStorage.getItem('access_token');
    const userData = localStorage.getItem('user');
    
    if (token && userData) {
        try {
            JSON.parse(userData);
        } catch {
            clearStoredAuth();
            updateUIForLoggedOutUser();
            enforcePageAccess(false);
            return;
        }
        if (isProtectedPage()) document.body.style.visibility = 'hidden';
        verifyToken(token);
    } else {
        currentUser = null;
        updateUIForLoggedOutUser();
        enforcePageAccess(false);
    }
}

function verifyToken(token) {
    fetch(`${API_BASE_URL}/auth/verify`, {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    })
    .then(async response => {
        const data = await response.json();
        if (!response.ok || !data.valid) throw new Error('Session expired');
        currentUser = JSON.parse(localStorage.getItem('user') || 'null');
        updateUIForLoggedInUser();
        document.body.style.visibility = '';
        renderNavigation();
        enforcePageAccess(true);
    })
    .catch(() => {
        clearStoredAuth();
        currentUser = null;
        updateUIForLoggedOutUser();
        document.body.style.visibility = '';
        enforcePageAccess(false);
    });
}

function isProtectedPage() {
    return new Set(['dashboard.html', 'report-crime.html', 'my-complaints.html', 'profile.html', 'ai-insights.html'])
        .has(window.location.pathname.split('/').pop());
}

function enforcePageAccess(authenticated) {
    const currentPage = window.location.pathname.split('/').pop();
    if (!authenticated && isProtectedPage()) {
        const returnTo = encodeURIComponent(currentPage);
        window.location.replace(`${pageLink('login')}?next=${returnTo}`);
    }
}

function updateUIForLoggedInUser() {
    renderNavigation();
    const navAuth = document.getElementById('navAuth');
    if (navAuth) {
        const base = isPagesDirectory() ? '' : 'pages/';
        navAuth.innerHTML = `
            <div class="dropdown">
                <button class="btn btn-outline" onclick="toggleDropdown()">
                    <i class="fas fa-user"></i> ${escapeHTML(currentUser?.full_name || 'User')}
                </button>
                <div class="dropdown-content" id="userDropdown">
                    <a href="${base}dashboard.html"><i class="fas fa-tachometer-alt"></i> Dashboard</a>
                    <a href="${base}profile.html"><i class="fas fa-user-circle"></i> Profile</a>
                    <a href="${base}my-complaints.html"><i class="fas fa-file-alt"></i> My Complaints</a>
                    <hr>
                    <a href="#" onclick="logout()"><i class="fas fa-sign-out-alt"></i> Logout</a>
                </div>
            </div>
        `;
    }
}

function updateUIForLoggedOutUser() {
    renderNavigation();
    const navAuth = document.getElementById('navAuth');
    if (navAuth) {
        const base = isPagesDirectory() ? '' : 'pages/';
        navAuth.innerHTML = `
            <a href="${base}login.html" class="btn btn-outline">Login</a>
            <a href="${base}register.html" class="btn btn-primary">Register</a>
        `;
    }
}

function clearStoredAuth() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
}

// Escape untrusted values before placing them in an HTML template.
function escapeHTML(value) {
    const entities = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
    return String(value ?? '').replace(/[&<>"']/g, character => entities[character]);
}

function logout() {
    clearStoredAuth();
    currentUser = null;
    updateUIForLoggedOutUser();
    showNotification('Logged out successfully', 'success');
    
    // Redirect to home if not already there
    if (!window.location.pathname.includes('index.html') && 
        window.location.pathname !== '/') {
        setTimeout(() => { window.location.href = homeLink(); }, 1500);
    }
}

function toggleDropdown() {
    const dropdown = document.getElementById('userDropdown');
    if (dropdown) {
        dropdown.classList.toggle('show');
    }
}

// Close dropdown when clicking outside
window.onclick = function(event) {
    if (!event.target.matches('.dropdown button')) {
        const dropdowns = document.getElementsByClassName('dropdown-content');
        for (let i = 0; i < dropdowns.length; i++) {
            if (dropdowns[i].classList.contains('show')) {
                dropdowns[i].classList.remove('show');
            }
        }
    }
}

// ========== FORMS ==========
function initializeForms() {
    // Add CSRF token to all forms if needed
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', handleFormSubmit);
    });
}

function handleFormSubmit(e) {
    // Don't prevent default - let individual handlers manage
    const form = e.target;
    const submitter = e.submitter;
    
    if (submitter && submitter.classList.contains('no-ajax')) {
        return; // Allow normal form submission
    }
}

// ========== MODALS ==========
function initializeModals() {
    const modals = document.querySelectorAll('.modal');
    const closeButtons = document.querySelectorAll('.modal .close');
    
    closeButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const modal = btn.closest('.modal');
            closeModal(modal);
        });
    });
    
    // Close modal when clicking outside
    modals.forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeModal(modal);
            }
        });
    });
}

function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(modal) {
    if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
    }
}

// ========== NOTIFICATIONS ==========
function showNotification(message, type = 'info') {
    // Create notification container if it doesn't exist
    let container = document.getElementById('notification-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'notification-container';
        container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10000;
        `;
        document.body.appendChild(container);
    }
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type}`;
    notification.style.cssText = `
        margin-bottom: 10px;
        animation: slideIn 0.3s ease;
        min-width: 250px;
        max-width: 350px;
    `;
    notification.innerHTML = `
        <i class="fas ${getIconForType(type)}"></i>
        <span>${escapeHTML(message)}</span>
        <button onclick="this.parentElement.remove()" style="float: right; background: none; border: none; cursor: pointer;">&times;</button>
    `;
    
    container.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}

function getIconForType(type) {
    switch(type) {
        case 'success': return 'fa-check-circle';
        case 'danger': return 'fa-exclamation-circle';
        case 'warning': return 'fa-exclamation-triangle';
        default: return 'fa-info-circle';
    }
}

// Add CSS animation
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
`;
document.head.appendChild(style);

// ========== LOADER ==========
function showLoader() {
    let loader = document.getElementById('global-loader');
    if (!loader) {
        loader = document.createElement('div');
        loader.id = 'global-loader';
        loader.className = 'loader-overlay';
        loader.innerHTML = '<div class="loader"></div>';
        document.body.appendChild(loader);
    }
    loader.style.display = 'flex';
}

function hideLoader() {
    const loader = document.getElementById('global-loader');
    if (loader) {
        loader.style.display = 'none';
    }
}

// ========== USER DATA ==========
function loadUserData() {
    if (currentUser) {
        // Update any user-specific elements
        const userElements = document.querySelectorAll('[data-user-field]');
        userElements.forEach(el => {
            const field = el.getAttribute('data-user-field');
            if (currentUser[field]) {
                el.textContent = currentUser[field];
            }
        });
    }
}

// ========== UTILITY FUNCTIONS ==========
function formatDate(dateString) {
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    return new Date(dateString).toLocaleDateString(undefined, options);
}

function formatDateTime(dateString) {
    const options = { 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    };
    return new Date(dateString).toLocaleDateString(undefined, options);
}

function generateComplaintNumber() {
    const prefix = 'CYS';
    const timestamp = Date.now().toString(36).toUpperCase();
    const random = Math.random().toString(36).substring(2, 6).toUpperCase();
    return `${prefix}${timestamp}${random}`;
}

function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function validatePhone(phone) {
    const re = /^[0-9]{10}$/;
    return re.test(phone);
}

function getStatusColor(status) {
    const colors = {
        'pending': 'warning',
        'under_review': 'info',
        'investigating': 'primary',
        'resolved': 'success',
        'rejected': 'danger'
    };
    return colors[status] || 'secondary';
}

function getStatusText(status) {
    const texts = {
        'pending': 'Pending Review',
        'under_review': 'Under Review',
        'investigating': 'Investigating',
        'resolved': 'Resolved',
        'rejected': 'Rejected'
    };
    return texts[status] || status;
}

// ========== EXPORT FUNCTIONS (for global use) ==========
window.showNotification = showNotification;
window.showLoader = showLoader;
window.hideLoader = hideLoader;
window.logout = logout;
window.openModal = openModal;
window.closeModal = closeModal;
window.toggleDropdown = toggleDropdown;
window.formatDate = formatDate;
window.formatDateTime = formatDateTime;
window.generateComplaintNumber = generateComplaintNumber;
window.validateEmail = validateEmail;
window.validatePhone = validatePhone;
window.getStatusColor = getStatusColor;
window.getStatusText = getStatusText;
