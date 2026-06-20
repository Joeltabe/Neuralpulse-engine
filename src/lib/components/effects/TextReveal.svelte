<script lang="ts">
  import { onMount } from 'svelte';
  import { gsap } from 'gsap';

  let { text = '', type = 'chars' as 'chars' | 'words' | 'typewriter', duration = 1.2, stagger = 0.03, class: className = '' } = $props();

  let el: HTMLDivElement;

  onMount(() => {
    if (!el) return;
    if (type === 'typewriter') {
      el.textContent = '';
      let i = 0;
      const chars = text.split('');
      gsap.to({}, {
        duration: chars.length * 0.05,
        ease: 'none',
        onUpdate: function() {
          const count = Math.floor(this.progress() * chars.length);
          el.textContent = chars.slice(0, count).join('');
        }
      });
    } else {
      const items = type === 'chars' ? text.split('') : text.split(' ');
      el.innerHTML = items.map((item, i) =>
        `<span class="reveal-char" style="display: inline-block; white-space: ${type === 'words' ? 'inline' : 'pre'};" data-index="${i}">${item}</span>`
      ).join('');
      const chars = el.querySelectorAll('.reveal-char');
      gsap.fromTo(chars,
        { opacity: 0, y: 30, rotateX: -90 },
        {
          opacity: 1, y: 0, rotateX: 0,
          duration: duration * 0.6,
          stagger,
          ease: 'back.out(1.7)'
        }
      );
    }
  });
</script>

<div bind:this={el} class={className}></div>
