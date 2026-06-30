export interface User {
  id: number;
  email: string;
  name: string;
  role: 'free' | 'starter' | 'pro' | 'agency' | 'admin';
  token_balance: number;
  total_tokens_purchased: number;
  total_tokens_used: number;
  is_active: boolean;
  created_at: string | null;
}

export interface AuthResponse {
  success: boolean;
  token?: string;
  user?: User;
  error?: string;
}

export interface TokenPackage {
  id: number;
  name: string;
  tokens: number;
  price_cents: number;
  price_display: string;
  popular: boolean;
  description: string | null;
}

export interface BrainScores {
  attention: DimensionScore;
  dopamine: DimensionScore;
  memory: DimensionScore;
}

export interface DimensionScore {
  overall: number;
  temporal_scores: number[];
  peak_moments: PeakMoment[];
  dropoff_moments: DropoffMoment[];
  roi_breakdown: Record<string, number>;
  label: string;
}

export interface PeakMoment {
  index: number;
  value: number;
  timestamp: number;
}

export interface DropoffMoment {
  index: number;
  value_before: number;
  value_after: number;
  timestamp: number;
}

export interface Recommendation {
  timestamp_sec: number;
  severity: 'critical' | 'moderate' | 'suggestion';
  category: string;
  title: string;
  description: string;
  suggestion: string;
  expected_impact: number;
}

export interface TargetAudience {
  predicted_age_group: string;
  age_key: string;
  psychological_profile: string;
  profile_description: string;
  needs: string[];
  avoids: string[];
  platform_affinity: {
    primary_platform: string;
    primary_fit_score: number;
    primary_reasoning: string;
    secondary_platform: string;
    secondary_fit_score: number;
    secondary_reasoning: string;
  };
  behavioral_triggers: {
    optimal_hook_window_sec: number;
    scene_change_rate_target: number;
    dopamine_peak_interval_sec: number;
  };
}

export interface AudienceProfile {
  primary_audience: {
    age_group: string;
    interest_category: string;
    geographic_affinity: string;
    confidence: number;
  };
  target_audience?: TargetAudience;
  age_breakdown: Record<string, { score: number; label: string }>;
  top_interests: { key: string; label: string; score: number }[];
  geographic_affinities: Record<string, { score: number; label: string }>;
  neural_signature: {
    attention_decay_rate: number;
    dopamine_peak_latency_sec: number;
    scene_change_rate: number;
    engagement_variance: number;
    early_engagement_score: number;
    final_memory_encoding_score: number;
    engagement_momentum: 'rising' | 'declining' | 'neutral';
    pacing_profile: 'ultra_fast' | 'fast' | 'moderate' | 'slow';
  };
  optimal_content_length_sec: {
    current_duration_sec: number;
    recommended_duration_sec: number;
    verdict: 'optimal' | 'too_long' | 'too_short';
    reasoning: string;
  };
  competitive_benchmark: {
    estimated_competitive_difficulty: string;
    content_uniqueness_score: number;
  };
}

export interface OptimizationSuggestion {
  priority?: string;
  area?: string;
  suggestion: string;
  expected_impact?: number;
}

export interface OptimizationCategory {
  verdict: string;
  recommendations?: OptimizationSuggestion[];
  suggestions?: OptimizationSuggestion[];
  dropoff_points?: {
    timestamp_sec: number;
    severity: string;
    value_before: number;
    value_after: number;
    drop_magnitude: number;
    related_recommendation?: string;
  }[];
  pattern?: string;
  total_dropoffs?: number;
  average_visual_engagement?: number;
  average_audio_engagement?: number;
  peak_emotional_moment_sec?: number;
  valley_moment_sec?: number;
}

export interface NeuroSurgicalDirective {
  domain: string;
  diagnosis: string;
  prescription: string;
  expected_impact: number;
}

export interface NeuroSurgicalCategory {
  verdict: string;
  diagnosis?: string;
  visual_cortex_activation?: number;
  facial_engagement_score?: number;
  auditory_cortex_activation?: number;
  directives: NeuroSurgicalDirective[];
  intro_directives?: NeuroSurgicalDirective[];
  outro_directives?: NeuroSurgicalDirective[];
}

