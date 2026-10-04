import { test, expect, Page } from "@playwright/test";
import { login, loginAsAdministrator } from "../../helpers/auth";
import { collectPageErrors } from "../../helpers/designFidelity";
import { asEmpty, systemManager } from "./helpers";

/**
 * CFG-CHG-002 v0.14 §9/§10.5 (tracker CFG14-5C) — the Funding sources section
 * in a real browser, on the canonical site. Structure is the fidelity gate's
 * job; this proves what a component test cannot: the section as its own view
 * behind the section links, the add/edit dialog drawn over the list with its
 * own link, a real create → disable → re-enable → remove cycle re-read from
 * the server, the referenced source's fixed name, focus, Back/Forward, the
 * empty and failed states, a second setup role, and narrow/200% layouts.
 *
 * Writes: one "Playwright test funding source", removed by its own test and
 * purged again by the gate's teardown.
 */
const SECTION = "/app/system-setup#procurement-settings/funding-sources";
const TEST_SOURCE = "Playwright test funding source";
const LIST = '[data-testid="kt-procset-sources"]';
const DIALOG = '[data-testid="kt-procset-source-editor"]';
const SETTINGS = "**/api/method/kentender_core.api.procurement_settings_api.get_procurement_settings";
// A command's answer, then the list re-read. Bounded like a reload: the shared
// dev server restarts whenever any app's Python changes, and the first request
// after that is slow.
const SERVER = { timeout: 20_000 };

async function openSection(page: Page, hash = SECTION): Promise<string[]> {
	const errors = collectPageErrors(page);
	await page.goto(hash, { waitUntil: "domcontentloaded" });
	await page.waitForSelector(LIST, { timeout: 20_000 });
	return errors;
}

async function noFrappeModal(page: Page): Promise<void> {
	// Bounded grace wait: a stock Frappe "Message" dialog mounts a tick after.
	await page.waitForTimeout(400);
	await expect(page.locator(".modal.show")).toHaveCount(0);
}

