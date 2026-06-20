<script lang="ts">
  import { _ } from '$lib/i18n';
  import Card from '$lib/components/ui/Card.svelte';
  import BrainViewer from '$lib/components/brain/BrainViewer.svelte';

  let mode = $state<'attention' | 'dopamine' | 'memory'>('attention');
  let autoRotate = $state(true);

  const rois: Record<string, { x: number; y: number; z: number }> = {
    pfc: { x: 0, y: 1.2, z: 0.6 },
    acc: { x: 0.3, y: 0.9, z: 0.4 },
    striatum: { x: 0.5, y: 0.2, z: 0.3 },
    amygdala: { x: -0.4, y: -0.2, z: 0.8 },
    hippocampus: { x: 0.6, y: -0.4, z: 0.7 },
    vlpfc: { x: -0.5, y: 0.8, z: 0.5 },
    cerebellum: { x: 0, y: -1.0, z: -0.2 },
    brainstem: { x: 0, y: -0.6, z: -0.4 }
  };

  let roiScores = $derived({
    pfc: mode === 'attention' ? 0.85 : mode === 'dopamine' ? 0.6 : 0.75,
    acc: mode === 'attention' ? 0.7 : mode === 'dopamine' ? 0.9 : 0.5,
    striatum: mode === 'attention' ? 0.5 : mode === 'dopamine' ? 0.88 : 0.6,
    amygdala: mode === 'attention' ? 0.6 : mode === 'dopamine' ? 0.7 : 0.85,
    hippocampus: mode === 'attention' ? 0.55 : mode === 'dopamine' ? 0.5 : 0.92,
    vlpfc: mode === 'attention' ? 0.78 : mode === 'dopamine' ? 0.55 : 0.5,
    cerebellum: 0.4, brainstem: 0.3
  });

  const modeInfo: Record<string, { color: string; desc: string; rois: string[] }> = {
    attention: { color: '#4d6cf5', desc: 'Prefrontal cortex, ACC, vlPFC — focus and engagement', rois: ['pfc', 'acc', 'vlpfc'] },
    dopamine: { color: '#f59e0b', desc: 'Striatum, ACC — reward and anticipation', rois: ['striatum', 'acc'] },
    memory: { color: '#10b981', desc: 'Hippocampus, Amygdala, PFC — encoding and retention', rois: ['hippocampus', 'amygdala', 'pfc'] }
  };
</script>

<div class="max-w-6xl mx-auto space-y-6">
  <h1 class="text-2xl font-bold">{$_('nav.brain_explorer')}</h1>

  <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
    <div class="lg:col-span-2">
      <Card class="p-0 overflow-hidden">
        <div class="h-[400px]">
          <BrainViewer roiScores={roiScores} mode={mode} autoRotate={autoRotate} />
        </div>
      </Card>
    </div>
    <div class="space-y-4">
      <Card>
        <h3 class="text-sm font-semibold mb-2">Mode</h3>
        <div class="flex flex-col gap-1.5">
          {#each Object.entries(modeInfo) as [key, info]}
            <button onclick={() => mode = key as 'attention' | 'dopamine' | 'memory'} class={`flex items-center gap-3 px-3 py-2 rounded-xl text-sm transition-all ${mode === key ? 'bg-neural-500/20 text-neural-300 border border-neural-500/20' : 'text-white/50 hover:text-white'}`}>
              <span class="w-2 h-2 rounded-full" style="background: {info.color}"></span>
              <span class="capitalize">{key}</span>
            </button>
          {/each}
        </div>
      </Card>
      <Card>
        <p class="text-xs text-white/50 leading-relaxed">{modeInfo[mode].desc}</p>
      </Card>
      <Card>
        <h3 class="text-sm font-semibold mb-2">Auto-rotate</h3>
        <button onclick={() => autoRotate = !autoRotate} class={`text-sm ${autoRotate ? 'text-emerald-400' : 'text-white/40'}`}>{autoRotate ? 'On' : 'Off'}</button>
      </Card>
    </div>
  </div>
</div>
