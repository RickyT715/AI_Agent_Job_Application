import { useMatches } from "../hooks/use-matches";
import { useAppStore } from "../stores/app-store";
import { JobFilters } from "../components/JobFilters";
import { JobList } from "../components/JobList";
import { MatchDetail } from "../components/MatchDetail";

export function DashboardPage() {
  const { filters, selectedJobId, setFilters, setSelectedJob } = useAppStore();
  const { data, isLoading, error } = useMatches(filters.min_score);

  const matches = data?.items ?? [];
  const selectedMatch = matches.find((m) => m.job?.id === selectedJobId);

  return (
    <div className="dashboard">
      <div className="page-header">
        <h1>Job Matches</h1>
        <p>{isLoading ? "Searching..." : `${matches.length} matches found`}</p>
      </div>

      <JobFilters filters={filters} onFilterChange={setFilters} />

      {error ? (
        <div className="empty-state">
          <p>Unable to load matches. Make sure the backend is running.</p>
        </div>
      ) : (
        <div className="dashboard-content">
          <JobList matches={matches} selectedJobId={selectedJobId} onSelectJob={setSelectedJob} />
          {selectedMatch && <MatchDetail match={selectedMatch} />}
        </div>
      )}
    </div>
  );
}
