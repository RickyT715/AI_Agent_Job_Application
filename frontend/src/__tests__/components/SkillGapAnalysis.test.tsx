import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { SkillGapAnalysis } from "../../components/SkillGapAnalysis";

describe("SkillGapAnalysis", () => {
  it("renders strengths list", () => {
    render(<SkillGapAnalysis strengths={["Python", "FastAPI"]} missingSkills={["Go"]} />);
    expect(screen.getByText("Python")).toBeInTheDocument();
    expect(screen.getByText("FastAPI")).toBeInTheDocument();
  });

  it("renders missing skills list", () => {
    render(<SkillGapAnalysis strengths={["Python"]} missingSkills={["Kubernetes", "Go"]} />);
    expect(screen.getByText("Kubernetes")).toBeInTheDocument();
    expect(screen.getByText("Go")).toBeInTheDocument();
  });

  it("renders both sections", () => {
    render(<SkillGapAnalysis strengths={["A"]} missingSkills={["B"]} />);
    expect(screen.getByText("Strengths")).toBeInTheDocument();
    expect(screen.getByText("Missing Skills")).toBeInTheDocument();
  });

  it("handles empty lists", () => {
    render(<SkillGapAnalysis strengths={[]} missingSkills={[]} />);
    expect(screen.getByTestId("skill-gap")).toBeInTheDocument();
  });
});
