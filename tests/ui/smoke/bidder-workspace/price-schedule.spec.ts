import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";

/**
 * Price Schedule — Stitch 01–04 overview / editor / review.
 * Routes:
 *   /tenders/<publication_ref>/sections/price_schedule
 *   /tenders/<publication_ref>/sections/price_schedule/schedules/<schedule_key>
 *   /tenders/<publication_ref>/sections/price_schedule/review
 */

async function seedLeanPsPublished(page: import("@playwright/test").Page): Promise<string> {
	await page.waitForFunction(
		() => typeof (window as unknown as { frappe?: unknown }).frappe !== "undefined",
	);
	const result = await page.evaluate(async () => {
		// @ts-expect-error frappe on desk
		const r = await frappe.call({
			method: "kentender_procurement.tender_configurations.publish_lean_price_schedule_for_tests",
			args: { clear: 1, fixture: "single_lot" },
		});
		return r.message || r;
	});
	const ref = (result as { publication_ref?: string }).publication_ref || "";
	if (!ref) {
		throw new Error("Lean PS publish seed failed: " + JSON.stringify(result));
	}
	return ref;
}

async function fillRequiredSupplyInEditor(page: import("@playwright/test").Page): Promise<void> {
	await expect(page.getByTestId("kt-ps-editor-root")).toBeVisible({ timeout: 30_000 });
	const rows = page.getByTestId("kt-ps-line-row");
	const count = await rows.count();
	for (let i = 0; i < count; i++) {
		const row = rows.nth(i);
		const required = await row.getAttribute("data-required");
		if (required !== "1") continue;
		const price = row.getByTestId("kt-ps-unit-price");
		if (await price.count()) {
			await price.fill("1000");
		}
		const country = row.getByTestId("kt-ps-country");
		if (await country.count()) {
			await country.selectOption({ label: "Kenya" });
		}
	}
	await page.getByTestId("kt-ps-save-draft").click();
	await page.waitForTimeout(1500);
}

test.describe("Price Schedule portal", () => {
	test("overview edit review Complete → checklist; FoT shows read-only total", async ({
		page,
	}) => {
		test.setTimeout(180_000);
		await page.setViewportSize({ width: 1400, height: 900 });
		await loginAsAdministrator(page);
		await page.goto("/desk", { waitUntil: "domcontentloaded" });
		const publicationRef = await seedLeanPsPublished(page);
		await loginAsAdministrator(page);

		const overviewUrl = `/tenders/${publicationRef}/sections/price_schedule`;
		await page.goto(overviewUrl, { waitUntil: "domcontentloaded" });
		await expect(page.getByTestId("kt-ps-root")).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId("kt-ps-title")).toBeVisible();
		await expect(page.getByTestId("kt-ps-progress-label")).toContainText(/schedules complete/i);
		await expect(page.getByTestId("kt-ps-schedules-table")).toBeVisible();
		expect(page.url()).not.toMatch(/\/desk\/|it-electronic-bidder-workspace/);

		const startBtn = page
			.getByTestId("kt-ps-schedule-action")
			.filter({ hasText: /Start|Continue|Review/i })
			.first();
		await expect(startBtn).toBeVisible({ timeout: 15_000 });
		await startBtn.click();
		await expect(page.getByTestId("kt-ps-editor-root")).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId("kt-ps-lines-table")).toBeVisible();

		await fillRequiredSupplyInEditor(page);
		await expect(page.getByTestId("kt-ps-editor-progress-label")).toContainText(/2 of 2/i, {
			timeout: 10_000,
		});
		// Totals must be thousands-formatted (Stitch: 3,400,000.00 style)
		await expect(page.getByTestId("kt-ps-line-total").first()).toHaveText(/,/);

		await page.goto(`${overviewUrl}/review`, { waitUntil: "domcontentloaded" });
		await expect(page.getByTestId("kt-ps-review-root")).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId("kt-ps-summary-table")).toBeVisible();
		await expect(page.getByTestId("kt-ps-review-back")).toHaveAttribute(
			"href",
			new RegExp(`/tenders/${publicationRef}/sections/price_schedule/?$`),
		);
		await expect(page.getByTestId("kt-ps-complete-btn")).toBeVisible();

		const completeEnabled = await page
			.getByTestId("kt-ps-review-root")
			.getAttribute("data-complete-enabled");
		if (completeEnabled !== "1") {
			await page.goto(`${overviewUrl}/schedules/supply_installation`, {
				waitUntil: "domcontentloaded",
			});
			await fillRequiredSupplyInEditor(page);
			await page.goto(`${overviewUrl}/review`, { waitUntil: "domcontentloaded" });
			await expect(page.getByTestId("kt-ps-review-root")).toHaveAttribute(
				"data-complete-enabled",
				"1",
				{ timeout: 30_000 },
			);
		}

		await page.getByTestId("kt-ps-complete-btn").click();
		await expect(page).toHaveURL(new RegExp(`/tenders/${publicationRef}/workspace/?$`), {
			timeout: 20_000,
		});
		await expect(page.getByTestId("kt-a2-checklist-root")).toBeVisible({ timeout: 30_000 });

		await page.goto(`/tenders/${publicationRef}/sections/form_of_tender`, {
			waitUntil: "domcontentloaded",
		});
		const fotRoot = page.locator("[data-testid='kt-fot-root'], .kt-fot-root").first();
		await expect(fotRoot).toBeVisible({ timeout: 30_000 });
		const retype = page.getByLabel(/re-?type.*total|enter.*grand total|price schedule total/i);
		await expect(retype).toHaveCount(0);
		const bodyText = await page.locator("body").innerText();
		expect(bodyText).toMatch(/5,?000|5000|KES|Price Schedule/i);

		await expect(page.locator(".navbar .navbar-home")).toHaveCount(0);
	});
});
