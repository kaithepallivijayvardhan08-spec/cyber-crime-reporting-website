// ========== API CONFIGURATION ==========
const API_BASE = 'http://127.0.0.1:5000/api';

// ========== API CLIENT ==========
class APIClient {
    constructor() {
        this.baseURL = API_BASE;
    }
    
    getHeaders() {
        const token = localStorage.getItem('access_token');
        const headers = {
            'Content-Type': 'application/json'
        };
        
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        
        return headers;
    }
    
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            ...options,
            headers: this.getHeaders()
        };
        
        try {
            const response = await fetch(url, config);
            const data = await response.json();
            
            if (!response.ok) {
                if (response.status === 401) {
                    // Token expired, try to refresh
                    const refreshed = await this.refreshToken();
                    if (refreshed) {
                        // Retry the request with new token
                        config.headers = this.getHeaders();
                        const retryResponse = await fetch(url, config);
                        return await retryResponse.json();
                    } else {
                        window.location.href = '/pages/login.html';
                        throw new Error('Session expired');
                    }
                }
                throw new Error(data.message || 'API request failed');
            }
            
            return data;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }
    
    async refreshToken() {
        const refreshToken = localStorage.getItem('refresh_token');
        if (!refreshToken) return false;
        
        try {
            const response = await fetch(`${this.baseURL}/auth/refresh`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ refresh_token: refreshToken })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                localStorage.setItem('access_token', data.access_token);
                return true;
            }
        } catch (error) {
            console.error('Token refresh failed:', error);
        }
        
        return false;
    }
    
    // ========== AUTH ENDPOINTS ==========
    async register(userData) {
        return this.request('/auth/register', {
            method: 'POST',
            body: JSON.stringify(userData)
        });
    }
    
    async login(credentials) {
        return this.request('/auth/login', {
            method: 'POST',
            body: JSON.stringify(credentials)
        });
    }
    
    async getProfile() {
        return this.request('/auth/profile');
    }
    
    async updateProfile(profileData) {
        return this.request('/auth/profile', {
            method: 'PUT',
            body: JSON.stringify(profileData)
        });
    }
    
    // ========== CRIME REPORTING ENDPOINTS ==========
    async submitComplaint(formData) {
        const token = localStorage.getItem('access_token');
        const url = `${this.baseURL}/crime/report`;
        
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                },
                body: formData
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.message || 'Failed to submit complaint');
            }
            
            return data;
        } catch (error) {
            console.error('Complaint submission error:', error);
            throw error;
        }
    }
    
    async getMyComplaints() {
        return this.request('/crime/my-complaints');
    }
    
    async getComplaintDetails(complaintNumber) {
        return this.request(`/crime/complaint/${complaintNumber}`);
    }
    
    // ========== DASHBOARD ENDPOINTS ==========
    async getDashboardStats() {
        return this.request('/dashboard/stats');
    }
    
    async getRecentComplaints(limit = 5) {
        return this.request(`/dashboard/recent-complaints?limit=${limit}`);
    }
    
    // ========== AI ENDPOINTS ==========
    async analyzeCrime(crimeData) {
        return this.request('/ai/analyze', {
            method: 'POST',
            body: JSON.stringify(crimeData)
        });
    }
    
    async getAIInsights(complaintId) {
        return this.request(`/ai/insights/${complaintId}`);
    }
    
    async getCrimeTrends() {
        return this.request('/ai/trends');
    }
    
    async getCrimeCategories() {
        return this.request('/ai/categories');
    }
    
    // ========== TRACKING ENDPOINTS ==========
    async trackComplaint(complaintNumber) {
        return this.request(`/tracking/track/${complaintNumber}`);
    }
    
    // ========== AWARENESS ARTICLES ==========
    async getArticles(category = null) {
        let url = '/awareness/articles';
        if (category) {
            url += `?category=${category}`;
        }
        return this.request(url);
    }
    
    async getArticleById(articleId) {
        return this.request(`/awareness/article/${articleId}`);
    }
}

// ========== EXPORT API CLIENT ==========
const apiClient = new APIClient();

// ========== HELPER FUNCTIONS ==========
async function fetchWithErrorHandling(apiCall, errorMessage = 'Operation failed') {
    showLoader();
    try {
        const result = await apiCall();
        return result;
    } catch (error) {
        console.error(error);
        showNotification(error.message || errorMessage, 'danger');
        return null;
    } finally {
        hideLoader();
    }
}

// Make available globally
window.apiClient = apiClient;
window.fetchWithErrorHandling = fetchWithErrorHandling;

// ========== INTERCEPTOR FOR AUTH TOKEN ==========
// Auto logout on 401
const originalFetch = window.fetch;
window.fetch = function(...args) {
    return originalFetch.apply(this, args).then(response => {
        if (response.status === 401) {
            const url = args[0];
            if (!url.includes('/auth/refresh') && !url.includes('/auth/login')) {
                localStorage.removeItem('access_token');
                localStorage.removeItem('user');
                if (!window.location.pathname.includes('login.html') &&
                    !window.location.pathname.includes('register.html') &&
                    !window.location.pathname.includes('index.html')) {
                    showNotification('Session expired. Please login again.', 'warning');
                    setTimeout(() => {
                        window.location.href = '/pages/login.html';
                    }, 1500);
                }
            }
        }
        return response;
    });
};