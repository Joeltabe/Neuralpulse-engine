<script lang="ts">
  import { _ } from '$lib/i18n';
  import { error as showError } from '$lib/stores/notifications';
  import Card from '$lib/components/ui/Card.svelte';
  import Button from '$lib/components/ui/Button.svelte';
  import Input from '$lib/components/ui/Input.svelte';
  import Spinner from '$lib/components/ui/Spinner.svelte';
  import ScoreCard from '$lib/components/analysis/ScoreCard.svelte';

  let original = $state('');
  let variants = $state<string[]>(['']);
  let loading = $state(false);
  let result: any = $state(null);

  async function analyze() {
    if (!original.trim() || variants.filter(v => v.trim()).length === 0) return;
    loading = true;
    try {
      const res = await fetch('/api/copy/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ original_copy: original, variants: variants.filter(v => v.trim()) })
      });
      const data = await res.json();
      if (data.success) result = data.data;
      else showError(data.error || 'Analysis failed');
    } catch { showError($_('errors.network')); }
    finally { loading = false; }
  }
</script>

<div class="max-w-6xl mx-auto space-y-6">
  <h1 class="text-2xl font-bold">{$_('nav.copywriting')}</h1>

  <Card>
    <div class="space-y-4">
      <Input type="textarea" label="Original Copy" placeholder="Paste your original copy here..." bind:value={original} />
      <div class="space-y-3">
        {#each variants as _, i}
          <Input type="textarea" label={`Variant ${i+1}`} placeholder={`Variant ${i+1} copy...`} bind:value={variants[i]} />
        {/each}
        <Button onclick={() => variants = [...variants, '']} variant="secondary" size="sm">+ Add Variant</Button>
      </div>
      <Button onclick={analyze} variant="gradient" size="lg" class="w-full" disabled={!original.trim() || variants.filter(v => v.trim()).length === 0} loading={loading} />
    </div>
  </Card>

  {#if result}
    <Card glow>
      <h2 class="text-lg font-semibold mb-4">Winner: <span class="gradient-text">{result.winning_variant || 'Original'}</span></h2>
      {#if result.comparison?.scores}
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {#each Object.entries(result.comparison.scores as Record<string, any>) as [name, scores]}
            <ScoreCard label={name} value={scores.overall || 0} color="#4d6cf5" sublabel={`A: ${(scores.attention*100).toFixed(0)}% D: ${(scores.dopamine*100).toFixed(0)}% M: ${(scores.memory*100).toFixed(0)}%`} />
          {/each}
        </div>
      {/if}
      {#if result.recommendations?.length}
        <Card class="mt-4">
          <ul class="space-y-2">
            {#each result.recommendations as rec}<li class="text-sm text-white/60 flex items-start gap-2"><span class="text-neural-400 mt-0.5">•</span>{rec}</li>{/each}
          </ul>
        </Card>
      {/if}
    </Card>
  {/if}
</div>
