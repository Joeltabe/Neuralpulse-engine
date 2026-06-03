const TRIBE_ROI_ATLAS = [
  { key: 'V1', aliases: ['V1/V2', 'Primary Visual', 'Visual Cortex'], label: 'V1/V2 (Primary Visual Cortex)', center: [0.00, -0.10, -0.82], radius: 0.30, network: 'visual', role: 'visual salience', weight: 0.16 },
  { key: 'V3V4', aliases: ['V3/V4', 'Visual Processing'], label: 'V3/V4 (Visual Processing)', center: [0.22, -0.24, -0.64], radius: 0.22, network: 'visual', role: 'color and form salience', weight: 0.09 },
  { key: 'MT', aliases: ['MT/V5', 'Visual Motion'], label: 'MT/V5 (Visual Motion)', center: [0.54, -0.20, -0.24], radius: 0.22, network: 'motion', role: 'motion and cuts', weight: 0.14 },
  { key: 'FFA', aliases: ['Fusiform Face Area'], label: 'FFA (Fusiform Face Area)', center: [0.42, -0.48, -0.22], radius: 0.20, network: 'social', role: 'faces and identity', weight: 0.18 },
  { key: 'TPJ', aliases: ['Temporo-Parietal Junction'], label: 'TPJ (Temporo-Parietal Junction)', center: [0.55, 0.12, -0.18], radius: 0.24, network: 'social', role: 'social inference', weight: 0.18 },
  { key: 'Amygdala', aliases: ['Amygdala'], label: 'Amygdala', center: [0.30, -0.54, -0.04], radius: 0.17, network: 'emotion', role: 'emotional arousal', weight: 0.16 },
  { key: 'A1', aliases: ['Primary Auditory', 'Auditory Cortex'], label: 'A1 (Primary Auditory Cortex)', center: [0.58, -0.08, -0.06], radius: 0.22, network: 'audio', role: 'audio hook', weight: 0.12 },
  { key: 'Broca', aliases: ["Broca's Area", 'Broca'], label: "Broca's Area", center: [0.35, 0.30, -0.10], radius: 0.19, network: 'language', role: 'speech production/language', weight: 0.06 },
  { key: 'Wernicke', aliases: ['Wernicke'], label: "Wernicke's Area", center: [0.47, 0.05, -0.26], radius: 0.20, network: 'language', role: 'speech comprehension', weight: 0.06 },
  { key: 'DMN', aliases: ['Default Mode Network', 'DMN'], label: 'DMN (Default Mode Network)', center: [0.00, 0.10, 0.38], radius: 0.34, network: 'narrative', role: 'narrative immersion', weight: 0.14 },
  { key: 'PCC', aliases: ['Posterior Cingulate', 'PCC'], label: 'PCC (Posterior Cingulate)', center: [0.00, -0.05, 0.50], radius: 0.20, network: 'narrative', role: 'self-referential context', weight: 0.05 },
  { key: 'HIP', aliases: ['Hippocampus', 'HIP'], label: 'Hippocampus', center: [0.22, -0.46, 0.04], radius: 0.18, network: 'memory', role: 'memory encoding', weight: 0.06 },
  { key: 'PHC', aliases: ['Parahippocampal', 'PHC'], label: 'PHC (Parahippocampal Cortex)', center: [0.22, -0.52, -0.12], radius: 0.18, network: 'memory', role: 'scene context', weight: 0.05 },
  { key: 'vmPFC', aliases: ['vmPFC'], label: 'vmPFC', center: [0.00, 0.58, 0.08], radius: 0.24, network: 'value', role: 'value and reward appraisal', weight: 0.07 },
  { key: 'DLPFC', aliases: ['DLPFC'], label: 'DLPFC', center: [0.38, 0.44, 0.14], radius: 0.22, network: 'executive', role: 'cognitive control', weight: 0.04 },
  { key: 'NAcc', aliases: ['VS/NAcc', 'Ventral Striatum', 'NAcc'], label: 'VS/NAcc (Ventral Striatum)', center: [0.16, 0.28, -0.06], radius: 0.16, network: 'reward', role: 'reward anticipation', weight: 0.10 },
  { key: 'SMA', aliases: ['SMA', 'Supplementary Motor'], label: 'SMA (Supplementary Motor Area)', center: [0.00, 0.28, 0.54], radius: 0.22, network: 'motor', role: 'action readiness', weight: 0.04 },
];

