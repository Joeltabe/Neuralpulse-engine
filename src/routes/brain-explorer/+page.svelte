<script lang="ts">
  import { _ } from '$lib/i18n';
  import Card from '$lib/components/ui/Card.svelte';
  import BrainViewer from '$lib/components/brain/BrainViewer.svelte';

  let mode = $state<'attention' | 'dopamine' | 'memory'>('attention');
  let autoRotate = $state(true);

  let roiScores = $derived({
    frontal: mode === 'attention' ? 0.92 : mode === 'dopamine' ? 0.72 : 0.70,
    pariet: mode === 'attention' ? 0.88 : mode === 'dopamine' ? 0.35 : 0.82,
    occipit: mode === 'attention' ? 0.78 : mode === 'dopamine' ? 0.25 : 0.40,
    temp: mode === 'attention' ? 0.55 : mode === 'dopamine' ? 0.60 : 0.95,
    corpus: mode === 'attention' ? 0.35 : mode === 'dopamine' ? 0.85 : 0.55,
    cereb: mode === 'attention' ? 0.30 : mode === 'dopamine' ? 0.28 : 0.30,
    stem: mode === 'attention' ? 0.20 : mode === 'dopamine' ? 0.90 : 0.22,
    pitua: mode === 'attention' ? 0.15 : mode === 'dopamine' ? 0.45 : 0.18
  });

  const modeInfo: Record<string, { color: string; desc: string; icon: string; rois: { name: string; fullName: string; score: number }[] }> = {
    attention: {
      color: '#4d6cf5',
      desc: 'Dorsal attention network — Frontal cortex (FEF), parietal lobe (IPS), and occipital visual areas coordinate focus, saccadic control, and sustained engagement with stimuli.',
      icon: 'M15 12a3 3 0 11-6 0 3 3 0 016 0z M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z',
      rois: [
        { name: 'Frontal', fullName: 'Frontal Lobe', score: 0.92 },
        { name: 'Parietal', fullName: 'Parietal Lobe', score: 0.88 },
        { name: 'Occipital', fullName: 'Occipital Lobe', score: 0.78 },
        { name: 'Temporal', fullName: 'Temporal Lobe', score: 0.55 },
        { name: 'Corpus', fullName: 'Corpus Callosum', score: 0.35 }
      ]
    },
    dopamine: {
      color: '#f59e0b',
      desc: 'Reward circuit — Brain stem (VTA/SN), corpus callosum pathways, and frontal cortex (vmPFC/OFC) drive anticipation, pleasure, motivation, and reward evaluation.',
      icon: 'M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z',
      rois: [
        { name: 'Stem', fullName: 'Brain Stem (VTA)', score: 0.90 },
        { name: 'Corpus', fullName: 'Corpus Callosum', score: 0.85 },
        { name: 'Frontal', fullName: 'Frontal Lobe (vmPFC)', score: 0.72 },
        { name: 'Temporal', fullName: 'Temporal Lobe', score: 0.60 },
        { name: 'Pituitary', fullName: 'Pituitary Gland', score: 0.45 }
      ]
    },
    memory: {
      color: '#10b981',
      desc: 'Memory encoding network — Temporal lobe (hippocampus), parietal cortex (PCC/angular gyrus), and frontal lobe (DLPFC) coordinate encoding, consolidation, and retrieval.',
      icon: 'M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10',
      rois: [
        { name: 'Temporal', fullName: 'Temporal Lobe (Hipp)', score: 0.95 },
        { name: 'Parietal', fullName: 'Parietal Lobe (PCC)', score: 0.82 },
        { name: 'Frontal', fullName: 'Frontal Lobe (DLPFC)', score: 0.70 },
        { name: 'Corpus', fullName: 'Corpus Callosum', score: 0.55 },
        { name: 'Occipital', fullName: 'Occipital Lobe', score: 0.40 }
      ]
    }
  };

  const currentMode = $derived(modeInfo[mode]);
