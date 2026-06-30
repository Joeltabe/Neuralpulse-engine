/**
 * RecommendationEngine.ts
 * 
 * TikTok/YouTube-Inspired Two-Stage Recommendation Pipeline
 * 
 * Stage 1 — Candidate Generation:
 *   Maps brain scores + engagement curves to a catalog of recommendation templates.
 *   Filters candidates by relevance threshold (like YouTube's candidate generation net).
 *
 * Stage 2 — Precision Ranking:
 *   Multi-signal fusion scoring (like TikTok's monolith model).
 *   Thompson sampling for exploration (like YouTube's contextual bandits).
 *   Watch-time-weighted impact prediction.
 *
 * This runs entirely client-side from existing AnalysisResult data.
 */

import type { AnalysisResult, Recommendation, BrainScores } from '$lib/types/api';

// ================================================================
// TYPES
// ================================================================

export interface RankedRecommendation extends Recommendation {
  rank: number;
  confidence: number;           // 0-1 from Thompson sampling
  neural_impact_score: number;  // predicted improvement magnitude
  affected_regions: AffectedRegion[];
  signal_breakdown: SignalBreakdown;
  why: string;                  // human-readable explanation
}

export interface AffectedRegion {
  key: string;       // e.g. 'frontal', 'temp'
  name: string;      // e.g. 'Frontal Lobe'
  activation: number;
  impact: 'primary' | 'secondary';
}

export interface SignalBreakdown {
  attention_signal: number;
  dopamine_signal: number;
  memory_signal: number;
  temporal_signal: number;
  pacing_signal: number;
}

export interface ContentProfile {
  attention_mean: number;
  attention_variance: number;
  attention_dropoff_count: number;
  attention_peak_count: number;
  dopamine_mean: number;
  dopamine_variance: number;
  dopamine_gap_score: number;    // how sparse are dopamine peaks
  memory_mean: number;
  memory_encoding_depth: number; // sustained memory signal
  engagement_trend: number;      // positive = growing, negative = declining
  engagement_volatility: number; // how jumpy is the curve
  pacing_score: number;          // scene transition frequency
  duration_sec: number;
  overall_grade_numeric: number;
}

// ================================================================
// RECOMMENDATION CATALOG
// Each template is a "candidate" that gets scored against the content
// ================================================================

interface CandidateTemplate {
  id: string;
  category: string;
  title: string;
  description: string;
  suggestion: string;
  // Which signals trigger this recommendation
  triggers: {
    signal: keyof SignalBreakdown;
    condition: 'low' | 'high' | 'volatile' | 'declining';
    threshold: number;
  }[];
  // Which brain regions this recommendation targets
  target_regions: string[];
  // Base severity weight
  base_severity: 'critical' | 'moderate' | 'suggestion';
  // Expected improvement range
  impact_range: [number, number];
}