export interface ContentOptimization {
  intro_optimization: OptimizationCategory;
  pacing_recommendations: OptimizationCategory;
  visual_optimization: OptimizationCategory;
  audio_optimization: OptimizationCategory;
  emotional_arc_recommendations: OptimizationCategory;
  memory_encoding_optimization: OptimizationCategory;
  dropoff_analysis: OptimizationCategory & { dropoff_points: any[]; pattern: string; total_dropoffs: number };
  outro_optimization: OptimizationCategory;
  hook_strategy: {
    recommended_hook_type: string;
    hook_description: string;
    optimal_hook_window_sec: number;
  };
  color_lighting_directives?: NeuroSurgicalCategory;
  camera_angle_directives?: NeuroSurgicalCategory;
  audio_pacing_directives?: NeuroSurgicalCategory;
  intro_outro_mechanics?: NeuroSurgicalCategory;
}

export interface AnalysisResult {
  id: string;
  filename: string;
  media_type: 'video' | 'audio' | 'text';
  duration_sec: number;
  brain_scores: BrainScores;
  recommendations: Recommendation[];
  engagement_curve: number[];
  timestamp_axis: number[];
  created_at: string;
  summary: string;
  overall_grade: string;
  scene_breaks?: number[];
  keyframes?: { timestamp: number; saliency_score: number }[];
  transcript_segments?: { start: number; end: number; text: string; attention_score: number }[];
  word_level_scores?: WordScore[];
  sentence_breakdown?: SentenceScore[];
  emotion_timeline?: EmotionTimeline;
  brain_viz_urls?: Record<string, string>;
  audience_profile?: AudienceProfile;
  content_optimization?: ContentOptimization;
  copyright_analysis?: CopyrightResult;
  content_identity?: ContentIdentity;
  tokens_used?: number;
  token_balance_after?: number;
}

export interface WordScore {
  word: string;
  timestamp: number;
  attention: number;
  dopamine: number;
  memory: number;
}

export interface SentenceScore {
  text: string;
  word_count: number;
  avg_attention: number;
  avg_dopamine: number;
  avg_memory: number;
  start_word: number;
  end_word: number;
}

export interface CopyrightResult {
  overall_risk: 'low' | 'moderate' | 'high' | 'critical';
  risk_score: number;
  analysis_type: 'video' | 'audio' | 'text';
  audio_duplicate_score: number;
  visual_duplicate_score: number;
  music_probability: number;
  derivative_detected: boolean;
  derivative_details: string | null;
  watermark_detected: boolean;
  watermark_details: string | null;
  findings: CopyrightFinding[];
  fingerprint_matches: FingerprintMatch[];
}

export interface CopyrightFinding {
  type: 'audio_duplicate' | 'visual_duplicate' | 'music' | 'derivative' | 'watermark' | 'metadata';
  severity: 'critical' | 'moderate' | 'suggestion';
  timestamp_sec: number | null;
  title: string;
  description: string;
  details: string;
  evidence: Record<string, unknown> | null;
}

export interface FingerprintMatch {
  source: string;
  confidence: number;
  match_type: 'audio' | 'visual' | 'melody';
  timestamp_sec: number | null;
  duration_sec: number | null;
  details: string;
}

export interface FrameSignature {
  index: number;
  timestamp_sec: number;
  perceptual_hash: string;
  dino_embedding: number[] | null;
  scene_boundary: boolean;
  similarity_to_reference: number | null;
}

export interface TemporalMatchSegment {
  start_frame: number;
  end_frame: number;
  start_sec: number;
  end_sec: number;
  match_confidence: number;
  match_type: 'exact' | 'near_duplicate' | 'modified' | 'reordered';
  reference_segment: {
    start_sec: number;
    end_sec: number;
    analysis_id: string;
    filename: string;
  } | null;
}

