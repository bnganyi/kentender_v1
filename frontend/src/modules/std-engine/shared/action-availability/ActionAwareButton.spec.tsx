import "@testing-library/jest-dom/vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { SEC_API_ACTION_AVAILABILITY_METHOD } from "./constants";
import { ActionAwareButton } from "./ActionAwareButton";

function successMessage(overrides: Record<string, unknown>) {
	return {
		message: {
			success: true,
			actor_user_code: "Administrator",
			action_code: "PUBLISH_TENDER",
			allowed: true,
			message: "Allowed",
			required_permission: null,
			risk_level: "Low",
			requires_confirmation: false,
			audit_on_attempt: false,
			...overrides,
		},
	};
}

describe("ActionAwareButton", () => {
	afterEach(() => {
		vi.unstubAllGlobals();
		vi.restoreAllMocks();
	});

	it("loads then enables and runs onAllowedClick when allowed without confirmation", async () => {
		const onAllowedClick = vi.fn();
		vi.stubGlobal("frappe", {
			call: vi.fn(async () =>
				successMessage({
					action_code: "SUBMIT_PR",
					allowed: true,
					requires_confirmation: false,
					message: "OK",
				}),
			),
		});

		render(
			<ActionAwareButton
				actionCode="SUBMIT_PR"
				objectType="Purchase Requisition"
				objectCode="PR-1"
				label="Submit"
				onAllowedClick={onAllowedClick}
			/>,
		);

		expect(screen.getByTestId("action-aware-button-SUBMIT_PR")).toHaveAttribute("aria-busy", "true");

		await waitFor(() => {
			expect(screen.getByTestId("action-aware-button-SUBMIT_PR")).not.toBeDisabled();
		});
		fireEvent.click(screen.getByTestId("action-aware-button-SUBMIT_PR"));
		expect(onAllowedClick).toHaveBeenCalledTimes(1);

		const frappe = globalThis as { frappe?: { call: ReturnType<typeof vi.fn> } };
		expect(frappe.frappe?.call).toHaveBeenCalledWith(
			expect.objectContaining({
				method: SEC_API_ACTION_AVAILABILITY_METHOD,
				args: expect.objectContaining({
					action_code: "SUBMIT_PR",
					object_type: "Purchase Requisition",
					object_code: "PR-1",
				}),
			}),
		);
	});

	it("uses frappe.confirm before onAllowedClick when requires_confirmation", async () => {
		const onAllowedClick = vi.fn();
		let yes: (() => void) | undefined;
		vi.stubGlobal("frappe", {
			call: vi.fn(async () =>
				successMessage({
					action_code: "PUBLISH_TENDER",
					allowed: true,
					requires_confirmation: true,
					message: "Publishing is irreversible.",
				}),
			),
			confirm: vi.fn((_html: string, y?: () => void) => {
				yes = y;
			}),
		});

		render(
			<ActionAwareButton
				actionCode="PUBLISH_TENDER"
				objectType="Procurement Tender"
				objectCode="TND-1"
				label="Publish"
				confirmationTitle="Publish tender?"
				confirmationMessage="This cannot be undone."
				onAllowedClick={onAllowedClick}
			/>,
		);

		await waitFor(() => {
			expect(screen.getByTestId("action-aware-button-PUBLISH_TENDER")).not.toBeDisabled();
		});
		expect(screen.getByTestId("action-confirmation-PUBLISH_TENDER")).toBeInTheDocument();

		fireEvent.click(screen.getByTestId("action-aware-button-PUBLISH_TENDER"));
		const frappe = globalThis as { frappe?: { confirm: ReturnType<typeof vi.fn> } };
		expect(frappe.frappe?.confirm).toHaveBeenCalled();
		expect(onAllowedClick).not.toHaveBeenCalled();
		yes?.();
		expect(onAllowedClick).toHaveBeenCalledTimes(1);
	});

	it("returns null when denied and hideWhenDenied", async () => {
		vi.stubGlobal("frappe", {
			call: vi.fn(async () =>
				successMessage({
					action_code: "DELETE_X",
					allowed: false,
					message: "You cannot delete this record.",
					requires_confirmation: false,
				}),
			),
		});

		const { container } = render(
			<ActionAwareButton
				actionCode="DELETE_X"
				objectType="X"
				objectCode="1"
				label="Delete"
				hideWhenDenied
				onAllowedClick={vi.fn()}
			/>,
		);

		await waitFor(() => expect(container.firstChild).toBeNull());
	});

	it("renders disabled button and denial reason when denied and visible", async () => {
		vi.stubGlobal("frappe", {
			call: vi.fn(async () =>
				successMessage({
					action_code: "APPROVE",
					allowed: false,
					message: "Only the assigned approver can approve.",
					requires_confirmation: false,
				}),
			),
		});

		render(
			<ActionAwareButton actionCode="APPROVE" objectType="PR" objectCode="P-1" label="Approve" onAllowedClick={vi.fn()} />,
		);

		const btn = await screen.findByTestId("action-aware-button-APPROVE");
		expect(btn).toBeDisabled();
		expect(screen.getByTestId("action-denial-reason-APPROVE")).toHaveTextContent("Only the assigned approver can approve.");
	});

	it("honors buttonTestId override for the primary button", async () => {
		vi.stubGlobal("frappe", {
			call: vi.fn(async () =>
				successMessage({
					action_code: "CUSTOM",
					allowed: true,
					requires_confirmation: false,
				}),
			),
		});
		render(
			<ActionAwareButton
				actionCode="CUSTOM"
				objectType="T"
				objectCode="1"
				label="Go"
				buttonTestId="std-library-import-package-button"
				onAllowedClick={vi.fn()}
			/>,
		);
		await waitFor(() => {
			expect(screen.getByTestId("std-library-import-package-button")).not.toBeDisabled();
		});
	});

	it("sanitizes actionCode in data-testid", async () => {
		vi.stubGlobal("frappe", {
			call: vi.fn(async () =>
				successMessage({
					action_code: "a/b",
					allowed: true,
					requires_confirmation: false,
				}),
			),
		});

		render(<ActionAwareButton actionCode="a/b" objectType="T" objectCode="1" label="Go" onAllowedClick={vi.fn()} />);

		await waitFor(() => {
			expect(screen.getByTestId("action-aware-button-a_b")).toBeInTheDocument();
		});
	});
});
