/** API response types matching the backend Pydantic schemas. */

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface JobResponse {
  id: number;
  external_id: string;
  source: string;
  title: string;
  company: string;
  location: string | null;
  workplace_type: string | null;
  description: string;
  requirements: string | null;
  salary_min: number | null;
  salary_max: number | null;
  salary_currency: string | null;
  employment_type: string | null;
  experience_level: string | null;
  apply_url: string | null;
  created_at: string | null;
}

export interface RequirementMatch {
  requirement: string;
  category: string;
  met: boolean;
  evidence: string;
  confidence: number;
}

export interface ATSKeywordScore {
  score: number;
  matched_keywords: string[];
  missing_keywords: string[];
  total_job_keywords: number;
  technical_match_pct: number;
  soft_skill_match_pct: number;
}

export interface MatchResponse {
  id: number;
  job_id: number;
  overall_score: number;
  score_breakdown: Record<string, number>;
  reasoning: string;
  strengths: string[];
  missing_skills: string[];
  interview_talking_points: string[];
  ats_score: number | null;
  ats_details: ATSKeywordScore | null;
  requirement_matches: RequirementMatch[] | null;
  requirements_met_ratio: number | null;
  integrated_score: number | null;
  job: JobResponse | null;
  created_at: string | null;
}

export interface TaskStatusResponse {
  task_id: string;
  status: string;
  result: Record<string, unknown> | null;
}

export interface AgentStatusMessage {
  step: string;
  status: string;
  progress: number;
  message: string;
  fields_filled: Record<string, string> | null;
  screenshot_b64: string | null;
}

export interface PreferencesResponse {
  job_titles: string[];
  locations: string[];
  salary_min: number | null;
  salary_max: number | null;
  workplace_types: string[];
  experience_level: string;
  weights: Record<string, number>;
  employment_types: string[];
  date_posted: string;
  salary_currency: string;
  final_results_count: number;
  num_pages_per_source: number;
  enabled_sources: string[];
  greenhouse_board_tokens: string[];
  lever_companies: string[];
  workday_urls: string[];
  anthropic_base_url: string;
  excluded_locations: string[];
  // Chinese pipeline settings
  ats_mode: 'auto' | 'skip' | 'llm';
  reranker_mode: 'auto' | 'bge' | 'flashrank' | 'flashrank-multilingual';
  embedding_model_choice: 'gemini' | 'bge-m3';
  recruitment_type: 'social' | 'campus' | 'both';
  graduation_year: number | null;
  mokahr_org_ids: string[];
  alibaba_app_key: string;
  boss_zhipin_cookie: string;
}

export interface ResumeUploadResponse {
  message: string;
  character_count: number;
}

// ---------------------------------------------------------------------------
// Resume Generator (external microservice)
// ---------------------------------------------------------------------------

export interface ResumeGenerateRequest {
  match_id: number;
  generate_cover_letter?: boolean;
  template_id?: string | null;
  language?: string;
  experience_level?: string;
  provider?: string;
}

export interface ResumeGenerateResponse {
  id: number;
  match_id: number;
  external_task_id: string;
  status: string;
  created_at: string | null;
}

export interface ResumeStatusResponse {
  id: number;
  match_id: number;
  external_task_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  resume_pdf_path: string | null;
  cover_letter_pdf_path: string | null;
  cover_letter_text: string | null;
  error_message: string | null;
  language: string;
  provider: string;
  created_at: string | null;
  updated_at: string | null;
}

export interface ResumeGeneratorHealthResponse {
  available: boolean;
  detail: string;
}

// ---------------------------------------------------------------------------
// Skill Market Analysis
// ---------------------------------------------------------------------------

export interface SkillFrequencyResponse {
  skill_name: string;
  category: string;
  count: number;
  percentage: number;
}

export interface SkillCoOccurrenceResponse {
  skill_a: string;
  skill_b: string;
  co_count: number;
  percentage: number;
}

export interface TitleGroupResponse {
  title: string;
  job_count: number;
}

export interface SkillMarketReportResponse {
  title_pattern: string;
  total_jobs: number;
  top_skills: SkillFrequencyResponse[];
  technical_skills: SkillFrequencyResponse[];
  soft_skills: SkillFrequencyResponse[];
  co_occurrences: SkillCoOccurrenceResponse[];
  category_breakdown: Record<string, number>;
}
