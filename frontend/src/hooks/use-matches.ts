/** TanStack Query hooks for match data. */

import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import type { MatchResponse, PaginatedResponse } from "../types/api";
import type { Filters } from "../stores/app-store";

export function useMatches(filters: Filters) {
  return useQuery({
    queryKey: ["matches", filters],
    queryFn: () => {
      const params = new URLSearchParams();
      if (filters.min_score !== undefined) params.set("min_score", String(filters.min_score));
      if (filters.q) params.set("q", filters.q);
      if (filters.location) params.set("location", filters.location);
      if (filters.workplace_type) params.set("workplace_type", filters.workplace_type);
      const qs = params.toString();
      return api.get<PaginatedResponse<MatchResponse>>(`/matches${qs ? `?${qs}` : ""}`);
    },
    staleTime: 30_000,
  });
}

export function useMatch(id: number | null) {
  return useQuery({
    queryKey: ["match", id],
    queryFn: () => api.get<MatchResponse>(`/matches/${id}`),
    enabled: id !== null,
  });
}
