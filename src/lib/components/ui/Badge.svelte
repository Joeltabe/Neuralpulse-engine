<script lang="ts">
  import { severityColor } from '$lib/utils/formatters';

  interface Props {
    variant?: 'default' | 'attention' | 'dopamine' | 'memory' | 'neural';
    class?: string;
    children?: import('svelte').Snippet;
  }

  let { variant = 'default', class: className = '', children }: Props = $props();

  const variants: Record<string, string> = {
    default: 'bg-white/5 text-white/70 border-white/10',
    attention: 'bg-neural-500/10 text-neural-400 border-neural-500/20',
    dopamine: 'bg-dopamine-500/10 text-dopamine-400 border-dopamine-500/20',
    memory: 'bg-memory-500/10 text-memory-400 border-memory-500/20',
    neural: 'bg-gradient-to-r from-neural-500/20 to-memory-500/20 text-white border-white/10'
  };
</script>

<span class={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium border ${variants[variant]} ${className}`}>
  {@render children?.()}
</span>
