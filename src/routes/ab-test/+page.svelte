<script lang="ts">
  import { _ } from '$lib/i18n';
  import { error as showError } from '$lib/stores/notifications';
  import Card from '$lib/components/ui/Card.svelte';
  import Button from '$lib/components/ui/Button.svelte';
  import Input from '$lib/components/ui/Input.svelte';
  import FileUpload from '$lib/components/ui/FileUpload.svelte';
  import Spinner from '$lib/components/ui/Spinner.svelte';
  import ScoreCard from '$lib/components/analysis/ScoreCard.svelte';

  let mode = $state<'video' | 'audio' | 'text'>('video');
  let textVariants = $state<string[]>(['', '']);
  let files = $state<File[]>([]);
  let loading = $state(false);
  let result: any = $state(null);

  async function compare() {
    loading = true;
    try {
      const form = new FormData();
      form.append('mode', mode);

      if (mode === 'text') {
        const trimmed = textVariants.filter(t => t.trim());
        form.append('texts', JSON.stringify(trimmed));
        form.append('variant_names', JSON.stringify(trimmed.map((_, i) => `Variant ${i + 1}`)));
      } else {
        files.forEach(f => form.append('files', f));
      }

      const res = await fetch('/api/analyze/ab-test', { method: 'POST', body: form });
      const data = await res.json();
      if (data.success) result = data.data;
      else showError(data.error || 'A/B test failed');
    } catch { showError($_('errors.network')); }
    finally { loading = false; }
  }
</script>

<div class="max-w-6xl mx-auto space-y-6">
  <h1 class="text-2xl font-bold">{$_('ab_test.title')}</h1>

  <div class="flex gap-2">
    {#each ['video', 'audio', 'text'] as m}
      <button onclick={() => mode = m as 'video' | 'audio' | 'text'} class={`px-4 py-2 rounded-xl text-sm font-medium transition-colors ${mode === m ? 'bg-neural-500/20 text-neural-300 border border-neural-500/20' : 'glass text-white/50'}`}>{m}</button>
    {/each}
  </div>

  {#if mode === 'text'}
    <Card>
      <div class="space-y-3">
        {#each textVariants as _, i}
          <Input type="textarea" placeholder={`Variant ${i + 1}`} bind:value={textVariants[i]} />
        {/each}
        <Button onclick={() => textVariants = [...textVariants, '']} variant="secondary" size="sm">+ Add Variant</Button>
      </div>
    </Card>
  {:else}
    <Card>
      <FileUpload accept={mode === 'video' ? '.mp4,.mov,.avi,.webm,.mkv' : '.mp3,.wav,.ogg,.m4a,.flac'} label={`Drop ${mode} files here`} multiple onupload={(f: File | File[]) => files = Array.isArray(f) ? f : [f]} />
      {#if files.length > 0}
        <div class="mt-3 space-y-1">
          {#each files as f, i}
            <div class="text-sm text-white/60">Variant {i + 1}: {f.name}</div>
          {/each}
        </div>
      {/if}
    </Card>
  {/if}

  <Button onclick={compare} variant="gradient" size="lg" class="w-full" disabled={mode === 'text' ? textVariants.filter(t => t.trim()).length < 2 : files.length < 2} loading={loading}>
    {loading ? 'Comparing...' : 'Compare Variants'}
  </Button>

  {#if loading}
    <div class="flex justify-center py-8"><Spinner size="lg" /></div>
  {/if}

  {#if result}
    <Card glow>
      <h2 class="text-lg font-semibold mb-4">{$_('ab_test.winner')}: <span class="gradient-text">{result.winning_variant}</span></h2>
      <p class="text-sm text-white/60 mb-4">{result.recommendation}</p>
      {#if result.dimension_comparison}
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          {#each Object.entries(result.dimension_comparison as Record<string, number[]>) as [dim, vals]}
            <ScoreCard label={dim} value={Math.max(...vals)} color="#4d6cf5" sublabel={`${vals.length} variants`} />
          {/each}
        </div>
      {/if}
    </Card>
  {/if}
</div>
