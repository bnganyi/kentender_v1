import path from "node:path";

import { expect, Page, test } from "@playwright/test";

import { login, loginAsAdministrator } from "../../helpers/auth";
import { collectPortalConsoleErrors, expectNoFrappeDialog, expectNoHorizontalOverflow, loginToPortal, waitForPortal } from "../../helpers/portal";
import { HOPF, PASSWORD as DESK_PASSWORD } from "../tenders/helpers";
import { bdsFixture, restoreBdsWorld } from "./bdsWorld";

/**
 * BDS-CHG-001 v0.8 plan Phase 12 — the §13.3 persona release pass, on this
 * module's own Playwright world (the Tenders test Tender, Afya (Test) and
 * Kisiwa (Test), the Test Trust Service and Test Tender Box, the persisted
 * test clock), in one worker so it reads as one evidence trail:
 *
 * Mary's Account is Active with David assigned; David starts the bid, asks a
 * question, completes the tasks and acknowledges the addendum; Charles
 * records the physical original blind in Desk; David reviews without Submit;
 * Mary reviews, signs and submits and reads her receipt; Peter is told the
 * bid does not exist; the period closes and the sealed box goes to Bid
 * Opening with no bid content; the Administrator's technical read finds the
 * bid's metadata only. A second world proves Mary's withdrawal.
 *
 * Task entry itself is proven page by page by the slice specs
 * (company, requirements, price); here the fixture completes the tasks with
 * the §10.1 facts through the same commands, at the §13.3 instants. Each
 * page read is captured at 1440 and 390 px into the evidence pack
 * (docs/mvp-1-r1/12_bid_submission/evidence/v0_8/screens/).
 */
type World = { tender_reference: string; bid_reference: string; receipt_reference: string; password: string; representative: string; signatory: string; other_user: string };

const EVIDENCE = path.resolve(__dirname, "../../../../docs/mvp-1-r1/12_bid_submission/evidence/v0_8/screens");

async function capture(page: Page, name: string): Promise<void> {
	await page.setViewportSize({ width: 1440, height: 1024 });
	await page.screenshot({ path: `${EVIDENCE}/bds-release-${name}-1440.png`, fullPage: true });
	await page.setViewportSize({ width: 390, height: 844 });
	await expectNoHorizontalOverflow(page);
	await page.screenshot({ path: `${EVIDENCE}/bds-release-${name}-390.png`, fullPage: true });
	await page.setViewportSize({ width: 720, height: 512 }); // 1440 at 200% zoom
	await expectNoHorizontalOverflow(page);
	await page.setViewportSize({ width: 1440, height: 1024 });
}

async function signOut(page: Page): Promise<void> {
	await page.context().clearCookies();
}

test.describe.configure({ mode: "serial", timeout: 900_000 });

