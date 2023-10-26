import type { ReactElement } from "react";
import { render, screen, waitFor } from "@testing-library/react";
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

const PAGE_CASES: Array<{
  name: string;
  path: string;
  element: ReactElement;
  heading: RegExp | string;
  fetchOnMount?: boolean;
}> = [
  { name: "Dashboard", path: "/", element: <Dashboard />, heading: /Command Center/i },
  { name: "Catalog", path: "/catalog", element: <Catalog />, heading: /Exhibition Catalog/i },
  {
    name: "ExhibitionDetail",
    path: "/exhibitions/ex-001",
    element: <ExhibitionDetail />,
    heading: /Exhibition Detail/i,
  },
  { name: "CrowdIntel", path: "/crowd-intel", element: <CrowdIntel />, heading: /Crowd Intelligence/i },
  { name: "Queue", path: "/queue", element: <Queue />, heading: /Job Queue/i },
  {
    name: "Pipeline",
    path: "/pipeline",
    element: <Pipeline />,
    heading: /Pipeline Runner/i,
    fetchOnMount: false,
  },
  { name: "Enterprise", path: "/enterprise", element: <Enterprise />, heading: /^Enterprise$/i },
  { name: "GraphExplorer", path: "/graph", element: <GraphExplorer />, heading: /Graph Explorer/i },
  {
    name: "ParserConsole",
    path: "/parser",
    element: <ParserConsole />,
    heading: /Parser Console/i,
    fetchOnMount: false,
  },
  { name: "Ingest", path: "/ingest", element: <Ingest />, heading: /^Ingest$/i },
  { name: "RulesReport", path: "/rules", element: <RulesReport />, heading: /Rules Report/i },
  {
    name: "SyncRebalance",
    path: "/sync-rebalance",
    element: <SyncRebalance />,
    heading: /Sync & Rebalance/i,
    fetchOnMount: false,
  },
  { name: "Editorial", path: "/editorial", element: <Editorial />, heading: /^Editorial$/i },
  { name: "AIRecommender", path: "/ai", element: <AIRecommender />, heading: /AI Recommender/i },
];

describe("page smoke tests", () => {
  beforeEach(() => {
    mockFetch({ ok: true, items: [] });
  });

  it.each(PAGE_CASES)("$name renders and loads data", async ({ element, path, heading, fetchOnMount = true }) => {
    render(
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route path={path} element={element} />
          <Route path="/exhibitions/:id" element={element} />
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByRole("heading", { name: heading })).toBeInTheDocument();
    if (fetchOnMount) {
      await waitFor(() => expect(fetch).toHaveBeenCalled());
    }
    vi.unstubAllGlobals();
  });
});
