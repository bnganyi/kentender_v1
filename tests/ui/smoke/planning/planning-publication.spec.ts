import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import {
	ACCOUNTING_OFFICER,
	PASSWORD,
	PLANNER,
	collectConsoleErrors,
	contextValue,
	scopeLine,
	expectReady,
	gotoPlanning,
	resetFixture,
	restoreSite,
	tickCheckbox,
} from "./helpers";

/**
 * PLN-CHG-001 v1.31 §10.12–§10.13 — what happens to an approved plan: the
 * Planner's publication confirmation and what follows it, the plan update that
 * succeeds it, and the procurement progress recorded against the plan in force.
 * MVP 1 publication is manual: the Planner records the Treasury submission and
 * the website publication; nothing here transmits, retries or reconciles.
 *
 * Two whole tests from the v1.12 version of this file are gone rather than
 * retargeted, because what they proved no longer exists: the forecast cascade
 * dialog and the daily approaching-milestone job were both removed with the
 * forecast facility (PLN23-CHG-001). Keeping a retargeted shell of them would
 * assert that a deleted feature still behaves.
 */

type ActiveState = { plan_reference: string; plan_item_id: string; publication: string };

// Sequential, but not serial: these run on one worker because the fixtures
// are one shared world, and each test rebuilds its own. Aborting the rest of
// the file because one test failed hides every other result behind it.
test.describe.configure({ timeout: 180_000 });

async function gotoPlan(page: import("@playwright/test").Page, reference: string): Promise<void> {
	await page.setViewportSize({ width: 1440, height: 1024 });
	await page.goto(`/app/annual-procurement-plan/${reference}`, { waitUntil: "domcontentloaded" });
	await expectReady(page, "plan");
}

