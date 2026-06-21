<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import * as THREE from 'three';
  import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
  import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

  let { roiScores = {} as Record<string, number>, mode = 'attention', autoRotate = true } = $props();

  let container: HTMLDivElement;
  let scene: THREE.Scene;
  let camera: THREE.PerspectiveCamera;
  let renderer: THREE.WebGLRenderer;
  let controls: OrbitControls;
  let brainGroup: THREE.Group;
  let animationId: number;
  let clock: THREE.Clock;
  let particles: THREE.Points;
  let isLoading = $state(true);
  let loadError = $state('');
  let hoveredRegion = $state('');

  // Raycaster for hover detection
  let raycaster: THREE.Raycaster;
  let mouse: THREE.Vector2;

  // Region materials map for activation control
  let regionMaterials: Map<string, THREE.ShaderMaterial> = new Map();
  let regionMeshes: Map<string, THREE.Mesh[]> = new Map();

  // Transition state
  let currentActivations: Map<string, number> = new Map();
  let targetActivations: Map<string, number> = new Map();
  let transitionProgress = 1.0;
  const TRANSITION_DURATION = 1.0;

  // Mode-specific rim colors
  const MODE_RIM_COLORS: Record<string, [number, number, number]> = {
    attention: [0.30, 0.42, 0.96],
    dopamine: [0.96, 0.62, 0.07],
    memory: [0.06, 0.73, 0.50]
  };

  // Mode-specific particle colors
  const MODE_PARTICLE_COLORS: Record<string, [number, number, number]> = {
    attention: [0.45, 0.55, 1.0],
    dopamine: [1.0, 0.70, 0.30],
    memory: [0.25, 0.85, 0.60]
  };

  // ================================================================
  // REGION ACTIVATION DEFINITIONS
  // Maps each mode → which GLTF regions activate and how strongly
  // ================================================================
  const REGION_ACTIVATIONS: Record<string, Record<string, number>> = {
    attention: {
      frontal: 0.92,    // FEF, prefrontal engagement
      pariet: 0.88,     // IPS, dorsal attention
      occipit: 0.78,    // V1/V2 visual cortex
      temp: 0.55,       // lateral attention spillover
      corpus: 0.35,     // inter-hemispheric relay
      cereb: 0.30,      // motor coordination
      stem: 0.20,       // arousal baseline
      pitua: 0.15       // minimal
    },
    dopamine: {
      frontal: 0.72,    // vmPFC, OFC reward evaluation
      corpus: 0.85,     // deep reward pathways
      stem: 0.90,       // VTA, substantia nigra
      temp: 0.60,       // emotional valence
      pariet: 0.35,     // sensory integration
      cereb: 0.28,      // motor anticipation
      occipit: 0.25,    // minimal visual
      pitua: 0.45       // hormonal reward response
    },
    memory: {
      temp: 0.95,       // hippocampus, medial temporal
      pariet: 0.82,     // angular gyrus, PCC
      frontal: 0.70,    // DLPFC, working memory
      corpus: 0.55,     // cross-hemispheric consolidation
      occipit: 0.40,    // visual memory encoding
      cereb: 0.30,      // procedural memory
      stem: 0.22,       // arousal modulation
      pitua: 0.18       // stress hormones
    }
  };

  // Region display names for tooltips
  const REGION_NAMES: Record<string, string> = {
    frontal: 'Frontal Lobe',
    temp: 'Temporal Lobe',
    pariet: 'Parietal Lobe',
    occipit: 'Occipital Lobe',
    cereb: 'Cerebellum',
    corpus: 'Corpus Callosum',
    stem: 'Brain Stem',
    pitua: 'Pituitary Gland'
  };

  // Base tissue gray per region (anatomical variation)
  const REGION_BASE_GRAY: Record<string, number> = {
    frontal: 0.62,
    temp: 0.60,
    pariet: 0.63,
    occipit: 0.61,
    cereb: 0.56,
    corpus: 0.72,    // white matter — lighter
    stem: 0.54,
    pitua: 0.58
  };

  // ================================================================
  // fMRI ACTIVATION COLORMAP
  // dark tissue → deep red → orange → bright yellow → white-hot
  // ================================================================
  function activationToColor(activity: number, baseGray: number): THREE.Color {
    if (activity < 0.10) {
      return new THREE.Color(baseGray, baseGray, baseGray * 0.97);
    }
    const t = Math.min(1, (activity - 0.10) / 0.90);
    let r: number, g: number, b: number;

    if (t < 0.25) {
      const k = t / 0.25;
      r = baseGray + k * (0.55 - baseGray);
      g = baseGray * (1 - k * 0.7);
      b = baseGray * (1 - k * 0.85);
    } else if (t < 0.5) {
      const k = (t - 0.25) / 0.25;
      r = 0.55 + k * 0.45;
      g = baseGray * 0.3 + k * 0.45;
      b = baseGray * 0.15 * (1 - k);
    } else if (t < 0.75) {
      const k = (t - 0.5) / 0.25;
      r = 1.0;
      g = 0.45 + k * 0.45;
      b = k * 0.1;
    } else {
      const k = (t - 0.75) / 0.25;
      r = 1.0;
      g = 0.9 + k * 0.1;
      b = 0.1 + k * 0.55;
    }
    return new THREE.Color(Math.min(1, r), Math.min(1, g), Math.min(1, b));
  }

  // ================================================================
  // CREATE REGION SHADER MATERIAL
  // Custom per-region material with fMRI heatmap + rim + SSS
  // ================================================================
  function createRegionMaterial(regionName: string): THREE.ShaderMaterial {
    const baseGray = REGION_BASE_GRAY[regionName] ?? 0.60;
    const rimColor = MODE_RIM_COLORS[mode] ?? MODE_RIM_COLORS.attention;
    const activation = currentActivations.get(regionName) ?? 0;
    const color = activationToColor(activation, baseGray);

    return new THREE.ShaderMaterial({
      uniforms: {
        uBaseColor: { value: new THREE.Vector3(color.r, color.g, color.b) },
        uRimColor: { value: new THREE.Vector3(...rimColor) },
        uRimPower: { value: 2.8 },
        uTime: { value: 0.0 },
        uActivation: { value: activation },
        uHovered: { value: 0.0 },
        uBaseGray: { value: baseGray },
        lightDir: { value: new THREE.Vector3(0.5, 0.8, 0.6).normalize() },
        lightDir2: { value: new THREE.Vector3(-0.4, -0.2, -0.8).normalize() }
      },
      vertexShader: `
        varying vec3 vNormal;
        varying vec3 vPosition;
        varying vec3 vWorldPosition;
        void main() {
          vNormal = normalize(normalMatrix * normal);
          vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
          vPosition = mvPosition.xyz;
          vWorldPosition = (modelMatrix * vec4(position, 1.0)).xyz;
          gl_Position = projectionMatrix * mvPosition;
        }
      `,
      fragmentShader: `
        uniform vec3 uBaseColor;
        uniform vec3 uRimColor;
        uniform float uRimPower;
        uniform float uTime;
        uniform float uActivation;
        uniform float uHovered;
        uniform float uBaseGray;
        uniform vec3 lightDir;
        uniform vec3 lightDir2;
        varying vec3 vNormal;
        varying vec3 vPosition;
        varying vec3 vWorldPosition;

        void main() {
          vec3 normal = normalize(vNormal);
          vec3 viewDir = normalize(-vPosition);

          // Diffuse lighting (two-light rig)
          float diff1 = max(dot(normal, lightDir), 0.0);
          float diff2 = max(dot(normal, lightDir2), 0.0) * 0.35;
          float diffuse = diff1 + diff2;

          // Specular highlights (wet tissue sheen)
          vec3 halfDir = normalize(lightDir + viewDir);
          float spec = pow(max(dot(normal, halfDir), 0.0), 40.0) * 0.35;
          vec3 halfDir2 = normalize(lightDir2 + viewDir);
          float spec2 = pow(max(dot(normal, halfDir2), 0.0), 30.0) * 0.12;

          // Subsurface Scattering approximation
          float sssWrap = max(0.0, dot(normal, -lightDir) * 0.5 + 0.5);
          vec3 sssColor = vec3(0.85, 0.45, 0.35) * sssWrap * 0.12 * uActivation;

          // Rim / Fresnel glow
          float fresnel = pow(1.0 - abs(dot(normal, viewDir)), uRimPower);
          vec3 rimContrib = uRimColor * fresnel * (0.35 + uActivation * 0.35);

          // Pulsing emission on active regions
          float pulse = sin(uTime * 2.0 + uActivation * 5.0) * 0.08 + sin(uTime * 3.5) * 0.04;
          float emissive = uActivation * (0.12 + pulse * uActivation);

          // Hover highlight
          float hoverGlow = uHovered * 0.18;

          // Combine
          vec3 litColor = uBaseColor * (0.28 + diffuse * 0.72);
          litColor += sssColor;
          litColor += vec3(spec + spec2) * vec3(1.0, 0.95, 0.9);
          litColor += rimContrib;
          litColor += uBaseColor * emissive;
          litColor += vec3(hoverGlow) * uRimColor;

          // Slight warm tint
          litColor *= vec3(1.02, 1.0, 0.97);

          gl_FragColor = vec4(litColor, 0.97);
        }
      `,
      side: THREE.FrontSide,
      transparent: true
    });
  }

  // ================================================================
  // UPDATE REGION ACTIVATIONS
  // ================================================================
  function getActivationsForMode(targetMode: string): Map<string, number> {
    const activations = new Map<string, number>();
    const modeData = REGION_ACTIVATIONS[targetMode] || REGION_ACTIVATIONS.attention;
    for (const [region, value] of Object.entries(modeData)) {
      // Factor in roiScores if provided
      const scoreKey = REGION_NAMES[region]?.split(' ')[0]?.toLowerCase() ?? region;
      const externalScore = roiScores[scoreKey] ?? roiScores[region];
      const finalValue = externalScore !== undefined ? (value * 0.6 + externalScore * 0.4) : value;
      activations.set(region, finalValue);
    }
    return activations;
  }

  function applyActivations(immediate = false) {
    const newTarget = getActivationsForMode(mode);
    const rimColor = MODE_RIM_COLORS[mode] ?? MODE_RIM_COLORS.attention;

    if (immediate || currentActivations.size === 0) {
      currentActivations = new Map(newTarget);
      targetActivations = new Map(newTarget);
      transitionProgress = 1.0;
    } else {
      targetActivations = newTarget;
      transitionProgress = 0.0;
    }

    // Update rim color on all materials
    regionMaterials.forEach((mat) => {
      mat.uniforms.uRimColor.value.set(rimColor[0], rimColor[1], rimColor[2]);
    });

    // If immediate, update colors now
    if (immediate) {
      updateMaterialColors();
    }
  }

  function updateMaterialColors() {
    regionMaterials.forEach((mat, region) => {
      const activation = currentActivations.get(region) ?? 0;
      const baseGray = REGION_BASE_GRAY[region] ?? 0.60;
      const color = activationToColor(activation, baseGray);
      mat.uniforms.uBaseColor.value.set(color.r, color.g, color.b);
      mat.uniforms.uActivation.value = activation;
    });
  }

  function updateTransition(deltaTime: number) {
    if (transitionProgress >= 1.0) return;
    transitionProgress += deltaTime / TRANSITION_DURATION;
    if (transitionProgress > 1.0) transitionProgress = 1.0;

    // Smooth ease-in-out
    const t = transitionProgress < 0.5
      ? 2 * transitionProgress * transitionProgress
      : 1 - Math.pow(-2 * transitionProgress + 2, 2) / 2;

    // Interpolate activations
    targetActivations.forEach((target, region) => {
      const current = currentActivations.get(region) ?? 0;
      const interpolated = current + (target - current) * t;
      currentActivations.set(region, interpolated);
    });

    updateMaterialColors();

    if (transitionProgress >= 1.0) {
      currentActivations = new Map(targetActivations);
    }
  }

  // ================================================================
  // NEURAL PARTICLES
  // ================================================================
  function createParticles(): THREE.Points {
    const count = 280;
    const positions = new Float32Array(count * 3);
    const sizes = new Float32Array(count);
    const alphas = new Float32Array(count);

    for (let i = 0; i < count; i++) {
      const r = 4.0 + Math.random() * 3.5;
      const t = Math.random() * Math.PI * 2;
      const p = Math.acos(2 * Math.random() - 1);
      positions[i * 3 + 0] = r * Math.sin(p) * Math.cos(t);
      positions[i * 3 + 1] = r * Math.sin(p) * Math.sin(t) * 0.75;
      positions[i * 3 + 2] = r * Math.cos(p);
      sizes[i] = 1.5 + Math.random() * 3.5;
      alphas[i] = Math.random();
    }

    const geom = new THREE.BufferGeometry();
    geom.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geom.setAttribute('size', new THREE.BufferAttribute(sizes, 1));
    geom.setAttribute('alpha', new THREE.BufferAttribute(alphas, 1));

    const mat = new THREE.ShaderMaterial({
      uniforms: {
        uTime: { value: 0.0 },
        uColor: { value: new THREE.Vector3(...MODE_PARTICLE_COLORS[mode]) }
      },
      vertexShader: `
        attribute float size;
        attribute float alpha;
        varying float vAlpha;
        uniform float uTime;
        void main() {
          vAlpha = alpha;
          vec3 pos = position;
          pos.x += sin(uTime * 0.3 + alpha * 6.28) * 0.15;
          pos.y += cos(uTime * 0.25 + alpha * 4.0) * 0.12;
          pos.z += sin(uTime * 0.2 + alpha * 5.0) * 0.13;
          vec4 mvPosition = modelViewMatrix * vec4(pos, 1.0);
          gl_Position = projectionMatrix * mvPosition;
          gl_PointSize = size * (250.0 / -mvPosition.z);
        }
      `,
      fragmentShader: `
        uniform vec3 uColor;
        varying float vAlpha;
        uniform float uTime;
        void main() {
          float d = length(gl_PointCoord - vec2(0.5));
          if (d > 0.5) discard;
          float a = smoothstep(0.5, 0.0, d);
          float twinkle = sin(uTime * 2.0 + vAlpha * 20.0) * 0.3 + 0.7;
          gl_FragColor = vec4(uColor, a * 0.15 * twinkle);
        }
      `,
      transparent: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending
    });

    return new THREE.Points(geom, mat);
  }

  // ================================================================
  // HOVER DETECTION
  // ================================================================
  function onMouseMove(event: MouseEvent) {
    if (!container || !raycaster || !camera || !brainGroup) return;
    const rect = container.getBoundingClientRect();
    mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

    raycaster.setFromCamera(mouse, camera);
    const allMeshes: THREE.Mesh[] = [];
    regionMeshes.forEach((meshes) => allMeshes.push(...meshes));
    const intersects = raycaster.intersectObjects(allMeshes, false);

    // Reset all hover states
    regionMaterials.forEach((mat) => {
      mat.uniforms.uHovered.value = 0.0;
    });
    hoveredRegion = '';

    if (intersects.length > 0) {
      const hit = intersects[0].object;
      // Find which region this mesh belongs to
      for (const [region, meshes] of regionMeshes.entries()) {
        if (meshes.includes(hit as THREE.Mesh)) {
          hoveredRegion = region;
          const mat = regionMaterials.get(region);
          if (mat) mat.uniforms.uHovered.value = 1.0;
          break;
        }
      }
    }
  }

  // ================================================================
  // GLTF LOADING & SCENE SETUP
  // ================================================================
  onMount(() => {
    if (!container) return;

    clock = new THREE.Clock();
    raycaster = new THREE.Raycaster();
    mouse = new THREE.Vector2();

    scene = new THREE.Scene();
    camera = new THREE.PerspectiveCamera(38, container.clientWidth / container.clientHeight, 0.1, 200);
    camera.position.set(8, 5, 8);
    camera.lookAt(0, 0, 0);

    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(0x000000, 0);
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.15;
    container.appendChild(renderer.domElement);

    controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.06;
    controls.autoRotate = autoRotate;
    controls.autoRotateSpeed = 1.0;
    controls.minDistance = 5;
    controls.maxDistance = 20;
    controls.enablePan = false;
    controls.target.set(0, 1, 0);

    // ===== CINEMATIC 3-POINT LIGHTING =====
    const keyLight = new THREE.DirectionalLight(0xfff6ec, 1.2);
    keyLight.position.set(8, 12, 10);
    scene.add(keyLight);

    const fillLight = new THREE.DirectionalLight(0x8899bb, 0.45);
    fillLight.position.set(-6, -3, -5);
    scene.add(fillLight);

    const backLight = new THREE.DirectionalLight(0xaaccff, 0.65);
    backLight.position.set(-4, 5, -10);
    scene.add(backLight);

    const ambient = new THREE.AmbientLight(0x40383a, 0.38);
    scene.add(ambient);

    const hemi = new THREE.HemisphereLight(0xeef2ff, 0x201818, 0.45);
    scene.add(hemi);

    const camLight = new THREE.PointLight(0xffffff, 0.25, 50);
    camera.add(camLight);
    scene.add(camera);

    // ===== LOAD GLTF =====
    const loader = new GLTFLoader();
    loader.load(
      '/brain/scene.gltf',
      (gltf) => {
        brainGroup = gltf.scene;

        // Known region node names from the GLTF
        const knownRegions = ['pitua', 'temp', 'pariet', 'stem', 'occipit', 'frontal', 'corpus', 'cereb'];

        // Initialize activations for current mode
        currentActivations = getActivationsForMode(mode);
        targetActivations = new Map(currentActivations);

        // Traverse and apply custom materials per region
        brainGroup.traverse((child) => {
          if (child instanceof THREE.Mesh) {
            // Find which region this mesh belongs to by walking up the hierarchy
            let regionName = '';
            let current: THREE.Object3D | null = child;
            while (current) {
              const name = current.name?.toLowerCase() ?? '';
              for (const region of knownRegions) {
                if (name === region || name.includes(region)) {
                  regionName = region;
                  break;
                }
              }
              if (regionName) break;
              current = current.parent;
            }

            if (regionName) {
              // Ensure normals exist
              if (!child.geometry.getAttribute('normal')) {
                child.geometry.computeVertexNormals();
              }

              const mat = createRegionMaterial(regionName);
              child.material = mat;
              regionMaterials.set(regionName, mat);

              // Track meshes per region
              if (!regionMeshes.has(regionName)) {
                regionMeshes.set(regionName, []);
              }
              regionMeshes.get(regionName)!.push(child);
            } else {
              // Default material for unknown parts (edge lines, etc.)
              const defaultMat = new THREE.MeshStandardMaterial({
                color: 0x808080,
                metalness: 0.0,
                roughness: 0.6,
                transparent: true,
                opacity: 0.4
              });
              child.material = defaultMat;
            }
          }
        });

        // Apply initial activation colors
        updateMaterialColors();

        scene.add(brainGroup);
        isLoading = false;
      },
      (progress) => {
        // Loading progress
        const pct = progress.total > 0 ? Math.round((progress.loaded / progress.total) * 100) : 0;
        // Could display progress if desired
      },
      (error) => {
        console.error('Failed to load brain GLTF:', error);
        loadError = 'Failed to load brain model';
        isLoading = false;
      }
    );

    // Create ambient particles
    particles = createParticles();
    scene.add(particles);

    // Mouse hover listener
    container.addEventListener('mousemove', onMouseMove);

    // Animation loop
    function animate() {
      animationId = requestAnimationFrame(animate);
      const delta = clock.getDelta();
      const elapsed = clock.getElapsedTime();

      controls.update();

      // Smooth mode transition
      updateTransition(delta);

      // Update pulsing on materials
      regionMaterials.forEach((mat) => {
        mat.uniforms.uTime.value = elapsed;
      });

      // Update particle time + color
      if (particles) {
        const pMat = particles.material as THREE.ShaderMaterial;
        pMat.uniforms.uTime.value = elapsed;
        const pc = MODE_PARTICLE_COLORS[mode] || MODE_PARTICLE_COLORS.attention;
        pMat.uniforms.uColor.value.set(pc[0], pc[1], pc[2]);
      }

      renderer.render(scene, camera);
    }
    animate();

    const resize = () => {
      const w = container.clientWidth;
      const h = container.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener('resize', resize);

    return () => {
      window.removeEventListener('resize', resize);
      container?.removeEventListener('mousemove', onMouseMove);
    };
  });

  $effect(() => {
    if (mode && regionMaterials.size > 0) {
      applyActivations(false);
    }
    if (controls) controls.autoRotate = autoRotate;
  });

  onDestroy(() => {
    if (animationId) cancelAnimationFrame(animationId);
    controls?.dispose();
    renderer?.dispose();
    if (container && renderer?.domElement) container.removeChild(renderer.domElement);
  });
</script>

<div class="brain-viewer-wrap">
  <div bind:this={container} class="w-full h-full rounded-2xl overflow-hidden relative">
    {#if isLoading}
      <div class="loading-overlay">
        <div class="loading-brain">
          <div class="brain-pulse-ring"></div>
          <div class="brain-pulse-ring delay-1"></div>
          <div class="brain-pulse-ring delay-2"></div>
          <svg class="brain-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2">
            <path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
        <p class="loading-text">Loading Neural Architecture<span class="loading-dots"></span></p>
      </div>
    {/if}

    {#if loadError}
      <div class="error-overlay">
        <p class="error-text">{loadError}</p>
      </div>
    {/if}

    {#if hoveredRegion}
      <div class="region-tooltip">
        <span class="tooltip-dot" style="background: {MODE_RIM_COLORS[mode] ? `rgb(${MODE_RIM_COLORS[mode].map(v => Math.round(v*255)).join(',')})` : '#fff'}"></span>
        <span class="tooltip-name">{REGION_NAMES[hoveredRegion] || hoveredRegion}</span>
        <span class="tooltip-score">{Math.round((currentActivations.get(hoveredRegion) ?? 0) * 100)}%</span>
      </div>
    {/if}
  </div>
</div>

<style>
  .brain-viewer-wrap {
    width: 100%;
    height: 100%;
    position: relative;
  }

  /* ===== LOADING OVERLAY ===== */
  .loading-overlay {
    position: absolute;
    inset: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    z-index: 20;
    background: radial-gradient(ellipse at center, rgba(10, 10, 20, 0.85) 0%, rgba(5, 5, 12, 0.95) 100%);
    backdrop-filter: blur(8px);
    border-radius: 1rem;
  }

  .loading-brain {
    position: relative;
    width: 80px;
    height: 80px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 1.5rem;
  }

  .brain-icon {
    width: 36px;
    height: 36px;
    color: rgba(255, 255, 255, 0.6);
    animation: float-icon 2s ease-in-out infinite;
  }

  .brain-pulse-ring {
    position: absolute;
    inset: 0;
    border-radius: 50%;
    border: 1.5px solid rgba(77, 108, 245, 0.3);
    animation: pulse-ring 2s ease-out infinite;
  }

  .brain-pulse-ring.delay-1 {
    animation-delay: 0.5s;
    border-color: rgba(245, 158, 11, 0.3);
  }

  .brain-pulse-ring.delay-2 {
    animation-delay: 1.0s;
    border-color: rgba(16, 185, 129, 0.3);
  }

  .loading-text {
    font-size: 0.8rem;
    color: rgba(255, 255, 255, 0.45);
    font-weight: 500;
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }

  .loading-dots::after {
    content: '';
    animation: dots 1.5s steps(4, end) infinite;
  }

  @keyframes dots {
    0% { content: ''; }
    25% { content: '.'; }
    50% { content: '..'; }
    75% { content: '...'; }
  }

  @keyframes pulse-ring {
    0% { transform: scale(0.6); opacity: 0.6; }
    100% { transform: scale(1.5); opacity: 0; }
  }

  @keyframes float-icon {
    0%, 100% { transform: translateY(0px); }
    50% { transform: translateY(-6px); }
  }

  /* ===== ERROR OVERLAY ===== */
  .error-overlay {
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 20;
    background: rgba(10, 10, 20, 0.9);
    border-radius: 1rem;
  }

  .error-text {
    color: rgba(239, 68, 68, 0.8);
    font-size: 0.85rem;
    font-weight: 500;
  }

  /* ===== REGION TOOLTIP ===== */
  .region-tooltip {
    position: absolute;
    bottom: 1rem;
    left: 50%;
    transform: translateX(-50%);
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.4rem 0.9rem;
    background: rgba(0, 0, 0, 0.55);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 0.6rem;
    z-index: 15;
    pointer-events: none;
    animation: tooltip-in 0.2s ease-out;
  }

  .tooltip-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    box-shadow: 0 0 6px currentColor;
  }

  .tooltip-name {
    font-size: 0.75rem;
    font-weight: 600;
    color: rgba(255, 255, 255, 0.85);
  }

  .tooltip-score {
    font-size: 0.7rem;
    color: rgba(255, 255, 255, 0.45);
    font-variant-numeric: tabular-nums;
  }

  @keyframes tooltip-in {
    from { opacity: 0; transform: translateX(-50%) translateY(4px); }
    to { opacity: 1; transform: translateX(-50%) translateY(0); }
  }
</style>