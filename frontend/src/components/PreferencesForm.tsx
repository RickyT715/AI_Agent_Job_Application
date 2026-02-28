import { useState } from "react";
import type { PreferencesResponse } from "../types/api";

interface PreferencesFormProps {
  preferences: PreferencesResponse;
  onSave: (updates: Partial<PreferencesResponse>) => void;
}

const WORKPLACE_OPTIONS = [
  { value: "remote", label: "Remote" },
  { value: "hybrid", label: "Hybrid" },
  { value: "onsite", label: "On-site" },
];

const EMPLOYMENT_OPTIONS = [
  { value: "FULLTIME", label: "Full-time" },
  { value: "PARTTIME", label: "Part-time" },
  { value: "CONTRACT", label: "Contract" },
  { value: "INTERNSHIP", label: "Internship" },
  { value: "TEMPORARY", label: "Temporary" },
];

const DATE_POSTED_OPTIONS = [
  { value: "today", label: "Today" },
  { value: "3days", label: "Past 3 days" },
  { value: "week", label: "Past week" },
  { value: "month", label: "Past month" },
  { value: "all", label: "All time" },
];

const CURRENCY_OPTIONS = ["USD", "CAD", "EUR", "GBP"];

const SOURCE_OPTIONS = [
  { value: "jsearch", label: "JSearch (Google Jobs)" },
  { value: "greenhouse", label: "Greenhouse" },
  { value: "lever", label: "Lever" },
  { value: "workday", label: "Workday" },
  { value: "adzuna", label: "Adzuna" },
  { value: "arbeitnow", label: "Arbeitnow" },
];

const WEIGHT_KEYS = ["skills", "experience", "education", "location", "salary"] as const;

