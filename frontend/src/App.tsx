import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Link, Navigate, Route, Routes, useLocation } from "react-router-dom";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { DashboardPage } from "./pages/DashboardPage";
import { SettingsPage } from "./pages/SettingsPage";
import { SkillAnalysisPage } from "./pages/SkillAnalysisPage";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 2, staleTime: 30_000 },
  },
});

function NavBar() {
  const location = useLocation();

  return (
    <nav>
      <span className="nav-brand">AI Job Agent</span>
      <Link to="/" className={location.pathname === "/" ? "active" : ""}>
        Dashboard
      </Link>
      <Link to="/settings" className={location.pathname === "/settings" ? "active" : ""}>
        Settings
      </Link>
      <Link to="/skill-analysis" className={location.pathname === "/skill-analysis" ? "active" : ""}>
        Skill Market
      </Link>
    </nav>
  );
}

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="app">
          <NavBar />
          <main>
            <ErrorBoundary>
              <Routes>
                <Route path="/" element={<DashboardPage />} />
                <Route path="/settings" element={<SettingsPage />} />
                <Route path="/skill-analysis" element={<SkillAnalysisPage />} />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </ErrorBoundary>
          </main>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
