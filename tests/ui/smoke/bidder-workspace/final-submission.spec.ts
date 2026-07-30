import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";

/**
 * Final Submission — Review & Validate → Final Bid Review → Submit → Receipt.
 */

async function seedReadyBid(page: import("@playwright/test").Page): Promise<string> {
	await page.waitForFunction(
		() => typeof (window as unknown as { frappe?: unknown }).frappe !== "undefined",
	);
	const result = await page.evaluate(async () => {
		// @ts-expect-error frappe on desk
		const r = await frappe.call({
			method:
				"kentender_procurement.tender_configurations.seed_ready_lean_bid_for_final_submission_tests",
			args: { clear: 1, fixture: "single_lot" },
		});
		return r.message || r;
	});
	const ref = (result as { publication_ref?: string }).publication_ref || "";
	if (!ref) {
		throw new Error("Ready lean bid seed failed: " + JSON.stringify(result));
	}
	return ref;
}

test.describe("Final Submission portal", () => {
	test("checklist → review → final → submit confirm → receipt", async ({ page }) => {
		test.setTimeout(300_000);
		await page.setViewportSize({ width: 1400, height: 900 });
		await loginAsAdministrator(page);
		await page.goto("/desk", { waitUntil: "domcontentloaded" });
		const publicationRef = await seedReadyBid(page);
		await loginAsAdministrator(page);

		await page.goto(`/tenders/${publicationRef}/workspace`, {
			waitUntil: "domcontentloaded",
		});
		await expect(page.getByTestId("kt-a2-checklist-root")).toBeVisible({ timeout: 30_000 });
		const cta = page.getByTestId("kt-a2-primary-cta");
		await expect(cta).toBeVisible();
		await expect(cta).toContainText(/Review & Validate Bid/i);
		await expect(cta).toHaveAttribute(
			"href",
			new RegExp(`/tenders/${publicationRef}/review-and-validate`),
		);

		const reviewNav = page.getByTestId("kt-a2-nav-review");
		await expect(reviewNav).not.toHaveClass(/is-disabled/);

		await cta.click();
		await expect(page.getByTestId("kt-fs-rav-root")).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId("kt-fs-rav-title")).toContainText(/Review & Validate/i);
		await expect(page.getByTestId("kt-fs-rav-table")).toBeVisible();
		await expect(page.getByTestId("kt-fs-rav-continue")).toBeEnabled({ timeout: 10_000 });
		await expect(page.getByTestId("kt-fs-rav-footer")).toBeVisible();

		await page.getByTestId("kt-fs-rav-continue").click();
		await expect(page.getByTestId("kt-fs-fbr-root")).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId("kt-fs-fbr-title")).toContainText(/Final Bid Review/i);
		await expect(page.getByTestId("kt-fs-fbr-continue")).toBeVisible();

		await page.getByTestId("kt-fs-fbr-continue").click();
		await expect(page.getByTestId("kt-fs-submit-root")).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId("kt-fs-submit-title")).toContainText(/Submit Bid/i);
		await expect(page.getByTestId("kt-fs-declare")).toBeVisible();

		const submitBtn = page.getByTestId("kt-fs-submit-btn");
		await expect(submitBtn).toBeDisabled();
		await page.getByTestId("kt-fs-declare").check();
		await expect(submitBtn).toBeEnabled({ timeout: 5_000 });

		await submitBtn.click();
		await expect(page.getByTestId("kt-fs-confirm-dialog")).toBeVisible();
		await page.getByTestId("kt-fs-confirm-cancel").click();
		await expect(page).toHaveURL(new RegExp(`/tenders/${publicationRef}/submit-bid`));

		await submitBtn.click();
		await page.getByTestId("kt-fs-confirm-submit").click();
		await expect(page.getByTestId("kt-fs-receipt-root")).toBeVisible({ timeout: 60_000 });
		await expect(page.getByTestId("kt-fs-receipt-code")).not.toHaveText("");
		await expect(page.getByTestId("kt-fs-receipt-title")).toContainText(/Bid submitted/i);
		const body = await page.locator("body").innerText();
		expect(body.toLowerCase()).not.toContain("seal_hash");
		expect(body.toLowerCase()).not.toMatch(/sha256|schema_hash/);

		await page.goto(`/tenders/${publicationRef}/workspace`, {
			waitUntil: "domcontentloaded",
		});
		await expect(page.getByTestId("kt-a2-primary-cta")).toContainText(/View Receipt/i);
	});
});
