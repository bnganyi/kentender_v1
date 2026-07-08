/**
 * UI-HARD-1640 — Action availability UI smoke (pack §21 ticket 1640, doc §21.5).
 *
 * Canonical React + SEC-0410 client under `std-engine` (Vitest / jsdom).
 * `UI-SMOKE-ACTION-004` aligns with pack “backend denial if endpoint called directly” via the
 * client’s refusal to accept a failed SEC envelope (`actionAvailabilityClient.spec.ts` detail tests).
 */
import "@testing-library/jest-dom/vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ActionAwareButton } from "../shared/action-availability/ActionAwareButton";
import { getActionAvailability, getBatchActionAvailability } from "../shared/action-availability/actionAvailabilityClient";
import {
	SEC_API_ACTION_AVAILABILITY_BATCH_METHOD,
	SEC_API_ACTION_AVAILABILITY_METHOD,
} from "../shared/action-availability/constants";

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

describe("UI-HARD-1640 — UI-SMOKE-ACTION-* (action availability)", () => {
	afterEach(() => {
		cleanup();
		vi.unstubAllGlobals();
		vi.restoreAllMocks();
	});

	it("UI-SMOKE-ACTION-001 — Disabled action shows backend denial reason", async () => {
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
		expect(screen.getByTestId("action-denial-reason-APPROVE")).toHaveTextContent(
			"Only the assigned approver can approve.",
		);

		const frappe = globalThis as { frappe?: { call: ReturnType<typeof vi.fn> } };
		expect(frappe.frappe?.call).toHaveBeenCalledWith(
			expect.objectContaining({
				method: SEC_API_ACTION_AVAILABILITY_METHOD,
				args: expect.objectContaining({
					action_code: "APPROVE",
					object_type: "PR",
					object_code: "P-1",
				}),
			}),
		);
	});

	it("UI-SMOKE-ACTION-002 — Hidden action absent when denied (hideWhenDenied)", async () => {
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

	it("UI-SMOKE-ACTION-003 — Batch action availability maps per-item allow / denial", async () => {
		vi.stubGlobal("frappe", {
			call: vi.fn(async () => ({
				message: {
					success: true,
					actor_user_code: "Administrator",
					items: [
						{
							action_code: "A",
							allowed: true,
							message: "ok",
							risk_level: "Low",
							requires_confirmation: false,
							audit_on_attempt: false,
						},
						{
							action_code: "B",
							allowed: false,
							message: "no",
							denial_code: "STD_AUTH_PERMISSION_DENIED",
							risk_level: "High",
							requires_confirmation: false,
							audit_on_attempt: true,
						},
					],
				},
			})),
		});

		const rows = await getBatchActionAvailability(
			[
				{ action_code: "A", object_type: "T", object_code: "1", context: { granted_permissions: ["PERM_X"] } },
				{ action_code: "B", object_type: "T", object_code: "2", context: { granted_permissions: [] } },
			],
			{ context: { enforce_negative_permission_rules: true } },
		);
		expect(rows).toHaveLength(2);
		expect(rows[0].allowed).toBe(true);
		expect(rows[1].allowed).toBe(false);
		expect(rows[1].denial_code).toBe("STD_AUTH_PERMISSION_DENIED");

		const frappe = globalThis as { frappe?: { call: ReturnType<typeof vi.fn> } };
		expect(frappe.frappe?.call).toHaveBeenCalledWith(
			expect.objectContaining({
				method: SEC_API_ACTION_AVAILABILITY_BATCH_METHOD,
			}),
		);
	});

	it("UI-SMOKE-ACTION-004 — Failed SEC envelope surfaces as client error (no silent allow)", async () => {
		vi.stubGlobal("frappe", {
			call: vi.fn(async () => ({
				message: {
					success: false,
					error_code: "SEC_API_PAYLOAD_INVALID",
					message: "context must be valid JSON.",
					details: {},
				},
			})),
		});

		await expect(
			getActionAvailability({
				action_code: "PUBLISH_TENDER",
				object_type: "Tender",
				object_code: "X",
			}),
		).rejects.toMatchObject({
			name: "ActionAvailabilityClientError",
			envelope: {
				success: false,
				error_code: "SEC_API_PAYLOAD_INVALID",
			},
		});
	});
});
