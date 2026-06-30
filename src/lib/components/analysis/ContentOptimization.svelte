<script lang="ts">
  import Card from '$lib/components/ui/Card.svelte';
  import type { ContentOptimization } from '$lib/types/api';

  let { optimization }: { optimization: ContentOptimization } = $props();

  let expanded = $state<Record<string, boolean>>({});

  function toggle(key: string) {
    expanded[key] = !expanded[key];
  }

  function priorityColor(p: string | undefined): string {
    if (p === 'critical') return 'bg-red-500/15 text-red-400';
    if (p === 'high') return 'bg-orange-500/15 text-orange-400';
    if (p === 'medium') return 'bg-amber-500/15 text-amber-400';
    return 'bg-white/5 text-white/40';
  }

  function verdictBadge(v: string): string {
    if (v === 'good') return 'bg-emerald-500/15 text-emerald-400';
    if (v === 'needs_improvement') return 'bg-amber-500/15 text-amber-400';
    if (v === 'insufficient_data') return 'bg-white/5 text-white/30';
    return 'bg-white/5 text-white/40';
  }

  interface Section {
    key: string;
    label: string;
    icon: string;
    data: any;
  }

  let sections = $derived<Section[]>([
    { key: 'hook_strategy', label: 'Hook Strategy', icon: '\u{1F3A3}', data: optimization.hook_strategy },
    { key: 'intro_optimization', label: 'Intro', icon: '\u25B6', data: optimization.intro_optimization },
    { key: 'pacing_recommendations', label: 'Pacing', icon: '\u{1F3AC}', data: optimization.pacing_recommendations },
    { key: 'color_lighting_directives', label: 'Color & Lighting', icon: '\u{1F4A1}', data: optimization.color_lighting_directives },
    { key: 'camera_angle_directives', label: 'Camera & Framing', icon: '\u{1F4F7}', data: optimization.camera_angle_directives },
    { key: 'audio_pacing_directives', label: 'Sound & Audio', icon: '\u{1F50A}', data: optimization.audio_pacing_directives },
    { key: 'visual_optimization', label: 'Visual', icon: '\u{1F4FA}', data: optimization.visual_optimization },
    { key: 'audio_optimization', label: 'Audio', icon: '\u{1F50A}', data: optimization.audio_optimization },
    { key: 'emotional_arc_recommendations', label: 'Emotional Arc', icon: '\u{1F4C8}', data: optimization.emotional_arc_recommendations },
    { key: 'memory_encoding_optimization', label: 'Memory Encoding', icon: '\u{1F9E0}', data: optimization.memory_encoding_optimization },
    { key: 'intro_outro_mechanics', label: 'Intro/Outro Mechanics', icon: '\u{1F3A8}', data: optimization.intro_outro_mechanics },
    { key: 'dropoff_analysis', label: 'Dropoffs', icon: '\u25BC', data: optimization.dropoff_analysis },
    { key: 'outro_optimization', label: 'Outro', icon: '\u{1F51A}', data: optimization.outro_optimization },
  ]);

  function items(data: any) {
    return data?.recommendations || data?.suggestions || [];
  }
</script>

