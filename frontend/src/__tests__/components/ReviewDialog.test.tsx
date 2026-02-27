import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { ReviewDialog } from "../../components/ReviewDialog";

const defaultProps = {
  fieldsFilled: { first_name: "John", email: "john@test.com", phone: "555-1234" },
  screenshotB64: null,
  onApprove: vi.fn(),
  onReject: vi.fn(),
  onEdit: vi.fn(),
};

describe("ReviewDialog", () => {
  it("shows filled fields", () => {
    render(<ReviewDialog {...defaultProps} />);
    expect(screen.getByText("first_name")).toBeInTheDocument();
    expect(screen.getByText("John")).toBeInTheDocument();
    expect(screen.getByText("email")).toBeInTheDocument();
    expect(screen.getByText("john@test.com")).toBeInTheDocument();
  });

  it("shows screenshot when provided", () => {
    render(<ReviewDialog {...defaultProps} screenshotB64="abc123" />);
    const img = screen.getByTestId("screenshot");
    expect(img).toBeInTheDocument();
    expect(img).toHaveAttribute("src", "data:image/png;base64,abc123");
  });

  it("does not show screenshot when null", () => {
    render(<ReviewDialog {...defaultProps} />);
    expect(screen.queryByTestId("screenshot")).not.toBeInTheDocument();
  });

  it("calls onApprove when Approve clicked", async () => {
    const user = userEvent.setup();
    const onApprove = vi.fn();
    render(<ReviewDialog {...defaultProps} onApprove={onApprove} />);
    await user.click(screen.getByTestId("approve-btn"));
    expect(onApprove).toHaveBeenCalledOnce();
  });

  it("calls onReject when Reject clicked", async () => {
    const user = userEvent.setup();
    const onReject = vi.fn();
    render(<ReviewDialog {...defaultProps} onReject={onReject} />);
    await user.click(screen.getByTestId("reject-btn"));
    expect(onReject).toHaveBeenCalledOnce();
  });

  it("enables field editing when Edit clicked", async () => {
    const user = userEvent.setup();
    render(<ReviewDialog {...defaultProps} />);
    await user.click(screen.getByTestId("edit-btn"));
    // In edit mode, fields become inputs
    const input = screen.getByLabelText("first_name");
    expect(input).toBeInTheDocument();
    expect(input).toHaveValue("John");
  });

  it("sends edited fields when Submit Changes clicked", async () => {
    const user = userEvent.setup();
    const onEdit = vi.fn();
    render(<ReviewDialog {...defaultProps} onEdit={onEdit} />);

    // Enter edit mode
    await user.click(screen.getByTestId("edit-btn"));

    // Change a field
    const input = screen.getByLabelText("first_name");
    await user.clear(input);
    await user.type(input, "Jane");

    // Submit
    await user.click(screen.getByText("Submit Changes"));
    expect(onEdit).toHaveBeenCalledWith(
      expect.objectContaining({ first_name: "Jane" }),
    );
  });
});
