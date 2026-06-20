<script lang="ts">
  import { gradeColor } from '$lib/utils/formatters';

  let { grade = 'N/A' } = $props();

  const glowColors: Record<string, string> = {
    'A+': 'shadow-emerald-500/30', 'A': 'shadow-emerald-500/30',
    'B+': 'shadow-neural-500/30', 'B': 'shadow-neural-500/30',
    'C+': 'shadow-dopamine-500/30', 'C': 'shadow-dopamine-500/30',
    'D': 'shadow-orange-500/30', 'F': 'shadow-red-500/30'
  };
</script>

<div class={`flex flex-col items-center justify-center w-24 h-24 rounded-2xl glass ${glowColors[grade] || ''} shadow-lg`}>
  <span class={`text-3xl font-black ${gradeColor(grade)}`}>{grade}</span>
  <span class="text-[10px] text-white/40 mt-0.5">GRADE</span>
</div>
