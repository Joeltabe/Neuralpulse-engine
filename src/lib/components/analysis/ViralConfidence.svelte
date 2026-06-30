<script lang="ts">
  import Card from '$lib/components/ui/Card.svelte';
  import type { CopyrightResult } from '$lib/types/api';

  let { analysis }: { analysis: CopyrightResult } = $props();

  let expandedSignal = $state<number | null>(null);
  let expandedSignatures = $state(false);

  const originalityVerdict = (r: string) =>
    r === 'low' ? { label: 'Verified Original', color: 'text-emerald-400', bg: 'bg-emerald-500/15', border: 'border-emerald-500/20', desc: 'Your content is highly original — platforms will boost your organic reach.', icon: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z' } :
    r === 'moderate' ? { label: 'Good Standing', color: 'text-amber-400', bg: 'bg-amber-500/15', border: 'border-amber-500/20', desc: 'Mostly original. A few elements may match existing content — review suggestions to maximize reach.', icon: 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z' } :
    r === 'high' ? { label: 'Needs Review', color: 'text-orange-400', bg: 'bg-orange-500/15', border: 'border-orange-500/20', desc: 'Some segments may match other content. Review flagged areas to avoid platform penalties.', icon: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z' } :
    { label: 'Attention Needed', color: 'text-rose-400', bg: 'bg-rose-500/15', border: 'border-rose-500/20', desc: 'Significant overlap with existing content. Make edits to protect your reach and avoid suppression.', icon: 'M12 9v2m0 4h.01' };

  const signalIcons: Record<string, string> = {
    audio_duplicate: 'M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3',
    visual_duplicate: 'M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z',
    music: 'M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2z',
    derivative: 'M7 11V7a5 5 0 0110 0v4m-6 4h2m-6 4h10a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2z',
    watermark: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z',
    metadata: 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
  };

  const signalLabels: Record<string, string> = {
    audio_duplicate: 'Audio Authenticity',
    visual_duplicate: 'Visual Authenticity',
    music: 'Music License Check',
    derivative: 'Content Evolution',
    watermark: 'Brand Attribution',
    metadata: 'Metadata Check',
  };

  const signalDescriptions: Record<string, string> = {
    audio_duplicate: 'Checks if your audio track is unique so platforms won\'t flag it.',
    visual_duplicate: 'Verifies your visuals are original for maximum organic reach.',
    music: 'Confirms your background music won\'t trigger copyright claims.',
    derivative: 'Detects if your content has been meaningfully transformed.',
    watermark: 'Identifies brand logos or attribution markers.',
    metadata: 'Reviews file metadata for originality signals.',
  };

  const severityStyles: Record<string, string> = {
    critical: 'bg-rose-500/15 text-rose-400 border-rose-500/20',
    moderate: 'bg-amber-500/15 text-amber-400 border-amber-500/20',
    suggestion: 'bg-blue-500/15 text-blue-400 border-blue-500/20',
  };

  const severityLabels: Record<string, string> = {
    critical: 'Attention',
    moderate: 'Review',
    suggestion: 'Info',
  };

  const sigTypeLabels: Record<string, string> = {
    audio: 'Audio Fingerprint',
    visual: 'Visual Fingerprint',
    melody: 'Melody ID',
  };
</script>

<Card>
  <div class="flex items-center justify-between mb-4">
    <div class="flex items-center gap-3">
      <div class="w-8 h-8 rounded-lg bg-emerald-500/15 flex items-center justify-center shrink-0">
        <svg class="w-4 h-4 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
      </div>
      <div>
        <h3 class="text-sm font-semibold">Viral Confidence</h3>
        <p class="text-[10px] text-white/30 mt-0.5">Originality validation that platforms trust — verified content gets boosted reach</p>
      </div>
    </div>
    <div class="flex items-center gap-2 shrink-0">
      <span class="text-[9px] text-white/20 uppercase tracking-wider">Trusted by</span>
      <span class="text-[9px] text-emerald-400 font-medium">Platform AI</span>
    </div>
  </div>

  <!-- Originality Verdict Banner -->
  {@const verdict = originalityVerdict(analysis.overall_risk)}
  <div class="rounded-xl border {verdict.border} {verdict.bg} p-4 mb-4">
    <div class="flex items-center gap-3">
      <svg class="w-6 h-6 shrink-0 {verdict.color}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d={verdict.icon} />
      </svg>
      <div class="flex-1">
        <div class="flex items-center gap-2">
          <span class="text-sm font-bold {verdict.color}">{verdict.label}</span>
          <div class="flex-1 h-1.5 max-w-32 rounded-full bg-white/5 overflow-hidden">
            <div class="h-full rounded-full transition-all duration-700" style="width: {analysis.risk_score * 100}%; background: linear-gradient(90deg, {analysis.overall_risk === 'low' ? '#34d399' : analysis.overall_risk === 'moderate' ? '#f59e0b' : '#ef4444'}, {analysis.overall_risk === 'critical' ? '#e11d48' : analysis.overall_risk === 'high' ? '#dc2626' : analysis.overall_risk === 'moderate' ? '#d97706' : '#10b981'});"></div>
          </div>
          <span class="text-xs font-bold {verdict.color} tabular-nums">{(analysis.risk_score * 100).toFixed(0)}%</span>
        </div>
        <p class="text-[10px] text-white/50 mt-0.5">{verdict.desc}</p>
      </div>
    </div>
  </div>

  <!-- Authenticity Scores Grid -->
  <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
    {#each [
      { label: 'Audio Authenticity', value: 1 - analysis.audio_duplicate_score, desc: 'Audio originality unlocks full reach' },
      { label: 'Visual Authenticity', value: 1 - analysis.visual_duplicate_score, desc: 'Unique visuals drive engagement' },
      { label: 'Music License', value: 1 - analysis.music_probability, desc: 'Licensed music avoids takedowns' },
      { label: 'Content Evolution', value: analysis.derivative_detected ? 0.25 : 0.95, desc: 'Fresh content gets algorithmic boost' },
    ] as metric}
      {@const col = metric.value > 0.7 ? '#34d399' : metric.value > 0.4 ? '#f59e0b' : '#ef4444'}
      <div class="rounded-lg bg-white/[0.03] border border-white/5 p-2.5">
        <div class="flex items-center gap-1.5 mb-1.5">
          <span class="w-1.5 h-1.5 rounded-full" style="background: {col}"></span>
          <span class="text-[9px] text-white/40 uppercase tracking-wider">{metric.label}</span>
        </div>
        <div class="flex items-center gap-2">
          <div class="flex-1 h-1.5 rounded-full bg-white/5 overflow-hidden">
            <div class="h-full rounded-full transition-all duration-700" style="width: {Math.min(100, metric.value * 100)}%; background: {col}80;"></div>
          </div>
          <span class="text-[10px] font-bold tabular-nums" style="color: {col}">{(metric.value * 100).toFixed(0)}%</span>
        </div>
        <p class="text-[8px] text-white/25 mt-1">{metric.desc}</p>
      </div>
    {/each}
  </div>

  <!-- Attribution & Evolution Details -->
  {#if analysis.watermark_detected || analysis.derivative_detected}
    <div class="flex flex-wrap gap-2 mb-4">
      {#if analysis.watermark_detected}
        <div class="px-2 py-1 rounded-lg bg-amber-500/10 border border-amber-500/20 text-[10px] text-amber-400 flex items-center gap-1.5">
          <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          <span>Brand attribution found</span>
          {#if analysis.watermark_details}
            <span class="text-amber-400/50">&mdash; {analysis.watermark_details}</span>
          {/if}
        </div>
      {/if}
      {#if analysis.derivative_detected}
        <div class="px-2 py-1 rounded-lg bg-blue-500/10 border border-blue-500/20 text-[10px] text-blue-400 flex items-center gap-1.5">
          <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
          <span>Content evolution detected</span>
          {#if analysis.derivative_details}
            <span class="text-blue-400/50">&mdash; {analysis.derivative_details}</span>
          {/if}
        </div>
      {/if}
    </div>
  {/if}

  <!-- Originality Signals -->
  {#if analysis.findings.length > 0}
    <div class="space-y-1.5 mb-4">
      <div class="flex items-center gap-2 mb-2">
        <span class="text-[10px] text-white/40 uppercase tracking-wider">Originality Signals</span>
        <span class="text-[9px] text-white/20">{analysis.findings.length} signal{analysis.findings.length > 1 ? 's' : ''}</span>
      </div>
      {#each analysis.findings as finding, i}
        <div class="rounded-lg border border-white/5 overflow-hidden">
          <button
            onclick={() => expandedSignal = expandedSignal === i ? null : i}
            class="w-full flex items-center gap-2.5 px-3 py-2 bg-white/[0.02] hover:bg-white/[0.04] transition-colors text-left"
          >
            <svg class="w-3.5 h-3.5 shrink-0 {finding.severity === 'critical' ? 'text-rose-400' : finding.severity === 'moderate' ? 'text-amber-400' : 'text-blue-400'}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d={signalIcons[finding.type] || signalIcons.metadata} />
            </svg>
            <span class="flex-1 text-[11px] font-medium text-white/70">{finding.title}</span>
            <span class="text-[8px] px-1.5 py-0.5 rounded {severityStyles[finding.severity]}">{severityLabels[finding.severity] || finding.severity}</span>
            <svg class="w-3 h-3 text-white/20 transition-transform {expandedSignal === i ? 'rotate-180' : ''}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          {#if expandedSignal === i}
            <div class="px-3 pb-3 pt-2 space-y-2" style="animation: expand-in 0.2s ease-out;">
              <div class="flex items-center gap-2">
                <span class="text-[9px] text-white/30 uppercase">Signal Type</span>
                <span class="text-[9px] px-1.5 py-0.5 rounded bg-white/5 text-white/50">{signalLabels[finding.type] || finding.type}</span>
                {#if finding.timestamp_sec !== null}
                  <span class="text-[9px] text-white/30">&middot; at {finding.timestamp_sec.toFixed(1)}s</span>
                {/if}
              </div>
              <p class="text-[9px] text-white/30 italic">{signalDescriptions[finding.type] || ''}</p>
              <p class="text-[10px] text-white/50 leading-relaxed">{finding.description}</p>
              <div class="rounded-lg bg-white/[0.02] border border-white/5 p-2.5">
                <p class="text-[9px] text-white/40 uppercase tracking-wider mb-0.5">Details</p>
                <p class="text-[10px] text-white/60 leading-relaxed">{finding.details}</p>
              </div>
              {#if finding.evidence}
                <div class="rounded-lg bg-white/[0.02] border border-white/5 p-2.5">
                  <p class="text-[9px] text-white/40 uppercase tracking-wider mb-1">Evidence</p>
                  <pre class="text-[9px] text-white/30 font-mono whitespace-pre-wrap">{JSON.stringify(finding.evidence, null, 2)}</pre>
                </div>
              {/if}
            </div>
          {/if}
        </div>
      {/each}
    </div>
  {/if}

  <!-- Content Signatures (strengthens ownership claim) -->
  {#if analysis.fingerprint_matches.length > 0}
    <div class="rounded-lg border border-white/5 overflow-hidden">
      <button
        onclick={() => expandedSignatures = !expandedSignatures}
        class="w-full flex items-center gap-2.5 px-3 py-2.5 bg-white/[0.02] hover:bg-white/[0.04] transition-colors text-left"
      >
        <svg class="w-3.5 h-3.5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
        <span class="flex-1 text-[11px] font-medium text-white/70">Content Signatures</span>
        <span class="text-[9px] text-white/30">{analysis.fingerprint_matches.length} signature{analysis.fingerprint_matches.length > 1 ? 's' : ''}</span>
        <svg class="w-3 h-3 text-white/20 transition-transform {expandedSignatures ? 'rotate-180' : ''}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      {#if expandedSignatures}
        <div class="px-3 pb-3 space-y-2">
          <p class="text-[9px] text-white/30 mt-2 mb-1">Your content&#39;s unique signatures are registered — this strengthens your ownership claim and helps platforms verify originality.</p>
          {#each analysis.fingerprint_matches as sig}
            <div class="rounded-lg bg-white/[0.02] border border-white/5 p-2.5">
              <div class="flex items-center gap-2 mb-1.5">
                <span class="text-[9px] font-medium text-white/60 uppercase">{sigTypeLabels[sig.match_type] || sig.match_type}</span>
                <div class="flex-1 h-1 max-w-16 rounded-full bg-white/5 overflow-hidden">
                  <div class="h-full rounded-full {sig.confidence > 0.7 ? 'bg-emerald-500/60' : sig.confidence > 0.4 ? 'bg-amber-500/60' : 'bg-blue-500/60'}" style="width: {sig.confidence * 100}%"></div>
                </div>
                <span class="text-[9px] font-bold tabular-nums {sig.confidence > 0.7 ? 'text-emerald-400' : sig.confidence > 0.4 ? 'text-amber-400' : 'text-blue-400'}">{(sig.confidence * 100).toFixed(0)}%</span>
              </div>
              <div class="flex items-center gap-2 text-[9px] text-white/30">
                <span>Source: {sig.source}</span>
                {#if sig.timestamp_sec !== null}
                  <span>&middot; at {sig.timestamp_sec.toFixed(1)}s</span>
                {/if}
                {#if sig.duration_sec !== null}
                  <span>&middot; duration {sig.duration_sec.toFixed(1)}s</span>
                {/if}
              </div>
              <p class="text-[9px] text-white/40 mt-1 leading-relaxed">{sig.details}</p>
            </div>
          {/each}
        </div>
      {/if}
    </div>
  {/if}
</Card>

<style>
  @keyframes expand-in {
    from { opacity: 0; }
    to { opacity: 1; }
  }
</style>
