import { afterEach, describe, expect, it, vi } from "vitest";

import {
	SEC_API_ACTION_AVAILABILITY_BATCH_METHOD,
	SEC_API_ACTION_AVAILABILITY_METHOD,
} from "./constants";
import {
	getActionAvailability,
	getBatchActionAvailability,
	ActionAvailabilityClientError,
} from "./actionAvailabilityClient";

describe("actionAvailabilityClient", () => {
	afterEach(() => {
		vi.unstubAllGlobals();
		vi.restoreAllMocks();
	});

	it("getActionAvailability maps Desk frappe.call { message } wrapper", async () => {
		vi.stubGlobal("frappe", {
			call: vi.fn(async () => ({
				message: {
					success: true,
					actor_user_code: "Administrator",
					action_code: "PUBLISH_TENDER",
					allowed: true,
					message: "Allowed",
					required_permission: "PERM_TENDER_PUBLISH",
					risk_level: "Critical",
					requires_confirmation: true,
					audit_on_attempt: true,
				},
			})),
		});
		const out = await getActionAvailability({
			action_code: "PUBLISH_TENDER",
			object_type: "Procurement Tender",
			object_code: "TND-1",
			context: { granted_permissions: ["PERM_TENDER_PUBLISH"] },
		});
		expect(out.allowed).toBe(true);
		expect(out.action_code).toBe("PUBLISH_TENDER");
		expect(out.requires_confirmation).toBe(true);
		expect(out.risk_level).toBe("Critical");
		const frappe = globalThis as { frappe?: { call: ReturnType<typeof vi.fn> } };
		expect(frappe.frappe?.call).toHaveBeenCalledWith(
			expect.objectContaining({
				method: SEC_API_ACTION_AVAILABILITY_METHOD,
				type: "POST",
				args: expect.objectContaining({
					action_code: "PUBLISH_TENDER",
					object_type: "Procurement Tender",
					object_code: "TND-1",
				}),
			}),
		);
	});

	it("getActionAvailability throws ActionAvailabilityClientError on SEC envelope failure", async () => {
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

	it("getBatchActionAvailability returns items array", async () => {
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

	it("getBatchActionAvailability rejects empty items before calling frappe", async () => {
		const spy = vi.fn();
		vi.stubGlobal("frappe", { call: spy });
		await expect(getBatchActionAvailability([])).rejects.toBeInstanceOf(ActionAvailabilityClientError);
		expect(spy).not.toHaveBeenCalled();
	});
});
