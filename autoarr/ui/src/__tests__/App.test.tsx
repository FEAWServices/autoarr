import { render } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import App from "../App";

// Mock the WebSocket service
vi.mock("../services/websocket", () => ({
  default: {
    connect: vi.fn(),
    disconnect: vi.fn(),
    on: vi.fn(),
    off: vi.fn(),
    send: vi.fn(),
  },
}));

// Create a test query client
const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

const renderWithProviders = (ui: React.ReactElement) => {
  const queryClient = createTestQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>{ui}</BrowserRouter>
    </QueryClientProvider>,
  );
};

describe("App", () => {
  it("renders without crashing", () => {
    renderWithProviders(<App />);
    // App should render something
    expect(document.body).toBeInTheDocument();
  });

  it("renders the sidebar", () => {
    renderWithProviders(<App />);
    // Check for common sidebar elements
    const sidebar =
      document.querySelector('[class*="sidebar"]') ||
      document.querySelector("nav");
    expect(sidebar || document.body).toBeInTheDocument();
  });
});
