import { useState } from "react";
import { api } from "../api/client";
import {
  useGenerateResume,
  useResumeGeneratorHealth,
  useResumesForMatch,
  useResumeStatus,
} from "../hooks/use-resume-generation";
import type { MatchResponse, ResumeStatusResponse } from "../types/api";

interface ResumeGeneratorProps {
  match: MatchResponse;
}

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

function StatusBadge({ status }: { status: string }) {
  const validStatuses = ["pending", "running", "completed", "failed"];
  const modifier = validStatuses.includes(status) ? status : "unknown";
  return (
    <span
      data-testid="status-badge"
      className={`status-badge ${modifier}`}
    >
      {status}
    </span>
  );
}

function ResumeEntry({ resume }: { resume: ResumeStatusResponse }) {
  const handleDownloadResume = async () => {
    const blob = await api.download(`/resumes/${resume.id}/download/resume`);
    downloadBlob(blob, `resume-${resume.id}.pdf`);
  };
  const handleDownloadCoverLetter = async () => {
    const blob = await api.download(`/resumes/${resume.id}/download/cover-letter`);
    downloadBlob(blob, `cover-letter-${resume.id}.pdf`);
  };

  return (
    <div className="resume-entry">
      <div className="resume-entry-header">
        <StatusBadge status={resume.status} />
        <span className="resume-entry-meta">
          {resume.language.toUpperCase()} &middot; {resume.provider}
        </span>
      </div>
      {resume.status === "completed" && (
        <div className="resume-entry-actions">
          {resume.resume_pdf_path && (
            <button onClick={handleDownloadResume} className="download-btn">
              Download Resume PDF
            </button>
          )}
          {resume.cover_letter_pdf_path && (
            <button onClick={handleDownloadCoverLetter} className="download-btn">
              Download Cover Letter PDF
            </button>
          )}
        </div>
      )}
      {resume.status === "failed" && resume.error_message && (
        <p className="resume-error">
          {resume.error_message}
        </p>
      )}
    </div>
  );
}

export function ResumeGenerator({ match }: ResumeGeneratorProps) {
  const { data: health } = useResumeGeneratorHealth();
  const generateMutation = useGenerateResume();
  const [activeResumeId, setActiveResumeId] = useState<number | null>(null);
  const { data: activeStatus } = useResumeStatus(activeResumeId);
  const { data: previousResumes } = useResumesForMatch(match.id);

  const isAvailable = health?.available ?? false;
  const isGenerating =
    generateMutation.isPending ||
    activeStatus?.status === "pending" ||
    activeStatus?.status === "running";

  const handleGenerate = () => {
    generateMutation.mutate(
      { match_id: match.id },
      {
        onSuccess: (data) => {
          setActiveResumeId(data.id);
        },
      },
    );
  };

  return (
    <div className="resume-generator" data-testid="resume-generator">
      <h3>Tailored Resume</h3>

      <button
        onClick={handleGenerate}
        disabled={!isAvailable || isGenerating}
        className="generate-resume-btn"
        data-testid="generate-resume-btn"
      >
        {isGenerating ? "Generating..." : "Generate Tailored Resume"}
      </button>

      {!isAvailable && health && (
        <p className="resume-hint" data-testid="unavailable-msg">
          Resume generator unavailable: {health.detail}
        </p>
      )}

      {generateMutation.isError && (
        <p className="resume-gen-error">
          {generateMutation.error.message}
        </p>
      )}

      {activeStatus && (
        <div className="resume-active-status">
          <ResumeEntry resume={activeStatus} />
        </div>
      )}

      {previousResumes && previousResumes.length > 0 && (
        <div className="resume-previous">
          <h4>Previous Generations</h4>
          {previousResumes
            .filter((r) => r.id !== activeResumeId)
            .map((r) => (
              <ResumeEntry key={r.id} resume={r} />
            ))}
        </div>
      )}
    </div>
  );
}
