import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import {
	HOD,
	OU_NAME,
	PASSWORD,
	PLANNER,
	collectConsoleErrors,
	expectReady,
	gotoDpp,
	gotoPlanning,
	resetFixture,
	restoreSite,
} from "./helpers";

/**
 * PLN-CHG-001 v1.12 Phase 3 (Slice A) — PLN-UI-06: the DPP validation task,
 * classification from the four-type catalogue, acceptance (auto-creating the
 * Draft Annual Plan) and the structured-issue return dialog, in a real
 * browser. The fixture drives the real §8.2 commands to a submitted state.
 */

type ReviewState = { task: string; dpp_reference: string; need_entry_id: string; direct_entry_id: string };

test.describe.configure({ mode: "serial" });

test.describe("PLN-UI-06 DPP validation", () => {
	let state: ReviewState;

	test.beforeEach(() => {
		state = resetFixture<ReviewState>("reset_review_fixture");
		expect(state.task).toBeTruthy();
	});
	test.afterAll(() => restoreSite());

	test("planner classifies every proceeding entry, accepts, and the workspace offers Ready to consolidate", async ({ page }) => {
		const errors = collectConsoleErrors(page);
		await login(page, PLANNER, PASSWORD);
		// the §10 deep link, exactly as My Work and notifications route it
		await gotoPlanning(page, `/dpp-review/${state.task}`);
		await expectReady(page, "dpp-review");

		// PLN-DES-06 exact composition — six facts, no Procuring Entity
		await expect(page.locator(".kt-page-kicker")).toHaveText("DEPARTMENTAL PLAN REVIEW");
		await expect(page.locator(".kt-page-title")).toHaveText(`Validate ${OU_NAME} departmental plan`);
		await expect(page.locator('[data-testid="dppv-badge"]')).toHaveText("Awaiting validation");
		const context = page.locator('[data-testid="dppv-context"]');
		await expect(context.locator("label")).toHaveText([
			"Department", "Financial Year", "Submitted by", "Submitted", "Requirements", "Total indicative value",
		]);
		await expect(context).toContainText("Playwright Planning HoD");
		await expect(context).toContainText("KES 100,000,000");
		await expect(page.locator('[data-testid="dppv-certification"]')).toContainText("Certified by Playwright Planning HoD");

		// View discloses the submitted narrative read-only
		await page.locator(`[data-testid="dppv-view-${state.need_entry_id}"]`).click();
		await expect(page.locator(`[data-testid="dppv-detail-${state.need_entry_id}"]`)).toContainText(
			"Procure and implement national digital health infrastructure"
		);

		// acceptance is blocked until every proceeding entry is classified (§12.6)
		const accept = page.locator('[data-testid="dppv-accept"]');
		await expect(accept).toBeDisabled();
		const needType = page.locator(`[data-testid="dppv-type-${state.need_entry_id}"]`);
		await expect(needType.locator("option:not([disabled])")).toHaveText([
			"Consulting services", "Goods", "Non-consulting services", "Works",
		]);
		await needType.selectOption("Non-consulting services");
		await expect(accept).toBeDisabled();
		await page.locator(`[data-testid="dppv-type-${state.direct_entry_id}"]`).selectOption("Consulting services");
		await expect(accept).toBeEnabled();
		await accept.click();

		// acceptance lands on the workspace, which now offers consolidation
		await expectReady(page, "workspace");
		const card = page.locator('[data-testid="pln-actionable"]');
		await expect(card.locator(".kt-card-title")).toHaveText("Ready to consolidate", { timeout: 30_000 });
		await expect(card.locator(".pln-ready-headline")).toHaveText("2 accepted departmental entries ready to consolidate");
		await expect(card.locator(".pln-ready-sub")).toContainText("KES 100,000,000");
		await expect(page.locator('[data-testid="pln-plan-summary"]')).toHaveText("· Annual Plan · Draft Version 1");
		await expect(page.locator('[data-testid="pln-departmental-plans"] tbody tr .kt-status')).toHaveText("Accepted");
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("return requires a complete structured issue and lands the correction on the department", async ({ page }) => {
		await login(page, PLANNER, PASSWORD);
		await gotoPlanning(page, `/dpp-review/${state.task}`);
		await expectReady(page, "dpp-review");

		await page.locator('[data-testid="dppv-return"]').click();
		const dialog = page.locator('[data-testid="dppv-return-dialog"]');
		await expect(dialog).toBeVisible();
		const confirm = page.locator('[data-testid="dppv-return-confirm"]');
		await expect(confirm).toBeDisabled(); // incomplete issue
		await page.locator('[data-testid="dppv-issue-problem-0"]').fill("Amount unsupported");
		await expect(confirm).toBeDisabled(); // correction still missing
		await page
			.locator('[data-testid="dppv-issue-correction-0"]')
			.fill("Align the indicative amount with the budget line.");
		await expect(confirm).toBeEnabled();
		await confirm.click();
		await expectReady(page, "workspace");

		// the department sees the returned plan with the issue on its entry
		await login(page, HOD, PASSWORD);
		await gotoDpp(page, state.dpp_reference);
		await expectReady(page, "dpp");
		// the correction copies the complete entries, so it is ready to resubmit
		// once the issue is addressed (§12.2) — issues sit next to their entry
		await expect(page.locator('[data-testid="dpp-badge"]')).toHaveText("Ready to submit");
		await expect(page.locator('[data-testid="dpp-certification"]')).toBeVisible();
		await expect(page.locator('[data-testid="dpp-issue"]')).toContainText("Amount unsupported");
		await expect(page.locator('[data-testid="dpp-issue"]')).toContainText(
			"Align the indicative amount with the budget line."
		);
	});

	test("a departmental actor's direct link to the task masks as not found", async ({ page }) => {
		await login(page, HOD, PASSWORD);
		await gotoPlanning(page, `/dpp-review/${state.task}`);
		await expectReady(page, "dpp-review");
		await expect(page.locator('[data-testid="pln-error"]')).toBeVisible();
		await expect(page.locator('[data-testid="dppv-accept"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="dppv-entries"]')).toHaveCount(0);
	});
});
