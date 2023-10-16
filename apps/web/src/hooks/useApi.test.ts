import { act, renderHook, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { apiGet, apiPost } from "../api/client";
import { useApi, useMutation } from "./useApi";

describe("useApi", () => {
  it("loads data on mount", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ data: { loaded: true } }),
      }),
    );

    const { result } = renderHook(() => useApi(() => apiGet("/v1/weave")));

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.data).toEqual({ loaded: true });
    expect(result.current.error).toBeNull();

    vi.unstubAllGlobals();
  });

  it("captures errors", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        text: async () => "fail",
      }),
    );

    const { result } = renderHook(() => useApi(() => apiGet("/v1/weave")));

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.error).toBeTruthy();

    vi.unstubAllGlobals();
  });

  it("refetch reloads data", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ data: { count: 1 } }),
      }),
    );

    const { result } = renderHook(() => useApi(() => apiGet("/v1/weave")));
    await waitFor(() => expect(result.current.loading).toBe(false));

    act(() => {
      result.current.refetch();
    });
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(2));

    vi.unstubAllGlobals();
  });
});

describe("useMutation", () => {
  it("runs mutator on demand", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ data: { posted: true } }),
      }),
    );

    const { result } = renderHook(() =>
      useMutation((body: string) => apiPost("/v1/pipeline/run", { body })),
    );

    await act(async () => {
      await result.current.mutate("test");
    });
    await waitFor(() => expect(result.current.data).toEqual({ posted: true }));

    vi.unstubAllGlobals();
  });

  it("records mutation errors", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 400,
        text: async () => "bad request",
      }),
    );

    const { result } = renderHook(() =>
      useMutation(() => apiPost("/v1/pipeline/run", {})),
    );

    await act(async () => {
      await expect(result.current.mutate()).rejects.toThrow();
    });
    await waitFor(() => expect(result.current.error).toBeTruthy());

    vi.unstubAllGlobals();
  });
});
