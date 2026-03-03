import { useState } from "react";
import { SkillFrequencyTable } from "../components/SkillFrequencyTable";
import {
  useBackfillSkills,
  useSkillReport,
  useTitleGroups,
} from "../hooks/use-skill-analysis";
import { api } from "../api/client";

export function SkillAnalysisPage() {
  const [selectedTitle, setSelectedTitle] = useState<string | null>(null);
  const [drillSkill, setDrillSkill] = useState<string | null>(null);

  const titleGroups = useTitleGroups();
  const report = useSkillReport(selectedTitle);
  const backfill = useBackfillSkills();

  const handleDownloadPdf = async () => {
    if (!selectedTitle) return;
    const blob = await api.download("/skill-analysis/report/pdf");
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "skill-report.pdf";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="skill-analysis-page">
      <h1>Skill Market Analysis</h1>

      <div className="controls">
        <label htmlFor="title-select">Job Title Group</label>
        <select
          id="title-select"
          data-testid="title-select"
          value={selectedTitle ?? ""}
          onChange={(e) => {
            setSelectedTitle(e.target.value || null);
            setDrillSkill(null);
          }}
        >
          <option value="">-- Select a title --</option>
          {titleGroups.data?.map((g) => (
            <option key={g.title} value={g.title}>
              {g.title} ({g.job_count} jobs)
            </option>
          ))}
        </select>

        <button
          data-testid="backfill-btn"
          onClick={() => backfill.mutate()}
          disabled={backfill.isPending}
        >
          {backfill.isPending ? "Backfilling..." : "Backfill Skills"}
        </button>

        {selectedTitle && (
          <button onClick={handleDownloadPdf}>Download PDF</button>
        )}
      </div>

      {backfill.data && (
        <p data-testid="backfill-result">
          Backfilled {backfill.data.total_skills} skills from{" "}
          {backfill.data.jobs_processed} jobs.
        </p>
      )}

      {report.isLoading && <p>Loading analysis...</p>}

      {report.data && (
        <div data-testid="report-section">
          <p>
            Analyzed <strong>{report.data.total_jobs}</strong> jobs matching "
            {report.data.title_pattern}"
          </p>

          <h2>Top Skills</h2>
          <SkillFrequencyTable
            skills={report.data.top_skills}
            onSkillClick={setDrillSkill}
          />

          {drillSkill && (() => {
            const filtered = report.data.co_occurrences.filter(
              (c) => c.skill_a === drillSkill || c.skill_b === drillSkill
            );
            if (filtered.length === 0) return null;
            return (
              <div data-testid="co-occurrence-section">
                <h2>
                  Co-occurring with "{drillSkill}"
                </h2>
                <table>
                  <thead>
                    <tr>
                      <th>Skill</th>
                      <th>Co-occurs</th>
                      <th>%</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filtered.map((c) => {
                      const paired = c.skill_a === drillSkill ? c.skill_b : c.skill_a;
                      return (
                        <tr key={paired}>
                          <td>{paired}</td>
                          <td>{c.co_count}</td>
                          <td>{c.percentage}%</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            );
          })()}
        </div>
      )}

      {!selectedTitle && !report.isLoading && (
        <p data-testid="empty-state">
          Select a job title group above to see skill demand analysis.
        </p>
      )}
    </div>
  );
}
