<script lang="ts">
  import { _ } from '$lib/i18n';
  import { page } from '$app/stores';
  import Card from '$lib/components/ui/Card.svelte';
  import Button from '$lib/components/ui/Button.svelte';
  import Input from '$lib/components/ui/Input.svelte';
  import { success, error as showError } from '$lib/stores/notifications';

  let locale = $state($page.data.locale || 'en');
  let name = $state($page.data.user?.name || '');
  let deleting = $state(false);

  async function updateProfile() {
    try {
      const res = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name })
      });
      const data = await res.json();
      if (data.success) success('Profile updated');
      else showError(data.error || 'Failed');
    } catch { showError('Network error'); }
  }

  async function deleteAccount() {
    if (!confirm('Are you sure you want to delete your account? This cannot be undone.')) return;
    deleting = true;
    try {
      const res = await fetch('/api/auth/logout', { method: 'POST' });
      await res.json();
      window.location.href = '/';
    } catch { /* ignore */ }
    deleting = false;
  }

  function setLocale(l: string) {
    locale = l;
    document.cookie = `locale=${l};path=/;max-age=31536000;SameSite=Lax`;
    location.reload();
  }
</script>

<div class="max-w-4xl mx-auto space-y-6">
  <h1 class="text-2xl font-bold">{$_('settings.title')}</h1>

  <Card>
    <h2 class="text-sm font-semibold mb-3">{$_('settings.profile')}</h2>
    <div class="space-y-3">
      <Input label="Name" bind:value={name} />
      <Button onclick={updateProfile} variant="primary">Save</Button>
    </div>
  </Card>

  <Card>
    <h2 class="text-sm font-semibold mb-3">{$_('settings.language')}</h2>
    <div class="flex gap-2">
      <button onclick={() => setLocale('en')} class={`px-4 py-2 rounded-xl text-sm ${locale === 'en' ? 'bg-neural-500/20 text-neural-300 border border-neural-500/20' : 'glass text-white/50'}`}>English</button>
      <button onclick={() => setLocale('es')} class={`px-4 py-2 rounded-xl text-sm ${locale === 'es' ? 'bg-neural-500/20 text-neural-300 border border-neural-500/20' : 'glass text-white/50'}`}>Español</button>
    </div>
  </Card>

  <Card>
    <h2 class="text-sm font-semibold mb-3">{$_('settings.danger_zone')}</h2>
    <p class="text-xs text-white/40 mb-3">Delete your account and all associated data. This action is irreversible.</p>
    <Button onclick={deleteAccount} variant="danger" loading={deleting}>Delete Account</Button>
  </Card>
</div>
