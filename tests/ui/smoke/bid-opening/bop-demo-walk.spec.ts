import { execSync } from "node:child_process";
import path from "node:path";

import { Browser, expect, Page, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { loginToPortal, waitForPortal } from "../../helpers/portal";
import { collectConsoleErrors, expectNextStep, expectScreen } from "./bopWorld";

/**
 * The Bid Opening demo profiles walked the way a person uses them: every
 * person starts from the Desk home and the menu (Procurement → Tender
 * Management → Tenders → the Tender → Bid opening), or from the notification
 * bell, never from a typed address. The profiles are the canonical Tender's
 * opening at one moment (`make seed-bop-profile`), as the canonical people;
 * the canonical completed opening is put back afterwards.
 */

const BENCH_ROOT = path.resolve(__dirname, "../../../../../..");
const SITE = process.env.UI_SITE || "kentender.midas.com";
const PROFILES = "kentender_procurement.bid_opening.seeds.profiles";
const PASSWORD = process.env.UI_SEED_PASSWORD || "Test@123";
const REF = "TND-MOH-2027-002";
const AMINA = "amina.hassan@moh.example.test";
const CHARLES = "charles.mutiso@moh.example.test";
const BRIAN = "brian.wafula@moh.example.test";
const BEATRICE = "beatrice.kamau@moh.example.test";
const JANE = "jane.wanjiku@observer.example";

function bench(fn: string, kwargs = ""): string {
	return execSync(`cd "${BENCH_ROOT}" && bench --site ${SITE} execute ${PROFILES}.${fn}${kwargs ? ` --kwargs '${kwargs}'` : ""}`, { stdio: "pipe", timeout: 600_000, encoding: "utf-8" });
}
function loadProfile(profile: string): { checks: { ok: boolean; person: string; observed: string }[] } {
	const out = JSON.parse(bench("load_profile", JSON.stringify({ profile })).trim().split("\n").pop() || "{}");
	for (const c of out.checks || []) expect(c.ok, `${profile}: ${c.person} sees "${c.observed}"`).toBe(true);
	return out;
}

/** Each person in their own browser session, signed in; the previous
 *  person's session is closed first (one open session at a time). */
let current: import("@playwright/test").BrowserContext | null = null;
async function as(browser: Browser, user: string): Promise<Page> {
	if (current) await current.close();
	const context = await browser.newContext({ baseURL: process.env.UI_BASE_URL || "http://127.0.0.1:8000" });
	current = context;
	const page = await context.newPage();
	await login(page, user, PASSWORD);
	return page;
}

/** Desk home → Procurement → Tender Management → Tenders → the Tender → Bid opening. */
async function openFromMenu(page: Page): Promise<void> {
	await page.setViewportSize({ width: 1440, height: 1024 });
	await page.goto("/app", { waitUntil: "domcontentloaded" });
	await page.getByText("Procurement", { exact: true }).first().click();
	const tenders = page.locator('a[href="/desk/tenders"]:visible');
	if (!(await tenders.count())) await page.locator("text=Tender Management").first().click();
	await tenders.first().click();
	const shell = page.locator('[data-testid="tnd-shell"]');
	await expect(shell).toHaveAttribute("data-screen", "workspace", { timeout: 30_000 });
	await expect(shell).toHaveAttribute("data-loading", "false", { timeout: 30_000 });
	await page.locator(`tr[data-tender="${REF}"] button`).first().click();
	await expect(shell).toHaveAttribute("data-loading", "false", { timeout: 30_000 });
	await page.locator('[data-testid="tnd-link-bid-opening"]').click();
}

/** Desk home → the notification bell → the named notification. */
async function openFromBell(page: Page, subject: string): Promise<void> {
	await page.setViewportSize({ width: 1440, height: 1024 });
	await page.goto("/app", { waitUntil: "domcontentloaded" });
	await page.locator(".dropdown-notifications .nav-link, .dropdown-notifications > a").first().click();
	await page.locator(".notification-list-body").getByText(subject).first().click();
}

test.describe.configure({ mode: "serial", timeout: 600_000 });

test.describe("Bid Opening demo profiles, walked from the menu", () => {
	test.afterAll(async () => {
		if (current) await current.close();
		current = null;
		bench("restore_base");
	});

	test("appoint and publish (Amina), with the independent member reaching it from her bell", async ({ browser }) => {
		let page: Page;
		loadProfile("BOP-DEMO-APPOINT");
		page = await as(browser, AMINA);
		const errors = collectConsoleErrors(page);
		await openFromMenu(page);
		await expectScreen(page, "prepare");
		await expectNextStep(page, "your_turn", "Appoint opening committee");
		const add = async (user: string, role: string) => {
			await page.locator('[data-testid="bop-add-member"]').click();
			await page.locator('[data-testid="bop-add-member-person"]').selectOption(user);
			await page.locator('[data-testid="bop-add-member-role"]').selectOption(role);
			await page.locator('[data-testid="bop-add-member-confirm"]').click();
		};
		await add(CHARLES, "Chair and recorder");
		await add(BRIAN, "Member");
		await page.locator('[data-testid="bop-appoint"]').click();
		await expectNextStep(page, "your_turn_blocked", "The opening committee needs an independent third member");
		await page.locator('[data-testid="bop-guidance"] [data-kt="next-step"] button', { hasText: "Add an independent third member" }).click();
		await page.locator('[data-testid="bop-add-member-person"]').selectOption(BEATRICE);
		await page.locator('[data-testid="bop-add-member-role"]').selectOption("Independent member");
		await page.locator('[data-testid="bop-add-member-confirm"]').click();
		await page.locator('[data-testid="bop-appoint"]').click();
		await expectScreen(page, "prepare");
		await expectNextStep(page, "your_turn", "Publish how to attend");

		page = await as(browser, BEATRICE);
		await openFromBell(page, `You are on the opening committee for ${REF}`);
		await expectScreen(page, "open-bids");

		page = await as(browser, AMINA);
		await openFromMenu(page);
		await page.locator('[data-testid="bop-open-arrangements"]').click();
		await page.locator('[data-testid="bop-publish"]').click();
		await expectScreen(page, "prepare");
		await expectNextStep(page, "done", /^You published how to attend on /);
		expect(errors, `console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("the whole opening from Ready to start, each person from the menu or the bell, to completion", async ({ browser }) => {
		let page: Page;
		loadProfile("BOP-DEMO-READY");
		page = await as(browser, CHARLES);
		await openFromMenu(page);
		await expectScreen(page, "open-bids");
		await expectNextStep(page, "your_turn", "Ready to start");
		await page.locator('[data-testid="bop-start"]').click();
		await expectNextStep(page, "your_turn", "Open the first bid");
		await page.locator('[data-testid="bop-open-next"]').click();
		await expectNextStep(page, "your_turn", "Record what was read aloud");

		page = await as(browser, BRIAN);
		await openFromMenu(page);
		await expectScreen(page, "open-bids");
		await expectNextStep(page, "your_turn", "Read these details aloud");
		await expect(page.locator('[data-testid="bop-read-aloud-text"]')).toContainText("Afya Digital Supplies Limited");

		page = await as(browser, CHARLES);
		await openFromMenu(page);
		await page.locator('[data-testid="bop-readout-by"]').selectOption(BRIAN);
		await page.locator('[data-testid="bop-record-readout"]').click();
		await expectNextStep(page, "your_turn", "End the opening");
		await page.locator('[data-testid="bop-end"]').click();
		await expectScreen(page, "record");
		await page.locator('[data-testid="bop-prepare-record"]').click();
		await page.locator('[data-testid="bop-finish-record"]').click();
		await expectNextStep(page, "your_turn", "Review and sign opening record");
		await page.locator('[data-testid="bop-sign"]').click();
		await expectNextStep(page, "waiting", /^Waiting for .* to sign the opening record$/);

		page = await as(browser, BRIAN);
		await openFromBell(page, `Review and sign opening record for ${REF}`);
		await expectScreen(page, "record");
		await page.locator('[data-testid="bop-sign"]').click();
		await expectNextStep(page, "waiting", /^Waiting for .* to sign the opening record$/);

		page = await as(browser, BEATRICE);
		await openFromBell(page, `Review and sign opening record for ${REF}`);
		await expectScreen(page, "record");
		await page.locator('[data-testid="bop-sign"]').click();
		await expectScreen(page, "completed");
		await expectNextStep(page, "done", /after the last signature\.$/);

		page = await as(browser, AMINA);
		await openFromMenu(page);
		await expectScreen(page, "completed");
		await expect(page.locator('[data-testid="bop-summary"]')).toContainText("EV-IN-");
	});

	test("a member missing at the deadline: the chair notifies her, she joins from the bell, the chair starts", async ({ browser }) => {
		let page: Page;
		loadProfile("BOP-DEMO-MISSING-MEMBER");
		page = await as(browser, CHARLES);
		await openFromMenu(page);
		await expectNextStep(page, "waiting", "Opening cannot start because Beatrice Kamau has not joined.");
		await page.locator(`[data-testid="bop-notify-${BEATRICE}"]`).click();
		await expectScreen(page, "open-bids");

		page = await as(browser, BEATRICE);
		await openFromBell(page, `Join opening for ${REF}`);
		await expectNextStep(page, "your_turn", `Join opening for ${REF}`);
		await page.locator('[data-testid="bop-join"]').click();
		await expect(page.locator('[data-testid="bop-join"]')).toHaveCount(0);

		page = await as(browser, CHARLES);
		await openFromMenu(page);
		await expectNextStep(page, "your_turn", "Ready to start");
		await page.locator('[data-testid="bop-start"]').click();
		await expectNextStep(page, "your_turn", "Open the first bid");
	});

	test("the public: Jane reaches the opening from the Tender's public page and joins", async ({ browser }) => {
		let page: Page;
		loadProfile("BOP-DEMO-JOIN");
		if (current) await current.close();
		current = await browser.newContext({ baseURL: process.env.UI_BASE_URL || "http://127.0.0.1:8000" });
		page = await current.newPage();
		await loginToPortal(page, JANE, PASSWORD, `/tenders/${REF}`);
		await page.locator('[data-testid="bds-overview-link-bid-opening"]').click();
		await waitForPortal(page);
		await expect(page.locator('[data-testid="bop-public"]')).toHaveAttribute("data-phase", "join");
		await page.locator('[data-testid="bop-public-join"]').click();
		await expect(page.locator('[data-testid="bop-public-joined"]')).toContainText("Joined");
	});

	test("paused and problem states: support could not open the bid (Charles), the decision (Amina), never started (Amina)", async ({ browser }) => {
		let page: Page;
		loadProfile("BOP-DEMO-CANNOT-OPEN");
		page = await as(browser, CHARLES);
		await openFromMenu(page);
		await expectNextStep(page, "your_turn_blocked", /^This bid could not be opened/);
		await expect(page.locator('[data-testid="bop-retry"]')).toBeDisabled();

		loadProfile("BOP-DEMO-AO-DECISION");
		page = await as(browser, AMINA);
		await openFromMenu(page);
		await expectNextStep(page, "your_turn", "Decide how to proceed with the paused opening");

		loadProfile("BOP-DEMO-NOT-HELD");
		await openFromMenu(page);
		await page.locator('[data-testid="bop-not-held-reason"]').fill("The public attendance service was unavailable; opening did not start");
		await page.locator('[data-testid="bop-record-not-held"]').click();
		await expectNextStep(page, "your_turn", "Decide what happens next");
	});
});
