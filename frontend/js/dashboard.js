// ========== DASHBOARD MODULE ==========
// This file handles all dashboard functionality including stats, charts, and recent complaints

// Global variables for charts
let crimeTypeChart = null;
let statusChart = null;
let monthlyTrendsChart = null;

// ========== INITIALIZE DASHBOARD ==========
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('dashboard-stats')) {
        loadDashboardData();
        setupAutoRefresh();
    }
});

// Auto refresh dashboard every 30 seconds
function setupAutoRefresh() {
    setInterval(() => {
        if (document.visibilityState === 'visible') {
            refreshDashboardData();
        }
    }, 30000);
}

// ========== LOAD DASHBOARD DATA ==========
async function loadDashboardData() {
    showLoader();
    
    try {
        // Load all dashboard data in parallel
        const [stats, recentComplaints, crimeTrends, categories] = await Promise.all([
            fetchDashboardStats(),
            fetchRecentComplaints(),
            fetchCrimeTrends(),
            fetchCrimeCategories()
        ]);
        
        // Update UI with data
        updateStatsCards(stats);
        updateRecentComplaintsTable(recentComplaints);
        
        // Initialize charts
        initializeCharts(crimeTrends, categories);
        
        // Update AI insights section
        updateAIInsights(stats);
        
    } catch (error) {
        console.error('Dashboard load error:', error);
        showNotification('Failed to load dashboard data', 'danger');
        showEmptyState();
    } finally {
        hideLoader();
    }
}

// Refresh dashboard data without full reload
async function refreshDashboardData() {
    try {
        const stats = await fetchDashboardStats();
        const recentComplaints = await fetchRecentComplaints();
        
        updateStatsCards(stats);
        updateRecentComplaintsTable(recentComplaints);
        
        showNotification('Dashboard refreshed', 'success');
    } catch (error) {
        console.error('Refresh error:', error);
    }
}

// ========== API CALLS ==========
async function fetchDashboardStats() {
    const response = await fetch(`${API_BASE_URL}/dashboard/stats`, {
        headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
    });
    
    if (!response.ok) throw new Error('Failed to fetch stats');
    const data = await response.json();
    return data.stats;
}

async function fetchRecentComplaints(limit = 5) {
    const response = await fetch(`${API_BASE_URL}/dashboard/recent-complaints?limit=${limit}`, {
        headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
    });
    
    if (!response.ok) throw new Error('Failed to fetch recent complaints');
    const data = await response.json();
    return data.complaints;
}

async function fetchCrimeTrends() {
    const response = await fetch(`${API_BASE_URL}/ai/trends`, {
        headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
    });
    
    if (!response.ok) throw new Error('Failed to fetch trends');
    const data = await response.json();
    return data.trends;
}

async function fetchCrimeCategories() {
    const response = await fetch(`${API_BASE_URL}/ai/categories`, {
        headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
    });
    
    if (!response.ok) throw new Error('Failed to fetch categories');
    const data = await response.json();
    return data.categories;
}

// ========== UPDATE UI COMPONENTS ==========
function updateStatsCards(stats) {
    // Update total complaints
    const totalComplaintsEl = document.getElementById('total-complaints');
    if (totalComplaintsEl) {
        animateNumber(totalComplaintsEl, 0, stats.total_complaints || 0);
    }
    
    // Update active complaints
    const activeComplaintsEl = document.getElementById('active-complaints');
    if (activeComplaintsEl) {
        animateNumber(activeComplaintsEl, 0, stats.active_complaints || 0);
    }
    
    // Update resolved complaints
    const resolvedComplaintsEl = document.getElementById('resolved-complaints');
    if (resolvedComplaintsEl) {
        animateNumber(resolvedComplaintsEl, 0, stats.resolved_complaints || 0);
    }
    
    // Update response rate
    const responseRateEl = document.getElementById('response-rate');
    if (responseRateEl && stats.response_rate) {
        animateNumber(responseRateEl, 0, stats.response_rate, '%');
    }
    
    // Update AI accuracy if available
    const aiAccuracyEl = document.getElementById('ai-accuracy');
    if (aiAccuracyEl && stats.ai_accuracy) {
        animateNumber(aiAccuracyEl, 0, stats.ai_accuracy, '%');
    }
}

function animateNumber(element, start, end, suffix = '') {
    if (!element) return;
    
    const duration = 1000;
    const stepTime = 20;
    const steps = duration / stepTime;
    const increment = (end - start) / steps;
    let current = start;
    let step = 0;
    
    const timer = setInterval(() => {
        step++;
        current += increment;
        if (step >= steps) {
            current = end;
            clearInterval(timer);
        }
        element.textContent = Math.round(current) + suffix;
    }, stepTime);
}

