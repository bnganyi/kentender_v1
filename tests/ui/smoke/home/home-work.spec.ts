import { expect, test } from "@playwright/test";

import { AMINA, BRIAN, CHARLES, NAOMI, PETER, flat, putWorldClock, openHomeFromMenu, region, root, rows } from "./helpers";

/**
 * HOME-CHG-001 v0.6 plan Phase 5 — the work regions as the seeded personas, entered from the sidebar menu.
 * Slice A: Tenders, Bid opening, Evaluation, Award (Charles, Amina, Brian). Slice B: Needs, Requisitions and the
 * oversight regions (Peter, Naomi). Acceptance: HOME-AC-01, 02, 05, 09, 11, 12, 13 (the browser half).
 */
test.describe.configure({ mode: "serial", timeout: 180_000 });

test.beforeAll(() => putWorldClock());

const title = (page: any) => page.locator('[data-testid="kt-home-title"]');
const summary = async (page: any) => (await page.locator('[data-testid^="kt-home-summary-"]').allInnerTexts()).map((t: string) => t.replace(/\s+/g, " ").trim());

test.describe("Charles, Head of Procurement Function (slice A)", () => {
	test("opens from the menu to his header, his three summary columns and no console errors", async ({ page }) => {
		const errors = await openHomeFromMenu(page, CHARLES);
		await expect(title(page)).toHaveText("Good morning, Charles");
		await expect(page.locator('[data-testid="kt-home-responsibilities"]')).toHaveText("Head of Procurement Function, site-wide");
		await expect(page.locator('[data-testid="kt-home-updated"]')).toContainText("Updated 18 June 2027, 10:00 EAT");
		expect(await summary(page)).toEqual([
			"My work 10 actions for you",
			"Waiting on others 3 items you're waiting on",
			"Records you oversee 6 records with outstanding matters",
		]);
		expect(errors, errors.join("\n")).toEqual([]);
	});

	test("My work leads with the title, shows the owner's action and timing, and only the first Continue is primary", async ({ page }) => {
		await openHomeFromMenu(page, CHARLES);
		const list = rows(page, "my-work");
		await expect(list).toHaveCount(5);
		expect(await flat(list.nth(0))).toBe("Supply of medical-grade tablets Tenders TND-MOH-2026-005 Respond to clarification Received 16 days ago (2 June, 10:00) Continue");
		expect(await flat(list.nth(4))).toBe("Supply of network switches Evaluation TND-MOH-2026-010 Assign evaluation secretary Received 5 days ago (13 June, 08:58) Continue");
		const buttons = region(page, "my-work").locator('[data-testid="kt-home-continue"]');
		expect(await buttons.evaluateAll((els) => els.map((e) => e.classList.contains("btn-primary")))).toEqual([true, false, false, false, false]);
		await expect(region(page, "my-work")).not.toContainText("Your turn");
	});

	test("Show more appends the next five in place, leaves the count, and moves focus to the first appended row", async ({ page }) => {
		await openHomeFromMenu(page, CHARLES);
		await expect(page.locator('#my-work [data-testid="kt-home-showing"]')).toHaveText("Showing 5 of 10");
		const more = page.locator('#my-work [data-testid="kt-home-show-more"]');
		await expect(more).toContainText("Show 5 more");
		await more.click();
		await expect(rows(page, "my-work")).toHaveCount(10);
		await expect(page.locator('#my-work [data-testid="kt-home-showing"]')).toHaveText("Showing 10 of 10");
		await expect(page.locator('#my-work [data-testid="kt-home-show-more"]')).toHaveCount(0);
		expect((await summary(page))[0]).toBe("My work 10 actions for you");
		const focused = await page.evaluate(() => (document.activeElement as HTMLElement | null)?.closest("[data-key]")?.getAttribute("data-key") || "");
		const sixth = await rows(page, "my-work").nth(5).getAttribute("data-key");
		expect(focused).toBe(sixth);
		await expect(page.locator('[data-testid="kt-home-live"]')).toHaveText("Showing 10 of 10");
	});

	test("Coming up shows the chair's Start opening with a relative badge and the exact time", async ({ page }) => {
		await openHomeFromMenu(page, CHARLES);
		await expect(rows(page, "coming-up")).toHaveCount(1);
		expect(await flat(rows(page, "coming-up").first())).toBe("Supply of medical-grade tablets Bid opening TND-MOH-2026-005 Start opening In 7 days 25 June, 11:00 View record");
	});

	test("Waiting on others names who holds each item and since when", async ({ page }) => {
		await openHomeFromMenu(page, CHARLES);
		const list = rows(page, "waiting");
		await expect(list).toHaveCount(3);
		expect(await flat(list.nth(0))).toBe("Supply of network switches Waiting for Amina Hassan to appoint the evaluation committee Waiting 5 days (since 13 June, 08:58)");
		expect(await flat(list.nth(1))).toBe("Supply of UPS units Waiting for Amina Hassan to decide publication Waiting 2 days (since 16 June, 15:30)");
		expect(await flat(list.nth(2))).toBe("Supply of laboratory desktop computers Waiting for Amina Hassan to decide the award Waiting 1 day (since 17 June, 16:00)");
	});

	test("Records you oversee counts outstanding matters, pages, and never shows a bid detail before delivery", async ({ page }) => {
		await openHomeFromMenu(page, CHARLES);
		await expect(rows(page, "oversee")).toHaveCount(5);
		await expect(page.locator('#oversee [data-testid="kt-home-showing"]')).toHaveText("Showing 5 of 6");
		await expect(page.locator('#oversee [data-testid="kt-home-show-more"]')).toContainText("Show 1 more");
		const text = await flat(region(page, "oversee"));
		expect(text).toContain("Supply of document scanners Committee review outstanding");
		expect(text).not.toMatch(/bidder|bids? received|score|finding/i); // Evaluation is status-only before the report is delivered
		// The Analytics link follows the server's verdict (ANL-CHG-001 v0.8, Gate ANL-G06): Charles may open Analytics.
		const analytics = page.locator('[data-testid="kt-home-analytics-link"]');
		await expect(analytics).toHaveText("See all in Procurement Analytics");
		await expect(analytics).toHaveAttribute("href", "/app/analytics");
		expect(await analytics.evaluate((el) => el.closest("#oversee") !== null)).toBe(true); // it sits in Records you oversee, after its rows
	});

	test("Recently completed actions read as the actor's own action with its exact time", async ({ page }) => {
		await openHomeFromMenu(page, CHARLES);
		await expect(region(page, "completed")).toContainText("You signed the professional opinion on 17 June 2027, 16:00 EAT.");
		await expect(region(page, "completed")).toContainText("You approved this Tender package on 16 June 2027, 15:30 EAT. It is awaiting publication authorisation by Amina Hassan.");
		await expect(page.locator('#completed [data-testid="kt-home-showing"]')).toHaveText("Showing 5 of 19");
	});

	test("Continue opens the owner's own route and writes nothing", async ({ page }) => {
		await openHomeFromMenu(page, CHARLES);
		await rows(page, "my-work").nth(4).locator('[data-testid="kt-home-continue"]').click();
		await expect(page).toHaveURL(/\/desk\/tenders\/TND-MOH-2026-010\/evaluation\/secretary$/, { timeout: 60_000 });
		await expect(root(page)).toBeHidden(); // Home stays mounted behind the next page (AGENTS.md §6.1), so it is hidden, not removed
	});
});

