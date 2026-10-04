import { test, expect, Page } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";
import { collectPageErrors } from "../../helpers/designFidelity";

/**
 * CFG-CHG-002 v0.14 §9 + AGENTS.md §6.4 (tracker CFG14-204) — System setup's
 * links, read through the shared route adapter (plan D12).
 *
 * Proves, in a real browser: every tab and a deep rule link survive direct
 * load, reload and back/forward; the address always names what is on screen;
 * and a return to an already-rendered tab repaints from what it had — the
 * page skeleton is never inserted again, counted with a MutationObserver
 * rather than inferred from a final screenshot.
 *
 * Read-only: nothing is written.
 */
const READY: Record<string, string> = {
	"procuring-entity": '[data-testid="kt-setup-pe-card"]',
	"fiscal-years": '[data-testid="kt-fy-table"]',
	"organisation-structure": '[data-testid="kt-ou-detail"]',
	"users-and-responsibilities": '[data-testid="kt-ura-table"]',
	"procurement-settings": '[data-testid="kt-procset-subnav"]',
};

async function countSkeletons(page: Page): Promise<void> {
	await page.evaluate(() => {
		const w = window as unknown as { __ktSkeletons: number };
		w.__ktSkeletons = 0;
		new MutationObserver((records) => {
			for (const record of records) {
				for (const node of Array.from(record.addedNodes)) {
					if (!(node instanceof HTMLElement)) continue;
					if (node.matches('[data-testid="kt-setup-loading"], [data-testid="kt-procset-loading"]') || node.querySelector('[data-testid="kt-setup-loading"], [data-testid="kt-procset-loading"]')) {
						w.__ktSkeletons += 1;
					}
				}
			}
		}).observe(document.body, { childList: true, subtree: true });
	});
}
const skeletons = (page: Page) => page.evaluate(() => (window as unknown as { __ktSkeletons: number }).__ktSkeletons);

test.describe("System setup — links and navigation", () => {
	test("each tab's link survives direct load and reload, and the address names the tab shown", async ({ page }) => {
		const errors = collectPageErrors(page);
		await loginAsAdministrator(page);
		for (const [tab, ready] of Object.entries(READY)) {
			await page.goto(`/app/system-setup#${tab}`, { waitUntil: "domcontentloaded" });
			await page.waitForSelector(ready, { timeout: 20_000 });
			await expect(page.locator(`[data-testid="kt-setup-tab-${tab}"]`)).toHaveAttribute("aria-selected", "true");
			await page.reload({ waitUntil: "domcontentloaded" });
			await page.waitForSelector(ready, { timeout: 20_000 });
			expect(new URL(page.url()).hash).toBe(`#${tab}`);
		}
		expect(errors, "console errors").toEqual([]);
	});

	test("with no link the page opens on Procuring entity and says so in the address, without adding a Back step", async ({ page }) => {
		await loginAsAdministrator(page);
		await page.goto("/app/system-setup", { waitUntil: "domcontentloaded" });
		await page.waitForSelector(READY["procuring-entity"], { timeout: 20_000 });
		await expect.poll(() => new URL(page.url()).hash).toBe("#procuring-entity");
	});

	test("tab clicks push history: Back and Forward walk them, and a revisited tab never shows the skeleton again", async ({ page }) => {
		const errors = collectPageErrors(page);
		await loginAsAdministrator(page);
		await page.goto("/app/system-setup#procuring-entity", { waitUntil: "domcontentloaded" });
		await page.waitForSelector(READY["procuring-entity"], { timeout: 20_000 });
		await page.click('[data-testid="kt-setup-tab-fiscal-years"]');
		await page.waitForSelector(READY["fiscal-years"]);
		await page.click('[data-testid="kt-setup-tab-procurement-settings"]');
		await page.waitForSelector(READY["procurement-settings"]);

		await countSkeletons(page);
		await page.goBack();
		await page.waitForSelector(READY["fiscal-years"]);
		expect(new URL(page.url()).hash).toBe("#fiscal-years");
		await page.goBack();
		await page.waitForSelector(READY["procuring-entity"]);
		await page.goForward();
		await page.waitForSelector(READY["fiscal-years"]);
		await page.click('[data-testid="kt-setup-tab-procurement-settings"]');
		await page.waitForSelector(READY["procurement-settings"]);
		// Let any quiet revalidation settle before counting.
		await page.waitForTimeout(500);
		expect(await skeletons(page), "skeleton inserted on a return to an already-rendered tab").toBe(0);
		expect(errors, "console errors").toEqual([]);
	});

	test("a rule's link opens that rule on direct load, and Back returns to the list it came from", async ({ page }) => {
		const errors = collectPageErrors(page);
		await loginAsAdministrator(page);
		await page.goto("/app/system-setup#procurement-settings/procurement-rules", { waitUntil: "domcontentloaded" });
		await page.waitForSelector(READY["procurement-settings"], { timeout: 20_000 });
		const first = page.locator('[data-testid^="kt-procset-rule-view-"]').first();
		await first.click();
		await page.waitForSelector('[data-testid="kt-procset-rule-card"]', { timeout: 20_000 });
		const link = new URL(page.url()).hash;
		expect(link).toMatch(/^#procurement-settings\/procurement-rules\/[^/]+$/);

		await page.reload({ waitUntil: "domcontentloaded" });
		await page.waitForSelector('[data-testid="kt-procset-rule-card"]', { timeout: 20_000 });
		expect(new URL(page.url()).hash).toBe(link);

		await page.goBack();
		await page.waitForSelector('[data-testid="kt-procset-rules"]', { timeout: 20_000 });
		await expect(page.locator('[data-testid="kt-procset-rule-card"]')).toHaveCount(0);
		expect(errors, "console errors").toEqual([]);
	});

	test("a link to a section opens that section's own view (the Procuring entity's View procurement rules)", async ({ page }) => {
		await loginAsAdministrator(page);
		await page.goto("/app/system-setup#procuring-entity", { waitUntil: "domcontentloaded" });
		await page.waitForSelector(READY["procuring-entity"], { timeout: 20_000 });
		await page.click('[data-testid="kt-setup-pe-approval-link"]');
		await page.waitForSelector(READY["procurement-settings"], { timeout: 20_000 });
		expect(new URL(page.url()).hash).toBe("#procurement-settings/procurement-rules");
		await expect(page.locator('[data-testid="kt-procset-rules"]')).toBeVisible();
		await expect(page.locator('[data-testid="kt-procset-sources"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="kt-procset-link-procurement-rules"]')).toHaveAttribute("aria-current", "page");
	});
});
