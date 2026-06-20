<script lang="ts">
  import { _ } from '$lib/i18n';
  import { error as showError, success } from '$lib/stores/notifications';
  import Card from '$lib/components/ui/Card.svelte';
  import Button from '$lib/components/ui/Button.svelte';
  import Input from '$lib/components/ui/Input.svelte';
  import Spinner from '$lib/components/ui/Spinner.svelte';

  let prompt = $state('');
  let loading = $state(false);
  let results: any[] = $state([]);
  let selectedModels = $state<string[]>(['flux1-dev', 'sd35-large', 'qwen-image', 'cosmos3-t2i']);

  const models = {
    'flux1-dev': 'FLUX.1-dev', 'sd35-large': 'SD 3.5 Large',
    'qwen-image': 'Qwen-Image', 'qwen-image-edit': 'Qwen-Image-Edit',
    'cosmos3-t2i': 'Cosmos3-Nano'
  };

  async function generate() {
    if (!prompt.trim()) return;
    if (selectedModels.length === 0) return;
    loading = true;
    results = [];
    try {
      // Generate for each selected model
      for (const modelKey of selectedModels) {
        const res = await fetch('/api/thumbnail/generate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            prompt, 
            model_key: modelKey,
            negative_prompt: '',
            guidance_scale: 7.5,
            num_inference_steps: 20
          })
        });
        const data = await res.json();
        
        if (data.success && data.results && data.results.length > 0) {
          results = [...results, ...data.results];
        } else if (res.ok && data.results) {
          results = [...results, ...data.results];
        } else if (data.error) {
          showError(data.error);
        }
      }
      
      if (results.length > 0) {
        success(`Generated ${results.length} thumbnail(s)!`);
      } else {
        showError('No thumbnails generated');
      }
    } catch (e) { 
      showError($_('errors.network') || 'Network error'); 
    } finally { 
      loading = false; 
    }
  }
</script>

<div class="max-w-6xl mx-auto space-y-6">
  <div class="flex items-center justify-between">
    <div>
      <h1 class="text-2xl font-bold">{$_('thumbnail.title')}</h1>
      <p class="text-sm text-white/50 mt-1">15 tokens per generation</p>
    </div>
    <a href="/thumbnail/history" class="text-sm text-neural-400 hover:text-neural-300">{$_('thumbnail.history')} &rarr;</a>
  </div>

  <Card>
    <div class="space-y-4">
      <Input type="textarea" label="Prompt" placeholder="A cinematic thumbnail of a person using a futuristic device, neon lights, dark background..." bind:value={prompt} />
      <div>
        <p class="text-sm text-white/70 mb-2">Models</p>
        <div class="flex flex-wrap gap-2">
          {#each Object.entries(models) as [key, name]}
            <button onclick={() => { if (selectedModels.includes(key)) selectedModels = selectedModels.filter(m => m !== key); else selectedModels = [...selectedModels, key]; }} class={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${selectedModels.includes(key) ? 'bg-neural-500/20 border-neural-500/30 text-neural-300' : 'border-white/10 text-white/40'}`}>{name}</button>
          {/each}
        </div>
      </div>
      <Button onclick={generate} variant="gradient" size="lg" class="w-full" disabled={!prompt.trim() || selectedModels.length === 0} loading={loading}>
        {loading ? 'Generating...' : 'Generate Thumbnails'}
      </Button>
    </div>
  </Card>

  {#if loading}
    <div class="flex justify-center py-12"><Spinner size="lg" /></div>
  {/if}

  {#if results.length > 0}
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {#each results as r}
        <Card class="p-0 overflow-hidden" hover>
          <div class="aspect-video bg-surface-800 relative overflow-hidden">
            {#if r.image_url}
              <img src={r.image_url} alt={r.model_name} class="w-full h-full object-cover" loading="lazy" />
            {:else}
              <div class="flex items-center justify-center h-full text-white/20 text-sm">{r.model_name}</div>
            {/if}
          </div>
          <div class="p-3">
            <div class="flex items-center justify-between mb-2">
              <span class="text-sm font-medium">{r.model_name}</span>
              {#if r.neural_scores}
                <span class={`text-xs font-bold ${(r.neural_scores.overall || 0) > 0.7 ? 'text-emerald-400' : 'text-dopamine-400'}`}>
                  {(r.neural_scores.overall * 100).toFixed(0)}%
                </span>
              {/if}
            </div>
            {#if r.neural_scores}
              <div class="flex gap-2 text-[10px] text-white/40">
                <span>A: {(r.neural_scores.attention * 100).toFixed(0)}%</span>
                <span>D: {(r.neural_scores.dopamine * 100).toFixed(0)}%</span>
                <span>M: {(r.neural_scores.memory * 100).toFixed(0)}%</span>
              </div>
            {/if}
            {#if r.generation_time_ms}
              <p class="text-[10px] text-white/30 mt-1">{(r.generation_time_ms / 1000).toFixed(1)}s</p>
            {/if}
          </div>
        </Card>
      {/each}
    </div>
  {/if}
</div>
