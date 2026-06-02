function renderEngagementChart(timestamps, engagement, benchmark) {
    const ctx = document.getElementById('engagementChart');
    if (!ctx) return;
    const cctx = ctx.getContext('2d');
    if (charts.engagement) charts.engagement.destroy();

    const grad = cctx.createLinearGradient(0, 0, 0, ctx.height || 200);
    grad.addColorStop(0, 'rgba(0, 212, 255, 0.3)');
    grad.addColorStop(1, 'rgba(0, 212, 255, 0.0)');

    const datasets = [{
        label: 'Neural Engagement',
        data: engagement,
        borderColor: '#00d4ff',
        backgroundColor: grad,
        borderWidth: 2,
        fill: true,
        pointRadius: 0,
        tension: 0.3,
    }];

    if (benchmark && benchmark.industry_average) {
        datasets.push({
            label: 'Industry Benchmark',
            data: Array(engagement.length).fill(benchmark.industry_average),
            borderColor: '#f59e0b',
            borderWidth: 1,
            borderDash: [5, 5],
            pointRadius: 0,
            fill: false,
        });
    }

    charts.engagement = new Chart(cctx, {
        type: 'line',
        data: {
            labels: timestamps.map(t => t.toFixed(1) + 's'),
            datasets: datasets,
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 800 },
            plugins: {
                legend: {
                    labels: { color: '#9498c7', font: { size: 11 } },
                },
                tooltip: {
                    callbacks: {
                        label: function(ctx) {
                            if (ctx.dataset.label === 'Industry Benchmark') return 'Benchmark: ' + (ctx.parsed.y * 100).toFixed(0) + '%';
                            return 'Engagement: ' + (ctx.parsed.y * 100).toFixed(0) + '%';
                        },
                    },
                },
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 1,
                    grid: { color: 'rgba(148,152,199,0.1)' },
                    ticks: { color: '#5c6090', callback: v => (v * 100).toFixed(0) + '%', maxTicksLimit: 6, font: { size: 10 } },
                },
                x: {
                    grid: { display: false },
                    ticks: {
                        color: '#5c6090',
                        maxTicksLimit: 10,
                        callback: function(v, i) {
                            if (i % Math.max(1, Math.floor(timestamps.length / 8)) === 0) return timestamps[i]?.toFixed(1) + 's';
                            return '';
                        },
                        font: { size: 10 },
                    },
                },
            },
        },
    });
}

function renderDimensionChart(attention, dopamine, memory) {
    const ctx = document.getElementById('dimensionChart');
    if (!ctx) return;
    const cctx = ctx.getContext('2d');
    if (charts.dimension) charts.dimension.destroy();

    charts.dimension = new Chart(cctx, {
        type: 'doughnut',
        data: {
            labels: ['Attention', 'Dopamine', 'Memory'],
            datasets: [{
                data: [
                    (attention.overall || 0) * 100,
                    (dopamine.overall || 0) * 100,
                    (memory.overall || 0) * 100,
                ],
                backgroundColor: ['#4d6cf5', '#f59e0b', '#10b981'],
                borderColor: ['#3b5de7', '#d97706', '#059669'],
                borderWidth: 2,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: '#9498c7', padding: 16, font: { size: 11 } },
                },
                tooltip: {
                    callbacks: {
                        label: ctx => ctx.label + ': ' + ctx.parsed.toFixed(0) + '%',
                    },
                },
            },
        },
    });
}

function renderRoiChart(attnRoi, dopRoi, memRoi) {
    const ctx = document.getElementById('roiChart');
    if (!ctx) return;
    const cctx = ctx.getContext('2d');
    if (charts.roi) charts.roi.destroy();

    const allRois = { ...(attnRoi || {}), ...(dopRoi || {}), ...(memRoi || {}) };
    const labels = Object.keys(allRois);
    const values = Object.values(allRois);

    const colors = labels.map(l => {
        if (l in (attnRoi || {})) return '#4d6cf5';
        if (l in (dopRoi || {})) return '#f59e0b';
        return '#10b981';
    });

    charts.roi = new Chart(cctx, {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                label: 'ROI Activation',
                data: values,
                backgroundColor: colors.map(c => c + '99'),
                borderColor: colors,
                borderWidth: 1,
                borderRadius: 4,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            indexAxis: 'y',
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: ctx => 'Activation: ' + (ctx.parsed.x * 100).toFixed(0) + '%',
                    },
                },
            },
            scales: {
                x: {
                    beginAtZero: true,
                    max: 1,
                    grid: { color: 'rgba(148,152,199,0.1)' },
                    ticks: { color: '#5c6090', callback: v => (v * 100).toFixed(0) + '%', font: { size: 10 } },
                },
                y: {
                    grid: { display: false },
                    ticks: { color: '#9498c7', font: { size: 10 } },
                },
            },
        },
    });
}

function renderGauge(canvasId, value, color) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    const container = canvas.parentElement;
    const w = container ? container.clientWidth : 200;
    const h = canvas.clientHeight || 60;

    canvas.width = w * (window.devicePixelRatio || 1);
    canvas.height = h * (window.devicePixelRatio || 1);
    const ctx = canvas.getContext('2d');
    ctx.scale(window.devicePixelRatio || 1, window.devicePixelRatio || 1);

    ctx.clearRect(0, 0, w, h);

    const cx = w / 2;
    const cy = h - 8;
    const radius = Math.min(w, h * 2) / 2 - 8;

    ctx.beginPath();
    ctx.arc(cx, cy, radius, Math.PI, 0);
    ctx.strokeStyle = 'rgba(255,255,255,0.08)';
    ctx.lineWidth = 8;
    ctx.stroke();

    const endAngle = Math.PI + (Math.PI * Math.min(value, 1));
    ctx.beginPath();
    ctx.arc(cx, cy, radius, Math.PI, endAngle);
    ctx.strokeStyle = color;
    ctx.lineWidth = 8;
    ctx.lineCap = 'round';
    ctx.stroke();
}
