import { describe, expect, it, beforeEach } from "vitest";
import { useAgentStore } from "../../stores/agent-store";

describe("useAgentStore", () => {
  beforeEach(() => {
    useAgentStore.getState().reset();
  });

  it("starts in idle state", () => {
    const state = useAgentStore.getState();
    expect(state.isRunning).toBe(false);
    expect(state.status).toBe("idle");
    expect(state.currentStep).toBe("");
  });

  it("setStatus updates all fields", () => {
    useAgentStore.getState().setStatus({
      step: "fill_fields",
      status: "filling",
      progress: 0.5,
      message: "Filling form fields...",
      fields_filled: { email: "test@test.com" },
      screenshot_b64: "base64data",
    });

    const state = useAgentStore.getState();
    expect(state.isRunning).toBe(true);
    expect(state.currentStep).toBe("fill_fields");
    expect(state.progress).toBe(0.5);
    expect(state.status).toBe("filling");
    expect(state.message).toBe("Filling form fields...");
    expect(state.fieldsFilled).toEqual({ email: "test@test.com" });
    expect(state.screenshotB64).toBe("base64data");
  });

  it("setStatus marks not running on submitted", () => {
    useAgentStore.getState().setStatus({ status: "submitted", step: "submit", progress: 1 });
    expect(useAgentStore.getState().isRunning).toBe(false);
  });

  it("setStatus marks not running on failed", () => {
    useAgentStore.getState().setStatus({ status: "failed", step: "error", progress: 0.3 });
    expect(useAgentStore.getState().isRunning).toBe(false);
  });

  it("setThreadId sets thread id", () => {
    useAgentStore.getState().setThreadId("thread-abc");
    expect(useAgentStore.getState().threadId).toBe("thread-abc");
  });

  it("reset returns to initial state", () => {
    useAgentStore.getState().setStatus({
      step: "navigate",
      status: "navigating",
      progress: 0.2,
    });
    useAgentStore.getState().setThreadId("t-1");
    useAgentStore.getState().reset();

    const state = useAgentStore.getState();
    expect(state.isRunning).toBe(false);
    expect(state.status).toBe("idle");
    expect(state.threadId).toBeNull();
    expect(state.progress).toBe(0);
  });
});
