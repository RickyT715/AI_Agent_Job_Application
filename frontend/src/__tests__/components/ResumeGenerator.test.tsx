import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ResumeGenerator } from "../../components/ResumeGenerator";
import { makeMatch } from "../mocks/data";

// Mock the hooks module
vi.mock("../../hooks/use-resume-generation", () => ({
  useResumeGeneratorHealth: vi.fn(),
  useGenerateResume: vi.fn(),
  useResumeStatus: vi.fn(),
  useResumesForMatch: vi.fn(),
}));

import {
  useResumeGeneratorHealth,
  useGenerateResume,
  useResumeStatus,
  useResumesForMatch,
} from "../../hooks/use-resume-generation";

function wrapper({ children }: { children: React.ReactNode }) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}

describe("ResumeGenerator", () => {
  it("renders generate button when service is available", () => {
    vi.mocked(useResumeGeneratorHealth).mockReturnValue({
      data: { available: true, detail: "Service healthy" },
    } as ReturnType<typeof useResumeGeneratorHealth>);
    vi.mocked(useGenerateResume).mockReturnValue({
      isPending: false,
      isError: false,
      mutate: vi.fn(),
      error: null,
    } as unknown as ReturnType<typeof useGenerateResume>);
    vi.mocked(useResumeStatus).mockReturnValue({
      data: undefined,
    } as ReturnType<typeof useResumeStatus>);
    vi.mocked(useResumesForMatch).mockReturnValue({
      data: [],
    } as unknown as ReturnType<typeof useResumesForMatch>);

    const match = makeMatch();
    render(<ResumeGenerator match={match} />, { wrapper });

    const btn = screen.getByTestId("generate-resume-btn");
    expect(btn).toBeInTheDocument();
    expect(btn).not.toBeDisabled();
    expect(btn).toHaveTextContent("Generate Tailored Resume");
  });

  it("shows unavailable message when service is down", () => {
    vi.mocked(useResumeGeneratorHealth).mockReturnValue({
      data: { available: false, detail: "Connection refused" },
    } as ReturnType<typeof useResumeGeneratorHealth>);
    vi.mocked(useGenerateResume).mockReturnValue({
      isPending: false,
      isError: false,
      mutate: vi.fn(),
      error: null,
    } as unknown as ReturnType<typeof useGenerateResume>);
    vi.mocked(useResumeStatus).mockReturnValue({
      data: undefined,
    } as ReturnType<typeof useResumeStatus>);
    vi.mocked(useResumesForMatch).mockReturnValue({
      data: [],
    } as unknown as ReturnType<typeof useResumesForMatch>);

    const match = makeMatch();
    render(<ResumeGenerator match={match} />, { wrapper });

    const btn = screen.getByTestId("generate-resume-btn");
    expect(btn).toBeDisabled();
    expect(screen.getByTestId("unavailable-msg")).toHaveTextContent("Connection refused");
  });

  it("shows generating state when mutation is pending", () => {
    vi.mocked(useResumeGeneratorHealth).mockReturnValue({
      data: { available: true, detail: "Service healthy" },
    } as ReturnType<typeof useResumeGeneratorHealth>);
    vi.mocked(useGenerateResume).mockReturnValue({
      isPending: true,
      isError: false,
      mutate: vi.fn(),
      error: null,
    } as unknown as ReturnType<typeof useGenerateResume>);
    vi.mocked(useResumeStatus).mockReturnValue({
      data: undefined,
    } as ReturnType<typeof useResumeStatus>);
    vi.mocked(useResumesForMatch).mockReturnValue({
      data: [],
    } as unknown as ReturnType<typeof useResumesForMatch>);

    const match = makeMatch();
    render(<ResumeGenerator match={match} />, { wrapper });

    const btn = screen.getByTestId("generate-resume-btn");
    expect(btn).toBeDisabled();
    expect(btn).toHaveTextContent("Generating...");
  });

  it("shows completed status with download buttons", () => {
    vi.mocked(useResumeGeneratorHealth).mockReturnValue({
      data: { available: true, detail: "Service healthy" },
    } as ReturnType<typeof useResumeGeneratorHealth>);
    vi.mocked(useGenerateResume).mockReturnValue({
      isPending: false,
      isError: false,
      mutate: vi.fn(),
      error: null,
    } as unknown as ReturnType<typeof useGenerateResume>);
    vi.mocked(useResumeStatus).mockReturnValue({
      data: {
        id: 1,
        match_id: 1,
        external_task_id: "ext-1",
        status: "completed" as const,
        resume_pdf_path: "data/resumes/resume-1.pdf",
        cover_letter_pdf_path: "data/resumes/cl-1.pdf",
        cover_letter_text: null,
        error_message: null,
        language: "en",
        provider: "anthropic",
        created_at: "2024-01-15T12:00:00Z",
        updated_at: "2024-01-15T12:05:00Z",
      },
    } as ReturnType<typeof useResumeStatus>);
    vi.mocked(useResumesForMatch).mockReturnValue({
      data: [],
    } as unknown as ReturnType<typeof useResumesForMatch>);

    const match = makeMatch();
    render(<ResumeGenerator match={match} />, { wrapper });

    expect(screen.getByText("Download Resume PDF")).toBeInTheDocument();
    expect(screen.getByText("Download Cover Letter PDF")).toBeInTheDocument();
    expect(screen.getByTestId("status-badge")).toHaveTextContent("completed");
  });

  it("shows error message on failure", () => {
    vi.mocked(useResumeGeneratorHealth).mockReturnValue({
      data: { available: true, detail: "Service healthy" },
    } as ReturnType<typeof useResumeGeneratorHealth>);
    vi.mocked(useGenerateResume).mockReturnValue({
      isPending: false,
      isError: false,
      mutate: vi.fn(),
      error: null,
    } as unknown as ReturnType<typeof useGenerateResume>);
    vi.mocked(useResumeStatus).mockReturnValue({
      data: {
        id: 2,
        match_id: 1,
        external_task_id: "ext-2",
        status: "failed" as const,
        resume_pdf_path: null,
        cover_letter_pdf_path: null,
        cover_letter_text: null,
        error_message: "LaTeX compilation failed",
        language: "en",
        provider: "anthropic",
        created_at: "2024-01-15T12:00:00Z",
        updated_at: "2024-01-15T12:01:00Z",
      },
    } as ReturnType<typeof useResumeStatus>);
    vi.mocked(useResumesForMatch).mockReturnValue({
      data: [],
    } as unknown as ReturnType<typeof useResumesForMatch>);

    const match = makeMatch();
    render(<ResumeGenerator match={match} />, { wrapper });

    expect(screen.getByTestId("status-badge")).toHaveTextContent("failed");
    expect(screen.getByText("LaTeX compilation failed")).toBeInTheDocument();
  });

  it("shows previous generations section", () => {
    vi.mocked(useResumeGeneratorHealth).mockReturnValue({
      data: { available: true, detail: "Service healthy" },
    } as ReturnType<typeof useResumeGeneratorHealth>);
    vi.mocked(useGenerateResume).mockReturnValue({
      isPending: false,
      isError: false,
      mutate: vi.fn(),
      error: null,
    } as unknown as ReturnType<typeof useGenerateResume>);
    vi.mocked(useResumeStatus).mockReturnValue({
      data: undefined,
    } as ReturnType<typeof useResumeStatus>);
    vi.mocked(useResumesForMatch).mockReturnValue({
      data: [
        {
          id: 10,
          match_id: 1,
          external_task_id: "ext-old",
          status: "completed" as const,
          resume_pdf_path: "data/resumes/resume-10.pdf",
          cover_letter_pdf_path: null,
          cover_letter_text: null,
          error_message: null,
          language: "en",
          provider: "anthropic",
          created_at: "2024-01-10T10:00:00Z",
          updated_at: "2024-01-10T10:05:00Z",
        },
      ],
    } as unknown as ReturnType<typeof useResumesForMatch>);

    const match = makeMatch();
    render(<ResumeGenerator match={match} />, { wrapper });

    expect(screen.getByText("Previous Generations")).toBeInTheDocument();
    expect(screen.getByText("Download Resume PDF")).toBeInTheDocument();
  });
});
