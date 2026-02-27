import type { MatchResponse } from "../types/api";

function scoreColor(score: number): string {
  if (score >= 8) return "green";
  if (score >= 6) return "yellow";
  return "red";
}

function formatSalary(min: number | null, max: number | null, currency: string | null): string | null {
  if (!min && !max) return null;
  const cur = currency ?? "USD";
  if (min && max) return `${cur} ${(min / 1000).toFixed(0)}k-${(max / 1000).toFixed(0)}k`;
  if (min) return `${cur} ${(min / 1000).toFixed(0)}k+`;
  return null;
}

interface JobCardProps {
  match: MatchResponse;
  onSelect: (id: number) => void;
  isSelected?: boolean;
}

export function JobCard({ match, onSelect, isSelected }: JobCardProps) {
  const job = match.job;
  if (!job) return null;

  const color = scoreColor(match.overall_score);
  const salary = formatSalary(job.salary_min, job.salary_max, job.salary_currency);

  return (
    <div
      role="article"
      className={`job-card ${isSelected ? "selected" : ""}`}
      onClick={() => onSelect(job.id)}
    >
      <div className="job-card-header">
        <h3>{job.title}</h3>
        <span data-testid="score-badge" data-color={color} className={`score-badge ${color}`}>
          {match.overall_score.toFixed(1)}
        </span>
      </div>
      <p className="company">{job.company}</p>
      <div className="meta">
        {job.location && <span>{job.location}</span>}
        {job.workplace_type && <span>{job.workplace_type}</span>}
        {job.source && <span>{job.source}</span>}
      </div>
      {salary && <span className="salary-tag">{salary}</span>}
    </div>
  );
}
