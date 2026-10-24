import { Page, expect, test } from "@playwright/test";

import { asAt, format, parse, shortDateTime, world } from "../../helpers/anchor";
import { loginToPortal, waitForPortal } from "../../helpers/portal";
import { AMINA, CHARLES, DAVID, EVIDENCE, MARY, PASSWORD, as, awdFixture, closeSession, collectConsoleErrors, expectJourney, expectNextStep, expectScreen,
	openAwardsFromMenu } from "./awdWorld";

/**
 * The canonical award (AWD-CHG-001 v0.4 §13, `make seed-canonical THROUGH=award`)
 * walked the way people reach it — the Head from the menu, the Accounting
 * Officer from the bell, the supplier from her own Tender page in the portal —
 * never from a typed address. Starts from demo profile AWD-DEMO-OPINION on the
 * real Evaluation delivery of TND-MOH-2026-002 and ends with the canonical
 * award restored (tracker AWD4-1103).
 */

const REF = "TND-MOH-2026-002";
const AWARD = "AWD-MOH-2026-002";
// The Accounting Officer awards at this instant (second step); the server sets the supplier's reply deadline from it under the
// entity's rule (seven days, by 17:00). The expectation is derived from that instant, not from the story's deadline mapped on its
// own: `world()` pushes a story instant later than the as-at date a further week out (a live seed deadline), which the server's
// own computation does not (found 18 Oct 2026: the spec expected 29 Oct where the page said 22 Oct).
const AWARDED_AT = world("2027-06-17 10:00:00");
const REPLY_BY = `${format(new Date(parse(AWARDED_AT).moment.getTime() + 7 * 86_400_000), true)} 17:00:00`;
// The waiting period ends fifteen days after the notices, at 09:00 (the story's 2 Jul 2027 for notices on 17 Jun), computed by the server from the
// same instant.
const WAIT_ENDS = `${format(new Date(parse(AWARDED_AT).moment.getTime() + 15 * 86_400_000), true)} 09:00:00`;

async function openFromBell(page: Page, subject: string): Promise<void> {
	// Home carries the bell (the "Notification" control); Desk's own navbar bell is not the way in any more
	await page.goto("/app/home", { waitUntil: "domcontentloaded" });
	await page.getByText("Notification", { exact: true }).first().click();
	await page.getByText(subject).first().click();
}

test.describe.configure({ mode: "serial", timeout: 600_000 });

