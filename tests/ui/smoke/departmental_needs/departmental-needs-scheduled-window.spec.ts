import { test, expect } from "@playwright/test";

import { loginAsNdsFixtureAuthor } from "../../helpers/auth";
import { collectConsoleErrors, expectScreen, gotoNeeds, resetFixture, selectContext } from "./helpers";

/**
 * CTX-CHG-001 rule 4 — the workspace always shows the selected PE, the
 * selected department, a CHANGEABLE Financial Year and the intake state with
 * its exact opening and closing instants; a Scheduled window disables
 * creation without ever trapping the user in that year.
 */

test.describe.configure({ mode: "serial" });

const OPEN_FY = "FY-2027-2028";
const SCHEDULED_FY = "FY-2098-2099";

test.describe("CTX-CHG-001 workspace context band", () => {
	test.beforeEach(() => resetFixture("reset_scheduled_window_fixture"));

	test("a Scheduled year disables creation and never traps", async ({ page }) => {
		const errors = collectConsoleErrors(page);
		await loginAsNdsFixtureAuthor(page);
		await gotoNeeds(page, "");
		await selectContext(page, "CGK-DEPT-HEALTH", OPEN_FY);
		await expectScreen(page, "workspace");

		// The band's FY selector is always rendered, even while a year is open.
		const fySelect = page.locator('[data-testid="nds-fy-band-select"]');
		await expect(fySelect).toBeVisible();
		await expect(page.locator('[data-testid="nds-intake-state"]')).toHaveText("Open");
		await expect(page.locator('[data-testid="nds-create-need"]')).toBeVisible();

		// Select the future year: state flips to Scheduled with exact instants
		// and creation disappears. The band alone carries this — the separate
		// notice panel duplicated it and was removed (user request 2026-08-30).
		await fySelect.selectOption(SCHEDULED_FY);
		await expect(page.locator('[data-testid="nds-intake-state"]')).toHaveText("Scheduled");
		await expect(page.locator('[data-testid="nds-intake-instants"]')).toContainText("Opens");
		await expect(page.locator('[data-testid="nds-intake-instants"]')).toContainText("Closes");
		await expect(page.locator('[data-testid="nds-create-need"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="nds-scheduled-notice"]')).toHaveCount(0);

		// And straight back — the selection is never a trap.
		await fySelect.selectOption(OPEN_FY);
		await expect(page.locator('[data-testid="nds-intake-state"]')).toHaveText("Open");
		await expect(page.locator('[data-testid="nds-create-need"]')).toBeVisible();
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("the module remembers its last financial year server-side", async ({ page }) => {
		const errors = collectConsoleErrors(page);
		await loginAsNdsFixtureAuthor(page);
		await gotoNeeds(page, "");
		await selectContext(page, "CGK-DEPT-HEALTH", OPEN_FY);
		await expectScreen(page, "workspace");
		await page.locator('[data-testid="nds-fy-band-select"]').selectOption(SCHEDULED_FY);
		await expect(page.locator('[data-testid="nds-intake-state"]')).toHaveText("Scheduled");

		// A full reload carries no client state; the server remembers.
		await gotoNeeds(page, "");
		await expectScreen(page, "workspace");
		await expect(page.locator('[data-testid="nds-fy-band-select"]')).toHaveValue(SCHEDULED_FY);
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("Change context is always available once resolved", async ({ page }) => {
		const errors = collectConsoleErrors(page);
		await loginAsNdsFixtureAuthor(page);
		await gotoNeeds(page, "");
		await selectContext(page, "CGK-DEPT-HEALTH", OPEN_FY);
		await expectScreen(page, "workspace");
		await page.locator('[data-testid="nds-change-context"]').click();
		await expect(page.locator('[data-testid="nds-shell"]')).toHaveAttribute(
			"data-screen",
			"context-selection",
		);
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});
});

test.describe("CTX-CHG-001 rail PE switcher", () => {
	test.beforeEach(() => resetFixture("reset_open_intake_fixture"));

	test("a single-PE author sees a chip, not a selector", async ({ page }) => {
		const errors = collectConsoleErrors(page);
		await loginAsNdsFixtureAuthor(page);
		await gotoNeeds(page, "");
		await selectContext(page, "CGK-DEPT-HEALTH");
		await expectScreen(page, "workspace");
		await expect(page.locator('[data-testid="kt-rail-pe"]')).toBeVisible();
		await expect(page.locator('[data-testid="kt-rail-pe-current"]')).toBeVisible();
		await expect(page.locator('[data-testid="kt-rail-pe-select"]')).toHaveCount(0);
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});
});
