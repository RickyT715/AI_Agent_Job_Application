/** TanStack Query hooks for match data. */

import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import type { MatchResponse, PaginatedResponse } from "../types/api";

export function useMatches(minScore?: number) {
  return useQuery({
    queryKey: ["matches", minScore],
    queryFn: () => {
      const params = new URLSearchParams();
      if (minScore !== undefined) params.set("min_score", String(minScore));
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
