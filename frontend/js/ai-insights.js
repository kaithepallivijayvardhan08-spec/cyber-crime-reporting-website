// ========== AI INSIGHTS MODULE ==========
// Displays complaint trends and analysis returned by the backend.

let currentPage = 1;
let totalPages = 1;
let trendsChartInstance = null;
let categoriesChartInstance = null;

document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('aiInsightsContainer')) {
        setupFilters();
        loadAllInsights();
    }
});

async function loadAllInsights() {
    showLoader();

    try {
        await Promise.all([
            loadCrimeTrends(),
            loadCrimeCategories(),
            loadPredictiveAnalysis(),
            loadRecentAIAnalysis()
        ]);
    } catch (error) {
        console.error('AI Insights load error:', error);
        showNotification('Failed to load AI insights', 'danger');
    } finally {
        hideLoader();
    }
}

// ========== CRIME TRENDS ==========
async function loadCrimeTrends() {
    try {
        const response = await fetch(`${API_BASE_URL}/ai/trends`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });

        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
            throw new Error(data.error || 'Trend data is unavailable');
        }

        displayCrimeTrends(data.trends);
        initializeTrendsChart(data.trends);
    } catch (error) {
        console.error('Trends load error:', error);
        displayCrimeTrends(null);
        initializeTrendsChart(null);
    }
}

function displayCrimeTrends(trends) {
    const container = document.getElementById('trendsContainer');
    if (!container) return;

    const monthlyValues = trends?.monthly_data?.values || [];

    if (!trends || monthlyValues.length === 0) {
        container.innerHTML =
            '<p class="no-data">No complaint trend data is available yet.</p>';
        return;
    }

    container.innerHTML = `
        <div class="trends-summary">
            <div class="trend-stat">
                <i class="fas fa-chart-line"></i>
                <div>
                    <h4>${escapeHTML(trends.overall_trend || 'Not enough data')}</h4>
                    <p>Observed Trend</p>
                </div>
            </div>
            <div class="trend-stat">
                <i class="fas fa-shield-alt"></i>
                <div>
                    <h4>${escapeHTML(trends.most_common_crime || 'Not enough data')}</h4>
                    <p>Most Reported Crime</p>
                </div>
            </div>
        </div>
        <p class="prediction-notice">
            This summarizes stored complaints. It is not a verified forecast.
        </p>
    `;
}

function initializeTrendsChart(trends) {
    const canvas = document.getElementById('trendsChart');
    if (!canvas) return;

    if (trendsChartInstance) {
        trendsChartInstance.destroy();
        trendsChartInstance = null;
    }

    const labels = trends?.monthly_data?.labels || [];
    const values = trends?.monthly_data?.values || [];

    trendsChartInstance = new Chart(canvas.getContext('2d'), {
        type: 'line',
        data: {
            labels,
            datasets: [{
                label: 'Stored Complaint Reports',
                data: values,
                borderColor: '#2c7da0',
                backgroundColor: 'rgba(44, 125, 160, 0.12)',
                borderWidth: 3,
                fill: true,
                tension: 0.3,
                pointBackgroundColor: '#2c7da0',
                pointBorderColor: '#ffffff',
                pointBorderWidth: 2,
                pointRadius: 5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'top' },
                tooltip: {
                    callbacks: {
                        label: context => `Reports: ${context.raw}`
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Number of Stored Reports'
                    }
                }
            }
        }
    });
}

// ========== CRIME CATEGORY COUNTS ==========
async function loadCrimeCategories() {
    try {
        const response = await fetch(`${API_BASE_URL}/ai/categories`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });

        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
            throw new Error(data.error || 'Category data is unavailable');
        }

        const categories = Array.isArray(data.categories)
            ? data.categories
            : [];

        displayCategoriesChart(categories);
        displayCategoriesList(categories);
    } catch (error) {
        console.error('Categories load error:', error);
        displayCategoriesChart([]);
        displayCategoriesList([]);
    }
}

