/** TanStack Query hooks for resume generation. */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";
import type {
  ResumeGenerateRequest,
  ResumeGenerateResponse,
  ResumeGeneratorHealthResponse,
  ResumeStatusResponse,
} from "../types/api";

export function useResumeGeneratorHealth() {
  return useQuery({
    queryKey: ["resume-generator-health"],
    queryFn: () => api.get<ResumeGeneratorHealthResponse>("/resumes/health"),
    staleTime: 60_000,
  });
}

export function useGenerateResume() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (req: ResumeGenerateRequest) =>
      api.post<ResumeGenerateResponse>("/resumes/generate", req),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ["resumes-for-match", variables.match_id] });
    },
  });
}

export function useResumeStatus(resumeId: number | null) {
  return useQuery({
    queryKey: ["resume-status", resumeId],
    queryFn: () => api.get<ResumeStatusResponse>(`/resumes/${resumeId}/status`),
    enabled: resumeId !== null,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === "pending" || status === "running") return 3000;
      return false;
    },
  });
}

export function useResumesForMatch(matchId: number | null) {
  return useQuery({
    queryKey: ["resumes-for-match", matchId],
    queryFn: () => api.get<ResumeStatusResponse[]>(`/resumes/by-match/${matchId}`),
    enabled: matchId !== null,
  });
}
