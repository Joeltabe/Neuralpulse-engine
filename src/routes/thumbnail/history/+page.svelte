<script lang="ts">
  import { onMount } from 'svelte';
  import { _ } from '$lib/i18n';
  import Card from '$lib/components/ui/Card.svelte';
  import Spinner from '$lib/components/ui/Spinner.svelte';

  let history: any[] = $state([]);
  let loading = $state(true);

  onMount(async () => {
    try {
      const res = await fetch('/api/thumbnail/history');
      const data = await res.json();
      if (data.success) history = data.history || data.generations || [];
    } catch { /* ignore */ }
    loading = false;
  });
</script>

<div class="max-w-6xl mx-auto space-y-6">
  <a href="/thumbnail" class="text-sm text-white/40 hover:text-white transition-colors">&larr; {$_('common.back')}</a>
  <h1 class="text-2xl font-bold">{$_('thumbnail.history')}</h1>

  {#if loading}
    <div class="flex justify-center py-16"><Spinner size="lg" /></div>
  {:else if history.length === 0}
    <Card class="text-center py-12"><p class="text-white/40">No thumbnail generations yet</p></Card>
  {:else}
    <div class="space-y-3">
      {#each history as item}
        <Card class="flex items-start gap-4">
          {#if item.image_url || item.preview_url}
            <div class="w-24 aspect-video rounded-lg overflow-hidden shrink-0 bg-surface-800">
              <img src={item.image_url || item.preview_url} alt="" class="w-full h-full object-cover" />
            </div>
          {/if}
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium truncate">{item.prompt || item.model_name || 'Generation'}</p>
            <p class="text-xs text-white/40 mt-0.5">{item.model_name} &middot; {(item.generation_time_ms / 1000).toFixed(1)}s</p>
            {#if item.created_at}<p class="text-xs text-white/30 mt-1">{new Date(item.created_at).toLocaleDateString()}</p>{/if}
          </div>
          {#if item.neural_scores?.overall}
            <div class="text-right">
              <span class="text-lg font-bold gradient-text">{(item.neural_scores.overall * 100).toFixed(0)}%</span>
            </div>
          {/if}
        </Card>
      {/each}
    </div>
  {/if}
</div>