export interface FrameAlignmentResult {
  alignment_score: number;
  offset_frames: number;
  matched_frame_count: number;
  total_frame_count: number;
  coverage_ratio: number;
  longest_match_segment_sec: number;
  reordered_segments: number;
}

export interface ContentIdentity {
  is_known_content: boolean;
  match_type: 'exact' | 'perceptual' | 'derivative' | 'reordered' | 'partial' | 'new';
  confidence: number;
  fingerprint_hash: string;
  first_seen_at: string | null;
  first_analysis_id: string | null;
  first_analysis_grade: string | null;
  first_filename: string | null;
  previous_scores: {
    attention: number;
    dopamine: number;
    memory: number;
    overall_grade: string;
  } | null;
  score_changes: {
    attention_delta: number;
    dopamine_delta: number;
    memory_delta: number;
  } | null;
  match_details: string;

  /** Frame-by-frame signatures extracted from the video */
  frame_signatures: FrameSignature[];
  /** Temporal segments that matched against the reference */
  temporal_matches: TemporalMatchSegment[];
  /** Frame sampling interval used (e.g. 0.5 = 2 fps, 1.0 = 1 fps) */
  frame_sample_interval_sec: number;
  /** Overall ratio of matching frames to total frames */
  temporal_match_coverage: number;
  /** Full sequence alignment result */
  alignment: FrameAlignmentResult | null;
}

export interface EmotionTimeline {
  dimensions: string[];
  timestamps: number[];
  scores: Record<string, number[]>;
  labels: Record<string, string[]>;
  events: EmotionalEvent[];
}

export interface EmotionalEvent {
  timestamp: number;
  type: string;
  severity: string;
  description: string;
}

export interface ABTestResult {
  id: string;
  variants: AnalysisResult[];
  winning_variant: string | null;
  dimension_comparison: Record<string, number[]>;
  significance_scores: Record<string, number>;
  recommendation: string;
}

export interface CopyVariant {
  id: string;
  name: string;
  content: string;
  framing_type: string;
  brain_scores: BrainScores | null;
}

export interface CopyAnalysisResult {
  original: CopyVariant;
  variants: CopyVariant[];
  comparison: Record<string, unknown>;
  winning_variant: string | null;
  recommendations: string[];
}

export interface ThumbnailResult {
  model_key: string;
  model_name: string;
  image_url: string;
  thumbnail_url: string;
  neural_scores: {
    attention: number;
    dopamine: number;
    memory: number;
    overall: number;
  };
  generation_time_ms: number;
  error_message?: string;
}

export interface ThumbnailHistoryItem {
  id: number;
  prompt: string;
  models_used: string[];
  engagement_forecast: number | null;
  tokens_used: number;
  created_at: string;
  results_count: number;
  results?: ThumbnailResult[];
}

export interface Transaction {
  id: number;
  type: string;
  amount: number;
  balance_after: number;
  description: string;
  created_at: string;
}

export interface AnalysisHistoryItem {
  id: string;
  media_type: string;
  filename: string;
  overall_grade: string;
  attention_score: number;
  dopamine_score: number;
  memory_score: number;
  duration_sec: number;
  tokens_used: number;
  created_at: string;
  results?: AnalysisResult;
}

export interface AnalysisResponse {
  success: boolean;
  data?: AnalysisResult;
  error?: string;
}

export interface BatchAnalysisResponse {
  success: boolean;
  data?: unknown[];
  error?: string;
}

export interface ChannelProfile {
  platform: 'youtube' | 'tiktok';
  channel_id: string;
  channel_name: string;
  description: string;
  subscriber_count: number;
  video_count: number;
  country: string | null;
  niche: string;
  niche_confidence: number;
  avatar_url: string | null;
  banner_url: string | null;
  recent_tags: string[];
  engagement_rate: number | null;
  inferred_audience: Record<string, unknown>;
  source_url: string;
}

export interface ChannelLinkResponse {
  success: boolean;
  profile?: ChannelProfile;
  error?: string;
}

export interface APIError {
  success: false;
  error: string;
}
