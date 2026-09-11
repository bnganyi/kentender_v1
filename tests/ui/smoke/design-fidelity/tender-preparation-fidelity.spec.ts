import { expect, test, Page } from "@playwright/test";

import { login } from "../../helpers/auth";
import { collectPageErrors, expectLandmarkSubsequence, landmarks, openArtboard } from "../../helpers/designFidelity";
import { HOPF, OFFICER, PASSWORD, expectReady, gotoTenderPreparation, resetFixture, restoreSite } from "../tender-preparation/helpers";

/**
 * Tender Preparation design-fidelity gate (TPR-CHG-001 v0.6, AGENTS.md
 * §6.6). Every artboard's ordered structural landmarks (card titles, dialog
 * titles, field labels, row labels, table headers, buttons) must appear in
 * order on the live screen. Data values are never compared.
 *
 * All thirteen TPR-CHG-001 artboards live in one file (`Tender Preparation
 * Screens.dc.html`), one `<section id="s-…">` per screen (plan D16); with
 * `support.js` blocked every section paints at once, so each artboard is
 * scoped to its own `section#id`.
 */

const ARTBOARD_FILE = "docs/mvp-1-r1/07_std_configuration/design/Tender Preparation Screens.dc.html";
const LIVE_SCOPE = '.kt-tpr [data-testid="tpr-shell"]';

function sectionScope(id: string): string {
	return `section#${id}`;
}

/**
 * The Task 2 technical-requirements card title embeds the fixture's own
 * requirement-set identifier ("Technical requirements — TRQ-MOH-033-001");
 * the live title embeds the inherited row-ID range instead. Strip everything
 * after the dash so only the structural wording is compared.
 */
function stripDataSuffix(list: string[]): string[] {
	return list.map((text) => text.replace(/^Technical requirements — .*$/, "Technical requirements"));
}

async function artboardLandmarks(browser: any, id: string): Promise<{ wanted: string[]; art: Page }> {
	const art = await browser.newPage();
	await openArtboard(art, ARTBOARD_FILE, sectionScope(id));
	return { wanted: stripDataSuffix(await landmarks(art, sectionScope(id))), art };
}

async function liveLandmarks(page: Page): Promise<string[]> {
	return stripDataSuffix(await landmarks(page, LIVE_SCOPE));
}

// Every test rebuilds its own opening state, so a failure never hides the
// next artboard's result (single worker keeps the site serialised).
test.describe.configure({ mode: "default", timeout: 240_000 });

test.describe("Tender Preparation — design fidelity", () => {
	test.afterAll(() => restoreSite());

	test("TPR-DES-01 — Workspace (s-workspace)", async ({ page, browser }) => {
		// one eligible handoff: the Ready to prepare table (and its Prepare
		// Tender action) paints only when a row exists; My Tenders always paints
		resetFixture("reset_workspace_fixture");
		const { wanted, art } = await artboardLandmarks(browser, "s-workspace");
		const errors = collectPageErrors(page);
		await login(page, OFFICER, PASSWORD);
		await gotoTenderPreparation(page);
		await expectReady(page, "workspace");
		expectLandmarkSubsequence(wanted, await liveLandmarks(page), "s-workspace");
		expect(errors).toEqual([]);
		await art.close();
	});

	test("TPR-DES-02 — Start Tender dialog (s-start)", async ({ page, browser }) => {
		const fixture = resetFixture<{ handoff: string }>("reset_workspace_fixture");
		const { wanted, art } = await artboardLandmarks(browser, "s-start");
		await login(page, OFFICER, PASSWORD);
		await gotoTenderPreparation(page, `/new/${fixture.handoff}`);
		await expectReady(page, "start");
		await expect(page.locator('[data-testid="tpr-start-confirm"]')).toBeVisible();
		expectLandmarkSubsequence(wanted, await liveLandmarks(page), "s-start");
		await art.close();
	});

	for (const [id, task, before] of [
		["s-task1", 1, ""],
		["s-task2", 2, ""],
		["s-task2-dialog", 2, "tpr-upstream-trigger"],
		["s-task3", 3, ""],
		["s-task4", 4, ""],
		["s-task5", 5, ""],
		["s-review", 6, ""],
	] as const) {
		test(`TPR-DES-03/04 — editor ${id}`, async ({ page, browser }) => {
			const fixture = resetFixture<{ tender: string }>("reset_complete_draft_fixture");
			const { wanted, art } = await artboardLandmarks(browser, id);
			await login(page, OFFICER, PASSWORD);
			await gotoTenderPreparation(page, `/${fixture.tender}`);
			await expectReady(page, "editor");
			await page.locator(task === 6 ? '[data-testid="tpr-task-review"]' : `[data-testid="tpr-task-${task}"]`).click();
			if (task === 6) await expect(page.locator('[data-testid="tpr-readiness-summary"]')).toBeVisible();
			else await expect(page.locator(`[data-testid="tpr-task-${task}"]`)).toHaveClass(/is-active/);
			if (before) {
				await page.locator(`[data-testid="${before}"]`).click();
				await expect(page.locator(".kt-dialog-title")).toBeVisible();
			}
			expectLandmarkSubsequence(wanted, await liveLandmarks(page), id);
			await art.close();
		});
	}

	for (const [id, before] of [
		["s-approval", ""],
		["s-approval-dialog", "tpr-return"],
	] as const) {
		test(`TPR-DES-05 — approval ${id}`, async ({ page, browser }) => {
			const fixture = resetFixture<{ task: string }>("reset_submitted_fixture");
			const { wanted, art } = await artboardLandmarks(browser, id);
			await login(page, HOPF, PASSWORD);
			await gotoTenderPreparation(page, `/task/${fixture.task}`);
			await expectReady(page, "task");
			if (before) {
				await page.locator(`[data-testid="${before}"]`).click();
				await expect(page.locator(".kt-dialog-title")).toBeVisible();
			}
			expectLandmarkSubsequence(wanted, await liveLandmarks(page), id);
			await art.close();
		});
	}

	for (const [id, before] of [
		["s-approved", ""],
		["s-approved-dialog", "tpr-reopen"],
	] as const) {
		test(`TPR-DES-06 — approved ${id}`, async ({ page, browser }) => {
			const fixture = resetFixture<{ tender: string }>("reset_approved_fixture");
			const { wanted, art } = await artboardLandmarks(browser, id);
			await login(page, HOPF, PASSWORD);
			await gotoTenderPreparation(page, `/${fixture.tender}/approved`);
			await expectReady(page, "approved");
			if (before) {
				await page.locator(`[data-testid="${before}"]`).click();
				await expect(page.locator(".kt-dialog-title")).toBeVisible();
			}
			expectLandmarkSubsequence(wanted, await liveLandmarks(page), id);
			await art.close();
		});
	}
});
