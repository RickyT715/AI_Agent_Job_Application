import type { MatchResponse } from "../types/api";
import { ScoreRadarChart } from "./ScoreRadarChart";
import { SkillGapAnalysis } from "./SkillGapAnalysis";

interface MatchDetailProps {
  match: MatchResponse;
  onStartAgent?: () => void;
}

export function MatchDetail({ match, onStartAgent }: MatchDetailProps) {
  const job = match.job;

  return (
    <div className="match-detail">
      <div>
        <h2>{job?.title ?? `Job #${match.job_id}`}</h2>
        <p className="company">{job?.company}</p>
      </div>

      {job && (
        <div className="job-meta">
          {job.location && <span className="meta-tag">{job.location}</span>}
          {job.workplace_type && <span className="meta-tag">{job.workplace_type}</span>}
          {job.employment_type && <span className="meta-tag">{job.employment_type}</span>}
          {job.salary_min && job.salary_max && (
            <span className="meta-tag">
              {job.salary_currency ?? "USD"} {(job.salary_min / 1000).toFixed(0)}k - {(job.salary_max / 1000).toFixed(0)}k
            </span>
          )}
        </div>
      )}

      <div className="score-section">
        <div className="overall-score">
          {match.overall_score.toFixed(1)}
          <small>/10</small>
        </div>
        <ScoreRadarChart breakdown={match.score_breakdown} />
      </div>

      <div className="detail-section reasoning">
        <h3>Reasoning</h3>
        <p>{match.reasoning}</p>
      </div>

      <SkillGapAnalysis strengths={match.strengths} missingSkills={match.missing_skills} />

      {match.interview_talking_points.length > 0 && (
        <div className="detail-section talking-points">
          <h3>Interview Talking Points</h3>
          <ul>
            {match.interview_talking_points.map((point, i) => (
              <li key={i}>{point}</li>
            ))}
          </ul>
        </div>
      )}

      {onStartAgent && (
        <button onClick={onStartAgent} className="start-agent-btn">
          Start Application Agent
        </button>
      )}
    </div>
  );
}
