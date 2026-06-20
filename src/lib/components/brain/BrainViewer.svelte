<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import * as THREE from 'three';
  import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

  let { roiScores = {} as Record<string, number>, mode = 'attention', autoRotate = true } = $props();

  let container: HTMLDivElement;
  let scene: THREE.Scene;
  let camera: THREE.PerspectiveCamera;
  let renderer: THREE.WebGLRenderer;
  let controls: OrbitControls;
  let brain: THREE.Group;
  let brainMesh: THREE.Mesh;
  let brainGeom: THREE.BufferGeometry;
  let animationId: number;
  let clock: THREE.Clock;
  let particles: THREE.Points;
  let rimShaderMaterial: THREE.ShaderMaterial;

  // For smooth mode transitions
  let previousColors: Float32Array | null = null;
  let targetColors: Float32Array | null = null;
  let transitionProgress = 1.0;
  const TRANSITION_DURATION = 0.8; // seconds

  const ROIS = {
    attention: { rois: ['V1', 'V2', 'V3', 'MT', 'IPS', 'FEF'], color: 0xffb020, label: 'Attention' },
    dopamine: { rois: ['VS', 'NAcc', 'vmPFC', 'SN', 'VTA'], color: 0xff8c1a, label: 'Dopamine' },
    memory: { rois: ['HIP', 'PHC', 'PRC', 'ERC', 'ANG', 'PCC', 'DLPFC'], color: 0xffd23f, label: 'Memory' }
  };

  // Mode-specific rim colors for visual feedback
  const MODE_RIM_COLORS: Record<string, [number, number, number]> = {
    attention: [0.35, 0.5, 1.0],    // blue-tinted rim
    dopamine: [1.0, 0.65, 0.25],    // amber rim
    memory: [0.2, 0.85, 0.55]       // green-tinted rim
  };

  // ---- Enhanced fMRI-style activation colormap ----
  // dark tissue → deep red → orange → bright yellow → white-hot core
  function activationColor(activity: number, baseGray: number): [number, number, number] {
    if (activity < 0.10) {
      return [baseGray, baseGray, baseGray * 0.97];
    }
    const t = Math.min(1, (activity - 0.10) / 0.90);

    let r: number, g: number, b: number;
    if (t < 0.25) {
      // dark tissue → deep red (threshold activation)
      const k = t / 0.25;
      r = baseGray + k * (0.55 - baseGray);
      g = baseGray * (1 - k * 0.7);
      b = baseGray * (1 - k * 0.85);
    } else if (t < 0.5) {
      // deep red → orange
      const k = (t - 0.25) / 0.25;
      r = 0.55 + k * 0.45;
      g = baseGray * 0.3 + k * 0.45;
      b = baseGray * 0.15 * (1 - k);
    } else if (t < 0.75) {
      // orange → bright yellow
      const k = (t - 0.5) / 0.25;
      r = 1.0;
      g = 0.45 + k * 0.45;
      b = k * 0.1;
    } else {
      // bright yellow → white-hot core
      const k = (t - 0.75) / 0.25;
      r = 1.0;
      g = 0.9 + k * 0.1;
      b = 0.1 + k * 0.55;
    }
    return [Math.min(1, r), Math.min(1, g), Math.min(1, b)];
  }

  // ================================================================
  // 3D VALUE NOISE — smooth, non-periodic, organic variation
  // ================================================================
  function hash3(ix: number, iy: number, iz: number): number {
    // Sine-based hash avoids precision overflow issues in JS bitwise ops
    const dot = ix * 12.9898 + iy * 78.233 + iz * 151.7182;
    const n = Math.sin(dot) * 43758.5453;
    return n - Math.floor(n);
  }

  function smoothstep(t: number): number {
    // Improved smootherstep for C2 continuous noise
    return t * t * t * (t * (t * 6 - 15) + 10);
  }

  function lerp(a: number, b: number, t: number): number {
    return a + (b - a) * t;
  }

  function noise3d(x: number, y: number, z: number): number {
    const ix = Math.floor(x), iy = Math.floor(y), iz = Math.floor(z);
    const fx = x - ix, fy = y - iy, fz = z - iz;
    const ux = smoothstep(fx), uy = smoothstep(fy), uz = smoothstep(fz);

    const v000 = hash3(ix, iy, iz) * 2 - 1;
    const v100 = hash3(ix + 1, iy, iz) * 2 - 1;
    const v010 = hash3(ix, iy + 1, iz) * 2 - 1;
    const v110 = hash3(ix + 1, iy + 1, iz) * 2 - 1;
    const v001 = hash3(ix, iy, iz + 1) * 2 - 1;
    const v101 = hash3(ix + 1, iy, iz + 1) * 2 - 1;
    const v011 = hash3(ix, iy + 1, iz + 1) * 2 - 1;
    const v111 = hash3(ix + 1, iy + 1, iz + 1) * 2 - 1;

    return lerp(
      lerp(lerp(v000, v100, ux), lerp(v010, v110, ux), uy),
      lerp(lerp(v001, v101, ux), lerp(v011, v111, ux), uy),
      uz
    );
  }

  // RIDGE NOISE: creates sharp narrow valleys + wide rounded ridges
  // This is what makes folds look like brain gyri instead of sine bumps
  function ridgeNoise(x: number, y: number, z: number): number {
    return 1.0 - Math.abs(noise3d(x, y, z));
  }

  // FBM with ridge noise — multi-scale organic brain folding
  function brainFolds(x: number, y: number, z: number, octaves: number): number {
    let value = 0;
    let amplitude = 1.0;
    let frequency = 1.0;
    let weight = 1.0;
    let totalAmp = 0;

    for (let i = 0; i < octaves; i++) {
      const n = ridgeNoise(x * frequency, y * frequency, z * frequency);
      // Weight successive octaves by the previous ridge value
      // so detail accumulates in the valley floors (sulci)
      const signal = n * n * weight;
      weight = Math.min(1, n);
      value += signal * amplitude;
      totalAmp += amplitude;
      amplitude *= 0.5;
      frequency *= 2.1;
    }
    return value / totalAmp;
  }

  // Simple hash for per-vertex color jitter
  function hashNoise(x: number, y: number, z: number): number {
    const n = Math.sin(x * 127.1 + y * 311.7 + z * 74.7) * 43758.5453;
    return n - Math.floor(n);
  }

  // ================================================================
  // BUILD THE BRAIN MESH
  // ================================================================
  function createBrainMesh(): THREE.Group {
    const group = new THREE.Group();

    // --- Icosahedron subdivision for smooth base sphere ---
    const PHI = (1.0 + Math.sqrt(5.0)) / 2.0;
    let verts: number[][] = [
      [-1, PHI, 0], [1, PHI, 0], [-1, -PHI, 0], [1, -PHI, 0],
      [0, -1, PHI], [0, 1, PHI], [0, -1, -PHI], [0, 1, -PHI],
      [PHI, 0, -1], [PHI, 0, 1], [-PHI, 0, -1], [-PHI, 0, 1]
    ];
    let faces: number[][] = [
      [0,11,5],[0,5,1],[0,1,7],[0,7,10],[0,10,11],
      [1,5,9],[5,11,4],[11,10,2],[10,7,6],[7,1,8],
      [3,9,4],[3,4,2],[3,2,6],[3,6,8],[3,8,9],
      [4,9,5],[2,4,11],[6,2,10],[8,6,7],[9,8,1]
    ];

    function subdivide(vs: number[][], fs: number[][]) {
      const newVerts = vs.slice();
      const midCache = new Map<string, number>();
      function getMid(i: number, j: number) {
        const key = i < j ? `${i}_${j}` : `${j}_${i}`;
        if (!midCache.has(key)) {
          const a = newVerts[i], b = newVerts[j];
          const p = [(a[0]+b[0])/2, (a[1]+b[1])/2, (a[2]+b[2])/2];
          const len = Math.hypot(p[0], p[1], p[2]) || 1;
          p[0]/=len; p[1]/=len; p[2]/=len;
          midCache.set(key, newVerts.push(p) - 1);
        }
        return midCache.get(key) as number;
      }
      const newFaces: number[][] = [];
      for (const f of fs) {
        const ab = getMid(f[0], f[1]);
        const bc = getMid(f[1], f[2]);
        const ca = getMid(f[2], f[0]);
        newFaces.push([f[0],ab,ca],[f[1],bc,ab],[f[2],ca,bc],[ab,bc,ca]);
      }
      return [newVerts, newFaces] as const;
    }

    // 6 subdivisions → ~40K tris → extremely high resolution for deep fold detail
    for (let i = 0; i < 6; i++) {
      const res = subdivide(verts, faces);
      verts = res[0]; faces = res[1];
    }

    // ================================================================
    // VERTEX DEFORMATION — build anatomical brain shape
    // ================================================================
    const positions: number[] = [];
    const baseGrays: number[] = [];
    const aoValues: number[] = [];
    const regionCoords: number[] = [];

    // Real brain proportions: more spherical, slightly longer front-to-back
    const SX = 0.88;   // left-right width
    const SY = 0.78;   // top-bottom height
    const SZ = 0.98;   // front-back length

    // Noise sampling scale — controls how many folds fit on the surface.
    const FOLD_SCALE = 3.0;    // Fewer, larger folds
    const FOLD_DEPTH = 0.12;   // Deep, dramatic crevices

    for (let i = 0; i < verts.length; i++) {
      let [ux, uy, uz] = verts[i];
      let norm = Math.hypot(ux, uy, uz) || 1;
      ux /= norm; uy /= norm; uz /= norm;

      const theta = Math.atan2(uz, ux);        // azimuth (longitude)
      const elev  = Math.asin(Math.max(-1, Math.min(1, uy))); // elevation

      // ----------------------------------------------------------
      // 1. BASE ELLIPSOID
      // ----------------------------------------------------------
      let rx = ux * SX;
      let ry = uy * SY;
      let rz = uz * SZ;

      // Flatten the underside (brains sit on a flat skull base)
      if (uy < 0) {
        const flatMask = 1.0 - Math.abs(uy);  // strongest near equator
        ry *= (1.0 - 0.30 * flatMask);
      }

      // Forward tilt — frontal slightly higher than occipital
      ry += uz * 0.04;

      // ----------------------------------------------------------
      // 2. LONGITUDINAL FISSURE (deep midline split)
      // ----------------------------------------------------------
      const fissW = 0.07;
      const fissTopMask = Math.max(0, uy + 0.15);  // deep on top, fades at bottom
      const fissGauss = Math.exp(-(ux * ux) / (2 * fissW * fissW));
      const fissDepth = 0.14 * fissGauss * fissTopMask;
      ry -= fissDepth;
      // Separate hemispheres laterally
      const xSign = ux >= 0 ? 1 : -1;
      rx += xSign * fissGauss * fissDepth * 0.5;

      // ----------------------------------------------------------
      // 3. TEMPORAL LOBES — bilateral bulges on each side
      // ----------------------------------------------------------
      const tempBulge = 0.14
        * Math.exp(-((elev + 0.25) ** 2) / 0.08)
        * Math.exp(-(theta ** 2) / 0.7)
        * Math.max(0, Math.abs(ux) * 1.6 - 0.15);
      rx += xSign * tempBulge * 0.9;
      ry -= tempBulge * 0.25;

      // ----------------------------------------------------------
      // 4. FRONTAL LOBE — rounded forward prominence
      // ----------------------------------------------------------
      const frontal = 0.10
        * Math.exp(-((theta + Math.PI * 0.5) ** 2) / 0.35)
        * Math.exp(-((elev - 0.08) ** 2) / 0.35);
      rz -= frontal;
      ry += frontal * 0.08 * Math.max(0, uy);

      // ----------------------------------------------------------
      // 5. OCCIPITAL LOBE — posterior bulge
      // ----------------------------------------------------------
      const occipital = 0.07
        * Math.exp(-((theta - Math.PI * 0.5) ** 2) / 0.25)
        * Math.exp(-(elev ** 2) / 0.35);
      rz += occipital;
      ry -= 0.03 * Math.exp(-((theta - Math.PI * 0.5) ** 2) / 0.2) * Math.max(0, -uy);

      // ----------------------------------------------------------
      // 6. CEREBELLUM — tight compact bump at back-bottom
      // ----------------------------------------------------------
      const cerebMask = Math.exp(-((theta - Math.PI * 0.5) ** 2) / 0.09)
                      * Math.exp(-((elev + 0.58) ** 2) / 0.05);
      const cerebBulge = 0.11 * cerebMask;
      rz += cerebBulge;
      ry -= cerebBulge * 0.25;
      // Tight horizontal folia (many fine ridges)
      const foliaDepth = 0.006 * Math.sin(40 * elev) * Math.min(1, cerebMask / 0.02);
      const cbr = Math.hypot(rx, ry, rz) || 1;
      rx += (rx / cbr) * foliaDepth;
      ry += (ry / cbr) * foliaDepth;
      rz += (rz / cbr) * foliaDepth;

      // ----------------------------------------------------------
      // 7. PARIETAL DOME — slight bilateral upper bulge
      // ----------------------------------------------------------
      const parietal = 0.04
        * Math.exp(-((theta - 0.2) ** 2) / 0.4)
        * Math.exp(-((elev - 0.5) ** 2) / 0.12)
        * Math.max(0.15, Math.abs(ux));
      ry += parietal;

      // ----------------------------------------------------------
      // 8. SYLVIAN FISSURE — separates temporal from frontal/parietal
      // ----------------------------------------------------------
      const sylvElev = elev + 0.08;
      const sylvDepth = 0.028
        * Math.exp(-(sylvElev * sylvElev) / 0.009)
        * Math.min(1, Math.max(0, Math.abs(ux) - 0.18) * 3.5)
        * Math.exp(-((theta - xSign * 0.15) ** 2) / 1.2);
      const sr = Math.hypot(rx, ry, rz) || 1;
      rx -= (rx / sr) * sylvDepth;
      ry -= (ry / sr) * sylvDepth;
      rz -= (rz / sr) * sylvDepth;

      // ----------------------------------------------------------
      // 9. CENTRAL SULCUS
      // ----------------------------------------------------------
      const centDepth = 0.018
        * Math.exp(-((theta + Math.PI * 0.1) ** 2) / 0.013)
        * Math.max(0, uy * 0.8 + 0.1)
        * Math.max(0.2, Math.abs(ux));
      const cr = Math.hypot(rx, ry, rz) || 1;
      rx -= (rx / cr) * centDepth;
      ry -= (ry / cr) * centDepth;
      rz -= (rz / cr) * centDepth;

      // ----------------------------------------------------------
      // 10. CORTICAL FOLDS — ridge noise for realistic gyri/sulci
      // ----------------------------------------------------------
      const foldVal = brainFolds(
        rx * FOLD_SCALE + 1.3,
        ry * FOLD_SCALE + 2.7,
        rz * FOLD_SCALE + 0.5,
        5  // 5 octaves for fine detail inside the folds
      );
      // Center at 0.7 to bias displacement inward, creating deep sulci
      const foldDisp = (foldVal - 0.7) * FOLD_DEPTH;

      // Suppress folds on cerebellum (it has its own folia pattern)
      const foldMask = 1.0 - Math.min(1, cerebMask / 0.04);

      // Apply displacement RADIALLY so silhouette stays clean
      const rr = Math.hypot(rx, ry, rz) || 1;
      const radialDisp = foldDisp * foldMask;
      rx += (rx / rr) * radialDisp;
      ry += (ry / rr) * radialDisp;
      rz += (rz / rr) * radialDisp;

      positions.push(rx, ry, rz);

      // ----------------------------------------------------------
      // GRAY/WHITE MATTER COLORING
      // ----------------------------------------------------------
      const isCereb = cerebMask > 0.02;
      const ridgeAmt = Math.max(0, foldVal - 0.7) / 0.3;    // 0..~1
      const sulcusAmt = Math.max(0, 0.7 - foldVal) / 0.7;   // 0..~1
      let baseGray: number;
      if (isCereb) {
        baseGray = 0.58 + ridgeAmt * 0.06 - sulcusAmt * 0.08;
      } else {
        baseGray = 0.64 + ridgeAmt * 0.14 - sulcusAmt * 0.12;
      }
      const jitter = hashNoise(rx * 12, ry * 12, rz * 12) * 0.03 - 0.015;
      baseGray = Math.min(0.85, Math.max(0.46, baseGray + jitter));
      baseGrays.push(baseGray);

      // ----------------------------------------------------------
      // AMBIENT OCCLUSION — darker in all groove areas
      // ----------------------------------------------------------
      const aoCrease = fissDepth * 0.7
                     + sylvDepth
                     + centDepth
                     + sulcusAmt * 0.15; // Significantly darkened for deep folds
      const ao = Math.max(0.20, 1.0 - aoCrease * 7.0);
      aoValues.push(ao);

      regionCoords.push(theta, elev, rx, ry, rz);
    }

    // ============================================================
    // BUILD CEREBRUM GEOMETRY
    // ============================================================
    const geom = new THREE.BufferGeometry();
    const posAttr = new Float32Array(positions);
    geom.setAttribute('position', new THREE.BufferAttribute(posAttr, 3));

    const indexArr = new (positions.length / 3 > 65535 ? Uint32Array : Uint16Array)(faces.length * 3);
    for (let fi = 0; fi < faces.length; fi++) {
      indexArr[fi * 3] = faces[fi][0];
      indexArr[fi * 3 + 1] = faces[fi][1];
      indexArr[fi * 3 + 2] = faces[fi][2];
    }
    geom.setIndex(new THREE.BufferAttribute(indexArr, 1));

    const vertexCount = positions.length / 3;
    geom.setAttribute('color', new THREE.BufferAttribute(new Float32Array(vertexCount * 3), 3));
    geom.setAttribute('ao', new THREE.BufferAttribute(new Float32Array(aoValues), 1));
    geom.computeVertexNormals();

    geom.userData.baseGrays = baseGrays;
    geom.userData.regionCoords = regionCoords;
    geom.userData.aoValues = aoValues;
    geom.userData.vertexCount = vertexCount;

    // ============================================================
    // ENHANCED SHADER (rim + SSS + AO + specular + Fresnel)
    // ============================================================
    rimShaderMaterial = new THREE.ShaderMaterial({
      uniforms: {
        rimColor: { value: new THREE.Vector3(...MODE_RIM_COLORS[mode]) },
        rimPower: { value: 2.8 },
        uTime: { value: 0.0 },
        lightDir: { value: new THREE.Vector3(0.5, 0.8, 0.6).normalize() },
        lightDir2: { value: new THREE.Vector3(-0.4, -0.2, -0.8).normalize() }
      },
      vertexShader: `
        attribute float ao;
        varying vec3 vNormal;
        varying vec3 vPosition;
        varying vec3 vWorldPosition;
        varying vec3 vColor;
        varying float vAO;
        void main() {
          vNormal = normalize(normalMatrix * normal);
          vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
          vPosition = mvPosition.xyz;
          vWorldPosition = (modelMatrix * vec4(position, 1.0)).xyz;
          vColor = color;
          vAO = ao;
          gl_Position = projectionMatrix * mvPosition;
        }
      `,
      fragmentShader: `
        uniform vec3 rimColor;
        uniform float rimPower;
        uniform float uTime;
        uniform vec3 lightDir;
        uniform vec3 lightDir2;
        varying vec3 vNormal;
        varying vec3 vPosition;
        varying vec3 vWorldPosition;
        varying vec3 vColor;
        varying float vAO;

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
          vec3 sssColor = vec3(0.85, 0.45, 0.35) * sssWrap * 0.12;

          // Rim / Fresnel glow
          float fresnel = pow(1.0 - abs(dot(normal, viewDir)), rimPower);
          vec3 rimContrib = rimColor * fresnel * 0.5;

          // Edge glow for depth definition
          float edgeGlow = pow(1.0 - abs(dot(normal, viewDir)), 4.5) * 0.15;

          // Combine
          float ao = vAO;
          vec3 baseColor = vColor;
          float activationStrength = max(0.0, max(baseColor.r - baseColor.g * 0.8, 0.0));

          vec3 litColor = baseColor * (0.28 + diffuse * 0.72) * ao;
          litColor += sssColor * ao;
          litColor += vec3(spec + spec2) * vec3(1.0, 0.95, 0.9);
          litColor += rimContrib;
          litColor += vec3(edgeGlow) * rimColor * 0.3;
          litColor += baseColor * activationStrength * 0.15;
          litColor *= vec3(1.02, 1.0, 0.97);

          gl_FragColor = vec4(litColor, 0.98);
        }
      `,
      side: THREE.FrontSide,
      transparent: true,
      vertexColors: true
    });

    const mesh = new THREE.Mesh(geom, rimShaderMaterial);
    group.add(mesh);
    brainMesh = mesh;
    brainGeom = geom;

    // ============================================================
    // BRAINSTEM — cylindrical extension below the cerebellum
    // ============================================================
    const stemSegs = 12;
    const stemRings = 8;
    const stemVerts: number[] = [];
    const stemIndices: number[] = [];
    const stemColors: number[] = [];
    const stemAO: number[] = [];

    for (let ring = 0; ring <= stemRings; ring++) {
      const t = ring / stemRings;        // 0 at top, 1 at tip
      const yy = -0.42 - t * 0.35;      // descend below the brain
      const radius = 0.09 * (1 - t * 0.4); // tapers to a point
      // Slight backward lean matching real brainstem angle
      const zOff = 0.65 + t * 0.08;

      for (let seg = 0; seg <= stemSegs; seg++) {
        const angle = (seg / stemSegs) * Math.PI * 2;
        const xx = Math.cos(angle) * radius;
        const zz = Math.sin(angle) * radius + zOff;
        stemVerts.push(xx, yy, zz);

        const gray = 0.55 + hashNoise(xx * 20, yy * 20, zz * 20) * 0.06;
        stemColors.push(gray, gray, gray * 0.97);
        stemAO.push(0.7 + Math.cos(angle) * 0.15);
      }
    }

    for (let ring = 0; ring < stemRings; ring++) {
      for (let seg = 0; seg < stemSegs; seg++) {
        const a = ring * (stemSegs + 1) + seg;
        const b = a + stemSegs + 1;
        stemIndices.push(a, b, a + 1);
        stemIndices.push(a + 1, b, b + 1);
      }
    }

    const stemGeom = new THREE.BufferGeometry();
    stemGeom.setAttribute('position', new THREE.BufferAttribute(new Float32Array(stemVerts), 3));
    stemGeom.setIndex(stemIndices);
    stemGeom.setAttribute('color', new THREE.BufferAttribute(new Float32Array(stemColors), 3));
    stemGeom.setAttribute('ao', new THREE.BufferAttribute(new Float32Array(stemAO), 1));
    stemGeom.computeVertexNormals();

    const stemMesh = new THREE.Mesh(stemGeom, rimShaderMaterial);
    group.add(stemMesh);

    return group;
  }

  // ===== Compute per-vertex activation for a given mode =====
  function computeActivationColors(targetMode: string, time: number): Float32Array {
    const baseGrays: number[] = brainGeom.userData.baseGrays;
    const regionCoords: number[] = brainGeom.userData.regionCoords;
    const vertexCount: number = brainGeom.userData.vertexCount;
    const colors = new Float32Array(vertexCount * 3);

    // Subtle pulsing amplitude
    const pulsePhase = Math.sin(time * 1.8) * 0.08 + Math.sin(time * 3.1) * 0.04;

    for (let i = 0; i < vertexCount; i++) {
      const theta = regionCoords[i * 5 + 0];
      const elev = regionCoords[i * 5 + 1];
      const rx = regionCoords[i * 5 + 2];
      const ry = regionCoords[i * 5 + 3];
      const rz = regionCoords[i * 5 + 4];

      let activity = 0;

      if (targetMode === 'attention') {
        // DORSAL ATTENTION NETWORK
        // Frontal Eye Fields (FEF) — superior frontal, bilateral
        const fef = 0.9 * Math.exp(-((theta + 1.2) ** 2) / 0.18) * Math.exp(-((elev - 0.4) ** 2) / 0.12);
        // Intraparietal Sulcus (IPS) — dorsal parietal
        const ips = 0.85 * Math.exp(-((theta - 0.2) ** 2) / 0.2) * Math.exp(-((elev - 0.45) ** 2) / 0.1);
        // Primary Visual Cortex (V1/V2) — occipital pole
        const v1 = 0.75 * Math.exp(-((theta - 1.4) ** 2) / 0.12) * Math.exp(-((elev + 0.05) ** 2) / 0.15);
        // MT/V5 — lateral occipital
        const mt = 0.65 * Math.exp(-((theta - 0.9) ** 2) / 0.15) * Math.exp(-((elev + 0.15) ** 2) / 0.1) * Math.max(0.5, Math.abs(rx));
        // PFC — prefrontal engagement
        const pfc = 0.7 * Math.exp(-((theta + 1.4) ** 2) / 0.25) * Math.exp(-((elev - 0.15) ** 2) / 0.2);
        // ACC — anterior cingulate
        const acc = 0.5 * Math.exp(-((theta + 0.8) ** 2) / 0.12) * Math.exp(-((elev - 0.25) ** 2) / 0.08) * Math.exp(-(rx * rx) / 0.04);
        activity = fef + ips + v1 + mt + pfc + acc;

      } else if (targetMode === 'dopamine') {
        // REWARD / DOPAMINE CIRCUIT
        // Ventral Striatum / NAcc — deep central-ventral
        const radius = Math.hypot(rx, ry, rz);
        const vs = 1.1 * Math.exp(-((radius - 0.15) ** 2) / 0.04) * Math.exp(-((elev + 0.15) ** 2) / 0.1);
        // VTA / Substantia Nigra — midbrain, very deep
        const vta = 0.8 * Math.exp(-((radius - 0.08) ** 2) / 0.02) * Math.exp(-((elev + 0.3) ** 2) / 0.06);
        // vmPFC — ventromedial prefrontal (surface bleed of reward signal)
        const vmpfc = 0.75 * Math.exp(-((theta + 1.3) ** 2) / 0.2) * Math.exp(-((elev + 0.2) ** 2) / 0.15) * Math.exp(-(rx * rx) / 0.06);
        // OFC — orbitofrontal cortex
        const ofc = 0.6 * Math.exp(-((theta + 1.5) ** 2) / 0.15) * Math.exp(-((elev + 0.35) ** 2) / 0.1);
        // Ventral central glow
        const ventral = 0.5 * Math.max(0, -elev) * Math.exp(-(radius * radius) / 0.15);
        // ACC — also part of reward evaluation
        const accReward = 0.55 * Math.exp(-((theta + 0.7) ** 2) / 0.1) * Math.exp(-((elev - 0.2) ** 2) / 0.08) * Math.exp(-(rx * rx) / 0.03);
        activity = vs + vta + vmpfc + ofc + ventral + accReward;

      } else {
        // MEMORY ENCODING NETWORK
        // Hippocampus — medial temporal, bilateral
        const hipp = 1.0 * Math.exp(-((theta - 0.6) ** 2) / 0.12) * Math.exp(-((elev + 0.3) ** 2) / 0.08) * Math.max(0.4, Math.abs(rx));
        // Parahippocampal Cortex
        const phc = 0.7 * Math.exp(-((theta - 0.5) ** 2) / 0.15) * Math.exp(-((elev + 0.4) ** 2) / 0.1);
        // Posterior Cingulate (PCC) — medial parietal
        const pcc = 0.75 * Math.exp(-((theta - 0.8) ** 2) / 0.12) * Math.exp(-((elev - 0.2) ** 2) / 0.1) * Math.exp(-(rx * rx) / 0.04);
        // Angular Gyrus — lateral parietal
        const ang = 0.6 * Math.exp(-((theta - 0.4) ** 2) / 0.15) * Math.exp(-((elev - 0.3) ** 2) / 0.12) * Math.max(0.3, Math.abs(rx));
        // DLPFC — dorsolateral prefrontal (working memory)
        const dlpfc = 0.65 * Math.exp(-((theta + 1.1) ** 2) / 0.2) * Math.exp(-((elev - 0.3) ** 2) / 0.12) * Math.max(0.3, Math.abs(rx));
        // Amygdala — adjacent to hippocampus
        const amyg = 0.55 * Math.exp(-((theta - 0.3) ** 2) / 0.1) * Math.exp(-((elev + 0.35) ** 2) / 0.06) * Math.max(0.4, Math.abs(rx));
        activity = hipp + phc + pcc + ang + dlpfc + amyg;
      }

      // Organic texture using deterministic noise + pulsing
      const noiseVal = hashNoise(theta * 5, elev * 5, i * 0.01);
      activity = activity * (0.88 + noiseVal * 0.24);
      // Pulsing modulation (only affects active regions)
      activity = activity * (1.0 + pulsePhase * Math.min(1, activity * 2));
      activity = Math.min(1, Math.max(0, activity));

      const [r, g, b] = activationColor(activity, baseGrays[i]);
      colors[i * 3 + 0] = r;
      colors[i * 3 + 1] = g;
      colors[i * 3 + 2] = b;
    }
    return colors;
  }

  // Apply activation with smooth transition support
  function applyModeActivation(immediate = false) {
    if (!brainGeom) return;
    const time = clock ? clock.getElapsedTime() : 0;

    const newColors = computeActivationColors(mode, time);

    if (immediate || !previousColors) {
      // Apply immediately (first load or forced)
      const colorAttr = brainGeom.getAttribute('color') as THREE.BufferAttribute;
      (colorAttr.array as Float32Array).set(newColors);
      colorAttr.needsUpdate = true;
      previousColors = new Float32Array(newColors);
      targetColors = null;
      transitionProgress = 1.0;
    } else {
      // Start transition
      previousColors = new Float32Array(brainGeom.getAttribute('color').array as Float32Array);
      targetColors = newColors;
      transitionProgress = 0.0;
    }

    // Update rim color for the mode
    if (rimShaderMaterial) {
      const rc = MODE_RIM_COLORS[mode] || MODE_RIM_COLORS.attention;
      rimShaderMaterial.uniforms.rimColor.value.set(rc[0], rc[1], rc[2]);
    }
  }

  // Update transition interpolation each frame
  function updateTransition(deltaTime: number) {
    if (!brainGeom || transitionProgress >= 1.0 || !targetColors || !previousColors) return;

    transitionProgress += deltaTime / TRANSITION_DURATION;
    if (transitionProgress > 1.0) transitionProgress = 1.0;

    // Smooth ease-in-out
    const t = transitionProgress < 0.5
      ? 2 * transitionProgress * transitionProgress
      : 1 - Math.pow(-2 * transitionProgress + 2, 2) / 2;

    const colorAttr = brainGeom.getAttribute('color') as THREE.BufferAttribute;
    const arr = colorAttr.array as Float32Array;
    for (let i = 0; i < arr.length; i++) {
      arr[i] = previousColors[i] + (targetColors[i] - previousColors[i]) * t;
    }
    colorAttr.needsUpdate = true;

    if (transitionProgress >= 1.0) {
      previousColors = new Float32Array(targetColors);
      targetColors = null;
    }
  }

  // Update pulsing activation in the animation loop
  function updatePulsingActivation(time: number) {
    if (!brainGeom || transitionProgress < 1.0) return; // don't pulse during transitions
    const colors = computeActivationColors(mode, time);
    const colorAttr = brainGeom.getAttribute('color') as THREE.BufferAttribute;
    (colorAttr.array as Float32Array).set(colors);
    colorAttr.needsUpdate = true;
    previousColors = new Float32Array(colors);
  }

  function activateROIs() {
    if (!brain) return;
    const cfg = ROIS[mode as keyof typeof ROIS] || ROIS.attention;
    const old = brain.children.filter(c => c.userData && c.userData.isROI);
    old.forEach(c => brain.remove(c));

    const markersByMode: Record<string, { name: string; pos: number[] }[]> = {
      attention: [
        { name: 'FEF', pos: [0.38, 0.42, 0.12] },
        { name: 'IPS', pos: [0.18, 0.38, 0.32] },
        { name: 'V1', pos: [-0.38, 0.02, 0.38] },
        { name: 'MT', pos: [-0.22, -0.06, 0.44] }
      ],
      dopamine: [
        { name: 'VTA', pos: [0.04, -0.14, 0.02] },
        { name: 'NAcc', pos: [0.18, -0.06, 0.12] },
        { name: 'vmPFC', pos: [0.38, -0.02, 0.04] },
        { name: 'VS', pos: [0.08, -0.10, 0.08] }
      ],
      memory: [
        { name: 'Hipp', pos: [0.42, -0.22, 0.32] },
        { name: 'PHC', pos: [0.34, -0.24, 0.40] },
        { name: 'PCC', pos: [-0.06, 0.06, 0.38] },
        { name: 'ANG', pos: [-0.28, 0.18, 0.28] }
      ]
    };
    const markers = markersByMode[mode] || markersByMode.attention;

    for (const m of markers) {
      const score = (roiScores[m.name] ?? roiScores[m.name.toLowerCase()] ?? 0.45 + Math.random() * 0.4) as number;
      const intensity = Math.min(1, Math.max(0, score));
      const size = 0.03 + intensity * 0.08;
      const sphereGeo = new THREE.SphereGeometry(size, 20, 14);
      const sphereMat = new THREE.MeshStandardMaterial({
        color: cfg.color,
        emissive: cfg.color,
        emissiveIntensity: intensity * 1.3,
        transparent: true,
        opacity: 0.45
      });
      const sphere = new THREE.Mesh(sphereGeo, sphereMat);
      sphere.position.set(m.pos[0], m.pos[1], m.pos[2]);
      sphere.userData = { isROI: true, roiName: m.name, score: intensity };
      brain.add(sphere);

      // Outer glow shell
      const glowGeo = new THREE.SphereGeometry(size * 2.0, 16, 10);
      const glowMat = new THREE.MeshBasicMaterial({
        color: cfg.color,
        transparent: true,
        opacity: 0.08 + intensity * 0.07,
        side: THREE.BackSide
      });
      const glow = new THREE.Mesh(glowGeo, glowMat);
      glow.position.copy(sphere.position);
      glow.userData = { isROI: true };
      brain.add(glow);
    }
  }

  // ===== AMBIENT NEURAL PARTICLES =====
  function createParticles(): THREE.Points {
    const count = 200;
    const positions = new Float32Array(count * 3);
    const sizes = new Float32Array(count);
    const alphas = new Float32Array(count);

    for (let i = 0; i < count; i++) {
      // Distribute in a shell around the brain
      const r = 1.2 + Math.random() * 1.0;
      const t = Math.random() * Math.PI * 2;
      const p = Math.acos(2 * Math.random() - 1);
      positions[i * 3 + 0] = r * Math.sin(p) * Math.cos(t);
      positions[i * 3 + 1] = r * Math.sin(p) * Math.sin(t) * 0.7;
      positions[i * 3 + 2] = r * Math.cos(p);
      sizes[i] = 1.5 + Math.random() * 3.0;
      alphas[i] = Math.random();
    }

    const geom = new THREE.BufferGeometry();
    geom.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geom.setAttribute('size', new THREE.BufferAttribute(sizes, 1));
    geom.setAttribute('alpha', new THREE.BufferAttribute(alphas, 1));

    const mat = new THREE.ShaderMaterial({
      uniforms: {
        uTime: { value: 0.0 },
        uColor: { value: new THREE.Vector3(0.6, 0.75, 1.0) }
      },
      vertexShader: `
        attribute float size;
        attribute float alpha;
        varying float vAlpha;
        uniform float uTime;
        void main() {
          vAlpha = alpha;
          vec3 pos = position;
          // Gentle floating motion
          pos.x += sin(uTime * 0.3 + alpha * 6.28) * 0.08;
          pos.y += cos(uTime * 0.25 + alpha * 4.0) * 0.06;
          pos.z += sin(uTime * 0.2 + alpha * 5.0) * 0.07;
          vec4 mvPosition = modelViewMatrix * vec4(pos, 1.0);
          gl_Position = projectionMatrix * mvPosition;
          gl_PointSize = size * (200.0 / -mvPosition.z);
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
          gl_FragColor = vec4(uColor, a * 0.18 * twinkle);
        }
      `,
      transparent: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending
    });

    return new THREE.Points(geom, mat);
  }

  onMount(() => {
    if (!container) return;

    clock = new THREE.Clock();
    scene = new THREE.Scene();
    camera = new THREE.PerspectiveCamera(42, container.clientWidth / container.clientHeight, 0.1, 100);
    camera.position.set(2.8, 1.6, 2.8);
    camera.lookAt(0, 0, 0);

    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(0x000000, 0);
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.1;
    container.appendChild(renderer.domElement);

    controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.06;
    controls.autoRotate = autoRotate;
    controls.autoRotateSpeed = 1.2;
    controls.minDistance = 1.8;
    controls.maxDistance = 6;
    controls.enablePan = false;

    // ===== CINEMATIC 3-POINT LIGHTING =====
    // Key light — warm, strong, from upper-right
    const keyLight = new THREE.DirectionalLight(0xfff6ec, 1.1);
    keyLight.position.set(5, 8, 6);
    scene.add(keyLight);

    // Fill light — cool, softer, from lower-left
    const fillLight = new THREE.DirectionalLight(0x8899bb, 0.4);
    fillLight.position.set(-4, -2, -3);
    scene.add(fillLight);

    // Back/rim light — strong from behind for edge definition
    const backLight = new THREE.DirectionalLight(0xaaccff, 0.6);
    backLight.position.set(-2, 3, -6);
    scene.add(backLight);

    // Ambient — very subtle to prevent completely black shadows
    const ambient = new THREE.AmbientLight(0x40383a, 0.35);
    scene.add(ambient);

    // Hemisphere for natural sky/ground lighting
    const hemi = new THREE.HemisphereLight(0xeef2ff, 0x201818, 0.4);
    scene.add(hemi);

    // Camera-attached point light for consistent highlights
    const camLight = new THREE.PointLight(0xffffff, 0.2);
    camera.add(camLight);
    scene.add(camera);

    // Create brain
    brain = createBrainMesh();
    scene.add(brain);

    // Create ambient particles
    particles = createParticles();
    scene.add(particles);

    // Initial activation
    applyModeActivation(true);
    activateROIs();

    // Pulse update counter (update pulsing every N frames for performance)
    let pulseFrame = 0;

    function animate() {
      animationId = requestAnimationFrame(animate);
      const delta = clock.getDelta();
      const elapsed = clock.getElapsedTime();

      controls.update();

      // Update shader time uniform
      if (rimShaderMaterial) {
        rimShaderMaterial.uniforms.uTime.value = elapsed;
      }

      // Update particle time
      if (particles) {
        const pMat = particles.material as THREE.ShaderMaterial;
        pMat.uniforms.uTime.value = elapsed;
        // Update particle color to match mode
        const rc = MODE_RIM_COLORS[mode] || MODE_RIM_COLORS.attention;
        pMat.uniforms.uColor.value.set(rc[0] * 0.7 + 0.3, rc[1] * 0.7 + 0.3, rc[2] * 0.7 + 0.3);
      }

      // Update ROI pulsing
      if (brain) {
        brain.children.forEach(c => {
          if (c.userData?.isROI && c instanceof THREE.Mesh && c.material instanceof THREE.MeshStandardMaterial) {
            const base = c.userData.score || 0.5;
            c.material.emissiveIntensity = base * (1.0 + Math.sin(elapsed * 2.5 + base * 5) * 0.3);
          }
        });
      }

      // Smooth mode transition
      updateTransition(delta);

      // Update pulsing activation every 6 frames for performance
      pulseFrame++;
      if (pulseFrame % 6 === 0 && transitionProgress >= 1.0) {
        updatePulsingActivation(elapsed);
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
    };
  });

  $effect(() => {
    if (mode && brainGeom) {
      applyModeActivation(false); // smooth transition
      activateROIs();
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

<div bind:this={container} class="w-full h-full min-h-[400px] rounded-2xl overflow-hidden"></div>