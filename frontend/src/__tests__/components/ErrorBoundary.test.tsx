import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { ErrorBoundary } from "../../components/ErrorBoundary";

// Component that throws an error on render
function ThrowingComponent({ error }: { error: Error }) {
  throw error;
}

// Component that renders normally
function GoodComponent() {
  return <div data-testid="good-child">All is well</div>;
}

describe("ErrorBoundary", () => {
  // Suppress console.error from React and ErrorBoundary during expected error tests
  beforeEach(() => {
    vi.spyOn(console, "error").mockImplementation(() => {});
  });

  it("renders children when no error occurs", () => {
    render(
      <ErrorBoundary>
        <GoodComponent />
      </ErrorBoundary>,
    );

    expect(screen.getByTestId("good-child")).toBeInTheDocument();
    expect(screen.getByText("All is well")).toBeInTheDocument();
  });

  it("renders multiple children", () => {
    render(
      <ErrorBoundary>
        <div data-testid="child-1">First</div>
        <div data-testid="child-2">Second</div>
      </ErrorBoundary>,
    );

    expect(screen.getByTestId("child-1")).toBeInTheDocument();
    expect(screen.getByTestId("child-2")).toBeInTheDocument();
  });

  it("shows error fallback UI when child throws", () => {
    render(
      <ErrorBoundary>
        <ThrowingComponent error={new Error("Test crash")} />
      </ErrorBoundary>,
    );

    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
    expect(screen.getByText("Test crash")).toBeInTheDocument();
  });

  it("shows default message when error has no message", () => {
    const error = new Error();
    error.message = "";

    render(
      <ErrorBoundary>
        <ThrowingComponent error={error} />
      </ErrorBoundary>,
    );

    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
  });

  it("renders Try again button in error state", () => {
    render(
      <ErrorBoundary>
        <ThrowingComponent error={new Error("Oops")} />
      </ErrorBoundary>,
    );

    const button = screen.getByText("Try again");
    expect(button).toBeInTheDocument();
    expect(button.tagName).toBe("BUTTON");
  });

  it("recovers from error when Try again is clicked", async () => {
    const user = userEvent.setup();
    let shouldThrow = true;

    function MaybeThrow() {
      if (shouldThrow) {
        throw new Error("Intermittent error");
      }
      return <div data-testid="recovered">Recovered!</div>;
    }

    const { rerender } = render(
      <ErrorBoundary>
        <MaybeThrow />
      </ErrorBoundary>,
    );

    // Should show error state
    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
    expect(screen.getByText("Intermittent error")).toBeInTheDocument();

    // Fix the error condition before clicking Try again
    shouldThrow = false;

    await user.click(screen.getByText("Try again"));

    // After clicking Try again, ErrorBoundary resets state and re-renders children.
    // The component no longer throws so it renders successfully.
    expect(screen.getByTestId("recovered")).toBeInTheDocument();
    expect(screen.getByText("Recovered!")).toBeInTheDocument();
  });

  it("calls console.error when error is caught", () => {
    const errorSpy = vi.spyOn(console, "error").mockImplementation(() => {});

    render(
      <ErrorBoundary>
        <ThrowingComponent error={new Error("Logged error")} />
      </ErrorBoundary>,
    );

    expect(errorSpy).toHaveBeenCalled();
    const callArgs = errorSpy.mock.calls.find(
      (call) =>
        typeof call[0] === "string" &&
        call[0].includes("ErrorBoundary caught an error"),
    );
    expect(callArgs).toBeTruthy();
  });
});
