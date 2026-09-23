import { test, expect } from "@playwright/test";

import { loginAsNdsFixtureAuthor } from "../../helpers/auth";
import { clearFixtures, collectConsoleErrors, expectScreen, gotoNeeds, resetFixture } from "./helpers";

/**
 * NDS-CHG-001 v1.14 §11.8A — the accepted-Need detail screen's dedicated,
 * independently-retriable Planning-status re-check (`get_need_planning_status`,
 * `services/usage.py::planning_status_for_need`/`older_revision_usage`).
 *
 * FOLLOW_UPS.md FU-27 built the real capability (a second async fetch, fired
 * fire-and-forget after the atomic `get_departmental_need` load, with its own
 * loading/retry state) and FU-31 named the 5 resulting states as built but
 * never regression-tested:
 *
 *  - REFRESHING / UNAVAILABLE / UNAVAILABLE-NO-SNAPSHOT are about the
 *    re-check call itself being slow or failing, independent of the rest of
 *    the page (which already rendered from the atomic load) — proven here
 *    with `page.route()` delaying or failing exactly that one endpoint.
 *  - OLDER is a real data state (no network mocking): the current accepted
 *    revision has never itself been projected by Planning, but an earlier
 *    accepted (now superseded) revision's inclusion still stands. The fixture
 *    (`reset_older_revision_fixture`) reuses the exact command sequence
 *    `test_older_revision_usage_walks_back_when_current_revision_is_unprojected`
 *    already proves at the service layer.
 *
 * DES-12-UNAVAILABLE (the withdrawal-review screen's equivalent failure state
 * for `check_accepted_need_withdrawal_dependency`) is covered alongside the
 * rest of NDS-UI-07 in `departmental-needs-withdrawal-review.spec.ts`.
 */

const PLANNING_STATUS_ROUTE =
	"**/api/method/kentender_procurement.departmental_needs.api.get_need_planning_status";

test.describe.configure({ mode: "serial" });

