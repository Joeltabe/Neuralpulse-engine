<script lang="ts">
  import { onMount } from 'svelte';
  import { gsap } from 'gsap';
  import { _ } from '$lib/i18n';
  import { success, error } from '$lib/stores/notifications';
  import Card from '$lib/components/ui/Card.svelte';
  import Button from '$lib/components/ui/Button.svelte';
  import Magnetic from '$lib/components/effects/Magnetic.svelte';

  let email = $state('');
  let password = $state('');
  let loading = $state(false);
  let cardEl: HTMLDivElement;
  let formEl: HTMLFormElement;
  let inputs: HTMLInputElement[] = [];

  onMount(() => {
    const tl = gsap.timeline({ defaults: { ease: 'power3.out' } });
    tl.from('.auth-logo', { opacity: 0, scale: 0, rotation: -180, duration: 0.8, ease: 'back.out(1.7)' })
      .from('.auth-title', { opacity: 0, y: 20, duration: 0.5 }, '-=0.3')
      .from('.auth-subtitle', { opacity: 0, y: 10, duration: 0.4 }, '-=0.2')
      .from('.auth-field', { opacity: 0, y: 15, duration: 0.4, stagger: 0.1 }, '-=0.2')
      .from('.auth-btn', { opacity: 0, y: 15, scale: 0.95, duration: 0.4 }, '-=0.1')
      .from('.auth-footer', { opacity: 0, y: 10, duration: 0.3 }, '-=0.1');

    gsap.utils.toArray<HTMLElement>('.auth-orb').forEach((orb) => {
      gsap.to(orb, {
        x: () => gsap.utils.random(-20, 20),
        y: () => gsap.utils.random(-20, 20),
        scale: 1.05,
        duration: 4 + Math.random() * 2,
        repeat: -1,
        yoyo: true,
        ease: 'sine.inOut'
      });
    });

    inputs.forEach((el) => {
      el.addEventListener('focus', () => {
        gsap.to(el, { scale: 1.02, borderColor: 'rgba(77,108,245,0.4)', duration: 0.2 });
      });
      el.addEventListener('blur', () => {
        gsap.to(el, { scale: 1, borderColor: 'rgba(255,255,255,0.1)', duration: 0.2 });
      });
    });
  });

  async function handleLogin(e: Event) {
    e.preventDefault();
    if (!email || !password) { error('Please fill in all fields'); return; }
    loading = true;
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });
      const data = await res.json();
      if (data.success) {
        success($_('auth.login_success'));
        gsap.to(cardEl, { opacity: 0, y: -20, scale: 0.95, duration: 0.3, onComplete: () => { window.location.href = '/dashboard'; } });
      } else {
        error(data.error || 'Login failed');
        gsap.fromTo(formEl, { x: -5 }, { x: 5, duration: 0.05, repeat: 3, yoyo: true, ease: 'none' });
      }
    } catch {
      error($_('errors.network'));
    } finally { loading = false; }
  }

  async function handleDemo() {
    loading = true;
    try {
      const res = await fetch('/api/auth/demo-login', { method: 'POST' });
      const data = await res.json();
      if (data.success) {
        success('Logged in as demo user');
        gsap.to(cardEl, { opacity: 0, y: -20, scale: 0.95, duration: 0.3, onComplete: () => { window.location.href = '/dashboard'; } });
      } else {
        error(data.error || 'Demo login failed');
      }
    } catch {
      error($_('errors.network'));
    } finally { loading = false; }
  }
</script>

<div class="min-h-screen neural-grid flex items-center justify-center p-4 relative overflow-hidden">
  <div class="auth-orb fixed top-1/4 -left-32 w-96 h-96 rounded-full bg-neural-500/10 blur-3xl pointer-events-none" style="will-change: transform;"></div>
  <div class="auth-orb fixed bottom-1/4 -right-32 w-96 h-96 rounded-full bg-dopamine-500/10 blur-3xl pointer-events-none" style="will-change: transform;"></div>
  <div class="auth-orb fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] rounded-full bg-memory-500/5 blur-3xl pointer-events-none" style="will-change: transform;"></div>

  <div bind:this={cardEl} class="auth-card w-full max-w-md relative z-10">
    <div class="text-center mb-8">
      <div class="auth-logo inline-flex items-center justify-center w-14 h-14 rounded-xl bg-gradient-to-br from-neural-500 to-dopamine-500 mb-4 shadow-lg shadow-neural-500/20">
        <svg class="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/></svg>
      </div>
      <h1 class="auth-title text-2xl font-bold">{$_('auth.login_title')}</h1>
      <p class="auth-subtitle text-sm text-white/50 mt-1">{$_('auth.login_subtitle')}</p>
    </div>

    <Card padding={false}>
      <form bind:this={formEl} onsubmit={handleLogin} class="p-6 space-y-4">
        <div class="auth-field space-y-1.5">
          <label for="email" class="text-sm text-white/70">{$_('auth.email')}</label>
          <input bind:this={inputs[0]} id="email" type="email" bind:value={email} class="input-neural w-full" placeholder="you@example.com" required />
        </div>
        <div class="auth-field space-y-1.5">
          <label for="password" class="text-sm text-white/70">{$_('auth.password')}</label>
          <input bind:this={inputs[1]} id="password" type="password" bind:value={password} class="input-neural w-full" placeholder="••••••••" required />
        </div>
        <div class="auth-btn">
          <Button type="submit" variant="gradient" size="lg" class="w-full" loading={loading}>
            {loading ? $_('auth.logging_in') : $_('auth.login')}
          </Button>
        </div>
      </form>
      <div class="auth-footer p-4 border-t border-white/5 text-center space-y-2">
        <Magnetic strength={0.15} radius={100}>
          <Button onclick={handleDemo} variant="secondary" size="md" class="w-full" loading={loading}>
            {$_('auth.demo_login')}
          </Button>
        </Magnetic>
        <p class="text-sm text-white/40">
          {$_('auth.no_account')} <a href="/register" class="text-neural-400 hover:text-neural-300 transition-colors">{$_('auth.sign_up')}</a>
        </p>
      </div>
    </Card>
  </div>
</div>
