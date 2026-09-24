import { test, expect, Page } from "@playwright/test";
import { login, loginAsAdministrator } from "../../helpers/auth";
import { collectPageErrors } from "../../helpers/designFidelity";
import { resetWorld, restoreSite, systemManager } from "./helpers";

/**
 * CFG-CHG-002 v0.14 §10.8 (tracker CFG14-5E) — Check sources in a real
 * browser, on the CONFIG-RULES world (a pending Reservation rules Version 1,
 * fixture-namespaced). Structure is the fidelity gate's job; this proves:
 * a real pending check recorded and shown in the history with who and when,
 * the verified-without-evidence refusal at the controls, a second check
 * recorded meanwhile caught as stale with the entries kept, the failed-read
 * state, a second setup role, and the narrow layout.
 *
 * Writes: source-check events on the fixture version, removed with it by
 * restoreSite.
 */
const SERVER = { timeout: 20_000 };
const FORM = '[data-testid="kt-source-check-form"]';
let version = "";

function checkLink(): string {
	return `/app/system-setup#procurement-settings/procurement-rules/${version}/check-sources`;
}

async function openCheck(page: Page): Promise<string[]> {
	const errors = collectPageErrors(page);
	await page.goto(checkLink(), { waitUntil: "domcontentloaded" });
	await page.waitForSelector(FORM, SERVER);
	return errors;
}

test.describe.serial("System setup — Source checks", () => {
	test.beforeAll(() => {
		const world = resetWorld("reset_config_rules");
		expect(world.reservation_version, "CONFIG-RULES reservation version").toBeTruthy();
		version = world.reservation_version as string;
	});
	test.afterAll(() => restoreSite());

	test("a pending check is recorded against the exact version and appears in its history with who and when", async ({ page }) => {
		await loginAsAdministrator(page);
		const errors = await openCheck(page);
		await expect(page.locator(`${FORM} h3`)).toHaveText("Check sources");
		await expect(page.locator('[data-testid="kt-source-check-version"]')).toHaveText("1");
		await expect(page.locator('[data-testid="kt-sc-result"]')).toHaveValue("Pending");
		// Nothing typed yet: it asks for the unresolved point before anything is sent.
		await expect(page.locator('[data-testid="kt-sc-unresolved-required"]')).toBeVisible();
		await expect(page.locator('[data-testid="kt-sc-record"]')).toBeDisabled();

		await page.fill('[data-testid="kt-sc-unresolved"]', "The applicable amended source and interpretation have not been established.");
		await page.fill('[data-testid="kt-sc-reason"]', "Record the remaining verification work for this reference version.");
		await expect(page.locator('[data-testid="kt-sc-pending-note"]')).toHaveText("This records outstanding work; it does not verify the rule.");
		await page.click('[data-testid="kt-sc-record"]');
		// Recorded: back on the rule's detail.
		await page.waitForSelector('[data-testid="kt-procset-rule-card"]', SERVER);
		expect(new URL(page.url()).hash).toBe(`#procurement-settings/procurement-rules/${version}`);

		await openCheck(page);
		const row = page.locator('[data-testid="kt-sc-history-row"]').first();
		await expect(row).toContainText("Source check needed");
		await expect(row).toContainText("Administrator");
		await expect(row).toContainText("Incomplete");
		await expect(page.locator(".modal.show")).toHaveCount(0);
		expect(errors, "console errors").toEqual([]);
	});

	test("Sources verified without complete evidence is refused at the controls, and nothing is sent", async ({ page }) => {
		await loginAsAdministrator(page);
		await openCheck(page);
		const sent: string[] = [];
		page.on("request", (request) => {
			if (request.url().includes("record_reference_verification")) sent.push(request.url());
		});
		await page.selectOption('[data-testid="kt-sc-result"]', "Verified");
		await expect(page.locator('[data-testid="kt-sc-evidence-required"]')).toBeVisible();
		for (const id of ["kt-sc-dates", "kt-sc-applicability", "kt-sc-interpretation"]) {
			await expect(page.locator(`[data-testid="${id}"]`)).toHaveAttribute("aria-invalid", "true");
		}
		await expect(page.locator('[data-testid="kt-sc-record"]')).toBeDisabled();
		expect(sent).toEqual([]);
	});

	test("a check recorded meanwhile makes this form stale; Review latest details shows it and keeps the entries", async ({ page, browser }) => {
		await loginAsAdministrator(page);
		await openCheck(page);
		await page.fill('[data-testid="kt-sc-unresolved"]', "Edition still to trace.");

		// Someone else records a check on the same version.
		const other = await browser.newPage();
		await loginAsAdministrator(other);
		await other.goto(checkLink(), { waitUntil: "domcontentloaded" });
		await other.waitForSelector(FORM, SERVER);
		await other.fill('[data-testid="kt-sc-unresolved"]', "Recorded from a second window.");
		await other.click('[data-testid="kt-sc-record"]');
		await other.waitForSelector('[data-testid="kt-procset-rule-card"]', SERVER);
		await other.close();

		const before = await page.locator('[data-testid="kt-sc-history-row"]').count();
		await page.click('[data-testid="kt-sc-record"]');
		await expect(page.locator('[data-testid="kt-rule-stale"]')).toContainText("This information has changed since you opened it.", SERVER);
		await page.click('[data-testid="kt-rule-review-latest"]');
		await expect(page.locator('[data-testid="kt-sc-history-row"]')).toHaveCount(before + 1, SERVER);
		await expect(page.locator('[data-testid="kt-sc-unresolved"]')).toHaveValue("Edition still to trace.");
		await expect(page.locator(".modal.show")).toHaveCount(0);
	});

	test("a failed read is shown in place, never a Frappe pop-up", async ({ page }) => {
		await loginAsAdministrator(page);
		const READ = "**/api/method/kentender_core.api.procurement_settings_api.get_regulatory_reference_version";
		await page.route(READ, (route) => route.fulfill({ status: 500, contentType: "application/json", body: JSON.stringify({ exc_type: "Exception" }) }));
		await page.goto(checkLink(), { waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="kt-source-check-error"]')).toBeVisible(SERVER);
		await page.waitForTimeout(400);
		await expect(page.locator(".modal.show")).toHaveCount(0);
		await page.unroute(READ);
	});

	test("a System Manager records source checks with the same screen", async ({ page }) => {
		const { user, password } = systemManager();
		await login(page, user, password);
		const errors = await openCheck(page);
		await expect(page.locator('[data-testid="kt-sc-result"]')).toBeEnabled();
		expect(errors, "console errors").toEqual([]);
	});

	test("at 400px the form and histories fit, with the tables scrolling inside their own box", async ({ page }) => {
		await loginAsAdministrator(page);
		await page.setViewportSize({ width: 400, height: 900 });
		await openCheck(page);
		const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
		expect(overflow, "horizontal overflow at 400px").toBeLessThanOrEqual(1);
		await page.locator('[data-testid="kt-sc-record"]').scrollIntoViewIfNeeded();
		await expect(page.locator('[data-testid="kt-sc-record"]')).toBeInViewport();
	});
});
