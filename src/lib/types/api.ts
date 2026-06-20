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

export interface APIError {
  success: false;
  error: string;
}
