<script lang="ts">
  import { onMount, tick } from 'svelte';
  import { gsap } from 'gsap';
  import { _ } from '$lib/i18n';
  import Card from '$lib/components/ui/Card.svelte';
  import Button from '$lib/components/ui/Button.svelte';
  import Spinner from '$lib/components/ui/Spinner.svelte';
  let packages = $state<{ id: number; name: string; tokens: number; price_display: string; popular: boolean; description: string }[]>([]);
  let loading = $state(true);

  onMount(async () => {
    try {
      const res = await fetch('/api/billing/packages');
      const data = await res.json();
      if (data.success && data.packages) packages = data.packages;
    } catch { /* ignore */ }
    finally { loading = false; }

    await tick();
    gsap.to('.pkg-card', { opacity: 1, y: 0, duration: 0.6, stagger: 0.12, ease: 'power3.out', delay: 0.1 });
  });

  const tokenCosts = [
    { label: 'Video analysis', cost: '50 tokens' },
    { label: 'Audio analysis', cost: '30 tokens' },
    { label: 'Text analysis', cost: '10 tokens' },
    { label: 'A/B test', cost: '25 tokens' },
    { label: 'Thumbnail generation', cost: '15 tokens' },
  ];
</script>

<div class="max-w-6xl mx-auto space-y-8">
  <div class="text-center space-y-3">
    <h1 class="text-3xl font-bold gradient-text">Token Packages</h1>
    <p class="text-white/50 max-w-md mx-auto">Purchase tokens to analyze content with our neural engine</p>
  </div>

  {#if loading}
    <div class="flex justify-center py-16"><Spinner size="lg" /></div>
  {:else}
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
      {#each packages as pkg, i}
        <Card glow={pkg.popular} class="pkg-card relative flex flex-col overflow-hidden opacity-0 translate-y-[30px]" style="animation-delay: {i * 0.1}s">
          {#if pkg.popular}
            <div class="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-neural-500 via-dopamine-500 to-memory-500"></div>
            <div class="absolute -top-2.5 left-1/2 -translate-x-1/2 bg-neural-500 text-black text-[10px] font-bold px-4 py-0.5 rounded-full">POPULAR</div>
          {/if}
          <div class="flex-1 space-y-4">
            <div>
              <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-neural-500/20 to-dopamine-500/10 flex items-center justify-center text-lg font-bold text-neural-300 mb-3">
                {pkg.tokens >= 1000 ? (pkg.tokens / 1000) + 'K' : pkg.tokens}
              </div>
              <h3 class="text-xl font-bold">{pkg.name}</h3>
              <div class="mt-2"><span class="text-4xl font-black gradient-text">{pkg.price_display}</span></div>
              <p class="text-sm text-white/40 mt-1">one-time payment</p>
            </div>
            {#if pkg.description}
              <p class="text-sm text-white/50">{pkg.description}</p>
            {/if}
            <ul class="space-y-2 pt-2">
              <li class="text-xs text-white/60 flex items-center gap-2"><svg class="w-3.5 h-3.5 text-emerald-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7"/></svg>{pkg.tokens} tokens</li>
              <li class="text-xs text-white/60 flex items-center gap-2"><svg class="w-3.5 h-3.5 text-emerald-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7"/></svg>All analysis types</li>
              <li class="text-xs text-white/60 flex items-center gap-2"><svg class="w-3.5 h-3.5 text-emerald-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7"/></svg>No expiration</li>
            </ul>
          </div>
            <Button href={'/payment?pkg=' + pkg.id} variant={pkg.popular ? 'gradient' : 'secondary'} class="mt-6 w-full">Purchase</Button>
        </Card>
      {/each}
    </div>

    <!-- Token Costs -->
    <Card class="max-w-lg mx-auto">
      <h3 class="text-sm font-semibold mb-3 text-center">Token Costs Per Analysis</h3>
      <div class="space-y-2">
        {#each tokenCosts as tc}
          <div class="flex items-center justify-between text-sm">
            <span class="text-white/60">{tc.label}</span>
            <span class="text-dopamine-400 font-medium">{tc.cost}</span>
          </div>
        {/each}
      </div>
    </Card>

    <!-- Payment Methods Preview -->
    <div class="text-center space-y-4">
      <p class="text-sm text-white/40">Accepted payment methods</p>
      <div class="flex justify-center gap-4">
        <div class="glass rounded-xl px-4 py-2 flex items-center gap-2 text-sm text-white/60">
          <img src="/orange.png" alt="Orange Money" class="w-5 h-5 object-contain" />
          Orange Money
        </div>
        <div class="glass rounded-xl px-4 py-2 flex items-center gap-2 text-sm text-white/60">
          <img src="/mtn-1.jpg" alt="MTN MoMo" class="w-5 h-5 object-contain rounded" />
          MTN MoMo
        </div>
        <div class="glass rounded-xl px-4 py-2 flex items-center gap-2 text-sm text-white/60">
          <span>💳</span> Card
        </div>
      </div>
    </div>
  {/if}
</div>