function displayCategoriesChart(categories) {
    const canvas = document.getElementById('categoriesChart');
    if (!canvas) return;

    if (categoriesChartInstance) {
        categoriesChartInstance.destroy();
        categoriesChartInstance = null;
    }

    const labels = categories.map(category => category.name);
    const values = categories.map(category => Number(category.count) || 0);

    categoriesChartInstance = new Chart(canvas.getContext('2d'), {
        type: 'doughnut',
        data: {
            labels,
            datasets: [{
                data: values,
                backgroundColor: generateColors(labels.length),
                borderWidth: 2,
                borderColor: '#ffffff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: { font: { size: 11 } }
                },
                tooltip: {
                    callbacks: {
                        label(context) {
                            const total = context.dataset.data.reduce(
                                (sum, value) => sum + value,
                                0
                            );
                            const value = Number(context.parsed) || 0;
                            const percentage = total
                                ? ((value / total) * 100).toFixed(1)
                                : '0.0';

                            return `${context.label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

function displayCategoriesList(categories) {
    const container = document.getElementById('categoriesList');
    if (!container) return;

    if (!categories || categories.length === 0) {
        container.innerHTML =
            '<p class="no-data">No complaint category data is available yet.</p>';
        return;
    }

    const total = categories.reduce(
        (sum, category) => sum + (Number(category.count) || 0),
        0
    );

    container.innerHTML = categories.map(category => {
        const count = Number(category.count) || 0;
        const percentage = total ? (count / total) * 100 : 0;

        return `
            <div class="category-item">
                <div class="category-name">
                    <i class="fas fa-shield-alt"></i>
                    <span>${escapeHTML(category.name)}</span>
                </div>
                <div class="category-stats">
                    <div class="category-bar">
                        <div
                            class="category-bar-fill"
                            style="width: ${percentage}%"
                        ></div>
                    </div>
                    <span class="category-count">${count}</span>
                </div>
            </div>
        `;
    }).join('');
}

// ========== DASHBOARD SUMMARY ==========
async function loadPredictiveAnalysis() {
    try {
        const response = await fetch(`${API_BASE_URL}/ai/predictions`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });

        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
            throw new Error(data.error || 'Dashboard summary is unavailable');
        }

        displayPredictions(data.predictions);
    } catch (error) {
        console.error('Dashboard summary load error:', error);
        displayPredictions(null);
    }
}

function displayPredictions(predictions) {
    const container = document.getElementById('predictionsContainer');
    if (!container) return;

    if (!predictions) {
        container.innerHTML =
            '<p class="no-data">Dashboard summary is unavailable.</p>';
        return;
    }

    const concerns = Array.isArray(predictions.emerging_threats)
        ? predictions.emerging_threats
        : [];

    container.innerHTML = `
        <div class="prediction-card risk-high">
            <i class="fas fa-exclamation-triangle"></i>
            <div>
                <h4>Top Reported Risk</h4>
                <p>${escapeHTML(predictions.high_risk_areas || 'Not enough data')}</p>
            </div>
        </div>
        <div class="prediction-card risk-medium">
            <i class="fas fa-chart-line"></i>
            <div>
                <h4>Observed Trend</h4>
                <p>${escapeHTML(predictions.expected_increase || 'Not enough data')}</p>
            </div>
        </div>
        <div class="prediction-card risk-low">
            <i class="fas fa-lightbulb"></i>
            <div>
                <h4>Suggested Action</h4>
                <p>${escapeHTML(predictions.recommendation || 'No suggestion available')}</p>
            </div>
        </div>
        ${
            concerns.length
                ? `<div class="prediction-card">
                    <i class="fas fa-list"></i>
                    <div>
                        <h4>Concerns to Review</h4>
                        <ul>
                            ${concerns.map(item =>
                                `<li>${escapeHTML(String(item))}</li>`
                            ).join('')}
                        </ul>
                    </div>
                </div>`
                : ''
        }
        <p class="prediction-notice">
            Source: ${escapeHTML(predictions.analysis_source || 'Database summary')}.
            ${escapeHTML(
                predictions.notice ||
                'This is a summary of stored complaint data, not a validated future forecast.'
            )}
        </p>
    `;
}

// ========== RECENT AI ANALYSIS ==========
async function loadRecentAIAnalysis(page = 1) {
    try {
        const response = await fetch(
            `${API_BASE_URL}/ai/recent-analysis?page=${page}&limit=10`,
            {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            }
        );

        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
            throw new Error(data.error || 'Recent analysis is unavailable');
        }

        displayRecentAnalysis(data.analysis, data.pagination);
    } catch (error) {
        console.error('Recent analysis load error:', error);
        displayRecentAnalysis([]);
    }
}

function displayRecentAnalysis(analysis, pagination) {
    const container = document.getElementById('recentAnalysisContainer');
    if (!container) return;

    if (!analysis || analysis.length === 0) {
        container.innerHTML =
            '<p class="no-data">No saved complaint analyses are available.</p>';
        return;
    }

    container.innerHTML = analysis.map(item => `
        <div class="analysis-card">
            <div class="analysis-header">
                <span class="complaint-number">
                    ${escapeHTML(item.complaint_number || '')}
                </span>
                <span class="severity severity-${String(
                    item.severity || 'medium'
                ).toLowerCase()}">
                    ${escapeHTML(item.severity || 'Unknown')} Priority
                </span>
            </div>
            <div class="analysis-body">
                <p><strong>Crime Type:</strong> ${escapeHTML(item.crime_type || '')}</p>
                <p><strong>Model Confidence:</strong> ${
                    escapeHTML(String(item.confidence ?? 'N/A'))
                }%</p>
                <p><strong>Analysis:</strong> ${
                    escapeHTML(item.analysis_summary || 'No summary saved')
                }</p>
            </div>
            <div class="analysis-footer">
                <button
                    class="btn btn-sm"
                    type="button"
                    data-complaint-number="${escapeHTML(item.complaint_number || '')}"
                >
                    View Details
                </button>
            </div>
        </div>
    `).join('');

    container.querySelectorAll('[data-complaint-number]').forEach(button => {
        button.addEventListener('click', () => {
            viewComplaintDetails(button.dataset.complaintNumber);
        });
    });

    if (pagination && pagination.total_pages > 1) {
        displayPagination(pagination);
    }
}

function displayPagination(pagination) {
    const container = document.getElementById('analysisPagination');
    if (!container) return;

    currentPage = pagination.current_page;
    totalPages = pagination.total_pages;

    container.innerHTML = '';

    const paginationDiv = document.createElement('div');
    paginationDiv.className = 'pagination';

    if (currentPage > 1) {
        const previous = document.createElement('button');
        previous.type = 'button';
        previous.textContent = 'Previous';
        previous.addEventListener('click', () => {
            loadRecentAIAnalysis(currentPage - 1);
        });
        paginationDiv.appendChild(previous);
    }

    for (let page = 1; page <= totalPages && page <= 5; page++) {
        const button = document.createElement('button');
        button.type = 'button';
        button.textContent = String(page);
        button.className = page === currentPage ? 'active' : '';
        button.addEventListener('click', () => loadRecentAIAnalysis(page));
        paginationDiv.appendChild(button);
    }

    if (currentPage < totalPages) {
        const next = document.createElement('button');
        next.type = 'button';
        next.textContent = 'Next';
        next.addEventListener('click', () => {
            loadRecentAIAnalysis(currentPage + 1);
        });
        paginationDiv.appendChild(next);
    }

    container.appendChild(paginationDiv);
}

// ========== FILTERS ==========
function setupFilters() {
    const filterSelect = document.getElementById('crimeTypeFilter');
    const dateFilter = document.getElementById('dateFilter');

    if (filterSelect) {
        filterSelect.addEventListener('change', applyFilters);
    }

    if (dateFilter) {
        dateFilter.addEventListener('change', applyFilters);
    }
}

function applyFilters() {
    // The current backend endpoint supports pagination only.
    // Reload the first page when a filter changes.
    loadRecentAIAnalysis(1);
}

// ========== UTILITY FUNCTIONS ==========
function generateColors(count) {
    const colors = [
        '#2c7da0', '#61a5c2', '#2a9d8f', '#e9c46a', '#e63946',
        '#9b5de5', '#f15bb5', '#fee440', '#00bbf9', '#00f5d4'
    ];

    const result = [];
    for (let i = 0; i < count; i++) {
        result.push(colors[i % colors.length]);
    }
    return result;
}

function viewComplaintDetails(complaintNumber) {
    window.location.href =
        `track-complaint.html?number=${encodeURIComponent(complaintNumber)}`;
}

// Export functions
window.loadRecentAIAnalysis = loadRecentAIAnalysis;
window.viewComplaintDetails = viewComplaintDetails;