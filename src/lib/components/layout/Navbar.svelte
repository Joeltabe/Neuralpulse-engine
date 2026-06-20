<script lang="ts">
  import { page } from '$app/stores';
  import { formatTokens } from '$lib/utils/formatters';
  import { _ } from '$lib/i18n';

  let { onToggle }: { onToggle: (e: MouseEvent) => void } = $props();
  let data = $page.data;
  let user = $derived(data.user);
</script>

<header class="shrink-0 glass border-b border-white/5 px-4 md:px-6 h-16 flex items-center justify-between">
  <div class="flex items-center gap-3">
    <button onclick={onToggle} class="lg:hidden text-white/50 hover:text-white p-2 -ml-2" aria-label="Toggle menu">
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/></svg>
    </button>
    <div class="hidden sm:flex items-center gap-2">
      <span class="text-sm text-white/40">{$_('common.app_name')}</span>
    </div>
  </div>
  <div class="flex items-center gap-4">
    {#if user}
      <div class="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-dopamine-500/10 border border-dopamine-500/20">
        <svg class="w-4 h-4 text-dopamine-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
        <span class="text-sm font-medium text-dopamine-400">{formatTokens(user.token_balance)}</span>
      </div>
      <div class="flex items-center gap-2 pl-3 border-l border-white/10">
        <div class="w-8 h-8 rounded-full bg-gradient-to-br from-neural-500 to-dopamine-500 flex items-center justify-center text-xs font-bold">
          {user.name?.charAt(0)?.toUpperCase() || 'U'}
        </div>
        <span class="text-sm text-white/70 hidden md:block">{user.name}</span>
      </div>
    {/if}
  </div>
</header>
