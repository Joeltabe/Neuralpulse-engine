export function formatTokens(n: number): string {
  return n.toLocaleString();
}

export function formatPercent(n: number, decimals = 0): string {
  return `${(n * 100).toFixed(decimals)}%`;
}

export function formatDuration(sec: number): string {
  if (sec < 60) return `${sec.toFixed(1)}s`;
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${m}m ${s}s`;
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('en-US', {
    year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
  });
}

export function formatRelativeTime(iso: string): string {
  const now = Date.now();
  const diff = now - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  if (days < 30) return `${days}d ago`;
  return formatDate(iso);
}

export function priceDisplay(cents: number): string {
  return `$${(cents / 100).toFixed(2)}`;
}

export function gradeColor(grade: string): string {
  const colors: Record<string, string> = {
    'A+': 'text-emerald-400', 'A': 'text-emerald-400',
    'B+': 'text-neural-400', 'B': 'text-neural-400',
    'C+': 'text-dopamine-400', 'C': 'text-dopamine-400',
    'D': 'text-orange-400', 'F': 'text-red-400'
  };
  return colors[grade] || 'text-white/60';
}

export function severityColor(severity: string): string {
  const colors: Record<string, string> = {
    critical: 'text-red-400 bg-red-500/10 border-red-500/20',
    moderate: 'text-dopamine-400 bg-dopamine-500/10 border-dopamine-500/20',
    suggestion: 'text-neural-400 bg-neural-500/10 border-neural-500/20'
  };
  return colors[severity] || colors.suggestion;
}

export function classNames(...classes: (string | false | undefined | null)[]): string {
  return classes.filter(Boolean).join(' ');
}
