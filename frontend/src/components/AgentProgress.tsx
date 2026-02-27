interface AgentProgressProps {
  currentStep: string;
  progress: number;
  status: string;
  message: string;
}

const STEPS = ["detect_ats", "navigate", "fill_fields", "upload_resume", "review", "submit"];

export function AgentProgress({ currentStep, progress, status, message }: AgentProgressProps) {
  return (
    <div className="agent-progress" data-testid="agent-progress">
      <div className="progress-bar">
        <div
          className="progress-fill"
          style={{ width: `${progress * 100}%` }}
          role="progressbar"
          aria-valuenow={progress * 100}
          aria-valuemin={0}
          aria-valuemax={100}
        />
      </div>
      <div className="steps">
        {STEPS.map((step) => (
          <span
            key={step}
            className={`step ${step === currentStep ? "active" : ""}`}
            data-status={step === currentStep ? status : ""}
          >
            {step.replace("_", " ")}
          </span>
        ))}
      </div>
      {message && <p className="status-message">{message}</p>}
    </div>
  );
}
