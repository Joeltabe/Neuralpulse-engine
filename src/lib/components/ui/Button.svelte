<script lang="ts">
  import { gsap } from 'gsap';

  interface Props {
    variant?: 'primary' | 'secondary' | 'ghost' | 'danger' | 'gradient';
    size?: 'sm' | 'md' | 'lg' | 'xl';
    type?: 'button' | 'submit' | 'reset';
    disabled?: boolean;
    loading?: boolean;
    href?: string;
    onclick?: (e: MouseEvent) => void;
    class?: string;
    children?: import('svelte').Snippet;
  }

  let { variant = 'primary', size = 'md', type = 'button', disabled = false, loading = false, href, onclick, class: className = '', children }: Props = $props();

  const base = 'inline-flex items-center justify-center font-medium rounded-xl transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-neural-500/40 disabled:opacity-50 disabled:cursor-not-allowed select-none';

  const variants: Record<string, string> = {
    primary: 'bg-neural-500 hover:bg-neural-600 text-white shadow-lg shadow-neural-500/20 hover:shadow-neural-500/30 active:scale-[0.98]',
    secondary: 'glass hover:bg-white/10 text-white active:scale-[0.98]',
    ghost: 'hover:bg-white/5 text-white/70 hover:text-white active:scale-[0.98]',
    danger: 'bg-red-500 hover:bg-red-600 text-white shadow-lg shadow-red-500/20 active:scale-[0.98]',
    gradient: 'bg-gradient-to-r from-neural-500 via-dopamine-500 to-memory-500 text-white shadow-lg shadow-neural-500/20 hover:shadow-neural-500/30 active:scale-[0.98]'
  };

  const sizes: Record<string, string> = {
    sm: 'px-3 py-1.5 text-sm gap-1.5',
    md: 'px-5 py-2.5 text-sm gap-2',
    lg: 'px-7 py-3.5 text-base gap-2.5',
    xl: 'px-10 py-4 text-lg gap-3'
  };

  let btn = $state<HTMLButtonElement | HTMLAnchorElement | null>(null);

  function handleClick(e: MouseEvent) {
    if (disabled || loading) return;
    if (btn && !href) {
      gsap.fromTo(btn, { scale: 0.97 }, { scale: 1, duration: 0.15, ease: 'power2.out' });
    }
    onclick?.(e);
  }
</script>

{#if href}
  <a
    bind:this={btn as HTMLAnchorElement}
    {href}
    class={`${base} ${variants[variant]} ${sizes[size]} ${className}`}
    onclick={handleClick}
  >
    {#if loading}
      <svg class="animate-spin -ml-1 h-4 w-4" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/></svg>
    {/if}
    {@render children?.()}
  </a>
{:else}
  <button
    bind:this={btn as HTMLButtonElement}
    {disabled}
    {type}
    class={`${base} ${variants[variant]} ${sizes[size]} ${className}`}
    onclick={handleClick}
  >
    {#if loading}
      <svg class="animate-spin -ml-1 h-4 w-4" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/></svg>
    {/if}
    {@render children?.()}
  </button>
{/if}
