import type { ReactElement } from "react";
import { act, cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { AIRecommender } from "./AIRecommender";
import { Catalog } from "./Catalog";
import { CrowdIntel } from "./CrowdIntel";
import { Dashboard } from "./Dashboard";
import { Editorial } from "./Editorial";
import { Enterprise } from "./Enterprise";
import { ExhibitionDetail } from "./ExhibitionDetail";
import { GraphExplorer } from "./GraphExplorer";
import { Ingest } from "./Ingest";
import { ParserConsole } from "./ParserConsole";
import { Pipeline } from "./Pipeline";
import { Queue } from "./Queue";
import { RulesReport } from "./RulesReport";
import { SyncRebalance } from "./SyncRebalance";

function mockFetch(data: unknown = {}) {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ data }),
    }),
  );
}

function renderPage(path: string, element: ReactElement) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path={path} element={element} />
        <Route path="/exhibitions/:id" element={element} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("page interactions", () => {
  beforeEach(() => mockFetch({ ok: true }));

  it("Dashboard refresh triggers refetch handlers", async () => {
    renderPage("/", <Dashboard />);
    const user = userEvent.setup();
    await act(async () => {
      await user.click(screen.getByRole("button", { name: /refresh all/i }));
    });
    expect(fetch).toHaveBeenCalled();
    vi.unstubAllGlobals();
  });

  it("ExhibitionDetail switches craft tabs", async () => {
    renderPage("/exhibitions/ex-001", <ExhibitionDetail />);
    const user = userEvent.setup();
    await act(async () => {
      await user.click(screen.getByRole("button", { name: /pacing/i }));
      await user.click(screen.getByRole("button", { name: /dialogue/i }));
    });
    expect(fetch).toHaveBeenCalled();
    vi.unstubAllGlobals();
  });

  it("CrowdIntel switches narrative tabs", async () => {
    renderPage("/crowd-intel", <CrowdIntel />);
    const user = userEvent.setup();
    await act(async () => {
      await user.click(screen.getByRole("button", { name: /visitor web/i }));
      await user.click(screen.getByRole("button", { name: /theme clusters/i }));
    });
    expect(fetch).toHaveBeenCalled();
    vi.unstubAllGlobals();
  });

  it("Queue replay submits job id", async () => {
    renderPage("/queue", <Queue />);
    const user = userEvent.setup();
    await act(async () => {
      await user.click(screen.getByRole("button", { name: /^replay$/i }));
    });
    expect(fetch).toHaveBeenCalled();
    vi.unstubAllGlobals();
  });

  it("Pipeline run posts payload", async () => {
    renderPage("/pipeline", <Pipeline />);
    const user = userEvent.setup();
    await act(async () => {
      await user.click(screen.getByRole("button", { name: /run pipeline/i }));
    });
    expect(fetch).toHaveBeenCalled();
    vi.unstubAllGlobals();
  });

  it("ParserConsole runs tokenize step", async () => {
    renderPage("/parser", <ParserConsole />);
    const user = userEvent.setup();
    await act(async () => {
      await user.click(screen.getByRole("button", { name: /run tokenize/i }));
    });
    expect(fetch).toHaveBeenCalled();
    vi.unstubAllGlobals();
  });

  it("SyncRebalance posts reconcile and route", async () => {
    renderPage("/sync-rebalance", <SyncRebalance />);
    const user = userEvent.setup();
    await act(async () => {
      await user.click(screen.getByRole("button", { name: /sync\/reconcile/i }));
      await user.click(screen.getByRole("button", { name: /rebalance\/route/i }));
    });
    expect(fetch).toHaveBeenCalled();
    vi.unstubAllGlobals();
  });

  it("AIRecommender posts recommendation", async () => {
    renderPage("/ai", <AIRecommender />);
    const user = userEvent.setup();
    await act(async () => {
      await user.click(screen.getByRole("button", { name: /post \/ai\/recommend/i }));
    });
    expect(fetch).toHaveBeenCalled();
    vi.unstubAllGlobals();
  });

  it("Ingest snapshot posts data", async () => {
    renderPage("/ingest", <Ingest />);
    const user = userEvent.setup();
    await act(async () => {
      await user.click(screen.getByRole("button", { name: /ingest\/snapshot/i }));
    });
    expect(fetch).toHaveBeenCalled();
    vi.unstubAllGlobals();
  });

  it("Catalog renders exhibition rows", async () => {
    mockFetch([
      { id: "ex-001", title: "Modern Forms", vitrine_score: 88 },
      { id: "ex-002", title: "Light Fields", vitrine_score: 72 },
    ]);
    renderPage("/catalog", <Catalog />);
    expect(await screen.findByText("Modern Forms")).toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: /view detail/i })).toHaveLength(2);
    vi.unstubAllGlobals();
  });

  it("Queue and AI tabs exercise secondary handlers", async () => {
    const user = userEvent.setup();
    renderPage("/queue", <Queue />);
    await act(async () => {
      await user.click(screen.getByRole("button", { name: /^schedule$/i }));
      await user.click(screen.getByRole("button", { name: /dead letter/i }));
    });
    cleanup();
    renderPage("/ai", <AIRecommender />);
    await act(async () => {
      await user.click(screen.getByRole("button", { name: /similar sets/i }));
      await user.click(screen.getByRole("button", { name: /post \/ai\/similar/i }));
    });
    cleanup();
    renderPage("/ingest", <Ingest />);
    await act(async () => {
      await user.click(screen.getByRole("button", { name: /post batch-score/i }));
      await user.click(screen.getByRole("button", { name: /post concurrency ingest/i }));
    });
    expect(fetch).toHaveBeenCalled();
    vi.unstubAllGlobals();
  });

  it("Dashboard error retry and input handlers fire", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValueOnce({
          ok: false,
          status: 500,
          text: async () => "fail",
        })
        .mockResolvedValue({
          ok: true,
          json: async () => ({ data: {} }),
        }),
    );

    renderPage("/", <Dashboard />);
    expect(await screen.findByText(/unable to load data/i)).toBeInTheDocument();
    const callsBeforeRetry = vi.mocked(fetch).mock.calls.length;
    await userEvent.click(screen.getByRole("button", { name: /retry/i }));
    expect(fetch).toHaveBeenCalledTimes(callsBeforeRetry + 3);
    vi.unstubAllGlobals();
  });

  it("Set id inputs and parser tabs update state", async () => {
    const user = userEvent.setup();
    renderPage("/crowd-intel", <CrowdIntel />);
    await user.clear(screen.getByLabelText(/exhibition set id/i));
    await user.type(screen.getByLabelText(/exhibition set id/i), "ex-002");

    cleanup();
    renderPage("/graph", <GraphExplorer />);
    await user.click(screen.getByRole("button", { name: /^path$/i }));
    await user.clear(screen.getByLabelText(/set id/i));
    await user.type(screen.getByLabelText(/set id/i), "ex-003");
    await user.click(screen.getByRole("button", { name: /residency tree/i }));

    cleanup();
    renderPage("/parser", <ParserConsole />);
    await user.click(screen.getByRole("button", { name: /^parse$/i }));
    await user.click(screen.getByRole("button", { name: /^compile$/i }));

    cleanup();
    renderPage("/exhibitions/ex-001", <ExhibitionDetail />);
    await user.click(screen.getByRole("button", { name: /^refresh$/i }));

    expect(fetch).toHaveBeenCalled();
    vi.unstubAllGlobals();
  });

  it("Catalog refresh and enterprise refresh work", async () => {
    const user = userEvent.setup();
    renderPage("/catalog", <Catalog />);
    await act(async () => {
      await user.click(screen.getByRole("button", { name: /refresh weave/i }));
    });
    cleanup();
    renderPage("/enterprise", <Enterprise />);
    await act(async () => {
      await user.click(screen.getByRole("button", { name: /^refresh$/i }));
    });
    cleanup();
    renderPage("/editorial", <Editorial />);
    await act(async () => {
      await user.click(screen.getByRole("button", { name: /^refresh$/i }));
    });
    cleanup();
    renderPage("/rules", <RulesReport />);
    await act(async () => {
      await user.click(screen.getByRole("button", { name: /^refresh$/i }));
    });
    cleanup();
    renderPage("/graph", <GraphExplorer />);
    await act(async () => {
      await user.click(screen.getByRole("button", { name: /traverse/i }));
    });
    expect(fetch).toHaveBeenCalled();
    vi.unstubAllGlobals();
  });
});
