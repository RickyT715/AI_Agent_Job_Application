/** TanStack Query hooks for job data. */

import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import type { JobResponse, PaginatedResponse } from "../types/api";
import { useAppStore } from "../stores/app-store";

export function useJobs() {
  const filters = useAppStore((s) => s.filters);

  return useQuery({
    queryKey: ["jobs", filters],
    queryFn: () => {
      const params = new URLSearchParams();
      if (filters.q) params.set("q", filters.q);
      if (filters.location) params.set("location", filters.location);
      if (filters.workplace_type) params.set("workplace_type", filters.workplace_type);
      const qs = params.toString();
      return api.get<PaginatedResponse<JobResponse>>(`/jobs${qs ? `?${qs}` : ""}`);
    },
    staleTime: 30_000,
  });
}

export function useJob(id: number | null) {
  return useQuery({
    queryKey: ["job", id],
    queryFn: () => api.get<JobResponse>(`/jobs/${id}`),
    enabled: id !== null,
  });
}