</script>

<div class="max-w-7xl mx-auto space-y-6">
  <!-- Header -->
  <div class="flex items-center justify-between">
    <div>
      <h1 class="text-2xl font-bold">{$_('nav.brain_explorer')}</h1>
      <p class="text-sm text-white/40 mt-1">Interactive neuromarketing visualization — Real anatomical brain model</p>
    </div>
    <div class="flex items-center gap-2">
      <span class="text-xs text-white/30 uppercase tracking-wider font-medium">Neural Engine v3 — GLTF</span>
      <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
    </div>
  </div>

  <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
    <!-- Brain Viewer (larger viewport) -->
    <div class="lg:col-span-8">
      <Card class="p-0 overflow-hidden relative">
        <div class="h-[550px] relative">
          <BrainViewer roiScores={roiScores} mode={mode} autoRotate={autoRotate} />
          <!-- Mode indicator overlay -->
          <div class="absolute top-4 left-4 flex items-center gap-2 px-3 py-1.5 rounded-lg bg-black/40 backdrop-blur-sm border border-white/10">
            <span class="w-2 h-2 rounded-full animate-pulse" style="background: {currentMode.color}"></span>
            <span class="text-xs font-medium text-white/70 capitalize">{mode} Mode</span>
          </div>
          <!-- Auto-rotate toggle overlay -->
          <button
            onclick={() => autoRotate = !autoRotate}
            class="absolute bottom-4 right-4 flex items-center gap-2 px-3 py-1.5 rounded-lg bg-black/40 backdrop-blur-sm border border-white/10 hover:border-white/20 transition-all text-xs"
          >
            <svg class="w-3.5 h-3.5 {autoRotate ? 'text-emerald-400 animate-spin' : 'text-white/40'}" style="animation-duration: 3s;" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            <span class="{autoRotate ? 'text-emerald-400' : 'text-white/40'}">Rotate</span>
          </button>
          <!-- Model credit -->
          <div class="absolute bottom-4 left-4 text-[9px] text-white/20 max-w-[200px] leading-tight">
            Brain model by farhad.Guli · CC-BY-4.0
          </div>
        </div>
      </Card>
    </div>

    <!-- Side Panel -->
    <div class="lg:col-span-4 space-y-4">
      <!-- Mode Selector -->
      <Card>
        <h3 class="text-xs font-semibold mb-3 text-white/50 uppercase tracking-wider">Activation Mode</h3>
        <div class="flex flex-col gap-1.5">
          {#each Object.entries(modeInfo) as [key, info]}
            <button
              onclick={() => mode = key as 'attention' | 'dopamine' | 'memory'}
              class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-all duration-300 {mode === key ? 'bg-white/10 border border-white/15 shadow-lg' : 'text-white/40 hover:text-white/70 hover:bg-white/5 border border-transparent'}"
              style={mode === key ? `box-shadow: 0 0 20px ${info.color}15, inset 0 0 20px ${info.color}08;` : ''}
            >
              <div class="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 transition-all duration-300" style="background: {info.color}{mode === key ? '25' : '10'};">
                <svg class="w-4 h-4 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24" style="color: {info.color};">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d={info.icon} />
                </svg>
              </div>
              <div class="text-left">
                <span class="capitalize font-medium {mode === key ? 'text-white' : ''}">{key}</span>
              </div>
              {#if mode === key}
                <div class="ml-auto w-1.5 h-1.5 rounded-full" style="background: {info.color}; box-shadow: 0 0 6px {info.color};"></div>
              {/if}
            </button>
          {/each}
        </div>
      </Card>

      <!-- Mode Description -->
      <Card>
        <div class="flex items-start gap-3">
          <div class="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0" style="background: {currentMode.color}15;">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" style="color: {currentMode.color};">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d={currentMode.icon} />
            </svg>
          </div>
          <p class="text-xs text-white/50 leading-relaxed">{currentMode.desc}</p>
        </div>
      </Card>

      <!-- ROI Activation Bars -->
      <Card>
        <h3 class="text-xs font-semibold mb-3 text-white/50 uppercase tracking-wider">Region Activation</h3>
        <div class="space-y-2.5">
          {#each currentMode.rois as roi}
            <div class="space-y-1">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-1.5">
                  <span class="text-xs font-medium text-white/70">{roi.name}</span>
                  <span class="text-[10px] text-white/25">{roi.fullName}</span>
                </div>
                <span class="text-xs text-white/40 tabular-nums">{Math.round(roi.score * 100)}%</span>
              </div>
              <div class="h-1.5 rounded-full bg-white/5 overflow-hidden">
                <div
                  class="h-full rounded-full transition-all duration-700 ease-out"
                  style="width: {roi.score * 100}%; background: linear-gradient(90deg, {currentMode.color}60, {currentMode.color}); box-shadow: 0 0 8px {currentMode.color}40;"
                ></div>
              </div>
            </div>
          {/each}
        </div>
      </Card>

      <!-- Color Ramp Legend -->
      <Card>
        <h3 class="text-xs font-semibold mb-3 text-white/50 uppercase tracking-wider">Activation Scale</h3>
        <div class="space-y-2">
          <div class="h-3 rounded-full overflow-hidden" style="background: linear-gradient(90deg, #7a7a7a 0%, #8c2020 15%, #cc4400 35%, #ee8800 55%, #ffcc00 75%, #ffeeaa 100%);"></div>
          <div class="flex items-center justify-between text-[10px] text-white/35 font-medium">
            <span>Baseline</span>
            <span>Low</span>
            <span>Medium</span>
            <span>High</span>
            <span>Peak</span>
          </div>
        </div>
      </Card>

      <!-- Primary Regions for Current Mode -->
      <Card>
        <h3 class="text-xs font-semibold mb-3 text-white/50 uppercase tracking-wider">Primary Regions</h3>
        <div class="flex flex-wrap gap-1.5">
          {#each currentMode.rois.slice(0, 3) as roi}
            <span
              class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium border"
              style="background: {currentMode.color}10; border-color: {currentMode.color}25; color: {currentMode.color};"
            >
              <span class="w-1 h-1 rounded-full" style="background: {currentMode.color}; box-shadow: 0 0 4px {currentMode.color};"></span>
              {roi.fullName}
            </span>
          {/each}
        </div>
      </Card>

      <!-- Anatomical Region Map -->
      <Card>
        <h3 class="text-xs font-semibold mb-3 text-white/50 uppercase tracking-wider">All Regions</h3>
        <div class="grid grid-cols-2 gap-1.5">
          {#each [
            { key: 'frontal', name: 'Frontal' },
            { key: 'pariet', name: 'Parietal' },
            { key: 'temp', name: 'Temporal' },
            { key: 'occipit', name: 'Occipital' },
            { key: 'cereb', name: 'Cerebellum' },
            { key: 'corpus', name: 'Corpus C.' },
            { key: 'stem', name: 'Brain Stem' },
            { key: 'pitua', name: 'Pituitary' }
          ] as region}
            {@const score = roiScores[region.key as keyof typeof roiScores] ?? 0}
            <div class="flex items-center gap-2 px-2 py-1.5 rounded-lg bg-white/3 border border-white/5">
              <div class="w-2 h-2 rounded-full flex-shrink-0" style="background: {score > 0.6 ? currentMode.color : score > 0.3 ? currentMode.color + '80' : 'rgba(255,255,255,0.15)'}; {score > 0.6 ? `box-shadow: 0 0 4px ${currentMode.color};` : ''}"></div>
              <span class="text-[10px] text-white/50 truncate">{region.name}</span>
              <span class="text-[10px] text-white/30 ml-auto tabular-nums">{Math.round(score * 100)}%</span>
            </div>
          {/each}
        </div>
      </Card>
    </div>
  </div>
</div>
