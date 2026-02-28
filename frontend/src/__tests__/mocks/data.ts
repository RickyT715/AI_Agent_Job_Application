/** Mock data factories for tests. */

import type { JobResponse, MatchResponse, PreferencesResponse } from "../../types/api";

export function makeJob(overrides: Partial<JobResponse> = {}): JobResponse {
  return {
    id: 1,
    external_id: "ext-001",
    source: "test",
    title: "Software Engineer",
    company: "TestCo",
    location: "Remote",
    workplace_type: "remote",
    description: "Build great software.",
    requirements: "Python, TypeScript",
    salary_min: 100000,
    salary_max: 150000,
    salary_currency: "USD",
    employment_type: "full_time",
    experience_level: "mid",
    apply_url: "https://example.com/apply",
    created_at: "2024-01-15T10:00:00Z",
    ...overrides,
  };
}

export function makeMatch(overrides: Partial<MatchResponse> = {}): MatchResponse {
  return {
    id: 1,
    job_id: 1,
    overall_score: 8.5,
    score_breakdown: {
      skills: 9,
      experience: 8,
      education: 7,
      location: 9,
      salary: 8,
    },
    reasoning: "Strong match due to Python and FastAPI experience.",
    strengths: ["Python expertise", "FastAPI experience", "Cloud knowledge"],
    missing_skills: ["Kubernetes", "Go"],
    interview_talking_points: ["Discuss ML pipeline work", "System design experience"],
    job: makeJob(),
    created_at: "2024-01-15T12:00:00Z",
    ...overrides,
  };
}

export function makeMatches(count: number): MatchResponse[] {
  return Array.from({ length: count }, (_, i) =>
    makeMatch({
      id: i + 1,
      job_id: i + 1,
      overall_score: 10 - i,
      job: makeJob({ id: i + 1, title: `Engineer ${i + 1}`, company: `Company ${i + 1}` }),
    }),
  );
}

export function makePreferences(): PreferencesResponse {
  return {
    job_titles: ["Software Engineer", "Backend Developer"],
    locations: ["Remote", "NYC"],
    salary_min: 100000,
    salary_max: 180000,
    workplace_types: ["remote", "hybrid"],
    experience_level: "mid",
    weights: { skills: 0.3, experience: 0.25, education: 0.15, location: 0.15, salary: 0.15 },
    employment_types: ["FULLTIME"],
    date_posted: "month",
    salary_currency: "USD",
    final_results_count: 10,
    num_pages_per_source: 1,
    enabled_sources: ["jsearch"],
    greenhouse_board_tokens: [],
    lever_companies: [],
    workday_urls: [],
    anthropic_base_url: "",
  };
}
