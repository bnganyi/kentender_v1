import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";

/**
 * Step 2 — App-wide Civic Ledger shell (native sidebar + route registry).
 *
 * On registered IT wizard routes: native .body-sidebar stays visible, Frappe
 * .navbar is hidden, #kt-cl-chrome-host persists, page header/title render.
 * Leaving a registered route tears the shell down.
 */

const NATIVE_RAIL = ".body-sidebar";
const CHROME_HOST = '[data-testid="kt-cl-chrome-host"]';
const PAGE_HEADER = '[data-testid="kt-cl-page-header"]';
const PAGE_TITLE = '[data-testid="kt-cl-page-title"]';
const UI00_ROOT = '[data-testid="kt-cl-ui00-root"]';

test.describe("IT STD Wizard — Civic Ledger shell (Step 2)", () => {
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1280, height: 800 });
		await loginAsAdministrator(page);
	});

	test("UI-00 activates native shell: rail visible, chrome host, navbar hidden", async ({ page }) => {
		await page.goto("/desk/it-tender-configuration-dashboard");
		await expect(page.locator(NATIVE_RAIL)).toBeVisible({ timeout: 30_000 });
		await expect(page.locator("#kt-cl-sidenav")).toHaveCount(0);
		await expect(page.locator(CHROME_HOST)).toBeVisible({ timeout: 15_000 });
		await expect(page.locator(PAGE_HEADER)).toBeVisible();
		await expect(page.locator(PAGE_TITLE)).toContainText("Tender Configurations");
		await expect(page.locator(UI00_ROOT)).toBeVisible();

		const state = await page.evaluate(() => {
			const body = document.body;
			const navbar =
				(document.querySelector("header.navbar") as HTMLElement | null) ||
				(document.querySelector(".navbar") as HTMLElement | null);
			return {
				hasNative: body.classList.contains("kt-cl-shell-native"),
				hasShell: body.classList.contains("kt-cl-shell"),
				navbarHidden:
					!navbar ||
					getComputedStyle(navbar).display === "none" ||
					getComputedStyle(navbar).visibility === "hidden",
			};
		});
		expect(state.hasNative).toBe(true);
		expect(state.hasShell).toBe(true);
		expect(state.navbarHidden).toBe(true);
	});

	test("UI-00 primary create action is present in the page header", async ({ page }) => {
		await page.goto("/desk/it-tender-configuration-dashboard");
		await expect(page.locator(PAGE_HEADER)).toBeVisible({ timeout: 30_000 });
		await expect(
			page.locator('[data-testid="kt-cl-action-create-tender-config"]')
		).toBeVisible();
	});

	test("chrome host persists when navigating to another registered stub route", async ({ page }) => {
		await page.goto("/desk/it-tender-configuration-dashboard");
		await expect(page.locator(CHROME_HOST)).toBeVisible({ timeout: 30_000 });

		await page.goto("/desk/it-tender-configuration-overview");
		await expect(page.locator(NATIVE_RAIL)).toBeVisible({ timeout: 30_000 });
		await expect(page.locator(CHROME_HOST)).toBeVisible({ timeout: 15_000 });

		const stillNative = await page.evaluate(() =>
			document.body.classList.contains("kt-cl-shell-native")
		);
		expect(stillNative).toBe(true);
	});

	test("leaving a registered route tears down the shell and restores Frappe navbar", async ({
		page,
	}) => {
		await page.goto("/desk/it-tender-configuration-dashboard");
		await expect(page.locator(CHROME_HOST)).toBeVisible({ timeout: 30_000 });

		await page.goto("/desk/build");
		await page.waitForTimeout(500);

		const state = await page.evaluate(() => {
			const body = document.body;
			const navbar = document.querySelector(".navbar") as HTMLElement | null;
			return {
				hasNative: body.classList.contains("kt-cl-shell-native"),
				chromeCount: document.querySelectorAll("#kt-cl-chrome-host").length,
				navbarDisplay: navbar ? getComputedStyle(navbar).display : "missing",
			};
		});
		expect(state.hasNative).toBe(false);
		expect(state.chromeCount).toBe(0);
		expect(state.navbarDisplay).not.toBe("none");
	});
});
