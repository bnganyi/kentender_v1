import { test, expect } from "@playwright/test";
import { loginAsDemandRequester } from "../../helpers/auth";

/**
 * DEM-AC-001 — Requester submits without Strategy / Budget / procurement method.
 * Route: /desk/demand-form
 */

const ROOT = '[data-testid="kt-dem-ui02-root"]';
const suffix = Date.now().toString().slice(-6);

test.describe("DEM-AC-001 Requester submit", () => {
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1400, height: 900 });
		await loginAsDemandRequester(page);
	});

	test("Submit succeeds without Strategy, Budget, or method fields", async ({ page }) => {
		await page.goto("/desk/demand-form", { waitUntil: "domcontentloaded" });
		await expect(page.locator(`${ROOT}[data-kt-dem-live="1"]`)).toBeVisible({ timeout: 30_000 });

		await page.getByTestId("kt-dem-ui02-title").fill(`AC001 submit ${suffix}`);
		await page.getByTestId("kt-dem-ui02-what").fill("Need clinic connectivity upgrades");
		await page.getByTestId("kt-dem-ui02-why").fill("Service continuity requires resilient links");
		await page.getByTestId("kt-dem-ui02-outcome").fill("Reliable clinic connectivity");
		await page.getByTestId("kt-dem-ui02-beneficiaries").fill("County clinics");
		await page.getByTestId("kt-dem-ui02-location").fill("Nairobi");
		await page.getByTestId("kt-dem-ui02-route").selectOption("Standard");
		// Required-by via native date overlay.
		await page.getByTestId("kt-dem-ui02-required-by-native").fill("2027-06-30");
		await page.locator('[data-kt-dem-item="description"]').first().fill("Network lot");
		await page.locator('[data-kt-dem-item="requester_estimate"]').first().fill("1000");
		await page.locator('[data-kt-dem-item="requester_estimate"]').first().blur();

		// No Strategy / Budget / method controls on create form.
		await expect(page.locator('[data-kt-dem-field="procurement_method"]')).toHaveCount(0);
		await expect(page.locator('[data-kt-dem-field="confirmed_estimate"]')).toHaveCount(0);
		await expect(page.getByText(/Strategy reference/i)).toHaveCount(0);

		await page.getByTestId("kt-dem-ui02-submit").click();
		await expect(page).toHaveURL(/demands-workspace/, { timeout: 30_000 });
		await expect(page.locator('[data-testid="kt-dem-ui01-root"][data-kt-dem-live="1"]')).toBeVisible({
			timeout: 30_000,
		});
		await expect(page.locator("[data-kt-dem-tbody]")).toContainText(`AC001 submit ${suffix}`, {
			timeout: 15_000,
		});
	});
});
