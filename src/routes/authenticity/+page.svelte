<script lang="ts">
  import { _ } from '$lib/i18n';
  import { error as showError } from '$lib/stores/notifications';
  import Card from '$lib/components/ui/Card.svelte';
  import Button from '$lib/components/ui/Button.svelte';
  import Input from '$lib/components/ui/Input.svelte';
  import FileUpload from '$lib/components/ui/FileUpload.svelte';
  import Spinner from '$lib/components/ui/Spinner.svelte';
  import DoughnutChart from '$lib/components/charts/DoughnutChart.svelte';

  type TabId = 'ai-detection' | 'plagiarism' | 'tamper-check' | 'provenance';

  const tabs: { id: TabId; label: string; color: string }[] = [
    { id: 'ai-detection', label: 'AI Detection', color: 'neural' },
    { id: 'plagiarism', label: 'Plagiarism', color: 'dopamine' },
    { id: 'tamper-check', label: 'Tamper Check', color: 'memory' },
    { id: 'provenance', label: 'Provenance', color: 'neural' }
  ];

  let activeTab = $state<TabId>('ai-detection');
  let loading = $state(false);
  let result = $state<any>(null);

  let aiFile = $state<File | null>(null);
  let aiText = $state('');
  let plagText = $state('');
  let tamperFile = $state<File | null>(null);
  let provFile = $state<File | null>(null);
  let provSource = $state('');
  let provHash = $state('');
  let lookupHash = $state('');
  let provResult = $state<any>(null);
  let provLookupResult = $state<any>(null);

  const tabColors: Record<string, string> = {
    neural: 'data-[active=true]:bg-neural-500/20 data-[active=true]:text-neural-300 data-[active=true]:border-neural-500/30',
    dopamine: 'data-[active=true]:bg-dopamine-500/20 data-[active=true]:text-dopamine-300 data-[active=true]:border-dopamine-500/30',
    memory: 'data-[active=true]:bg-memory-500/20 data-[active=true]:text-memory-300 data-[active=true]:border-memory-500/30'
  };
  const tabInactive = 'text-white/50 hover:text-white/80 border-transparent';

  function getGrade(score: number): string {
    if (score >= 90) return 'A';
    if (score >= 80) return 'B';
    if (score >= 65) return 'C';
    if (score >= 50) return 'D';
    return 'F';
  }

  function gradeTextColor(grade: string): string {
    const m: Record<string, string> = { A: 'text-emerald-400', B: 'text-neural-400', C: 'text-dopamine-400', D: 'text-orange-400', F: 'text-red-400' };
    return m[grade] || 'text-white/60';
  }

  function riskBadge(risk: string): string {
    const m: Record<string, string> = {
      low: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
      medium: 'text-dopamine-400 bg-dopamine-500/10 border-dopamine-500/20',
      high: 'text-red-400 bg-red-500/10 border-red-500/20',
      critical: 'text-red-400 bg-red-500/10 border-red-500/20'
    };
    return m[risk?.toLowerCase()] || 'text-white/60 bg-white/5 border-white/10';
  }

  function badgeClass(v: string): string {
    const m: Record<string, string> = {
      original: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
      suspicious: 'text-dopamine-400 bg-dopamine-500/10 border-dopamine-500/20',
      plagiarized: 'text-red-400 bg-red-500/10 border-red-500/20'
    };
    return m[v?.toLowerCase()] || 'text-white/60 bg-white/5 border-white/10';
  }

  async function callApi(method: string, body?: BodyInit, isFormData = false) {
    loading = true;
    try {
      const opts: RequestInit = { method };
      if (body) {
        if (isFormData) {
          opts.body = body;
        } else {
          opts.headers = { 'Content-Type': 'application/json' };
          opts.body = body;
        }
      }
      const res = await fetch(`/api/authenticity/${method}`, opts);
      const data = await res.json();
      if (data.success) return data.data;
      showError(data.error || 'Request failed');
      return null;
    } catch {
      showError('Network error');
      return null;
    } finally {
      loading = false;
    }
  }

  async function runAiDetection() {
    if (!aiFile && !aiText.trim()) return;
    if (aiFile) {
      const form = new FormData();
      form.append('file', aiFile);
      result = await callApi('analyze', form, true);
    } else {
      result = await callApi('analyze', JSON.stringify({ text: aiText }));
    }
  }

  async function runPlagiarism() {
    if (!plagText.trim()) return;
    result = await callApi('index', JSON.stringify({ text: plagText }));
  }

  async function runTamperCheck() {
    if (!tamperFile) return;
    const form = new FormData();
    form.append('file', tamperFile);
    result = await callApi('analyze', form, true);
  }

  async function registerProvenance() {
    if (!provFile) return;
    const form = new FormData();
    form.append('file', provFile);
    if (provSource.trim()) form.append('source', provSource);
    provResult = await callApi('provenance-register', form, true);
  }

  async function lookupProvenance() {
    if (!lookupHash.trim()) return;
    loading = true;
    try {
      const res = await fetch(`/api/authenticity/provenance-lookup?content_hash=${encodeURIComponent(lookupHash)}`);
      const data = await res.json();
      if (data.success) provLookupResult = data.data;
      else showError(data.error || 'Lookup failed');
    } catch { showError('Network error'); }
    finally { loading = false; }
  }

  function resetResult() {
    result = null;
    provResult = null;
    provLookupResult = null;
    aiFile = null;
    aiText = '';
    plagText = '';
    tamperFile = null;
    provFile = null;
    provSource = '';
    provHash = '';
    lookupHash = '';
  }

  function switchTab(tab: TabId) {
    activeTab = tab;
    resetResult();
  }