const RECOMMENDATION_CATALOG: CandidateTemplate[] = [
  // ── ATTENTION: Hook & Opening ──
  {
    id: 'hook-weak-opening',
    category: 'Hook',
    title: 'Weak Opening — Viewers Drop in First 3 Seconds',
    description: 'The opening fails to capture immediate attention. TikTok data shows 65% of viewers decide within 1 second whether to keep watching.',
    suggestion: 'Start with a pattern interrupt — unexpected visual, provocative question, or mid-action shot. Remove any logos or intros before the hook.',
    triggers: [{ signal: 'attention_signal', condition: 'low', threshold: 0.45 }],
    target_regions: ['frontal', 'occipit'],
    base_severity: 'critical',
    impact_range: [0.15, 0.35]
  },
  {
    id: 'hook-no-curiosity-gap',
    category: 'Hook',
    title: 'No Curiosity Gap — Nothing Pulls Viewers Forward',
    description: 'The content lacks an open loop that creates anticipation. YouTube\'s algorithm rewards content that generates sustained watch time through curiosity.',
    suggestion: 'Plant an unanswered question or tease a payoff in the first 2 seconds. "Watch what happens when..." or show the end result first.',
    triggers: [{ signal: 'dopamine_signal', condition: 'low', threshold: 0.40 }],
    target_regions: ['frontal', 'stem'],
    base_severity: 'critical',
    impact_range: [0.12, 0.30]
  },
  // ── ATTENTION: Sustained ──
  {
    id: 'attention-midroll-drop',
    category: 'Pacing',
    title: 'Mid-Content Attention Cliff',
    description: 'Attention drops sharply in the middle section. This is where most viewers bounce — the content loses energy after the initial hook.',
    suggestion: 'Insert a "mini-hook" every 15-30 seconds: a scene change, new angle, text overlay, sound effect, or rhetorical question to re-engage.',
    triggers: [{ signal: 'temporal_signal', condition: 'declining', threshold: 0.30 }],
    target_regions: ['frontal', 'pariet'],
    base_severity: 'critical',
    impact_range: [0.10, 0.25]
  },
  {
    id: 'attention-flat-energy',
    category: 'Pacing',
    title: 'Flat Energy — No Peaks or Valleys',
    description: 'The engagement curve is monotone. TikTok\'s algorithm penalizes content with flat watch patterns because it signals low emotional investment.',
    suggestion: 'Create deliberate tension arcs: build → peak → release. Vary vocal intensity, music volume, and visual density to create rhythm.',
    triggers: [{ signal: 'attention_signal', condition: 'low', threshold: 0.50 }, { signal: 'pacing_signal', condition: 'low', threshold: 0.35 }],
    target_regions: ['frontal', 'pariet', 'occipit'],
    base_severity: 'moderate',
    impact_range: [0.08, 0.20]
  },
  {
    id: 'pacing-too-slow',
    category: 'Pacing',
    title: 'Pacing Too Slow — Losing Scroll-Happy Viewers',
    description: 'Scene transitions and information delivery are slower than optimal. Modern viewers, trained by TikTok, expect new visual information every 2-3 seconds.',
    suggestion: 'Cut dead air, tighten transitions, use jump cuts. Every shot should advance the story or add new visual information.',
    triggers: [{ signal: 'pacing_signal', condition: 'low', threshold: 0.30 }],
    target_regions: ['frontal', 'occipit'],
    base_severity: 'moderate',
    impact_range: [0.08, 0.18]
  },
  {
    id: 'pacing-too-fast',
    category: 'Pacing',
    title: 'Pacing Too Fast — Brain Can\'t Process',
    description: 'Information is delivered faster than the brain can encode. Memory scores drop when visual change rate exceeds cognitive processing capacity.',
    suggestion: 'Add brief pauses (0.5-1s) after key moments to let the brain consolidate. Use slower reveals for important information.',
    triggers: [{ signal: 'pacing_signal', condition: 'high', threshold: 0.85 }, { signal: 'memory_signal', condition: 'low', threshold: 0.40 }],
    target_regions: ['temp', 'pariet'],
    base_severity: 'moderate',
    impact_range: [0.06, 0.15]
  },
  // ── DOPAMINE: Reward & Emotion ──
  {
    id: 'dopamine-no-payoff',
    category: 'Emotional Arc',
    title: 'No Reward Payoff — Brain Doesn\'t Get the Hit',
    description: 'The content builds expectation but never delivers a satisfying payoff. The ventral striatum shows low activation — viewers feel unsatisfied.',
    suggestion: 'Deliver on every promise. If you tease a result, show it. Add micro-payoffs: reveals, transformations, satisfying outcomes, or emotional peaks.',
    triggers: [{ signal: 'dopamine_signal', condition: 'low', threshold: 0.35 }],
    target_regions: ['stem', 'corpus', 'frontal'],
    base_severity: 'critical',
    impact_range: [0.12, 0.28]
  },
  {
    id: 'dopamine-sparse-peaks',
    category: 'Emotional Arc',
    title: 'Dopamine Peaks Too Far Apart',
    description: 'Reward signals are spaced too widely. YouTube data shows the optimal dopamine hit frequency is every 8-12 seconds for short-form content.',
    suggestion: 'Add micro-rewards between major payoffs: satisfying sound effects, visual reveals, humor beats, progress indicators, or "aha" moments.',
    triggers: [{ signal: 'dopamine_signal', condition: 'low', threshold: 0.45 }],
    target_regions: ['stem', 'frontal'],
    base_severity: 'moderate',
    impact_range: [0.08, 0.20]
  },
  {
    id: 'dopamine-no-emotional-contrast',
    category: 'Emotional Arc',
    title: 'No Emotional Contrast — Content Feels One-Note',
    description: 'The emotional valence stays constant. The brain habituates to a single emotional register, reducing engagement over time.',
    suggestion: 'Alternate between tension and relief, humor and seriousness, excitement and calm. Contrast makes each emotion hit harder.',
    triggers: [{ signal: 'dopamine_signal', condition: 'low', threshold: 0.50 }, { signal: 'attention_signal', condition: 'volatile', threshold: 0.60 }],
    target_regions: ['temp', 'frontal', 'stem'],
    base_severity: 'moderate',
    impact_range: [0.07, 0.18]
  },
  {
    id: 'dopamine-missing-social-proof',
    category: 'Persuasion',
    title: 'Missing Social Proof Triggers',
    description: 'Content lacks social validation cues. The brain\'s reward system activates 40% more when content includes evidence of others\' reactions.',
    suggestion: 'Show reactions, testimonials, numbers ("10M views"), crowd responses, or before/after comparisons with social context.',
    triggers: [{ signal: 'dopamine_signal', condition: 'low', threshold: 0.42 }],
    target_regions: ['temp', 'frontal'],
    base_severity: 'suggestion',
    impact_range: [0.05, 0.14]
  },
  // ── MEMORY: Encoding & Recall ──
  {
    id: 'memory-no-anchor',
    category: 'Memorability',
    title: 'No Memory Anchor — Content Won\'t Stick',
    description: 'Hippocampal activation is weak. Without strong memory encoding, viewers won\'t recall the brand, message, or CTA.',
    suggestion: 'Add distinctive elements: a unique visual motif, a catchy phrase, an unexpected metaphor, or a signature sound. Repeat the key message 2-3 times.',
    triggers: [{ signal: 'memory_signal', condition: 'low', threshold: 0.40 }],
    target_regions: ['temp', 'pariet', 'frontal'],
    base_severity: 'critical',
    impact_range: [0.10, 0.25]
  },
  {
    id: 'memory-no-story-structure',
    category: 'Memorability',
    title: 'Weak Narrative Structure — Hard to Follow',
    description: 'The content lacks a clear beginning-middle-end arc. The brain encodes information 22x better when structured as a story.',
    suggestion: 'Frame content as: Setup (problem) → Confrontation (tension) → Resolution (payoff). Even 15-second clips benefit from micro-narratives.',
    triggers: [{ signal: 'memory_signal', condition: 'low', threshold: 0.45 }, { signal: 'attention_signal', condition: 'declining', threshold: 0.40 }],
    target_regions: ['temp', 'frontal'],
    base_severity: 'moderate',
    impact_range: [0.08, 0.20]
  },
  {
    id: 'memory-cognitive-overload',
    category: 'Memorability',
    title: 'Cognitive Overload — Too Much at Once',
    description: 'Multiple competing stimuli overwhelm working memory. The DLPFC can only hold 4±1 items simultaneously.',
    suggestion: 'Simplify each moment: one key visual + one key message. Remove competing text overlays, reduce simultaneous information streams.',
    triggers: [{ signal: 'memory_signal', condition: 'low', threshold: 0.38 }, { signal: 'pacing_signal', condition: 'high', threshold: 0.80 }],
    target_regions: ['frontal', 'pariet'],
    base_severity: 'moderate',
    impact_range: [0.07, 0.18]
  },
  {
    id: 'memory-weak-ending',
    category: 'Memorability',
    title: 'Weak Ending — No Lasting Impression',
    description: 'The final moments lack impact. The peak-end rule shows the brain disproportionately remembers the last thing experienced.',
    suggestion: 'End with the strongest moment: a powerful visual, an emotional peak, a clear CTA, or a callback to the opening hook. Never fade to nothing.',
    triggers: [{ signal: 'memory_signal', condition: 'declining', threshold: 0.35 }],
    target_regions: ['temp', 'pariet', 'frontal'],
    base_severity: 'moderate',
    impact_range: [0.08, 0.20]
  },
  // ── VISUAL ──
  {
    id: 'visual-low-contrast',
    category: 'Visual',
    title: 'Low Visual Contrast — Eyes Don\'t Know Where to Look',
    description: 'The visual field lacks focal hierarchy. The occipital cortex responds strongest to high-contrast, well-composed focal points.',
    suggestion: 'Use contrast (light/dark, color/neutral, large/small) to direct the eye. Ensure the subject pops against the background.',
    triggers: [{ signal: 'attention_signal', condition: 'low', threshold: 0.48 }],
    target_regions: ['occipit', 'pariet'],
    base_severity: 'moderate',
    impact_range: [0.06, 0.16]
  },
  {
    id: 'visual-no-faces',
    category: 'Visual',
    title: 'No Human Faces — Missing Strongest Attention Magnet',
    description: 'The fusiform face area (FFA) is the brain\'s most powerful involuntary attention trigger. Content without faces loses this advantage.',
    suggestion: 'Include human faces, especially making eye contact with the camera. Face-forward shots generate 2.5x more engagement.',
    triggers: [{ signal: 'attention_signal', condition: 'low', threshold: 0.52 }],
    target_regions: ['occipit', 'temp', 'frontal'],
    base_severity: 'suggestion',
    impact_range: [0.05, 0.15]
  },
  {
    id: 'visual-static-composition',
    category: 'Visual',
    title: 'Static Visual Composition — No Motion Energy',
    description: 'The visual field lacks dynamic movement. Motion in the periphery triggers involuntary attention shifts through the superior colliculus.',
    suggestion: 'Add camera movement (subtle push-in, tracking), dynamic text animations, or subject movement. Static frames lose to scrolling feeds.',
    triggers: [{ signal: 'attention_signal', condition: 'low', threshold: 0.45 }, { signal: 'pacing_signal', condition: 'low', threshold: 0.35 }],
    target_regions: ['occipit', 'pariet'],
    base_severity: 'suggestion',
    impact_range: [0.05, 0.14]
  },
  // ── AUDIO ──
  {
    id: 'audio-low-energy',
    category: 'Audio',
    title: 'Audio Energy Flat — Sound Isn\'t Driving Emotion',
    description: 'The auditory cortex and amygdala respond to dynamic audio. Flat audio energy means the soundtrack isn\'t amplifying the emotional arc.',
    suggestion: 'Match music/sound energy to the content arc. Build during tension, peak during reveals, soften during intimate moments. Use trending sounds.',
    triggers: [{ signal: 'dopamine_signal', condition: 'low', threshold: 0.45 }, { signal: 'attention_signal', condition: 'low', threshold: 0.50 }],
    target_regions: ['temp', 'stem'],
    base_severity: 'moderate',
    impact_range: [0.07, 0.18]
  },
  {
    id: 'audio-no-sound-design',
    category: 'Audio',
    title: 'Missing Sound Design — No Sonic Texture',
    description: 'Content lacks layered audio (foley, effects, ambient). Multi-layer sound activates deeper temporal processing and increases perceived production quality.',
    suggestion: 'Layer 2-3 audio tracks: voice + music + effects. Add whooshes on transitions, impacts on reveals, ambient texture for immersion.',
    triggers: [{ signal: 'dopamine_signal', condition: 'low', threshold: 0.48 }],
    target_regions: ['temp', 'stem'],
    base_severity: 'suggestion',
    impact_range: [0.04, 0.12]
  },
  // ── TEXT / CTA ──
  {
    id: 'text-no-cta',
    category: 'CTA',
    title: 'No Clear Call-to-Action',
    description: 'The content doesn\'t direct viewer behavior. Without a clear CTA, the prefrontal cortex doesn\'t engage decision-making circuits.',
    suggestion: 'End with one clear, specific action: "Follow for part 2", "Link in bio", "Comment your answer". Make it feel urgent or exclusive.',
    triggers: [{ signal: 'memory_signal', condition: 'low', threshold: 0.42 }, { signal: 'dopamine_signal', condition: 'low', threshold: 0.45 }],
    target_regions: ['frontal'],
    base_severity: 'moderate',
    impact_range: [0.06, 0.15]
  },
  {
    id: 'text-too-dense',
    category: 'Text',
    title: 'Text Overlays Too Dense — Viewers Skip Reading',
    description: 'On-screen text competes with visuals for occipital processing bandwidth. Dense text blocks get skipped entirely on mobile feeds.',
    suggestion: 'Limit on-screen text to 5-7 words per frame. Use large, high-contrast fonts. Reveal text word-by-word for better attention capture.',
    triggers: [{ signal: 'attention_signal', condition: 'low', threshold: 0.45 }, { signal: 'memory_signal', condition: 'low', threshold: 0.40 }],
    target_regions: ['occipit', 'frontal'],
    base_severity: 'suggestion',
    impact_range: [0.04, 0.12]
  },
  // ── TRANSITION / SCENE ──
  {
    id: 'transition-jarring',
    category: 'Transitions',
    title: 'Jarring Transitions — Brain Needs to Re-orient',
    description: 'Abrupt scene changes without visual flow force the parietal cortex to spend cognitive resources re-orienting, breaking engagement.',
    suggestion: 'Use motivated transitions: match-cuts, movement-based transitions, or brief fade-throughs. Each cut should feel intentional, not random.',
    triggers: [{ signal: 'attention_signal', condition: 'volatile', threshold: 0.55 }, { signal: 'pacing_signal', condition: 'high', threshold: 0.75 }],
    target_regions: ['pariet', 'occipit', 'frontal'],
    base_severity: 'moderate',
    impact_range: [0.06, 0.15]
  },
  {
    id: 'transition-too-few',
    category: 'Transitions',
    title: 'Too Few Scene Changes — Visual Monotony',
    description: 'Extended single-shot content causes habituation in the visual cortex. The brain stops actively processing familiar static scenes.',
    suggestion: 'Break long shots into multiple angles. Add B-roll cutaways, close-ups, or reaction shots every 3-5 seconds for short-form content.',
    triggers: [{ signal: 'pacing_signal', condition: 'low', threshold: 0.28 }, { signal: 'attention_signal', condition: 'declining', threshold: 0.40 }],
    target_regions: ['occipit', 'pariet'],
    base_severity: 'moderate',
    impact_range: [0.07, 0.17]
  },
  // ── PLATFORM-SPECIFIC ──
  {
    id: 'platform-loop-potential',
    category: 'Virality',
    title: 'Low Loop Potential — Won\'t Trigger Rewatches',
    description: 'TikTok\'s algorithm heavily weights replays. Content that loops seamlessly gets 3-5x more distribution.',
    suggestion: 'Design the ending to connect back to the beginning. Create a "wait, what?" moment that makes viewers rewatch. The last frame should tease the first.',
    triggers: [{ signal: 'dopamine_signal', condition: 'low', threshold: 0.50 }, { signal: 'memory_signal', condition: 'low', threshold: 0.45 }],
    target_regions: ['frontal', 'stem', 'temp'],
    base_severity: 'suggestion',
    impact_range: [0.08, 0.22]
  },
  {
    id: 'platform-share-triggers',
    category: 'Virality',
    title: 'No Share Triggers — Viewers Won\'t Forward This',
    description: 'Content lacks emotional intensity needed to trigger sharing behavior. People share content that makes them feel something strongly.',
    suggestion: 'Amplify one emotion to an extreme: make it funnier, more shocking, more heartwarming, or more relatable. Moderate emotions don\'t get shared.',
    triggers: [{ signal: 'dopamine_signal', condition: 'low', threshold: 0.45 }, { signal: 'attention_signal', condition: 'low', threshold: 0.50 }],
    target_regions: ['temp', 'frontal', 'stem'],
    base_severity: 'suggestion',
    impact_range: [0.06, 0.18]
  },
  {
    id: 'platform-comment-bait',
    category: 'Virality',
    title: 'No Comment Triggers — Viewers Watch and Leave',
    description: 'The content doesn\'t provoke a response. YouTube and TikTok both weight comments heavily — they signal deep engagement.',
    suggestion: 'Include a debatable opinion, ask a direct question, make a claim viewers want to correct, or leave something intentionally ambiguous.',
    triggers: [{ signal: 'dopamine_signal', condition: 'low', threshold: 0.48 }],
    target_regions: ['frontal', 'temp'],
    base_severity: 'suggestion',
    impact_range: [0.05, 0.15]
  },
  // ── ADVANCED PATTERNS ──
  {
    id: 'advanced-pattern-interrupt',
    category: 'Advanced',
    title: 'Missing Pattern Interrupts — Brain Auto-pilots',
    description: 'The brain enters default mode network when content becomes predictable. Without interrupts, viewers zone out even while "watching".',
    suggestion: 'Every 8-10 seconds, break the pattern: unexpected angle, sudden silence, visual glitch effect, tone shift, or surprising fact.',
    triggers: [{ signal: 'attention_signal', condition: 'declining', threshold: 0.42 }, { signal: 'pacing_signal', condition: 'low', threshold: 0.40 }],
    target_regions: ['frontal', 'pariet'],
    base_severity: 'moderate',
    impact_range: [0.07, 0.18]
  },
  {
    id: 'advanced-cognitive-fluency',
    category: 'Advanced',
    title: 'Low Cognitive Fluency — Content Feels "Hard"',
    description: 'The brain prefers content that\'s easy to process. Low fluency (complex visuals + fast audio + dense text) creates friction that drives viewers away.',
    suggestion: 'Simplify: clear focal point, steady audio pace, minimal competing information. Make the content feel effortless to consume.',
    triggers: [{ signal: 'memory_signal', condition: 'low', threshold: 0.38 }, { signal: 'attention_signal', condition: 'low', threshold: 0.42 }],
    target_regions: ['frontal', 'pariet', 'temp'],
    base_severity: 'moderate',
    impact_range: [0.06, 0.16]
  },
  {
    id: 'advanced-anticipation-gap',
    category: 'Advanced',
    title: 'No Anticipation Build — Dopamine Stays Flat',
    description: 'Dopamine fires more during anticipation than reward itself. Content that delivers everything immediately misses the brain\'s most powerful engagement mechanism.',
    suggestion: 'Delay gratification: tease the payoff, build towards reveals, use countdowns or progressive disclosure. Make viewers want what\'s coming next.',
    triggers: [{ signal: 'dopamine_signal', condition: 'low', threshold: 0.42 }],
    target_regions: ['stem', 'frontal', 'corpus'],
    base_severity: 'moderate',
    impact_range: [0.08, 0.20]
  },
  // ── ENGAGEMENT CURVE SPECIFIC ──
  {
    id: 'curve-front-loaded',
    category: 'Engagement Curve',
    title: 'Front-Loaded Content — All Energy Spent Early',
    description: 'Engagement peaks in the first quarter then steadily declines. The algorithm interprets this as clickbait — strong hook, weak content.',
    suggestion: 'Redistribute your best moments: put 30% of energy in the hook, 40% in the middle, 30% in the ending. Save a strong moment for the final third.',
    triggers: [{ signal: 'temporal_signal', condition: 'declining', threshold: 0.35 }],
    target_regions: ['frontal', 'pariet'],
    base_severity: 'critical',
    impact_range: [0.10, 0.25]
  },
  {
    id: 'curve-slow-burn',
    category: 'Engagement Curve',
    title: 'Slow Burn Start — Losing Viewers Before the Good Part',
    description: 'Content gets better over time but the algorithm never sees it because viewers leave before the payoff. 50% of viewers drop in the first 25%.',
    suggestion: 'Move your best moment to the first 3 seconds as a teaser, then loop back to build towards it. Front-load the value proposition.',
    triggers: [{ signal: 'attention_signal', condition: 'low', threshold: 0.42 }, { signal: 'temporal_signal', condition: 'low', threshold: 0.35 }],
    target_regions: ['frontal', 'occipit'],
    base_severity: 'critical',
    impact_range: [0.12, 0.30]
  },
  {
    id: 'curve-volatile',
    category: 'Engagement Curve',
    title: 'Volatile Engagement — Viewer Experience is Inconsistent',
    description: 'Engagement spikes and crashes unpredictably. This creates an inconsistent viewer experience that confuses the algorithm.',
    suggestion: 'Smooth the transitions between high and low energy. Create a consistent rhythm rather than random spikes. Think of it as a heartbeat, not static.',
    triggers: [{ signal: 'attention_signal', condition: 'volatile', threshold: 0.60 }],
    target_regions: ['frontal', 'pariet'],
    base_severity: 'moderate',
    impact_range: [0.06, 0.15]
  },
  // ════════════════════════════════════════════════════════════════════
  // NEURO-SURGICAL DIRECTIVES — COLOR & LIGHTING
  // ════════════════════════════════════════════════════════════════════
  {
    id: 'color-low-contrast-occipital',
    category: 'Color & Lighting',
    title: 'Low Visual Contrast — Occipital Lobe Under-Stimulated',
    description: 'The occipital lobe (V1-V3) is receiving insufficient contrast differential. The lateral geniculate nucleus needs strong edge boundaries to fire direction-selective cells.',
    suggestion: 'Increase global saturation by 15% in the first 3 seconds. Shift lighting from flat ambient to high-contrast directional lighting. Position a key light at 45 degrees to create chiaroscuro depth. Target a luminance ratio of 3:1 between key and fill to force visual cortex engagement.',
    triggers: [{ signal: 'attention_signal', condition: 'low', threshold: 0.40 }],
    target_regions: ['occipit', 'pariet'],
    base_severity: 'critical',
    impact_range: [0.15, 0.35]
  },
  {
    id: 'color-wrong-temperature',
    category: 'Color & Lighting',
    title: 'Wrong Color Temperature — Emotional Tone Mismatch',
    description: 'Color temperature doesn\'t match the intended emotional valence. Warm light (3200K) triggers parasympathetic comfort; cool light (5600K) triggers alertness. Mismatch creates cognitive dissonance.',
    suggestion: 'Match color temperature to content emotion. For warm/trust content: 3200K tungsten with golden hour hues. For high-energy/alert content: 5600K daylight with blue accents. Use teal-orange color grading for human subjects — complementary skin-tone/background contrast maximizes V4 color region response.',
    triggers: [{ signal: 'dopamine_signal', condition: 'low', threshold: 0.40 }, { signal: 'attention_signal', condition: 'low', threshold: 0.45 }],
    target_regions: ['occipit', 'stem', 'frontal'],
    base_severity: 'moderate',
    impact_range: [0.10, 0.25]
  },
  {
    id: 'color-no-s-curve',
    category: 'Color & Lighting',
    title: 'Un-graded Footage — Flat Dynamic Range Dulls V1 Firing',
    description: 'Flat log or ungraded footage provides insufficient luminance range. V1 simple cells require high edge contrast to fire optimally. Flat footage literally doesn\'t register in early visual processing.',
    suggestion: 'Apply an S-curve contrast grade: lift shadows by +10, pull highlights by -5. Add a subtle vignette (20% darkening at edges) to focus attention on the center of frame — the retina\'s fovea is 50% more sensitive to central contrast. Avoid crushed blacks: the visual system uses shadow detail to judge depth.',
    triggers: [{ signal: 'attention_signal', condition: 'low', threshold: 0.42 }],
    target_regions: ['occipit'],
    base_severity: 'moderate',
    impact_range: [0.08, 0.20]
  },
  {
    id: 'color-dim-underexposed',
    category: 'Color & Lighting',
    title: 'Under-Exposed Footage — Pupil Dilation Hurts Processing',
    description: 'Content is too dark. The brain unconsciously dilates pupils to gather more light, increasing cognitive load by 15-20%. Dark content that isn\'t intentionally moody feels "hard to watch."',
    suggestion: 'Raise exposure by 0.5-1.0 stops. Ensure the subject\'s face is properly exposed (60-70 IRE for skin tones). If the dark look is intentional, add a bright accent (catchlight in eyes, backlight rim) to give the brain a luminance reference point. Never let skin tones fall below 40 IRE.',
    triggers: [{ signal: 'attention_signal', condition: 'low', threshold: 0.38 }],
    target_regions: ['occipit', 'stem'],
    base_severity: 'moderate',
    impact_range: [0.10, 0.22]
  },
  {
    id: 'color-no-focal-hierarchy',
    category: 'Color & Lighting',
    title: 'No Focal Hierarchy — Brain Doesn\'t Know Where to Look',
    description: 'The frame lacks a dominant visual anchor. The superior colliculus automatically directs gaze to the highest-contrast region — if everything is equal contrast, attention scatters.',
    suggestion: 'Create a clear focal point: brighten the subject by +15% relative to background, or add a colored accent (red/orange) on the primary element. The visual cortex processes warm colors 50ms faster than cool colors. Position the focal anchor at a rule-of-thirds intersection for optimal saccadic targeting.',
    triggers: [{ signal: 'attention_signal', condition: 'low', threshold: 0.44 }, { signal: 'pacing_signal', condition: 'low', threshold: 0.40 }],
    target_regions: ['occipit', 'pariet', 'frontal'],
    base_severity: 'moderate',
    impact_range: [0.08, 0.18]
  },
  // ════════════════════════════════════════════════════════════════════
  // NEURO-SURGICAL DIRECTIVES — CAMERA ANGLE & FRAMING
  // ════════════════════════════════════════════════════════════════════
  {
    id: 'camera-too-distant',
    category: 'Camera & Framing',
    title: 'Subject Too Distant — No Parasocial Bond Forming',
    description: 'The camera is positioned more than 6 feet from the subject. At this distance, facial micro-expressions are invisible and the fusiform face area (FFA) doesn\'t engage. The brain categorizes the subject as "background" not "conversation partner."',
    suggestion: 'Move camera to within 3 feet of the subject. A medium close-up (head and shoulders, face filling 60%+ of frame) triggers the FFA optimally — the brain treats this as intimate conversation distance. If using a phone, 2x zoom at 2 feet achieves the same framing. Eye contact with the lens is non-negotiable.',
    triggers: [{ signal: 'dopamine_signal', condition: 'low', threshold: 0.38 }, { signal: 'memory_signal', condition: 'low', threshold: 0.40 }],
    target_regions: ['temp', 'occipit', 'frontal'],
    base_severity: 'critical',
    impact_range: [0.15, 0.32]
  },
  {
    id: 'camera-no-eye-contact',
    category: 'Camera & Framing',
    title: 'No Eye Contact — Viewers Feel Spoken "At" Not "To"',
    description: 'The speaker is looking off-camera or at a viewfinder. The superior temporal sulcus (STS) detects gaze direction within 200ms — off-axis gaze signals disinterest or dishonesty to the limbic system.',
    suggestion: 'Speaker must look directly into the lens. Place a small sticker with a dot right next to the lens as a gaze target. The 2-degree difference between looking at the lens vs. looking at the screen is detectable by viewers. Direct gaze triggers the STS to process intentionality, creating a parasocial bond within 3 seconds.',
    triggers: [{ signal: 'dopamine_signal', condition: 'low', threshold: 0.42 }],
    target_regions: ['temp', 'stem', 'frontal'],
    base_severity: 'critical',
    impact_range: [0.12, 0.28]
  },
  {
    id: 'camera-wrong-angle',
    category: 'Camera & Framing',
    title: 'Unflattering Camera Angle — Subconscious Negative Bias',
    description: 'Low-angle shots (camera below eye level) activate amygdala threat detection. Extreme high angles activate caregiving circuits but reduce authority. Neutral eye-level is safe but emotionally flat.',
    suggestion: 'Use a slight high angle (15 degrees above eye level) for warmth and trust — this subtle angle triggers caregiving circuits in the amygdala. For authority segments, switch to eye-level. For emotional moments, push to a 30-degree high-angle close-up: the combination of proximity + vulnerability maximizes parasocial bonding.',
    triggers: [{ signal: 'dopamine_signal', condition: 'low', threshold: 0.45 }],
    target_regions: ['stem', 'temp', 'frontal'],
    base_severity: 'moderate',
    impact_range: [0.08, 0.20]
  },
  {
    id: 'camera-static-monotone',
    category: 'Camera & Framing',
    title: 'Static Camera — Visual Habituation Sets In',
    description: 'A locked-down, non-moving camera leads to rapid visual habituation. The visual cortex stops processing familiar static scenes within 8-12 seconds. Motion in the periphery triggers involuntary attention shifts through the superior colliculus.',
    suggestion: 'Add subtle camera motion: slow push-in during important statements (creates intimacy), slow pull-out during transitions (creates breathing room). Use a 3-axis gimbal or warp stabilizer for handheld feel. Even 0.5 degrees of dutch tilt during high-tension moments signals "something is wrong" subconsciously, increasing engagement.',
    triggers: [{ signal: 'attention_signal', condition: 'low', threshold: 0.42 }, { signal: 'pacing_signal', condition: 'low', threshold: 0.32 }],
    target_regions: ['occipit', 'pariet', 'frontal'],
    base_severity: 'moderate',
    impact_range: [0.07, 0.18]
  },
  {
    id: 'camera-too-close-aggressive',
    category: 'Camera & Framing',
    title: 'Too Close / Wide Lens — Subconscious Threat Response',
    description: 'An ultra-wide lens (< 24mm equivalent) at close range distorts facial proportions. The brain detects the distortion subconsciously and categorizes it as "uncanny" — activation drops in the FFA.',
    suggestion: 'Use a 50-85mm equivalent focal length for face shots. This focal range matches natural human vision perspective. If using a phone, 2-3x zoom at 3-4 feet distance. The FFA activates most strongly when facial proportions match the innate "face template" the brain developed through evolution.',
    triggers: [{ signal: 'dopamine_signal', condition: 'low', threshold: 0.40 }],
    target_regions: ['temp', 'occipit', 'stem'],
    base_severity: 'moderate',
    impact_range: [0.06, 0.16]
  },
  // ════════════════════════════════════════════════════════════════════
  // NEURO-SURGICAL DIRECTIVES — SOUND & AUDIO PACING
  // ════════════════════════════════════════════════════════════════════
  {
    id: 'audio-vocal-muddy',
    category: 'Sound & Audio',
    title: 'Muddy Vocal — Auditory Cortex Can\'t Parse Speech',
    description: 'The vocal track is drowning in low-mid frequencies (200-500 Hz). The primary auditory cortex (A1) needs the 2-4 kHz presence range to resolve consonants. Without clear consonants, the brain works 30% harder to understand speech.',
    suggestion: 'Apply vocal EQ: boost 2-4 kHz (presence range) by 3-4 dB, cut 200-300 Hz (muddy range) by 2-3 dB, high-pass filter at 80 Hz to remove rumble. The brain resolves consonants in the 2-4 kHz range — this alone creates "perceived clarity." If the recording is noisy, use a noise gate at -40 dB threshold with 10ms attack.',
    triggers: [{ signal: 'attention_signal', condition: 'low', threshold: 0.40 }, { signal: 'memory_signal', condition: 'low', threshold: 0.38 }],
    target_regions: ['temp', 'frontal'],
    base_severity: 'critical',
    impact_range: [0.15, 0.30]
  },
  {
    id: 'audio-no-sub-bass',
    category: 'Sound & Audio',
    title: 'Missing Sub-Bass Frequencies — Brainstem Bypass Missing',
    description: 'Content lacks sub-bass frequencies (40-80 Hz). Sub-bass bypasses conscious hearing and directly activates the brainstem\'s reticular activating system — it creates tension and anticipation without the viewer knowing why.',
    suggestion: 'During high-tension or high-emotion moments, add a subtle sub-bass tone (50-60 Hz, -18dB below dialogue). This frequency range is felt more than heard, activating the vestibulocochlear nerve directly. Use a sine wave generator or a dedicated sub-bass sound effect. Limit to 1-3 second bursts — the brain habituates quickly.',
    triggers: [{ signal: 'dopamine_signal', condition: 'low', threshold: 0.42 }],
    target_regions: ['stem', 'temp'],
    base_severity: 'suggestion',
    impact_range: [0.05, 0.14]
  },
  {
    id: 'audio-no-riser-transitions',
    category: 'Sound & Audio',
    title: 'No Audio Riser on Transitions — Missed Dopamine Cue',
    description: 'Scene transitions lack audio cues. The brain uses audio transitions as dopamine anticipation signals — a rising tone before a reveal triggers prediction error when the payoff arrives.',
    suggestion: 'Add a riser (rising pitch sound effect) starting 0.5 seconds before each transition or reveal. The rising frequency creates tension that releases when the new visual arrives — this is a classic dopamine prediction-error loop. Use a 300ms-800ms riser at -15dB with an exponential pitch curve. Match the riser length to the transition speed.',
    triggers: [{ signal: 'dopamine_signal', condition: 'low', threshold: 0.45 }, { signal: 'pacing_signal', condition: 'low', threshold: 0.38 }],
    target_regions: ['temp', 'stem', 'frontal'],
    base_severity: 'suggestion',
    impact_range: [0.04, 0.12]
  },
  {
    id: 'audio-pacing-dropoff',
    category: 'Sound & Audio',
    title: 'Audio-Induced Attention Drop — Habituation to Consistent Sound',
    description: 'The auditory cortex habituates to consistent sound within 8-12 seconds. If the audio mix (voice + music + effects) stays constant, the brain begins filtering it out, and attention drops correlate with these habituation points.',
    suggestion: 'Every 8-12 seconds, vary one audio element: drop the music out for 2 seconds, add a sound effect, change vocal delivery speed, or introduce a 0.3s silence. These "audio pattern interrupts" force an orienting response that resets attention. The most effective pattern interrupt is sudden silence — the brain treats silence as a threat signal.',
    triggers: [{ signal: 'temporal_signal', condition: 'declining', threshold: 0.30 }, { signal: 'attention_signal', condition: 'declining', threshold: 0.38 }],
    target_regions: ['temp', 'stem', 'pariet'],
    base_severity: 'moderate',
    impact_range: [0.08, 0.20]
  },
  {
    id: 'audio-music-wrong-energy',
    category: 'Sound & Audio',
    title: 'Mismatched Music Energy — Emotional Arc Contradicted',
    description: 'Background music energy doesn\'t match the visual emotional arc. The amygdala processes music and visual emotion together — mismatch creates cognitive dissonance that reduces engagement.',
    suggestion: 'Match the music\'s energy envelope to the content arc: rising energy during building tension, peak energy at reveals, falling energy during reflective moments, cut to silence before the climax. For short-form content, use a single track with a clear energy structure. Music should amplify, not compete with, the emotional journey.',
    triggers: [{ signal: 'dopamine_signal', condition: 'low', threshold: 0.40 }, { signal: 'memory_signal', condition: 'low', threshold: 0.42 }],
    target_regions: ['temp', 'stem', 'frontal'],
    base_severity: 'moderate',
    impact_range: [0.08, 0.18]
  },
  // ════════════════════════════════════════════════════════════════════
  // NEURO-SURGICAL DIRECTIVES — INTRO & OUTRO MECHANICS
  // ════════════════════════════════════════════════════════════════════
  {
    id: 'intro-no-pattern-interrupt',
    category: 'Intro/Outro Mechanics',
    title: 'No Pattern Interrupt — Brain Auto-Pilots Past the Hook',
    description: 'The opening is predictable (fade in, logo, "Hi everyone"). The brain\'s default mode network recognizes this as "safe/intro" and reduces attention. No orienting response is triggered.',
    suggestion: 'Start mid-action — the first frame must be the most visually intense frame of the entire video. Open with a surprising visual, a provocative question mid-sentence, or the end result before explaining how you got there. The brain needs an "orienting response" within the first 500ms — this means maximum contrast, motion, or surprise in frame one. No logos, no fades, no countdowns.',
    triggers: [{ signal: 'attention_signal', condition: 'low', threshold: 0.45 }],
    target_regions: ['frontal', 'occipit', 'stem'],
    base_severity: 'critical',
    impact_range: [0.18, 0.35]
  },
  {
    id: 'intro-curiosity-gap-missing',
    category: 'Intro/Outro Mechanics',
    title: 'No Curiosity Gap — Nothing Pulls Viewers Forward',
    description: 'The opening provides information but doesn\'t create an open loop. The medial prefrontal cortex needs an unanswered question to stay engaged. Without a curiosity gap, viewers have no reason to continue beyond the hook.',
    suggestion: 'In the first 3 seconds, create an information gap: start with the ending ("Here\'s what happens when...") then rewind to the beginning. Or ask a question the viewer needs answered and tease that the answer is coming. The Zeigarnik effect means the brain obsesses over incomplete information — use this to pull viewers through the entire video. "Watch what happens when..." is the most effective opening pattern.',
    triggers: [{ signal: 'dopamine_signal', condition: 'low', threshold: 0.42 }],
    target_regions: ['frontal', 'stem', 'temp'],
    base_severity: 'critical',
    impact_range: [0.12, 0.28]
  },
  {
    id: 'intro-slow-warmup',
    category: 'Intro/Outro Mechanics',
    title: 'Slow Warm-Up — 50% of Viewers Gone Before Payoff',
    description: 'The content gets better over time but the algorithm never sees it because viewers leave during the slow opening. TikTok data shows 65% of viewers decide within 1 second.',
    suggestion: 'Front-load the single most compelling moment from the video into the first 2 seconds as a teaser, then cut to the actual beginning. This "temporal re-ordering" gives the brain a promise of future reward immediately. Even if the content naturally builds slowly, the teaser frame keeps viewers watching through the setup.',
    triggers: [{ signal: 'temporal_signal', condition: 'declining', threshold: 0.25 }, { signal: 'attention_signal', condition: 'low', threshold: 0.40 }],
    target_regions: ['frontal', 'occipit'],
    base_severity: 'critical',
    impact_range: [0.15, 0.30]
  },
  {
    id: 'outro-no-zeigarnik',
    category: 'Intro/Outro Mechanics',
    title: 'Resolved Ending — No Zeigarnik Effect Triggered',
    description: 'The video ends conclusively (fade to black, "thanks for watching," end card). The brain marks the content as "complete" and files it away — no reason to rewatch or think about it after viewing.',
    suggestion: 'Cut the traditional outro entirely. End on a sudden, unresolved moment: a question without an answer, a visual that creates more questions, or a "wait, what?" frame that makes viewers rewind. The last frame should connect back to the first frame to create a loop. Unresolved endings have 40% stronger memory encoding and 2.5x more replays. Content that loops perfectly is TikTok\'s highest distribution signal.',
    triggers: [{ signal: 'memory_signal', condition: 'low', threshold: 0.38 }],
    target_regions: ['temp', 'frontal', 'pariet'],
    base_severity: 'moderate',
    impact_range: [0.10, 0.25]
  },
  {
    id: 'outro-weak-cta-memory',
    category: 'Intro/Outro Mechanics',
    title: 'CTA Not Encoded — Viewer Won\'t Remember to Act',
    description: 'The call-to-action is presented but not encoded into memory. The hippocampus shows low activity during the final moments — without hippocampal encoding, the CTA is forgotten within 30 seconds.',
    suggestion: 'Present the CTA visually (on-screen text) AND verbally at the same moment — dual-coding theory shows this doubles hippocampal encoding probability. Use a distinctive visual motif or sound for the CTA that doesn\'t appear anywhere else in the video. The brain encodes unique sensory events more strongly. Keep CTA text on screen for 3+ seconds minimum.',
    triggers: [{ signal: 'memory_signal', condition: 'declining', threshold: 0.35 }],
    target_regions: ['frontal', 'temp', 'pariet'],
    base_severity: 'moderate',
    impact_range: [0.07, 0.18]
  },
  {
    id: 'outro-energy-collapse',
    category: 'Intro/Outro Mechanics',
    title: 'Outro Energy Collapse — Peak-End Rule Violated',
    description: 'Energy drops significantly in the final 10 seconds. The peak-end rule means viewers judge the entire experience by its most intense moment and its ending — a weak ending retroactively lowers the entire video\'s perceived quality.',
    suggestion: 'The final 5 seconds must be the second most neurologically intense moment after the hook. Structure the ending as a "mini-climax": summarize the key takeaway with intensity, then deliver a final punch (a surprising statistic, an emotional callback, or a direct challenge). Never let the energy fade — if you must fade, add a text overlay that creates an open loop.',
    triggers: [{ signal: 'temporal_signal', condition: 'declining', threshold: 0.30 }],
    target_regions: ['frontal', 'temp', 'pariet'],
    base_severity: 'moderate',
    impact_range: [0.08, 0.22]
  }
];

