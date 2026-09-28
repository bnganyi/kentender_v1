import path from "node:path";

import { expect, Page, test } from "@playwright/test";

import { collectPortalConsoleErrors, expectNoFrappeDialog, expectNoHorizontalOverflow, loginToPortal, waitForPortal } from "../../helpers/portal";
import { accountFixture, bdsFixture, restoreAccountWorld, restoreBdsWorld } from "./bdsWorld";

/**
 * BDS-CHG-001 v0.8 acceptance rows the 28 Sep 2026 audit left without a
 * browser proof (owner: "Create the tests"): the sign-in round trip back to
 * the same Tender (BDS01-AC-003); every bid dialog at 390 with focus kept in
 * the dialog and returned on Escape (BDS03-AC-013, BDS07-AC-014); an
 * automated accessibility scan of the portal pages (BDS01-AC-088); the first
 * working region at 200% zoom and no journey tracker on the register-type
 * pages (BDS08-AC-004).
 */
type OverviewWorld = { tender_reference: string; bid_reference: string; password: string; afya_user: string; kisiwa_user: string };
type MyBidsWorld = { tender_reference: string; bid_reference: string; receipt_reference: string; password: string; representative: string; signatory: string; other_user: string };

const AXE = path.resolve(__dirname, "../../../../node_modules/axe-core/axe.min.js");

