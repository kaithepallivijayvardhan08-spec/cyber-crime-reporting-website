// ========== CRIME REPORTING MODULE ==========
// Handles crime report submission, file uploads, form validation,
// AI analysis, and dynamic safety tips.

let uploadedFiles = [];
let aiAnalysisResult = null;

// ========== INITIALIZE CRIME REPORT FORM ==========
document.addEventListener('DOMContentLoaded', () => {
    const reportForm = document.getElementById('crimeReportForm');

    if (reportForm) {
        initializeForm();
        setupFormListeners();
        loadCrimeCategories();
    }
});

function initializeForm() {
    // Set default date to today.
    const incidentDateInput = document.getElementById('incident_date');

    if (incidentDateInput) {
        incidentDateInput.max = new Date().toISOString().split('T')[0];
        incidentDateInput.value = new Date().toISOString().split('T')[0];
    }

    initializeFileUpload();

    // Initialize the AI analysis button.
    const analyzeBtn = document.getElementById('analyzeWithAI');

    if (analyzeBtn) {
        analyzeBtn.addEventListener('click', performAIAnalysis);
    }
}

function setupFormListeners() {
    const form = document.getElementById('crimeReportForm');

    if (form) {
        form.addEventListener('submit', submitCrimeReport);
    }

    // Real-time validation.
    const inputs = [
        'crime_type',
        'description',
        'incident_date',
        'incident_location'
    ];

    inputs.forEach((inputId) => {
        const input = document.getElementById(inputId);

        if (input) {
            input.addEventListener('blur', () => validateField(inputId));
            input.addEventListener('input', () => clearFieldError(inputId));
        }
    });
}

// ========== LOAD CRIME CATEGORIES ==========
async function loadCrimeCategories() {
    const categorySelect = document.getElementById('crime_type');

    if (!categorySelect) return;

    try {
        const response = await fetch(`${API_BASE_URL}/ai/categories`, {
            headers: {
                Authorization: `Bearer ${localStorage.getItem('access_token') || ''}`
            }
        });

        if (!response.ok) {
            populateDefaultCategories();
            return;
        }

        const data = await response.json();
        populateCategories(data.categories || []);
    } catch (error) {
        console.error('Failed to load categories:', error);
        populateDefaultCategories();
    }
}

function populateCategories(categories) {
    const categorySelect = document.getElementById('crime_type');

    if (!categorySelect) return;

    categorySelect.innerHTML =
        '<option value="">Select Crime Type</option>';

    categories.forEach((category) => {
        const option = document.createElement('option');
        option.value = category.name;
        option.textContent = category.name;
        categorySelect.appendChild(option);
    });
}

function populateDefaultCategories() {
    const categories = [
        'Phishing Attack',
        'Identity Theft',
        'Online Fraud',
        'Cyber Bullying',
        'Data Breach',
        'Ransomware Attack',
        'Credit Card Fraud',
        'Social Media Hacking',
        'Online Scam',
        'Other Cyber Crime'
    ];

    const categorySelect = document.getElementById('crime_type');

    if (!categorySelect) return;

    categorySelect.innerHTML =
        '<option value="">Select Crime Type</option>';

    categories.forEach((category) => {
        const option = document.createElement('option');
        option.value = category;
        option.textContent = category;
        categorySelect.appendChild(option);
    });
}

// ========== FILE UPLOAD HANDLING ==========
function initializeFileUpload() {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('evidence_files');

    if (!dropZone || !fileInput) return;

    dropZone.addEventListener('click', () => fileInput.click());

    dropZone.addEventListener('dragover', (event) => {
        event.preventDefault();
        dropZone.classList.add('drag-over');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('drag-over');
    });

    dropZone.addEventListener('drop', (event) => {
        event.preventDefault();
        dropZone.classList.remove('drag-over');
        handleFiles(Array.from(event.dataTransfer.files));
    });

    fileInput.addEventListener('change', (event) => {
        handleFiles(Array.from(event.target.files));
    });
}

