import { Browser, expect, Page, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { loginToPortal, waitForPortal } from "../../helpers/portal";
import { collectConsoleErrors, evlFixture, expectNextStep, expectScreen } from "./evlWorld";

/**
 * The canonical evaluation (`make seed-canonical THROUGH=bid_evaluation`,
 * EVL-CHG-001 v0.4 §11.1: report sent on 16 Jun 2027) walked the way people
 * reach it: from the Desk home and the menu (Procurement → Tender Management →
 * Evaluation), or from the Tender's own page, never from a typed address.
 * Read-only: the canonical evaluation is left exactly as seeded.
 */

const PASSWORD = process.env.UI_SEED_PASSWORD || "Test@123";
const REF = "TND-MOH-2027-002";
const CHARLES = "charles.mutiso@moh.example.test";
const GRACE = "grace.wambui@moh.example.test";
const DAVID = "david.ouma@afyadigital.example";

let current: import("@playwright/test").BrowserContext | null = null;
async function as(browser: Browser, user: string): Promise<Page> {
	if (current) await current.close();
	const context = await browser.newContext({ baseURL: process.env.UI_BASE_URL || "http://127.0.0.1:8000" });
	current = context;
	const page = await context.newPage();
	await page.setViewportSize({ width: 1440, height: 1024 });
	await login(page, user, PASSWORD);
	return page;
}

/** Desk home → Procurement → Tender Management → Evaluation (the workspace). */
async function openWorkspaceFromMenu(page: Page): Promise<void> {
	await page.goto("/app", { waitUntil: "domcontentloaded" });
	await page.getByText("Procurement", { exact: true }).first().click();
	const evaluation = page.locator('a[href="/desk/bid-evaluation"]:visible, a[href="/app/bid-evaluation"]:visible');
	if (!(await evaluation.count())) await page.locator("text=Tender Management").first().click();
	await evaluation.first().click();
	await expect(page.locator('[data-testid="evl-workspace"]')).toHaveAttribute("data-loading", "false", { timeout: 30_000 });
}

test.describe.configure({ mode: "serial", timeout: 600_000 });

test.describe("Bid Evaluation, walked from the menu on the canonical Tender", () => {
	// the canonical story's own moment: just after the report reached Charles
	let previous = "";
	test.beforeAll(() => {
		previous = evlFixture<{ previous: string }>("set_instant", { instant: "2027-06-16 14:08:00" }).previous;
	});
	test.afterAll(async () => {
		if (current) await current.close();
		current = null;
		evlFixture("set_instant", { instant: previous });
	});

	test("the Head of Procurement finds the delivered report, now with Award", async ({ browser }) => {
		// AWD-CHG-001 v0.4 §3: Award received the report and the Head's review is
		// Award's opinion task (tests/ui/smoke/award/awd-demo-walk.spec.ts walks it).
		const page = await as(browser, CHARLES);
		const errors = collectConsoleErrors(page);
		await openWorkspaceFromMenu(page);
		const ws = page.locator('[data-testid="evl-workspace"]');
		await expect(ws.locator(".kt-task-row", { hasText: `Review evaluation report for ${REF}` })).toHaveCount(0);
		await page.goto(`/app/tenders/${REF}/evaluation/report`, { waitUntil: "domcontentloaded" });
		await expectScreen(page, "report");
		await expectNextStep(page, "done", /^The committee report was sent to Charles Mutiso on 16 Jun 2027, 14:07 EAT\.$/);
		await expect(page.locator('[data-testid="evl-root"] [data-testid="evl-summary"]')).toContainText("Afya Digital Supplies Limited");
		await expect(page.locator('[data-testid="evl-root"] [data-testid="evl-summary"]')).toContainText("KES 46,400,000.00");
		await expect(page.getByRole("button", { name: /award/i })).toHaveCount(0);
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("the chair finds the evaluation done, and the committee record", async ({ browser }) => {
		const page = await as(browser, GRACE);
		const errors = collectConsoleErrors(page);
		await openWorkspaceFromMenu(page);
		await page.locator(`[data-testid="evl-view-${REF}"]`).click();
		await expectScreen(page, "results");
		await expectNextStep(page, "done", /^The committee report was sent to Charles Mutiso on 16 Jun 2027, 14:07 EAT\.$/);
		await page.locator('[data-testid="evl-root"] [data-testid="evl-tab-committee-record"]').click();
		await expectScreen(page, "committee-record");
		await expect(page.locator('[data-testid="evl-root"]')).toContainText("Please identify the page and section");
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("the supplier reaches the closed question from the Tender page", async ({ page }) => {
		await page.setViewportSize({ width: 390, height: 844 });
		await loginToPortal(page, DAVID, PASSWORD, `/tenders/${REF}`);
		await waitForPortal(page);
		const link = page.locator(`a[href^="/tenders/${REF}/bid/evaluation-clarifications/"]`);
		await expect(link).toBeVisible({ timeout: 30_000 });
		await link.first().click();
		const screen = page.locator('[data-testid="evl-supplier"]');
		await expect(screen).toHaveAttribute("data-state", "Closed", { timeout: 30_000 });
		await expect(screen.locator('[data-testid="evl-next-step-headline"]')).toHaveText("This clarification is closed.");
		await expect(screen).not.toContainText(/Meets|Recommendation|46,400,000/);
	});
});
