import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import App, { AppRoutes } from "./App";

describe("App", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ data: {} }),
      }),
    );
  });

  it("renders Vitrine brand and navigation", async () => {
    render(
      <MemoryRouter initialEntries={["/"]}>
        <AppRoutes />
      </MemoryRouter>,
    );

    expect(screen.getByText("Vitrine")).toBeInTheDocument();
    expect(screen.getByText("Command Center")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Catalog" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "AI Recommender" })).toBeInTheDocument();

    await waitFor(() => {
      expect(fetch).toHaveBeenCalled();
    });

    vi.unstubAllGlobals();
  });

  it("default App export renders router shell", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ data: {} }),
      }),
    );

    render(<App />);
    expect(screen.getByText("Vitrine")).toBeInTheDocument();
    await waitFor(() => expect(fetch).toHaveBeenCalled());
    vi.unstubAllGlobals();
  });
});