function handleFiles(files) {
    const maxSize = 16 * 1024 * 1024;
    const allowedTypes = [
        'image/jpeg',
        'image/png',
        'application/pdf',
        'text/plain'
    ];

    for (const file of files) {
        if (file.size > maxSize) {
            showNotification(`${file.name} exceeds 16MB limit`, 'danger');
            continue;
        }

        const currentUploadSize = uploadedFiles.reduce(
            (total, uploadedFile) => total + uploadedFile.size,
            0
        );

        if (currentUploadSize + file.size > maxSize) {
            showNotification(
                'Combined evidence files exceed the 16MB upload limit',
                'danger'
            );
            continue;
        }

        if (!allowedTypes.includes(file.type)) {
            showNotification(`${file.name} is not an allowed file type`, 'danger');
            continue;
        }

        const duplicate = uploadedFiles.some(
            (existingFile) =>
                existingFile.name === file.name &&
                existingFile.size === file.size
        );

        if (duplicate) {
            showNotification(`${file.name} already added`, 'warning');
            continue;
        }

        uploadedFiles.push(file);
    }

    updateFileList();
    updateFileInput();
}

function updateFileList() {
    const fileListContainer = document.getElementById('fileList');

    if (!fileListContainer) return;

    if (uploadedFiles.length === 0) {
        fileListContainer.innerHTML = '';
        return;
    }

    fileListContainer.innerHTML = uploadedFiles
        .map(
            (file, index) => `
                <div class="file-item">
                    <div class="file-info">
                        <i class="fas ${getFileIcon(file.type)}"></i>
                        <span class="file-name">${escapeHTML(file.name)}</span>
                        <span class="file-size">(${formatFileSize(file.size)})</span>
                    </div>
                    <button
                        type="button"
                        class="remove-file"
                        onclick="removeFile(${index})"
                        aria-label="Remove ${escapeHTML(file.name)}"
                    >
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            `
        )
        .join('');
}

function updateFileInput() {
    const fileInput = document.getElementById('evidence_files');

    if (!fileInput) return;

    const dataTransfer = new DataTransfer();
    uploadedFiles.forEach((file) => dataTransfer.items.add(file));
    fileInput.files = dataTransfer.files;
}

function removeFile(index) {
    uploadedFiles.splice(index, 1);
    updateFileList();
    updateFileInput();
}

function getFileIcon(fileType) {
    if (fileType.startsWith('image/')) return 'fa-image';
    if (fileType === 'application/pdf') return 'fa-file-pdf';
    if (fileType === 'text/plain') return 'fa-file-alt';
    return 'fa-file';
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';

    const units = ['Bytes', 'KB', 'MB', 'GB'];
    const unitIndex = Math.floor(Math.log(bytes) / Math.log(1024));

    return (
        parseFloat((bytes / Math.pow(1024, unitIndex)).toFixed(2)) +
        ' ' +
        units[unitIndex]
    );
}

// ========== FORM VALIDATION ==========
function validateField(fieldId) {
    const field = document.getElementById(fieldId);

    if (!field) return true;

    const value = field.value.trim();
    let isValid = true;
    let errorMessage = '';

    switch (fieldId) {
        case 'crime_type':
            if (!value) {
                errorMessage = 'Please select a crime type';
                isValid = false;
            }
            break;

        case 'description':
            if (!value) {
                errorMessage = 'Please provide a description';
                isValid = false;
            } else if (value.length < 20) {
                errorMessage = 'Description must be at least 20 characters';
                isValid = false;
            } else if (value.length > 5000) {
                errorMessage = 'Description must not exceed 5000 characters';
                isValid = false;
            }
            break;

        case 'incident_date':
            if (!value) {
                errorMessage = 'Please select incident date';
                isValid = false;
            } else if (new Date(value) > new Date()) {
                errorMessage = 'Incident date cannot be in the future';
                isValid = false;
            }
            break;

        case 'incident_location':
            if (!value) {
                errorMessage = 'Please provide incident location';
                isValid = false;
            } else if (value.length < 5) {
                errorMessage = 'Please provide a valid location';
                isValid = false;
            }
            break;
    }

    if (!isValid) {
        showFieldError(fieldId, errorMessage);
    } else {
        clearFieldError(fieldId);
    }

    return isValid;
}

function showFieldError(fieldId, message) {
    const field = document.getElementById(fieldId);
    const errorDiv = document.getElementById(`${fieldId}_error`);

    field?.classList.add('error');

    if (errorDiv) {
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
    } else if (field?.parentNode) {
        const newErrorDiv = document.createElement('div');
        newErrorDiv.id = `${fieldId}_error`;
        newErrorDiv.className = 'error-message';
        newErrorDiv.textContent = message;
        field.parentNode.appendChild(newErrorDiv);
    }
}

