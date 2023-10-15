import { describe, expect, it } from "vitest";
import { ApiError, apiClient, apiGet, apiPost } from "./client";

describe("apiClient", () => {
  it("unwraps { data } envelope", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ data: { score: 42 } }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const result = await apiClient<{ score: number }>("/v1/weave");
    expect(result).toEqual({ score: 42 });
    expect(fetchMock).toHaveBeenCalledWith(
      "/v1/weave",
      expect.objectContaining({ method: "GET" }),
    );

    vi.unstubAllGlobals();
  });

  it("throws ApiError on non-ok response", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        text: async () => "Server error",
      }),
    );

    await expect(apiClient("/v1/weave")).rejects.toBeInstanceOf(ApiError);
    vi.unstubAllGlobals();
  });

  it("apiPost sends JSON body", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ data: { ok: true } }),
    });
    vi.stubGlobal("fetch", fetchMock);

    await apiPost("/v1/pipeline/run", { stages: ["normalize"] });
    expect(fetchMock).toHaveBeenCalledWith(
      "/v1/pipeline/run",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ stages: ["normalize"] }),
      }),
    );

    vi.unstubAllGlobals();
  });

  it("apiGet delegates to apiClient", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ data: [1, 2] }),
      }),
    );

    const rows = await apiGet<number[]>("/v1/weave");
    expect(rows).toEqual([1, 2]);
    vi.unstubAllGlobals();
  });
});
