<script lang="ts">
  interface Props {
    type?: string;
    label?: string;
    placeholder?: string;
    value?: string;
    error?: string;
    class?: string;
    [key: string]: any;
  }

  let { type = 'text', label, placeholder = '', value = $bindable(''), error, class: className = '', ...rest }: Props = $props();

  let id = crypto.randomUUID();
</script>

<div class={`space-y-1.5 ${className}`}>
  {#if label}
    <label for={id} class="block text-sm font-medium text-white/70">{label}</label>
  {/if}
  {#if type === 'textarea'}
    <textarea
      {id}
      {placeholder}
      bind:value
      class="input-neural w-full min-h-[120px] resize-y"
      {...rest}
    ></textarea>
  {:else}
    <input
      {id}
      {type}
      {placeholder}
      bind:value
      class="input-neural w-full"
      {...rest}
    />
  {/if}
  {#if error}
    <p class="text-xs text-red-400">{error}</p>
  {/if}
</div>
