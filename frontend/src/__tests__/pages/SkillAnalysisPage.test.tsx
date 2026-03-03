import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { SkillAnalysisPage } from "../../pages/SkillAnalysisPage";

// Mock the hooks module
vi.mock("../../hooks/use-skill-analysis", () => ({
  useTitleGroups: vi.fn(),
  useSkillReport: vi.fn(),
  useBackfillSkills: vi.fn(),
}));

// Mock the api client
vi.mock("../../api/client", () => ({
  api: { get: vi.fn(), post: vi.fn(), download: vi.fn() },
}));

import {
  useTitleGroups,
  useSkillReport,
  useBackfillSkills,
} from "../../hooks/use-skill-analysis";

function wrapper({ children }: { children: React.ReactNode }) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return (
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  );
}

describe("SkillAnalysisPage", () => {
  it("shows empty state when no title is selected", () => {
    vi.mocked(useTitleGroups).mockReturnValue({
      data: [
        { title: "software engineer", job_count: 10 },
        { title: "data scientist", job_count: 5 },
      ],
    } as unknown as ReturnType<typeof useTitleGroups>);
    vi.mocked(useSkillReport).mockReturnValue({
      data: undefined,
      isLoading: false,
    } as unknown as ReturnType<typeof useSkillReport>);
    vi.mocked(useBackfillSkills).mockReturnValue({
      isPending: false,
      mutate: vi.fn(),
      data: undefined,
    } as unknown as ReturnType<typeof useBackfillSkills>);

    render(<SkillAnalysisPage />, { wrapper });

    expect(screen.getByTestId("empty-state")).toBeInTheDocument();
    expect(screen.getByTestId("title-select")).toBeInTheDocument();
  });

  it("shows title selector with options", () => {
    vi.mocked(useTitleGroups).mockReturnValue({
      data: [
        { title: "software engineer", job_count: 10 },
        { title: "data scientist", job_count: 5 },
      ],
    } as unknown as ReturnType<typeof useTitleGroups>);
    vi.mocked(useSkillReport).mockReturnValue({
      data: undefined,
      isLoading: false,
    } as unknown as ReturnType<typeof useSkillReport>);
    vi.mocked(useBackfillSkills).mockReturnValue({
      isPending: false,
      mutate: vi.fn(),
      data: undefined,
    } as unknown as ReturnType<typeof useBackfillSkills>);

    render(<SkillAnalysisPage />, { wrapper });

    const select = screen.getByTestId("title-select");
    expect(select).toBeInTheDocument();
    expect(select.querySelectorAll("option").length).toBe(3); // placeholder + 2 options
  });

  it("renders skill data when report is loaded", () => {
    vi.mocked(useTitleGroups).mockReturnValue({
      data: [{ title: "software engineer", job_count: 10 }],
    } as unknown as ReturnType<typeof useTitleGroups>);
    vi.mocked(useSkillReport).mockReturnValue({
      data: {
        title_pattern: "software engineer",
        total_jobs: 10,
        top_skills: [
          { skill_name: "python", category: "technical", count: 9, percentage: 90 },
          { skill_name: "docker", category: "technical", count: 6, percentage: 60 },
        ],
        technical_skills: [],
        soft_skills: [],
        co_occurrences: [],
        category_breakdown: { technical: 8, soft_skill: 3 },
      },
      isLoading: false,
    } as unknown as ReturnType<typeof useSkillReport>);
    vi.mocked(useBackfillSkills).mockReturnValue({
      isPending: false,
      mutate: vi.fn(),
      data: undefined,
    } as unknown as ReturnType<typeof useBackfillSkills>);

    render(<SkillAnalysisPage />, { wrapper });

    expect(screen.getByTestId("report-section")).toBeInTheDocument();
    expect(screen.getByText("python")).toBeInTheDocument();
    expect(screen.getByText("docker")).toBeInTheDocument();
  });
});
