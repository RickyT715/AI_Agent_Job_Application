import type { MatchResponse } from "../types/api";
import { JobCard } from "./JobCard";

interface JobListProps {
  matches: MatchResponse[];
  selectedJobId: number | null;
  onSelectJob: (id: number) => void;
}

export function JobList({ matches, selectedJobId, onSelectJob }: JobListProps) {
  if (matches.length === 0) {
    return (
      <div className="empty-state">
        <p data-testid="empty-list">No matches found. Try adjusting your filters or run a new search.</p>
      </div>
    );
  }

  return (
    <div className="job-list" role="list">
      {matches.map((match) => (
        <JobCard
          key={match.id}
          match={match}
          onSelect={onSelectJob}
          isSelected={match.job?.id === selectedJobId}
        />
      ))}
    </div>
  );
}