</script>

<div class="max-w-6xl mx-auto space-y-6">
  <div>
    <h1 class="text-2xl font-bold">Content Authenticity</h1>
    <p class="text-sm text-white/50 mt-1">Analyze content for AI generation, plagiarism, tampering, and verify provenance</p>
  </div>

  <!-- Tabs -->
  <div class="flex gap-2 flex-wrap">
    {#each tabs as t}
      <button
        onclick={() => switchTab(t.id)}
        data-active={activeTab === t.id}
        class={`px-4 py-2 rounded-xl text-sm font-medium border transition-all duration-200 ${activeTab === t.id ? tabColors[t.color] : tabInactive} ${activeTab !== t.id ? 'glass' : ''}`}
      >
        {t.label}
      </button>
    {/each}
  </div>

  {#if activeTab === 'ai-detection'}
    {#if !result}
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <h3 class="text-sm font-semibold mb-3 text-neural-400">Upload File</h3>
          <FileUpload accept=".txt,.csv,.json,.docx,.pdf" label="Drop file or click to browse" onupload={(f) => aiFile = Array.isArray(f) ? f[0] : f} />
          {#if aiFile}
            <div class="mt-3 glass rounded-xl p-3 flex items-center justify-between">
              <span class="text-sm truncate">{aiFile.name}</span>
              <span class="text-xs text-white/40">{(aiFile.size / 1024).toFixed(1)} KB</span>
            </div>
          {/if}
        </Card>
        <Card>
          <h3 class="text-sm font-semibold mb-3 text-neural-400">Or Paste Text</h3>
          <Input type="textarea" placeholder="Paste your content here..." bind:value={aiText} />
        </Card>
      </div>
      <Button onclick={runAiDetection} variant="gradient" size="lg" class="w-full" disabled={!aiFile && !aiText.trim()} loading={loading}>
        {loading ? 'Analyzing...' : 'Analyze Content'}
      </Button>
    {/if}

  {:else if activeTab === 'plagiarism'}
    {#if !result}
      <Card>
        <h3 class="text-sm font-semibold mb-3 text-dopamine-400">Text to Check</h3>
        <Input type="textarea" placeholder="Paste text to check for plagiarism..." bind:value={plagText} />
      </Card>
      <Button onclick={runPlagiarism} variant="gradient" size="lg" class="w-full" disabled={!plagText.trim()} loading={loading}>
        {loading ? 'Checking...' : 'Check Plagiarism'}
      </Button>
    {/if}

  {:else if activeTab === 'tamper-check'}
    {#if !result}
      <Card>
        <h3 class="text-sm font-semibold mb-3 text-memory-400">Upload Image for Tamper Analysis</h3>
        <FileUpload accept=".png,.jpg,.jpeg,.webp" label="Drop image or click to browse" onupload={(f) => tamperFile = Array.isArray(f) ? f[0] : f} />
        {#if tamperFile}
          <div class="mt-3 glass rounded-xl p-3 flex items-center justify-between">
            <span class="text-sm truncate">{tamperFile.name}</span>
            <span class="text-xs text-white/40">{(tamperFile.size / 1024).toFixed(1)} KB</span>
          </div>
        {/if}
      </Card>
      <Button onclick={runTamperCheck} variant="gradient" size="lg" class="w-full" disabled={!tamperFile} loading={loading}>
        {loading ? 'Analyzing...' : 'Check for Tampering'}
      </Button>
    {/if}

  {:else if activeTab === 'provenance'}
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <Card>
        <h3 class="text-sm font-semibold mb-3 text-neural-400">Register Content</h3>
        <div class="space-y-3">
          <FileUpload accept="*" label="Drop file to register" onupload={(f) => provFile = Array.isArray(f) ? f[0] : f} />
          {#if provFile}
            <div class="glass rounded-xl p-3 flex items-center justify-between">
              <span class="text-sm truncate">{provFile.name}</span>
              <span class="text-xs text-white/40">{(provFile.size / 1024).toFixed(1)} KB</span>
            </div>
          {/if}
          <Input placeholder="Source (optional)" bind:value={provSource} />
          <Button onclick={registerProvenance} variant="primary" size="md" class="w-full" disabled={!provFile} loading={loading}>
            Register
          </Button>
        </div>
        {#if provResult}
          <div class="mt-4 glass rounded-xl p-4 space-y-2">
            <p class="text-xs text-white/40">Content Hash</p>
            <p class="text-sm font-mono text-neural-300 break-all">{provResult.content_hash || provResult.hash || '—'}</p>
            {#if provResult.source}<p class="text-xs text-white/40 mt-2">Source: {provResult.source}</p>{/if}
            {#if provResult.created_at || provResult.registered_at}
              <p class="text-xs text-white/40">Registered: {provResult.created_at || provResult.registered_at}</p>
            {/if}
          </div>
        {/if}
      </Card>
      <Card>
        <h3 class="text-sm font-semibold mb-3 text-neural-400">Lookup by Hash</h3>
        <div class="space-y-3">
          <Input placeholder="Enter content hash" bind:value={lookupHash} />
          <Button onclick={lookupProvenance} variant="primary" size="md" class="w-full" disabled={!lookupHash.trim()} loading={loading}>
            Lookup
          </Button>
        </div>
        {#if provLookupResult}
          <div class="mt-4 glass rounded-xl p-4 space-y-2">
            {#if provLookupResult.filename}
              <p class="text-sm text-white/70"><span class="text-xs text-white/40">File:</span> {provLookupResult.filename}</p>
            {/if}
            {#if provLookupResult.source}
              <p class="text-sm text-white/70"><span class="text-xs text-white/40">Source:</span> {provLookupResult.source}</p>
            {/if}
            {#if provLookupResult.content_hash}
              <p class="text-xs text-white/40 mt-1">Hash: <span class="font-mono text-neural-300">{provLookupResult.content_hash}</span></p>
            {/if}
            {#if provLookupResult.created_at || provLookupResult.registered_at}
              <p class="text-xs text-white/40">Registered: {provLookupResult.created_at || provLookupResult.registered_at}</p>
            {/if}
          </div>
        {/if}
      </Card>
    </div>
  {/if}

  {#if loading}
    <div class="flex justify-center py-12"><Spinner size="lg" /></div>
  {/if}

  <!-- Results -->
  {#if result && !loading}
    <div class="space-y-6">
      {#if activeTab === 'ai-detection'}
        <div class="flex items-start gap-6">
          <div class="w-28 h-28 shrink-0">
            <DoughnutChart value={(result.overall_score ?? result.ai_score ?? 0) / 100} color="#4d6cf5" label="Score" />
          </div>
          <div>
            <div class="flex items-center gap-3">
              <h2 class="text-xl font-bold">AI Detection</h2>
              <span class={`text-3xl font-black ${gradeTextColor(getGrade(result.overall_score ?? result.ai_score ?? 0))}`}>
                {getGrade(result.overall_score ?? result.ai_score ?? 0)}
              </span>
            </div>
            <p class="text-sm text-white/50 mt-1">Authenticity score based on neural signal analysis</p>
            {#if result.confidence != null}
              <div class="mt-2 flex items-center gap-2">
                <span class="text-xs text-white/40">Confidence:</span>
                <div class="flex-1 h-1.5 rounded-full bg-white/10 max-w-32">
                  <div class="h-full rounded-full bg-neural-400 transition-all" style="width: {result.confidence * 100}%"></div>
                </div>
                <span class="text-xs text-neural-300">{(result.confidence * 100).toFixed(0)}%</span>
              </div>
            {/if}
          </div>
        </div>

        {#if result.signals?.length}
          <Card>
            <h3 class="text-sm font-semibold mb-4 text-neural-400">Detection Signals</h3>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {#each result.signals as signal}
                <div class="glass rounded-xl p-4 flex items-center justify-between">
                  <div class="min-w-0">
                    <p class="text-sm font-medium text-white/80">{signal.label || signal.name}</p>
                    <p class="text-xs text-white/40 mt-0.5">{signal.name || signal.label}</p>
                  </div>
                  <div class="flex items-center gap-2 shrink-0">
                    <span class={`text-sm font-bold ${signal.score > 0.7 ? 'text-red-400' : signal.score > 0.4 ? 'text-dopamine-400' : 'text-emerald-400'}`}>
                      {(signal.score * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              {/each}
            </div>
          </Card>
        {/if}

      {:else if activeTab === 'plagiarism'}
        <div class="flex items-start gap-6">
          <div class="w-28 h-28 shrink-0">
            <DoughnutChart value={(result.max_similarity ?? 0) / 100} color="#f59e0b" label="Similarity" />
          </div>
          <div>
            <div class="flex items-center gap-3">
              <h2 class="text-xl font-bold">Plagiarism Check</h2>
              {#if result.verdict}
                <span class={`px-3 py-1 rounded-full text-xs font-semibold border ${badgeClass(result.verdict)}`}>
                  {result.verdict}
                </span>
              {/if}
            </div>
            <p class="text-sm text-white/50 mt-1">
              Max similarity: <span class="text-dopamine-400 font-semibold">{((result.max_similarity ?? 0) * 100).toFixed(1)}%</span>
            </p>
          </div>
        </div>

        {#if result.matches?.length}
          <Card>
            <h3 class="text-sm font-semibold mb-4 text-dopamine-400">Matched Sources</h3>
            <div class="space-y-2">
              {#each result.matches as match}
                <div class="glass rounded-xl p-4">
                  <div class="flex items-center justify-between">
                    <p class="text-sm font-medium text-white/80 truncate">{match.source || match.url || 'Unknown source'}</p>
                    <span class={`text-sm font-bold shrink-0 ml-2 ${(match.similarity ?? 0) > 0.7 ? 'text-red-400' : (match.similarity ?? 0) > 0.4 ? 'text-dopamine-400' : 'text-emerald-400'}`}>
                      {((match.similarity ?? 0) * 100).toFixed(1)}%
                    </span>
                  </div>
                  {#if match.url && match.url !== match.source}
                    <p class="text-xs text-white/40 mt-1 truncate">{match.url}</p>
                  {/if}
                </div>
              {/each}
            </div>
          </Card>
        {/if}

      {:else if activeTab === 'tamper-check'}
        <div class="flex items-start gap-6">
          <div class="w-28 h-28 shrink-0">
            <DoughnutChart value={(result.risk_score ?? result.overall_score ?? 0) / 100} color="#10b981" label="Risk" />
          </div>
          <div>
            <div class="flex items-center gap-3">
              <h2 class="text-xl font-bold">Tamper Analysis</h2>
              {#if result.manipulation_risk}
                <span class={`px-3 py-1 rounded-full text-xs font-semibold border ${riskBadge(result.manipulation_risk)}`}>
                  {result.manipulation_risk}
                </span>
              {:else}
                <span class={`px-3 py-1 rounded-full text-xs font-semibold border ${riskBadge(result.risk ?? 'low')}`}>
                  {result.risk ?? 'Unknown'}
                </span>
              {/if}
            </div>
            <p class="text-sm text-white/50 mt-1">Error Level Analysis & tamper detection results</p>
          </div>
        </div>

        {#if result.ela_metrics}
          <Card>
            <h3 class="text-sm font-semibold mb-4 text-memory-400">ELA Metrics</h3>
            <div class="grid grid-cols-3 gap-4">
              {#if result.ela_metrics.mean != null}
                <div class="glass rounded-xl p-4 text-center">
                  <p class="text-xs text-white/40">Mean</p>
                  <p class="text-lg font-bold text-white/80">{result.ela_metrics.mean.toFixed(4)}</p>
                </div>
              {/if}
              {#if result.ela_metrics.std != null}
                <div class="glass rounded-xl p-4 text-center">
                  <p class="text-xs text-white/40">Std Dev</p>
                  <p class="text-lg font-bold text-white/80">{result.ela_metrics.std.toFixed(4)}</p>
                </div>
              {/if}
              {#if result.ela_metrics.variance != null}
                <div class="glass rounded-xl p-4 text-center">
                  <p class="text-xs text-white/40">Variance</p>
                  <p class="text-lg font-bold text-white/80">{result.ela_metrics.variance.toFixed(4)}</p>
                </div>
              {/if}
            </div>
          </Card>
        {/if}
      {/if}

      {#if result.overall_grade || result.overall_score != null}
        <Card>
          <div class="flex items-center justify-between">
            <div>
              <p class="text-xs text-white/40 uppercase tracking-wider">Overall Authenticity</p>
              <p class="text-lg font-bold mt-1">{result.overall_grade || getGrade(result.overall_score)}</p>
            </div>
            {#if result.tokens_used != null}
              <span class="text-xs text-dopamine-400">-{result.tokens_used} tokens</span>
            {/if}
          </div>
        </Card>
      {/if}

      <div class="flex justify-center">
        <Button onclick={resetResult} variant="secondary">Analyze Another</Button>
      </div>
    </div>
  {/if}
</div>
