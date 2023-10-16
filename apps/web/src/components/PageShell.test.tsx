import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { ErrorBanner } from "./PageShell";

describe("PageShell helpers", () => {
  it("ErrorBanner retry invokes callback", async () => {
    const onRetry = vi.fn();
    render(<ErrorBanner message="Network down" onRetry={onRetry} />);
    await userEvent.click(screen.getByRole("button", { name: /retry/i }));
    expect(onRetry).toHaveBeenCalledOnce();
  });
});
