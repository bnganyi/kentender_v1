import { test, expect } from "@playwright/test";

import { loginAsNdsFixtureAuthor, loginAsNdsFixtureReviewer } from "../../helpers/auth";
import {
	clearFixtures,
	collectConsoleErrors,
	expectScreen,
	gotoNeeds,
	resetFixture,
	selectContext,
} from "./helpers";

/**
 * NDS-CHG-001 v1.1 — NDS-UI-06 accepted source detail
 * (`/app/departmental-needs/{need_reference}/accepted/{version_number}`).
 *
 * The last of DEBT-06's four screens. It is the deep link Procurement Planning
 * follows to read the exact accepted version a Plan Item was built from, so
 * the rule that matters is §12.4: when the pinned version has been superseded,
 * the page stays **historically readable** at the version that was asked for
 * and names the current one — it must not redirect or silently rewrite the
 * route to the newer version, or Planning's lineage would read as though it
 * had always pointed at the successor.
 *
 * Fixture: `reset_accepted_source_fixture` — Version 1 accepted then superseded
 * by an accepted Version 2, under PE-CGKIS (DEBT-07).
 */

const NEED = "NDS-CGKIS-2027-0001";

test.describe.configure({ mode: "serial" });

test.describe("NDS-UI-06 accepted source detail", () => {
	test.beforeAll(() => resetFixture("reset_accepted_source_fixture"));
	test.afterAll(() => clearFixtures());

	test("a superseded version stays readable at the route that asked for it", async ({ page }) => {
		const errors = collectConsoleErrors(page);
		await loginAsNdsFixtureReviewer(page);
		await gotoNeeds(page, `/${NEED}/accepted/1`);
		await expectScreen(page, "detail");

		// §12.4 — the requested version is still the one on screen. Asserting the
		// URL is the point: a redirect to /accepted/2 would satisfy any content
		// check that only looked for "some accepted version".
		await expect(page).toHaveURL(new RegExp(`/departmental-needs/${NEED}/accepted/1$`));
		await expect(page.locator('[data-testid="nds-shell"]')).toHaveAttribute(
			"data-reference",
			NEED,
		);
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("the current accepted version is reachable at its own route", async ({ page }) => {
		const errors = collectConsoleErrors(page);
		await loginAsNdsFixtureReviewer(page);
		await gotoNeeds(page, `/${NEED}/accepted/2`);
		await expectScreen(page, "detail");
		await expect(page).toHaveURL(new RegExp(`/departmental-needs/${NEED}/accepted/2$`));
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("the unpinned detail route shows the Need without a pinned version", async ({ page }) => {
		const errors = collectConsoleErrors(page);
		await loginAsNdsFixtureAuthor(page);
		await gotoNeeds(page, "");
		await selectContext(page, "CGK-DEPT-HEALTH");
		await expectScreen(page, "workspace");

		// Reaching the detail the way a user does — from the row — rather than by
		// typing the route, so this also covers the workspace → detail hop.
		await page
			.locator(`[data-testid="nds-need-row"][data-reference="${NEED}"] [data-testid="nds-row-action"]`)
			.click();
		await expectScreen(page, "detail");
		await expect(page).toHaveURL(new RegExp(`/departmental-needs/${NEED}$`));
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});
});
