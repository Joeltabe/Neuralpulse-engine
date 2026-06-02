const BRAIN_REGION_EXPLANATIONS = {
  "L_Visual Cortex": {
    label: "Left Visual Cortex",
    function: "Processes visual information from the right visual field",
    why: "Activated by motion, contrast, color changes, and scene complexity",
    triggered_by: ["Fast-paced scenes", "High contrast visuals", "Multiple scene changes", "Bright colors"],
    impact: "attention",
  },
  "R_Visual Cortex": {
    label: "Right Visual Cortex",
    function: "Processes visual information from the left visual field",
    why: "Responds to visual complexity, motion patterns, and spatial arrangement",
    triggered_by: ["Visual motion", "Scene transitions", "Detailed imagery", "Color variation"],
    impact: "attention",
  },
  "L_Prefrontal": {
    label: "Left Prefrontal Cortex",
    function: "Executive control, decision-making, and cognitive evaluation",
    why: "Engaged when content requires critical thinking, value assessment, or purchase decisions",
    triggered_by: ["Pricing information", "Comparison statements", "Call-to-action", "Risk/benefit analysis"],
    impact: "dopamine",
  },
  "R_Prefrontal": {
    label: "Right Prefrontal Cortex",
    function: "Emotional regulation, reward evaluation, and social cognition",
    why: "Activated by emotionally charged content, social proof, and reward cues",
    triggered_by: ["Emotional appeals", "Social proof", "Reward anticipation", "Status signaling"],
    impact: "dopamine",
  },
  "L_Temporal": {
    label: "Left Temporal Cortex",
    function: "Language comprehension, semantic processing, and memory encoding",
    why: "Engaged by speech, text content, and meaningful narrative structure",
    triggered_by: ["Spoken dialogue", "Text-heavy content", "Storytelling", "Factual information"],
    impact: "memory",
  },
  "R_Temporal": {
    label: "Right Temporal Cortex",
    function: "Facial recognition, emotional prosody, and auditory memory",
    why: "Responsive to tone of voice, music, emotional speech, and familiar faces",
    triggered_by: ["Facial expressions", "Voice tone changes", "Music/rhythm", "Emotional narration"],
    impact: "memory",
  },
  "L_Parietal": {
    label: "Left Parietal Cortex",
    function: "Spatial attention, numerical processing, and sensorimotor integration",
    why: "Activated by spatial layout, number processing, and attention-grabbing visual cues",
    triggered_by: ["Location cues", "Statistical claims", "Arrows/directional cues", "Spatial arrangement"],
    impact: "attention",
  },
  "R_Parietal": {
    label: "Right Parietal Cortex",
    function: "Visuospatial attention, novelty detection, and salience mapping",
    why: "Responds to unexpected stimuli, visual salience, and spatial novelty",
    triggered_by: ["Unexpected visuals", "Novel elements", "Visual pop-out effects", "Salient objects"],
    impact: "attention",
  },
  "L_Motor/Somatosensory": {
    label: "Left Motor/Somatosensory",
    function: "Motor planning and tactile sensation (right body)",
    why: "Mirror neuron activation from observed actions and tactile imagery",
    triggered_by: ["Demonstrations of use", "Tactile language", "Action shots", "Product interaction"],
    impact: "dopamine",
  },
  "R_Motor/Somatosensory": {
    label: "Right Motor/Somatosensory",
    function: "Motor planning and tactile sensation (left body)",
    why: "Engaged by observed movements and embodied language",
    triggered_by: ["Movement demonstrations", "Action verbs", "Physical interaction", "Gesture cues"],
    impact: "dopamine",
  },
  "L_Default Mode": {
    label: "Left Default Mode Network",
    function: "Self-referential thought, autobiographical memory, and social cognition",
    why: "Activated when content relates to personal identity, memories, or social scenarios",
    triggered_by: ["Personal stories", "Relatable scenarios", "Identity appeals", "Nostalgia"],
    impact: "memory",
  },
  "R_Default Mode": {
    label: "Right Default Mode Network",
    function: "Social cognition, empathy, and mental state attribution",
    why: "Engaged by emotionally resonant content, empathy-evoking scenarios, and social bonds",
    triggered_by: ["Emotional stories", "Testimonials", "Community appeals", "Empathy triggers"],
    impact: "memory",
  },
  "L_Other": {
    label: "Left Association Cortex",
    function: "Multimodal integration and higher-order cognition",
    why: "General engagement indicator for complex, multimodal content",
    triggered_by: ["Complex messaging", "Multiple information streams", "Novel concepts"],
    impact: "attention",
  },
  "R_Other": {
    label: "Right Association Cortex",
    function: "Holistic processing and creative cognition",
    why: "Responds to creative content, metaphors, and holistic messaging",
    triggered_by: ["Creative visuals", "Metaphors", "Abstract concepts", "Brand imagery"],
    impact: "dopamine",
  },
};

