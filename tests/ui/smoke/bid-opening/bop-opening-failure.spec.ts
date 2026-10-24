import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { collectConsoleErrors as tenderConsoleErrors, expectReady as expectTenderReady, expectSettled as expectTenderSettled } from "../tenders/helpers";
import { AO, AUDITOR, CHAIR, PASSWORD, SUPPORT, collectConsoleErrors, expectNextStep, expectScreen, gotoOpening, openingWorld, restoreBopWorld, verifyGrounds } from "./bopWorld";

/**
 * Opening-failure recovery and post-close cancellation (BOP-CHG-001 v0.16 §5.2, §10.7–§10.8; TPR-CHG-001 v0.24 §5.7, §5.12, §10.13 POSTCLOSE;
 * TRUST-OPS-001 v0.2 §9.2). Every journey starts where a person would: the opening page they were sent to, never a deep link into a state.
 *
 *  - OF-F01 recovered: support records a finding on its own page; the chair then retries the same bid.
 *  - OF-F02 irrecoverable: the Accounting Officer is told what stops the decision, follows the exact item to the Tender, cancels on a verified ground,
 *    and the opening ends with what was recorded kept.
 *  - OF-F03 not held: the same route ends a record that never started.
 */

test.describe.configure({ mode: "serial", timeout: 420_000 });

const GROUND = "INADEQUATE_BUDGET";
const REASON = "The confirmed budget available for this procurement is insufficient to proceed.";

