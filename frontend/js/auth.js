// ========== AUTHENTICATION HANDLERS ==========
const AUTH_API_URL = 'http://127.0.0.1:5000/api/auth';

// ========== REGISTRATION AND LOGIN FORM SETUP ==========
document.addEventListener('DOMContentLoaded', () => {
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', handleRegister);
    }

    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
});

// Accept a 10-digit Indian mobile number starting with 6, 7, 8, or 9.
// Reject numbers made up of the same digit repeated ten times.
function isValidIndianMobile(phone) {
    const value = String(phone || '').trim();
    return /^[6-9]\d{9}$/.test(value) && !/^(\d)\1{9}$/.test(value);
}

// ========== REGISTRATION ==========
async function handleRegister(e) {
    e.preventDefault();

    const full_name = document.getElementById('full_name')?.value.trim();
    const email = document.getElementById('email')?.value.trim();
    const phone = document.getElementById('phone')?.value.trim();
    const password = document.getElementById('password')?.value;
    const confirm_password =
        document.getElementById('confirm_password')?.value;

    if (!full_name || !email || !phone || !password || !confirm_password) {
        showNotification('Please fill all fields', 'danger');
        return;
    }

    if (!validateEmail(email)) {
        showNotification('Please enter a valid email address', 'danger');
        return;
    }

    if (!isValidIndianMobile(phone)) {
        showNotification(
            'Enter a valid 10-digit Indian mobile number starting with 6, 7, 8, or 9.',
            'danger'
        );
        return;
    }

    if (password !== confirm_password) {
        showNotification('Passwords do not match', 'danger');
        return;
    }

    if (!isPasswordStrong(password)) {
        showNotification(
            'Password must be at least 6 characters and include an uppercase letter and a number',
            'danger'
        );
        return;
    }

    showLoader();

    try {
        const response = await fetch(`${AUTH_API_URL}/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                full_name,
                email,
                phone,
                password
            })
        });

        const data = await response.json().catch(() => ({}));

        if (response.ok) {
            showNotification(
                'Registration successful! Please login.',
                'success'
            );

            setTimeout(() => {
                window.location.href = 'login.html';
            }, 2000);
        } else {
            showNotification(
                data.error ||
                    data.message ||
                    `Registration failed (HTTP ${response.status})`,
                'danger'
            );
        }
    } catch (error) {
        console.error('Registration error:', error);
        showNotification('Network error. Please try again.', 'danger');
    } finally {
        hideLoader();
    }
}

// ========== LOGIN ==========
async function handleLogin(e) {
    e.preventDefault();

    const email = document.getElementById('email')?.value.trim();
    const password = document.getElementById('password')?.value;
    const remember = document.getElementById('remember')?.checked;

    if (!email || !password) {
        showNotification('Please enter email and password', 'danger');
        return;
    }

    showLoader();

    try {
        const response = await fetch(`${AUTH_API_URL}/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email,
                password,
                remember
            })
        });

        const data = await response.json().catch(() => ({}));

        if (response.ok) {
            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('refresh_token', data.refresh_token);
            localStorage.setItem('user', JSON.stringify(data.user));

            showNotification(
                'Login successful! Redirecting...',
                'success'
            );

            setTimeout(() => {
                const allowedNextPages = new Set([
                    'dashboard.html',
                    'report-crime.html',
                    'my-complaints.html',
                    'profile.html',
                    'ai-insights.html'
                ]);

                const requestedPage =
                    new URLSearchParams(window.location.search).get('next');

                window.location.href = allowedNextPages.has(requestedPage)
                    ? requestedPage
                    : 'dashboard.html';
            }, 1500);
        } else {
            showNotification(
                data.error ||
                    data.message ||
                    `Login failed (HTTP ${response.status})`,
                'danger'
            );
        }
    } catch (error) {
        console.error('Login error:', error);
        showNotification('Network error. Please try again.', 'danger');
    } finally {
        hideLoader();
    }
}

// ========== LOGOUT ==========
function logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');

    showNotification('Logged out successfully', 'success');

    setTimeout(() => {
        window.location.href = '../index.html';
    }, 1000);
}

// ========== PROFILE MANAGEMENT ==========
async function loadProfile() {
    const token = localStorage.getItem('access_token');

    if (!token) {
        window.location.href = 'login.html';
        return;
    }

    showLoader();

    try {
        const response = await fetch(`${AUTH_API_URL}/profile`, {
            headers: {
                Authorization: `Bearer ${token}`
            }
        });

        const data = await response.json().catch(() => ({}));

        if (response.ok) {
            displayProfile(data.user);
        } else {
            showNotification(
                data.error || data.message || 'Failed to load profile',
                'danger'
            );

            if (data.message === 'Token expired') {
                logout();
            }
        }
    } catch (error) {
        console.error('Profile load error:', error);
        showNotification('Network error', 'danger');
    } finally {
        hideLoader();
    }
}

