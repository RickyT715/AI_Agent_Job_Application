import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Link, Route, Routes, useLocation } from "react-router-dom";
import { DashboardPage } from "./pages/DashboardPage";
import { SettingsPage } from "./pages/SettingsPage";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false },
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
            <Routes>
              <Route path="/" element={<DashboardPage />} />
              <Route path="/settings" element={<SettingsPage />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
