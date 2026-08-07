import { test, expect } from "@playwright/test";
import {
	loginAsAdministrator,
	loginAsProcurementApprover,
} from "../../helpers/auth";
import { assertStitchDeskChrome } from "../../helpers/stitchDeskChrome";

/**
 * DEM-UI-05 / DEM-UI-05A — Procurement enrichment + Strategy assign drawer.
 * Route: /desk/demand-review/<name>
 */

const ROOT = '[data-testid="kt-dem-ui04-root"]';

async function prepareEnrichmentDemand(
	page: import("@playwright/test").Page,
): Promise<string> {
	await loginAsAdministrator(page);
	await page.goto("/desk", { waitUntil: "domcontentloaded" });
	const demandName = await page.evaluate(async () => {
		const r = await (
			window as unknown as {
				frappe: {
					call: (o: { method: string }) => Promise<{
						message?: { demand?: string; ok?: boolean };
					}>;
				};
			}
		).frappe.call({
			method: "kentender_procurement.demands.api.prepare_enrichment_ui05",
		});
		return r.message?.demand || "";
	});
	expect(demandName).toBeTruthy();
	return demandName;
}

test.describe("DEM-UI-05 Procurement Enrichment", () => {
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1400, height: 900 });
	});

	test("Stitch regions, Assign drawer, Save, Send readiness", async ({ page }) => {
		const demandName = await prepareEnrichmentDemand(page);
		await page.context().clearCookies();
		await loginAsProcurementApprover(page);
		await page.goto(`/desk/demand-review/${demandName}`, {
			waitUntil: "domcontentloaded",
		});
		await expect(page.locator(`${ROOT}[data-kt-dem-live="1"]`)).toBeVisible({
			timeout: 30_000,
		});
		await expect(page.locator(ROOT)).toHaveAttribute(
			"data-kt-dem-review-stage",
			"Procurement Enrichment",
		);
		await expect(page.getByTestId("kt-dem-record-header")).toBeVisible();
		await expect(page.getByTestId("kt-dem-stage")).toContainText(
			/Procurement enrichment/i,
		);
		await expect(page.getByTestId("kt-dem-stage")).toContainText(/Current/i);
		await expect(page.getByTestId("kt-dem-business-host")).toBeHidden();
		await expect(page.getByTestId("kt-dem-ui05-root")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui05-section-business")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui05-section-classify")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui05-section-items")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui05-section-strategy")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui05-section-pvc")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui05-section-duplication")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui05-footer")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui05-strategy-pill")).toContainText(
			/Not assigned/i,
		);
		await expect(page.getByTestId("kt-dem-ui05-send")).toBeDisabled();
		// No procurement-method / tender chrome.
		await expect(page.getByText(/procurement method/i)).toHaveCount(0);
		await expect(page.getByText(/tender method/i)).toHaveCount(0);
		await expect(page.locator("cdn.tailwindcss.com")).toHaveCount(0);

		await page.getByTestId("kt-dem-ui05-category").selectOption({
			label: "ICT infrastructure and services",
		});
		await page.getByTestId("kt-dem-ui05-confirmed-estimate").fill("455,000,000");
		await page.getByTestId("kt-dem-ui05-estimate-basis").fill(
			"Market research and infrastructure assessment",
		);

		await page.getByTestId("kt-dem-ui05-assign-strategy").click();
		const drawer = page.getByTestId("kt-dem-ui05a-drawer");
		await expect(drawer).toBeVisible({ timeout: 10_000 });
		await expect(drawer).not.toHaveAttribute("hidden", "");
		await expect(page.getByTestId("kt-dem-ui05a-search")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui05a-suggestions")).toBeVisible();
		const firstOption = page.getByTestId("kt-dem-ui05a-option-0");
		await expect(firstOption).toBeVisible({ timeout: 15_000 });
		await firstOption.check();
		await page.getByTestId("kt-dem-ui05a-reason").fill("Primary alignment with digital health target");
		await page.getByTestId("kt-dem-ui05a-assign").click();
		await expect(drawer).toBeHidden({ timeout: 15_000 });
		await expect(page.getByTestId("kt-dem-ui05-strategy-pill")).toContainText(
			/Assigned/i,
			{ timeout: 15_000 },
		);
		await expect(page.getByTestId("kt-dem-ui05-strategy-assigned")).toBeVisible();

		await page.getByTestId("kt-dem-ui05-save").click();
		await expect(page.getByText(/Enrichment saved/i)).toBeVisible({
			timeout: 15_000,
		});
		await expect(page.getByTestId("kt-dem-ui05-send")).toBeEnabled({
			timeout: 15_000,
		});

		await assertStitchDeskChrome(page, {
			rootTestId: "kt-dem-ui04-root",
			primaryCtaTestId: "kt-dem-ui05-send",
		});
		// DEM-UI-05 Stitch uses bordered section cards + h2 rules (not UI-04 primary-fixed section headers).

		await page.getByTestId("kt-dem-ui05-send").click();
		await expect(page).toHaveURL(/demands-workspace/, { timeout: 20_000 });
	});

	test("Return for correction uses Stitch reason modal at Enrichment stage", async ({
		page,
	}) => {
		const demandName = await prepareEnrichmentDemand(page);
		await page.context().clearCookies();
		await loginAsProcurementApprover(page);
		await page.goto(`/desk/demand-review/${demandName}`, {
			waitUntil: "domcontentloaded",
		});
		await expect(page.locator(`${ROOT}[data-kt-dem-live="1"]`)).toBeVisible({
			timeout: 30_000,
		});
		await page.getByTestId("kt-dem-ui05-return").click();
		const modal = page.getByTestId("kt-dem-ui04-reason-modal");
		await expect(modal).toBeVisible({ timeout: 10_000 });
		await expect(page.locator(".frappe-dialog:visible, .modal-dialog:visible")).toHaveCount(
			0,
		);
		await page.getByTestId("kt-dem-ui04-reason-confirm").click();
		await expect(page.getByTestId("kt-dem-ui04-reason-error")).toContainText(/required/i);
		await page
			.getByTestId("kt-dem-ui04-reason-comment")
			.fill("Revise confirmed quantities before enrichment");
		await page.getByTestId("kt-dem-ui04-reason-confirm").click();
		await expect(page).toHaveURL(/demands-workspace/, { timeout: 20_000 });
	});
});
