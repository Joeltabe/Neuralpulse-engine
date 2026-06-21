<script lang="ts">
  import { onMount, tick } from 'svelte';
  import { gsap } from 'gsap';
  import { page } from '$app/stores';
  import { _ } from '$lib/i18n';
  import Card from '$lib/components/ui/Card.svelte';
  import Button from '$lib/components/ui/Button.svelte';
  import Spinner from '$lib/components/ui/Spinner.svelte';
  import { success, error as showError } from '$lib/stores/notifications';
  import { detectCardType, formatCardNumber, formatExpiry, isValidCardNumber, isValidExpiry, isValidCvc, isValidPhone, CARD_LOGOS, type CardInfo } from '$lib/utils/card';

  let step = $state<'select' | 'method' | 'pay' | 'confirm'>('select');
  let packages = $state<{ id: number; name: string; tokens: number; price_cents: number; price_display: string; popular: boolean; description: string }[]>([]);
  let selectedPkg: typeof packages[0] | null = $state(null);
  let preselectedId = $derived(parseInt($page.url.searchParams.get('pkg') || '0', 10));
  let method = $state<'orange' | 'mtn' | 'card' | null>(null);
  let loading = $state(false);
  let paid = $state(false);

  let cardNum = $state('');
  let cardType = $state<CardInfo | null>(null);
  let cardExpiry = $state('');
  let cardCvc = $state('');
  let cardName = $state('');
  let phone = $state('');
  let result: any = $state(null);

  let selectRef: HTMLDivElement;
  let methodRef: HTMLDivElement;
  let formRef: HTMLDivElement;
  let confirmRef: HTMLDivElement;

  let detectedCard = $derived(detectCardType(cardNum));
  let cardValid = $derived(isValidCardNumber(cardNum, detectedCard));
  let expiryValid = $derived(isValidExpiry(cardExpiry));
  let cvcValid = $derived(isValidCvc(cardCvc, detectedCard));
  let phoneValid = $derived(isValidPhone(phone));
  let formValid = $derived(method === 'card' ? (cardValid && expiryValid && cvcValid && cardName.trim().length > 0) : phoneValid);

  onMount(async () => {
    const url = $page.url;
    if (url.searchParams.has('success')) { paid = true; animateIn('.confirm-section'); return; }
    try {
      const res = await fetch('/api/billing/packages');
      const data = await res.json();
      if (data.success && data.packages) {
        packages = data.packages;
        if (preselectedId) {
          const match = packages.find(p => p.id === preselectedId);
          if (match) { selectedPkg = match; transitionTo('method'); return; }
        }
      }
    } catch { /* ignore */ }
    await tick();
    animateIn('.select-section');
  });

  function animateIn(sel: string) {
    gsap.fromTo(sel, { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.5, ease: 'power3.out' });
  }

  function transitionTo(next: 'select' | 'method' | 'pay' | 'confirm') {
    step = next;
    tick().then(() => {
      const map: Record<string, string> = { select: '.select-section', method: '.method-section', pay: '.pay-section', confirm: '.confirm-section' };
      animateIn(map[next]);
    });
  }

  function selectPackage(pkg: typeof packages[0]) {
    selectedPkg = pkg;
    transitionTo('method');
  }

  function selectMethod(m: 'orange' | 'mtn' | 'card') {
    method = m;
    transitionTo('pay');
  }

  function handleCardInput(e: Event) {
    const input = e.target as HTMLInputElement;
    let val = input.value;
    cardType = detectCardType(val);
    cardNum = formatCardNumber(val, cardType);
  }

  async function submitPayment() {
    if (!selectedPkg || !method || !formValid) return;
    loading = true;
    try {
      const body = method === 'card'
        ? { package_id: selectedPkg.id, payment_method: 'card' }
        : { package_id: selectedPkg.id, provider: method, phone };

      const ep = method === 'card' ? '/api/billing/purchase' : '/api/billing/mobile-payment';
      const res = await fetch(ep, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      if (data.checkout_url) { window.location.href = data.checkout_url; return; }
      if (data.success) {
        paid = true;
        result = data;
        transitionTo('confirm');
        success(`Payment successful! ${selectedPkg.tokens} tokens added.`);
      } else {
        showError(data.error || 'Payment failed');
      }
    } catch { showError('Network error'); }
    finally { loading = false; }
  }
</script>

<div class="max-w-2xl mx-auto">
  {#if step === 'select'}
    <div class="select-section space-y-6" bind:this={selectRef}>
      <div class="text-center space-y-2">
        <h1 class="text-3xl font-bold gradient-text">Token Packages</h1>
        <p class="text-white/50">Choose a package to get started</p>
      </div>
      <div class="space-y-3">
        {#each packages as pkg, i}
          <button onclick={() => selectPackage(pkg)}
            class="w-full glass rounded-2xl p-5 card-hover flex items-center justify-between group text-left"
            style="animation-delay: {i * 0.1}s"
          >
            <div class="flex items-center gap-4">
              <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-neural-500/20 to-dopamine-500/10 flex items-center justify-center text-lg font-bold text-neural-300">
                {pkg.tokens >= 1000 ? (pkg.tokens / 1000) + 'K' : pkg.tokens}
              </div>
              <div>
                <h3 class="font-semibold">{pkg.name}</h3>
                <p class="text-xs text-white/40">{pkg.tokens} tokens</p>
              </div>
            </div>
            <div class="text-right flex items-center gap-3">
              <div>
                <p class="text-xl font-bold gradient-text">{pkg.price_display}</p>
                {#if pkg.popular}
                  <span class="text-[10px] bg-neural-500/20 text-neural-400 px-2 py-0.5 rounded-full">Best Value</span>
                {/if}
              </div>
              <svg class="w-5 h-5 text-white/20 group-hover:text-neural-400 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
            </div>
          </button>
        {/each}
      </div>
    </div>
  {/if}

  {#if step === 'method'}
    <div class="method-section space-y-6 opacity-0" bind:this={methodRef}>
      <button onclick={() => transitionTo('select')} class="text-sm text-white/40 hover:text-white flex items-center gap-1">&larr; Back</button>
      <div class="text-center space-y-2">
        <h1 class="text-2xl font-bold">Payment Method</h1>
        <p class="text-white/50">{selectedPkg?.name} — {selectedPkg?.price_display}</p>
      </div>
      <div class="space-y-3">
        <button onclick={() => selectMethod('orange')}
          class="w-full glass rounded-2xl p-5 card-hover flex items-center gap-4 group text-left"
        >
          <div class="w-12 h-12 rounded-xl bg-white/5 flex items-center justify-center p-2">
            <img src="/orange.png" alt="Orange Money" class="w-full h-full object-contain" />
          </div>
          <div>
            <h3 class="font-semibold">Orange Money</h3>
            <p class="text-xs text-white/40">Pay with Orange Money</p>
          </div>
        </button>
        <button onclick={() => selectMethod('mtn')}
          class="w-full glass rounded-2xl p-5 card-hover flex items-center gap-4 group text-left"
        >
          <div class="w-12 h-12 rounded-xl bg-white/5 flex items-center justify-center p-2">
            <img src="/mtn-1.jpg" alt="MTN MoMo" class="w-full h-full object-contain rounded" />
          </div>
          <div>
            <h3 class="font-semibold">MTN MoMo</h3>
            <p class="text-xs text-white/40">Pay with MTN Mobile Money</p>
          </div>
        </button>
        <button onclick={() => selectMethod('card')}
          class="w-full glass rounded-2xl p-5 card-hover flex items-center gap-4 group text-left"
        >
          <div class="w-12 h-12 rounded-xl bg-neural-500/10 flex items-center justify-center text-xl">💳</div>
          <div>
            <h3 class="font-semibold">Credit / Debit Card</h3>
            <p class="text-xs text-white/40">Visa, Mastercard, Amex & more</p>
          </div>
        </button>
      </div>
    </div>
  {/if}

  {#if step === 'pay'}
    <div class="pay-section space-y-6 opacity-0" bind:this={formRef}>
      <button onclick={() => transitionTo('method')} class="text-sm text-white/40 hover:text-white flex items-center gap-1">&larr; Back</button>
      <Card>
        <div class="space-y-6">
          <div class="flex items-center justify-between">
            <h2 class="text-xl font-bold">{selectedPkg?.name}</h2>
            <span class="text-2xl font-bold gradient-text">{selectedPkg?.price_display}</span>
          </div>
          <div class="h-px bg-white/5"></div>

          {#if method === 'card'}
            <div class="space-y-4">
              <div class="relative">
                <label class="text-xs text-white/40 uppercase tracking-wider block mb-1.5">Card Number</label>
                <div class="relative">
                  <input
                    type="tel" inputmode="numeric" maxlength="23" placeholder="1234 5678 9012 3456"
                    value={cardNum} oninput={handleCardInput}
                    class="input-neural w-full text-lg tracking-wider pr-12 font-mono"
                  />
                  <div class="absolute right-3 top-1/2 -translate-y-1/2">
                    {#if detectedCard}
                      {@html CARD_LOGOS[detectedCard.type] || ''}
                    {:else if cardNum.length > 0}
                      <span class="text-xs text-white/30">?</span>
                    {/if}
                  </div>
                </div>
              </div>
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label class="text-xs text-white/40 uppercase tracking-wider block mb-1.5">Expiry</label>
                  <input type="tel" inputmode="numeric" maxlength="7" placeholder="MM / YY"
                    value={cardExpiry} oninput={(e) => cardExpiry = formatExpiry((e.target as HTMLInputElement).value)}
                    class="input-neural w-full text-center font-mono"
                  />
                </div>
                <div>
                  <label class="text-xs text-white/40 uppercase tracking-wider block mb-1.5">CVC</label>
                  <input type="tel" inputmode="numeric" maxlength="4" placeholder="***"
                    value={cardCvc} oninput={(e) => cardCvc = (e.target as HTMLInputElement).value.replace(/\D/g, '').slice(0, 4)}
                    class="input-neural w-full text-center font-mono"
                  />
                </div>
              </div>
              <div>
                <label class="text-xs text-white/40 uppercase tracking-wider block mb-1.5">Cardholder Name</label>
                <input type="text" placeholder="John Doe"
                  bind:value={cardName}
                  class="input-neural w-full"
                />
              </div>
            </div>
          {:else}
            <div class="space-y-4">
              <div class="flex items-center gap-4 p-4 rounded-xl bg-white/5">
                <div class="w-10 h-10 rounded-lg flex items-center justify-center p-1.5 bg-white/5">
                  <img src={method === 'orange' ? '/orange.png' : '/mtn-1.jpg'} alt={method === 'orange' ? 'Orange Money' : 'MTN MoMo'} class="w-full h-full object-contain rounded" />
                </div>
                <div>
                  <p class="font-semibold">{method === 'orange' ? 'Orange Money' : 'MTN MoMo'}</p>
                  <p class="text-xs text-white/40">You will receive a payment request on your phone</p>
                </div>
              </div>
              <div>
                <label class="text-xs text-white/40 uppercase tracking-wider block mb-1.5">Phone Number</label>
                <input type="tel" inputmode="numeric" placeholder="+237 6XX XXX XXX"
                  bind:value={phone}
                  class="input-neural w-full text-lg"
                />
              </div>
            </div>
          {/if}

          <div class="h-px bg-white/5"></div>

          <div class="flex items-center justify-between text-sm">
            <span class="text-white/50">You will receive</span>
            <span class="font-bold text-lg">{selectedPkg?.tokens} tokens</span>
          </div>

          <Button onclick={submitPayment} variant="gradient" size="lg" class="w-full" disabled={!formValid} loading={loading}>
            {loading ? 'Processing...' : `Pay ${selectedPkg?.price_display}`}
          </Button>
        </div>
      </Card>
    </div>
  {/if}

  {#if step === 'confirm' && paid}
    <div class="confirm-section space-y-6 opacity-0" bind:this={confirmRef}>
      <div class="text-center space-y-4 py-8">
        <div class="inline-flex items-center justify-center w-20 h-20 rounded-full bg-emerald-500/20 animate-bounce-in">
          <svg class="w-10 h-10 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
        </div>
        <h1 class="text-3xl font-bold gradient-text">Payment Successful!</h1>
        <p class="text-white/50">{selectedPkg?.tokens} tokens have been added to your account</p>
      </div>
      <Card glow class="text-center space-y-3">
        <div class="grid grid-cols-2 gap-4 text-sm">
          <div class="p-3 rounded-xl bg-white/5">
            <p class="text-white/40">Package</p>
            <p class="font-semibold mt-1">{selectedPkg?.name}</p>
          </div>
          <div class="p-3 rounded-xl bg-white/5">
            <p class="text-white/40">Tokens</p>
            <p class="font-semibold mt-1">{selectedPkg?.tokens}</p>
          </div>
          <div class="p-3 rounded-xl bg-white/5">
            <p class="text-white/40">Amount</p>
            <p class="font-semibold mt-1">{selectedPkg?.price_display}</p>
          </div>
          <div class="p-3 rounded-xl bg-white/5">
            <p class="text-white/40">Reference</p>
            <p class="font-semibold mt-1 text-xs truncate">{result?.payment_ref || result?.transaction?.id || '—'}</p>
          </div>
        </div>
      </Card>
      <div class="flex justify-center gap-3">
        <Button href="/dashboard" variant="gradient">Go to Dashboard</Button>
        <Button href="/analyze" variant="secondary">Analyze Content</Button>
      </div>
    </div>
  {/if}

  {#if paid && step !== 'confirm'}
    <div class="text-center space-y-4 py-16">
      <div class="inline-flex items-center justify-center w-20 h-20 rounded-full bg-emerald-500/20">
        <svg class="w-10 h-10 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
      </div>
      <h1 class="text-2xl font-bold gradient-text">Payment Successful!</h1>
      <div class="flex justify-center gap-3 mt-4">
        <Button href="/dashboard" variant="gradient">Go to Dashboard</Button>
        <Button href="/analyze" variant="secondary">Analyze Content</Button>
      </div>
    </div>
  {/if}
</div>
