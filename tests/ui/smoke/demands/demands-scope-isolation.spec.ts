import { test, expect } from "@playwright/test";
import {
	loginAsDemandRequester,
	loginAsStrategyViewerOtherPe,
} from "../../helpers/auth";

/**
 * DEM-AC-010 — cross-entity / OU denial in Desk UI.
 * MOH requester must not see county Draft; Kisumu user must not open MOH Approved.
 * Requires canonical seeds DMD-CGK-2027-006 and DMD-MOH-2027-014 (DEM-SEED-001/003).
 */

const WORKSPACE = '[data-testid="kt-dem-ui01-root"]';

function errText(error: unknown): string {
	if (typeof error === "string") return error;
	try {
		return JSON.stringify(error);
	} catch {
		return String(error);
	}
}

test.describe("DEM-AC-010 Demands scope isolation", () => {
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1400, height: 900 });
	});

	test("MOH requester workspace excludes county Draft code", async ({ page }) => {
		await loginAsDemandRequester(page);
		await page.goto("/desk/demands-workspace", { waitUntil: "domcontentloaded" });
		await expect(page.locator(`${WORKSPACE}[data-kt-dem-live="1"]`)).toBeVisible({
			timeout: 30_000,
		});
		await expect(page.locator("[data-kt-dem-tbody]")).toBeVisible({ timeout: 15_000 });
		await expect(page.locator("[data-kt-dem-tbody]")).not.toContainText("DMD-CGK-2027-006");

		const denied = await page.evaluate(async () => {
			try {
				const r = await (
					window as unknown as {
						frappe: {
							call: (o: {
								method: string;
								args?: Record<string, string>;
							}) => Promise<{ message?: { demand?: unknown; ok?: boolean } }>;
						};
					}
				).frappe.call({
					method: "kentender_procurement.demands.api.get_demand_form",
					args: { demand: "DMD-CGK-2027-006" },
				});
				return { ok: true as const, message: r.message };
			} catch (e) {
				const anyErr = e as { message?: string; exc?: string; _server_messages?: string };
				return {
					ok: false as const,
					error:
						anyErr?.message ||
						anyErr?.exc ||
						anyErr?._server_messages ||
						JSON.stringify(e),
				};
			}
		});
		if (denied.ok) {
			expect(denied.message?.demand == null).toBeTruthy();
		} else {
			expect(errText(denied.error)).toMatch(
				/SCOPE|permission|not permitted|Permission|organisational scope/i,
			);
		}
	});

	test("Kisumu user cannot open MOH Approved detail", async ({ page }) => {
		await loginAsStrategyViewerOtherPe(page);
		await page.goto("/desk/demands-workspace", { waitUntil: "domcontentloaded" });
		await expect(page.locator(`${WORKSPACE}[data-kt-dem-live="1"]`)).toBeVisible({
			timeout: 30_000,
		});
		await expect(page.locator("[data-kt-dem-tbody]")).not.toContainText("DMD-MOH-2027-014");

		const denied = await page.evaluate(async () => {
			try {
				const r = await (
					window as unknown as {
						frappe: {
							call: (o: {
								method: string;
								args?: Record<string, string>;
							}) => Promise<{ message?: unknown }>;
						};
					}
				).frappe.call({
					method: "kentender_procurement.demands.api.get_demand_detail",
					args: { demand: "DMD-MOH-2027-014" },
				});
				return { ok: true as const, message: r.message };
			} catch (e) {
				const anyErr = e as { message?: string; exc?: string; _server_messages?: string };
				return {
					ok: false as const,
					error:
						anyErr?.message ||
						anyErr?.exc ||
						anyErr?._server_messages ||
						JSON.stringify(e),
				};
			}
		});
		expect(denied.ok).toBeFalsy();
		if (!denied.ok) {
			expect(errText(denied.error)).toMatch(
				/SCOPE|permission|not permitted|Permission|organisational scope/i,
			);
		}
	});
});
