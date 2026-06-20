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
  let animationId: number;

  const ROIS = {
    attention: { rois: ['V1', 'V2', 'V3', 'MT', 'IPS', 'FEF'], color: 0x4d6cf5, label: 'Attention' },
    dopamine: { rois: ['VS', 'NAcc', 'vmPFC', 'SN', 'VTA'], color: 0xf59e0b, label: 'Dopamine' },
    memory: { rois: ['HIP', 'PHC', 'PRC', 'ERC', 'ANG', 'PCC', 'DLPFC'], color: 0x10b981, label: 'Memory' }
  };
  // Create a deformed icosphere that resembles a brain and supports vertex-color overlays
  function createBrainMesh(): THREE.Group {
    const group = new THREE.Group();

    // Build an icosahedron and subdivide it to create a smooth mesh
    const t = (1.0 + Math.sqrt(5.0)) / 2.0;
    let verts: number[][] = [
      [-1, t, 0], [1, t, 0], [-1, -t, 0], [1, -t, 0],
      [0, -1, t], [0, 1, t], [0, -1, -t], [0, 1, -t],
      [t, 0, -1], [t, 0, 1], [-t, 0, -1], [-t, 0, 1]
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
          const a = newVerts[i];
          const b = newVerts[j];
          const p = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2];
          const len = Math.hypot(p[0], p[1], p[2]) || 1;
          p[0] /= len; p[1] /= len; p[2] /= len;
          midCache.set(key, newVerts.push(p) - 1);
        }
        return midCache.get(key) as number;
      }
      const newFaces: number[][] = [];
      for (const f of fs) {
        const [a, b, c] = f;
        const ab = getMid(a, b);
        const bc = getMid(b, c);
        const ca = getMid(c, a);
        newFaces.push([a, ab, ca]);
        newFaces.push([b, bc, ab]);
        newFaces.push([c, ca, bc]);
        newFaces.push([ab, bc, ca]);
      }
      return [newVerts, newFaces] as const;
    }

    // Subdivide a few times for smoother mesh
    for (let i = 0; i < 3; i++) {
      const res = subdivide(verts, faces);
      verts = res[0]; faces = res[1];
    }

    // Deform into a brain-like shape (frontal/anterior emphasis, sulci-like noise)
    const positions: number[] = [];
    const normals: number[] = [];
    const colors: number[] = [];

    // helper colormap: base color depends on mode
    const baseColor = new THREE.Color((ROIS[mode as keyof typeof ROIS] || ROIS.attention).color);

    for (let i = 0; i < verts.length; i++) {
      let [x, y, z] = verts[i];
      // spherical coordinates
      const theta = Math.atan2(z, x);
      const phi = Math.asin(Math.max(-1, Math.min(1, y)));

      // deformations
      const apStretch = 1.15 - 0.15 * Math.sin(theta);
      const sulci = 0.03 * Math.sin(5 * theta + 3 * phi) + 0.02 * Math.cos(7 * phi);
      const temporal = 0.06 * Math.exp(-((phi - 0.3) ** 2) / 0.1) * (1 - Math.abs(z) * 0.15);
      const frontal = 0.05 * Math.exp(-((theta + Math.PI/2) ** 2) / 0.3) * Math.exp(-(phi ** 2) / 0.2);
      let rx = Math.cos(phi) * Math.cos(theta);
      let ry = Math.sin(phi);
      let rz = Math.cos(phi) * Math.sin(theta);

      rx = rx * (1.12 + 0.02 * Math.sin(theta)) + temporal * Math.cos(theta) + frontal * Math.cos(theta + Math.PI/2);
      ry = ry * (1.0 + 0.04 * Math.cos(2 * phi)) + sulci + temporal * Math.sin(phi);
      rz = rz * apStretch + temporal * Math.sin(theta);

      // normalize overall size
      const norm = Math.hypot(rx, ry, rz) || 1;
      rx /= norm; ry /= norm; rz /= norm;

      positions.push(rx, ry, rz);
      // placeholder normal - will be recomputed by three
      normals.push(0, 0, 0);

      // compute an activity score for this vertex based on position and selected `mode`
      let activity = 0;
      if (mode === 'attention') {
        // frontal bias (x > 0)
        activity = Math.max(0, rx * 1.5 + ry * 0.2);
      } else if (mode === 'dopamine') {
        // central/subcortical bias (near center)
        const r = Math.hypot(rx * 0.8, ry * 0.8, rz * 0.8);
        activity = Math.max(0, 1.0 - r);
      } else {
        // memory - medial temporal bias (lower-right / temporal region)
        activity = Math.max(0, 0.6 * (1 - Math.abs(ry)) + 0.8 * (Math.abs(rz) > 0.4 ? 0.5 : 0));
      }
      activity = Math.min(1, Math.max(0, (activity + 0.2 * Math.random())));

      // vertex color = blend between baseColor and dark
      const col = new THREE.Color();
      col.copy(baseColor);
      col.lerp(new THREE.Color(0x111118), 1 - activity);
      colors.push(col.r, col.g, col.b);
    }

    // Build BufferGeometry
    const geom = new THREE.BufferGeometry();
    const posAttr = new Float32Array(positions);
    geom.setAttribute('position', new THREE.BufferAttribute(posAttr, 3));

    const indexArr = new (positions.length / 3 > 65535 ? Uint32Array : Uint16Array)(faces.length * 3);
    for (let i = 0; i < faces.length; i++) {
      indexArr[i * 3 + 0] = faces[i][0];
      indexArr[i * 3 + 1] = faces[i][1];
      indexArr[i * 3 + 2] = faces[i][2];
    }
    geom.setIndex(new THREE.BufferAttribute(indexArr, 1));
    geom.setAttribute('color', new THREE.BufferAttribute(new Float32Array(colors), 3));
    geom.computeVertexNormals();

    const mat = new THREE.MeshPhysicalMaterial({
      vertexColors: true,
      metalness: 0.05,
      roughness: 0.6,
      clearcoat: 0.1,
      reflectivity: 0.2,
      transparent: true,
      opacity: 0.98,
    });

    const mesh = new THREE.Mesh(geom, mat);
    mesh.castShadow = false;
    mesh.receiveShadow = false;
    mesh.scale.set(1.2, 1.05, 1.0);
    group.add(mesh);

    // subtle wireframe overlay to reveal folds
    const wire = new THREE.Mesh(geom.clone(), new THREE.MeshBasicMaterial({ color: 0x222233, wireframe: true, opacity: 0.06, transparent: true }));
    group.add(wire);

    return group;
  }

  function activateROIs() {
    // Keep small ROI markers for context; remove existing markers then add a few anatomically placed ones
    if (!brain) return;
    const cfg = ROIS[mode as keyof typeof ROIS] || ROIS.attention;
    const old = brain.children.filter(c => c.userData && c.userData.isROI);
    old.forEach(c => brain.remove(c));

    const markers = [
      { name: 'PFC', pos: [0.45, 0.6, 0.1] },
      { name: 'ACC', pos: [0.15, 0.4, 0.3] },
      { name: 'Hipp', pos: [0.6, -0.25, 0.55] },
      { name: 'Striatum', pos: [0.25, 0.0, 0.15] },
      { name: 'Amyg', pos: [-0.35, -0.15, 0.5] }
    ];

    for (const m of markers) {
      const score = (roiScores[m.name] ?? roiScores[m.name.toLowerCase()] ?? Math.random() * 0.6) as number;
      const intensity = Math.min(1, Math.max(0, score || 0.35));
      const size = 0.04 + intensity * 0.12;
      const sphereGeo = new THREE.SphereGeometry(size, 16, 12);
      const sphereMat = new THREE.MeshStandardMaterial({ color: cfg.color, emissive: cfg.color, emissiveIntensity: intensity * 0.9, transparent: true, opacity: 0.6 });
      const sphere = new THREE.Mesh(sphereGeo, sphereMat);
      sphere.position.set(m.pos[0], m.pos[1], m.pos[2]);
      sphere.userData = { isROI: true, roiName: m.name, score: intensity };
      brain.add(sphere);
    }
  }

  onMount(() => {
    if (!container) return;

    scene = new THREE.Scene();
    camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 100);
    camera.position.set(3.5, 2, 3.5);
    camera.lookAt(0, 0, 0);

    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(0x000000, 0);
    container.appendChild(renderer.domElement);

    controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.autoRotate = autoRotate;
    controls.autoRotateSpeed = 1.5;
    controls.minDistance = 2.5;
    controls.maxDistance = 8;

    const ambient = new THREE.AmbientLight(0x404060, 0.5);
    scene.add(ambient);
    const dir = new THREE.DirectionalLight(0xffffff, 1);
    dir.position.set(5, 10, 7);
    scene.add(dir);
    const fill = new THREE.DirectionalLight(0x4d6cf5, 0.3);
    fill.position.set(-3, -1, -4);
    scene.add(fill);

    brain = createBrainMesh();
    scene.add(brain);

    activateROIs();

    function animate() {
      animationId = requestAnimationFrame(animate);
      controls.update();
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
    if (mode && brain) activateROIs();
    if (controls) controls.autoRotate = autoRotate;
  });

  onDestroy(() => {
    if (animationId) cancelAnimationFrame(animationId);
    controls?.dispose();
    renderer?.dispose();
    if (container && renderer.domElement) container.removeChild(renderer.domElement);
  });
</script>

<div bind:this={container} class="w-full h-full min-h-[400px] rounded-2xl overflow-hidden"></div>
