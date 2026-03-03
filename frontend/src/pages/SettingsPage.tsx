import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";
import { PreferencesForm } from "../components/PreferencesForm";
import type { PreferencesResponse } from "../types/api";

const DEFAULT_PREFERENCES: PreferencesResponse = {
  job_titles: ["Software Engineer"],
  locations: ["Remote"],
  salary_min: null,
  salary_max: null,
  workplace_types: ["remote", "hybrid"],
  experience_level: "mid",
  weights: { skills: 0.30, experience: 0.25, education: 0.15, location: 0.15, salary: 0.15 },
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
  excluded_locations: [],
  ats_mode: "auto",
  reranker_mode: "auto",
  embedding_model_choice: "gemini",
  recruitment_type: "social",
  graduation_year: null,
  mokahr_org_ids: [],
  alibaba_app_key: "",
  boss_zhipin_cookie: "",
};

export function SettingsPage() {
  const queryClient = useQueryClient();

  const { data: preferences, isLoading } = useQuery({
    queryKey: ["preferences"],
    queryFn: () => api.get<PreferencesResponse>("/config/preferences"),
  });

  const updateMutation = useMutation({
    mutationFn: (updates: Partial<PreferencesResponse>) =>
      api.put<PreferencesResponse>("/config/preferences", updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["preferences"] });
    },
  });

  if (isLoading) return <p>Loading preferences...</p>;

  return (
    <div className="settings-page">
      <div className="page-header">
        <h1>Settings</h1>
        <p>Configure your job search preferences and matching criteria</p>
      </div>
      <PreferencesForm
        preferences={preferences ?? DEFAULT_PREFERENCES}
        onSave={(updated) => updateMutation.mutate(updated)}
      />
      {updateMutation.isSuccess && (
        <p className="save-confirmation">Preferences saved successfully!</p>
      )}
      {updateMutation.isError && (
        <p className="save-error">Failed to save preferences.</p>
      )}
    </div>
  );
}
