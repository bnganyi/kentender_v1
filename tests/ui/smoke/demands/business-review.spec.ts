import { test, expect } from "@playwright/test";
import {
	loginAsAdministrator,
	loginAsBusinessApprover,
} from "../../helpers/auth";
import {
	assertStitchDeskChrome,
	assertStitchSectionTableChrome,
} from "../../helpers/stitchDeskChrome";

/**
 * DEM-UI-04 Business review — Stitch Desk canvas + live bind.
 * Route: /desk/demand-review/<name>
 */

const ROOT = '[data-testid="kt-dem-ui04-root"]';

async function prepareReviewDemand(page: import("@playwright/test").Page): Promise<string> {
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
			method: "kentender_procurement.demands.api.prepare_business_review_ui04",
		});
		return r.message?.demand || "";
	});
	expect(demandName).toBeTruthy();
	return demandName;
}

test.describe("DEM-UI-04 Business Review", () => {
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1400, height: 900 });
	});

	test("Stitch regions, statements, disclaimer, and Support advance stage", async ({
		page,
	}) => {
		const demandName = await prepareReviewDemand(page);
		await page.context().clearCookies();
		await loginAsBusinessApprover(page);
		await page.goto(`/desk/demand-review/${demandName}`, {
			waitUntil: "domcontentloaded",
		});
		await expect(page.locator(`${ROOT}[data-kt-dem-live="1"]`)).toBeVisible({
			timeout: 30_000,
		});
		await expect(page.locator(`${ROOT}.kt-stitch-canvas`)).toBeVisible();
		await expect(page.getByTestId("kt-dem-record-header")).toBeVisible();
		await expect(page.getByTestId("kt-dem-record-meta-top")).toBeVisible();
		await expect(page.getByTestId("kt-dem-code")).not.toHaveText("—");
		await expect(page.getByTestId("kt-dem-status-pill")).toContainText(/In review/i);
		await expect(page.getByTestId("kt-dem-route-pill")).toBeVisible();
		await expect(page.getByTestId("kt-dem-route-pill")).toContainText(/Route/i);
		await expect(page.getByTestId("kt-dem-record-pe")).toContainText(/Ministry of Health/i);
		await expect(page.getByTestId("kt-dem-stage")).toBeVisible();
		await expect(page.getByTestId("kt-dem-stage")).toContainText(/Business review/i);
		await expect(page.getByTestId("kt-dem-stage")).toContainText(/Current/i);
		// Desktop stepper must stay horizontal (workspace .flex-col !important used to stack it ~400px tall).
		const stageLayout = await page.locator("[data-kt-dem-stage-list]").evaluate((el) => {
			const cs = getComputedStyle(el);
			const r = el.getBoundingClientRect();
			return { flexDirection: cs.flexDirection, height: r.height, width: r.width };
		});
		expect(stageLayout.flexDirection).toBe("row");
		expect(stageLayout.height).toBeLessThan(140);
		expect(stageLayout.width).toBeGreaterThan(stageLayout.height * 2);
		await expect(page.getByTestId("kt-dem-ui04-section-need")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui04-section-items")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui04-section-delivery")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui04-section-supporting")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui04-decision")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui04-disclaimer")).toContainText(
			/does not confirm funding|final procurement approval/i,
		);
		const prompts = page.getByTestId("kt-dem-ui04-prompts");
		await expect(prompts).toContainText(/Review Criteria/i);
		await expect(prompts).toContainText(/necessary and supports the unit/i);
		await expect(prompts).toContainText(/expected outcome and beneficiaries/i);
		await expect(prompts).toContainText(/timing and priority/i);
		await expect(prompts).toContainText(/owning unit accepts accountability/i);
		// Stitch: acknowledgement checkboxes (not scored questions / bullet list).
		await expect(prompts.locator('input[type="checkbox"]')).toHaveCount(4);
		await expect(prompts.locator("ul, li")).toHaveCount(0);
		await expect(page.getByTestId("kt-dem-ui04-support")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui04-return")).toContainText(
			/Return for correction/i,
		);
		await expect(page.getByTestId("kt-dem-ui04-reject")).toContainText(/Reject demand/i);
		// Stitch reason modal is in the fixture but closed until Return/Reject.
		await expect(page.getByTestId("kt-dem-ui04-reason-modal")).toBeAttached();
		await expect(page.getByTestId("kt-dem-ui04-reason-modal")).toBeHidden();
		await expect(page.locator("cdn.tailwindcss.com")).toHaveCount(0);
		// No specialist mutation controls on Business stage (enrichment drawer markup stays in DOM but hidden).
		const businessHost = page.getByTestId("kt-dem-business-host");
		await expect(businessHost).toBeVisible();
		await expect(businessHost.getByText(/Budget Line/i)).toHaveCount(0);
		await expect(businessHost.getByText(/Strategy target/i)).toHaveCount(0);
		await expect(page.getByTestId("kt-dem-ui05-root")).toBeHidden();
		await expect(page.getByTestId("kt-dem-ui05a-drawer")).toBeHidden();

		await page.getByTestId("kt-dem-ui04-comment").fill("Aligned with unit mandate");
		await page.getByTestId("kt-dem-ui04-support").click();
		await expect(page).toHaveURL(/demands-workspace/, { timeout: 20_000 });
	});

	test("Stitch chrome and section headers match app-wide pins", async ({ page }) => {
		const demandName = await prepareReviewDemand(page);
		await page.context().clearCookies();
		await loginAsBusinessApprover(page);
		await page.goto(`/desk/demand-review/${demandName}`, {
			waitUntil: "domcontentloaded",
		});
		await expect(page.locator(`${ROOT}[data-kt-dem-live="1"]`)).toBeVisible({
			timeout: 30_000,
		});
		await assertStitchDeskChrome(page, {
			rootTestId: "kt-dem-ui04-root",
			primaryCtaTestId: "kt-dem-ui04-support",
		});
		await assertStitchSectionTableChrome(page, {
			sectionTestId: "kt-dem-ui04-section-need",
		});
		// Decision footer must stay muted surface — not section-header primary-fixed + navy inset.
		const actionsChrome = await page.getByTestId("kt-dem-ui04-actions").evaluate((el) => {
			const cs = getComputedStyle(el);
			return { bg: cs.backgroundColor, boxShadow: cs.boxShadow, padding: cs.padding };
		});
		expect(actionsChrome.bg).toBe("rgb(244, 243, 249)");
		expect(actionsChrome.boxShadow === "none" || !actionsChrome.boxShadow.includes("inset")).toBe(
			true,
		);
		expect(actionsChrome.padding).toMatch(/20px/);
	});

	test("Return for correction requires Stitch reason modal", async ({ page }) => {
		const demandName = await prepareReviewDemand(page);
		await page.context().clearCookies();
		await loginAsBusinessApprover(page);
		await page.goto(`/desk/demand-review/${demandName}`, {
			waitUntil: "domcontentloaded",
		});
		await expect(page.locator(`${ROOT}[data-kt-dem-live="1"]`)).toBeVisible({
			timeout: 30_000,
		});
		await page.getByTestId("kt-dem-ui04-return").click();
		const modal = page.getByTestId("kt-dem-ui04-reason-modal");
		await expect(modal).toBeVisible({ timeout: 10_000 });
		await expect(modal).not.toHaveAttribute("hidden", "");
		await expect(page.getByTestId("kt-dem-ui04-reason-hints")).toBeVisible();
		await expect(page.locator(".frappe-dialog:visible, .modal-dialog:visible")).toHaveCount(0);
		await page.getByTestId("kt-dem-ui04-reason-confirm").click();
		await expect(page.getByTestId("kt-dem-ui04-reason-error")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui04-reason-error")).toContainText(/required/i);
		await expect(
			page.getByRole("dialog", { name: "Message" }),
		).toHaveCount(0);
		await page.getByTestId("kt-dem-ui04-reason-comment").fill(
			"Revise estimate and participant counts",
		);
		await page.getByTestId("kt-dem-ui04-hint-outcome").check();
		await page.getByTestId("kt-dem-ui04-reason-confirm").click();
		await expect(page).toHaveURL(/demands-workspace/, { timeout: 20_000 });
	});
});
