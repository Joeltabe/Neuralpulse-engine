const API_BASE = window.location.origin;
let charts = {};

function getToken() { return localStorage.getItem('neuralpulse_token'); }
function getUser() {
    try { return JSON.parse(localStorage.getItem('neuralpulse_user') || '{}'); }
    catch { return {}; }
}

document.addEventListener('DOMContentLoaded', () => {
    if (window.location.pathname.includes('dashboard.html')) {
        initDashboard();
    } else {
        checkHealth();
        setupNavigation();
        setupUploads();
        setupABTesting();
        setupCopywriting();
    }
});

function initDashboard() {
    const token = getToken();
    if (!token) {
        window.location.href = '/app/login.html';
        return;
    }
    setupSidebar();
    checkHealth();
    setupDashboardUploads();
    setupABTesting();
    setupCopywriting();
    loadHistory();
    loadBalance();
    setupMobileBrand();
    const params = new URLSearchParams(window.location.search);
    const purchased = params.get('purchased');
    if (purchased) {
        showToast('+' + purchased + ' tokens added to your account!', 'success');
        window.history.replaceState({}, '', '/app/dashboard.html');
    }
}

function showToast(message, type) {
    const existing = document.querySelector('.toast-notification');
    if (existing) existing.remove();
    const toast = document.createElement('div');
    toast.className = 'toast-notification toast-' + (type || 'info');
    toast.textContent = message;
    Object.assign(toast.style, {
        position: 'fixed', bottom: '80px', left: '50%', transform: 'translateX(-50%)',
        background: type === 'success' ? 'rgba(16,185,129,0.95)' : 'rgba(100,100,200,0.95)',
        color: '#fff', padding: '12px 24px', borderRadius: '10px', fontSize: '14px',
        fontWeight: '600', zIndex: '99999', boxShadow: '0 4px 20px rgba(0,0,0,0.4)',
        backdropFilter: 'blur(8px)', maxWidth: '90%', textAlign: 'center',
        animation: 'fadeInUp 0.3s ease',
    });
    document.body.appendChild(toast);
    setTimeout(() => { toast.style.opacity = '0'; toast.style.transition = 'opacity 0.5s'; setTimeout(() => toast.remove(), 500); }, 3000);
}

function setupSidebar() {
    const user = getUser();
    if (user.name) {
        const initial = user.name.charAt(0).toUpperCase();
        document.getElementById('sideAvatar').textContent = initial;
        document.getElementById('sideName').textContent = user.name;
        document.getElementById('sideEmail').textContent = user.email || '';
    }
}

function setupMobileBrand() {
    const user = getUser();
    if (user.name) {
        document.getElementById('mobileBrand').style.display = 'flex';
    }
}

async function loadBalance() {
    const token = getToken();
    if (!token) return;
    try {
        const res = await fetch(API_BASE + '/billing/balance', {
            headers: { 'Authorization': 'Bearer ' + token }
        });
        const data = await res.json();
        if (data.success) {
            const bal = data.balance || 0;
            document.getElementById('sideBalance').textContent = bal;
            document.getElementById('mobileBalance').textContent = bal + ' tokens';
            localStorage.setItem('neuralpulse_user', JSON.stringify(data.user || getUser()));
        }
    } catch {}
}

