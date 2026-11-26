// ========== COMPLAINT TRACKING MODULE ==========
// Handles complaint tracking, status updates, and timeline visualization

// Global variables
let currentComplaint = null;

// ========== INITIALIZE TRACKING PAGE ==========
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('trackingContainer')) {
        initializeTracking();
    }
    
    if (document.getElementById('myComplaintsContainer')) {
        loadMyComplaints();
    }
});

function initializeTracking() {
    // Get complaint number from URL
    const urlParams = new URLSearchParams(window.location.search);
    const complaintNumber = urlParams.get('number');
    
    if (complaintNumber) {
        trackComplaint(complaintNumber);
    }
    
    // Setup track form
    const trackForm = document.getElementById('trackForm');
    if (trackForm) {
        trackForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const number = document.getElementById('complaintNumber')?.value;
            if (number) {
                trackComplaint(number);
            }
        });
    }
}

// ========== TRACK COMPLAINT ==========
async function trackComplaint(complaintNumber) {
    showLoader();
    
    try {
        const response = await fetch(`${API_BASE_URL}/tracking/track/${complaintNumber}`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            currentComplaint = { ...data.complaint, analysis: data.analysis };
            displayComplaintDetails(currentComplaint);
            displayTrackingTimeline(data.timeline);
            updateURL(complaintNumber);
        } else {
            const error = await response.json();
            showNotFoundError(error.message || 'Complaint not found');
        }
    } catch (error) {
        console.error('Tracking error:', error);
        showNotFoundError('Unable to fetch complaint details. Please try again.');
    } finally {
        hideLoader();
    }
}

function renderSavedAnalysis(analysis) {
    if (!analysis || typeof analysis !== 'object') return '';
    const severity = String(analysis.severity_score || 'Unknown');
    let actions = analysis.suggested_actions;
    if (typeof actions === 'string') {
        try { actions = JSON.parse(actions); } catch { actions = [actions]; }
    }
    if (!Array.isArray(actions)) actions = [];
    const actionItems = actions
        .filter(action => typeof action === 'string' && action.trim())
        .map(action => '<li>' + escapeHTML(action) + '</li>').join('');
    return '<section class="ai-prediction" aria-label="Preliminary complaint analysis">' +
        '<h3><i class="fas fa-robot"></i> Preliminary Analysis</h3><div class="prediction-content">' +
        '<p><strong>Suggested category:</strong> ' + escapeHTML(analysis.crime_category || 'Not available') + '</p>' +
        '<p><strong>Severity:</strong> ' + escapeHTML(severity) + '</p>' +
        '<p><strong>Model confidence:</strong> ' + escapeHTML(analysis.confidence_score ?? 0) + '%</p>' +
        '<p><strong>Estimated resolution:</strong> ' + escapeHTML(analysis.estimated_resolution_time || 'Not estimated') + '</p>' +
        (actionItems ? '<p><strong>Suggested actions for this complaint:</strong></p><ul>' + actionItems + '</ul>' :
         '<p>No recommendations were saved for this complaint.</p>') +
        '<small>Preliminary guidance only; follow official advice for urgent incidents.</small></div></section>';
}

function displayComplaintDetails(complaint) {
    const container = document.getElementById('complaintDetails');
    if (!container) return;
    
    container.innerHTML = `
        <div class="complaint-header">
            <div class="complaint-number">
                <i class="fas fa-hashtag"></i>
                <span>${escapeHTML(complaint.complaint_number)}</span>
            </div>
            <div class="complaint-status">
                <span class="status-badge status-${complaint.status.replace(/_/g, '-')}">
                    ${getStatusText(complaint.status)}
                </span>
            </div>
        </div>
        
        <div class="complaint-info-grid">
            <div class="info-item">
                <label><i class="fas fa-tag"></i> Crime Type</label>
                <p>${escapeHTML(complaint.crime_type)}</p>
            </div>
            <div class="info-item">
                <label><i class="fas fa-calendar"></i> Filed On</label>
                <p>${formatDateTime(complaint.created_at)}</p>
            </div>
            <div class="info-item">
                <label><i class="fas fa-map-marker-alt"></i> Incident Location</label>
                <p>${escapeHTML(complaint.incident_location)}</p>
            </div>
            <div class="info-item">
                <label><i class="fas fa-chart-line"></i> Priority</label>
                <p><span class="priority-badge priority-${complaint.priority || 'medium'}">
                    ${(complaint.priority || 'MEDIUM').toUpperCase()}
                </span></p>
            </div>
        </div>
        
        <div class="complaint-description">
            <label><i class="fas fa-file-alt"></i> Description</label>
            <p>${escapeHTML(complaint.description)}</p>
        </div>
        
        ${renderSavedAnalysis(complaint.analysis)}
    `;
}

function displayTrackingTimeline(timeline) {
    const container = document.getElementById('trackingTimeline');
    if (!container) return;
    
    if (!timeline || timeline.length === 0) {
        container.innerHTML = '<p class="no-timeline">No tracking updates available</p>';
        return;
    }
    
    container.innerHTML = timeline.map((item, index) => `
        <div class="timeline-item ${index === timeline.length - 1 ? 'latest' : ''}">
            <div class="timeline-marker">
                <i class="fas ${getTimelineIcon(item.status)}"></i>
            </div>
            <div class="timeline-content">
                <div class="timeline-header">
                    <span class="timeline-status">${getStatusText(item.status)}</span>
                    <span class="timeline-date">${formatDateTime(item.created_at)}</span>
                </div>
                <div class="timeline-body">
                    <p>${escapeHTML(item.notes || getDefaultNote(item.status))}</p>
                </div>
            </div>
        </div>
    `).join('');
}

