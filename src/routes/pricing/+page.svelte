<script lang="ts">
  import { _ } from '$lib/i18n';
  import Card from '$lib/components/ui/Card.svelte';
  import Button from '$lib/components/ui/Button.svelte';
  import { success } from '$lib/stores/notifications';

  const plans = [
    { name: 'Starter', tokens: '100', price: '$9', features: ['Video analysis', 'Audio analysis', 'Text analysis', 'Basic brain scores'], popular: false },
    { name: 'Creator', tokens: '500', price: '$29', features: ['Everything in Starter', 'A/B testing', 'Copywriting analysis', 'Priority support', 'Brain explorer full access'], popular: true },
    { name: 'Pro', tokens: '2000', price: '$79', features: ['Everything in Creator', 'Thumbnail generation', 'API access', 'Team members (5)', 'Dedicated support'], popular: false },
    { name: 'Enterprise', tokens: '10000', price: '$249', features: ['Everything in Pro', 'Unlimited team members', 'Custom models', 'SLA guarantee', 'On-premise option'], popular: false }
  ];

  async function purchase(plan: string) {
    try {
      const priceMap: Record<string, string> = { Starter: 'price_starter_9', Creator: 'price_creator_29', Pro: 'price_pro_79', Enterprise: 'price_enterprise_249' };
      const res = await fetch('/api/billing/purchase', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ price_id: priceMap[plan] })
      });
      const data = await res.json();
      if (data.url) window.location.href = data.url;
      else if (data.success) success(`Purchased ${plan} plan!`);
    } catch { /* ignore */ }
  }
</script>

<div class="max-w-6xl mx-auto space-y-8">
  <div class="text-center">
    <h1 class="text-3xl font-bold">{$_('pricing.title')}</h1>
    <p class="text-white/50 mt-2">{$_('pricing.subtitle')}</p>
  </div>

  <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
    {#each plans as plan}
      <Card glow={plan.popular} class={`relative flex flex-col ${plan.popular ? 'border-neural-500/30' : ''}`}>
        {#if plan.popular}
          <div class="absolute -top-2.5 left-1/2 -translate-x-1/2 bg-neural-500 text-black text-[10px] font-bold px-3 py-0.5 rounded-full">POPULAR</div>
        {/if}
        <h3 class="text-lg font-bold">{plan.name}</h3>
        <div class="mt-2"><span class="text-3xl font-bold">{plan.price}</span><span class="text-sm text-white/40">/mo</span></div>
        <p class="text-sm text-white/50 mt-1">{plan.tokens} tokens/mo</p>
        <ul class="mt-4 space-y-2 flex-1">
          {#each plan.features as f}
            <li class="text-xs text-white/60 flex items-start gap-2"><span class="text-emerald-400 mt-0.5">✓</span>{f}</li>
          {/each}
        </ul>
        <Button onclick={() => purchase(plan.name)} variant={plan.popular ? 'gradient' : 'secondary'} class="mt-6 w-full">Get Started</Button>
      </Card>
    {/each}
  </div>
</div>