// ================================================================
// REGION METADATA
// ================================================================

const REGION_DISPLAY_NAMES: Record<string, string> = {
  frontal: 'Frontal Lobe',
  temp: 'Temporal Lobe',
  pariet: 'Parietal Lobe',
  occipit: 'Occipital Lobe',
  cereb: 'Cerebellum',
  corpus: 'Corpus Callosum',
  stem: 'Brain Stem',
  pitua: 'Pituitary Gland'
};

// ================================================================
// CONTENT PROFILER
// Extracts a fixed-length feature vector from analysis results
// (Inspired by YouTube's user embedding from watch history)
// ================================================================

function buildContentProfile(result: AnalysisResult): ContentProfile {
  const { brain_scores, engagement_curve, timestamp_axis, duration_sec, overall_grade } = result;
  const att = brain_scores.attention;
  const dop = brain_scores.dopamine;
  const mem = brain_scores.memory;

  // Attention stats
  const attScores = att.temporal_scores.length > 0 ? att.temporal_scores : [att.overall];
  const attMean = mean(attScores);
  const attVar = variance(attScores, attMean);
  const attDropoffs = att.dropoff_moments?.length ?? 0;
  const attPeaks = att.peak_moments?.length ?? 0;

  // Dopamine stats
  const dopScores = dop.temporal_scores.length > 0 ? dop.temporal_scores : [dop.overall];
  const dopMean = mean(dopScores);
  const dopVar = variance(dopScores, dopMean);
  const dopGapScore = dopScores.length > 1 ? computeGapScore(dopScores) : 1 - dop.overall;

  // Memory stats
  const memScores = mem.temporal_scores.length > 0 ? mem.temporal_scores : [mem.overall];
  const memMean = mean(memScores);
  const memDepth = computeEncodingDepth(memScores);

  // Engagement curve stats
  const engCurve = engagement_curve.length > 0 ? engagement_curve : [att.overall];
  const engTrend = computeTrend(engCurve);
  const engVolatility = computeVolatility(engCurve);

  // Pacing from scene breaks or engagement variance
  const pacingScore = result.scene_breaks
    ? Math.min(1, (result.scene_breaks.length / Math.max(1, duration_sec)) * 10)
    : engVolatility * 0.8;

  // Grade to numeric
  const gradeMap: Record<string, number> = {
    'A+': 0.97, 'A': 0.93, 'A-': 0.90, 'B+': 0.87, 'B': 0.83, 'B-': 0.80,
    'C+': 0.77, 'C': 0.73, 'C-': 0.70, 'D+': 0.67, 'D': 0.63, 'D-': 0.60, 'F': 0.50
  };
  const gradeNum = gradeMap[overall_grade] ?? 0.70;

  return {
    attention_mean: attMean,
    attention_variance: attVar,
    attention_dropoff_count: attDropoffs,
    attention_peak_count: attPeaks,
    dopamine_mean: dopMean,
    dopamine_variance: dopVar,
    dopamine_gap_score: dopGapScore,
    memory_mean: memMean,
    memory_encoding_depth: memDepth,
    engagement_trend: engTrend,
    engagement_volatility: engVolatility,
    pacing_score: pacingScore,
    duration_sec,
    overall_grade_numeric: gradeNum
  };
}

