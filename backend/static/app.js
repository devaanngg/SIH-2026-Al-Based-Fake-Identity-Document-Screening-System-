const API_BASE_URL = 'http://localhost:8000';

// State
let selectedFile = null;
let currentPage = 'dashboard';

// DOM Elements
document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initUploadArea();
    initScreeningForm();
    checkApiStatus();
    loadDashboard();
    loadHistory();
});

// Navigation
function initNavigation() {
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', () => {
            const page = item.dataset.page;
            navigateTo(page);
        });
    });
}

function navigateTo(page) {
    currentPage = page;
    document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
    document.querySelector(`.nav-item[data-page="${page}"]`).classList.add('active');
    
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.getElementById(`page-${page}`).classList.add('active');
    
    if (page === 'dashboard') loadDashboard();
    if (page === 'history') loadHistory();
}

// File upload area
function initUploadArea() {
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('file-input');
    
    uploadArea.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', (e) => handleFileSelect(e.target.files[0]));
    
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', () => uploadArea.classList.remove('dragover'));
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        handleFileSelect(e.dataTransfer.files[0]);
    });
}

function handleFileSelect(file) {
    if (!file) return;
    
    const validTypes = ['image/jpeg', 'image/png', 'image/jpg'];
    if (!validTypes.includes(file.type)) {
        showToast('Please upload a valid image file (JPG or PNG)', 'error');
        return;
    }
    
    if (file.size > 10 * 1024 * 1024) {
        showToast('File size should be less than 10MB', 'error');
        return;
    }
    
    selectedFile = file;
    const uploadArea = document.getElementById('upload-area');
    uploadArea.classList.add('has-file');
    
    document.getElementById('upload-content').innerHTML = `
        <span class="upload-icon">✅</span>
        <p>${file.name}</p>
        <span class="upload-hint">Click to change file (${(file.size / 1024).toFixed(0)} KB)</span>
    `;
}

// Screening form
function initScreeningForm() {
    document.getElementById('screening-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const documentType = document.getElementById('document-type').value;
        
        if (!documentType) {
            showToast('Please select document type', 'error');
            return;
        }
        
        if (!selectedFile) {
            showToast('Please upload a document image', 'error');
            return;
        }
        
        await screenDocument(documentType, selectedFile);
    });
}

