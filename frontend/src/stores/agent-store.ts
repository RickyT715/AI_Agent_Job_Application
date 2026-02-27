/** Agent status state store. */

import { create } from "zustand";
import type { AgentStatusMessage } from "../types/api";

interface AgentState {
  isRunning: boolean;
  currentStep: string;
  progress: number;
  status: string;
  message: string;
  fieldsFilled: Record<string, string>;
  screenshotB64: string | null;
  threadId: string | null;
  setStatus: (msg: Partial<AgentStatusMessage>) => void;
  setThreadId: (id: string) => void;
  reset: () => void;
}

const initialState = {
  isRunning: false,
  currentStep: "",
  progress: 0,
  status: "idle",
  message: "",
  fieldsFilled: {},
  screenshotB64: null,
  threadId: null,
};

export const useAgentStore = create<AgentState>((set) => ({
  ...initialState,
  setStatus: (msg) =>
    set({
      isRunning: msg.status !== "submitted" && msg.status !== "failed",
      currentStep: msg.step ?? "",
      progress: msg.progress ?? 0,
      status: msg.status ?? "",
      message: msg.message ?? "",
      fieldsFilled: msg.fields_filled ?? {},
      screenshotB64: msg.screenshot_b64 ?? null,
    }),
  setThreadId: (id) => set({ threadId: id }),
  reset: () => set(initialState),
}));
