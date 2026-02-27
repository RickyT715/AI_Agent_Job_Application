import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { PreferencesForm } from "../../components/PreferencesForm";
import { makePreferences } from "../mocks/data";

describe("PreferencesForm", () => {
  it("renders form with current values", () => {
    const prefs = makePreferences();
    render(<PreferencesForm preferences={prefs} onSave={vi.fn()} />);
    expect(screen.getByTestId("preferences-form")).toBeInTheDocument();
    const titleInput = screen.getByLabelText("Job titles");
    expect(titleInput).toHaveValue("Software Engineer, Backend Developer");
  });

  it("calls onSave with updated values on submit", async () => {
    const user = userEvent.setup();
    const onSave = vi.fn();
    const prefs = makePreferences();
    render(<PreferencesForm preferences={prefs} onSave={onSave} />);

    const titleInput = screen.getByLabelText("Job titles");
    await user.clear(titleInput);
    await user.type(titleInput, "ML Engineer");

    await user.click(screen.getByText("Save Preferences"));
    expect(onSave).toHaveBeenCalledWith(
      expect.objectContaining({ job_titles: ["ML Engineer"] }),
    );
  });

  it("renders experience level selector", () => {
    const prefs = makePreferences();
    render(<PreferencesForm preferences={prefs} onSave={vi.fn()} />);
    const select = screen.getByLabelText("Experience level");
    expect(select).toHaveValue("mid");
  });
});