async function screenDocument(documentType, file) {
    const button = document.getElementById('screen-btn');
    const btnText = button.querySelector('.btn-text');
    const spinner = button.querySelector('.spinner');
    
    button.disabled = true;
    btnText.textContent = 'Screening...';
    spinner.classList.remove('hidden');
    
    document.getElementById('screening-results').classList.add('hidden');
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/screening/documents?document_type=${documentType}`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Screening failed');
        }
        
        const result = await response.json();
        showToast('Document screened successfully', 'success');
        
        // Load detailed result
        const detailResponse = await fetch(`${API_BASE_URL}/api/screening/${result.document_id}`);
        if (detailResponse.ok) {
            const details = await detailResponse.json();
            renderScreeningResults(details);
        }
        
        // Refresh history
        loadHistory();
        loadDashboard();
        
    } catch (error) {
        showToast(error.message, 'error');
    } finally {
        button.disabled = false;
        btnText.textContent = 'Start Screening';
        spinner.classList.add('hidden');
    }
}

// Render results
function renderScreeningResults(details) {
    const container = document.getElementById('screening-results');
    const riskLevel = details.risk_level || 'unknown';
    const extracted = details.extracted_data || {};
    
    const extractedFields = Object.entries(extracted)
        .filter(([key]) => !key.includes('file_path'))
        .map(([key, value]) => `
            <div class="data-item">
                <span class="label">${formatLabel(key)}</span>
                <span class="value">${value}</span>
            </div>
        `).join('');
    
    const validationErrors = (details.validation_errors || []).join(' • ') || 'All checks passed';
    const validationClass = details.validation_errors && details.validation_errors.length > 0 ? 'medium' : 'low';
    
    container.innerHTML = `
        <div class="result-card">
            <div class="result-header">
                <div>
                    <strong>Document #${details.id}</strong>
                    <span style="color: var(--text-light); margin-left: 8px;">${formatLabel(details.document_type)}</span>
                </div>
                <span class="risk-badge ${riskLevel}">${riskLevel.toUpperCase()} risk</span>
            </div>
            <div class="result-sections">
                <div class="result-section">
                    <h4>📋 Risk Score: ${details.risk_score.toFixed(1)}/100</h4>
                    <div class="score-bar">
                        <div class="score-fill ${riskLevel}" style="width: ${details.risk_score}%"></div>
                    </div>
                </div>
                ${extractedFields ? `
                <div class="result-section">
                    <h4>📄 Extracted Data</h4>
                    <div class="data-grid">${extractedFields}</div>
                </div>` : ''}
                <div class="result-section">
                    <h4>✅ Document Validation</h4>
                    <div class="section-content">
                        <span class="status-chip ${validationClass === 'low' ? 'cleared' : 'flagged'}">
                            ${validationClass === 'low' ? 'Valid' : 'Issues Found'}
                        </span>
                        <p style="margin-top: 8px; color: var(--text-light);">${validationErrors}</p>
                    </div>
                </div>
                <div class="result-section">
                    <h4>🔍 Tampering Analysis</h4>
                    <div class="section-content">
                        <span class="status-chip ${details.has_tampering ? 'flagged' : 'cleared'}">
                            ${details.has_tampering ? `Tampering Suspicion (${details.tampering_score.toFixed(1)}%)` : `No Tampering Detected (${details.tampering_score.toFixed(1)}%)`}
                        </span>
                    </div>
                </div>
                ${details.face_match_score !== undefined ? `
                <div class="result-section">
                    <h4>👤 Face Verification</h4>
                    <div class="section-content">
                        <span class="status-chip ${details.face_match ? 'cleared' : 'flagged'}">
                            ${details.face_match ? `Match Confirmed (${details.face_match_score}%)` : `No Match (${details.face_match_score}%)`}
                        </span>
                    </div>
                </div>` : ''}
            </div>
        </div>
    `;
    
    container.classList.remove('hidden');
    container.scrollIntoView({ behavior: 'smooth' });
}

// Dashboard
async function loadDashboard() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/dashboard/stats`);
        
        if (!response.ok) throw new Error('Failed to load dashboard');
        
        const stats = await response.json();
        
        document.getElementById('stat-total').textContent = stats.total_documents || 0;
        document.getElementById('stat-flagged').textContent = stats.flagged_documents || 0;
        document.getElementById('stat-high-risk').textContent = stats.high_risk_count || 0;
        
        renderBarChart('chart-type', stats.documents_by_type || {}, ['#2563eb', '#10b981', '#f59e0b', '#ef4444']);
        renderBarChart('chart-risk', stats.risk_distribution || {}, ['#10b981', '#f59e0b', '#ef4444', '#7f1d1d']);
        
    } catch (error) {
        console.error('Failed to load dashboard:', error);
    }
}

function renderBarChart(containerId, data, colors) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const entries = Object.entries(data);
    if (entries.length === 0) {
        container.innerHTML = '<p style="color: var(--text-light); text-align: center; padding-top: 3rem;">No data yet</p>';
        return;
    }
    
    const max = Math.max(...entries.map(([, v]) => v));
    
    container.innerHTML = entries.map(([label, value], i) => `
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
            <span style="min-width: 80px; font-size: 0.85rem; color: var(--text-light);">${formatLabel(label)}</span>
            <div style="flex: 1; background: var(--bg); border-radius: 4px; height: 20px; overflow: hidden;">
                <div style="width: ${max > 0 ? (value / max * 100) : 0}%; height: 100%; background: ${colors[i % colors.length]}; border-radius: 4px; transition: width 0.6s ease;"></div>
            </div>
            <span style="min-width: 30px; font-weight: 600; font-size: 0.85rem;">${value}</span>
        </div>
    `).join('');
}