function displayProfile(user) {
    const fields = ['full_name', 'email', 'phone', 'role'];

    fields.forEach((field) => {
        const element = document.getElementById(`profile_${field}`);

        if (element) {
            element.textContent = user[field] || 'Not provided';
        }

        const input = document.getElementById(field);

        if (input) {
            input.value = user[field] || '';
        }
    });

    const joinedElement = document.getElementById('profile_joined');

    if (joinedElement && user.created_at) {
        joinedElement.textContent = formatDate(user.created_at);
    }
}

async function updateProfile(e) {
    e.preventDefault();

    const token = localStorage.getItem('access_token');

    if (!token) {
        window.location.href = 'login.html';
        return;
    }

    const full_name = document.getElementById('full_name')?.value.trim();
    const phone = document.getElementById('phone')?.value.trim();

    if (!full_name || !phone) {
        showNotification('Please fill all fields', 'danger');
        return;
    }

    if (!isValidIndianMobile(phone)) {
        showNotification(
            'Enter a valid 10-digit Indian mobile number starting with 6, 7, 8, or 9.',
            'danger'
        );
        return;
    }

    showLoader();

    try {
        const response = await fetch(`${AUTH_API_URL}/profile`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                Authorization: `Bearer ${token}`
            },
            body: JSON.stringify({
                full_name,
                phone
            })
        });

        const data = await response.json().catch(() => ({}));

        if (response.ok) {
            const user = JSON.parse(
                localStorage.getItem('user') || '{}'
            );

            user.full_name = full_name;
            user.phone = phone;

            localStorage.setItem('user', JSON.stringify(user));

            showNotification('Profile updated successfully', 'success');
            loadProfile();
        } else {
            showNotification(
                data.error || data.message || 'Update failed',
                'danger'
            );
        }
    } catch (error) {
        console.error('Profile update error:', error);
        showNotification('Network error', 'danger');
    } finally {
        hideLoader();
    }
}

// ========== CHANGE PASSWORD ==========
async function changePassword(e) {
    e.preventDefault();

    const token = localStorage.getItem('access_token');

    if (!token) {
        window.location.href = 'login.html';
        return;
    }

    const current_password =
        document.getElementById('current_password')?.value;
    const new_password =
        document.getElementById('new_password')?.value;
    const confirm_password =
        document.getElementById('confirm_password')?.value;

    if (!current_password || !new_password || !confirm_password) {
        showNotification('Please fill all password fields', 'danger');
        return;
    }

    if (new_password !== confirm_password) {
        showNotification('New passwords do not match', 'danger');
        return;
    }

    if (!isPasswordStrong(new_password)) {
        showNotification(
            'Password must be at least 6 characters and include an uppercase letter and a number',
            'danger'
        );
        return;
    }

    showLoader();

    try {
        const response = await fetch(`${AUTH_API_URL}/change-password`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                Authorization: `Bearer ${token}`
            },
            body: JSON.stringify({
                current_password,
                new_password
            })
        });

        const data = await response.json().catch(() => ({}));

        if (response.ok) {
            document.getElementById('current_password').value = '';
            document.getElementById('new_password').value = '';
            document.getElementById('confirm_password').value = '';

            const successModal =
                document.getElementById('passwordSuccessModal');

            if (successModal) {
                openModal('passwordSuccessModal');
            } else {
                showNotification(
                    'Password changed successfully',
                    'success'
                );
            }
        } else {
            showNotification(
                data.error || data.message || 'Password change failed',
                'danger'
            );
        }
    } catch (error) {
        console.error('Password change error:', error);
        showNotification('Network error', 'danger');
    } finally {
        hideLoader();
    }
}

function isPasswordStrong(password) {
    return (
        password.length >= 6 &&
        /[A-Z]/.test(password) &&
        /\d/.test(password)
    );
}

// ========== AUTH GUARD ==========
function requireAuth() {
    const token = localStorage.getItem('access_token');

    if (!token) {
        showNotification('Please login to access this page', 'warning');

        setTimeout(() => {
            window.location.href = 'login.html';
        }, 1500);

        return false;
    }

    return true;
}

// Initialize the profile page.
if (window.location.pathname.includes('profile.html')) {
    document.addEventListener('DOMContentLoaded', () => {
        if (requireAuth()) {
            loadProfile();

            const profileForm = document.getElementById('profileForm');

            if (profileForm) {
                profileForm.addEventListener('submit', updateProfile);
            }

            const passwordForm = document.getElementById('passwordForm');

            if (passwordForm) {
                passwordForm.addEventListener(
                    'submit',
                    changePassword
                );
            }
        }
    });
}

// Check authentication on protected pages.
if (
    window.location.pathname.includes('dashboard.html') ||
    window.location.pathname.includes('profile.html') ||
    window.location.pathname.includes('report-crime.html') ||
    window.location.pathname.includes('my-complaints.html')
) {
    document.addEventListener('DOMContentLoaded', requireAuth);
}