import { useState } from "react";
import type { Filters } from "../stores/app-store";

interface JobFiltersProps {
  filters: Filters;
  onFilterChange: (filters: Partial<Filters>) => void;
}

export function JobFilters({ filters, onFilterChange }: JobFiltersProps) {
  const [search, setSearch] = useState(filters.q ?? "");

  const handleSearch = () => {
    onFilterChange({ q: search || undefined });
  };

  return (
    <div className="job-filters">
      <div className="search-wrapper">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M9 3.5a5.5 5.5 0 100 11 5.5 5.5 0 000-11zM2 9a7 7 0 1112.452 4.391l3.328 3.329a.75.75 0 11-1.06 1.06l-3.329-3.328A7 7 0 012 9z" clipRule="evenodd" />
        </svg>
        <input
          type="text"
          placeholder="Search jobs..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          aria-label="Search jobs"
        />
      </div>

      <div className="filter-group">
        <label
          className={`filter-pill ${filters.workplace_type === "remote" ? "active" : ""}`}
        >
          <input
            type="checkbox"
            checked={filters.workplace_type === "remote"}
            onChange={(e) =>
              onFilterChange({ workplace_type: e.target.checked ? "remote" : undefined })
            }
          />
          Remote
        </label>
        <label
          className={`filter-pill ${filters.workplace_type === "hybrid" ? "active" : ""}`}
        >
          <input
            type="checkbox"
            checked={filters.workplace_type === "hybrid"}
            onChange={(e) =>
              onFilterChange({ workplace_type: e.target.checked ? "hybrid" : undefined })
            }
          />
          Hybrid
        </label>
        <label
          className={`filter-pill ${filters.workplace_type === "onsite" ? "active" : ""}`}
        >
          <input
            type="checkbox"
            checked={filters.workplace_type === "onsite"}
            onChange={(e) =>
              onFilterChange({ workplace_type: e.target.checked ? "onsite" : undefined })
            }
          />
          On-site
        </label>
      </div>

      <div className="score-filter">
        <span>Min score</span>
        <input
          type="range"
          min={0}
          max={10}
          step={0.5}
          value={filters.min_score ?? 0}
          onChange={(e) => onFilterChange({ min_score: Number(e.target.value) || undefined })}
          aria-label="Minimum score"
        />
        <span className="score-val">{filters.min_score ?? 0}</span>
      </div>
    </div>
  );
}
