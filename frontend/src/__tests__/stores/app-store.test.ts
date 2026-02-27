import { describe, expect, it, beforeEach } from "vitest";
import { useAppStore } from "../../stores/app-store";

describe("useAppStore", () => {
  beforeEach(() => {
    // Reset store between tests
    useAppStore.setState({
      filters: {},
      selectedJobId: null,
      sidebarOpen: true,
    });
  });

  it("has empty filters by default", () => {
    const state = useAppStore.getState();
    expect(state.filters).toEqual({});
  });

  it("setFilters updates state", () => {
    useAppStore.getState().setFilters({ location: "Remote" });
    expect(useAppStore.getState().filters.location).toBe("Remote");
  });

  it("setFilters merges with existing filters", () => {
    useAppStore.getState().setFilters({ location: "Remote" });
    useAppStore.getState().setFilters({ q: "Python" });
    const filters = useAppStore.getState().filters;
    expect(filters.location).toBe("Remote");
    expect(filters.q).toBe("Python");
  });

  it("setSelectedJob sets job id", () => {
    useAppStore.getState().setSelectedJob(5);
    expect(useAppStore.getState().selectedJobId).toBe(5);
  });

  it("setSelectedJob can clear selection", () => {
    useAppStore.getState().setSelectedJob(5);
    useAppStore.getState().setSelectedJob(null);
    expect(useAppStore.getState().selectedJobId).toBeNull();
  });

  it("toggleSidebar toggles state", () => {
    expect(useAppStore.getState().sidebarOpen).toBe(true);
    useAppStore.getState().toggleSidebar();
    expect(useAppStore.getState().sidebarOpen).toBe(false);
    useAppStore.getState().toggleSidebar();
    expect(useAppStore.getState().sidebarOpen).toBe(true);
  });
});