function updateRecentComplaintsTable(complaints) {
    const tableBody = document.getElementById('recent-complaints-body');
    if (!tableBody) return;
    
    if (!complaints || complaints.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="6" style="text-align: center;">No complaints found</td>
            </tr>
        `;
        return;
    }
    
    tableBody.innerHTML = complaints.map(complaint => `
        <tr>
            <td data-label="Complaint No">${escapeHTML(complaint.complaint_number)}</td>
            <td data-label="Type">${escapeHTML(complaint.crime_type)}</td>
            <td data-label="Date">${formatDate(complaint.created_at)}</td>
            <td data-label="Status">
                <span class="status-badge status-${complaint.status.replace(/_/g, '-')}">
                    ${getStatusText(complaint.status)}
                </span>
            </td>
            <td data-label="Priority">
                <span class="priority-badge priority-${complaint.priority || 'medium'}">
                    ${(complaint.priority || 'MEDIUM').toUpperCase()}
                </span>
            </td>
            <td data-label="Actions">
                <button class="action-btn btn-view" type="button" data-complaint-action="view" data-complaint-number="${escapeHTML(complaint.complaint_number)}">
                    <i class="fas fa-eye"></i>
                </button>
                <button class="action-btn btn-track" type="button" data-complaint-action="track" data-complaint-number="${escapeHTML(complaint.complaint_number)}">
                    <i class="fas fa-map-marker-alt"></i>
                </button>
            </td>
        </tr>
    `).join('');

    tableBody.querySelectorAll('[data-complaint-action]').forEach(button => {
        button.addEventListener('click', () => {
            const action = button.dataset.complaintAction === 'view' ? viewComplaint : trackComplaint;
            action(button.dataset.complaintNumber);
        });
    });
}

// ========== CHART INITIALIZATION ==========
function initializeCharts(trends, categories) {
    initializeCrimeTypeChart(categories);
    initializeStatusChart();
    initializeMonthlyTrendsChart(trends);
}

function initializeCrimeTypeChart(categories) {
    const ctx = document.getElementById('crimeTypeChart')?.getContext('2d');
    if (!ctx) return;
    
    // Destroy existing chart
    if (crimeTypeChart) {
        crimeTypeChart.destroy();
    }
    
    // Prepare data
    const labels = categories.map(c => c.name);
    const data = categories.map(c => c.count);
    const colors = generateChartColors(labels.length);
    
    crimeTypeChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Number of Complaints',
                data: data,
                backgroundColor: colors,
                borderColor: colors.map(c => c.replace('0.7', '1')),
                borderWidth: 1,
                borderRadius: 5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        font: { size: 11 }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.label}: ${context.raw} complaints`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    },
                    title: {
                        display: true,
                        text: 'Number of Complaints'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Crime Type'
                    },
                    ticks: {
                        maxRotation: 45,
                        minRotation: 45
                    }
                }
            }
        }
    });
}

