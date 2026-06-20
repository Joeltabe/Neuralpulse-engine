<script lang="ts">
  import { gsap } from 'gsap';

  interface Props {
    accept?: string;
    label?: string;
    onupload?: (files: File | File[]) => void;
    disabled?: boolean;
    multiple?: boolean;
  }

  let { accept = '', label, onupload, disabled = false, multiple = false }: Props = $props();

  let dropzone: HTMLDivElement;
  let isDragging = $state(false);
  let fileName = $state('');

  function handleDrop(e: DragEvent) {
    e.preventDefault();
    isDragging = false;
    const files = Array.from(e.dataTransfer?.files || []);
    if (files.length) handleFiles(files);
  }

  function handleFileInput(e: Event) {
    const files = Array.from((e.target as HTMLInputElement).files || []);
    if (files.length) handleFiles(files);
  }

  function handleFiles(files: File[]) {
    fileName = files.map(f => f.name).join(', ');
    onupload?.(multiple ? files : files[0]);
  }

  $effect(() => {
    if (dropzone && isDragging) {
      gsap.to(dropzone, { scale: 1.02, borderColor: 'rgba(77,108,245,0.5)', duration: 0.2 });
    } else if (dropzone) {
      gsap.to(dropzone, { scale: 1, borderColor: 'rgba(255,255,255,0.1)', duration: 0.2 });
    }
  });
</script>

<div
  bind:this={dropzone}
  class={`relative border-2 border-dashed rounded-2xl p-8 text-center transition-colors duration-200 ${isDragging ? 'border-neural-500/50 bg-neural-500/5' : 'border-white/10 hover:border-white/20'} ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
  class:drag-over={isDragging}
  ondragover={(e) => { e.preventDefault(); isDragging = true; }}
  ondragleave={() => isDragging = false}
  ondrop={handleDrop}
  onclick={() => !disabled && document.getElementById('file-input')?.click()}
  onkeydown={(e) => (e.key === 'Enter' || e.key === ' ') && !disabled && document.getElementById('file-input')?.click()}
  role="button"
  tabindex="0"
>
  <input id="file-input" type="file" {accept} {multiple} class="hidden" onchange={handleFileInput} disabled={disabled} />
  <div class="flex flex-col items-center gap-3">
    <div class="w-12 h-12 rounded-full bg-neural-500/10 flex items-center justify-center">
      <svg class="w-6 h-6 text-neural-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/>
      </svg>
    </div>
    <div>
      <p class="text-sm text-white/70">{label || 'Drop file here or click to browse'}</p>
      <p class="text-xs text-white/40 mt-1">Accepted: {accept || 'All files'}</p>
    </div>
    {#if fileName}
      <p class="text-sm text-neural-400 font-medium">{fileName}</p>
    {/if}
  </div>
</div>
