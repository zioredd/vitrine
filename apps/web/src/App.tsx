import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { AIRecommender } from "./pages/AIRecommender";
import { Catalog } from "./pages/Catalog";
import { CrowdIntel } from "./pages/CrowdIntel";
import { Dashboard } from "./pages/Dashboard";
import { Editorial } from "./pages/Editorial";
import { Enterprise } from "./pages/Enterprise";
import { ExhibitionDetail } from "./pages/ExhibitionDetail";
import { GraphExplorer } from "./pages/GraphExplorer";
import { Ingest } from "./pages/Ingest";
import { ParserConsole } from "./pages/ParserConsole";
import { Pipeline } from "./pages/Pipeline";
import { Queue } from "./pages/Queue";
import { RulesReport } from "./pages/RulesReport";
import { SyncRebalance } from "./pages/SyncRebalance";

export function AppRoutes() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="catalog" element={<Catalog />} />
        <Route path="exhibitions/:id" element={<ExhibitionDetail />} />
        <Route path="crowd-intel" element={<CrowdIntel />} />
        <Route path="queue" element={<Queue />} />
        <Route path="pipeline" element={<Pipeline />} />
        <Route path="enterprise" element={<Enterprise />} />
        <Route path="graph" element={<GraphExplorer />} />
        <Route path="parser" element={<ParserConsole />} />
        <Route path="ingest" element={<Ingest />} />
        <Route path="rules" element={<RulesReport />} />
        <Route path="sync-rebalance" element={<SyncRebalance />} />
        <Route path="editorial" element={<Editorial />} />
        <Route path="ai" element={<AIRecommender />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppRoutes />
    </BrowserRouter>
  );
}