function clearFieldError(fieldId) {
    const field = document.getElementById(fieldId);
    const errorDiv = document.getElementById(`${fieldId}_error`);

    field?.classList.remove('error');

    if (errorDiv) {
        errorDiv.style.display = 'none';
    }
}

function validateForm() {
    const fields = [
        'crime_type',
        'description',
        'incident_date',
        'incident_location'
    ];

    let isValid = true;

    for (const field of fields) {
        if (!validateField(field)) {
            isValid = false;
        }
    }

    return isValid;
}

// ========== DYNAMIC SAFETY TIPS ==========
async function loadCrimeSafetyTips(crimeType, description) {
    const status = document.getElementById('safetyTipsStatus');
    const list = document.getElementById('safetyTipsList');
    const source = document.getElementById('safetyTipsSource');

    if (!list) {
        console.warn(
            'Safety tips list is missing. Check the report page HTML IDs.'
        );
        return;
    }

    if (status) status.textContent = 'Generating safety tips…';
    if (source) source.textContent = '';
    list.replaceChildren();

    try {
        const response = await fetch(`${API_BASE_URL}/ai/safety-tips`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                Authorization: `Bearer ${localStorage.getItem('access_token') || ''}`
            },
            body: JSON.stringify({
                crime_type: crimeType,
                description: description
            })
        });

        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
            throw new Error(
                data.error || `Could not load safety tips (HTTP ${response.status})`
            );
        }

        const result = data.safety_tips || {};
        const tips = Array.isArray(result.tips) ? result.tips : [];

        if (tips.length === 0) {
            if (status) status.textContent = 'No safety tips were returned.';
            return;
        }

        tips.forEach((tip) => {
            const item = document.createElement('li');
            item.textContent = String(tip);
            list.appendChild(item);
        });

        if (status) status.textContent = '';

        if (source) {
            source.textContent =
                `Tips generated by: ${result.analysis_source || 'the configured analysis service'}`;
        }
    } catch (error) {
        console.error('Safety tips error:', error);

        if (status) {
            status.textContent =
                'Safety tips could not be loaded. Please try again.';
        }
    }
}