// ================================================================
// STAGE 1: CANDIDATE GENERATION
// Score each template against the content profile
// ================================================================

function generateCandidates(
  profile: ContentProfile,
  result: AnalysisResult
): { template: CandidateTemplate; relevance: number; timestamp: number }[] {
  const signals = computeSignals(profile);
  const candidates: { template: CandidateTemplate; relevance: number; timestamp: number }[] = [];

  for (const tmpl of RECOMMENDATION_CATALOG) {
    let relevance = 0;
    let triggerCount = 0;

    for (const trigger of tmpl.triggers) {
      const signalValue = signals[trigger.signal];
      let triggered = false;

      switch (trigger.condition) {
        case 'low':
          if (signalValue < trigger.threshold) {
            relevance += (trigger.threshold - signalValue) / trigger.threshold;
            triggered = true;
          }
          break;
        case 'high':
          if (signalValue > trigger.threshold) {
            relevance += (signalValue - trigger.threshold) / (1 - trigger.threshold);
            triggered = true;
          }
          break;
        case 'volatile':
          if (profile.engagement_volatility > trigger.threshold) {
            relevance += profile.engagement_volatility;
            triggered = true;
          }
          break;
        case 'declining':
          if (profile.engagement_trend < -trigger.threshold) {
            relevance += Math.abs(profile.engagement_trend);
            triggered = true;
          }
          break;
      }

      if (triggered) triggerCount++;
    }

    // Must match at least one trigger
    if (triggerCount === 0) continue;

    // Normalize relevance by trigger count
    relevance = relevance / tmpl.triggers.length;

    // Boost for multiple trigger matches
    if (triggerCount > 1) relevance *= 1 + (triggerCount - 1) * 0.3;

    // Find best timestamp for this recommendation
    const timestamp = findBestTimestamp(tmpl, result, profile);

    candidates.push({ template: tmpl, relevance, timestamp });
  }

  return candidates;
}