async function loadHistory() {
    const token = getToken();
    if (!token) return;
    try {
        const res = await fetch(API_BASE + '/history/analyses', {
            headers: { 'Authorization': 'Bearer ' + token }
        });
        const data = await res.json();
        const container = document.getElementById('historyContent');
        const loading = document.getElementById('historyLoading');
        loading.style.display = 'none';

        if (data.success && data.analyses && data.analyses.length) {
            container.innerHTML = `
                <div class="history-table-wrap">
                    <table class="frame-analysis-table">
                        <thead><tr>
                            <th>Date</th>
                            <th>Type</th>
                            <th>File</th>
                            <th>Grade</th>
                            <th>Attention</th>
                            <th>Dopamine</th>
                            <th>Memory</th>
                            <th>Tokens</th>
                        </tr></thead>
                        <tbody>
                            ${data.analyses.map(a => `
                                <tr>
                                    <td>${new Date(a.created_at).toLocaleDateString()}</td>
                                    <td>${a.media_type}</td>
                                    <td>${a.filename || '—'}</td>
                                    <td><span class="grade-badge" style="font-size:12px;padding:2px 10px">${a.overall_grade || '—'}</span></td>
                                    <td>${a.attention_score ? (a.attention_score*100).toFixed(0)+'%' : '—'}</td>
                                    <td>${a.dopamine_score ? (a.dopamine_score*100).toFixed(0)+'%' : '—'}</td>
                                    <td>${a.memory_score ? (a.memory_score*100).toFixed(0)+'%' : '—'}</td>
                                    <td>${a.tokens_used}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
                <div class="history-cards">
                    ${data.analyses.map(a => `
                        <div class="audit-card">
                            <div class="audit-row"><span class="label">Date</span><span class="value">${new Date(a.created_at).toLocaleDateString()}</span></div>
                            <div class="audit-row"><span class="label">Type</span><span class="value">${a.media_type}</span></div>
                            <div class="audit-row"><span class="label">Grade</span><span class="value">${a.overall_grade || '—'}</span></div>
                            <div class="audit-row"><span class="label">Attention</span><span class="value">${a.attention_score ? (a.attention_score*100).toFixed(0)+'%' : '—'}</span></div>
                            <div class="audit-row"><span class="label">Tokens</span><span class="value">${a.tokens_used}</span></div>
                        </div>
                    `).join('')}
                </div>
            `;
        } else {
            container.innerHTML = '<p style="text-align:center;color:var(--text-muted);padding:40px">No analyses yet. Upload your first ad to get started.</p>';
        }
    } catch {
        document.getElementById('historyLoading').style.display = 'none';
        document.getElementById('historyContent').innerHTML = '<p style="text-align:center;color:var(--accent-red);padding:40px">Failed to load history.</p>';
    }
}

async function checkHealth() {
    try {
        const res = await fetch(API_BASE + '/health');
        const data = await res.json();
        const dot = document.getElementById('statusDot');
        const txt = document.getElementById('statusText');
        if (dot && txt) {
            if (data.status === 'ok') {
                dot.className = 'status-dot online';
                txt.textContent = 'TRIBE v2 Online';
            } else { txt.textContent = 'Model Offline'; }
        }
    } catch {
        const txt = document.getElementById('statusText');
        if (txt) txt.textContent = 'Disconnected';
    }
}

function switchSection(name) {
    document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
    const section = document.getElementById('section-' + name);
    if (section) section.classList.add('active');

    document.querySelectorAll('.nav-links-side a, .tab-bar a').forEach(l => {
        l.classList.toggle('active', l.getAttribute('href') === '#' + name);
    });
}

function logout() {
    localStorage.removeItem('neuralpulse_token');
    localStorage.removeItem('neuralpulse_user');
    window.location.href = '/app/login.html';
}

function setupDashboardUploads() {
    document.querySelectorAll('.upload-card').forEach(card => {
        const fileInput = card.querySelector('.file-input');
        const uploadBtn = card.querySelector('.upload-btn');
        const textInput = card.querySelector('.text-input');
        const textBtn = card.querySelector('.text-analyze-btn');
        const mediaType = card.dataset.type;

        if (fileInput && uploadBtn) {
            fileInput.addEventListener('change', () => {
                uploadBtn.disabled = !fileInput.files.length;
            });
            uploadBtn.addEventListener('click', () => handleFileUpload(fileInput, mediaType));
        }
        if (textBtn && textInput) {
            textBtn.addEventListener('click', () => handleTextAnalysis(textInput.value));
        }
    });
}

function setupNavigation() {
    document.querySelectorAll('.nav-link[href^="#"]').forEach(link => {
        link.addEventListener('click', e => {
            e.preventDefault();
            const target = link.getAttribute('href').slice(1);
            document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
            document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
            const el = document.getElementById(target);
            if (el) el.classList.add('active');
            link.classList.add('active');
        });
    });
}

function setupUploads() {
    setupDashboardUploads();
}

async function handleFileUpload(input, mediaType) {
    const file = input.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    showLoading('loading');

    try {
        const res = await fetch(API_BASE + '/analyze/' + mediaType, {
            method: 'POST',
            headers: getToken() ? { 'Authorization': 'Bearer ' + getToken() } : {},
            body: formData,
        });
        const result = await res.json();
        hideLoading('loading');
        if (result.success) {
            displayResults(result.data);
            loadBalance();
        } else {
            if (result.error && result.error.includes('Insufficient tokens')) {
                document.getElementById('insufficientMsg').textContent = result.error;
                document.getElementById('insufficientTokens').style.display = 'flex';
            } else {
                showError(result.error || 'Analysis failed');
            }
        }
    } catch (err) {
        hideLoading('loading');
        showError(err.message);
    }
}

async function handleTextAnalysis(text) {
    if (!text.trim()) return;
    showLoading('loading');
    try {
        const res = await fetch(API_BASE + '/analyze/text', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...(getToken() ? { 'Authorization': 'Bearer ' + getToken() } : {}),
            },
            body: JSON.stringify({ text, filename: 'Ad Copy' }),
        });
        const result = await res.json();
        hideLoading('loading');
        if (result.success) {
            displayResults(result.data);
            loadBalance();
        } else {
            if (result.error && result.error.includes('Insufficient tokens')) {
                document.getElementById('insufficientMsg').textContent = result.error;
                document.getElementById('insufficientTokens').style.display = 'flex';
            } else {
                showError(result.error || 'Text analysis failed');
            }
        }
    } catch (err) {
        hideLoading('loading');
        showError(err.message);
    }
}

function showLoading(id) {
    const el = document.getElementById(id);
    if (el) el.classList.remove('hidden');
    const res = document.getElementById('results');
    if (res) res.classList.add('hidden');
}

function hideLoading(id) {
    const el = document.getElementById(id);
    if (el) el.classList.add('hidden');
}

function showError(msg) {
    const el = document.getElementById('results');
    if (!el) return;
    el.classList.remove('hidden');
    el.innerHTML = `<div style="text-align:center;padding:40px;color:var(--accent-red)"><h3>Analysis Failed</h3><p>${msg}</p></div>`;
}

function displayResults(data) {
    const results = document.getElementById('results');
    if (!results) return;
    results.classList.remove('hidden');
    results.scrollIntoView({ behavior: 'smooth', block: 'start' });

    const a = data.brain_scores?.attention || {};
    const d = data.brain_scores?.dopamine || {};
    const m = data.brain_scores?.memory || {};

    const benchmark = data.benchmark || {};
    const directives = data.directives || [];
    const dopamineTriggers = data.dopamine_triggers || [];
    const visualDropoffs = data.visual_dropoffs || [];
    const frameAnalysis = data.frame_analysis || [];

    let benchmarkHtml = '';
    if (benchmark.industry_average) {
        const overall = (a.overall || 0) * 0.35 + (d.overall || 0) * 0.35 + (m.overall || 0) * 0.30;
        const pct = Math.min(100, Math.round((overall / (benchmark.industry_average * 1.5)) * 100));
        const avgPct = Math.min(100, Math.round((benchmark.industry_average / (benchmark.industry_average * 1.5)) * 100));
        benchmarkHtml = `
            <div class="benchmark-bar">
                <span class="bench-label">Benchmark</span>
                <div class="bench-track">
                    <div class="bench-fill" style="width:${pct}%"></div>
                    <div class="bench-marker" style="left:${avgPct}%">
                        <span class="bench-marker-label">Industry Avg</span>
                    </div>
                </div>
                <span class="bench-percentile">${benchmark.percentile_rank || 50}th percentile</span>
            </div>
        `;
    }

    let directivesHtml = '';
    if (directives.length) {
        directivesHtml = `
            <div class="directives-section">
                <h3>Optimization Directives</h3>
                <div class="directives-grid">
                    ${directives.map(dir => `
                        <div class="directive-card ${dir.priority.toLowerCase()}">
                            <span class="dir-priority">${dir.priority}</span>
                            <div class="dir-title">${dir.title}</div>
                            <div class="dir-action">${dir.action}</div>
                            <div class="dir-impact">Expected: ${dir.expected_impact}</div>
                            <div class="dir-impl">${dir.implementation}</div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    let triggerHtml = '';
    if (dopamineTriggers.length) {
        triggerHtml = `
            <div class="directives-section">
                <h3>Dopamine Triggers Detected (${dopamineTriggers.length})</h3>
                <div class="trigger-timeline">
                    ${dopamineTriggers.map(t => `
                        <div class="trigger-dot ${t.intensity > 0.7 ? 'high' : t.intensity > 0.5 ? 'medium' : 'low'}"
                             data-tooltip="${t.trigger_type} (${(t.intensity*100).toFixed(0)}%) @ ${t.timestamp_sec.toFixed(1)}s">
                        </div>
                    `).join('')}
                </div>
                <table class="frame-analysis-table">
                    <thead><tr><th>Time</th><th>Type</th><th>Intensity</th></tr></thead>
                    <tbody>
                        ${dopamineTriggers.map(t => `
                            <tr>
                                <td>${t.timestamp_sec.toFixed(1)}s</td>
                                <td><span class="trigger-badge">${t.trigger_type.replace(/_/g,' ')}</span></td>
                                <td>${(t.intensity*100).toFixed(0)}%</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    }

    let dropoffHtml = '';
    if (visualDropoffs.length) {
        dropoffHtml = `
            <div class="directives-section">
                <h3>Visual Drop-offs (${visualDropoffs.length})</h3>
                <table class="frame-analysis-table">
                    <thead><tr><th>Time</th><th>Drop</th><th>Severity</th><th>Frame</th></tr></thead>
                    <tbody>
                        ${visualDropoffs.map(d => `
                            <tr>
                                <td>${d.timestamp_sec.toFixed(1)}s</td>
                                <td>${(d.drop_magnitude*100).toFixed(0)}%</td>
                                <td><span class="dropoff-badge ${d.severity}">${d.severity}</span></td>
                                <td style="font-size:12px;color:var(--text-muted)">${d.frame_description}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    }

    let tokensHtml = data.tokens_used ? `
        <div style="text-align:right;font-size:12px;color:var(--text-muted);margin-bottom:8px">
            Used ${data.tokens_used} tokens | Balance: ${data.token_balance_after || '?'} tokens
        </div>
    ` : '';

    results.innerHTML = `
        ${tokensHtml}
        <div class="result-header">
            <h2>Analysis Report</h2>
            <span class="grade-badge" id="gradeBadge">${data.overall_grade || 'N/A'}</span>
        </div>
        <p class="summary" id="summaryText">${data.summary || ''}</p>

        ${benchmarkHtml}

        <div class="scores-grid">
            <div class="score-card attention">
                <div class="score-label">Attention</div>
                <div class="score-value" id="attentionScore">${(a.overall*100 || 0).toFixed(0)}%</div>
                <canvas class="score-gauge" id="attentionGauge" height="60"></canvas>
                <div class="score-detail" id="attentionDetail">${a.label || ''}</div>
            </div>
            <div class="score-card dopamine">
                <div class="score-label">Dopamine</div>
                <div class="score-value" id="dopamineScore">${(d.overall*100 || 0).toFixed(0)}%</div>
                <canvas class="score-gauge" id="dopamineGauge" height="60"></canvas>
                <div class="score-detail" id="dopamineDetail">${d.label || ''}</div>
            </div>
            <div class="score-card memory">
                <div class="score-label">Memory</div>
                <div class="score-value" id="memoryScore">${(m.overall*100 || 0).toFixed(0)}%</div>
                <canvas class="score-gauge" id="memoryGauge" height="60"></canvas>
                <div class="score-detail" id="memoryDetail">${m.label || ''}</div>
            </div>
        </div>

        <div class="chart-row">
            <div class="chart-card full">
                <h3>Neural Engagement Curve</h3>
                <canvas id="engagementChart" height="200"></canvas>
            </div>
        </div>

        <div class="chart-row">
            <div class="chart-card">
                <h3>ROI Brain Activity Breakdown</h3>
                <canvas id="roiChart" height="200"></canvas>
            </div>
            <div class="chart-card">
                <h3>Dimension Comparison</h3>
                <canvas id="dimensionChart" height="200"></canvas>
            </div>
        </div>

        <div class="brain-section" id="brainSection">
            <div class="brain-header">
                <h3>Predicted brain activity</h3>
                <div class="brain-mode-switch">
                    <button class="brain-mode-btn active" data-mode="attention" onclick="switchBrainMode('attention')">Attention</button>
                    <button class="brain-mode-btn" data-mode="dopamine" onclick="switchBrainMode('dopamine')">Dopamine</button>
                    <button class="brain-mode-btn" data-mode="memory" onclick="switchBrainMode('memory')">Memory</button>
                </div>
            </div>
            <div class="brain-iframe-wrap" id="brainContainer">
                <div class="brain-loading" id="brainLoading">Generating 3D brain map...</div>
                <iframe id="brainIframe" style="display:none"></iframe>
            </div>
        </div>

        ${directivesHtml}
        ${triggerHtml}
        ${dropoffHtml}

        <div class="recommendations-section">
            <h3>Actionable Recommendations</h3>
            <div id="recommendationsList"></div>
        </div>

        <div class="word-level" id="wordLevelSection" style="display:none">
            <h3>Word-Level Neural Response</h3>
            <div class="word-cloud" id="wordCloud"></div>
        </div>
    `;

    renderEngagementChart(data.timestamp_axis, data.engagement_curve, benchmark);
    renderDimensionChart(a, d, m);
    renderRoiChart(a.roi_breakdown, d.roi_breakdown, m.roi_breakdown);
    renderRecommendations(data.recommendations);
    renderGauge('attentionGauge', a.overall || 0, '#4d6cf5');
    renderGauge('dopamineGauge', d.overall || 0, '#f59e0b');
    renderGauge('memoryGauge', m.overall || 0, '#10b981');

    const wordSection = document.getElementById('wordLevelSection');
    const wordCloud = document.getElementById('wordCloud');
    if (data.word_level_scores && data.word_level_scores.length) {
        wordSection.style.display = 'block';
        renderWordCloud(data.word_level_scores, wordCloud);
    } else {
        wordSection.style.display = 'none';
    }

    initBrainViewer(data.brain_viz_urls || {});
}

function initBrainViewer(vizUrls) {
    const container = document.getElementById('brainContainer');
    const iframe = document.getElementById('brainIframe');
    const loading = document.getElementById('brainLoading');
    if (!container || !iframe) return;
    if (!vizUrls || !vizUrls.attention) {
        container.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:rgba(255,255,255,0.3);background:#000">Brain map not available</div>';
        return;
    }
    window._brainVizUrls = vizUrls;
    loadBrainMode('attention');
}

function loadBrainMode(mode) {
    const iframe = document.getElementById('brainIframe');
    const loading = document.getElementById('brainLoading');
    const urls = window._brainVizUrls || {};
    const url = urls[mode];
    if (!url || !iframe) return;
    loading.classList.remove('hidden');
    iframe.style.display = 'none';
    iframe.src = url;
    iframe.onload = () => {
        loading.classList.add('hidden');
        iframe.style.display = 'block';
    };
    iframe.onerror = () => {
        loading.textContent = 'Failed to load brain map';
    };
}

function switchBrainMode(mode) {
    document.querySelectorAll('.brain-mode-btn').forEach(b => {
        b.classList.toggle('active', b.dataset.mode === mode);
    });
    loadBrainMode(mode);
}

function renderRecommendations(recs) {
    const container = document.getElementById('recommendationsList');
    if (!container) return;
    if (!recs || !recs.length) {
        container.innerHTML = '<p class="text-muted">No recommendations generated.</p>';
        return;
    }
    container.innerHTML = recs.map(r => `
        <div class="rec-card ${r.severity}">
            <div class="rec-header">
                <span class="rec-title">${r.title || 'Recommendation'}</span>
                <span class="rec-severity ${r.severity}">${r.severity}</span>
            </div>
            <div class="rec-description">${r.description || ''}</div>
            <div class="rec-suggestion">${r.suggestion || ''}</div>
            <div class="rec-impact">Expected impact: ${(r.expected_impact * 100).toFixed(0)}%</div>
        </div>
    `).join('');
}

function renderWordCloud(scores, container) {
    if (!container) return;
    const maxScore = Math.max(...scores.map(s => s.attention || 0), 0.01);
    container.innerHTML = scores.map(s => {
        const intensity = (s.attention || 0.3) / maxScore;
        const r = Math.round(77 + (77 - 77) * intensity);
        const g = Math.round(108 + (212 - 108) * intensity);
        const b = Math.round(245 + (255 - 245) * intensity);
        const size = 11 + intensity * 10;
        return `<span class="word-item" style="background:rgba(${r},${g},${b},${0.15 + intensity * 0.4});color:rgb(${r},${g},${b});font-size:${size}px" title="Attention: ${(s.attention * 100).toFixed(0)}% | Dopamine: ${(s.dopamine * 100).toFixed(0)}% | Memory: ${(s.memory * 100).toFixed(0)}%">${s.word}</span>`;
    }).join('');
}

function setupABTesting() {
    let currentMedia = 'video';

    document.querySelectorAll('.ab-type').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.ab-type').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentMedia = btn.dataset.media;
            const isText = currentMedia === 'text';
            document.querySelectorAll('.ab-variant').forEach(v => {
                v.querySelector('.ab-file').classList.toggle('hidden', isText);
                v.querySelector('.ab-text').classList.toggle('hidden', !isText);
            });
        });
    });

    const runBtn = document.getElementById('abRunBtn');
    if (!runBtn) return;

    runBtn.addEventListener('click', async () => {
        const isLoading = document.getElementById('abLoading');
        const results = document.getElementById('abResults');
        isLoading.classList.remove('hidden');
        results.classList.add('hidden');

        try {
            let result;
            if (currentMedia === 'text') {
                const texts = [];
                const names = [];
                document.querySelectorAll('.ab-variant').forEach(v => {
                    const val = v.querySelector('.ab-text').value.trim();
                    if (val) { texts.push(val); names.push(v.querySelector('label').textContent.trim()); }
                });
                if (texts.length < 2) { alert('Need at least 2 text variants'); isLoading.classList.add('hidden'); return; }
                const res = await fetch(API_BASE + '/analyze/ab-test/text', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        ...(getToken() ? { 'Authorization': 'Bearer ' + getToken() } : {}),
                    },
                    body: JSON.stringify({ texts, variant_names: names }),
                });
                result = await res.json();
            } else {
                const formData = new FormData();
                let fileCount = 0;
                document.querySelectorAll('.ab-variant').forEach(v => {
                    const file = v.querySelector('.ab-file').files[0];
                    if (file) { formData.append('files', file); fileCount++; }
                });
                if (fileCount < 2) { alert('Select at least 2 files for A/B comparison'); isLoading.classList.add('hidden'); return; }
                const res = await fetch(API_BASE + '/analyze/ab-test/' + currentMedia, {
                    method: 'POST',
                    headers: getToken() ? { 'Authorization': 'Bearer ' + getToken() } : {},
                    body: formData,
                });
                result = await res.json();
                if (!res.ok) {
                    result = { success: false, error: result.detail || ('Server error (' + res.status + ')') };
                }
            }

            isLoading.classList.add('hidden');
            if (result.success) {
                displayABResults(result.data);
                loadBalance();
            } else {
                results.classList.remove('hidden');
                if (result.error && result.error.includes('Insufficient tokens')) {
                    document.getElementById('insufficientMsg').textContent = result.error;
                    document.getElementById('insufficientTokens').style.display = 'flex';
                } else {
                    results.innerHTML = '<div style="text-align:center;padding:40px;color:var(--accent-red)"><h3>AB Test Failed</h3><p>' + (result.error || 'Unknown error') + '</p></div>';
                }
            }
        } catch (err) {
            isLoading.classList.add('hidden');
            alert('Error: ' + err.message);
        }
    });
}

function displayABResults(data) {
    const el = document.getElementById('abResults');
    if (!el) return;
    el.classList.remove('hidden');
    el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    el.innerHTML = '';

    const header = document.createElement('div');
    header.className = 'result-header';
    header.innerHTML = '<h2>A/B Test Results</h2><span class="winner-badge">' + (data.winning_variant ? 'Winner: ' + data.winning_variant : 'No clear winner') + '</span>';
    el.appendChild(header);

    const summary = document.createElement('p');
    summary.className = 'summary';
    summary.textContent = data.recommendation || '';
    el.appendChild(summary);

    const chartWrap = document.createElement('div');
    chartWrap.className = 'chart-card full';
    chartWrap.innerHTML = '<h3>Variant Comparison</h3><canvas id="abChart" height="250"></canvas>';
    el.appendChild(chartWrap);

    const dims = data.dimension_comparison || {};
    const variants = data.variants || [];
    const labels = variants.map(v => v.filename || 'Variant');
    const datasets = [];
    if (dims.attention) datasets.push({ label: 'Attention', data: dims.attention, backgroundColor: 'rgba(77,108,245,0.7)', borderColor: '#4d6cf5', borderWidth: 2 });
    if (dims.dopamine) datasets.push({ label: 'Dopamine', data: dims.dopamine, backgroundColor: 'rgba(245,158,11,0.7)', borderColor: '#f59e0b', borderWidth: 2 });
    if (dims.memory) datasets.push({ label: 'Memory', data: dims.memory, backgroundColor: 'rgba(16,185,129,0.7)', borderColor: '#10b981', borderWidth: 2 });

    const ctx = document.getElementById('abChart').getContext('2d');
    if (charts.abChart) charts.abChart.destroy();
    charts.abChart = new Chart(ctx, {
        type: 'bar',
        data: { labels, datasets },
        options: {
            responsive: true,
            plugins: { legend: { labels: { color: '#9498c7' } } },
            scales: {
                y: { beginAtZero: true, max: 1, ticks: { color: '#5c6090', callback: v => (v*100).toFixed(0) + '%' } },
                x: { ticks: { color: '#9498c7' } },
            },
        },
    });

    const details = document.createElement('div');
    details.className = 'ab-details';
    details.innerHTML = variants.map(v => {
        const overall = v.brain_scores ? (
            v.brain_scores.attention.overall * 0.35 + v.brain_scores.dopamine.overall * 0.35 + v.brain_scores.memory.overall * 0.30
        ) : 0;
        return '<div class="ab-detail-row"><span class="ab-detail-name">' + (v.filename || 'Variant') + '</span><span class="ab-detail-score">Overall: ' + (overall*100).toFixed(0) + '% | Attn: ' + (v.brain_scores?.attention?.overall ? (v.brain_scores.attention.overall*100).toFixed(0) : 0) + '% | Dop: ' + (v.brain_scores?.dopamine?.overall ? (v.brain_scores.dopamine.overall*100).toFixed(0) : 0) + '% | Mem: ' + (v.brain_scores?.memory?.overall ? (v.brain_scores.memory.overall*100).toFixed(0) : 0) + '%</span></div>';
    }).join('');
    if (data.significance_scores) {
        details.innerHTML += '<h4 style="margin-top:16px;margin-bottom:8px;color:var(--text-secondary)">Statistical Significance</h4>';
        for (const [dim, score] of Object.entries(data.significance_scores)) {
            details.innerHTML += '<div class="ab-detail-row"><span>' + dim + '</span><span>' + (score*100).toFixed(0) + '% confidence</span></div>';
        }
    }
    el.appendChild(details);
}

function setupCopywriting() {
    const runBtn = document.getElementById('copyRunBtn');
    if (!runBtn) return;

    runBtn.addEventListener('click', async () => {
        const original = document.getElementById('copyOriginal').value.trim();
        const v1 = document.getElementById('copyVariant1').value.trim();
        const v2 = document.getElementById('copyVariant2').value.trim();
        if (!original) { alert('Enter original copy'); return; }

        const variants = [], variantNames = [], framingTypes = [];
        if (v1) { variants.push(v1); variantNames.push('Variant 1'); framingTypes.push(document.getElementById('copyFraming1').value); }
        if (v2) { variants.push(v2); variantNames.push('Variant 2'); framingTypes.push(document.getElementById('copyFraming2').value); }
        if (!variants.length) { alert('Add at least one variant'); return; }

        const loading = document.getElementById('copyLoading');
        const results = document.getElementById('copyResults');
        loading.classList.remove('hidden');
        results.classList.add('hidden');

        try {
            const res = await fetch(API_BASE + '/copy/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(getToken() ? { 'Authorization': 'Bearer ' + getToken() } : {}),
                },
                body: JSON.stringify({
                    original_copy: original,
                    variants,
                    variant_names: ['Variant 1: ' + framingTypes[0], ...(framingTypes.length > 1 ? ['Variant 2: ' + framingTypes[1]] : [])],
                    framing_types: framingTypes,
                }),
            });
            const result = await res.json();
            loading.classList.add('hidden');
            if (result.success) {
                displayCopyResults(result.data);
                loadBalance();
            } else {
                results.classList.remove('hidden');
                if (result.error && result.error.includes('Insufficient tokens')) {
                    document.getElementById('insufficientMsg').textContent = result.error;
                    document.getElementById('insufficientTokens').style.display = 'flex';
                } else {
                    results.innerHTML = '<div style="text-align:center;padding:40px;color:var(--accent-red)"><h3>Analysis Failed</h3><p>' + (result.error || 'Unknown error') + '</p></div>';
                }
            }
        } catch (err) {
            loading.classList.add('hidden');
            alert('Error: ' + err.message);
        }
    });
}

function displayCopyResults(data) {
    const el = document.getElementById('copyResults');
    if (!el) return;
    el.classList.remove('hidden');
    el.scrollIntoView({ behavior: 'smooth', block: 'start' });

    const allVariants = [data.original, ...data.variants];
    const scores = data.comparison?.scores || {};
    const firstLine = allVariants.map(v => { const s = scores[v.name] || {}; return v.name + ': ' + ((s.overall*100 || 0).toFixed(0)) + '%'; }).join(' | ');

    let tokensHtml = '';
    if (data.tokens_used) {
        tokensHtml = '<div style="text-align:right;font-size:12px;color:var(--text-muted);margin-bottom:8px">Used ' + data.tokens_used + ' tokens | Balance: ' + (data.token_balance_after || '?') + ' tokens</div>';
    }

    el.innerHTML = tokensHtml + `
        <div class="result-header">
            <h2>Neural Copywriting Report</h2>
            <span class="winner-badge" id="copyWinnerBadge">${data.winning_variant ? 'Best: ' + data.winning_variant : 'Draw'}</span>
        </div>
        <p class="summary" id="copySummary">Winner: ${data.winning_variant || 'None'}. ${firstLine}</p>
        <div class="chart-card full">
            <h3>Variant Comparison</h3>
            <canvas id="copyChart" height="250"></canvas>
        </div>
        <div id="copyDetails" class="ab-details"></div>
        <div class="recommendations-section">
            <h3>Copy Optimization Recommendations</h3>
            <div id="copyRecommendations"></div>
        </div>
    `;

    const labels = Object.keys(scores);
    const attnData = labels.map(l => scores[l].attention || 0);
    const dopData = labels.map(l => scores[l].dopamine || 0);
    const memData = labels.map(l => scores[l].memory || 0);

    const ctx = document.getElementById('copyChart').getContext('2d');
    if (charts.copyChart) charts.copyChart.destroy();
    charts.copyChart = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: ['Attention', 'Dopamine', 'Memory'],
            datasets: labels.map((l, i) => ({
                label: l,
                data: [attnData[i], dopData[i], memData[i]],
                backgroundColor: 'hsla(' + (i * 120) + ', 70%, 50%, 0.1)',
                borderColor: 'hsl(' + (i * 120) + ', 70%, 55%)',
                borderWidth: 2,
                pointBackgroundColor: 'hsl(' + (i * 120) + ', 70%, 55%)',
            })),
        },
        options: {
            responsive: true,
            plugins: { legend: { labels: { color: '#9498c7' } } },
            scales: {
                r: { beginAtZero: true, max: 1, grid: { color: 'rgba(148,152,199,0.2)' }, angleLines: { color: 'rgba(148,152,199,0.2)' }, pointLabels: { color: '#9498c7' }, ticks: { color: '#5c6090', backdropColor: 'transparent' } },
            },
        },
    });

    const details = document.getElementById('copyDetails');
    details.innerHTML = allVariants.map(v => {
        const s = scores[v.name] || {};
        return '<div class="ab-detail-row"><span class="ab-detail-name">' + v.name + ' (' + (v.framing_type || 'original') + ')</span><span class="ab-detail-score">Overall: ' + ((s.overall*100 || 0).toFixed(0)) + '% | Attn: ' + ((s.attention*100 || 0).toFixed(0)) + '% | Dop: ' + ((s.dopamine*100 || 0).toFixed(0)) + '% | Mem: ' + ((s.memory*100 || 0).toFixed(0)) + '%</span></div>';
    }).join('');

    const recs = document.getElementById('copyRecommendations');
    if (data.recommendations && data.recommendations.length) {
        recs.innerHTML = data.recommendations.map(r => '<div class="rec-card suggestion"><div class="rec-title">' + r + '</div></div>').join('');
    } else {
        recs.innerHTML = '<p class="text-muted">No additional recommendations.</p>';
    }
}
