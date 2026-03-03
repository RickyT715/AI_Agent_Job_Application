import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import type {
  SkillMarketReportResponse,
  TitleGroupResponse,
} from "../types/api";

export function useTitleGroups(minJobs: number = 3) {
  return useQuery({
    queryKey: ["skill-title-groups", minJobs],
    queryFn: () =>
      api.get<TitleGroupResponse[]>(
        `/skill-analysis/title-groups?min_jobs=${minJobs}`,
      ),
    staleTime: 60_000,
  });
}

export function useSkillReport(
  titlePattern: string | null,
  topN: number = 20,
) {
  return useQuery({
    queryKey: ["skill-report", titlePattern, topN],
    queryFn: () =>
      api.post<SkillMarketReportResponse>("/skill-analysis/report", {
        title_pattern: titlePattern,
        top_n: topN,
      }),
    enabled: !!titlePattern,
  });
}

export function useBackfillSkills() {
  return useMutation({
    mutationFn: () =>
      api.post<{ jobs_processed: number; total_skills: number }>(
        "/skill-analysis/backfill",
      ),
  });
}