// History
async function loadHistory() {
    const tbody = document.getElementById('history-table-body');
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/screening/results`);
        
        if (!response.ok) throw new Error('Failed to load history');
        
        const records = await response.json();
        
        if (records.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="loading-cell">No screening records yet</td></tr>';
            return;
        }
        
        tbody.innerHTML = records.map(record => `
            <tr>
                <td>#${record.id}</td>
                <td>${formatLabel(record.document_type)}</td>
                <td>${escapeHtml(record.filename)}</td>
                <td>${formatDate(record.upload_time)}</td>
                <td>
                    <span class="risk-badge ${record.risk_level || 'medium'}" style="font-size: 0.7rem; padding: 4px 10px;">
                        ${typeof record.risk_score === 'number' ? record.risk_score.toFixed(0) : '—'} / 100
                    </span>
                </td>
                <td>
                    <span class="status-chip ${record.has_tampering ? 'flagged' : 'cleared'}">
                        ${record.has_tampering ? `Yes (${record.tampering_score.toFixed(0)}%)` : 'No'}
                    </span>
                </td>
                <td>
                    <span class="status-chip ${record.status}">${formatLabel(record.status)}</span>
                </td>
                <td>
                    <button class="button secondary small" onclick="viewResult(${record.id})">View</button>
                </td>
            </tr>
        `).join('');
        
    } catch (error) {
        tbody.innerHTML = `<tr><td colspan="8" class="loading-cell">Error loading history: ${escapeHtml(error.message)}</td></tr>`;
    }
}

// View result modal
async function viewResult(id) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/screening/${id}`);
        if (!response.ok) throw new Error('Failed to load result');
        
        const record = await response.json();
        const modal = document.getElementById('result-modal');
        const body = document.getElementById('modal-body');
        const extracted = record.extracted_data || {};
        
        const fields = Object.entries(extracted)
            .map(([key, value]) => `
                <div style="display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid var(--border);">
                    <span style="color: var(--text-light);">${formatLabel(key)}</span>
                    <strong>${escapeHtml(String(value))}</strong>
                </div>
            `).join('');
        
        body.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                <div>
                    <h4 style="margin-bottom: 4px;">${formatLabel(record.document_type)} - ${escapeHtml(record.filename)}</h4>
                    <span style="color: var(--text-light); font-size: 0.85rem;">${formatDate(record.upload_time)}</span>
                </div>
                <span class="risk-badge ${record.risk_level || 'medium'}">${(record.risk_level || 'unknown').toUpperCase()}</span>
            </div>
            <div style="margin-bottom: 1rem;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                    <span style="color: var(--text-light);">Risk Score</span>
                    <strong>${record.risk_score.toFixed(1)} / 100</strong>
                </div>
                <div class="score-bar">
                    <div class="score-fill ${record.risk_level || 'medium'}" style="width: ${record.risk_score}%"></div>
                </div>
            </div>
            ${fields ? `<h4 style="margin-bottom: 8px;">Extracted Data</h4>${fields}` : ''}
            <h4 style="margin: 1rem 0 8px;">Tampering Analysis</h4>
            <p style="color: var(--text-light);">
                ${record.has_tampering 
                    ? `<span style="color: var(--danger);">⚠️ Tampering suspected (${record.tampering_score.toFixed(1)}%)</span>`
                    : `<span style="color: var(--success);">✓ No tampering detected (${record.tampering_score.toFixed(1)}%)</span>`}
            </p>
            ${record.notes ? `<h4 style="margin: 1rem 0 8px;">Notes</h4><p style="color: var(--text-light);">${escapeHtml(record.notes)}</p>` : ''}
        `;
        
        modal.classList.remove('hidden');
        
    } catch (error) {
        showToast(error.message, 'error');
    }
}

function closeModal() {
    document.getElementById('result-modal').classList.add('hidden');
}

// API status check
async function checkApiStatus() {
    const statusEl = document.getElementById('api-status');
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        if (response.ok) {
            statusEl.textContent = 'Online';
            statusEl.parentElement.querySelector('.status-dot').classList.remove('error');
        } else {
            throw new Error();
        }
    } catch (error) {
        statusEl.textContent = 'Offline';
        statusEl.parentElement.querySelector('.status-dot').classList.add('error');
    }
}

// Toast notifications
function showToast(message, type = '') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type}`;
    
    setTimeout(() => {
        toast.classList.add('hidden');
    }, 3000);
}

// Utilities
function formatLabel(str) {
    if (!str) return '';
    return str
        .replace(/_/g, ' ')
        .replace(/\b\w/g, c => c.toUpperCase());
}

function formatDate(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleString();
}

function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}
