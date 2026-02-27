/** Global UI state store using Zustand. */

import { create } from "zustand";

export interface Filters {
  q?: string;
  location?: string;
  workplace_type?: string;
  min_score?: number;
}

interface AppState {
  filters: Filters;
  selectedJobId: number | null;
  sidebarOpen: boolean;
  setFilters: (filters: Partial<Filters>) => void;
  setSelectedJob: (id: number | null) => void;
  toggleSidebar: () => void;
}

export const useAppStore = create<AppState>((set) => ({
  filters: {},
  selectedJobId: null,
  sidebarOpen: true,
  setFilters: (filters) =>
    set((state) => ({ filters: { ...state.filters, ...filters } })),
  setSelectedJob: (id) => set({ selectedJobId: id }),
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
}));