test.describe("Amina, Accounting Officer (slice A)", () => {
	test("her four decisions across three modules, oldest first, with their exact timings", async ({ page }) => {
		await openHomeFromMenu(page, AMINA);
		await expect(title(page)).toHaveText("Good morning, Amina");
		await expect(page.locator('[data-testid="kt-home-responsibilities"]')).toHaveText("Accounting Officer, site-wide");
		expect((await summary(page))[0]).toBe("My work 4 actions for you");
		const list = rows(page, "my-work");
		await expect(list).toHaveCount(4);
		expect(await flat(list.nth(0))).toBe("Supply of network switches Evaluation TND-MOH-2026-010 Appoint the evaluation committee Received 5 days ago (13 June, 08:58) Continue");
		expect(await flat(list.nth(1))).toBe("Supply of field laptops Tenders TND-MOH-2026-006 Consider cancellation Received 2 days ago (16 June, 14:00) Continue");
		expect(await flat(list.nth(2))).toBe("Supply of UPS units Tenders TND-MOH-2026-011 Authorise publication Received 2 days ago (16 June, 15:30) Continue");
		expect(await flat(list.nth(3))).toBe("Supply of laboratory desktop computers Award TND-MOH-2026-004 Decide award Received yesterday (17 June, 16:00) Continue");
		await expect(region(page, "my-work").locator('[data-testid="kt-home-show-more"]')).toHaveCount(0);
	});

	test("an owner deadline that has passed reads Overdue since, and nothing is overdue from age alone", async ({ page }) => {
		await openHomeFromMenu(page, AMINA);
		expect(await flat(rows(page, "waiting").nth(1))).toBe("Supply of desktop computers Waiting for cancellation compliance evidence from Brian Wafula Waiting 3 days (since 15 June, 12:00) Overdue since 15 June");
		await expect(region(page, "my-work")).not.toContainText("Overdue"); // old work (5 days) is not overdue: no owner deadline
	});

	test("the oversight she holds is read-only, with no Continue button anywhere in the rail", async ({ page }) => {
		await openHomeFromMenu(page, AMINA);
		await expect(page.locator('[data-testid="kt-home-rail"] button').filter({ hasText: "Continue" })).toHaveCount(0);
		expect((await summary(page))[2]).toBe("Records you oversee 6 records with outstanding matters");
	});
});