const NETWORK_DIMENSIONS = {
  visual: 'attention', motion: 'attention', social: 'attention', audio: 'attention',
  emotion: 'dopamine', reward: 'dopamine', value: 'dopamine', motor: 'dopamine',
  language: 'memory', narrative: 'memory', memory: 'memory', executive: 'memory',
};

class BrainViewer {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    if (!this.container) return;
    this.mesh = null;
    this.currentView = 'lateral';
    this.currentMode = 'heatmap';
    this.isAnimating = true;
    this.rotationSpeed = 0.0022;
    this.currentPayload = { scores: { attention: 0.1, dopamine: 0.1, memory: 0.1 }, regions: [] };
    this.vertexActivation = [];
    this.vertexRegion = [];
    this.regionSummary = [];
    this.init();
  }

  init() {
    const rect = this.container.getBoundingClientRect();
    const w = rect.width || 600;
    const h = rect.height || 420;
    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(30, w / h, 0.1, 12);
    this.camera.position.set(0, 0, 3.2);
    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    this.renderer.setSize(w, h);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    this.renderer.setClearColor(0x000000, 0);
    this.container.appendChild(this.renderer.domElement);

    this.scene.add(new THREE.AmbientLight(0x6d7188, 0.55));
    const key = new THREE.DirectionalLight(0xffffff, 1.25);
    key.position.set(1.4, 1.8, 2.2);
    this.scene.add(key);
    const rim = new THREE.DirectionalLight(0x9bbcff, 0.55);
    rim.position.set(-1.5, 0.2, -1.8);
    this.scene.add(rim);
    const sulciLight = new THREE.DirectionalLight(0xffffff, 0.35);
    sulciLight.position.set(0, -2, 0.8);
    this.scene.add(sulciLight);

    this.loadMesh();
    this.setupTooltip();
    this.setupInteraction();
    this.animate();

    new ResizeObserver(() => {
      const r = this.container.getBoundingClientRect();
      this.camera.aspect = r.width / r.height;
      this.camera.updateProjectionMatrix();
      this.renderer.setSize(r.width, r.height);
    }).observe(this.container);
  }

  loadMesh() {
    this.container.classList.add('loading');
    fetch('js/brain_mesh.json')
      .then(r => r.json())
      .then(data => {
        this.buildMesh(data);
        this.container.classList.remove('loading');
      })
      .catch(() => {
        this.container.innerHTML = '<div class="brain-error">Could not load brain mesh</div>';
      });
  }

  corticalFold(x, y, z) {
    const gyri = Math.sin(28 * x + 8 * z) * Math.sin(22 * y - 5 * z);
    const sulci = Math.sin(42 * (x + z)) * Math.cos(34 * (y - z));
    return { ridge: gyri, fine: sulci, groove: gyri < -0.18 || sulci < -0.62 };
  }

  buildMesh(data) {
    const geo = new THREE.BufferGeometry();
    const verts = data.vertices;
    const positions = new Float32Array(verts.length * 3);

    for (let i = 0; i < verts.length; i++) {
      const [x, y, z] = verts[i];
      const fold = this.corticalFold(x, y, z);
      const scale = 1 + fold.ridge * 0.026 + fold.fine * 0.012;
      positions[i * 3] = x * scale;
      positions[i * 3 + 1] = y * scale;
      positions[i * 3 + 2] = z * scale;
    }

    geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geo.setIndex(data.faces.flat());
    geo.computeVertexNormals();
    geo.setAttribute('color', new THREE.BufferAttribute(new Float32Array(verts.length * 3), 3));

    const material = new THREE.MeshPhongMaterial({
      vertexColors: true,
      shininess: 72,
      specular: new THREE.Color(0x343443),
      side: THREE.DoubleSide,
    });

    this.mesh = new THREE.Mesh(geo, material);
    this.scene.add(this.mesh);

    const lineMaterial = new THREE.MeshBasicMaterial({ color: 0x09090d, wireframe: true, transparent: true, opacity: 0.10 });
    this.wireMesh = new THREE.Mesh(geo.clone(), lineMaterial);
    this.scene.add(this.wireMesh);

    this.updateColors(this.currentPayload);
  }

  setupTooltip() {
    this.tooltipEl = document.createElement('div');
    this.tooltipEl.className = 'brain-tooltip';
    this.tooltipEl.style.display = 'none';
    document.body.appendChild(this.tooltipEl);
  }

  setupInteraction() {
    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();
    let isDragging = false;
    let prevMouse = { x: 0, y: 0 };

    this.renderer.domElement.addEventListener('mousedown', e => {
      isDragging = false;
      prevMouse = { x: e.clientX, y: e.clientY };
    });

    this.renderer.domElement.addEventListener('mousemove', e => {
      const dx = e.clientX - prevMouse.x;
      const dy = e.clientY - prevMouse.y;
      if (Math.abs(dx) > 3 || Math.abs(dy) > 3) {
        isDragging = true;
        this.rotate(dx, dy);
        this.hideTooltip();
      }
      prevMouse = { x: e.clientX, y: e.clientY };
      if (isDragging || !this.mesh) return;

      const rect = this.renderer.domElement.getBoundingClientRect();
      mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
      raycaster.setFromCamera(mouse, this.camera);
      const hit = raycaster.intersectObject(this.mesh)[0];
      if (hit) {
        this.renderer.domElement.style.cursor = 'pointer';
        this.showTooltip(hit, e.clientX, e.clientY);
      } else {
        this.renderer.domElement.style.cursor = 'default';
        this.hideTooltip();
      }
    });

    this.renderer.domElement.addEventListener('click', () => {
      if (!isDragging) {
        this.isAnimating = !this.isAnimating;
        const indicator = document.getElementById('rotateIndicator');
        if (indicator) indicator.textContent = this.isAnimating ? 'Auto-rotate ON' : 'Auto-rotate OFF';
      }
    });
    this.renderer.domElement.addEventListener('mouseleave', () => this.hideTooltip());

    let touchStart = { x: 0, y: 0 };
    this.renderer.domElement.addEventListener('touchstart', e => {
      const t = e.touches[0];
      touchStart = { x: t.clientX, y: t.clientY };
    });
    this.renderer.domElement.addEventListener('touchmove', e => {
      e.preventDefault();
      const t = e.touches[0];
      this.rotate(t.clientX - touchStart.x, t.clientY - touchStart.y);
      touchStart = { x: t.clientX, y: t.clientY };
    }, { passive: false });
  }

  rotate(dx, dy) {
    if (!this.mesh) return;
    this.mesh.rotation.y += dx * 0.005;
    this.mesh.rotation.x = Math.max(-1.2, Math.min(1.2, this.mesh.rotation.x + dy * 0.005));
    if (this.wireMesh) {
      this.wireMesh.rotation.copy(this.mesh.rotation);
    }
  }

  normalizePayload(input = {}) {
    const regions = Array.isArray(input.regions) ? input.regions : [];
    const scores = input.scores || input;
    return {
      scores: {
        attention: Number(scores.attention ?? 0) || 0,
        dopamine: Number(scores.dopamine ?? 0) || 0,
        memory: Number(scores.memory ?? 0) || 0,
      },
      regions: regions.map(r => ({ ...r, value: this.normalizeValue(r.value ?? r.activation ?? r.score ?? 0) })),
      vertices: input.vertices || input.vertexActivations || null,
    };
  }

  normalizeValue(value) {
    const v = Number(value) || 0;
    return v > 1 ? Math.max(0, Math.min(1, v / 100)) : Math.max(0, Math.min(1, v));
  }

  matchRoi(regionName = '') {
    const normalized = regionName.toLowerCase();
    return TRIBE_ROI_ATLAS.find(roi =>
      normalized.includes(roi.key.toLowerCase()) || roi.aliases.some(alias => normalized.includes(alias.toLowerCase()))
    );
  }

  mirroredCenters(roi) {
    const [x, y, z] = roi.center;
    if (Math.abs(x) < 0.03) return [[x, y, z]];
    return [[x, y, z], [-x, y, z]];
  }

  scoreVertexFromRegions(vertexIndex, payload) {
    const pos = this.mesh.geometry.attributes.position.array;
    const x = pos[vertexIndex * 3], y = pos[vertexIndex * 3 + 1], z = pos[vertexIndex * 3 + 2];
    let best = 0;
    let bestRegion = null;
    for (const region of payload.regions) {
      const roi = this.matchRoi(region.name || region.key || region.label);
      if (!roi) continue;
      const modeDim = NETWORK_DIMENSIONS[roi.network] || 'attention';
      const modeMultiplier = this.currentMode === 'heatmap' || this.currentMode === modeDim ? 1 : 0.22;
      for (const c of this.mirroredCenters(roi)) {
        const dx = x - c[0], dy = y - c[1], dz = z - c[2];
        const d2 = dx * dx + dy * dy + dz * dz;
        const blob = Math.exp(-d2 / (2 * roi.radius * roi.radius));
        const score = region.value * blob * modeMultiplier;
        if (score > best) {
          best = score;
          bestRegion = { ...roi, activation: region.value, sourceName: region.name || roi.label };
        }
      }
    }
    return { score: Math.max(0, Math.min(1, best)), region: bestRegion };
  }

  baseCortexColor(vertexIndex, activation) {
    const pos = this.mesh.geometry.attributes.position.array;
    const x = pos[vertexIndex * 3], y = pos[vertexIndex * 3 + 1], z = pos[vertexIndex * 3 + 2];
    const fold = this.corticalFold(x, y, z);
    const shade = fold.groove ? 0.015 : 0.78 + 0.12 * fold.ridge;
    return activation > 0.03 ? shade * 0.18 : shade;
  }

  heatmapColor(score, vertexIndex) {
    const t = Math.max(0, Math.min(1, score));
    if (t <= 0.02) {
      const base = this.baseCortexColor(vertexIndex, t);
      return { r: base, g: base, b: base };
    }
    if (t < 0.22) return { r: 0.12 + t * 1.8, g: 0, b: 0 };
    if (t < 0.48) return { r: 0.50 + (t - 0.22) * 1.9, g: (t - 0.22) * 0.5, b: 0 };
    if (t < 0.72) return { r: 1, g: (t - 0.48) * 3.1, b: 0 };
    if (t < 0.90) return { r: 1, g: 0.74 + (t - 0.72) * 1.45, b: (t - 0.72) * 0.8 };
    return { r: 1, g: 1, b: 0.25 + (t - 0.90) * 7.5 };
  }

  updateColors(rawPayload) {
    this.currentPayload = this.normalizePayload(rawPayload);
    if (!this.mesh) return;
    const colors = this.mesh.geometry.attributes.color.array;
    const n = this.mesh.geometry.attributes.position.count;
    this.vertexActivation = new Array(n);
    this.vertexRegion = new Array(n);

    for (let i = 0; i < n; i++) {
      const scored = this.scoreVertexFromRegions(i, this.currentPayload);
      this.vertexActivation[i] = scored.score;
      this.vertexRegion[i] = scored.region;
      const c = this.heatmapColor(scored.score, i);
      colors[i * 3] = c.r;
      colors[i * 3 + 1] = c.g;
      colors[i * 3 + 2] = c.b;
    }
    this.mesh.geometry.attributes.color.needsUpdate = true;
    this.regionSummary = this.currentPayload.regions;
  }

  showTooltip(hit, x, y) {
    if (!hit.face) return;
    const candidates = [hit.face.a, hit.face.b, hit.face.c];
    const vertex = candidates.reduce((best, idx) => (this.vertexActivation[idx] || 0) > (this.vertexActivation[best] || 0) ? idx : best, candidates[0]);
    const region = this.vertexRegion[vertex];
    const activation = this.vertexActivation[vertex] || 0;
    if (!region || activation < 0.025) {
      this.tooltipEl.innerHTML = `<div class="brain-tip-header"><span class="brain-tip-name">Cortical surface</span><span class="brain-tip-score">${Math.round(activation * 100)}%</span></div><div class="brain-tip-section">Hover an activation blob to inspect its TRIBE ROI score.</div>`;
    } else {
      this.tooltipEl.innerHTML = `
        <div class="brain-tip-header">
          <span class="brain-tip-name">${region.label}</span>
          <span class="brain-tip-score">${Math.round(region.activation * 100)}%</span>
        </div>
        <div class="brain-tip-section"><strong>TRIBE ROI:</strong> ${region.sourceName}</div>
        <div class="brain-tip-section"><strong>Virality role:</strong> ${region.role}</div>
        <div class="brain-tip-section"><strong>Network:</strong> ${region.network}</div>
        <div class="brain-tip-footer">Blob intensity uses black→red→orange→yellow→white heatmap.</div>
      `;
    }
    this.tooltipEl.style.display = 'block';
    let tx = x + 15, ty = y - 10;
    const tw = this.tooltipEl.offsetWidth, th = this.tooltipEl.offsetHeight;
    if (tx + tw > window.innerWidth) tx = x - tw - 15;
    if (ty + th > window.innerHeight) ty = window.innerHeight - th - 10;
    if (ty < 10) ty = 10;
    this.tooltipEl.style.left = tx + 'px';
    this.tooltipEl.style.top = ty + 'px';
  }

  hideTooltip() {
    if (this.tooltipEl) this.tooltipEl.style.display = 'none';
  }

  setMode(mode) {
    this.currentMode = mode;
    this.updateColors(this.currentPayload);
  }

  setView(view) {
    this.currentView = view;
    this.isAnimating = false;
    const views = {
      lateral: { pos: [0, 0, 3.2], rot: [0, 0, 0] },
      medial: { pos: [0, 0, -3.2], rot: [0, Math.PI, 0] },
      dorsal: { pos: [0, 3.2, 0.01], rot: [0, 0, 0] },
      ventral: { pos: [0, -3.2, 0.01], rot: [0, 0, 0] },
      anterior: { pos: [3.2, 0, 0], rot: [0, 0, 0] },
      posterior: { pos: [-3.2, 0, 0], rot: [0, 0, 0] },
    };
    const v = views[view] || views.lateral;
    this.camera.position.set(...v.pos);
    this.camera.lookAt(0, 0, 0);
    if (this.mesh) {
      this.mesh.rotation.set(...v.rot);
      if (this.wireMesh) this.wireMesh.rotation.copy(this.mesh.rotation);
    }
    const indicator = document.getElementById('rotateIndicator');
    if (indicator) indicator.textContent = 'Auto-rotate OFF';
  }

  animate() {
    requestAnimationFrame(() => this.animate());
    if (this.isAnimating && this.mesh) {
      this.mesh.rotation.y += this.rotationSpeed;
      if (this.wireMesh) this.wireMesh.rotation.copy(this.mesh.rotation);
    }
    this.renderer.render(this.scene, this.camera);
  }

  loadScores(scores) {
    this.loadActivations(scores);
  }

  loadActivations(payload) {
    this.updateColors(payload);
  }
}

window.BrainViewer = BrainViewer;
window.TRIBE_ROI_ATLAS = TRIBE_ROI_ATLAS;
