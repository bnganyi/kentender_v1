import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";

/**
 * A2 Submission Checklist — Website workspace home.
 * Route: /tenders/<publication_ref>/workspace
 *
 * Seeds the lean NSSF published tender (electronic template snapshot) so the
 * checklist is authoritative and not dependent on stale /tenders cards.
 */

const CHECKLIST = '[data-testid="kt-a2-checklist-root"]';

async function seedLeanNssfPublished(page: import("@playwright/test").Page): Promise<string> {
	await page.waitForFunction(
		() => typeof (window as unknown as { frappe?: unknown }).frappe !== "undefined",
	);
	const result = await page.evaluate(async () => {
		// @ts-expect-error frappe on desk
		const r = await frappe.call({
			method: "kentender_procurement.tender_configurations.publish_e1_nssf_lean_for_tests",
			args: { clear: 1 },
		});
		return r.message || r;
	});
	const ref = (result as { publication_ref?: string }).publication_ref || "";
	if (!ref) {
		throw new Error("Lean NSSF publish seed failed: " + JSON.stringify(result));
	}
	return ref;
}

test.describe("A2 Submission Checklist portal", () => {
	test("workspace checklist loads on Website with sidebar (no Desk Procurement rail)", async ({
		page,
	}) => {
		await page.setViewportSize({ width: 1400, height: 900 });
		await loginAsAdministrator(page);
		await page.goto("/desk", { waitUntil: "domcontentloaded" });
		const publicationRef = await seedLeanNssfPublished(page);
		// Re-auth for Website host — long seed / desk session can drop portal cookies.
		await loginAsAdministrator(page);

		await page.goto(`/tenders/${publicationRef}/workspace`, {
			waitUntil: "domcontentloaded",
		});
		expect(page.url()).toMatch(/\/tenders\/[^/?#]+\/workspace/);
		expect(page.url()).not.toMatch(/\/desk\/|it-electronic-bidder-workspace/);

		await expect(page.locator(CHECKLIST)).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId("kt-a2-title")).toContainText("Submission Checklist");
		await expect(page.getByTestId("kt-a2-sidebar")).toBeVisible();
		await expect(page.getByTestId("kt-a2-nav-checklist")).toBeVisible();
		await expect(page.getByTestId("kt-a2-section-checklist")).toBeVisible();
		await expect(page.getByTestId("kt-a2-section-row").first()).toBeVisible();
		await expect(page.getByTestId("kt-a2-primary-cta")).toBeVisible();

		// Lean canonical 10-section checklist (includes Tender Security + Form of Tender).
		await expect(page.getByTestId("kt-a2-section-row")).toHaveCount(10);
		await expect(page.locator(CHECKLIST)).toContainText("Form of Tender");
		await expect(page.locator(CHECKLIST)).toContainText("Tender Security");

		const countdown = page.getByTestId("kt-a2-time-remaining");
		await expect(countdown).toHaveAttribute("data-kt-countdown", "");
		await expect(countdown).toHaveAttribute("data-deadline", /.+/);
		const before = (await countdown.innerText()).trim();
		await expect
			.poll(async () => (await countdown.innerText()).trim(), { timeout: 2500 })
			.not.toBe(before);

		const body = await page.locator("body").innerText();
		expect(body).not.toMatch(/Tender Management|Tender Configurations|Evaluation and Award/i);
		await expect(page.locator("nav.navbar")).toBeHidden();
	});
});
