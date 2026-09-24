import { test, expect, Page } from "@playwright/test";
import { login, loginAsAdministrator } from "../../helpers/auth";
import { collectPageErrors } from "../../helpers/designFidelity";
import { restoreSite, systemManager } from "./helpers";

/**
 * CFG-CHG-002 v0.14 §10.9 (tracker CFG14-5F) — Procurement schedules and
 * working-day calendars in a real browser, on the canonical site. Structure
 * is the fidelity gate's job; this proves: the schedules list and a saved
 * schedule by its link; a calendar added, corrected in place while nothing
 * depends on it, replaced by a new version with its reason, its history, and
 * a source check recorded on it — each view with its own link surviving
 * reload; the failed-read state; a second setup role; the narrow layout.
 *
 * Writes: calendars and schedules named "Playwright…" (and checks on them),
 * removed by restoreSite → purge_playwright_calendars / _schedules.
 */
const SERVER = { timeout: 20_000 };
const SECTION = "/app/system-setup#procurement-settings/schedule-profiles";
const CAL = "Playwright calendar";

function hash(page: Page): string {
	return decodeURIComponent(new URL(page.url()).hash);
}

async function openSchedules(page: Page): Promise<string[]> {
	const errors = collectPageErrors(page);
	await page.goto(SECTION, { waitUntil: "domcontentloaded" });
	await page.waitForSelector('[data-testid="kt-procset-profiles"]', SERVER);
	return errors;
}