// ========== AI ANALYSIS ==========
async function performAIAnalysis() {
    const crimeType = document.getElementById('crime_type')?.value;
    const description = document.getElementById('description')?.value;
    const analysisDiv = document.getElementById('aiAnalysisResult');

    if (!crimeType || !description) {
        showNotification(
            'Please fill crime type and description first',
            'warning'
        );
        return;
    }

    // Clear previous results so they are not confused with this analysis.
    aiAnalysisResult = null;

    if (analysisDiv) {
        analysisDiv.style.display = 'none';
        analysisDiv.innerHTML = '';
    }

    showLoader();

    // Request safety tips independently. The tips endpoint handles its own
    // Ollama failure fallback and reports its source.
    const safetyTipsRequest = loadCrimeSafetyTips(crimeType, description);

    try {
        const response = await fetch(`${API_BASE_URL}/ai/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                Authorization: `Bearer ${localStorage.getItem('access_token') || ''}`
            },
            body: JSON.stringify({
                crime_type: crimeType,
                description: description
            })
        });

        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
            throw new Error(
                data.error || `Analysis failed (HTTP ${response.status})`
            );
        }

        if (!data.analysis) {
            throw new Error('The server returned no analysis result');
        }

        aiAnalysisResult = data.analysis;
        displayAIAnalysis(aiAnalysisResult);
    } catch (error) {
        console.error('Analysis request error:', error);
        aiAnalysisResult = null;

        showNotification(
            error.message || 'Could not get an analysis',
            'danger'
        );
    } finally {
        await safetyTipsRequest;
        hideLoader();
    }
}

function displayAIAnalysis(analysis) {
    const analysisDiv = document.getElementById('aiAnalysisResult');

    if (!analysisDiv) return;

    const severity = String(analysis.severity_score || 'Unknown');
    const severityClass = severity.toLowerCase().replace(/[^a-z]/g, '');
    const actions = Array.isArray(analysis.suggested_actions)
        ? analysis.suggested_actions
        : [];

    analysisDiv.style.display = 'block';
    analysisDiv.innerHTML = `
        <h4><i class="fas fa-robot"></i> Analysis Results</h4>
        <p class="analysis-source">
            Source: ${escapeHTML(analysis.analysis_source || 'Ollama local model')}
        </p>
        <div class="analysis-grid">
            <div class="analysis-item">
                <label>Crime Category</label>
                <p>
                    <strong>${escapeHTML(analysis.crime_category || 'Analyzed')}</strong>
                </p>
            </div>
            <div class="analysis-item">
                <label>Severity</label>
                <p>
                    <span class="severity-${severityClass}">
                        ${escapeHTML(severity)}
                    </span>
                </p>
            </div>
            <div class="analysis-item">
                <label>Model Confidence</label>
                <p>${escapeHTML(String(analysis.confidence_score ?? 'N/A'))}%</p>
            </div>
            <div class="analysis-item">
                <label>Estimated Resolution</label>
                <p>
                    ${escapeHTML(
                        analysis.estimated_resolution_time || 'Not provided'
                    )}
                </p>
            </div>
        </div>
        <div class="analysis-suggestions">
            <label>Suggested Actions:</label>
            <ul>
                ${actions
                    .map(
                        (action) => `
                            <li>
                                <i class="fas fa-check"></i>
                                ${escapeHTML(String(action))}
                            </li>
                        `
                    )
                    .join('')}
            </ul>
        </div>
        <p class="analysis-disclaimer">
            This is a preliminary assessment, not a verified investigation
            or guaranteed prediction.
        </p>
    `;

    analysisDiv.scrollIntoView({
        behavior: 'smooth',
        block: 'nearest'
    });
}

// ========== SUBMIT CRIME REPORT ==========
async function submitCrimeReport(event) {
    event.preventDefault();

    if (!validateForm()) {
        showNotification('Please fix the errors before submitting', 'danger');
        return;
    }

    if (uploadedFiles.length === 0) {
        showNotification('Please upload at least one evidence file', 'warning');
        return;
    }

    showLoader();

    const formData = new FormData();
    formData.append(
        'crime_type',
        document.getElementById('crime_type').value
    );
    formData.append(
        'description',
        document.getElementById('description').value
    );
    formData.append(
        'incident_date',
        document.getElementById('incident_date').value
    );
    formData.append(
        'incident_location',
        document.getElementById('incident_location').value
    );

    const additionalInfo = document.getElementById('additional_info');

    if (additionalInfo?.value) {
        formData.append('additional_info', additionalInfo.value);
    }

    // Include the AI analysis if the user requested one.
    if (aiAnalysisResult) {
        formData.append('ai_analysis', JSON.stringify(aiAnalysisResult));
    }

    uploadedFiles.forEach((file) => {
        formData.append('evidence_files', file);
    });

    try {
        const response = await fetch(`${API_BASE_URL}/crime/report`, {
            method: 'POST',
            headers: {
                Authorization: `Bearer ${localStorage.getItem('access_token') || ''}`
            },
            body: formData
        });

        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
            showNotification(
                data.error || data.message || 'Failed to submit complaint',
                'danger'
            );
            return;
        }

        showNotification('Complaint filed successfully!', 'success');
        showComplaintNumber(data.complaint_number);

        setTimeout(() => {
            window.location.href =
                `track-complaint.html?number=${encodeURIComponent(data.complaint_number)}`;
        }, 3000);
    } catch (error) {
        console.error('Submission error:', error);
        showNotification('Network error. Please try again.', 'danger');
    } finally {
        hideLoader();
    }
}

function showComplaintNumber(complaintNumber) {
    const modal = document.getElementById('complaintSuccessModal');
    const numberSpan = document.getElementById('complaintNumber');
    const trackButton = document.getElementById('trackSubmittedComplaint');

    if (numberSpan) {
        numberSpan.textContent = complaintNumber;
    }

    if (trackButton) {
        trackButton.onclick = () => {
            window.location.href =
                `track-complaint.html?number=${encodeURIComponent(complaintNumber)}`;
        };
    }

    if (modal) {
        openModal('complaintSuccessModal');
    }
}

// Export functions used by inline HTML handlers.
window.removeFile = removeFile;
window.performAIAnalysis = performAIAnalysis;