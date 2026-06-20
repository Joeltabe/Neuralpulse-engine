<script lang="ts">
  import { onMount, onDestroy } from 'svelte';

  let { count = 60, color1 = '#4d6cf5', color2 = '#f59e0b', color3 = '#10b981', connectDistance = 120, mouseInfluence = true } = $props();

  let canvas: HTMLCanvasElement;
  let ctx: CanvasRenderingContext2D | null;
  let particles: Particle[] = [];
  let animId: number;
  let mouse = { x: -1000, y: -1000 };

  class Particle {
    x: number; y: number; vx: number; vy: number; size: number; alpha: number; color: string; pulse: number; pulseSpeed: number;
    constructor(w: number, h: number) {
      this.x = Math.random() * w;
      this.y = Math.random() * h;
      this.vx = (Math.random() - 0.5) * 0.5;
      this.vy = (Math.random() - 0.5) * 0.5;
      this.size = Math.random() * 3 + 1;
      this.alpha = Math.random() * 0.5 + 0.1;
      const colors = [color1, color2, color3];
      this.color = colors[Math.floor(Math.random() * colors.length)];
      this.pulse = Math.random() * Math.PI * 2;
      this.pulseSpeed = Math.random() * 0.02 + 0.005;
    }
    update(w: number, h: number) {
      this.x += this.vx;
      this.y += this.vy;
      this.pulse += this.pulseSpeed;
      if (this.x < 0 || this.x > w) this.vx *= -1;
      if (this.y < 0 || this.y > h) this.vy *= -1;
      if (mouseInfluence) {
        const dx = mouse.x - this.x;
        const dy = mouse.y - this.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 200) {
          this.vx += dx * 0.00005;
          this.vy += dy * 0.00005;
          this.vx *= 0.98;
          this.vy *= 0.98;
        }
      }
      this.vx = Math.max(-1, Math.min(1, this.vx));
      this.vy = Math.max(-1, Math.min(1, this.vy));
    }
    draw(ctx: CanvasRenderingContext2D) {
      const pulseAlpha = this.alpha + Math.sin(this.pulse) * 0.15;
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.size + Math.sin(this.pulse) * 0.5, 0, Math.PI * 2);
      ctx.fillStyle = this.color;
      ctx.globalAlpha = Math.max(0, Math.min(1, pulseAlpha));
      ctx.fill();
      ctx.globalAlpha = 1;
    }
  }

  function init() {
    if (!canvas) return;
    ctx = canvas.getContext('2d');
    resize();
    particles = Array.from({ length: count }, () => new Particle(canvas.width, canvas.height));
    animate();
  }

  function resize() {
    if (!canvas) return;
    canvas.width = canvas.offsetWidth * 2;
    canvas.height = canvas.offsetHeight * 2;
    canvas.style.width = canvas.offsetWidth + 'px';
    canvas.style.height = canvas.offsetHeight + 'px';
    if (ctx) ctx.scale(1, 1);
  }

  function animate() {
    if (!canvas || !ctx) return;
    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);
    particles.forEach(p => p.update(w, h));
    particles.forEach(p => p.draw(ctx!));
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const a = particles[i], b = particles[j];
        const dx = a.x - b.x, dy = a.y - b.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < connectDistance) {
          ctx.beginPath();
          ctx.moveTo(a.x, a.y);
          ctx.lineTo(b.x, b.y);
          ctx.strokeStyle = `rgba(77, 108, 245, ${(1 - dist / connectDistance) * 0.15})`;
          ctx.lineWidth = 0.5;
          ctx.stroke();
        }
      }
    }
    animId = requestAnimationFrame(animate);
  }

  onMount(() => {
    init();
    const ro = new ResizeObserver(() => resize());
    if (canvas) ro.observe(canvas.parentElement || canvas);
    if (mouseInfluence) {
      const move = (e: MouseEvent) => { mouse.x = e.clientX * 2; mouse.y = e.clientY * 2; };
      const leave = () => { mouse.x = -1000; mouse.y = -1000; };
      window.addEventListener('mousemove', move);
      window.addEventListener('mouseleave', leave);
      return () => { window.removeEventListener('mousemove', move); window.removeEventListener('mouseleave', leave); };
    }
    return () => ro.disconnect();
  });

  onDestroy(() => { if (animId) cancelAnimationFrame(animId); });
</script>

<canvas bind:this={canvas} class="absolute inset-0 pointer-events-none" style="z-index: 0;"></canvas>
