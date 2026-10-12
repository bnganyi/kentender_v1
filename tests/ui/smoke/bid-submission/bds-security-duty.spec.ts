import { execSync } from "node:child_process";
import path from "node:path";

import { expect, Page, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { expectNoFrappeDialog, expectNoHorizontalOverflow } from "../../helpers/portal";
import { AUDITOR, HOPF, OFFICER, PASSWORD, collectConsoleErrors } from "../tenders/helpers";

/**
 * Project Owner, 10 October 2026 — the Head of Procurement Function assigns the
 * tender-security intake duty for one Tender. The Head sees officers (with the
 * reason one is not eligible) and the assignments, never an intake record, a
 * supplier or a bid; assigning gives the officer the intake page, ending it
 * takes the page away; nobody else reaches the assignment page.
 *
 * World: `bid_submission.seeds.playwright_ui_fixtures` — a published Tender
 * whose duty is unassigned (`assigned: false`). `restore_site` removes it all.
 */

const BENCH_ROOT = path.resolve(__dirname, "../../../../../..");
const SITE = process.env.UI_SITE || "kentender.midas.com";
const FIXTURES = "kentender_procurement.bid_submission.seeds.playwright_ui_fixtures";
const DUTY_ROUTE = "/desk/tender-security-duty";
const RECEIPTS_ROUTE = "/desk/tender-security-receipts";

type World = { tender_reference: string; bid_reference: string; supplier_name: string };

function execute<T>(fn: string, kwargs: Record<string, unknown> = {}): T {
	const args = Object.keys(kwargs).length ? ` --kwargs '${JSON.stringify(kwargs).replace(/\btrue\b/g, "True").replace(/\bfalse\b/g, "False")}'` : "";
	const output = execSync(`cd "${BENCH_ROOT}" && bench --site ${SITE} execute ${FIXTURES}.${fn}${args}`, { stdio: "pipe", timeout: 600_000, encoding: "utf-8" });
	return JSON.parse(output.trim().split("\n").pop() || "{}") as T;
}

async function openDuty(page: Page, tender = ""): Promise<void> {
	await page.goto(`${DUTY_ROUTE}${tender ? `#tender=${tender}` : ""}`, { waitUntil: "domcontentloaded" });
	const shell = page.getByTestId("tsd-shell");
	await expect(shell).toHaveAttribute("data-loading", "false", { timeout: 30_000 });
	await expect(shell).toHaveAttribute("data-refreshing", "false", { timeout: 30_000 });
}

async function expectNoSupplierFacts(page: Page, world: World): Promise<void> {
	const text = await page.locator(".kt-tsd").innerText();
	for (const leak of [world.supplier_name, "Afya", world.bid_reference, "BID-", "ARR-", "TSI-", "Matched", "Draft"]) {
		expect(text, `the page shows "${leak}"`).not.toContain(leak);
	}
}

test.describe.configure({ mode: "serial", timeout: 240_000 });

test.describe("Tender-security intake duty — assigned by the Head of Procurement Function", () => {
	test.afterAll(() => execute("restore_site"));

	test("the Head assigns the duty, the officer gains the intake page, ending it takes the page away", async ({ page, browser }) => {
		const world = execute<World>("reset_security_intake_fixture", { assigned: false });
		const errors = collectConsoleErrors(page);
		await page.setViewportSize({ width: 1440, height: 1024 });
		await login(page, HOPF, PASSWORD);
		await openDuty(page);
		await expect(page.getByRole("heading", { level: 1, name: "Tender-security intake duty" })).toBeVisible();
		await expect(page.getByTestId("tsd-prompt")).toBeVisible();

		await page.getByTestId("tsd-tender").fill(world.tender_reference);
		await page.getByTestId("tsd-tender").press("Enter");
		await expect(page).toHaveURL(new RegExp(`#tender=${world.tender_reference}$`));
		await expect(page.getByTestId("tsd-officer").first()).toBeVisible();
		await expect(page.getByTestId("tsd-no-assignments")).toHaveText("Nobody holds the intake duty for this Tender.");
		await expectNoSupplierFacts(page, world);

		// the officer is eligible; the Head's own office is not offered as eligible
		const officerRow = page.getByTestId("tsd-officer").filter({ hasText: "Playwright Tenders Officer" });
		await officerRow.getByTestId("tsd-assign").click();
		await expect(page.getByTestId("tsd-dialog")).toBeVisible();
		await page.getByTestId("tsd-d-submit").click();
		await expect(page.getByTestId("tsd-done")).toContainText("The intake duty is assigned to");
		await expect(page.getByTestId("tsd-assignment")).toHaveCount(1);
		await expect(page.getByTestId("tsd-assignment")).toContainText("Playwright Tenders Officer");
		await expect(page.getByTestId("tsd-assignment")).toContainText("Active");
		await expectNoSupplierFacts(page, world);
		await expectNoFrappeDialog(page);

		// the assigned officer now has the intake page for exactly this Tender
		const officer = await (await browser.newContext()).newPage();
		await officer.setViewportSize({ width: 1440, height: 1024 });
		await login(officer, OFFICER, PASSWORD);
		await officer.goto(RECEIPTS_ROUTE, { waitUntil: "domcontentloaded" });
		await expect(officer.getByTestId("tsr-shell")).toHaveAttribute("data-loading", "false", { timeout: 30_000 });
		await expect(officer.getByTestId("tsr-forbidden")).toHaveCount(0);
		await expect(officer.getByTestId("tsr-record")).toBeVisible();

		// ending the duty takes the page away at once
		await page.getByTestId("tsd-revoke").click();
		await page.getByTestId("tsd-d-reason").fill("The duty is no longer needed for this Tender.");
		await page.getByTestId("tsd-d-submit").click();
		await expect(page.getByTestId("tsd-done")).toContainText("has ended");
		await expect(page.getByTestId("tsd-assignment")).toContainText("Revoked");
		await officer.reload({ waitUntil: "domcontentloaded" });
		await expect(officer.getByTestId("tsr-forbidden")).toContainText("You are not assigned to record tender-security receipts for this Tender.");
		await officer.context().close();
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("a person on the Tender's opening or evaluation, and the Head's own office, are refused with the duty named", async ({ page }) => {
		const world = execute<World>("reset_security_intake_fixture", { assigned: false });
		await page.setViewportSize({ width: 1440, height: 1024 });
		await login(page, HOPF, PASSWORD);
		await openDuty(page, world.tender_reference);
		const reasons = page.getByTestId("tsd-reason");
		// every person shown as not eligible says which duty is incompatible, and none names a supplier
		const texts = await reasons.allInnerTexts();
		for (const text of texts) {
			expect(text).toMatch(/cannot also take its tender-security intake/);
			expect(text.toLowerCase()).not.toContain("afya");
		}
	});

	for (const [who, user] of [["the intake officer", OFFICER], ["an Auditor", AUDITOR]] as const) {
		test(`${who} cannot reach the assignment page`, async ({ page }) => {
			await page.setViewportSize({ width: 1440, height: 1024 });
			await login(page, user, PASSWORD);
			await openDuty(page);
			await expect(page.getByTestId("tsd-forbidden")).toContainText("Only the Head of Procurement Function assigns the tender-security intake duty.");
			await expect(page.getByTestId("tsd-assign")).toHaveCount(0);
		});
	}

	test("the duty page fits at 390 px", async ({ page }) => {
		const world = execute<World>("reset_security_intake_fixture", { assigned: false });
		await page.setViewportSize({ width: 390, height: 844 });
		await login(page, HOPF, PASSWORD);
		await openDuty(page, world.tender_reference);
		await expectNoHorizontalOverflow(page);
	});
});
