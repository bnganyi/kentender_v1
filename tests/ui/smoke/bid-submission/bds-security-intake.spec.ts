import { execSync } from "node:child_process";
import path from "node:path";

import { expect, Page, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { expectNoFrappeDialog, expectNoHorizontalOverflow } from "../../helpers/portal";
import { AUDITOR, HOPF, OFFICER, PASSWORD, collectConsoleErrors } from "../tenders/helpers";

/**
 * BDS-CHG-001 v0.8 plan Phase 7 (BDS8-704) — the blind physical
 * tender-security intake, owner decisions OD-G/OD-H (replacing BDS-DES-15).
 * The Head of Procurement Function records an original by Tender reference
 * and the instrument's own details; the page never shows a bid, a supplier
 * or whether anything matched. The match is private: only the supplier's own
 * bid learns "recorded" (read here through the fixture, since the supplier
 * screen that shows it is a later slice).
 *
 * World: `bid_submission.seeds.playwright_ui_fixtures` on the Tenders
 * Playwright world (FY 2099-2100) — a published Tender whose one bid (Afya,
 * David Ouma) has its instrument details saved. `restore_site` removes it all.
 */

const BENCH_ROOT = path.resolve(__dirname, "../../../../../..");
const SITE = process.env.UI_SITE || "kentender.midas.com";
const FIXTURES = "kentender_procurement.bid_submission.seeds.playwright_ui_fixtures";
const ROUTE = "/desk/tender-security-receipts";

type World = { tender_reference: string; bid_reference: string; supplier_name: string; amount: string; currency: string; issuer: string; instrument_reference: string; instrument_type: string };

function execute<T>(fn: string, kwargs: Record<string, unknown> = {}): T {
	const args = Object.keys(kwargs).length ? ` --kwargs '${JSON.stringify(kwargs).replace(/\btrue\b/g, "True").replace(/\bfalse\b/g, "False")}'` : "";
	const output = execSync(`cd "${BENCH_ROOT}" && bench --site ${SITE} execute ${FIXTURES}.${fn}${args}`, { stdio: "pipe", timeout: 600_000, encoding: "utf-8" });
	return JSON.parse(output.trim().split("\n").pop() || "{}") as T;
}

async function openPage(page: Page, fragment = ""): Promise<void> {
	await page.goto(`${ROUTE}${fragment}`, { waitUntil: "domcontentloaded" });
	const shell = page.getByTestId("tsr-shell");
	await expect(shell).toHaveAttribute("data-loading", "false", { timeout: 30_000 });
	await expect(shell).toHaveAttribute("data-refreshing", "false", { timeout: 30_000 });
}

async function fillIntake(page: Page, world: World, overrides: Partial<Record<"reference" | "received" | "amount", string>> = {}, confirm = true): Promise<void> {
	const dialog = page.getByTestId("tsr-dialog");
	await dialog.getByTestId("tsr-d-tender").fill(world.tender_reference);
	await dialog.getByTestId("tsr-d-tender").blur();
	await expect(dialog.getByTestId("tsr-d-requirement")).toContainText(`Required: ${world.currency} 500,000.00`);
	await dialog.getByTestId("tsr-d-type").selectOption(world.instrument_type);
	await dialog.getByTestId("tsr-d-issuer").fill(world.issuer);
	await dialog.getByTestId("tsr-d-reference").fill(overrides.reference ?? world.instrument_reference);
	await dialog.getByTestId("tsr-d-amount").fill(overrides.amount ?? world.amount);
	await expect(dialog.getByTestId("tsr-d-currency")).toHaveValue(world.currency);
	await dialog.getByTestId("tsr-d-received").fill(overrides.received ?? "2026-09-01T09:00");
	await dialog.getByTestId("tsr-d-confirm").setChecked(confirm);
}

/** Nothing about any bid reaches the recorder. */
async function expectNoBidFacts(page: Page, world: World): Promise<void> {
	const text = await page.locator(".kt-tsr").innerText();
	for (const leak of [world.supplier_name, "Afya", world.bid_reference, "BID-", "ARR-", "Matched", "match", "candidate", "Draft"]) {
		expect(text, `the page shows "${leak}"`).not.toContain(leak);
	}
}

test.describe.configure({ mode: "serial", timeout: 240_000 });

test.describe("Tender-security receipts — the blind physical-original intake", () => {
	test.afterAll(() => execute("restore_site"));

	test("the Head of Procurement Function records a matching original; bad input is named; the supplier alone learns it", async ({ page }) => {
		const world = execute<World>("reset_security_intake_fixture");
		const errors = collectConsoleErrors(page);
		await page.setViewportSize({ width: 1440, height: 1024 });
		await login(page, HOPF, PASSWORD);
		await openPage(page);
		await expect(page.getByRole("heading", { level: 1, name: "Tender-security receipts" })).toBeVisible();
		await expect(page.getByTestId("tsr-empty")).toHaveText("You have not recorded any tender-security originals yet.");

		// Refused input keeps what was entered and names each field.
		await page.getByTestId("tsr-record").click();
		await fillIntake(page, world, { received: "2030-01-01T09:00" }, false);
		await page.getByTestId("tsr-d-submit").click();
		const dialog = page.getByTestId("tsr-dialog");
		await expect(dialog.locator(".kt-field-error")).toHaveText(["The time received cannot be in the future.", "Confirm that the original was received as recorded."]);
		await expect(dialog.getByTestId("tsr-d-issuer")).toHaveValue(world.issuer);
		await expectNoFrappeDialog(page);

		// Corrected: recorded, confirmed with an opaque intake reference.
		await dialog.getByTestId("tsr-d-received").fill("2026-09-01T09:00");
		await dialog.getByTestId("tsr-d-confirm").check();
		await dialog.getByTestId("tsr-d-submit").click();
		await expect(page.getByTestId("tsr-dialog")).toHaveCount(0);
		const toast = page.getByTestId("tsr-recorded");
		await expect(toast).toHaveText(/^Receipt recorded\. Intake reference TSI-[0-9A-F]{10}\.$/);
		const intake = ((await toast.innerText()).match(/TSI-[0-9A-F]{10}/) || [""])[0];
		const row = page.getByTestId("tsr-row");
		await expect(row).toHaveCount(1);
		await expect(row.locator("td")).toHaveText([intake, world.tender_reference, new RegExp(`${world.instrument_type} · ${world.issuer}`), `${world.currency} 500,000.00`, /1 Sep 2026, 09:00 EAT\s*Before deadline/, /EAT$/]);
		await expectNoBidFacts(page, world);

		// Only the matched supplier's own bid learns it, with the same reference.
		expect(execute<Record<string, string>>("physical_receipt_status", { tender_reference: world.tender_reference })).toEqual({
			physical_receipt_status: "Recorded before deadline", physical_receipt_reference: intake, physical_received_at: "1 Sep 2026, 09:00 EAT",
		});

		// The Tender-reference filter lives in the address: reload keeps it.
		await page.getByTestId("tsr-filter-tender").fill(world.tender_reference);
		await page.getByTestId("tsr-filter-tender").press("Enter");
		await expect(page).toHaveURL(new RegExp(`#tender=${world.tender_reference}$`));
		await page.reload({ waitUntil: "domcontentloaded" });
		await openPage(page, `#tender=${world.tender_reference}`);
		await expect(page.getByTestId("tsr-filter-tender")).toHaveValue(world.tender_reference);
		await expect(page.getByTestId("tsr-row")).toHaveCount(1);
		await page.getByTestId("tsr-filter-tender").fill("TND-NONE-0000-000");
		await page.getByTestId("tsr-filter-tender").press("Enter");
		await expect(page.getByTestId("tsr-empty")).toHaveText("No receipts match this Tender reference.");
		await page.getByTestId("tsr-clear-filters").click();
		await expect(page.getByTestId("tsr-row")).toHaveCount(1);
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("an original no bid matches gets the very same answer, and the supplier's bid still says Not recorded", async ({ page }) => {
		const world = execute<World>("reset_security_intake_fixture");
		const errors = collectConsoleErrors(page);
		await page.setViewportSize({ width: 1440, height: 1024 });
		await login(page, HOPF, PASSWORD);
		await openPage(page);
		await page.getByTestId("tsr-record").click();
		await fillIntake(page, world, { reference: "EQB/TG/2099/0001" });
		await page.getByTestId("tsr-d-submit").click();
		await expect(page.getByTestId("tsr-recorded")).toHaveText(/^Receipt recorded\. Intake reference TSI-[0-9A-F]{10}\.$/);
		await expect(page.getByTestId("tsr-row").locator("td").nth(4)).toContainText("Before deadline");
		await expectNoBidFacts(page, world);
		expect(execute<Record<string, string>>("physical_receipt_status", { tender_reference: world.tender_reference }).physical_receipt_status).toBe("Not recorded");
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("the receipts stack as labelled cards at 390 px and the dialog fits", async ({ page }) => {
		const errors = collectConsoleErrors(page);
		await page.setViewportSize({ width: 390, height: 844 });
		await login(page, HOPF, PASSWORD);
		await openPage(page);
		await expect(page.getByTestId("tsr-row")).toHaveCount(1);
		await expect(page.getByTestId("tsr-table").locator("thead")).toHaveCSS("position", "absolute");
		await expectNoHorizontalOverflow(page);
		await page.getByTestId("tsr-record").click();
		await expect(page.getByTestId("tsr-d-tender")).toBeFocused();
		await expectNoHorizontalOverflow(page);
		await page.keyboard.press("Escape");
		await expect(page.getByTestId("tsr-dialog")).toHaveCount(0);
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	for (const [who, user] of [["a Procurement Officer", OFFICER], ["an Auditor", AUDITOR]] as const) {
		test(`${who} is told the page is not theirs and can record nothing`, async ({ page }) => {
			const errors = collectConsoleErrors(page);
			await page.setViewportSize({ width: 1440, height: 1024 });
			await login(page, user, PASSWORD);
			await openPage(page);
			await expect(page.getByTestId("tsr-forbidden")).toContainText("Only the Head of Procurement Function records physical tender-security originals.");
			await expect(page.getByTestId("tsr-record")).toHaveCount(0);
			await expect(page.getByTestId("tsr-table")).toHaveCount(0);
			expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
		});
	}
});