// ================================================================
// STAGE 2: PRECISION RANKING
// Multi-signal fusion + Thompson sampling
// ================================================================

function rankCandidates(
  candidates: { template: CandidateTemplate; relevance: number; timestamp: number }[],
  profile: ContentProfile,
  result: AnalysisResult
): RankedRecommendation[] {
  const signals = computeSignals(profile);
  const ranked: RankedRecommendation[] = [];

  for (const candidate of candidates) {
    const { template, relevance, timestamp } = candidate;

    // ── Multi-signal fusion score ──
    // Inspired by TikTok's real-time feature combination
    const severityWeight = template.base_severity === 'critical' ? 1.5 :
                           template.base_severity === 'moderate' ? 1.0 : 0.7;

    const signalBreakdown: SignalBreakdown = {
      attention_signal: signals.attention_signal,
      dopamine_signal: signals.dopamine_signal,
      memory_signal: signals.memory_signal,
      temporal_signal: signals.temporal_signal,
      pacing_signal: signals.pacing_signal
    };

    // Watch-time-inspired weighting: deeper engagement signals → higher weight
    const fusionScore = (
      relevance * 0.35 +
      (1 - signals.attention_signal) * 0.20 +
      (1 - signals.dopamine_signal) * 0.20 +
      (1 - signals.memory_signal) * 0.15 +
      Math.abs(signals.temporal_signal - 0.5) * 0.10
    ) * severityWeight;

    // ── Thompson sampling for exploration ──
    // Add controlled randomness to prevent always showing the same recs
    const alpha = 2 + fusionScore * 8;  // successes
    const beta = 2 + (1 - fusionScore) * 8;  // failures
    const thompsonSample = betaSample(alpha, beta);
    const confidence = fusionScore;

    // ── Expected impact ──
    const [minImpact, maxImpact] = template.impact_range;
    const impactLerp = Math.min(1, relevance * 1.5);
    const neural_impact_score = minImpact + (maxImpact - minImpact) * impactLerp;

    // ── Affected regions ──
    const affected_regions = resolveAffectedRegions(template, result);

    // ── "Why this" explanation ──
    const why = generateWhyExplanation(template, profile, signals);

    // ── Final ranking score (Thompson-adjusted) ──
    const rankScore = fusionScore * 0.7 + thompsonSample * 0.3;

    // Determine final severity based on actual signal data
    const finalSeverity = fusionScore > 0.7 ? 'critical' :
                          fusionScore > 0.4 ? 'moderate' : 'suggestion';

    ranked.push({
      rank: 0, // filled after sort
      timestamp_sec: timestamp,
      severity: finalSeverity,
      category: template.category,
      title: template.title,
      description: template.description,
      suggestion: template.suggestion,
      expected_impact: neural_impact_score,
      confidence,
      neural_impact_score,
      affected_regions,
      signal_breakdown: signalBreakdown,
      why,
      _rankScore: rankScore // internal, stripped later
    } as RankedRecommendation & { _rankScore: number });
  }

  // Sort by rank score descending
  ranked.sort((a, b) => (b as any)._rankScore - (a as any)._rankScore);

  // Deduplicate by category (keep top 2 per category max)
  const categoryCounts = new Map<string, number>();
  const deduped: RankedRecommendation[] = [];
  for (const rec of ranked) {
    const count = categoryCounts.get(rec.category) ?? 0;
    if (count >= 2) continue;
    categoryCounts.set(rec.category, count + 1);
    rec.rank = deduped.length + 1;
    delete (rec as any)._rankScore;
    deduped.push(rec);
  }

  return deduped;
}

