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

export interface MatchResponse {
  id: number;
  job_id: number;
  overall_score: number;
  score_breakdown: Record<string, number>;
  reasoning: string;
  strengths: string[];
  missing_skills: string[];
  interview_talking_points: string[];
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
}

export interface ResumeUploadResponse {
  message: string;
  character_count: number;
}