test.describe.serial("System setup — Procurement schedules and calendars", () => {
	test.afterAll(() => restoreSite());

	test("the schedules list and a saved schedule by its link, with the board's columns and facts", async ({ page }) => {
		await loginAsAdministrator(page);
		const errors = await openSchedules(page);
		await expect(page.locator('[data-testid="kt-procset-profiles"] th')).toHaveText([
			"Name", "Method", "Procedure", "Category", "Version", "Applies from", "Applies until", "Source check", "Action",
		]);
		await page.click('[data-testid="kt-procset-profile-view-SPR-OPEN-TENDER-GOODS-V1"]');
		await page.waitForSelector('[data-testid="kt-procset-profile-table"]', SERVER);
		expect(hash(page)).toBe("#procurement-settings/schedule-profiles/SPR-OPEN-TENDER-GOODS-V1");
		await expect(page.locator('[data-testid="kt-procset-profile-title"]')).toHaveText("Open Tender — goods");
		await expect(page.locator('[data-testid="kt-procset-profile-intervals"] th')).toHaveCount(9);
		await expect(page.locator('[data-testid="kt-procset-profile-table"] input')).toHaveCount(0);
		await page.reload({ waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="kt-procset-profile-title"]')).toHaveText("Open Tender — goods", SERVER);
		await page.goBack();
		await page.waitForSelector('[data-testid="kt-procset-profiles"]', SERVER);
		expect(errors, "console errors").toEqual([]);
	});

	test("a calendar: added, corrected in place, replaced by a new version with its reason, and its history", async ({ page }) => {
		await loginAsAdministrator(page);
		const errors = await openSchedules(page);
		await page.click('[data-testid="kt-procset-calendar-add"]');
		await page.waitForSelector('[data-testid="kt-calendar-editor"]', SERVER);
		expect(hash(page)).toBe("#procurement-settings/calendars/new");
		await page.fill('[data-testid="kt-cal-name"]', CAL);
		await page.fill('[data-testid="kt-cal-from"]', "2098-07-01");
		await page.fill('[data-testid="kt-cal-until"]', "2099-06-30");
		await page.click('[data-testid="kt-cal-add-holiday"]');
		await page.fill('[data-testid="kt-cal-holiday-date-0"]', "2098-12-12");
		await page.fill('[data-testid="kt-cal-holiday-name-0"]', "Jamhuri Day");
		await page.fill('[data-testid="kt-cal-holiday-source-0"]', "Public Holidays Act s.2");
		await page.click('[data-testid="kt-cal-save"]');

		// Saved: its own detail, with its link.
		await page.waitForSelector('[data-testid="kt-calendar-detail"]', SERVER);
		const first = hash(page).split("/").pop()!;
		await expect(page.locator('[data-testid="kt-cal-holidays"]')).toContainText("Public Holidays Act s.2");
		// Nothing depends on it yet, so it is corrected in place (D15).
		await expect(page.locator('[data-testid="kt-cal-readonly"]')).toHaveCount(0);
		await page.click('[data-testid="kt-cal-edit"]');
		await page.waitForSelector('[data-testid="kt-cal-correcting-notice"]', SERVER);
		expect(hash(page)).toBe(`#procurement-settings/calendars/${first}/edit`);
		await page.locator('[data-testid="kt-cal-weekend-Friday"]').check({ force: true });
		await page.click('[data-testid="kt-cal-save"]');
		await page.waitForSelector('[data-testid="kt-calendar-detail"]', SERVER);
		await expect(page.locator('[data-testid="kt-cal-weekend-ro"]')).toContainText("Friday", SERVER);
		await expect(page.locator('[data-testid="kt-cal-version"]')).toHaveText("1");

		// A new version: overlapping dates replace Version 1, with the reason.
		await page.click('[data-testid="kt-cal-new-version"]');
		await page.waitForSelector('[data-testid="kt-cal-reason"]', SERVER);
		expect(hash(page)).toBe(`#procurement-settings/calendars/${first}/new-version`);
		await page.reload({ waitUntil: "domcontentloaded" });
		await page.waitForSelector('[data-testid="kt-cal-reason"]', SERVER);
		await page.fill('[data-testid="kt-cal-from"]', "2099-01-01");
		await page.fill('[data-testid="kt-cal-until"]', "2099-06-30");
		await expect(page.locator('[data-testid="kt-cal-replaces"]')).toHaveValue("Version 1");
		await page.fill('[data-testid="kt-cal-reason"]', "Gazetted holidays added.");
		await page.click('[data-testid="kt-cal-save"]');
		await page.waitForSelector('[data-testid="kt-calendar-detail"]', SERVER);
		await expect(page.locator('[data-testid="kt-cal-version"]')).toHaveText("2", SERVER);
		await expect(page.locator('[data-testid="kt-cal-change-reason"]')).toHaveText("Gazetted holidays added.");
		const second = hash(page).split("/").pop()!;

		// Its usage and history lists both versions.
		await page.click('[data-testid="kt-cal-history"]');
		await page.waitForSelector('[data-testid="kt-calendar-history"]', SERVER);
		expect(hash(page)).toBe(`#procurement-settings/calendars/${second}/history`);
		await expect(page.locator('[data-testid^="kt-sc-version-view-"]')).toHaveCount(2, SERVER);
		await expect(page.locator('[data-testid="kt-sc-version-2"]')).toContainText("Administrator");
		await page.click('[data-testid="kt-sc-version-view-1"]');
		await page.waitForSelector('[data-testid="kt-calendar-detail"]', SERVER);
		expect(hash(page)).toBe(`#procurement-settings/calendars/${first}`);
		await expect(page.locator(".modal.show")).toHaveCount(0);
		expect(errors, "console errors").toEqual([]);
	});

	test("Check sources on a calendar records against that calendar and returns to it", async ({ page }) => {
		await loginAsAdministrator(page);
		const response = await page.request.get("/api/method/kentender_core.api.procurement_settings_api.get_procurement_settings");
		const calendar = ((await response.json()).message.calendars || []).find((row: any) => row.calendar_name === CAL && row.version_number === 2);
		expect(calendar, "the calendar the previous test added").toBeTruthy();
		const errors = collectPageErrors(page);
		await page.goto(`/app/system-setup#procurement-settings/calendars/${calendar.calendar}`, { waitUntil: "domcontentloaded" });
		await page.waitForSelector('[data-testid="kt-calendar-detail"]', SERVER);
		await page.click('[data-testid="kt-cal-check-sources"]');
		await page.waitForSelector('[data-testid="kt-source-check-form"]', SERVER);
		await expect(page.locator('[data-testid="kt-source-check-form"] .kt-meta-row').first()).toContainText("Working-day calendar");
		await page.fill('[data-testid="kt-sc-unresolved"]', "Holiday list awaiting gazettement.");
		await page.click('[data-testid="kt-sc-record"]');
		await page.waitForSelector('[data-testid="kt-calendar-detail"]', SERVER);
		expect(hash(page)).toBe(`#procurement-settings/calendars/${calendar.calendar}`);
		// A source check freezes it: no more correction in place.
		await expect(page.locator('[data-testid="kt-cal-readonly"]')).toBeVisible(SERVER);
		await expect(page.locator('[data-testid="kt-cal-edit"]')).toHaveCount(0);
		expect(errors, "console errors").toEqual([]);
	});

	test("Add procurement schedule: an existing method and category lead to its new version; versions replace only on overlap", async ({ page }) => {
		// The canonical site already has a schedule for every method and
		// category, so Add always meets an existing pair here; a first version
		// for a new pair is proven by the component and service tests.
		await loginAsAdministrator(page);
		const errors = await openSchedules(page);
		await page.click('[data-testid="kt-procset-schedule-add"]');
		await page.waitForSelector('[data-testid="kt-procset-schedule-editor"]', SERVER);
		expect(hash(page)).toBe("#procurement-settings/schedule-profiles/new");
		await expect(page.locator('[data-testid="kt-sve-title"]')).toHaveText("Add procurement schedule");
		await page.selectOption('[data-testid="kt-sve-method"]', "Open Tender");
		await page.selectOption('[data-testid="kt-sve-category"]', "Services");
		await expect(page.locator('[data-testid="kt-sve-exists"]')).toBeVisible();
		await expect(page.locator('[data-testid="kt-sve-save"]')).toBeDisabled();
		await page.click('[data-testid="kt-sve-open-existing"]');
		await page.waitForSelector('[data-testid="kt-sve-reason"]', SERVER);
		expect(hash(page)).toMatch(/^#procurement-settings\/schedule-profiles\/SPR-OPEN-TENDER-SERVICES-V\d+\/new-version$/);

		// A far-future version: it overlaps nothing, so it replaces nothing.
		await page.fill('[data-testid="kt-sve-name"]', "Playwright schedule");
		await page.fill('[data-testid="kt-sve-from"]', "2098-07-01");
		await page.fill('[data-testid="kt-sve-until"]', "2099-06-30");
		await expect(page.locator('[data-testid="kt-sve-replaces"]')).toContainText("so it is not replaced");
		await page.click('[data-testid="kt-sve-select-bid_opening"]');
		await expect(page.locator('[data-testid="kt-sve-selected-title"]')).toHaveText("Selected interval — Bid opening");
		await page.fill('[data-testid="kt-sve-i-default"]', "28");
		await page.selectOption('[data-testid="kt-sve-i-basis"]', "Planning assumption");
		await page.fill('[data-testid="kt-sve-reason"]', "Future period drafted.");
		await page.click('[data-testid="kt-sve-save"]');
		await page.waitForSelector('[data-testid="kt-procset-profile-table"]', SERVER);
		await expect(page.locator('[data-testid="kt-procset-profile-title"]')).toHaveText("Playwright schedule", SERVER);
		await expect(page.locator('[data-testid="kt-procset-interval-bid_opening"]')).toContainText("28");
		await expect(page.locator('[data-testid="kt-procset-interval-bid_opening"]')).toContainText("Planning assumption");
		await expect(page.locator('[data-testid="kt-procset-profile-change-reason"]')).toHaveText("Future period drafted.");
		const first = await page.locator('[data-testid="kt-procset-profile-version"]').textContent();

		// Its own successor overlaps it, so it names it and the reason.
		await page.click('[data-testid="kt-procset-profile-new-version"]');
		await page.waitForSelector('[data-testid="kt-sve-reason"]', SERVER);
		await page.fill('[data-testid="kt-sve-from"]', "2099-01-01");
		await expect(page.locator('[data-testid="kt-sve-replaces"]')).toHaveText(`Earlier versions this replaces: Playwright schedule Version ${first}.`);
		await page.fill('[data-testid="kt-sve-reason"]', "Bid opening period confirmed.");
		await page.click('[data-testid="kt-sve-save"]');
		await page.waitForSelector('[data-testid="kt-procset-profile-table"]', SERVER);
		await expect(page.locator('[data-testid="kt-procset-profile-version"]')).toHaveText(String(Number(first) + 1), SERVER);
		await expect(page.locator('[data-testid="kt-procset-profile-change-reason"]')).toHaveText("Bid opening period confirmed.");
		await expect(page.locator(".modal.show")).toHaveCount(0);
		expect(errors, "console errors").toEqual([]);
	});

	test("a failed calendar read is shown in place, never a Frappe pop-up", async ({ page }) => {
		await loginAsAdministrator(page);
		const READ = "**/api/method/kentender_core.api.procurement_settings_api.get_business_day_calendar";
		await page.route(READ, (route) => route.fulfill({ status: 500, contentType: "application/json", body: JSON.stringify({ exc_type: "Exception" }) }));
		await page.goto("/app/system-setup#procurement-settings/calendars/ANY-V1", { waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="kt-calendar-error"]')).toBeVisible(SERVER);
		await page.waitForTimeout(400);
		await expect(page.locator(".modal.show")).toHaveCount(0);
		await page.unroute(READ);
	});

	test("a System Manager reads schedules and calendars with the same screens", async ({ page }) => {
		const { user, password } = systemManager();
		await login(page, user, password);
		const errors = await openSchedules(page);
		await page.click('[data-testid="kt-procset-profile-view-SPR-OPEN-TENDER-GOODS-V1"]');
		await page.waitForSelector('[data-testid="kt-procset-profile-table"]', SERVER);
		expect(errors, "console errors").toEqual([]);
	});

	test("at 400px the schedule detail's wide tables scroll inside their own box", async ({ page }) => {
		await loginAsAdministrator(page);
		await page.setViewportSize({ width: 400, height: 900 });
		await page.goto(`${SECTION}/SPR-OPEN-TENDER-GOODS-V1`, { waitUntil: "domcontentloaded" });
		await page.waitForSelector('[data-testid="kt-procset-profile-table"]', SERVER);
		const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
		expect(overflow, "horizontal overflow at 400px").toBeLessThanOrEqual(1);
	});
});
