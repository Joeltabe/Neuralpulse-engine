<script lang="ts">
  interface Props {
    class?: string;
    glow?: boolean;
    hover?: boolean;
    padding?: boolean;
    children?: import('svelte').Snippet;
  }

  let { class: className = '', glow = false, hover = false, padding = true, children }: Props = $props();
</script>

<div class={`glass rounded-2xl ${padding ? 'p-5' : ''} ${glow ? 'glow-border' : ''} ${hover ? 'card-hover' : ''} ${className}`}>
  {@render children?.()}
</div>
