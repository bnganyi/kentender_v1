import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { collectConsoleErrors } from "../planning/helpers";
import { CHARLES, DANIEL, JOSPHAT, PASSWORD, flat, putWorldClock, openHomeFromMenu, root, rows, waitForHome } from "./helpers";

/**
 * HOME-CHG-001 v0.6 plan Phase 5 — states and navigation: the landing page, a direct load, refresh, browser
 * back and forward, revalidation in place on return, a forced 500 with Try again, the technical reader and a
 * successful empty read. Acceptance: HOME-AC-06, 08 (history), 14 (browser half).
 */
test.describe.configure({ mode: "serial", timeout: 180_000 });

test.beforeAll(() => putWorldClock());

const READ = "**/api/method/kentender_core.api.home.get_home_workspace*";

test.describe("landing and history", () => {
	test("opening /app shows Home for an internal user, and the sidebar item is a plain link", async ({ page }) => {
		const errors = collectConsoleErrors(page);
		await login(page, CHARLES, PASSWORD);
		await page.goto("/app", { waitUntil: "domcontentloaded" });
		await waitForHome(page);
		await expect(page.locator('[data-testid="kt-home-title"]')).toHaveText("Good morning, Charles");
		const item = page.locator(".standard-sidebar-item").filter({ hasText: /^\s*Home\s*$/ }).first();
		await expect(item).not.toContainText("Planned");
		expect(errors, errors.join("\n")).toEqual([]);
	});

	test("a direct load of /desk/home and a refresh keep the page, and ERPNext's own Home workspace no longer answers", async ({ page }) => {
		await login(page, CHARLES, PASSWORD);
		await page.goto("/desk/home", { waitUntil: "domcontentloaded" });
		await waitForHome(page);
		await expect(page.locator('[data-testid="kt-home-summary-my_work"]')).toContainText("10");
		await page.reload({ waitUntil: "domcontentloaded" });
		await waitForHome(page);
		await expect(page).toHaveURL(/\/desk\/home$/);
		await expect(page.getByText("Your Shortcuts")).toHaveCount(0); // ERPNext's Home workspace content
		await expect(page.getByText("Reports & Masters")).toHaveCount(0);
	});

	test("browser back returns to Home with its content at once, and forward returns to the record", async ({ page }) => {
		await openHomeFromMenu(page, CHARLES);
		await rows(page, "my-work").nth(4).locator('[data-testid="kt-home-continue"]').click();
		await expect(page).toHaveURL(/\/evaluation\/secretary$/, { timeout: 60_000 });
		await page.goBack();
		await expect(root(page)).toBeVisible({ timeout: 30_000 });
		await expect(page.locator('[data-testid="kt-home-loading"]')).toHaveCount(0);
		await expect(rows(page, "my-work")).toHaveCount(5);
		await page.goForward();
		await expect(page).toHaveURL(/\/evaluation\/secretary$/, { timeout: 30_000 });
	});

	test("returning to Home re-reads quietly: the page keeps its content and no skeleton is shown", async ({ page }) => {
		await openHomeFromMenu(page, CHARLES);
		let reads = 0;
		await page.route(READ, (route) => {
			reads += 1;
			return route.continue();
		});
		await page.evaluate(() => (window as any).frappe.set_route("technical-search"));
		await expect(root(page)).toBeHidden();
		await page.evaluate(() => (window as any).frappe.set_route("home"));
		await expect(root(page)).toBeVisible();
		await expect(page.locator('[data-testid="kt-home-loading"]')).toHaveCount(0); // never over a page that has content
		await expect(rows(page, "my-work")).toHaveCount(5);
		await expect.poll(() => reads, { timeout: 15_000 }).toBeGreaterThanOrEqual(1);
	});
});

test.describe("failure and recovery", () => {
	test("a failed first read shows the total-failure state, and Try again recovers", async ({ page }) => {
		await login(page, CHARLES, PASSWORD);
		let failing = true; // every read fails until Try again is pressed, so a repeated first read cannot slip through
		await page.route(READ, (route) => {
			if (failing) return route.fulfill({ status: 500, contentType: "application/json", body: JSON.stringify({ exc_type: "ValidationError", exception: "frappe.exceptions.ValidationError: boom" }) });
			return route.continue();
		});
		await page.goto("/desk/home", { waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="kt-home-failed"]')).toContainText("We could not load your work.", { timeout: 60_000 });
		await expect(page.locator('[data-testid="kt-home-summary"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="kt-home-retry-all"]')).toHaveClass(/btn-primary/);
		failing = false;
		await page.locator('[data-testid="kt-home-retry-all"]').click();
		await waitForHome(page);
		await expect(page.locator('[data-testid="kt-home-title"]')).toHaveText("Good morning, Charles");
	});
});

test.describe("the technical reader and an empty read", () => {
	test("Daniel (Technical Operator) sees the orientation, the search link and no business action", async ({ page }) => {
		const errors = await openHomeFromMenu(page, DANIEL);
		await expect(page.locator('[data-testid="kt-home-title"]')).toHaveText("Good morning, Daniel");
		await expect(page.locator('[data-testid="kt-home-responsibilities"]')).toHaveText("Technical Operator, site-wide");
		await expect(page.locator('[data-testid="kt-home-empty-technical"]')).toContainText("Nothing needs your action right now.");
		await expect(page.locator('[data-testid="kt-home-summary"]')).toHaveCount(0);
		await expect(root(page).locator("button")).toHaveCount(0);
		// both header links are for technical readers; the Analytics one follows the server's verdict (ANL-G06)
		await expect(page.locator('[data-testid="kt-home-header-analytics-link"]')).toHaveText("Procurement Analytics");
		await page.locator('[data-testid="kt-home-technical-link"]').click();
		await expect(page).toHaveURL(/\/desk\/technical-search/, { timeout: 30_000 });
		expect(errors, errors.join("\n")).toEqual([]);
	});

	test("an ordinary user never sees the technical link", async ({ page }) => {
		await openHomeFromMenu(page, CHARLES);
		await expect(page.locator('[data-testid="kt-home-technical-link"]')).toHaveCount(0);
	});

	test("a successful read with nothing in it shows the spot and the sentence, not zeros (Josphat)", async ({ page }) => {
		await openHomeFromMenu(page, JOSPHAT);
		expect(await flat(page.locator('[data-testid="kt-home-empty"]'))).toBe("Nothing needs your action right now.");
		await expect(page.locator(".kt-spot.is-success")).toBeVisible();
		await expect(page.locator('[data-testid="kt-home-summary"]')).toHaveCount(0);
		await expect(page.locator("section")).toHaveCount(0);
	});
});
