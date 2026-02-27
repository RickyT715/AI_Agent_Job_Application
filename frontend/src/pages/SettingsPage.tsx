import { useState } from "react";
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
};

export function SettingsPage() {
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div className="settings-page">
      <div className="page-header">
        <h1>Settings</h1>
        <p>Configure your job search preferences and matching criteria</p>
      </div>
      <PreferencesForm preferences={DEFAULT_PREFERENCES} onSave={handleSave} />
      {saved && <p className="save-confirmation">Preferences saved successfully!</p>}
    </div>
  );
}