test.describe("Award, walked from the menu, the bell and the portal on the canonical Tender", () => {
	test.beforeAll(() => {
		awdFixture("set_instant", { instant: "" });
	});
	test.afterAll(async () => {
		await closeSession();
		awdFixture("set_instant", { instant: "" });
	});

	test("the Head of Procurement signs the opinion from the task in the menu", async ({ browser }) => {
		const profile = awdFixtureProfile("AWD-DEMO-OPINION");
		expect(profile.award).toBe(AWARD);
		const page = await as(browser, CHARLES);
		const errors = collectConsoleErrors(page);
		await openAwardsFromMenu(page);
		const row = page.locator('[data-testid="awd-root"] tr', { hasText: AWARD });
		await expect(row).toContainText("Prepare professional opinion");
		await row.getByRole("button", { name: "Open award" }).click();
		await expectScreen(page, "opinion");
		await expectNextStep(page, "your_turn", "Prepare the professional opinion.");
		const root = page.locator('[data-testid="awd-root"]');
		await expect(root.locator('[data-testid="awd-desc"]')).toContainText(REF);
		await expect(root.locator('[data-testid="awd-fact-supplier"]')).toHaveText("Afya Digital Supplies Limited");
		await root.locator("label.radio", { hasText: "Recommend award" }).click();
		await root.locator('[data-testid="awd-field-reason"]').fill("The signed report identifies Afya Digital Supplies Limited as the lowest evaluated responsive tenderer. No unresolved issue prevents the proposed award.");
		await root.locator('[data-testid="awd-action-sign-opinion"]').click();
		await expectScreen(page, "decision-read");
		await expectJourney(page, ["Done", "Current", "Not started", "Not started", "Not started"]);
		expect(errors, errors.join(" | ")).toEqual([]);
	});

	test("the Accounting Officer awards from the bell", async ({ browser }) => {
		awdFixture("set_instant", { instant: AWARDED_AT });
		const page = await as(browser, AMINA);
		await openFromBell(page, `Decide award for ${REF}`);
		await expectScreen(page, "decision");
		await expectNextStep(page, "your_turn", "Decide the award.");
		const root = page.locator('[data-testid="awd-root"]');
		await root.locator('[data-testid="awd-field-decision_reason"]').fill("I accept the recommendation in the signed evaluation report and professional opinion.");
		await root.locator('[data-testid="awd-action-award-and-notify-bidders"]').click();
		await expectScreen(page, "wait");
		await expectJourney(page, ["Done", "Done", "Done", "Current", "Not started"]);
	});

	test("the supplier finds and accepts the notice from her Tender page", async ({ browser }) => {
		awdFixture("set_instant", { instant: world("2027-06-18 09:00:00") });
		const context = await browser.newContext({ baseURL: process.env.UI_BASE_URL || "http://127.0.0.1:8000" });
		let page = await context.newPage();
		await page.setViewportSize({ width: 390, height: 844 });
		await loginToPortal(page, DAVID, PASSWORD, `/tenders/${REF}`);
		await waitForPortal(page);
		await page.locator('[data-testid="bds-overview-link-award-notice"]').click();
		let portal = page.locator('[data-testid="awd-portal"]');
		await expect(portal).toContainText("Mary Wanjiku must respond for Afya Digital Supplies Limited.", { timeout: 30_000 });
		await context.close();
		const mary = await browser.newContext({ baseURL: process.env.UI_BASE_URL || "http://127.0.0.1:8000" });
		page = await mary.newPage();
		await page.setViewportSize({ width: 390, height: 844 });
		await loginToPortal(page, MARY, PASSWORD, `/tenders/${REF}`);
		await waitForPortal(page);
		await page.locator('[data-testid="bds-overview-link-award-notice"]').click();
		portal = page.locator('[data-testid="awd-portal"]');
		await expect(portal.locator('[data-testid="awd-next-step-headline"]')).toHaveText("Your tender was successful.", { timeout: 30_000 });
		await expect(portal.locator('[data-testid="awd-fact-reply-by"]')).toHaveText(shortDateTime(REPLY_BY));
		await portal.locator('[data-testid="awd-action-accept-award"]').click();
		await portal.locator('[data-testid="awd-dialog-accept-award"]').click();
		await expect(portal.locator('[data-testid="awd-next-step-headline"]')).toHaveText("You accepted this award.", { timeout: 30_000 });
		await mary.close();
	});

	test("the wait ends and Contracting receives the canonical award", async ({ browser }) => {
		awdFixture("set_instant", { instant: world("2027-06-18 09:05:00") });
		let page = await as(browser, CHARLES);
		await page.goto("/app", { waitUntil: "domcontentloaded" });
		await openAwardsFromMenu(page);
		await page.goto(`/app/award/${AWARD}`, { waitUntil: "domcontentloaded" });
		await expectScreen(page, "wait");
		await expectNextStep(page, "waiting", "The required waiting period is still running.");
		await expect(page.locator('[data-testid="awd-fact-earliest-permitted-date-and-time"]')).toHaveText(shortDateTime(WAIT_ENDS));
		await page.screenshot({ path: `${EVIDENCE}/canonical-D05.png`, fullPage: true });
		if (WAIT_ENDS > asAt()) {
			// Contracting receives the award only when the waiting period ends, and in a world anchored on the real date that
			// moment (the story's 2 Jul 2027) is some days after the anchor: this step runs once the real clock reaches it
			// (SEED-002 v0.8 R1: no simulated instant is later than the real clock).
			const late = WAIT_ENDS;
			if (new Date(late.replace(" ", "T")).getTime() > Date.now() + 3 * 3_600_000) {
				test.info().annotations.push({ type: "not-yet-reached", description: `Contracting receives the canonical award at ${late}; the walk ends at the wait` });
				const restoredEarly = awdFixtureRestore();
				expect(restoredEarly.ok).toBe(true);
				return;
			}
		}
		awdFixture("set_instant", { instant: WAIT_ENDS });
		awdFixture("refresh", { award: AWARD });
		page = await as(browser, CHARLES);
		await page.goto(`/app/award/${AWARD}`, { waitUntil: "domcontentloaded" });
		await expectScreen(page, "delivered");
		await expectNextStep(page, "done", "Contracting has received the award.");
		await page.screenshot({ path: `${EVIDENCE}/canonical-D06.png`, fullPage: true });
		const restored = awdFixtureRestore();
		expect(restored.ok).toBe(true);
	});
});

function awdFixtureProfile(profile: string): { award: string } {
	return awdProfiles("load_profile", { profile });
}

function awdFixtureRestore(): { ok: boolean } {
	return awdProfiles("restore_base", {});
}

function awdProfiles<T = any>(fn: string, kwargs: Record<string, unknown>): T {
	// the demo profiles live beside the browser worlds
	const { execSync } = require("node:child_process");
	const path = require("node:path");
	const bench = path.resolve(__dirname, "../../../../../..");
	const args = Object.keys(kwargs).length ? ` --kwargs '${JSON.stringify(kwargs)}'` : "";
	const out = execSync(`cd "${bench}" && bench --site ${process.env.UI_SITE || "kentender.midas.com"} execute kentender_procurement.award.seeds.profiles.${fn}${args}`,
		{ stdio: "pipe", timeout: 300_000, encoding: "utf-8" });
	return JSON.parse(out.trim().split("\n").pop() || "{}") as T;
}
