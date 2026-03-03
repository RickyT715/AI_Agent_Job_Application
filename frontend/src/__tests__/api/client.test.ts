import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { api } from "../../api/client";

// Save original fetch
const originalFetch = globalThis.fetch;

describe("api client", () => {
  let mockFetch: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    mockFetch = vi.fn();
    globalThis.fetch = mockFetch;
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  describe("get", () => {
    it("sends GET request with correct URL and headers", async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ data: "test" }),
      });

      const result = await api.get<{ data: string }>("/matches");

      expect(mockFetch).toHaveBeenCalledWith(
        "/api/matches",
        expect.objectContaining({
          headers: expect.objectContaining({
            "Content-Type": "application/json",
            "X-API-Key": "",
          }),
        }),
      );
      expect(result).toEqual({ data: "test" });
    });
  });

  describe("post", () => {
    it("sends POST request with JSON body", async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ id: 1 }),
      });

      await api.post("/agent/start", { resume: "test" });

      expect(mockFetch).toHaveBeenCalledWith(
        "/api/agent/start",
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({ resume: "test" }),
          headers: expect.objectContaining({
            "Content-Type": "application/json",
          }),
        }),
      );
    });

    it("sends POST request without body when none provided", async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ status: "ok" }),
      });

      await api.post("/agent/start");

      expect(mockFetch).toHaveBeenCalledWith(
        "/api/agent/start",
        expect.objectContaining({
          method: "POST",
          body: undefined,
        }),
      );
    });
  });

  describe("put", () => {
    it("sends PUT request with JSON body", async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ updated: true }),
      });

      await api.put("/config/preferences", { job_titles: ["Engineer"] });

      expect(mockFetch).toHaveBeenCalledWith(
        "/api/config/preferences",
        expect.objectContaining({
          method: "PUT",
          body: JSON.stringify({ job_titles: ["Engineer"] }),
          headers: expect.objectContaining({
            "Content-Type": "application/json",
          }),
        }),
      );
    });
  });

  describe("delete", () => {
    it("sends DELETE request", async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ deleted: true }),
      });

      await api.delete("/resumes/1");

      expect(mockFetch).toHaveBeenCalledWith(
        "/api/resumes/1",
        expect.objectContaining({
          method: "DELETE",
          headers: expect.objectContaining({
            "Content-Type": "application/json",
          }),
        }),
      );
    });
  });

  describe("download", () => {
    it("sends GET request and returns blob", async () => {
      const mockBlob = new Blob(["pdf-content"], { type: "application/pdf" });
      mockFetch.mockResolvedValue({
        ok: true,
        blob: () => Promise.resolve(mockBlob),
      });

      const result = await api.download("/skill-analysis/report/pdf");

      expect(mockFetch).toHaveBeenCalledWith(
        "/api/skill-analysis/report/pdf",
        expect.objectContaining({
          headers: expect.objectContaining({
            "X-API-Key": "",
          }),
        }),
      );
      expect(result).toBe(mockBlob);
    });

    it("does not include Content-Type header in download", async () => {
      const mockBlob = new Blob(["data"]);
      mockFetch.mockResolvedValue({
        ok: true,
        blob: () => Promise.resolve(mockBlob),
      });

      await api.download("/resumes/1/pdf");

      const callHeaders = mockFetch.mock.calls[0][1].headers;
      expect(callHeaders).not.toHaveProperty("Content-Type");
    });
  });

  describe("error handling", () => {
    it("throws on non-ok response for get", async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 404,
        statusText: "Not Found",
      });

      await expect(api.get("/nonexistent")).rejects.toThrow(
        "API error: 404 Not Found",
      );
    });

    it("throws on non-ok response for post", async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 500,
        statusText: "Internal Server Error",
      });

      await expect(api.post("/agent/start", {})).rejects.toThrow(
        "API error: 500 Internal Server Error",
      );
    });

    it("throws on non-ok response for download", async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 403,
        statusText: "Forbidden",
      });

      await expect(api.download("/secret")).rejects.toThrow(
        "API error: 403 Forbidden",
      );
    });

    it("includes X-API-Key header from env", async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({}),
      });

      await api.get("/test");

      const callHeaders = mockFetch.mock.calls[0][1].headers;
      expect(callHeaders).toHaveProperty("X-API-Key");
    });
  });
});