export function PreferencesForm({ preferences, onSave }: PreferencesFormProps) {
  const [jobTitles, setJobTitles] = useState(preferences.job_titles.join(", "));
  const [locations, setLocations] = useState(preferences.locations.join(", "));
  const [experienceLevel, setExperienceLevel] = useState(preferences.experience_level);
  const [salaryMin, setSalaryMin] = useState(preferences.salary_min?.toString() ?? "");
  const [salaryMax, setSalaryMax] = useState(preferences.salary_max?.toString() ?? "");
  const [workplaceTypes, setWorkplaceTypes] = useState<string[]>(preferences.workplace_types);
  const [weights, setWeights] = useState<Record<string, number>>(
    preferences.weights ?? { skills: 0.3, experience: 0.25, education: 0.15, location: 0.15, salary: 0.15 }
  );
  const [resumeFile, setResumeFile] = useState<string | null>(null);
  const [employmentTypes, setEmploymentTypes] = useState<string[]>(preferences.employment_types ?? ["FULLTIME"]);
  const [datePosted, setDatePosted] = useState(preferences.date_posted ?? "month");
  const [salaryCurrency, setSalaryCurrency] = useState(preferences.salary_currency ?? "USD");
  const [finalResultsCount, setFinalResultsCount] = useState(preferences.final_results_count ?? 10);
  const [numPagesPerSource, setNumPagesPerSource] = useState(preferences.num_pages_per_source ?? 1);
  const [enabledSources, setEnabledSources] = useState<string[]>(preferences.enabled_sources ?? ["jsearch"]);
  const [greenhouseBoardTokens, setGreenhouseBoardTokens] = useState(
    (preferences.greenhouse_board_tokens ?? []).join(", ")
  );
  const [leverCompanies, setLeverCompanies] = useState(
    (preferences.lever_companies ?? []).join(", ")
  );
  const [workdayUrls, setWorkdayUrls] = useState(
    (preferences.workday_urls ?? []).join("\n")
  );
  const [anthropicBaseUrl, setAnthropicBaseUrl] = useState(
    preferences.anthropic_base_url ?? ""
  );

  const weightsTotal = Object.values(weights).reduce((a, b) => a + b, 0);
  const weightsValid = Math.abs(weightsTotal - 1.0) < 0.02;

  const toggleWorkplace = (value: string) => {
    setWorkplaceTypes((prev) =>
      prev.includes(value) ? prev.filter((t) => t !== value) : [...prev, value]
    );
  };

  const toggleEmployment = (value: string) => {
    setEmploymentTypes((prev) =>
      prev.includes(value) ? prev.filter((t) => t !== value) : [...prev, value]
    );
  };

  const toggleSource = (value: string) => {
    setEnabledSources((prev) =>
      prev.includes(value) ? prev.filter((t) => t !== value) : [...prev, value]
    );
  };

  const updateWeight = (key: string, value: number) => {
    setWeights((prev) => ({ ...prev, [key]: value }));
  };

  const handleResumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setResumeFile(file.name);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave({
      job_titles: jobTitles.split(",").map((s) => s.trim()).filter(Boolean),
      locations: locations.split(",").map((s) => s.trim()).filter(Boolean),
      experience_level: experienceLevel,
      salary_min: salaryMin ? parseInt(salaryMin, 10) : null,
      salary_max: salaryMax ? parseInt(salaryMax, 10) : null,
      workplace_types: workplaceTypes,
      weights,
      employment_types: employmentTypes,
      date_posted: datePosted,
      salary_currency: salaryCurrency,
      final_results_count: finalResultsCount,
      num_pages_per_source: numPagesPerSource,
      enabled_sources: enabledSources,
      greenhouse_board_tokens: greenhouseBoardTokens.split(",").map((s) => s.trim()).filter(Boolean),
      lever_companies: leverCompanies.split(",").map((s) => s.trim()).filter(Boolean),
      workday_urls: workdayUrls.split("\n").map((s) => s.trim()).filter(Boolean),
      anthropic_base_url: anthropicBaseUrl.trim(),
    });
  };

  return (
    <form onSubmit={handleSubmit} className="preferences-form" data-testid="preferences-form">
      {/* --- Job Search Section --- */}
      <div className="settings-section">
        <h2>Job Search Preferences</h2>
        <div className="form-section">
          <div className="form-group">
            <label>Job Titles</label>
            <input
              type="text"
              value={jobTitles}
              onChange={(e) => setJobTitles(e.target.value)}
              aria-label="Job titles"
              placeholder="e.g. Software Engineer, ML Engineer, Backend Developer"
            />
            <span className="hint">Comma-separated list of target job titles</span>
          </div>

          <div className="form-group">
            <label>Preferred Locations</label>
            <input
              type="text"
              value={locations}
              onChange={(e) => setLocations(e.target.value)}
              aria-label="Locations"
              placeholder="e.g. Remote, Toronto ON, San Francisco CA"
            />
            <span className="hint">Comma-separated list of preferred locations</span>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Experience Level</label>
              <select
                value={experienceLevel}
                onChange={(e) => setExperienceLevel(e.target.value)}
                aria-label="Experience level"
              >
                <option value="entry">Entry Level</option>
                <option value="mid">Mid Level</option>
                <option value="senior">Senior Level</option>
                <option value="lead">Lead / Staff</option>
                <option value="executive">Executive</option>
              </select>
            </div>
            <div className="form-group">
              <label>Workplace Type</label>
              <div className="checkbox-group">
                {WORKPLACE_OPTIONS.map(({ value, label }) => (
                  <label
                    key={value}
                    className={`checkbox-pill ${workplaceTypes.includes(value) ? "checked" : ""}`}
                  >
                    <input
                      type="checkbox"
                      checked={workplaceTypes.includes(value)}
                      onChange={() => toggleWorkplace(value)}
                    />
                    {label}
                  </label>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* --- Employment Type Section --- */}
      <div className="settings-section">
        <h2>Employment Type</h2>
        <div className="form-section">
          <div className="checkbox-group">
            {EMPLOYMENT_OPTIONS.map(({ value, label }) => (
              <label
                key={value}
                className={`checkbox-pill ${employmentTypes.includes(value) ? "checked" : ""}`}
              >
                <input
                  type="checkbox"
                  checked={employmentTypes.includes(value)}
                  onChange={() => toggleEmployment(value)}
                />
                {label}
              </label>
            ))}
          </div>
        </div>
      </div>

      {/* --- Date Posted Filter --- */}
      <div className="settings-section">
        <h2>Date Posted</h2>
        <div className="form-section">
          <div className="form-group">
            <select
              value={datePosted}
              onChange={(e) => setDatePosted(e.target.value)}
              aria-label="Date posted filter"
            >
              {DATE_POSTED_OPTIONS.map(({ value, label }) => (
                <option key={value} value={value}>{label}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* --- Salary Section --- */}
      <div className="settings-section">
        <h2>Salary Expectations</h2>
        <div className="form-section">
          <div className="form-row">
            <div className="form-group">
              <label>Minimum Salary</label>
              <input
                type="number"
                value={salaryMin}
                onChange={(e) => setSalaryMin(e.target.value)}
                placeholder="e.g. 100000"
                min={0}
                step={5000}
                aria-label="Minimum salary"
              />
            </div>
            <div className="form-group">
              <label>Maximum Salary</label>
              <input
                type="number"
                value={salaryMax}
                onChange={(e) => setSalaryMax(e.target.value)}
                placeholder="e.g. 200000"
                min={0}
                step={5000}
                aria-label="Maximum salary"
              />
            </div>
            <div className="form-group">
              <label>Currency</label>
              <select
                value={salaryCurrency}
                onChange={(e) => setSalaryCurrency(e.target.value)}
                aria-label="Salary currency"
              >
                {CURRENCY_OPTIONS.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>
          </div>
          <span className="hint">Leave salary blank if no specific range</span>
        </div>
      </div>

      {/* --- Results & Pagination --- */}
      <div className="settings-section">
        <h2>Search Settings</h2>
        <div className="form-section">
          <div className="form-row">
            <div className="form-group">
              <label>Results to show</label>
              <input
                type="number"
                value={finalResultsCount}
                onChange={(e) => setFinalResultsCount(parseInt(e.target.value, 10) || 10)}
                min={1}
                max={50}
                aria-label="Number of results"
              />
              <span className="hint">How many matched jobs to return (1-50)</span>
            </div>
            <div className="form-group">
              <label>Pages per source</label>
              <input
                type="number"
                value={numPagesPerSource}
                onChange={(e) => setNumPagesPerSource(parseInt(e.target.value, 10) || 1)}
                min={1}
                max={10}
                aria-label="Pages per source"
              />
              <span className="hint">More pages = more jobs to search through</span>
            </div>
          </div>
        </div>
      </div>

      {/* --- Search Sources --- */}
      <div className="settings-section">
        <h2>Search Sources</h2>
        <div className="form-section">
          <div className="checkbox-group">
            {SOURCE_OPTIONS.map(({ value, label }) => (
              <label
                key={value}
                className={`checkbox-pill ${enabledSources.includes(value) ? "checked" : ""}`}
              >
                <input
                  type="checkbox"
                  checked={enabledSources.includes(value)}
                  onChange={() => toggleSource(value)}
                />
                {label}
              </label>
            ))}
          </div>

          {enabledSources.includes("greenhouse") && (
            <div className="form-group" style={{ marginTop: "1rem" }}>
              <label>Greenhouse Board Tokens</label>
              <input
                type="text"
                value={greenhouseBoardTokens}
                onChange={(e) => setGreenhouseBoardTokens(e.target.value)}
                placeholder="e.g. stripe, airbnb"
                aria-label="Greenhouse board tokens"
              />
              <span className="hint">Comma-separated company board tokens</span>
            </div>
          )}

          {enabledSources.includes("lever") && (
            <div className="form-group" style={{ marginTop: "1rem" }}>
              <label>Lever Company Slugs</label>
              <input
                type="text"
                value={leverCompanies}
                onChange={(e) => setLeverCompanies(e.target.value)}
                placeholder="e.g. netflix, figma"
                aria-label="Lever company slugs"
              />
              <span className="hint">Comma-separated company slugs</span>
            </div>
          )}

          {enabledSources.includes("workday") && (
            <div className="form-group" style={{ marginTop: "1rem" }}>
              <label>Workday Base URLs</label>
              <textarea
                value={workdayUrls}
                onChange={(e) => setWorkdayUrls(e.target.value)}
                placeholder="One URL per line"
                rows={3}
                aria-label="Workday base URLs"
              />
              <span className="hint">One Workday base URL per line</span>
            </div>
          )}
        </div>
      </div>

      {/* --- Claude Proxy Section --- */}
      <div className="settings-section">
        <h2>Claude API Proxy</h2>
        <div className="form-section">
          <div className="form-group">
            <label>Proxy URL</label>
            <input
              type="text"
              value={anthropicBaseUrl}
              onChange={(e) => setAnthropicBaseUrl(e.target.value)}
              placeholder="e.g. http://localhost:42069"
              aria-label="Claude proxy URL"
            />
            <span className="hint">
              Route Claude API calls through a local proxy (e.g. claude-code-proxy).
              Leave empty to use direct Anthropic API with your API key.
            </span>
          </div>
        </div>
      </div>

      {/* --- Scoring Weights Section --- */}
      <div className="settings-section">
        <h2>Match Scoring Weights</h2>
        <div className="form-section">
          <span className="hint">
            Adjust how each dimension contributes to the overall match score. Weights must sum to 1.0.
          </span>
          <div className="weight-sliders">
            {WEIGHT_KEYS.map((key) => (
              <div key={key} className="weight-row">
                <label>{key}</label>
                <input
                  type="range"
                  min={0}
                  max={0.5}
                  step={0.05}
                  value={weights[key] ?? 0.2}
                  onChange={(e) => updateWeight(key, parseFloat(e.target.value))}
                  aria-label={`${key} weight`}
                />
                <span className="weight-val">{(weights[key] ?? 0).toFixed(2)}</span>
              </div>
            ))}
          </div>
          <p className={`weight-total ${weightsValid ? "valid" : "invalid"}`}>
            Total: {weightsTotal.toFixed(2)} {weightsValid ? "" : "(must equal 1.00)"}
          </p>
        </div>
      </div>

      {/* --- Resume Upload Section --- */}
      <div className="settings-section">
        <h2>Resume</h2>
        <div className="form-section">
          <div className="resume-upload">
            {resumeFile ? (
              <div className="resume-status">
                Uploaded: {resumeFile}
              </div>
            ) : (
              <label className="upload-area">
                <span className="upload-icon">+</span>
                <span>Click to upload your resume (PDF, DOCX, TXT)</span>
                <span className="hint">Max 10 MB</span>
                <input
                  type="file"
                  accept=".pdf,.docx,.txt"
                  onChange={handleResumeChange}
                  style={{ display: "none" }}
                  aria-label="Upload resume"
                />
              </label>
            )}
          </div>
        </div>
      </div>

      {/* --- Save Button --- */}
      <button type="submit" className="save-btn">
        Save Preferences
      </button>
    </form>
  );
}
