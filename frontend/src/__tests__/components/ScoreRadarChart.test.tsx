import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ScoreRadarChart } from "../../components/ScoreRadarChart";

describe("ScoreRadarChart", () => {
  it("renders the chart container", () => {
    const breakdown = { skills: 8, experience: 7, education: 6, location: 9, salary: 7 };
    render(<ScoreRadarChart breakdown={breakdown} />);
    expect(screen.getByTestId("radar-chart")).toBeInTheDocument();
  });

  it("handles zero scores without error", () => {
    const breakdown = { skills: 0, experience: 0, education: 0, location: 0, salary: 0 };
    render(<ScoreRadarChart breakdown={breakdown} />);
    expect(screen.getByTestId("radar-chart")).toBeInTheDocument();
  });

  it("handles max scores without error", () => {
    const breakdown = { skills: 10, experience: 10, education: 10, location: 10, salary: 10 };
    render(<ScoreRadarChart breakdown={breakdown} />);
    expect(screen.getByTestId("radar-chart")).toBeInTheDocument();
  });

  it("handles missing dimensions gracefully", () => {
    const breakdown = { skills: 8 }; // Only one dimension
    render(<ScoreRadarChart breakdown={breakdown} />);
    expect(screen.getByTestId("radar-chart")).toBeInTheDocument();
  });
});