async function axeViolations(page: Page): Promise<string[]> {
	await page.addScriptTag({ path: AXE });
	const found = await page.evaluate(async () => {
		// @ts-expect-error axe is injected above
		const result = await window.axe.run(document.querySelector("#kt-portal-app") || document, { resultTypes: ["violations"], runOnly: { type: "tag", values: ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"] } });
		return result.violations.filter((v: { impact: string }) => v.impact === "serious" || v.impact === "critical").map((v: { id: string; nodes: { target: string[] }[] }) => `${v.id} @ ${v.nodes.slice(0, 3).map((n) => n.target.join(" ")).join(", ")}`);
	});
	return found;
}

async function dialogAt390(page: Page, open: () => Promise<void>, dialog: string) {
	await page.setViewportSize({ width: 390, height: 844 });
	await open();
	await expect(page.getByTestId(dialog)).toBeVisible();
	await expectNoHorizontalOverflow(page);
	expect(await page.evaluate((id) => !!document.activeElement && !!document.querySelector(`[data-testid="${id}"]`)?.contains(document.activeElement), dialog)).toBe(true);
	await page.keyboard.press("Tab");
	expect(await page.evaluate((id) => !!document.querySelector(`[data-testid="${id}"]`)?.contains(document.activeElement), dialog)).toBe(true);
	await page.keyboard.press("Escape");
	await expect(page.getByTestId(dialog)).toHaveCount(0);
}

test.describe.configure({ mode: "serial", timeout: 300_000 });

test.describe("BDS acceptance gaps — browser proofs", () => {
	test.afterAll(() => {
		restoreBdsWorld();
		restoreAccountWorld();
	});

	test("a signed-out visitor signs in from the Tender and comes back to the same Tender (BDS01-AC-003)", async ({ page }) => {
		const world = bdsFixture<OverviewWorld>("reset_overview_fixture", { started: false });
		await page.context().clearCookies();
		await page.goto(`/tenders/${world.tender_reference}`, { waitUntil: "domcontentloaded" });
		await waitForPortal(page);
		await page.getByTestId("bds-overview-action").click();
		await expect(page).toHaveURL(/\/login/);
		await page.locator("#login_email").fill(world.kisiwa_user);
		await page.locator("#login_password").fill(world.password);
		await page.getByRole("button", { name: "Login", exact: true }).click();
		await expect(page).toHaveURL(new RegExp(`/tenders/${world.tender_reference}$`), { timeout: 60_000 });
		await waitForPortal(page);
		await expect(page.getByTestId("bds-overview-action")).toHaveText("Start bid");
	});

	test("every bid dialog fits 390, keeps focus inside and gives it back on Escape (BDS03-AC-013, BDS07-AC-014)", async ({ page }) => {
		const errors = collectPortalConsoleErrors(page);
		const overview = bdsFixture<OverviewWorld>("reset_overview_fixture", { started: true });
		const tender = `/tenders/${overview.tender_reference}`;
		// Who is bidding? (Peter, no bid yet)
		await loginToPortal(page, overview.kisiwa_user, overview.password, tender);
		await dialogAt390(page, () => page.getByTestId("bds-overview-action").click(), "bds-start-dialog");
		await expect(page.getByTestId("bds-overview-action")).toBeFocused();
		// Ask a question (David, a candidate while clarifications are open)
		await page.context().clearCookies();
		await loginToPortal(page, overview.afya_user, overview.password, tender);
		await page.setViewportSize({ width: 390, height: 844 });
		await dialogAt390(page, () => page.getByTestId("bds-ask-question").click(), "bds-question-dialog");
		await expect(page.getByTestId("bds-ask-question")).toBeFocused();

		// Submit this bid? (Mary, ready)
		const ready = bdsFixture<MyBidsWorld>("reset_my_bids_fixture", { state: "review" });
		await page.context().clearCookies();
		await loginToPortal(page, ready.signatory, ready.password, `/tenders/${ready.tender_reference}/bid/submit`);
		await page.getByTestId("bds-submit-decision").locator("label.kt-checkbox").click();
		await dialogAt390(page, () => page.getByTestId("bds-submit-open").click(), "bds-submit-dialog");
		await expect(page.getByTestId("bds-submit-open")).toBeFocused();

		// Withdraw this bid? (Mary, submitted)
		const submitted = bdsFixture<MyBidsWorld>("reset_my_bids_fixture", { state: "submitted" });
		await page.context().clearCookies();
		await loginToPortal(page, submitted.signatory, submitted.password, `/tenders/${submitted.tender_reference}/bid/receipt/${submitted.receipt_reference}`);
		await dialogAt390(page, () => page.getByTestId("bds-receipt-withdraw").click(), "bds-withdraw-dialog");
		await expect(page.getByTestId("bds-receipt-withdraw")).toBeFocused();
		await expectNoFrappeDialog(page);
		expect(errors.filter((e) => !/404 \(Not Found\)/.test(e)), errors.join(" | ")).toEqual([]);
	});

	test("the portal pages pass the automated accessibility scan (BDS01-AC-088)", async ({ page }) => {
		const world = bdsFixture<MyBidsWorld>("reset_my_bids_fixture", { state: "submitted" });
		await page.setViewportSize({ width: 1440, height: 1024 });
		const pages = [
			"/tenders",
			`/tenders/${world.tender_reference}`,
			`/tenders/${world.tender_reference}/bid`,
			...["documents", "company", "requirements", "price", "review"].map((t) => `/tenders/${world.tender_reference}/bid/${t}`),
			`/tenders/${world.tender_reference}/bid/receipt/${world.receipt_reference}`,
			"/my-bids",
			"/account/receipts",
			"/account",
		];
		await loginToPortal(page, world.signatory, world.password, pages[0]);
		const failures: string[] = [];
		for (const url of pages) {
			await page.goto(url, { waitUntil: "domcontentloaded" });
			await waitForPortal(page);
			await page.waitForLoadState("networkidle");
			for (const v of await axeViolations(page)) failures.push(`${url}: ${v}`);
		}
		expect(failures, failures.join("\n")).toEqual([]);
	});

	test("at 200% the first working region is on screen, and register pages carry no journey tracker (BDS08-AC-004)", async ({ page }) => {
		const world = bdsFixture<MyBidsWorld>("reset_my_bids_fixture", { state: "submitted" });
		await page.setViewportSize({ width: 1440, height: 1024 });
		await loginToPortal(page, world.signatory, world.password, `/tenders/${world.tender_reference}/bid`);
		// 200% browser zoom on a 1440 × 1024 screen is a 720 × 512 CSS-pixel viewport
		await page.setViewportSize({ width: 720, height: 512 });
		for (const url of [`/tenders/${world.tender_reference}/bid`, `/tenders/${world.tender_reference}`, "/my-bids", "/account/receipts", "/tenders"]) {
			await page.goto(url, { waitUntil: "domcontentloaded" });
			await waitForPortal(page);
			await expect(page.locator("#kt-portal-app h1").first()).toBeInViewport();
			await expectNoHorizontalOverflow(page);
		}
		for (const url of ["/tenders", "/account/receipts", "/my-bids/not-a-page"]) {
			await page.goto(url, { waitUntil: "domcontentloaded" });
			await waitForPortal(page);
			await expect(page.locator('[data-kt="journey"]')).toHaveCount(0);
		}
	});

	test("a suspended Account still reads its receipts register and receipt, with no change action (BDS01-AC-010)", async ({ page }) => {
		const world = bdsFixture<MyBidsWorld>("reset_my_bids_fixture", { state: "submitted" });
		expect(accountFixture<{ account_status: string }>("suspend_organisation", { registration_number: "PVT-PW-AFYA01" }).account_status).toBe("Suspended");
		const errors = collectPortalConsoleErrors(page);
		await page.setViewportSize({ width: 1440, height: 1024 });
		await loginToPortal(page, world.signatory, world.password, "/account/receipts");
		await expect(page.getByTestId(`bds-receipt-row-${world.receipt_reference}`)).toContainText("Submitted");
		await expect(page.getByTestId("bds-receipts")).toContainText(/suspended/i);
		await page.getByTestId(`bds-receipt-row-${world.receipt_reference}`).getByRole("link").first().click();
		await expect(page).toHaveURL(new RegExp(`/bid/receipt/${world.receipt_reference}$`));
		await expect(page.getByTestId("bds-receipt-facts")).toContainText(world.receipt_reference);
		await expect(page.getByTestId("bds-receipt-withdraw")).toHaveCount(0);
		await expect(page.getByTestId("bds-receipt-prepare_replacement")).toHaveCount(0);
		await page.setViewportSize({ width: 390, height: 844 });
		await page.goto("/account/receipts", { waitUntil: "domcontentloaded" });
		await waitForPortal(page);
		await expect(page.getByTestId("bds-receipts-cards")).toBeVisible();
		await expectNoHorizontalOverflow(page);
		expect(errors, errors.join(" | ")).toEqual([]);
	});
});
