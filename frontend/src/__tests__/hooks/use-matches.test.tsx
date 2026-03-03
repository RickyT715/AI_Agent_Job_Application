import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import type { ReactNode } from "react";

// Mock api client
vi.mock("../../api/client", () => ({
  api: {
    get: vi.fn(),
  },
}));

import { api } from "../../api/client";
import { useMatches, useMatch } from "../../hooks/use-matches";
import { makeMatches, makeMatch } from "../mocks/data";

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
  };
}

describe("useMatches", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("calls api.get with /matches when filters are empty", async () => {
    const matches = makeMatches(3);
    vi.mocked(api.get).mockResolvedValue({
      items: matches,
      total: 3,
      limit: 20,
      offset: 0,
    });

    const { result } = renderHook(() => useMatches({}), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(api.get).toHaveBeenCalledWith("/matches");
  });

  it("passes q filter as query param", async () => {
    vi.mocked(api.get).mockResolvedValue({
      items: [],
      total: 0,
      limit: 20,
      offset: 0,
    });

    const { result } = renderHook(
      () => useMatches({ q: "python" }),
      { wrapper: createWrapper() },
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(api.get).toHaveBeenCalledWith(
      expect.stringContaining("q=python"),
    );
  });

  it("passes location filter as query param", async () => {
    vi.mocked(api.get).mockResolvedValue({
      items: [],
      total: 0,
      limit: 20,
      offset: 0,
    });

    const { result } = renderHook(
      () => useMatches({ location: "Remote" }),
      { wrapper: createWrapper() },
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(api.get).toHaveBeenCalledWith(
      expect.stringContaining("location=Remote"),
    );
  });

  it("passes workplace_type filter as query param", async () => {
    vi.mocked(api.get).mockResolvedValue({
      items: [],
      total: 0,
      limit: 20,
      offset: 0,
    });

    const { result } = renderHook(
      () => useMatches({ workplace_type: "hybrid" }),
      { wrapper: createWrapper() },
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(api.get).toHaveBeenCalledWith(
      expect.stringContaining("workplace_type=hybrid"),
    );
  });

  it("passes min_score filter as query param", async () => {
    vi.mocked(api.get).mockResolvedValue({
      items: [],
      total: 0,
      limit: 20,
      offset: 0,
    });

    const { result } = renderHook(
      () => useMatches({ min_score: 7 }),
      { wrapper: createWrapper() },
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(api.get).toHaveBeenCalledWith(
      expect.stringContaining("min_score=7"),
    );
  });

  it("combines multiple filters into query string", async () => {
    vi.mocked(api.get).mockResolvedValue({
      items: [],
      total: 0,
      limit: 20,
      offset: 0,
    });

    const { result } = renderHook(
      () => useMatches({ q: "react", location: "NYC", min_score: 5 }),
      { wrapper: createWrapper() },
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    const calledUrl = vi.mocked(api.get).mock.calls[0][0];
    expect(calledUrl).toContain("q=react");
    expect(calledUrl).toContain("location=NYC");
    expect(calledUrl).toContain("min_score=5");
  });

  it("does not add params for undefined filter values", async () => {
    vi.mocked(api.get).mockResolvedValue({
      items: [],
      total: 0,
      limit: 20,
      offset: 0,
    });

    const { result } = renderHook(
      () => useMatches({ q: undefined, location: undefined }),
      { wrapper: createWrapper() },
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    // No query string when all filters are undefined
    expect(api.get).toHaveBeenCalledWith("/matches");
  });

  it("returns match data on success", async () => {
    const matches = makeMatches(2);
    vi.mocked(api.get).mockResolvedValue({
      items: matches,
      total: 2,
      limit: 20,
      offset: 0,
    });

    const { result } = renderHook(() => useMatches({}), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.items).toHaveLength(2);
    expect(result.current.data?.total).toBe(2);
  });
});

describe("useMatch", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("fetches single match by id", async () => {
    const match = makeMatch({ id: 42 });
    vi.mocked(api.get).mockResolvedValue(match);

    const { result } = renderHook(() => useMatch(42), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(api.get).toHaveBeenCalledWith("/matches/42");
    expect(result.current.data?.id).toBe(42);
  });

  it("does not fetch when id is null", () => {
    const { result } = renderHook(() => useMatch(null), {
      wrapper: createWrapper(),
    });

    // Query should not be enabled
    expect(result.current.fetchStatus).toBe("idle");
    expect(api.get).not.toHaveBeenCalled();
  });
});