// ================================================================
// PUBLIC API
// ================================================================

export function generateRecommendations(result: AnalysisResult): RankedRecommendation[] {
  const profile = buildContentProfile(result);
  const candidates = generateCandidates(profile, result);
  const ranked = rankCandidates(candidates, profile, result);
  
  // Return top 12 recommendations max
  return ranked.slice(0, 12);
}

export function getContentProfile(result: AnalysisResult): ContentProfile {
  return buildContentProfile(result);
}

// ================================================================
// HELPERS
// ================================================================

function computeSignals(profile: ContentProfile): SignalBreakdown {
  return {
    attention_signal: profile.attention_mean,
    dopamine_signal: profile.dopamine_mean,
    memory_signal: profile.memory_mean,
    temporal_signal: profile.engagement_trend > 0 ? 0.5 + profile.engagement_trend : 0.5 + profile.engagement_trend,
    pacing_signal: profile.pacing_score
  };
}

function findBestTimestamp(
  template: CandidateTemplate,
  result: AnalysisResult,
  profile: ContentProfile
): number {
  const { engagement_curve, timestamp_axis, duration_sec } = result;
  if (!engagement_curve.length || !timestamp_axis.length) return 0;

  // For hook-related recs, always timestamp at start
  if (template.category === 'Hook') return 0;

  // For ending-related recs, timestamp near end
  if (template.id.includes('ending') || template.id.includes('weak-ending')) {
    return duration_sec * 0.85;
  }

  // For engagement curve recs, find the worst point
  if (template.category === 'Engagement Curve' || template.category === 'Pacing') {
    let worstIdx = 0;
    let worstVal = 1;
    for (let i = 0; i < engagement_curve.length; i++) {
      if (engagement_curve[i] < worstVal) {
        worstVal = engagement_curve[i];
        worstIdx = i;
      }
    }
    return timestamp_axis[worstIdx] ?? (worstIdx / engagement_curve.length) * duration_sec;
  }

  // For dropoff-related, find biggest dropoff
  const dropoffs = result.brain_scores.attention.dropoff_moments ?? [];
  if (dropoffs.length > 0) {
    const worst = dropoffs.reduce((a, b) =>
      (a.value_before - a.value_after) > (b.value_before - b.value_after) ? a : b
    );
    return worst.timestamp;
  }

  // Default: midpoint of content
  return duration_sec * 0.5;
}