test.describe.serial("System setup — Funding sources", () => {
	test("the section is its own view behind the section links, and opens by default", async ({ page }) => {
		await loginAsAdministrator(page);
		const errors = await openSection(page, "/app/system-setup#procurement-settings");
		const links = page.locator('[data-testid="kt-procset-subnav"] a');
		await expect(links).toHaveText(["Funding sources", "Procurement rules", "Procurement schedules", "Reminders"]);
		await expect(page.locator('[data-testid="kt-procset-link-funding-sources"]')).toHaveAttribute("aria-current", "page");
		await expect(page.locator(`${LIST} h3`)).toHaveText("Funding sources");
		await expect(page.locator(`${LIST} th`)).toHaveText(["Name", "Available for new selection", "Action"]);
		await expect(page.locator('[data-testid="kt-procset-source-Government of Kenya"]')).toContainText("Yes");
		// Absent: the other sections, and any approval or combined-status control.
		for (const other of ["kt-procset-rules", "kt-procset-profiles", "kt-procset-reminder"]) {
			await expect(page.locator(`[data-testid="${other}"]`)).toHaveCount(0);
		}
		await expect(page.getByText(/^(Ready|Approve|Submit for approval)$/)).toHaveCount(0);

		// A section link changes the view and the address; Back returns.
		await page.click('[data-testid="kt-procset-link-procurement-rules"]');
		await page.waitForSelector('[data-testid="kt-procset-rules"]');
		expect(new URL(page.url()).hash).toBe("#procurement-settings/procurement-rules");
		await expect(page.locator(LIST)).toHaveCount(0);
		await page.goBack();
		await page.waitForSelector(LIST);
		expect(errors, "console errors").toEqual([]);
	});

	test("add, disable, re-enable and remove a source: each change is re-read from the server and survives reload", async ({ page }) => {
		await loginAsAdministrator(page);
		const errors = await openSection(page);
		const row = page.locator(`[data-testid="kt-procset-source-${TEST_SOURCE}"]`);
		await expect(row, "left over from an earlier run — run the gate's purge").toHaveCount(0);

		await page.click('[data-testid="kt-procset-source-add"]');
		await page.waitForSelector(DIALOG);
		// The dialog is drawn over the list, with its own link, focus on its first field.
		await expect(page.locator(LIST)).toBeVisible();
		expect(new URL(page.url()).hash).toBe("#procurement-settings/funding-sources/new");
		await expect(page.locator('[data-testid="kt-fs-name"]')).toBeFocused();

		// The exact duplicate defect, before anything is sent.
		await page.fill('[data-testid="kt-fs-name"]', "government of kenya");
		await expect(page.locator('[data-testid="kt-fs-duplicate"]')).toHaveText("Duplicate. A funding source with this name already exists.");
		await expect(page.locator('[data-testid="kt-fs-save"]')).toBeDisabled();

		await page.fill('[data-testid="kt-fs-name"]', TEST_SOURCE);
		await page.click('[data-testid="kt-fs-enabled-no"]');
		await page.click('[data-testid="kt-fs-save"]');
		await expect(page.locator(DIALOG)).toHaveCount(0, SERVER);
		expect(new URL(page.url()).hash).toBe("#procurement-settings/funding-sources");
		await expect(row).toContainText("No", SERVER);

		await page.reload({ waitUntil: "domcontentloaded" });
		await expect(row).toContainText("No", { timeout: 20_000 });

		await page.click(`[data-testid="kt-procset-source-edit-${TEST_SOURCE}"]`);
		await page.waitForSelector(DIALOG);
		expect(new URL(page.url()).hash).toBe(`#procurement-settings/funding-sources/${encodeURIComponent(TEST_SOURCE)}`);
		await expect(page.locator('[data-testid="kt-fs-enabled-no"] input')).toBeChecked();
		await page.click('[data-testid="kt-fs-enabled-yes"]');
		await page.click('[data-testid="kt-fs-save"]');
		await expect(page.locator(DIALOG)).toHaveCount(0, SERVER);
		await expect(row).toContainText("Yes", SERVER);

		// Never used, so it can be removed outright.
		await page.click(`[data-testid="kt-procset-source-remove-${TEST_SOURCE}"]`);
		await page.click('[data-testid="kt-procset-source-remove-confirm"] [data-testid="kt-ou-confirm-accept"]');
		await expect(row).toHaveCount(0, SERVER);
		await page.reload({ waitUntil: "domcontentloaded" });
		await page.waitForSelector(LIST, { timeout: 20_000 });
		await expect(row).toHaveCount(0);
		await noFrappeModal(page);
		expect(errors, "console errors").toEqual([]);
	});

	test("a referenced source keeps its name; Escape closes the dialog and focus returns to its Edit link", async ({ page }) => {
		await loginAsAdministrator(page);
		const errors = await openSection(page);
		const edit = page.locator('[data-testid="kt-procset-source-edit-Government of Kenya"]');
		await edit.focus();
		await page.keyboard.press("Enter");
		await page.waitForSelector(DIALOG);
		await expect(page.locator('[data-testid="kt-fs-name"]')).toBeDisabled();
		await expect(page.locator('[data-testid="kt-fs-locked"]')).toHaveText("This source is referenced by a Budget line and cannot be renamed.");
		await expect(page.locator('[data-testid="kt-fs-enabled-yes"] input')).toBeFocused();
		await page.keyboard.press("Escape");
		await expect(page.locator(DIALOG)).toHaveCount(0);
		await expect(edit).toBeFocused();
		expect(new URL(page.url()).hash).toBe("#procurement-settings/funding-sources");
		expect(errors, "console errors").toEqual([]);
	});

	test("an edit link survives reload, and Back and Forward close and reopen the dialog", async ({ page }) => {
		await loginAsAdministrator(page);
		const errors = await openSection(page);
		await page.click('[data-testid="kt-procset-source-edit-Government of Kenya"]');
		await page.waitForSelector(DIALOG);
		await page.reload({ waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="kt-fs-name"]')).toHaveValue("Government of Kenya", { timeout: 20_000 });
		await page.goBack();
		await expect(page.locator(DIALOG)).toHaveCount(0);
		await expect(page.locator(LIST)).toBeVisible();
		await page.goForward();
		await expect(page.locator(DIALOG)).toBeVisible();
		expect(errors, "console errors").toEqual([]);
	});

	test("an empty catalogue shows its own state, and a failed load is recoverable with Try again", async ({ page }) => {
		await loginAsAdministrator(page);
		await asEmpty(page, { fundingSources: true });
		await openSection(page);
		await expect(page.locator('[data-testid="kt-procset-sources-empty"]')).toContainText("No funding sources yet");
		await expect(page.locator(`${LIST} table`)).toHaveCount(0);
		await page.unrouteAll({ behavior: "wait" });

		await page.route(SETTINGS, (route) => route.fulfill({ status: 500, contentType: "application/json", body: JSON.stringify({ exc_type: "Exception" }) }));
		await page.goto(SECTION, { waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="kt-procset-error"]')).toBeVisible({ timeout: 20_000 });
		await noFrappeModal(page);
		await page.unroute(SETTINGS);
		await page.click('[data-testid="kt-procset-retry"]');
		await page.waitForSelector(LIST);
	});

	test("a System Manager maintains funding sources too, with the same screen", async ({ page }) => {
		const { user, password } = systemManager();
		await login(page, user, password);
		const errors = await openSection(page);
		await page.click('[data-testid="kt-procset-source-add"]');
		await expect(page.locator('[data-testid="kt-fs-name"]')).toBeEditable();
		await page.click('[data-testid="kt-fs-cancel"]');
		await expect(page.locator(DIALOG)).toHaveCount(0);
		expect(errors, "console errors").toEqual([]);
	});

	test("narrow width and 200% text keep the list and the dialog usable with no horizontal scroll", async ({ page }) => {
		await loginAsAdministrator(page);
		for (const [width, zoom] of [[400, 1], [1440, 2]] as const) {
			await page.setViewportSize({ width, height: 900 });
			await openSection(page, `${SECTION}/new`);
			await page.waitForSelector(DIALOG);
			await page.evaluate((z) => ((document.documentElement.style as any).zoom = String(z)), zoom);
			const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
			expect(overflow, `horizontal overflow at ${width}px × ${zoom}`).toBeLessThanOrEqual(1);
			await page.locator('[data-testid="kt-fs-save"]').scrollIntoViewIfNeeded();
			await expect(page.locator('[data-testid="kt-fs-save"]')).toBeInViewport();
			await expect(page.locator('[data-testid="kt-fs-cancel"]')).toBeInViewport();
		}
	});
});
