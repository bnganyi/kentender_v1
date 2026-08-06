import { test, expect } from "@playwright/test";
import { loginAsStrategyOfficer } from "../../helpers/auth";

/**
 * KENTENDER_MVP_V1 §10 — Medical Services unit officer can open Strategy Performance;
 * cross-entity denial is covered by domain validate / isolation checks.
 */
test.describe("KENTENDER_MVP_V1 ownership smoke", () => {
	test("Medical Services officer opens Strategy Performance", async ({ page }) => {
		test.setTimeout(120_000);
		await loginAsStrategyOfficer(page);
		await page.goto("/desk/strategy-performance", { waitUntil: "domcontentloaded" });
		await expect(page.locator("body")).not.toContainText("Invalid Login", { timeout: 15_000 });
		await expect(
			page.locator(".kt-str-root, [data-testid='kt-str-performance'], .page-container").first()
		).toBeVisible({
			timeout: 45_000,
		});
	});
});