test.describe("Brian, Procurement Officer (slice A)", () => {
	test("his overdue cancellation evidence leads, his clarifications follow, and he has no oversight column", async ({ page }) => {
		await openHomeFromMenu(page, BRIAN);
		await expect(title(page)).toHaveText("Good morning, Brian");
		expect(await summary(page)).toEqual(["My work 9 actions for you", "Waiting on others 1 item you're waiting on"]);
		expect(await flat(rows(page, "my-work").first())).toBe("Supply of desktop computers Tenders TND-MOH-2026-012 Record cancellation notices and PPRA report Received 3 days ago (15 June, 12:00) Overdue since 15 June Continue");
		await expect(region(page, "waiting")).toContainText("Waiting for Amina Hassan to consider cancellation");
		await expect(region(page, "oversee")).toHaveCount(0);
	});
});

test.describe("Peter and Naomi (slice B: Needs, Requisitions and oversight)", () => {
	test("Peter decides a Need, waits on a Requisition, and oversees six records", async ({ page }) => {
		await openHomeFromMenu(page, PETER);
		await expect(title(page)).toHaveText("Good morning, Peter");
		await expect(page.locator('[data-testid="kt-home-responsibilities"]')).toContainText("Head of User Department, Human Resources Management and Development");
		expect(await flat(rows(page, "my-work").first())).toBe("Digital health workforce certification programme Needs NDS-MOH-2027-0002 Decide whether this requirement is available to Procurement Planning Submitted 206 days ago (24 November 2026, 12:20) Continue");
		expect(await flat(region(page, "waiting"))).toContain("Clinic desktop computers Waiting for Charles Mutiso to authorise the requisition Waiting 2 days (since 16 June, 11:00)");
		expect((await summary(page))[2]).toBe("Records you oversee 6 records with outstanding matters");
		await expect(region(page, "oversee")).not.toContainText("awaiting correction by"); // a department head sees the neutral line: no holder name
		await expect(region(page, "oversee")).toContainText("Returned for correction");
	});

	test("Naomi has nothing to act on, so the sentence leads and Records you oversee moves into the main column", async ({ page }) => {
		await openHomeFromMenu(page, NAOMI);
		await expect(page.locator('[data-testid="kt-home-nothing"]')).toHaveText("Nothing needs your action right now.");
		expect(await summary(page)).toEqual(["My work 0 actions for you", "Waiting on others 0 items you're waiting on", "Records you oversee 8 records with outstanding matters"]);
		await expect(page.locator('[data-testid="kt-home-main"]')).toHaveClass(/is-full/);
		await expect(page.locator("aside")).toHaveCount(0);
		await expect(region(page, "oversee").locator("h2")).toHaveClass(/is-main/);
		await expect(rows(page, "oversee")).toHaveCount(5);
		await expect(page.locator('#oversee [data-testid="kt-home-show-more"]')).toContainText("Show 3 more");
	});
});