const BRAIN_COLOR_PALETTE = {
  attention: { low: [0x1a1a2e, 0x16213e], mid: [0x0f3460, 0xe94560], high: [0x533483, 0xff6b6b] },
  dopamine: { low: [0x1a1a2e, 0x16213e], mid: [0x006d77, 0x83c5be], high: [0x219ebc, 0xffb703] },
  memory: { low: [0x1a1a2e, 0x16213e], mid: [0x2d6a4f, 0x52b788], high: [0x40916c, 0x95d5b2] },
};

class BrainViewer {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    if (!this.container) return;
    this.mesh = null;
    this.currentMode = 'attention';
    this.tooltipEl = null;
    this.rotationSpeed = 0.002;
    this.targetRotation = { x: 0.3, y: -0.5 };
    this.currentRotation = { x: 0.3, y: -0.5 };
    this.isAnimating = true;
    this.regionData = [];
    this.currentScores = null;
    this.init();
  }

  init() {
    const rect = this.container.getBoundingClientRect();
    const w = rect.width || 400;
    const h = rect.height || 350;

    this.scene = new THREE.Scene();

    this.camera = new THREE.PerspectiveCamera(35, w / h, 0.1, 10);
    this.camera.position.set(0, 0, 3.2);
    this.camera.lookAt(0, 0, 0);

    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    this.renderer.setSize(w, h);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.setClearColor(0x000000, 0);
    this.container.appendChild(this.renderer.domElement);

    const ambient = new THREE.AmbientLight(0x404060, 0.6);
    this.scene.add(ambient);

    const dirLight = new THREE.DirectionalLight(0xffffff, 1.0);
    dirLight.position.set(1, 1, 2);
    this.scene.add(dirLight);

    const rimLight = new THREE.DirectionalLight(0x8888ff, 0.4);
    rimLight.position.set(-1, -0.5, -1);
    this.scene.add(rimLight);

    this.loadMesh();
    this.setupTooltip();
    this.setupInteraction();
    this.animate();

    const resizeObserver = new ResizeObserver(() => {
      const r = this.container.getBoundingClientRect();
      this.camera.aspect = r.width / r.height;
      this.camera.updateProjectionMatrix();
      this.renderer.setSize(r.width, r.height);
    });
    resizeObserver.observe(this.container);
  }

  loadMesh() {
    fetch('js/brain_mesh.json')
      .then(r => r.json())
      .then(data => this.buildMesh(data))
      .catch(() => {
        this.container.innerHTML = '<div class="brain-error">Could not load brain mesh</div>';
      });
  }

  buildMesh(data) {
    const geo = new THREE.BufferGeometry();
    const verts = data.vertices;
    const faces = data.faces;
    const groupIds = data.group_ids;
    const uniqueGroups = data.unique_groups;

    const positions = new Float32Array(verts.length * 3);
    for (let i = 0; i < verts.length; i++) {
      positions[i * 3] = verts[i][0];
      positions[i * 3 + 1] = verts[i][1];
      positions[i * 3 + 2] = verts[i][2];
    }

    const indices = [];
    for (const f of faces) {
      indices.push(f[0], f[1], f[2]);
    }

    geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geo.setIndex(indices);
    geo.computeVertexNormals();

    // Store per-vertex group
    this.vertexGroups = groupIds;

    // Build region data
    this.regionData = uniqueGroups.map((name, i) => ({
      name,
      index: i,
      explanation: BRAIN_REGION_EXPLANATIONS[name] || {
        label: name,
        function: 'General cortical processing',
        why: 'Engaged during active content processing',
        triggered_by: ['Content engagement'],
        impact: 'attention',
      },
    }));

    // Per-vertex colors (initial: dark blue-purple)
    const colors = new Float32Array(verts.length * 3);
    for (let i = 0; i < verts.length; i++) {
      colors[i * 3] = 0.12;
      colors[i * 3 + 1] = 0.10;
      colors[i * 3 + 2] = 0.22;
    }
    geo.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    const mat = new THREE.MeshPhongMaterial({
      vertexColors: true,
      shininess: 30,
      specular: new THREE.Color(0x222244),
      flatShading: false,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.92,
    });

    this.mesh = new THREE.Mesh(geo, mat);
    this.mesh.rotation.x = this.currentRotation.x;
    this.mesh.rotation.y = this.currentRotation.y;
    this.scene.add(this.mesh);

    // Wireframe overlay for definition
    const wireMat = new THREE.MeshBasicMaterial({
      color: 0x444466,
      wireframe: true,
      transparent: true,
      opacity: 0.08,
    });
    const wireMesh = new THREE.Mesh(geo.clone(), wireMat);
    wireMesh.rotation.x = this.currentRotation.x;
    wireMesh.rotation.y = this.currentRotation.y;
    this.scene.add(wireMesh);
    this.wireMesh = wireMesh;

    if (this.currentScores) {
      this.updateColors(this.currentScores);
    }
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

    this.renderer.domElement.addEventListener('mousedown', (e) => {
      isDragging = false;
      prevMouse.x = e.clientX;
      prevMouse.y = e.clientY;
    });

    this.renderer.domElement.addEventListener('mousemove', (e) => {
      const dx = e.clientX - prevMouse.x;
      const dy = e.clientY - prevMouse.y;
      if (Math.abs(dx) > 3 || Math.abs(dy) > 3) {
        isDragging = true;
        if (this.mesh) {
          this.mesh.rotation.y += dx * 0.005;
          this.mesh.rotation.x += dy * 0.005;
          this.mesh.rotation.x = Math.max(-1, Math.min(1, this.mesh.rotation.x));
        }
        this.hideTooltip();
      }
      prevMouse.x = e.clientX;
      prevMouse.y = e.clientY;

      if (!isDragging && this.mesh) {
        const rect = this.renderer.domElement.getBoundingClientRect();
        mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
        mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
        raycaster.setFromCamera(mouse, this.camera);
        const hits = raycaster.intersectObject(this.mesh);
        if (hits.length > 0) {
          this.renderer.domElement.style.cursor = 'pointer';
          this.showTooltip(hits[0], e.clientX, e.clientY);
        } else {
          this.renderer.domElement.style.cursor = 'default';
          this.hideTooltip();
        }
      }
    });

    this.renderer.domElement.addEventListener('click', () => {
      if (!isDragging) {
        this.isAnimating = !this.isAnimating;
      }
    });

    this.renderer.domElement.addEventListener('mouseleave', () => this.hideTooltip());

    // Touch support for mobile
    let touchStart = { x: 0, y: 0 };
    this.renderer.domElement.addEventListener('touchstart', (e) => {
      const t = e.touches[0];
      touchStart.x = t.clientX;
      touchStart.y = t.clientY;
    });

    this.renderer.domElement.addEventListener('touchmove', (e) => {
      e.preventDefault();
      const t = e.touches[0];
      const dx = t.clientX - touchStart.x;
      const dy = t.clientY - touchStart.y;
      if (this.mesh) {
        this.mesh.rotation.y += dx * 0.005;
        this.mesh.rotation.x += dy * 0.005;
      }
      touchStart.x = t.clientX;
      touchStart.y = t.clientY;
    }, { passive: false });
  }

  showTooltip(hit, x, y) {
    if (!hit.face) return;
    const pos = hit.face.a * 3;
    const colorAttr = this.mesh.geometry.attributes.color;
    if (!colorAttr) return;
    const r = colorAttr.array[pos];
    const g = colorAttr.array[pos + 1];
    const b = colorAttr.array[pos + 2];

    // Find closest region by vertex position
    const vertPos = this.mesh.geometry.attributes.position;
    const vx = vertPos.array[pos];
    const vy = vertPos.array[pos + 1];
    const vz = vertPos.array[pos + 2];

    // Determine which group this vertex belongs to
    const score = Math.max(r, g, b);
    const mode = this.currentMode;
    const intensity = score;

    // Find the region
    const closest = this.findClosestRegion(vx, vy, vz);
    const exp = closest ? closest.explanation : null;

    if (!exp) return;

    const pct = Math.round(intensity * 100);
    const impactColor = intensity > 0.5 ? '#4ade80' : intensity > 0.25 ? '#fbbf24' : '#f87171';

    this.tooltipEl.innerHTML = `
      <div class="brain-tip-header">
        <span class="brain-tip-name">${exp.label}</span>
        <span class="brain-tip-score" style="color:${impactColor}">${pct}%</span>
      </div>
      <div class="brain-tip-section">
        <strong>Function:</strong> ${exp.function}
      </div>
      <div class="brain-tip-section">
        <strong>Why activated:</strong> ${exp.why}
      </div>
      <div class="brain-tip-section">
        <strong>Triggered by:</strong>
        <ul class="brain-tip-triggers">
          ${exp.triggered_by.map(t => `<li>${t}</li>`).join('')}
        </ul>
      </div>
      <div class="brain-tip-footer">
        Affects <strong>${exp.impact.toUpperCase()}</strong> score
      </div>
    `;

    this.tooltipEl.style.display = 'block';
    let tx = x + 15;
    let ty = y - 10;
    const tw = this.tooltipEl.offsetWidth;
    const th = this.tooltipEl.offsetHeight;
    if (tx + tw > window.innerWidth) tx = x - tw - 15;
    if (ty + th > window.innerHeight) ty = window.innerHeight - th - 10;
    if (ty < 10) ty = 10;
    this.tooltipEl.style.left = tx + 'px';
    this.tooltipEl.style.top = ty + 'px';
  }

  findClosestRegion(vx, vy, vz) {
    if (!this.regionData.length) return null;
    const mesh = this.mesh;
    if (!mesh) return null;

    // Use vertex position to determine region
    // Regions are mapped by position in the mesh
    const pos = mesh.geometry.attributes.position;
    let minDist = Infinity;
    let best = this.regionData[0];

    // Sample vertices by group to find closest match
    const groups = {};
    for (let i = 0; i < pos.count; i++) {
      const px = pos.array[i * 3];
      const py = pos.array[i * 3 + 1];
      const pz = pos.array[i * 3 + 2];
      const dist = Math.sqrt((px - vx) ** 2 + (py - vy) ** 2 + (pz - vz) ** 2);
      if (dist < minDist) {
        minDist = dist;
      }
    }

    // Find by checking position-based heuristics
    const hemi = vz < 0 ? 'L' : 'R';
    if (vx > 0.2) {
      const name = `${hemi}_Prefrontal`;
      const found = this.regionData.find(r => r.name === name);
      if (found) return found;
    }
    if (vx < -0.2) {
      const name = `${hemi}_Visual Cortex`;
      const found = this.regionData.find(r => r.name === name);
      if (found) return found;
    }
    if (Math.abs(vy) > 0.35) {
      const name = `${hemi}_Motor/Somatosensory`;
      const found = this.regionData.find(r => r.name === name);
      if (found) return found;
    }
    if (Math.abs(vx) < 0.15 && vy < -0.1) {
      const name = `${hemi}_Default Mode`;
      const found = this.regionData.find(r => r.name === name);
      if (found) return found;
    }
    if (Math.abs(vy) < 0.25 && Math.abs(vz) > 0.2) {
      const name = `${hemi}_Temporal`;
      const found = this.regionData.find(r => r.name === name);
      if (found) return found;
    }
    if (Math.abs(vx) < 0.25 && vy < -0.15) {
      const name = `${hemi}_Parietal`;
      const found = this.regionData.find(r => r.name === name);
      if (found) return found;
    }

    return this.regionData.find(r => r.name.startsWith(hemi)) || best;
  }

  hideTooltip() {
    if (this.tooltipEl) this.tooltipEl.style.display = 'none';
  }

  updateColors(scores) {
    this.currentScores = scores;
    if (!this.mesh) return;

    const colorAttr = this.mesh.geometry.attributes.color;
    const pos = this.mesh.geometry.attributes.position;
    const colors = colorAttr.array;
    const n = pos.count;
    const mode = this.currentMode;

    const getRegionScore = (i) => {
      const px = pos.array[i * 3];
      const py = pos.array[i * 3 + 1];
      const pz = pos.array[i * 3 + 2];

      if (mode === 'attention') {
        if (px < -0.1) return scores.attention * (0.7 + 0.3 * Math.abs(px));
        if (py < -0.15) return scores.attention * 0.85;
        return scores.attention * 0.6;
      } else if (mode === 'dopamine') {
        if (px > 0.1) return scores.dopamine * (0.7 + 0.3 * px);
        if (Math.abs(py) > 0.25) return scores.dopamine * 0.8;
        return scores.dopamine * 0.5;
      } else {
        if (Math.abs(pz) > 0.15) return scores.memory * (0.7 + 0.3 * Math.abs(pz));
        if (py < -0.1) return scores.memory * 0.75;
        return scores.memory * 0.5;
      }
    };

    for (let i = 0; i < n; i++) {
      const score = Math.min(1, Math.max(0, getRegionScore(i)));
      const base = 0.08;
      colors[i * 3] = Math.min(1, base + score * 0.85);
      colors[i * 3 + 1] = Math.min(1, base + score * 0.35);
      colors[i * 3 + 2] = Math.min(1, base + (1 - score) * 0.5);
    }
    colorAttr.needsUpdate = true;
  }

  setMode(mode) {
    this.currentMode = mode;
    if (this.currentScores) {
      this.updateColors(this.currentScores);
    }
  }

  animate() {
    requestAnimationFrame(() => this.animate());

    if (this.isAnimating && this.mesh) {
      this.mesh.rotation.y += this.rotationSpeed;
    }

    if (this.mesh) {
      this.mesh.rotation.x += (this.currentRotation.x - this.mesh.rotation.x) * 0.02;
    }

    this.renderer.render(this.scene, this.camera);
  }
}

window.BrainViewer = BrainViewer;
