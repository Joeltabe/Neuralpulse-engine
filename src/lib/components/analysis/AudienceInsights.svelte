<script lang="ts">
  import Card from '$lib/components/ui/Card.svelte';
  import type { AudienceProfile } from '$lib/types/api';

  let { profile }: { profile: AudienceProfile } = $props();

  const confidenceColor = (v: number) =>
    v > 0.6 ? 'text-emerald-400' : v > 0.4 ? 'text-amber-400' : 'text-red-400';

  const barColor = (v: number) =>
    v > 0.6 ? 'bg-emerald-400/60' : v > 0.4 ? 'bg-amber-400/60' : 'bg-red-400/60';

  const pacingLabel: Record<string, string> = {
    ultra_fast: 'Ultra-Fast',
    fast: 'Fast',
    moderate: 'Moderate',
    slow: 'Slow',
  };

  const momentumIcon: Record<string, string> = {
    rising: '\u2191',
    declining: '\u2193',
    neutral: '\u2192',
  };
</script>

<Card>
  <div class="flex items-center justify-between mb-4">
    <div>
      <h3 class="text-sm font-semibold">Audience Profile</h3>
      <p class="text-[10px] text-white/30 mt-0.5">Demographic & interest predictions from neural response patterns</p>
    </div>
  </div>

  <!-- Primary Audience -->
  <div class="rounded-lg bg-gradient-to-r from-neural-500/10 via-dopamine-500/5 to-memory-500/10 border border-white/5 p-4 mb-4">
    <div class="flex items-center gap-3 mb-3">
      <div class="w-10 h-10 rounded-full bg-neural-500/20 flex items-center justify-center shrink-0">
        <svg class="w-5 h-5 text-neural-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
        </svg>
      </div>
      <div class="flex-1">
        <p class="text-[10px] text-white/40 uppercase tracking-wider">Primary Audience</p>
        <div class="flex flex-wrap items-baseline gap-x-4 gap-y-1 mt-0.5">
          <span class="text-sm font-bold text-white/90">{profile.primary_audience.age_group}</span>
          <span class="text-xs text-white/60">&middot; {profile.primary_audience.interest_category}</span>
          <span class="text-xs text-white/60">&middot; {profile.primary_audience.geographic_affinity}</span>
        </div>
      </div>
      <div class="text-right shrink-0">
        <p class="text-[10px] text-white/40 uppercase">Confidence</p>
        <p class="text-sm font-bold {confidenceColor(profile.primary_audience.confidence)}">
          {(profile.primary_audience.confidence * 100).toFixed(0)}%
        </p>
      </div>
    </div>

    <!-- Target Audience (Neuro-Specialist Prediction) -->
    {#if profile.target_audience}
      <div class="border-t border-white/5 pt-3 mt-1">
        <div class="flex items-center gap-2 mb-2">
          <span class="text-[9px] text-white/30 uppercase tracking-wider">Neural Audience Prediction</span>
          <span class="px-1.5 py-0.5 rounded text-[8px] font-medium bg-neural-500/15 text-neural-400">v2</span>
        </div>

        <div class="flex flex-wrap gap-3">
          <div class="flex-1 min-w-[140px]">
            <p class="text-[9px] text-white/40">Predicted Age Bracket</p>
            <p class="text-xs font-bold text-white/80">{profile.target_audience.predicted_age_group}</p>
          </div>
          <div class="flex-1 min-w-[140px]">
            <p class="text-[9px] text-white/40">Psychological Profile</p>
            <p class="text-xs font-bold text-dopamine-400">{profile.target_audience.psychological_profile}</p>
          </div>
        </div>

        <p class="text-[10px] text-white/50 leading-relaxed mt-1.5">{profile.target_audience.profile_description}</p>

        <div class="flex flex-wrap gap-2 mt-2">
          {#each profile.target_audience.needs.slice(0, 3) as need}
            <span class="px-1.5 py-0.5 rounded text-[9px] bg-emerald-500/10 text-emerald-400 capitalize">{need.replace(/_/g, ' ')}</span>
          {/each}
          {#each profile.target_audience.avoids.slice(0, 2) as avoid}
            <span class="px-1.5 py-0.5 rounded text-[9px] bg-red-500/10 text-red-400 capitalize">{avoid.replace(/_/g, ' ')}</span>
          {/each}
        </div>

        <!-- Platform Affinity -->
        <div class="grid grid-cols-2 gap-2 mt-3">
          <div class="rounded-lg bg-white/[0.03] border border-white/5 p-2">
            <div class="flex items-center justify-between mb-1">
              <span class="text-[9px] font-medium text-white/70">{profile.target_audience.platform_affinity.primary_platform}</span>
              <span class="text-[9px] font-bold text-emerald-400">{(profile.target_audience.platform_affinity.primary_fit_score * 100).toFixed(0)}%</span>
            </div>
            <p class="text-[9px] text-white/40 leading-relaxed">{profile.target_audience.platform_affinity.primary_reasoning}</p>
          </div>
          <div class="rounded-lg bg-white/[0.03] border border-white/5 p-2">
            <div class="flex items-center justify-between mb-1">
              <span class="text-[9px] font-medium text-white/70">{profile.target_audience.platform_affinity.secondary_platform}</span>
              <span class="text-[9px] font-bold text-amber-400">{(profile.target_audience.platform_affinity.secondary_fit_score * 100).toFixed(0)}%</span>
            </div>
            <p class="text-[9px] text-white/40 leading-relaxed">{profile.target_audience.platform_affinity.secondary_reasoning}</p>
          </div>
        </div>

        <!-- Behavioral Triggers -->
        <div class="flex gap-3 mt-2 text-[10px] text-white/40">
          <span>Hook window: <span class="text-white/60 font-medium">{profile.target_audience.behavioral_triggers.optimal_hook_window_sec}s</span></span>
          <span>Scene rate: <span class="text-white/60 font-medium">{profile.target_audience.behavioral_triggers.scene_change_rate_target}/sec</span></span>
          <span>Dopamine interval: <span class="text-white/60 font-medium">{profile.target_audience.behavioral_triggers.dopamine_peak_interval_sec}s</span></span>
        </div>
      </div>
    {/if}
  </div>

  <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
    <!-- Neural Signature -->
    <div>
      <p class="text-[10px] text-white/40 uppercase tracking-wider mb-2">Neural Signature</p>
      <div class="space-y-2">
        {#each [
          { label: 'Attention Decay', value: 1 - profile.neural_signature.attention_decay_rate / 2, key: 'attention_decay_rate' },
          { label: 'Dopamine Peak Latency', value: 1 - profile.neural_signature.dopamine_peak_latency_sec / 8, key: 'dopamine_peak_latency_sec' },
          { label: 'Scene Change Rate', value: profile.neural_signature.scene_change_rate, key: 'scene_change_rate' },
          { label: 'Engagement Variance', value: profile.neural_signature.engagement_variance, key: 'engagement_variance' },
          { label: 'Early Engagement', value: profile.neural_signature.early_engagement_score, key: 'early_engagement_score' },
          { label: 'Final Memory Encoding', value: profile.neural_signature.final_memory_encoding_score, key: 'final_memory_encoding_score' },
        ] as sig}
          <div class="flex items-center gap-2">
            <span class="text-[10px] text-white/50 w-28 shrink-0">{sig.label}</span>
            <div class="flex-1 h-1.5 rounded-full bg-white/5 overflow-hidden">
              <div class="h-full rounded-full {barColor(sig.value)} transition-all" style="width: {Math.min(100, sig.value * 100)}%"></div>
            </div>
            <span class="text-[10px] text-white/40 w-8 text-right tabular-nums">{(sig.value * 100).toFixed(0)}%</span>
          </div>
        {/each}
      </div>
      <div class="flex gap-3 mt-2">
        <span class="text-[10px] text-white/50">
          Pacing: <span class="text-white/70 font-medium">{pacingLabel[profile.neural_signature.pacing_profile] || profile.neural_signature.pacing_profile}</span>
        </span>
        <span class="text-[10px] text-white/50">
          Momentum: <span class="text-white/70 font-medium">{momentumIcon[profile.neural_signature.engagement_momentum]} {profile.neural_signature.engagement_momentum}</span>
        </span>
      </div>
    </div>

    <!-- Duration & Benchmark -->
    <div class="space-y-3">
      <div>
        <p class="text-[10px] text-white/40 uppercase tracking-wider mb-2">Content Length</p>
        <div class="rounded-lg border border-white/5 bg-white/[0.03] p-3">
          <div class="flex items-center gap-3">
            <div class="flex items-center gap-1.5">
              <span class="text-lg font-bold text-white/90">{profile.optimal_content_length_sec.recommended_duration_sec}s</span>
              <span class="text-[10px] text-white/30">recommended</span>
            </div>
            <span class="text-white/20">&middot;</span>
            <span class="text-[10px] text-white/40">Current: {profile.optimal_content_length_sec.current_duration_sec}s</span>
          </div>
          <div class="mt-1.5 flex items-center gap-1.5">
            {#if profile.optimal_content_length_sec.verdict === 'optimal'}
              <span class="px-1.5 py-0.5 rounded text-[9px] font-medium bg-emerald-500/15 text-emerald-400">Optimal</span>
            {:else if profile.optimal_content_length_sec.verdict === 'too_long'}
              <span class="px-1.5 py-0.5 rounded text-[9px] font-medium bg-red-500/15 text-red-400">Too Long</span>
            {:else}
              <span class="px-1.5 py-0.5 rounded text-[9px] font-medium bg-amber-500/15 text-amber-400">Too Short</span>
            {/if}
            <span class="text-[10px] text-white/40">{profile.optimal_content_length_sec.reasoning}</span>
          </div>
        </div>
      </div>

      <div>
        <p class="text-[10px] text-white/40 uppercase tracking-wider mb-2">Competitive Benchmark</p>
        <div class="flex gap-3">
          <div class="flex-1 rounded-lg border border-white/5 bg-white/[0.03] p-2.5 text-center">
            <p class="text-[9px] text-white/40 uppercase">Difficulty</p>
            <p class="text-xs font-bold mt-0.5 capitalize {profile.competitive_benchmark.estimated_competitive_difficulty === 'low' ? 'text-emerald-400' : profile.competitive_benchmark.estimated_competitive_difficulty === 'medium' ? 'text-amber-400' : 'text-red-400'}">
              {profile.competitive_benchmark.estimated_competitive_difficulty}
            </p>
          </div>
          <div class="flex-1 rounded-lg border border-white/5 bg-white/[0.03] p-2.5 text-center">
            <p class="text-[9px] text-white/40 uppercase">Uniqueness</p>
            <p class="text-xs font-bold mt-0.5 text-neural-400">{(profile.competitive_benchmark.content_uniqueness_score * 100).toFixed(0)}%</p>
          </div>
        </div>
      </div>

      <!-- Audience Segments -->
      <div>
        <p class="text-[10px] text-white/40 uppercase tracking-wider mb-2">Age Segments</p>
        <div class="flex flex-wrap gap-1.5">
          {#each Object.entries(profile.age_breakdown).slice(0, 3) as [key, seg]}
            <div class="px-2 py-1 rounded-md bg-white/[0.04] border border-white/5 text-[10px]">
              <span class="text-white/70">{seg.label}</span>
              <span class="text-white/30 ml-1">{(seg.score * 100).toFixed(0)}%</span>
            </div>
          {/each}
        </div>
      </div>

      <!-- Top Interests -->
      <div>
        <p class="text-[10px] text-white/40 uppercase tracking-wider mb-2">Interest Affinity</p>
        <div class="flex flex-wrap gap-1.5">
          {#each profile.top_interests.slice(0, 3) as interest}
            <div class="px-2 py-1 rounded-md bg-dopamine-500/10 border border-dopamine-500/20 text-[10px]">
              <span class="text-dopamine-400">{interest.label}</span>
              <span class="text-dopamine-400/50 ml-1">{(interest.score * 100).toFixed(0)}%</span>
            </div>
          {/each}
        </div>
      </div>
    </div>
  </div>
</Card>