function getTimelineIcon(status) {
    const icons = {
        'pending': 'fa-clock',
        'under_review': 'fa-search',
        'investigating': 'fa-microscope',
        'resolved': 'fa-check-circle',
        'rejected': 'fa-times-circle'
    };
    return icons[status] || 'fa-info-circle';
}

function getDefaultNote(status) {
    const notes = {
        'pending': 'Your complaint has been registered and is pending review.',
        'under_review': 'Your complaint is being reviewed by our team.',
        'investigating': 'Investigation is in progress. We will update you soon.',
        'resolved': 'Your complaint has been resolved successfully.',
        'rejected': 'Your complaint has been rejected due to insufficient evidence.'
    };
    return notes[status] || 'Status updated';
}

function updateURL(complaintNumber) {
    const url = new URL(window.location);
    url.searchParams.set('number', complaintNumber);
    window.history.pushState({}, '', url);
}

function showNotFoundError(message) {
    const container = document.getElementById('trackingContainer');
    if (container) {
        container.innerHTML = `
            <div class="error-state">
                <i class="fas fa-search"></i>
                <h3>Complaint Not Found</h3>
                <p>${message}</p>
                <button class="btn btn-primary" onclick="location.reload()">Try Again</button>
            </div>
        `;
    }
}

// ========== MY COMPLAINTS LIST ==========
async function loadMyComplaints(page = 1, status = 'all') {
    showLoader();
    
    try {
        let url = `${API_BASE_URL}/crime/my-complaints?page=${page}&limit=10`;
        if (status !== 'all') {
            url += `&status=${status}`;
        }
        
        const response = await fetch(url, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            displayMyComplaints(data.complaints, data.pagination);
        } else {
            showNoComplaints();
        }
    } catch (error) {
        console.error('Load complaints error:', error);
        showNoComplaints();
    } finally {
        hideLoader();
    }
}

function displayMyComplaints(complaints, pagination) {
    const container = document.getElementById('myComplaintsContainer');
    if (!container) return;
    
    if (!complaints || complaints.length === 0) {
        showNoComplaints();
        return;
    }
    
    container.innerHTML = `
        <div class="complaints-list">
            ${complaints.map(complaint => `
                <div class="complaint-card">
                    <div class="complaint-card-header">
                        <div>
                            <span class="complaint-id">${escapeHTML(complaint.complaint_number)}</span>
                            <span class="complaint-type">${escapeHTML(complaint.crime_type)}</span>
                        </div>
                        <span class="status-badge status-${complaint.status.replace(/_/g, '-')}">
                            ${getStatusText(complaint.status)}
                        </span>
                    </div>
                    <div class="complaint-card-body">
                        <p>${escapeHTML((complaint.description || '').substring(0, 100))}${complaint.description && complaint.description.length > 100 ? '...' : ''}</p>
                        <div class="complaint-meta">
                            <span><i class="fas fa-calendar"></i> ${formatDate(complaint.created_at)}</span>
                            <span><i class="fas fa-chart-line"></i> Priority: ${(complaint.priority || 'Medium').toUpperCase()}</span>
                        </div>
                    </div>
                    <div class="complaint-card-footer">
                        <button class="btn btn-sm btn-view" type="button" data-complaint-action="view" data-complaint-number="${escapeHTML(complaint.complaint_number)}">
                            View Details
                        </button>
                        <button class="btn btn-sm btn-track" type="button" data-complaint-action="track" data-complaint-number="${escapeHTML(complaint.complaint_number)}">
                            Track Status
                        </button>
                    </div>
                </div>
            `).join('')}
        </div>
        ${pagination && pagination.total_pages > 1 ? createPagination(pagination) : ''}
    `;

    container.querySelectorAll('[data-complaint-action]').forEach(button => {
        button.addEventListener('click', () => {
            const action = button.dataset.complaintAction === 'view' ? viewComplaint : trackFromList;
            action(button.dataset.complaintNumber);
        });
    });
}

function createPagination(pagination) {
    return `
        <div class="pagination">
            <button onclick="loadMyComplaints(${pagination.current_page - 1})" ${pagination.current_page === 1 ? 'disabled' : ''}>
                Previous
            </button>
            <span>Page ${pagination.current_page} of ${pagination.total_pages}</span>
            <button onclick="loadMyComplaints(${pagination.current_page + 1})" ${pagination.current_page === pagination.total_pages ? 'disabled' : ''}>
                Next
            </button>
        </div>
    `;
}

function showNoComplaints() {
    const container = document.getElementById('myComplaintsContainer');
    if (container) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-file-alt"></i>
                <h3>No Complaints Found</h3>
                <p>You haven't filed any complaints yet.</p>
                <a href="report-crime.html" class="btn btn-primary">File Your First Complaint</a>
            </div>
        `;
    }
}

// ========== FILTER COMPLAINTS ==========
function setupComplaintFilters() {
    const filterSelect = document.getElementById('statusFilter');
    if (filterSelect) {
        filterSelect.addEventListener('change', (e) => {
            loadMyComplaints(1, e.target.value);
        });
    }
}

// ========== COMPLAINT ACTIONS ==========
function viewComplaint(complaintNumber) {
    window.location.href = `track-complaint.html?number=${encodeURIComponent(complaintNumber)}`;
}

function trackFromList(complaintNumber) {
    window.location.href = `track-complaint.html?number=${encodeURIComponent(complaintNumber)}`;
}

// Export functions
window.trackComplaint = trackComplaint;
window.viewComplaint = viewComplaint;
window.trackFromList = trackFromList;
window.loadMyComplaints = loadMyComplaints;

// Initialize filters when on my-complaints page
if (window.location.pathname.includes('my-complaints.html')) {
    document.addEventListener('DOMContentLoaded', setupComplaintFilters);
}