function resolveAffectedRegions(
  template: CandidateTemplate,
  result: AnalysisResult
): AffectedRegion[] {
  const regions: AffectedRegion[] = [];
  const roiData = {
    ...result.brain_scores.attention.roi_breakdown,
    ...result.brain_scores.dopamine.roi_breakdown,
    ...result.brain_scores.memory.roi_breakdown
  };

  for (let i = 0; i < template.target_regions.length; i++) {
    const key = template.target_regions[i];
    regions.push({
      key,
      name: REGION_DISPLAY_NAMES[key] ?? key,
      activation: roiData[key] ?? 0.5,
      impact: i === 0 ? 'primary' : 'secondary'
    });
  }
  return regions;
}

function generateWhyExplanation(
  template: CandidateTemplate,
  profile: ContentProfile,
  signals: SignalBreakdown
): string {
  const parts: string[] = [];

  for (const trigger of template.triggers) {
    const val = signals[trigger.signal];
    const label = trigger.signal.replace('_signal', '').replace('_', ' ');

    switch (trigger.condition) {
      case 'low':
        parts.push(`${label} is at ${(val * 100).toFixed(0)}% (below ${(trigger.threshold * 100).toFixed(0)}% threshold)`);
        break;
      case 'high':
        parts.push(`${label} is elevated at ${(val * 100).toFixed(0)}% (above ${(trigger.threshold * 100).toFixed(0)}% threshold)`);
        break;
      case 'declining':
        parts.push(`${label} trend is declining (${(profile.engagement_trend * 100).toFixed(0)}% slope)`);
        break;
      case 'volatile':
        parts.push(`${label} volatility is high (${(profile.engagement_volatility * 100).toFixed(0)}%)`);
        break;
    }
  }

  return parts.join('. ') + '.';
}