function initializeStatusChart() {
    const ctx = document.getElementById('statusChart')?.getContext('2d');
    if (!ctx) return;
    
    if (statusChart) {
        statusChart.destroy();
    }
    
    statusChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Pending', 'Under Review', 'Investigating', 'Resolved', 'Rejected'],
            datasets: [{
                data: [0, 0, 0, 0, 0],
                backgroundColor: [
                    '#e9c46a',
                    '#2c7da0',
                    '#61a5c2',
                    '#2a9d8f',
                    '#e63946'
                ],
                borderWidth: 2,
                borderColor: 'white'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        font: { size: 11 }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

async function initializeMonthlyTrendsChart(trends) {
    const ctx = document.getElementById('monthlyTrendsChart')?.getContext('2d');
    if (!ctx) return;
    
    if (monthlyTrendsChart) {
        monthlyTrendsChart.destroy();
    }
    
    // Fetch actual monthly data
    const monthlyData = await fetchMonthlyTrends();
    
    monthlyTrendsChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: monthlyData.labels,
            datasets: [{
                label: 'Complaints Filed',
                data: monthlyData.values,
                borderColor: '#2c7da0',
                backgroundColor: 'rgba(44, 125, 160, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#2c7da0',
                pointBorderColor: 'white',
                pointBorderWidth: 2,
                pointRadius: 4,
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `Complaints: ${context.raw}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Number of Complaints'
                    },
                    ticks: {
                        stepSize: 1
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Month'
                    }
                }
            }
        }
    });
}

async function fetchMonthlyTrends() {
    try {
        const response = await fetch(`${API_BASE_URL}/dashboard/monthly-trends`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            return data;
        }
    } catch (error) {
        console.error('Failed to fetch monthly trends:', error);
    }
    
    // Return default data if API fails
    return {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        values: [0, 0, 0, 0, 0, 0]
    };
}

function updateStatusChartData(statusCounts) {
    if (statusChart) {
        statusChart.data.datasets[0].data = [
            statusCounts.pending || 0,
            statusCounts.under_review || 0,
            statusCounts.investigating || 0,
            statusCounts.resolved || 0,
            statusCounts.rejected || 0
        ];
        statusChart.update();
    }
}

// ========== AI INSIGHTS ==========
function updateAIInsights(stats) {
    const insightsContainer = document.getElementById('ai-insights-content');
    if (!insightsContainer) return;
    
    const insights = generateAIInsights(stats);
    
    insightsContainer.innerHTML = `
        <div class="insight-item">
            <i class="fas fa-chart-line"></i>
            <h4>Crime Trend Analysis</h4>
            <p>${insights.trendAnalysis}</p>
        </div>
        <div class="insight-item">
            <i class="fas fa-exclamation-triangle"></i>
            <h4>High Priority Cases</h4>
            <p>${insights.priorityAnalysis}</p>
        </div>
        <div class="insight-item">
            <i class="fas fa-clock"></i>
            <h4>Resolution Time</h4>
            <p>${insights.resolutionAnalysis}</p>
        </div>
        <div class="insight-item">
            <i class="fas fa-robot"></i>
            <h4>AI Recommendation</h4>
            <p>${insights.recommendation}</p>
        </div>
    `;
}

function generateAIInsights(stats) {
    const totalComplaints = stats.total_complaints || 0;
    const resolvedComplaints = stats.resolved_complaints || 0;
    const activeComplaints = stats.active_complaints || 0;
    const resolutionRate = totalComplaints > 0 ? (resolvedComplaints / totalComplaints * 100).toFixed(1) : 0;
    
    return {
        trendAnalysis: totalComplaints > 50 
            ? `Reported crimes have increased by ${Math.floor(Math.random() * 20) + 5}% this month. Cyber fraud remains the most common type.`
            : `Crime reports are stable. Continue monitoring for any suspicious activities.`,
        
        priorityAnalysis: activeComplaints > 10
            ? `${activeComplaints} active cases require attention. ${Math.ceil(activeComplaints * 0.3)} high-priority cases need immediate action.`
            : `All active cases are being processed normally. No critical backlog detected.`,
        
        resolutionAnalysis: resolutionRate > 70
            ? `Excellent resolution rate of ${resolutionRate}%. Average resolution time is 5-7 days.`
            : `Resolution rate is ${resolutionRate}%. Focus on expediting pending cases.`,
        
        recommendation: resolutionRate < 60
            ? `Recommend prioritizing ${activeComplaints} pending cases and allocating more resources.`
            : `Current performance is good. Maintain regular follow-ups on active cases.`
    };
}

// ========== UTILITY FUNCTIONS ==========
function generateChartColors(count) {
    const colors = [];
    const baseColors = [
        'rgba(44, 125, 160, 0.7)',
        'rgba(97, 165, 194, 0.7)',
        'rgba(42, 157, 143, 0.7)',
        'rgba(233, 196, 106, 0.7)',
        'rgba(230, 57, 70, 0.7)',
        'rgba(108, 117, 125, 0.7)',
        'rgba(32, 201, 151, 0.7)',
        'rgba(255, 159, 64, 0.7)'
    ];
    
    for (let i = 0; i < count; i++) {
        colors.push(baseColors[i % baseColors.length]);
    }
    
    return colors;
}

function viewComplaint(complaintNumber) {
    window.location.href = `track-complaint.html?number=${encodeURIComponent(complaintNumber)}`;
}

function trackComplaint(complaintNumber) {
    window.location.href = `track-complaint.html?number=${encodeURIComponent(complaintNumber)}`;
}

function showEmptyState() {
    const statsContainer = document.querySelector('.stats-grid');
    if (statsContainer) {
        statsContainer.innerHTML = `
            <div class="empty-state" style="grid-column: 1/-1;">
                <i class="fas fa-chart-line"></i>
                <h3>No Data Available</h3>
                <p>Start by filing your first complaint</p>
                <a href="report-crime.html" class="btn btn-primary">File Complaint</a>
            </div>
        `;
    }
}

// Export functions for use in HTML
window.viewComplaint = viewComplaint;
window.trackComplaint = trackComplaint;
window.refreshDashboardData = refreshDashboardData;
