<script lang="ts">
  import { onMount } from 'svelte';
  import { gsap } from 'gsap';
  import { _ } from '$lib/i18n';
  import { success, error } from '$lib/stores/notifications';
  import Card from '$lib/components/ui/Card.svelte';
  import Button from '$lib/components/ui/Button.svelte';

  let name = $state('');
  let email = $state('');
  let password = $state('');
  let loading = $state(false);

  onMount(() => {
    gsap.from('.auth-card', { opacity: 0, y: 40, duration: 0.8, ease: 'power3.out' });
  });

  async function handleRegister(e: Event) {
    e.preventDefault();
    if (!email || !password) { error('Please fill in all fields'); return; }
    if (password.length < 6) { error('Password must be at least 6 characters'); return; }
    loading = true;
    try {
      const res = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, name: name || undefined })
      });
      const data = await res.json();
      if (data.success) {
        success($_('auth.register_success'));
        window.location.href = '/dashboard';
      } else {
        error(data.error || 'Registration failed');
      }
    } catch {
      error($_('errors.network'));
    } finally { loading = false; }
  }
</script>

<div class="min-h-screen bg-surface-950 neural-grid flex items-center justify-center p-4">
  <div class="w-full max-w-md auth-card">
    <div class="text-center mb-8">
      <div class="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br from-neural-500 to-dopamine-500 mb-4">
        <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/></svg>
      </div>
      <h1 class="text-2xl font-bold">{$_('auth.register_title')}</h1>
      <p class="text-sm text-white/50 mt-1">{$_('auth.register_subtitle')}</p>
    </div>
    <Card padding={false}>
      <form onsubmit={handleRegister} class="p-6 space-y-4">
        <div class="space-y-1.5">
          <label for="name" class="text-sm text-white/70">{$_('auth.name')}</label>
          <input id="name" type="text" bind:value={name} class="input-neural w-full" placeholder="Your name" />
        </div>
        <div class="space-y-1.5">
          <label for="email" class="text-sm text-white/70">{$_('auth.email')}</label>
          <input id="email" type="email" bind:value={email} class="input-neural w-full" placeholder="you@example.com" required />
        </div>
        <div class="space-y-1.5">
          <label for="password" class="text-sm text-white/70">{$_('auth.password')}</label>
          <input id="password" type="password" bind:value={password} class="input-neural w-full" placeholder="Min 6 characters" required minlength={6} />
        </div>
        <Button type="submit" variant="gradient" size="lg" class="w-full" loading={loading}>
          {loading ? $_('auth.registering') : $_('auth.register')}
        </Button>
      </form>
      <div class="p-4 border-t border-white/5 text-center">
        <p class="text-sm text-white/40">
          {$_('auth.has_account')} <a href="/login" class="text-neural-400 hover:text-neural-300">{$_('auth.login')}</a>
        </p>
      </div>
    </Card>
  </div>
</div>
