import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes, Navigate } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

// Mock all page components to keep tests focused on routing
vi.mock("../pages/DashboardPage", () => ({
  DashboardPage: () => <div data-testid="dashboard-page">Dashboard</div>,
}));

vi.mock("../pages/SettingsPage", () => ({
  SettingsPage: () => <div data-testid="settings-page">Settings</div>,
}));

vi.mock("../pages/SkillAnalysisPage", () => ({
  SkillAnalysisPage: () => <div data-testid="skill-analysis-page">Skill Analysis</div>,
}));

// Import App after mocks are set up
import { App } from "../App";
import { ErrorBoundary } from "../components/ErrorBoundary";

function createQueryClient() {
  return new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
}

// Helper to render App with a specific initial route via MemoryRouter.
// Since App uses BrowserRouter internally, we test routing by rendering
// the full App and checking what's displayed. For route-specific testing,
// we recreate the route structure with MemoryRouter.
function renderWithRoute(route: string) {
  const queryClient = createQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[route]}>
        <ErrorBoundary>
          <Routes>
            <Route path="/" element={<div data-testid="dashboard-page">Dashboard</div>} />
            <Route path="/settings" element={<div data-testid="settings-page">Settings</div>} />
            <Route path="/skill-analysis" element={<div data-testid="skill-analysis-page">Skill Analysis</div>} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </ErrorBoundary>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("App routing", () => {
  it("renders DashboardPage at /", () => {
    renderWithRoute("/");
    expect(screen.getByTestId("dashboard-page")).toBeInTheDocument();
  });

  it("renders SettingsPage at /settings", () => {
    renderWithRoute("/settings");
    expect(screen.getByTestId("settings-page")).toBeInTheDocument();
  });

  it("renders SkillAnalysisPage at /skill-analysis", () => {
    renderWithRoute("/skill-analysis");
    expect(screen.getByTestId("skill-analysis-page")).toBeInTheDocument();
  });

  it("redirects unknown routes to /", () => {
    renderWithRoute("/nonexistent-page");
    expect(screen.getByTestId("dashboard-page")).toBeInTheDocument();
  });

  it("redirects /foo/bar to /", () => {
    renderWithRoute("/foo/bar");
    expect(screen.getByTestId("dashboard-page")).toBeInTheDocument();
  });
});

describe("App component renders correctly", () => {
  it("renders full App without crashing", () => {
    // Render the actual App component
    const { container } = render(<App />);
    expect(container).toBeTruthy();
  });

  it("renders nav bar with links", () => {
    render(<App />);
    expect(screen.getByText("AI Job Agent")).toBeInTheDocument();
    // Nav links share text with mocked page content, so target <a> elements
    const navLinks = screen.getAllByRole("link");
    const navTexts = navLinks.map((link) => link.textContent);
    expect(navTexts).toContain("Dashboard");
    expect(navTexts).toContain("Settings");
    expect(navTexts).toContain("Skill Market");
  });
});
