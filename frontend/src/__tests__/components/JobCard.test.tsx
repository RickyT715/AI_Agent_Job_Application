import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { JobCard } from "../../components/JobCard";
import { makeMatch } from "../mocks/data";

describe("JobCard", () => {
  it("renders job title and company", () => {
    const match = makeMatch();
    render(<JobCard match={match} onSelect={vi.fn()} />);
    expect(screen.getByText("Software Engineer")).toBeInTheDocument();
    expect(screen.getByText("TestCo")).toBeInTheDocument();
  });

  it("renders score badge green for score >= 8", () => {
    const match = makeMatch({ overall_score: 9.0 });
    render(<JobCard match={match} onSelect={vi.fn()} />);
    const badge = screen.getByTestId("score-badge");
    expect(badge).toHaveAttribute("data-color", "green");
  });

  it("renders score badge yellow for score 6-7", () => {
    const match = makeMatch({ overall_score: 6.5 });
    render(<JobCard match={match} onSelect={vi.fn()} />);
    const badge = screen.getByTestId("score-badge");
    expect(badge).toHaveAttribute("data-color", "yellow");
  });

  it("renders score badge red for score <= 5", () => {
    const match = makeMatch({ overall_score: 4.0 });
    render(<JobCard match={match} onSelect={vi.fn()} />);
    const badge = screen.getByTestId("score-badge");
    expect(badge).toHaveAttribute("data-color", "red");
  });

  it("calls onSelect with job id when clicked", async () => {
    const user = userEvent.setup();
    const onSelect = vi.fn();
    const match = makeMatch();
    render(<JobCard match={match} onSelect={onSelect} />);
    await user.click(screen.getByRole("article"));
    expect(onSelect).toHaveBeenCalledWith(1);
  });

  it("renders location when present", () => {
    const match = makeMatch();
    render(<JobCard match={match} onSelect={vi.fn()} />);
    expect(screen.getByText("Remote")).toBeInTheDocument();
  });
});
