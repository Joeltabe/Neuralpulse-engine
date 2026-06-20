<script lang="ts">
  import { onMount } from 'svelte';
  import { gsap } from 'gsap';
  import { ScrollTrigger } from 'gsap/ScrollTrigger';
  import '../app.css';
  import Navbar from '$lib/components/layout/Navbar.svelte';
  import Sidebar from '$lib/components/layout/Sidebar.svelte';
  import Footer from '$lib/components/layout/Footer.svelte';
  import Toast from '$lib/components/ui/Toast.svelte';
  import Particles from '$lib/components/effects/Particles.svelte';
  import FloatingOrbs from '$lib/components/effects/FloatingOrbs.svelte';
  import { theme, applyTheme } from '$lib/stores/theme';
  import { page } from '$app/stores';
  import { tick } from 'svelte';

  let { children } = $props();
  let sidebarOpen = $state(false);
  let mainEl = $state<HTMLElement | null>(null);
  let isAuthPage = $derived(
    $page.url.pathname === '/login' || $page.url.pathname === '/register' || $page.url.pathname === '/'
  );
  let prevPath = $state($page.url.pathname);

  onMount(() => {
    gsap.registerPlugin(ScrollTrigger);
    applyTheme('dark');
  });

  $effect(() => {
    const path = $page.url.pathname;
    if (path !== prevPath && !isAuthPage && mainEl) {
      const el = mainEl;
      tick().then(() => {
        const content = el.querySelector('.page-content') as HTMLElement | null;
        if (content) {
          gsap.fromTo(content,
            { opacity: 0, y: 30, scale: 0.98 },
            { opacity: 1, y: 0, scale: 1, duration: 0.4, ease: 'power3.out' }
          );
        }
      });
      prevPath = path;
    }
  });
</script>

<div class="min-h-screen bg-surface-950 neural-grid">
  <Toast />
  {#if isAuthPage}
    <FloatingOrbs count={4} colors={['#4d6cf5', '#f59e0b', '#10b981', '#8b5cf6']} />
    <div class="relative z-10">
      {@render children()}
    </div>
  {:else}
    <div class="flex h-screen overflow-hidden">
      <Sidebar bind:open={sidebarOpen} />
      <div class="flex flex-1 flex-col overflow-hidden">
        <Navbar onToggle={() => sidebarOpen = !sidebarOpen} />
        <main bind:this={mainEl} class="flex-1 overflow-y-auto p-4 md:p-6 lg:p-8 relative">
          <div class="page-content relative z-10">
            <Particles count={40} color1="#4d6cf5" color2="#f59e0b" color3="#10b981" connectDistance={100} />
            {@render children()}
          </div>
        </main>
        <Footer />
      </div>
    </div>
  {/if}
</div>