test.describe("BDS-CHG-001 v0.8 — persona release pass", () => {
	test.afterAll(() => restoreBdsWorld());

	test("§13.3: start, question, tasks, addendum, blind intake, review, signed submission, receipt, close and hand-off", async ({ page }) => {
		const world = bdsFixture<World>("reset_my_bids_fixture", { state: "empty" });
		const base = `/tenders/${world.tender_reference}`;
		const errors = collectPortalConsoleErrors(page);
		await page.setViewportSize({ width: 1440, height: 1024 });

		// Mary — her Account is Active and David is its Supplier Representative.
		await loginToPortal(page, world.signatory, world.password, "/account");
		await expect(page.getByTestId("acc-status")).toContainText("Active");
		await expect(page.locator("body")).toContainText("David Ouma");
		await capture(page, "account");
		await signOut(page);

		// David — Start bid from the published Tender.
		await loginToPortal(page, world.representative, world.password, base);
		await page.getByTestId("bds-overview-action").click();
		const start = page.getByTestId("bds-start-dialog");
		await expect(start.getByRole("dialog")).toHaveAccessibleName("Who is bidding?");
		await start.getByTestId("bds-start-submit").click();
		await expect(page.getByTestId("bds-start-dialog")).toHaveCount(0);
		await expect(page.getByTestId("bds-overview-action")).toHaveText("Continue bid");
		await capture(page, "overview-draft");

		// …asks a question before the clarification deadline.
		await page.getByTestId("bds-ask-question").click();
		const question = page.getByTestId("bds-question-dialog");
		await question.getByTestId("bds-question-text").fill("May the two comparable contracts be from different customers?");
		await question.getByTestId("bds-question-send").click();
		await expect(question.getByTestId("bds-question-sent")).toContainText("Question received");
		await question.getByTestId("bds-question-close").click();

		// 19–30 May: the company and requirements tasks, with the §10.1 facts.
		await page.getByTestId("bds-overview-action").click();
		await expect(page).toHaveURL(new RegExp(`${base}/bid$`));
		await expect(page.getByTestId("bds-workspace-refs")).toContainText("BID-");
		const reference = (await page.getByTestId("bds-workspace-refs").innerText()).match(/BID-[A-Z0-9-]+/)?.[0] || "";
		expect(reference).toMatch(/^BID-/);
		bdsFixture("fill_world_bid", { bid_reference: reference, tasks: ["company", "requirements"], at: "2027-05-20 11:10:00" });
		bdsFixture("set_instant", { instant: "2027-05-20 11:15:00" });
		await page.reload({ waitUntil: "domcontentloaded" });
		await waitForPortal(page);
		await expect(page.getByTestId("bds-task-company")).toContainText("Complete");
		await capture(page, "workspace-preparing");

		// 31 May: the addendum; 1 Jun 12:05 David acknowledges it and the bid moves to it.
		bdsFixture("issue_world_addendum", { tender_reference: world.tender_reference, instant: "2027-06-01 12:05:00" });
		await page.goto(`${base}/bid/documents`, { waitUntil: "domcontentloaded" });
		await waitForPortal(page);
		await expect(page.getByTestId("bds-documents-badge")).toHaveText("Needs attention");
		await page.locator('[data-testid^="bds-acknowledge-"]').click();
		await page.getByTestId("bds-documents-save").click();
		// Save and continue leads to the next task still to do: the addendum left Price needing attention, so Price
		await expect(page).toHaveURL(new RegExp(`${base}/bid/price$`));
		await page.goto(`${base}/bid/company`, { waitUntil: "domcontentloaded" });
		// …and reviews the responses the addendum moved (§13.3 Draft Version 5).
		bdsFixture("fill_world_bid", { bid_reference: reference, tasks: ["company", "requirements"], at: "2027-06-01 12:10:00" });
		await page.reload({ waitUntil: "domcontentloaded" });
		await waitForPortal(page);
		await expect(page.getByTestId("bds-company-badge")).toHaveText("Complete");
		await capture(page, "company");
		await signOut(page);

		// 10 Jun 10:00 — Charles records the physical original blind, in Desk.
		const security = bdsFixture<Record<string, string>>("world_security", { bid_reference: reference });
		bdsFixture("set_instant", { instant: "2027-06-10 10:00:00" });
		await login(page, HOPF, DESK_PASSWORD);
		await page.goto("/desk/tender-security-receipts", { waitUntil: "domcontentloaded" });
		await expect(page.getByTestId("tsr-shell")).toHaveAttribute("data-loading", "false", { timeout: 30_000 });
		await page.getByTestId("tsr-record").click();
		const intake = page.getByTestId("tsr-dialog");
		await intake.getByTestId("tsr-d-tender").fill(world.tender_reference);
		await intake.getByTestId("tsr-d-tender").blur();
		await expect(intake.getByTestId("tsr-d-requirement")).toContainText("Required: KES 500,000.00");
		await intake.getByTestId("tsr-d-type").selectOption({ label: security.security_type });
		await intake.getByTestId("tsr-d-issuer").fill(security.issuer);
		await intake.getByTestId("tsr-d-reference").fill(security.reference);
		await intake.getByTestId("tsr-d-amount").fill(security.amount);
		await intake.getByTestId("tsr-d-received").fill("2027-06-10T09:55");
		await intake.getByTestId("tsr-d-confirm").setChecked(true);
		await intake.getByTestId("tsr-d-submit").click();
		await expect(page.getByTestId("tsr-recorded")).toContainText("Receipt recorded. Intake reference TSI-");
		await expect(page.locator(".kt-tsr")).not.toContainText(reference);
		await page.screenshot({ path: `${EVIDENCE}/bds-release-intake-1440.png`, fullPage: true });
		await signOut(page);

		// 10 Jun 13:50 — the price completes the Draft; 14:15 David reviews and cannot submit.
		bdsFixture("fill_world_bid", { bid_reference: reference, tasks: ["price"], at: "2027-06-10 13:50:00" });
		bdsFixture("set_instant", { instant: "2027-06-10 14:15:00" });
		await loginToPortal(page, world.representative, world.password, `${base}/bid/review`);
		await expect(page.getByTestId("bds-review-result")).toHaveText("All required bid information is complete.");
		await expect(page.getByTestId("bds-review-security")).toContainText("recorded as received on 10 Jun 2027, 09:55 EAT");
		await expect(page.getByText("Submit bid", { exact: true })).toHaveCount(0);
		await signOut(page);

		// Mary reviews, signs and submits; the receipt is her proof.
		await loginToPortal(page, world.signatory, world.password, `${base}/bid/review`);
		await capture(page, "review");
		bdsFixture("set_instant", { instant: "2027-06-10 14:31:58" });
		await page.getByTestId("bds-review-action").click();
		await expect(page).toHaveURL(new RegExp(`${base}/bid/submit$`));
		// She has no certificate yet: she obtains one, then Check certificate.
		await expect(page.getByTestId("bds-submit-signatory").locator(".kt-status")).toHaveText("Not available");
		await page.screenshot({ path: `${EVIDENCE}/bds-release-submit-certificate-1440.png`, fullPage: true });
		bdsFixture("issue_signatory_certificate", { bid_reference: reference });
		await page.getByRole("button", { name: "Check certificate" }).click();
		await expect(page.getByTestId("bds-submit-signatory").locator(".kt-status")).toHaveText("Ready");
		await page.getByTestId("bds-submit-decision").locator("label.kt-checkbox").click();
		await capture(page, "submit");
		await page.getByTestId("bds-submit-open").click();
		await page.screenshot({ path: `${EVIDENCE}/bds-release-submit-dialog-1440.png` });
		await page.getByTestId("bds-submit-confirm").click();
		await expect(page).toHaveURL(new RegExp(`${base}/bid/receipt/RCPT-`), { timeout: 60_000 });
		await expect(page.getByTestId("bds-receipt-facts")).toContainText("10 Jun 2027, 14:31:58 EAT");
		await expect(page.getByTestId("bds-receipt-facts")).toContainText("Mary Wanjiku");
		const receipt = new URL(page.url()).pathname.split("/").pop() || "";
		await capture(page, "receipt");
		await signOut(page);

		// Peter (Kisiwa) is told the bid and its receipt do not exist.
		await loginToPortal(page, world.other_user, world.password, `${base}/bid/receipt/${receipt}`);
		await expect(page.getByTestId("bds-state-receipt-not-found")).toBeVisible();
		await expect(page.locator("body")).not.toContainText(reference);
		await signOut(page);

		// 12 Jun 11:00 — the period ends; the sealed box goes to Bid Opening with no bid content.
		const closed = bdsFixture<{ handoff: string; envelopes: number; payload_text: string }>("close_world", { tender_reference: world.tender_reference });
		expect(closed.envelopes).toBe(1);
		// no bid content (its answers and prices); the physical-intake inventory
		// Charles recorded is carried by design (owner decision OD-H)
		for (const content of ["ApexBook", "160000", "6400000", "Seeded answer"]) expect(closed.payload_text, `the hand-off carries "${content}"`).not.toContain(content);
		expect(closed.payload_text).toContain('"intakes"');
		await loginToPortal(page, world.signatory, world.password, `${base}/bid/receipt/${receipt}`);
		await expect(page.getByTestId("bds-receipt-sentence")).toContainText("Submission changes closed on ");
		await expect(page.getByTestId("bds-receipt-actions").locator(".kt-btn")).toHaveText(["Print receipt"]);
		await capture(page, "receipt-closed");
		await expectNoFrappeDialog(page);
		expect(errors.filter((e) => !/404 \(Not Found\)/.test(e)), errors.join(" | ")).toEqual([]);
		await signOut(page);

		// The Administrator's technical read finds the bid's metadata, never its content.
		await loginAsAdministrator(page);
		await page.goto("/app/technical-search", { waitUntil: "domcontentloaded" });
		await page.getByTestId("kt-ts-input").fill(reference);
		await page.getByTestId("kt-ts-search").click();
		const row = page.getByTestId("kt-ts-row").first();
		await expect(row).toContainText(reference, { timeout: 20_000 });
		await expect(page.locator("body")).not.toContainText("ApexBook");
	});

	test("Mary withdraws a submitted bid with a reason and the acknowledgement keeps the history", async ({ page }) => {
		const world = bdsFixture<World>("reset_my_bids_fixture", { state: "submitted" });
		await page.setViewportSize({ width: 1440, height: 1024 });
		await loginToPortal(page, world.signatory, world.password, `/tenders/${world.tender_reference}/bid/receipt/${world.receipt_reference}`);
		await page.getByTestId("bds-receipt-withdraw").click();
		const dialog = page.getByRole("dialog", { name: "Withdraw this bid?" });
		await dialog.getByLabel("Reason for withdrawal").fill("Our pricing changed; we will submit a corrected bid.");
		await page.screenshot({ path: `${EVIDENCE}/bds-release-withdraw-dialog-1440.png` });
		await dialog.getByTestId("bds-withdraw-confirm").click();
		await expect(page.getByRole("heading", { level: 1, name: "Bid withdrawn" })).toBeVisible();
		await expect(page.getByTestId("bds-acknowledgement-facts")).toContainText(/WD-[A-Z0-9-]+/);
		await capture(page, "withdrawn");
	});
});
