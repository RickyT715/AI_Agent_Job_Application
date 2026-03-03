import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { MemoryRouter } from "react-router-dom";
import { SettingsPage } from "../../pages/SettingsPage";

// Mock api client
vi.mock("../../api/client", () => ({
  api: {
    get: vi.fn(),
    put: vi.fn(),
  },
}));

import { api } from "../../api/client";
import { makePreferences } from "../mocks/data";

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>{children}</MemoryRouter>
      </QueryClientProvider>
    );
  };
}

describe("SettingsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows loading state while fetching preferences", () => {
    // Never resolve so the query stays in loading
    vi.mocked(api.get).mockReturnValue(new Promise(() => {}));

    render(<SettingsPage />, { wrapper: createWrapper() });
    expect(screen.getByText("Loading preferences...")).toBeInTheDocument();
  });

  it("renders PreferencesForm after loading", async () => {
    const prefs = makePreferences();
    vi.mocked(api.get).mockResolvedValue(prefs);

    render(<SettingsPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByTestId("preferences-form")).toBeInTheDocument();
    });
    expect(screen.getByText("Settings")).toBeInTheDocument();
    expect(
      screen.getByText("Configure your job search preferences and matching criteria"),
    ).toBeInTheDocument();
  });

  it("shows default preferences when API returns nothing", async () => {
    vi.mocked(api.get).mockRejectedValue(new Error("Network error"));

    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <SettingsPage />
        </MemoryRouter>
      </QueryClientProvider>,
    );

    // After error, the component uses DEFAULT_PREFERENCES via ?? fallback
    await waitFor(() => {
      expect(screen.getByTestId("preferences-form")).toBeInTheDocument();
    });
  });

  it("calls api.put on save and shows success message", async () => {
    const user = userEvent.setup();
    const prefs = makePreferences();
    vi.mocked(api.get).mockResolvedValue(prefs);
    vi.mocked(api.put).mockResolvedValue(prefs);

    render(<SettingsPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByTestId("preferences-form")).toBeInTheDocument();
    });

    await user.click(screen.getByText("Save Preferences"));

    await waitFor(() => {
      expect(api.put).toHaveBeenCalledWith(
        "/config/preferences",
        expect.objectContaining({ job_titles: expect.any(Array) }),
      );
    });

    await waitFor(() => {
      expect(screen.getByText("Preferences saved successfully!")).toBeInTheDocument();
    });
  });

  it("shows error message when save fails", async () => {
    const user = userEvent.setup();
    const prefs = makePreferences();
    vi.mocked(api.get).mockResolvedValue(prefs);
    vi.mocked(api.put).mockRejectedValue(new Error("Save failed"));

    render(<SettingsPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByTestId("preferences-form")).toBeInTheDocument();
    });

    await user.click(screen.getByText("Save Preferences"));

    await waitFor(() => {
      expect(screen.getByText("Failed to save preferences.")).toBeInTheDocument();
    });
  });
});
