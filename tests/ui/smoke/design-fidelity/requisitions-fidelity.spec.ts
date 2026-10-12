import { expect, test, Page } from "@playwright/test";

import { login } from "../../helpers/auth";
import { collectPageErrors, expectLandmarkSubsequence, expectStructure, landmarks, onceEach, openArtboard, outerHtml } from "../../helpers/designFidelity";
import { DEPARTURES } from "../../fidelity/departures/procurement-requisitions.js";
import { AUTHOR, HOD, HOPF, PASSWORD, expectReady, gotoRequisitions, resetFixture, restoreSite } from "../requisitions/helpers";

/**
 * Procurement Requisitions design-fidelity gate (REQ-CHG-001 v1.15, board v2,
 * AGENTS.md §6.6): each base artboard frame against the live screen reached
 * as the frame's own actor on its own reset — the containers it is built from
 * (structure) and its ordered labels, titles and headers (text). Data values
 * differ legitimately between the board's MOH 2027 fixture and the
 * Playwright world (FY 2099), so references, money, quantities and dates are
 * normalised on both sides; nothing else is.
 */

const BOARD = "docs/mvp-1-r1/06_requisitions/design/Requisitions - Design Board v2.dc.html";
const LIVE_PAGE = '.kt-req [data-testid="req-shell"] > .kt-panel-lg';
// The dialog must be a child of the compared root on both sides.
const LIVE_DIALOG = ".kt-req .dialog-backdrop";

const DATA = [
	[/\b(REQ|PPI|SRC|DPER|RSV|PDR|UI-CORR|TND|PLN|RQV|PRQ)-[A-Z0-9-]+/g, "<ref>"],
	[/KES [\d,]+\.\d{2}/g, "<money>"],
	[/\b[\d,]+ Each\b/g, "<qty>"],
	[/\b\d{1,2} [A-Z][a-z]{2} \d{4}(, \d{2}:\d{2} EAT)?/g, "<date>"],
	[/Playwright — /g, ""],
	[/\bHRMD\b|HR Management and Development/g, "Human Resources Management and Development"],
] as const;

function normalise(list: string[]): string[] {
	return list.map((text) => DATA.reduce((t, [pattern, to]) => t.replace(pattern as RegExp, to as string), text));
}

// The board's annotation captions (.sub/.cap) are not part of any screen.
async function openFrame(art: Page, selector: string): Promise<{ html: string; wanted: string[] }> {
	await openArtboard(art, BOARD, selector);
	await art.evaluate((sel) => {
		const frame = document.querySelector(sel);
		frame?.querySelectorAll(".sub, .cap").forEach((el) => el.remove());
	}, selector);
	return { html: await outerHtml(art, selector), wanted: normalise(await landmarks(art, selector)) };
}

async function compare(page: Page, browser: any, frame: string, live: string, label: string, departureKey: string) {
	const art = await browser.newPage();
	const { html, wanted } = await openFrame(art, frame);
	await art.close();
	const got = normalise(await landmarks(page, live));
	expectLandmarkSubsequence(onceEach(wanted), got, label);
	await expectStructure(page, live, frame.includes(".dialog") ? `<div>${html}</div>` : html, label, (DEPARTURES as any)[departureKey] || []);
}

type World = { plan_item_id: string; requisition: string; department_task?: string; procurement_task?: string };

test.describe.configure({ mode: "serial", timeout: 180_000 });

test.describe("Procurement Requisitions — design fidelity (board v2)", () => {
	test.afterAll(() => restoreSite());

	test("REQ-DES-01 workspace and REQ-DES-02 start dialog", async ({ page, browser }) => {
		const world = resetFixture<World>("reset_workspace_ready");
		const errors = collectPageErrors(page);
		await login(page, AUTHOR, PASSWORD);
		await gotoRequisitions(page);
		await expectReady(page, "workspace");
		await compare(page, browser, "div#des01 > .kt-panel-lg", LIVE_PAGE, "REQ-DES-01", "WorkspaceScreen#REQ-DES-01");
		await gotoRequisitions(page, `/new/${world.plan_item_id}`);
		await expectReady(page, "start");
		await compare(page, browser, "div#des02 > div > div > .dialog", LIVE_DIALOG, "REQ-DES-02", "StartDialog#REQ-DES-02");
		expect(errors).toEqual([]);
	});

	test("REQ-DES-03 Request details", async ({ page, browser }) => {
		const world = resetFixture<World>("reset_draft");
		await login(page, AUTHOR, PASSWORD);
		await gotoRequisitions(page, `/${world.requisition}`);
		await expectReady(page, "record");
		await compare(page, browser, "div#des03 > .kt-panel-lg", LIVE_PAGE, "REQ-DES-03", "EditorScreen#REQ-DES-03");
	});

	test("REQ-DES-05 Requirements (review required)", async ({ page, browser }) => {
		const world = resetFixture<World>("reset_review_required");
		await login(page, AUTHOR, PASSWORD);
		await gotoRequisitions(page, `/${world.requisition}`);
		await expectReady(page, "record");
		await page.getByTestId("req-task-requirements").click();
		await compare(page, browser, "div#des05 > .kt-panel-lg", LIVE_PAGE, "REQ-DES-05", "EditorScreen#REQ-DES-05");
	});

	test("REQ-DES-07 HoD review", async ({ page, browser }) => {
		const world = resetFixture<World>("reset_department_task");
		await login(page, HOD, PASSWORD);
		await gotoRequisitions(page, `/department-task/${world.department_task}`);
		await expectReady(page, "department-task");
		await compare(page, browser, "div#des07 > div > .kt-panel-lg", LIVE_PAGE, "REQ-DES-07", "DepartmentTaskScreen#REQ-DES-07");
	});

	test("REQ-DES-08 Procurement authorisation", async ({ page, browser }) => {
		const world = resetFixture<World>("reset_procurement_task");
		await login(page, HOPF, PASSWORD);
		await gotoRequisitions(page, `/procurement-task/${world.procurement_task}`);
		await expectReady(page, "procurement-task");
		await compare(page, browser, "div#des08 > .kt-panel-lg", LIVE_PAGE, "REQ-DES-08", "ProcurementTaskScreen#REQ-DES-08");
	});
});