// ── Math utilities ──

function mean(arr: number[]): number {
  if (arr.length === 0) return 0;
  return arr.reduce((s, v) => s + v, 0) / arr.length;
}

function variance(arr: number[], m: number): number {
  if (arr.length < 2) return 0;
  return arr.reduce((s, v) => s + (v - m) ** 2, 0) / arr.length;
}

function computeGapScore(scores: number[]): number {
  if (scores.length < 2) return 0.5;
  let maxGap = 0;
  for (let i = 1; i < scores.length; i++) {
    const gap = Math.abs(scores[i] - scores[i - 1]);
    if (gap > maxGap) maxGap = gap;
  }
  return maxGap;
}

function computeEncodingDepth(scores: number[]): number {
  if (scores.length < 2) return scores[0] ?? 0.5;
  // Sustained high scores = deeper encoding
  const highCount = scores.filter(s => s > 0.6).length;
  return highCount / scores.length;
}

function computeTrend(curve: number[]): number {
  if (curve.length < 3) return 0;
  const firstThird = mean(curve.slice(0, Math.floor(curve.length / 3)));
  const lastThird = mean(curve.slice(Math.floor(curve.length * 2 / 3)));
  return lastThird - firstThird; // positive = growing, negative = declining
}

function computeVolatility(curve: number[]): number {
  if (curve.length < 3) return 0;
  let totalChange = 0;
  for (let i = 1; i < curve.length; i++) {
    totalChange += Math.abs(curve[i] - curve[i - 1]);
  }
  return Math.min(1, totalChange / curve.length);
}

function betaSample(alpha: number, beta: number): number {
  // Simplified Beta distribution sampling using Gamma approximation
  const x = gammaSample(alpha);
  const y = gammaSample(beta);
  return x / (x + y);
}

function gammaSample(shape: number): number {
  // Marsaglia and Tsang's method for shape >= 1
  if (shape < 1) return gammaSample(shape + 1) * Math.pow(Math.random(), 1 / shape);
  const d = shape - 1 / 3;
  const c = 1 / Math.sqrt(9 * d);
  while (true) {
    let x: number, v: number;
    do {
      x = randn();
      v = 1 + c * x;
    } while (v <= 0);
    v = v * v * v;
    const u = Math.random();
    if (u < 1 - 0.0331 * (x * x) * (x * x)) return d * v;
    if (Math.log(u) < 0.5 * x * x + d * (1 - v + Math.log(v))) return d * v;
  }
}

function randn(): number {
  // Box-Muller transform
  const u1 = Math.random();
  const u2 = Math.random();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}
