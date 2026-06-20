<script lang="ts">
  import { gsap } from 'gsap';
  import { slide } from 'svelte/transition';
  import { notifications, type Notification, removeNotification } from '$lib/stores/notifications';

  const icons: Record<string, string> = {
    success: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>',
    error: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"/>',
    warning: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>',
    info: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>'
  };

  const colors: Record<string, string> = {
    success: 'border-emerald-500/30 bg-emerald-500/10',
    error: 'border-red-500/30 bg-red-500/10',
    warning: 'border-dopamine-500/30 bg-dopamine-500/10',
    info: 'border-neural-500/30 bg-neural-500/10'
  };

  let items = $derived($notifications);
</script>

<div class="fixed top-4 right-4 z-[100] flex flex-col gap-2 max-w-sm w-full pointer-events-none">
  {#each items as notif (notif.id)}
    <div
      class={`pointer-events-auto glass-strong rounded-xl border p-4 flex items-start gap-3 ${colors[notif.type]}`}
      in:slide={{ duration: 300 }}
    >
      <svg class="w-5 h-5 mt-0.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        {@html icons[notif.type]}
      </svg>
      <p class="text-sm flex-1">{notif.message}</p>
      <button onclick={() => removeNotification(notif.id)} class="text-white/30 hover:text-white shrink-0" aria-label="Dismiss notification">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
      </button>
    </div>
  {/each}
</div>