test.describe("BOP-CHG-001 v0.16 — opening failure and cancellation", () => {
	test.afterAll(() => {
		verifyGrounds("");
		restoreBopWorld();
	});

	test("OF-F01: support records Recovered; the chair retries the same bid", async ({ page }) => {
		const errors = collectConsoleErrors(page);
		const world = openingWorld("unreadable");
		await login(page, SUPPORT, PASSWORD);
		await gotoOpening(page, world.tender_reference);
		await expect(page.locator('[data-testid="bop-support-incidents"]')).toBeVisible();
		// the finding needs a reason and a choice, and says so before anything is sent
		await page.locator('[data-testid="bop-finding-submit"]').click();
		await expect(page.locator('[data-testid="bop-finding-error"]')).toHaveText("Choose what you found.");
		await page.locator('[data-testid="bop-finding-select"]').selectOption("Recovered");
		await page.locator('[data-testid="bop-finding-submit"]').click();
		await expect(page.locator('[data-testid="bop-finding-error"]')).toHaveText("Record what you found.");
		await page.locator('[data-testid="bop-finding-reason"]').fill("The rendering service was restored and the package renders.");
		await page.locator('[data-testid="bop-finding-evidence"]').fill("CHK-RENDER-001");
		await page.locator('[data-testid="bop-finding-submit"]').click();
		// the re-render after the command shows the new finding in the table and in the form
		await expect(page.locator('[data-testid="bop-finding-current"]')).toHaveText("Recovered");
		await expect(page.locator('[data-testid^="bop-support-incident-"] td').nth(3)).toHaveText("Recovered");
		// support has no ceremony action of any kind
		await expect(page.locator('[data-testid="bop-retry"], [data-testid="bop-resume"], [data-testid="bop-open-next"]')).toHaveCount(0);

		await login(page, CHAIR, PASSWORD);
		await gotoOpening(page, world.tender_reference);
		await expectScreen(page, "open-bids");
		await expectNextStep(page, "your_turn", "Retry opening");
		await expect(page.locator('[data-testid="bop-problem-status"]')).toContainText("Recovered");
		await page.locator('[data-testid="bop-retry"]').click();
		await expectScreen(page, "open-bids");
		await expectNextStep(page, "your_turn", "Record what was read aloud");
		// a refresh keeps the position, and the bid is not read out twice
		await page.reload();
		await expectScreen(page, "open-bids");
		await expectNextStep(page, "your_turn", "Record what was read aloud");
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("OF-F02: cannot recover — the Accounting Officer is sent to the exact Tender decision and cancels on a verified ground", async ({ page }) => {
		const errors = collectConsoleErrors(page);
		verifyGrounds("");
		const world = openingWorld("unresolved");

		// the chair waits; nothing to retry, resume or skip
		await login(page, CHAIR, PASSWORD);
		await gotoOpening(page, world.tender_reference);
		await expectScreen(page, "open-bids");
		await expectNextStep(page, "waiting", /to resolve the paused opening$/);
		await expect(page.locator('[data-testid="bop-problem-status"]')).toHaveText("Could not be recovered");
		await expect(page.locator('[data-testid="bop-not-recovered"]')).toHaveText("Opening could not be recovered. The Accounting Officer must review the next step.");
		await expect(page.locator('[data-testid="bop-retry"], [data-testid="bop-resume"], [data-testid="bop-open-next"]')).toHaveCount(0);
		// the chair can read the problem but support's finding form is not theirs
		await page.locator("button", { hasText: "View problem details" }).first().click();
		await expect(page.locator('[data-testid^="bop-finding-form-"]')).toHaveCount(0);

		// the Accounting Officer: the decision is blocked until a ground is verified, and the screen says so
		await login(page, AO, PASSWORD);
		await gotoOpening(page, world.tender_reference);
		await expectScreen(page, "open-bids");
		await expectNextStep(page, "your_turn_blocked", "A tender decision is needed");
		await expect(page.locator('[data-testid="bop-decision-message"]')).toHaveText("Opening could not be recovered. The Accounting Officer must review the next step.");
		await page.locator('[data-testid="bop-open-tender-decision"]').click();
		await page.waitForURL(new RegExp(`/app/tenders/${world.tender_reference}/cancel/[^/]+$`));
		const decisionUrl = page.url();
		await expectTenderReady(page, "cancel");
		const decision = page.locator('[data-testid="tnd-postclose"]');
		await expect(decision).toHaveAttribute("data-allowed", "false");
		await expect(page.locator('[data-testid="tnd-blocker"]')).toHaveAttribute("data-code", "TND_CANCEL_GROUND_UNVERIFIED");
		await expect(page.locator('[data-testid="tnd-cancel-open-dialog"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="tnd-opening-context"]')).toContainText("Opening could not be recovered");

		// a verified ground exists now; a refresh keeps the item in the path and the screen re-reads the verdict
		verifyGrounds(GROUND);
		await page.reload();
		expect(page.url()).toBe(decisionUrl);
		await expectTenderReady(page, "cancel");
		await expect(decision).toHaveAttribute("data-allowed", "true");
		await page.goBack();
		await expectScreen(page, "open-bids");
		await expectNextStep(page, "your_turn", "Decide how to proceed with the paused opening");
		await page.goForward();
		await expectTenderReady(page, "cancel");
		await page.locator('[data-testid="tnd-cancel-ground"]').selectOption(GROUND);
		await page.locator('[data-testid="tnd-cancel-reason"]').fill(REASON);
		await page.locator('[data-testid="tnd-cancel-open-dialog"]').click();
		await page.locator('[data-testid="tnd-cancel-dialog-confirm"]').click();
		await expectTenderSettled(page);
		await expect(page.locator('[data-testid="tnd-record-badge"]')).toHaveText("Cancelled");
		await expect(page.locator('[data-testid="tnd-cancelled-from"]')).toHaveText("Submission period ended");
		await page.reload();
		await expectTenderReady(page, "cancel");
		await expect(page.locator('[data-testid="tnd-delivery-bid-opening"]')).toHaveAttribute("data-status", "Delivered");

		// the opening now says it ended; what was recorded stays and nothing can be done to it
		await gotoOpening(page, world.tender_reference);
		await expectScreen(page, "open-bids");
		await expect(page.locator('[data-testid="bop-cancelled"] h2')).toHaveText("This tender was cancelled. Opening ended.");
		await expect(page.locator('[data-testid="bop-cancelled"]')).toContainText("There is no opening record to sign");
		await expect(page.locator("button.btn-primary")).toHaveCount(0);
		await login(page, CHAIR, PASSWORD);
		await gotoOpening(page, world.tender_reference);
		await expectScreen(page, "open-bids");
		await expect(page.locator('[data-testid="bop-cancelled"] h2')).toHaveText("This tender was cancelled. Opening ended.");
		await expect(page.locator("button.btn-primary")).toHaveCount(0);
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("OF-F03: not held — the Accounting Officer's decision ends the record with the cancellation", async ({ page }) => {
		const errors = tenderConsoleErrors(page);
		verifyGrounds(GROUND);
		const world = openingWorld("not-held");
		await login(page, AO, PASSWORD);
		await gotoOpening(page, world.tender_reference);
		await expectScreen(page, "open-bids");
		await expect(page.locator('[data-testid="bop-not-held"]')).toBeVisible();
		await expect(page.locator('[data-testid="bop-open-tender-decision"]')).toBeVisible();
		await page.locator('[data-testid="bop-open-tender-decision"]').click();
		await page.waitForURL(new RegExp(`/app/tenders/${world.tender_reference}/cancel`));
		await expectTenderReady(page, "cancel");
		await page.locator('[data-testid="tnd-cancel-ground"]').selectOption(GROUND);
		await page.locator('[data-testid="tnd-cancel-reason"]').fill(REASON);
		await page.locator('[data-testid="tnd-cancel-open-dialog"]').click();
		await page.locator('[data-testid="tnd-cancel-dialog-confirm"]').click();
		await expectTenderSettled(page);
		await expect(page.locator('[data-testid="tnd-record-badge"]')).toHaveText("Cancelled");

		await gotoOpening(page, world.tender_reference);
		await expectScreen(page, "open-bids");
		await expect(page.locator('[data-testid="bop-cancelled"] h2')).toHaveText("This tender was cancelled. Opening ended.");
		await expect(page.locator('[data-testid="bop-cancelled-outcome"]')).toHaveText("Opening not held");
		await expect(page.locator("button.btn-primary")).toHaveCount(0);
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("access: neither the Auditor nor the Accounting Officer is given the finding form", async ({ page }) => {
		verifyGrounds("");
		const world = openingWorld("unresolved");
		await login(page, AUDITOR, PASSWORD);
		await gotoOpening(page, world.tender_reference);
		await expectScreen(page, "open-bids");
		await expect(page.locator('[data-testid^="bop-finding-form-"]')).toHaveCount(0);
		await login(page, AO, PASSWORD);
		await gotoOpening(page, world.tender_reference);
		await expectScreen(page, "open-bids");
		await expect(page.locator('[data-testid^="bop-finding-form-"]')).toHaveCount(0);
	});
});