test.describe("NDS-DES-07A Planning-status variants (FU-31)", () => {
	test.afterAll(() => clearFixtures());

	test("REFRESHING — an in-flight re-check shows Updating Planning information, then settles (NDS-DES-07A-REFRESHING)", async ({
		page,
	}) => {
		const fixture = resetFixture<{ need: string }>("reset_disposition_still_active_fixture");
		const errors = collectConsoleErrors(page);
		await loginAsNdsFixtureAuthor(page);

		// The atomic get_departmental_need load is untouched — only the
		// dedicated re-check it fires afterwards is delayed.
		await page.route(PLANNING_STATUS_ROUTE, async (route) => {
			const response = await route.fetch();
			await new Promise((resolve) => setTimeout(resolve, 2500));
			await route.fulfill({ response });
		});

		await gotoNeeds(page, `/${fixture.need}`);
		await expectScreen(page, "detail");

		// Mid-flight: the atomic load's own STILL-ACTIVE facts are already on
		// screen (from get_departmental_need, not the delayed re-check), with
		// the "last confirmed" suffix and the "Updating…" line while the
		// dedicated re-check is still in flight.
		await expect(page.getByText("Updating Planning information…")).toBeVisible();
		await expect(page.getByText(/Still included.*last confirmed/)).toBeVisible();
		await expect(page.getByText(/Not included this year.*last confirmed/)).toBeVisible();
		await expect(page.locator('[data-testid="nds-retry-planning"]')).toHaveCount(0);

		// The delayed call resolves and the screen settles back to the plain
		// presentation, no different from a Need Planning already reported on.
		await expect(page.getByText("Updating Planning information…")).toHaveCount(0, { timeout: 10_000 });
		await expect(page.getByText("Still included", { exact: true })).toBeVisible();
		await expect(page.getByText("Not included this year", { exact: true })).toBeVisible();

		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("UNAVAILABLE — a failed re-check keeps the last-confirmed snapshot and offers Try again (NDS-DES-07A-UNAVAILABLE)", async ({
		page,
	}) => {
		const fixture = resetFixture<{ need: string }>("reset_disposition_still_active_fixture");
		await loginAsNdsFixtureAuthor(page);
		await page.route(PLANNING_STATUS_ROUTE, (route) =>
			route.fulfill({ status: 500, contentType: "application/json", body: JSON.stringify({ exc_type: "Exception" }) }),
		);

		await gotoNeeds(page, `/${fixture.need}`);
		await expectScreen(page, "detail");

		await expect(page.getByText("Planning information is temporarily unavailable.")).toBeVisible();
		await expect(page.getByTestId("nds-retry-planning")).toBeVisible();
		// The pre-existing atomic-load snapshot is kept, not blanked out — with
		// its own "last confirmed" suffix, distinguishing this from a fresh
		// confirmed result.
		await expect(page.getByText(/Still included.*last confirmed/)).toBeVisible();
		await expect(page.getByText(/Not included this year.*last confirmed/)).toBeVisible();

		// Try again re-runs the same (still failing) check; no crash, state holds.
		await page.getByTestId("nds-retry-planning").click();
		await expect(page.getByText("Planning information is temporarily unavailable.")).toBeVisible();
		await expect(page.getByTestId("nds-retry-planning")).toBeVisible();
	});

	test("UNAVAILABLE-NO-SNAPSHOT — a failed re-check with nothing to fall back on shows Unavailable, not a default (NDS-DES-07A-UNAVAILABLE-NO-SNAPSHOT)", async ({
		page,
	}) => {
		const fixture = resetFixture<{ need: string }>("reset_disposition_none_fixture");
		await loginAsNdsFixtureAuthor(page);
		await page.route(PLANNING_STATUS_ROUTE, (route) =>
			route.fulfill({ status: 500, contentType: "application/json", body: JSON.stringify({ exc_type: "Exception" }) }),
		);

		await gotoNeeds(page, `/${fixture.need}`);
		await expectScreen(page, "detail");

		await expect(page.getByText("Planning information is temporarily unavailable.")).toBeVisible();
		await expect(page.getByTestId("nds-retry-planning")).toBeVisible();
		// Both facts read "Unavailable" — never the ordinary "no accepted
		// decision recorded"/"Not included" defaults a caller with a real
		// snapshot would see, and never a "— last confirmed" suffix (there is
		// nothing to have last confirmed). `exact: true` so this counts only
		// the two `.kt-status` badges themselves, not the notice's own prose
		// ("...temporarily unavailable.") that a plain substring match also
		// catches (found live 23 Sep 2026).
		await expect(page.getByText("Unavailable", { exact: true })).toHaveCount(2);
		await expect(page.getByText("No accepted departmental decision recorded", { exact: false })).toHaveCount(0);
		await expect(page.getByText(/last confirmed/)).toHaveCount(0);
	});

	test("OLDER — the current annual plan still uses the previously accepted revision (NDS-DES-07A-OLDER)", async ({
		page,
	}) => {
		const fixture = resetFixture<{ need: string; revision_1: string; revision_2: string }>(
			"reset_older_revision_fixture",
		);
		const errors = collectConsoleErrors(page);
		await loginAsNdsFixtureAuthor(page);

		await gotoNeeds(page, `/${fixture.need}`);
		await expectScreen(page, "detail");

		// The current (Revision 2) accepted version has no projection of its
		// own yet, so the plain "Current annual plan" pill reads Not included —
		// the OLDER disclosure is the separate supplementary fact, never a
		// silent switch of the pill itself (services/usage.py::older_revision_usage's
		// own docstring: "never changes the current revision's own status").
		await expect(page.getByText("Not included", { exact: true })).toBeVisible();
		await expect(page.getByText("The current annual plan still uses the previously accepted details.")).toBeVisible();
		await expect(page.getByText(/Included requirement revision/)).toBeVisible();

		const toggle = page.getByTestId("nds-view-earlier-requirement");
		await expect(toggle).toHaveText("View earlier requirement");
		await toggle.click();
		await expect(toggle).toHaveText("Hide earlier requirement");
		await expect(page.getByText("Earlier required-by date")).toBeVisible();

		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});
});