<Card>
  <div class="flex items-center justify-between mb-4">
    <div>
      <h3 class="text-sm font-semibold">Content Optimization</h3>
      <p class="text-[10px] text-white/30 mt-0.5">Actionable recommendations to improve neural engagement</p>
    </div>
    <button
      onclick={() => {
        const all = sections.length;
        const open = Object.values(expanded).filter(Boolean).length;
        const expandAll = open < all;
        for (const s of sections) expanded[s.key] = expandAll;
      }}
      class="text-[10px] text-neural-400 hover:text-neural-300 transition-colors"
    >
      {Object.values(expanded).filter(Boolean).length === sections.length ? 'Collapse All' : 'Expand All'}
    </button>
  </div>

  <div class="space-y-2">
    {#each sections as section}
      {@const data = section.data}
      {@const recs = items(data)}
      <div class="rounded-lg border border-white/5 overflow-hidden">
        <button
          onclick={() => toggle(section.key)}
          class="w-full flex items-center gap-3 px-3 py-2.5 bg-white/[0.02] hover:bg-white/[0.04] transition-colors text-left"
        >
          <span class="text-sm">{section.icon}</span>
          <span class="flex-1 text-xs font-medium text-white/80">{section.label}</span>
          {#if data?.verdict}
            <span class="text-[9px] px-1.5 py-0.5 rounded {verdictBadge(data.verdict)}">
              {data.verdict === 'needs_improvement' ? 'Improve' : data.verdict === 'good' ? 'Good' : 'N/A'}
            </span>
          {/if}
          {#if recs.length > 0}
            <span class="text-[9px] text-white/30">{recs.length}</span>
          {/if}
          <svg class="w-3 h-3 text-white/30 transition-transform {expanded[section.key] ? 'rotate-180' : ''}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
          </svg>
        </button>

        {#if expanded[section.key]}
          <div class="px-3 pb-3 space-y-2">
            {#if section.key === 'hook_strategy'}
              <div class="mt-2 rounded-lg bg-dopamine-500/10 border border-dopamine-500/20 p-3">
                <div class="flex items-center gap-2 mb-1">
                  <span class="text-[9px] uppercase tracking-wider text-white/40">Recommended Hook</span>
                  <span class="px-1.5 py-0.5 rounded text-[9px] font-medium bg-dopamine-500/20 text-dopamine-400 uppercase">
                    {data.recommended_hook_type.replace(/_/g, ' ')}
                  </span>
                </div>
                <p class="text-xs text-white/70 leading-relaxed">{data.hook_description}</p>
                <p class="text-[10px] text-white/40 mt-1">Optimal hook window: <span class="text-white/60 font-medium">{data.optimal_hook_window_sec}s</span></p>
              </div>

            {:else if section.key === 'dropoff_analysis'}
              {#if data.pattern}
                <div class="flex items-center gap-2 mt-2">
                  <span class="text-[9px] text-white/40 uppercase">Dropoff Pattern</span>
                  <span class="px-1.5 py-0.5 rounded text-[9px] font-medium bg-red-500/10 text-red-400 capitalize">{data.pattern.replace(/_/g, ' ')}</span>
                  <span class="text-[9px] text-white/30">{data.total_dropoffs} points</span>
                </div>
              {/if}
              {#if data.dropoff_points?.length}
                <div class="mt-1.5 space-y-1">
                  {#each data.dropoff_points.slice(0, 5) as dp}
                    <div class="flex items-center gap-2 text-[10px] bg-white/[0.02] rounded px-2 py-1.5">
                      <span class="text-white/30 font-mono tabular-nums w-12">{dp.timestamp_sec}s</span>
                      <div class="flex-1 h-1 rounded-full bg-white/5 overflow-hidden">
                        <div
                          class="h-full rounded-full {dp.severity === 'critical' ? 'bg-red-500/60' : 'bg-amber-500/60'}"
                          style="width: {Math.min(100, (dp.drop_magnitude / 0.3) * 100)}%"
                        ></div>
                      </div>
                      <span class="text-white/40 w-12 text-right">-{(dp.drop_magnitude * 100).toFixed(0)}%</span>
                    </div>
                  {/each}
                </div>
              {/if}
              {#each recs as rec}
                <div class="text-[10px] text-white/60 pl-1">{rec.suggestion}</div>
              {/each}

            {:else if section.key === 'color_lighting_directives' || section.key === 'camera_angle_directives' || section.key === 'audio_pacing_directives'}
              {#if data.diagnosis}
                <div class="mt-2 rounded-lg bg-white/[0.02] border border-white/5 p-2.5">
                  <p class="text-[9px] text-white/40 uppercase tracking-wider mb-1">Diagnosis</p>
                  <p class="text-[10px] text-white/60 leading-relaxed">{data.diagnosis}</p>
                </div>
              {/if}
              {#if data.visual_cortex_activation !== undefined}
                <div class="flex items-center gap-2 mt-2 text-[10px] text-white/40">
                  <span>Visual Cortex Activation:</span>
                  <span class="text-white/60 font-medium">{(data.visual_cortex_activation * 100).toFixed(0)}%</span>
                </div>
              {/if}
              {#if data.facial_engagement_score !== undefined}
                <div class="flex items-center gap-2 mt-2 text-[10px] text-white/40">
                  <span>Facial Engagement (FFA):</span>
                  <span class="text-white/60 font-medium">{(data.facial_engagement_score * 100).toFixed(0)}%</span>
                </div>
              {/if}
              {#if data.auditory_cortex_activation !== undefined}
                <div class="flex items-center gap-2 mt-2 text-[10px] text-white/40">
                  <span>Auditory Cortex (STG):</span>
                  <span class="text-white/60 font-medium">{(data.auditory_cortex_activation * 100).toFixed(0)}%</span>
                </div>
              {/if}
              {#each data.directives as directive}
                <div class="mt-1.5 rounded-lg border border-white/5 overflow-hidden">
                  <div class="bg-white/[0.02] px-2.5 py-1.5 flex items-center justify-between">
                    <span class="text-[9px] font-medium text-white/60 uppercase tracking-wider">{directive.domain}</span>
                    <span class="text-[8px] text-emerald-400/60">+{(directive.expected_impact * 100).toFixed(0)}% impact</span>
                  </div>
                  <div class="px-2.5 py-2 space-y-1.5">
                    <div>
                      <p class="text-[8px] text-white/30 uppercase tracking-wider">Diagnosis</p>
                      <p class="text-[10px] text-white/50 leading-relaxed">{directive.diagnosis}</p>
                    </div>
                    <div>
                      <p class="text-[8px] text-white/30 uppercase tracking-wider">Prescription</p>
                      <p class="text-[10px] text-white/70 leading-relaxed">{directive.prescription}</p>
                    </div>
                  </div>
                </div>
              {/each}

            {:else if section.key === 'intro_outro_mechanics'}
              {#if data.diagnosis}
                <div class="mt-2 rounded-lg bg-white/[0.02] border border-white/5 p-2.5">
                  <p class="text-[9px] text-white/40 uppercase tracking-wider mb-1">Diagnosis</p>
                  <p class="text-[10px] text-white/60 leading-relaxed">{data.diagnosis}</p>
                </div>
              {/if}
              {#if data.intro_directives?.length}
                <p class="text-[9px] text-white/40 uppercase tracking-wider mt-2 mb-1">Intro Directives</p>
                {#each data.intro_directives as directive}
                  <div class="mt-1 rounded-lg border border-cyan-500/15 overflow-hidden">
                    <div class="bg-cyan-500/5 px-2.5 py-1.5 flex items-center justify-between">
                      <span class="text-[9px] font-medium text-cyan-400/80 uppercase tracking-wider">{directive.domain}</span>
                      <span class="text-[8px] text-emerald-400/60">+{(directive.expected_impact * 100).toFixed(0)}% impact</span>
                    </div>
                    <div class="px-2.5 py-2 space-y-1.5">
                      <div>
                        <p class="text-[8px] text-white/30 uppercase tracking-wider">Diagnosis</p>
                        <p class="text-[10px] text-white/50 leading-relaxed">{directive.diagnosis}</p>
                      </div>
                      <div>
                        <p class="text-[8px] text-white/30 uppercase tracking-wider">Prescription</p>
                        <p class="text-[10px] text-white/70 leading-relaxed">{directive.prescription}</p>
                      </div>
                    </div>
                  </div>
                {/each}
              {/if}
              {#if data.outro_directives?.length}
                <p class="text-[9px] text-white/40 uppercase tracking-wider mt-2 mb-1">Outro Directives</p>
                {#each data.outro_directives as directive}
                  <div class="mt-1 rounded-lg border border-purple-500/15 overflow-hidden">
                    <div class="bg-purple-500/5 px-2.5 py-1.5 flex items-center justify-between">
                      <span class="text-[9px] font-medium text-purple-400/80 uppercase tracking-wider">{directive.domain}</span>
                      <span class="text-[8px] text-emerald-400/60">+{(directive.expected_impact * 100).toFixed(0)}% impact</span>
                    </div>
                    <div class="px-2.5 py-2 space-y-1.5">
                      <div>
                        <p class="text-[8px] text-white/30 uppercase tracking-wider">Diagnosis</p>
                        <p class="text-[10px] text-white/50 leading-relaxed">{directive.diagnosis}</p>
                      </div>
                      <div>
                        <p class="text-[8px] text-white/30 uppercase tracking-wider">Prescription</p>
                        <p class="text-[10px] text-white/70 leading-relaxed">{directive.prescription}</p>
                      </div>
                    </div>
                  </div>
                {/each}
              {/if}

            {:else}
              {#if data.average_visual_engagement !== undefined}
                <div class="flex items-center gap-2 mt-2 text-[10px] text-white/40">
                  <span>Avg Visual Engagement:</span>
                  <span class="text-white/60 font-medium">{(data.average_visual_engagement * 100).toFixed(0)}%</span>
                </div>
              {/if}
              {#if data.average_audio_engagement !== undefined}
                <div class="flex items-center gap-2 mt-2 text-[10px] text-white/40">
                  <span>Avg Audio Engagement:</span>
                  <span class="text-white/60 font-medium">{(data.average_audio_engagement * 100).toFixed(0)}%</span>
                </div>
              {/if}
              {#if data.peak_emotional_moment_sec !== undefined}
                <div class="flex items-center gap-3 mt-2 text-[10px] text-white/40">
                  <span>Peak: <span class="text-white/60">{data.peak_emotional_moment_sec}s</span></span>
                  <span>Valley: <span class="text-white/60">{data.valley_moment_sec}s</span></span>
                </div>
              {/if}
              {#each recs as rec}
                <div class="mt-1.5 rounded-lg bg-white/[0.02] border border-white/5 p-2.5">
                  <div class="flex items-start gap-2">
                    {#if rec.priority}
                      <span class="text-[8px] px-1 py-0.5 rounded shrink-0 mt-0.5 {priorityColor(rec.priority)}">{rec.priority}</span>
                    {/if}
                    <div class="flex-1 min-w-0">
                      {#if rec.area}
                        <p class="text-[10px] font-medium text-white/70">{rec.area}</p>
                      {/if}
                      <p class="text-[10px] text-white/50 leading-relaxed">{rec.suggestion}</p>
                      {#if rec.expected_impact !== undefined}
                        <div class="flex items-center gap-1.5 mt-1">
                          <div class="flex-1 h-1 rounded-full bg-white/5 overflow-hidden max-w-16">
                            <div class="h-full rounded-full bg-emerald-500/50" style="width: {rec.expected_impact * 100}%"></div>
                          </div>
                          <span class="text-[8px] text-emerald-400/60">+{(rec.expected_impact * 100).toFixed(0)}% impact</span>
                        </div>
                      {/if}
                    </div>
                  </div>
                </div>
              {/each}
            {/if}

            {#if section.key !== 'hook_strategy' && recs.length === 0 && data?.verdict === 'good'}
              <p class="text-[10px] text-emerald-400/60 mt-2">No improvements needed &mdash; this area is performing well.</p>
            {/if}
          </div>
        {/if}
      </div>
    {/each}
  </div>
</Card>