test.describe("Publication, recovery and the plan in force", () => {
	test.afterAll(() => restoreSite());

	test("an active plan states its approval and publication, and offers the progress against it", async ({ page }) => {
		const state = resetFixture<ActiveState>("reset_active_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, PLANNER, PASSWORD);
		await gotoPlan(page, state.plan_reference);

		// §10.6 — once a version is in force, its approval and publication are
		// facts about it rather than steps still to take.
		const governance = page.locator('[data-testid="ppl-governance"]');
		await expect(governance).toContainText("Confirmed");
		await expect(governance).toContainText("Adopted by the Accounting Officer");

		await page.locator('[data-testid="ppl-view-progress"]').click();
		await expectReady(page, "progress");
		// §10.13 — planned, covered and started; quantity and value together.
		const purchase = page.locator('[data-testid="prg-purchase"]').first();
		await expect(purchase).toContainText("Digital health infrastructure package");
		await expect(purchase).toContainText("KES 80,000,000");
		await expect(purchase).toContainText("Not started");
		// PLN22-AC-009 / PLN23-CHG-001 — the absence is the acceptance criterion.
		await expect(page.locator(".kt-pln .kt-shell")).not.toContainText("Completion");
		await expect(page.locator(".kt-pln .kt-shell")).not.toContainText("Forecast");
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("preparing an update opens one draft successor, and the plan in force stays in force", async ({ page }) => {
		const state = resetFixture<ActiveState>("reset_active_fixture");
		await login(page, PLANNER, PASSWORD);
		await gotoPlanning(page);
		await expectReady(page, "workspace");

		// §5.2.3 — the guarded successor start, from the workspace.
		await page.locator('[data-testid="pln-prepare-update"]').click();
		await expectReady(page, "plan");
		await expect(scopeLine(page, "ppl-context")).toContainText("Version 2");
		await expect(scopeLine(page, "ppl-context")).toContainText("Draft update");
		await expect(page.locator('[data-testid="ppl-purchase-row"]')).toHaveCount(1);

		await gotoPlanning(page);
		await expectReady(page, "workspace");
		// The plan in force and its candidate are two rows, and the start
		// control is gone rather than disabled while one exists (§10.3).
		await expect(page.locator('[data-testid="pln-plan-row-current"]')).toBeVisible();
		await expect(page.locator('[data-testid="pln-plan-row-candidate"]')).toBeVisible();
		await expect(page.locator('[data-testid="pln-prepare-update"]')).toHaveCount(0);
	});

	test("the Planner confirms publication and the plan becomes current; nobody else is offered it", async ({ page }) => {
		const state = resetFixture<ActiveState>("reset_approved_fixture");
		const errors = collectConsoleErrors(page);

		// The Accounting Officer reads the same page, is told whose turn it is, and is offered nothing.
		await login(page, ACCOUNTING_OFFICER, PASSWORD);
		await gotoPlanning(page, `/publication/${state.publication}`);
		await expectReady(page, "publication");
		await expect(page.locator(".kt-page-head .kt-next-step")).toContainText("to confirm publication");
		await expect(page.locator('[data-testid="pub-form"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="pub-confirm"]')).toHaveCount(0);
		for (const gone of ["pub-record-treasury", "pub-publish", "pub-retry", "pub-reconcile"]) {
			await expect(page.locator(`[data-testid="${gone}"]`)).toHaveCount(0);
		}

		await login(page, PLANNER, PASSWORD);
		await gotoPlanning(page, `/publication/${state.publication}`);
		await expectReady(page, "publication");
		await expect(page.locator('[data-testid="pub-title"]')).toHaveText("Confirm publication of the annual plan");
		await expect(page.locator(".kt-page-head .kt-next-step")).toHaveText(/^Your turn\s+Confirm plan publication$/);
		await expect(page.locator(".kt-journey.is-reduced")).toContainText(/^Stage 6 of 7: Publication/);
		const rows = page.locator('[data-testid="pub-status-row"]');
		await expect(rows).toHaveCount(4);
		await expect(rows.nth(1)).toContainText("Not yet confirmed");

		// The form: confirming needs the statement and complete evidence, and says so.
		const confirm = page.locator('[data-testid="pub-confirm"]');
		await expect(confirm).toBeDisabled();
		await expect(page.locator('[data-testid="pub-confirm-hint"]')).toHaveText("Complete every field and tick the confirmation to confirm.");
		const today = new Date().toISOString().slice(0, 10);
		await page.locator('[data-testid="pub-treasury-date"]').fill(today);
		await page.locator('[data-testid="pub-treasury-reference"]').fill("MOH/APP/2098/001");
		await page.locator('[data-testid="pub-website-date"]').fill(today);
		// Found live 9 Oct 2026: an address without http:// or https:// enabled Confirm and was refused with a generic
		// sentence that named no field. It is now named at its own field before anything is pressed.
		await page.locator('[data-testid="pub-public-url"]').fill("www.xyz.com");
		await tickCheckbox(page.locator('[data-testid="pub-statement"]'));
		await expect(page.locator('[data-testid="pub-error-public_plan_url"]')).toHaveText("Enter the address of the published plan, starting with http:// or https://.");
		await expect(page.locator('[data-testid="pub-field-public_plan_url"]')).toHaveClass(/pln-field-flagged/);
		await expect(confirm).toBeDisabled();
		await expect(page.locator('[data-testid="pub-confirm-hint"]')).toHaveText("Fix the highlighted fields to confirm.");
		await page.locator('[data-testid="pub-public-url"]').fill("https://www.moh.example.test/procurement/annual-procurement-plan");
		await expect(page.locator('[data-testid="pub-error-public_plan_url"]')).toHaveCount(0);
		await expect(confirm).toBeEnabled();

		// A Draft saves incomplete evidence without confirming anything.
		await page.locator('[data-testid="pub-save-draft"]').click();
		await expect(rows.nth(1)).toContainText("Not yet confirmed");
		await expect(rows.nth(3)).toContainText("This plan is not yet active");

		// saving the Draft refilled the form from it, and the statement starts unchecked every time
		await expect(page.locator('[data-testid="pub-statement"]')).not.toBeChecked();
		await tickCheckbox(page.locator('[data-testid="pub-statement"]'));
		await confirm.click();
		await expect(rows.nth(1)).toContainText("Confirmed", { timeout: 30_000 });
		await expect(rows.nth(2)).toContainText("Confirmed");
		await expect(rows.nth(3)).toContainText("Current plan");
		await expect(page.locator('[data-testid="pub-confirmation"]')).toContainText("MOH/APP/2098/001");
		await expect(page.locator('[data-testid="pub-form"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="pub-correct"]')).toBeVisible();
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("Save draft keeps everything typed, even an address that is not yet valid and an uploaded file, and it is still there after a reload", async ({ page }) => {
		// Found live 9 Oct 2026: Save draft with "www.xyz.com" saved nothing at all, and nothing said so.
		const state = resetFixture<ActiveState>("reset_approved_fixture");
		await login(page, PLANNER, PASSWORD);
		await gotoPlanning(page, `/publication/${state.publication}`);
		await expectReady(page, "publication");
		const today = new Date().toISOString().slice(0, 10);
		const jpg = Buffer.from(
			"/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////wgALCAABAAEBAREA/8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABPxA=",
			"base64",
		);
		await page.locator('[data-testid="pub-treasury-date"]').fill(today);
		await page.locator('[data-testid="pub-treasury-reference"]').fill("ST-003");
		await page.locator('[data-testid="pub-treasury-file"]').setInputFiles({ name: "evidence.jpg", mimeType: "image/jpeg", buffer: jpg });
		await page.locator('[data-testid="pub-website-date"]').fill(today);
		await page.locator('[data-testid="pub-public-url"]').fill("www.xyz.com");
		await page.locator('[data-testid="pub-save-draft"]').click();
		await expect(page.locator('[data-testid="pub-draft-saved"]')).toContainText("Nothing has been confirmed yet.", { timeout: 30_000 });
		await expect(page.locator('[data-testid="pub-attached-file"]')).toBeVisible();
		// the address is still flagged: saving a draft does not confirm it
		await expect(page.locator('[data-testid="pub-error-public_plan_url"]')).toBeVisible();
		await expect(page.locator('[data-testid="pub-confirm"]')).toBeDisabled();

		await page.reload();
		await expectReady(page, "publication");
		await expect(page.locator('[data-testid="pub-treasury-reference"]')).toHaveValue("ST-003");
		await expect(page.locator('[data-testid="pub-treasury-date"]')).toHaveValue(today);
		await expect(page.locator('[data-testid="pub-website-date"]')).toHaveValue(today);
		await expect(page.locator('[data-testid="pub-public-url"]')).toHaveValue("www.xyz.com");
		await expect(page.locator('[data-testid="pub-attached-file"]')).toBeVisible();
		await expect(page.locator('[data-testid="pub-draft-saved"]')).toBeVisible();
		// and the rest of the journey still works from the draft: fix the address, tick, confirm
		await page.locator('[data-testid="pub-public-url"]').fill("https://www.xyz.com/plan");
		await tickCheckbox(page.locator('[data-testid="pub-statement"]'));
		await page.locator('[data-testid="pub-confirm"]').click();
		await expect(page.locator('[data-testid="pub-status-row"]').nth(3)).toContainText("Current plan", { timeout: 30_000 });
		await expect(page.locator('[data-testid="pub-view-evidence"]')).toBeVisible();
	});

	test("the recorded publication facts line up, and a long public address wraps inside the card", async ({ page }) => {
		// Found live 9 Oct 2026: a long address sat in a fourth, bottom-aligned column, wrapped to three lines, dragged its
		// neighbours' labels out of line and ran past the card edge.
		const state = resetFixture<ActiveState>("reset_approved_fixture");
		await login(page, PLANNER, PASSWORD);
		await page.setViewportSize({ width: 1440, height: 1024 });
		await gotoPlanning(page, `/publication/${state.publication}`);
		await expectReady(page, "publication");
		const today = new Date().toISOString().slice(0, 10);
		await page.locator('[data-testid="pub-treasury-date"]').fill(today);
		await page.locator('[data-testid="pub-treasury-reference"]').fill("ST-001");
		await page.locator('[data-testid="pub-website-date"]').fill(today);
		await page.locator('[data-testid="pub-public-url"]').fill("https://chatgpt.com/c/6ac8ac05-2d08-83ed-86ad-fc5613675d38/with/a/much/longer/path/that/keeps/going/and/going");
		await tickCheckbox(page.locator('[data-testid="pub-statement"]'));
		await page.locator('[data-testid="pub-confirm"]').click();
		const facts = page.locator('[data-testid="pub-confirmation"] .pln-facts');
		await expect(facts).toBeVisible({ timeout: 30_000 });

		const box = async (fact: string) => {
			const b = await facts.locator(`[data-fact="${fact}"] .kt-label`).boundingBox();
			if (!b) throw new Error(`no box for ${fact}`);
			return b;
		};
		const [date, reference, website, url, by, at] = await Promise.all(
			["treasury_date", "reference", "website_date", "url", "confirmed_by", "confirmed_at"].map(box),
		);
		// the three short facts share one top edge, and none shares a row with the address
		expect(Math.abs(date.y - reference.y)).toBeLessThanOrEqual(1);
		expect(Math.abs(date.y - website.y)).toBeLessThanOrEqual(1);
		expect(url.y).toBeGreaterThan(date.y + 20);
		// the address and who confirmed it start flush with the first column
		expect(Math.abs(url.x - date.x)).toBeLessThanOrEqual(1);
		expect(Math.abs(by.x - date.x)).toBeLessThanOrEqual(1);
		expect(Math.abs(by.y - at.y)).toBeLessThanOrEqual(1);
		// and the address wraps inside the section instead of running past it
		const section = await page.locator('[data-testid="pub-confirmation"]').boundingBox();
		const link = await facts.locator('[data-fact="url"] a').boundingBox();
		if (!section || !link) throw new Error("no boxes");
		expect(link.x + link.width).toBeLessThanOrEqual(section.x + section.width + 1);

		// the correction form lays the previous details out the same way
		await page.locator('[data-testid="pub-correct"]').click();
		const prior = page.locator('[data-testid="pub-correct-prior"]');
		const priorDate = await prior.locator(".kt-label").first().boundingBox();
		const priorUrl = await prior.locator(".pln-fact-wide .kt-label").boundingBox();
		if (!priorDate || !priorUrl) throw new Error("no prior boxes");
		expect(Math.abs(priorUrl.x - priorDate.x)).toBeLessThanOrEqual(1);
		expect(priorUrl.y).toBeGreaterThan(priorDate.y + 20);
	});

	test("the plan page's Your turn line is itself the link to Confirm plan publication", async ({ page }) => {
		const state = resetFixture<ActiveState>("reset_approved_fixture");
		await login(page, PLANNER, PASSWORD);
		await gotoPlan(page, state.plan_reference);
		const link = page.locator(".kt-page-head .kt-next-step .kt-next-step-link");
		await expect(link).toHaveText("Confirm plan publication");
		await link.click();
		await expectReady(page, "publication");
		await expect(page.locator('[data-testid="pub-form"]')).toBeVisible();
	});

	test("a plan whose activation checks fail is shown as published but held, with its evidence kept and correctable", async ({ page }) => {
		const state = resetFixture<ActiveState>("reset_activation_held_fixture");
		await login(page, PLANNER, PASSWORD);
		await gotoPlanning(page, `/publication/${state.publication}`);
		await expectReady(page, "publication");
		const rows = page.locator('[data-testid="pub-status-row"]');
		await expect(rows.nth(1)).toContainText("Confirmed");
		await expect(rows.nth(3)).toContainText("Published, but not available for new procurement");
		await expect(page.locator('[data-testid="pub-confirm"]')).toHaveCount(0);

		await page.locator('[data-testid="pub-correct"]').click();
		const form = page.locator('[data-testid="pub-correct-form"]');
		await expect(form).toBeVisible();
		await expect(form).toContainText("Correcting these details does not change the approved plan, deactivate an active plan or repeat an approval.");
		await expect(page.locator('[data-testid="pub-correct-submit"]')).toBeDisabled();
		await page.locator('[data-testid="pub-correct-reference"]').fill("MOH/APP/2098/002");
		await page.locator('[data-testid="pub-correct-reason"]').fill("The reference was typed from the wrong letter.");
		await page.locator('[data-testid="pub-correct-submit"]').click();
		await expect(page.locator('[data-testid="pub-confirmation"]')).toContainText("MOH/APP/2098/002", { timeout: 30_000 });
		// still held: a correction runs no second activation
		await expect(rows.nth(3)).toContainText("Published, but not available for new procurement");
	});

	test("the Accounting Officer asks for a withdrawal of an unconfirmed plan; the approving authority decides it", async ({ page }) => {
		const state = resetFixture<ActiveState>("reset_approved_fixture");
		await login(page, ACCOUNTING_OFFICER, PASSWORD);
		await gotoPlanning(page, `/publication/${state.publication}`);
		await expectReady(page, "publication");

		await page.locator('[data-testid="pub-request-withdrawal"]').click();
		const dialog = page.locator('[data-testid="pub-withdrawal-dialog"]');
		await expect(dialog).toBeVisible();
		await expect(page.locator('[data-testid="pub-withdrawal-confirmation"]')).toHaveText("Confirmed not published");
		// A reason someone can act on, or no request.
		await expect(page.locator('[data-testid="pub-withdrawal-confirm"]')).toBeDisabled();
		await page.locator('[data-testid="pub-withdrawal-reason"]').fill(
			"A material defect was found in the approved content before it was submitted to Treasury."
		);
		await page.locator('[data-testid="pub-withdrawal-confirm"]').click();

		// The AO has asked; there is nothing more for them to do but wait.
		await expect(page.locator('[data-testid="pub-withdrawal-state"]')).toBeVisible({ timeout: 30_000 });
		await expect(page.locator('[data-testid="pub-request-withdrawal"]')).toHaveCount(0);
	});
});
