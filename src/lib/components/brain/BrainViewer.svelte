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

  function createBrainMesh(): THREE.Group {
    const group = new THREE.Group();
    const geo = new THREE.SphereGeometry(2, 32, 32);
    const mat = new THREE.MeshPhysicalMaterial({
      color: 0x1a1a2e,
      metalness: 0.1,
      roughness: 0.6,
      transparent: true,
      opacity: 0.85,
      wireframe: false
    });
    const main = new THREE.Mesh(geo, mat);
    main.scale.set(1, 0.88, 0.75);
    group.add(main);

    const wireMat = new THREE.MeshBasicMaterial({
      color: 0x4d6cf5,
      wireframe: true,
      transparent: true,
      opacity: 0.08
    });
    const wire = new THREE.Mesh(geo.clone(), wireMat);
    wire.scale.set(1, 0.88, 0.75);
    group.add(wire);

    return group;
  }

  function activateROIs() {
    if (!brain) return;
    const cfg = ROIS[mode as keyof typeof ROIS] || ROIS.attention;
    const children = brain.children.filter(c => c.userData.isROI);
    children.forEach(c => brain.remove(c));

    const currentModeRois = cfg.rois;
    const allRois = ['V1', 'V2', 'V3', 'MT', 'IPS', 'FEF', 'VS', 'NAcc', 'vmPFC', 'SN', 'VTA', 'HIP', 'PHC', 'PRC', 'ERC', 'ANG', 'PCC', 'DLPFC'];

    allRois.forEach((roi, i) => {
      const score = roiScores[roi] || 0;
      const isPrimary = currentModeRois.includes(roi);
      const intensity = isPrimary ? score : score * 0.15;

      const theta = (i / allRois.length) * Math.PI * 2;
      const phi = Math.sin(i * 1.5) * 0.6;
      const r = 1.6 + intensity * 0.4;
      const x = r * Math.cos(theta) * Math.cos(phi);
      const y = r * Math.sin(phi);
      const z = r * Math.sin(theta) * Math.cos(phi);

      const size = 0.08 + intensity * 0.2;
      const sphereGeo = new THREE.SphereGeometry(size, 12, 12);
      const sphereMat = new THREE.MeshPhysicalMaterial({
        color: isPrimary ? cfg.color : 0x444466,
        emissive: isPrimary ? cfg.color : 0x222244,
        emissiveIntensity: intensity * 0.8,
        transparent: true,
        opacity: 0.3 + intensity * 0.7,
        metalness: 0.3,
        roughness: 0.4
      });
      const sphere = new THREE.Mesh(sphereGeo, sphereMat);
      sphere.position.set(x, y, z);
      sphere.userData.isROI = true;
      sphere.userData.roiName = roi;
      sphere.userData.score = intensity;
      brain.add(sphere);
    });
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
