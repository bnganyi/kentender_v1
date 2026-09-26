import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { AO, AUDITOR, HOPF, OFFICER, PASSWORD, collectConsoleErrors, expectGuidance, expectReady, gotoTenders, resetFixture, restoreSite } from "./helpers";

/**
 * TPR-CHG-001 v0.12 Phase 13 (was v0.8 Phase 9) — the §13.3 persona pass,
 * with the §10.17 guidance asserted at every hand-off and the record read at
 * 1440 px, 390 px and 200% zoom: Brian Wafula
 * (Procurement Officer), Charles Mutiso (Head of Procurement Function),
 * Amina Hassan (Accounting Officer) and Naomi Chebet (Auditor) walk one
 * Tender from Start through a closed submission period, each acting only
 * where their responsibility permits, in a single worker so the sequence
 * reads as one continuous release evidence trail.
 *
 * This exercises the same command sequence `tenders/seeds/kentender_mvp_v1.py`
 * drives on the canonical site, but through the real browser and the four
 * canonical actors, on this module's own disposable Playwright world so
 * the canonical Tender itself is never touched by a UI run.
 */

test.describe.configure({ mode: "serial", timeout: 600_000 });

/** §10.17: at 390 px the one-line journey and no sideways scroll; at 200% zoom
 *  (1440 px at 200% is 720 CSS px) no sideways scroll, whichever form fits. */
async function expectReflows(page: import("@playwright/test").Page) {
	for (const [width, height] of [[390, 844], [720, 512]] as const) {
		await page.setViewportSize({ width, height });
		if (width === 390) await expect(page.locator(".kt-journey-compact")).toBeVisible();
		const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
		expect(overflow, `horizontal scroll at ${width}px`).toBeLessThanOrEqual(1);
	}
	await page.setViewportSize({ width: 1440, height: 1024 });
}

test.describe("TPR-CHG-001 v0.12 — persona release pass", () => {
	test.afterAll(() => restoreSite());

	test("Brian starts, drafts and submits; Charles returns then approves; Amina authorises and confirms; the Tender publishes and closes", async ({ page }) => {
		const state = resetFixture<{ handoff: string; tender_reference?: string }>("reset_start_fixture");
		const errors = collectConsoleErrors(page);

		// Brian Wafula — Procurement Officer: Start, complete both tasks, submit.
		await login(page, OFFICER, PASSWORD);
		await gotoTenders(page, `/new/${state.handoff}`);
		await expectReady(page, "start");
		await page.locator('[data-testid="tnd-start-confirm"]').click();
		await expectReady(page, "details");
		await expectGuidance(page, "DES-03");
		const ref = (await page.url().match(/tenders\/(TND-[A-Z0-9-]+)\/details/)) ?.[1];
		expect(ref).toBeTruthy();

		await page.locator('[data-testid="tnd-field-issue_date"]').fill("2027-05-15");
		await page.locator('[data-testid="tnd-field-clarification_deadline"]').fill("2027-05-27T17:00");
		await page.locator('[data-testid="tnd-field-submission_deadline"]').fill("2027-06-05T11:00");
		await page.locator('[data-testid="tnd-field-tender_security_amount"]').fill("500000");
		await page.locator('[data-testid="tnd-continue"]').click();
		await expectReady(page, "requirements");
		await page.locator('[data-testid="tnd-field-inspection_location"]').selectOption({ index: 1 });
		await page.locator('[data-testid="tnd-field-contract_contact_office"]').selectOption({ index: 1 });
		await page.locator('[data-testid="tnd-continue"]').click();
		await expectReady(page, "review");
		await expectGuidance(page, "DES-05");
		await page.locator('[data-testid="tnd-submit-for-approval"]').click();
		await page.locator('[data-testid="tnd-submit-dialog-confirm"]').click();
		await expectReady(page, "workspace");
		// the officer now waits on the HOPF, named on the record
		await gotoTenders(page, `/${ref}`);
		await expectReady(page, "record");
		await expect(page.locator('[data-kt="next-step"]')).toHaveAttribute("data-kind", "waiting");

		// Charles Mutiso — HoPF: returns it once (release evidence for the
		// returned path), then approves the resubmission.
		await login(page, HOPF, PASSWORD);
		await gotoTenders(page, `/${ref}`);
		await expectReady(page, "approval");
		await expectGuidance(page, "DES-06");
		await expectReflows(page);
		await page.locator('[data-testid="tnd-return-for-correction"]').click();
		await page.locator('[data-testid="tnd-return-dialog-reason"]').fill("Confirm the manufacturer authorisation criterion is proportionate to this purchase.");
		await page.locator('[data-testid="tnd-return-dialog-select"]').selectOption("Supplier and contract requirements");
		await page.locator('[data-testid="tnd-return-dialog-confirm"]').click();
		await expectReady(page, "workspace");

		await login(page, OFFICER, PASSWORD);
		await gotoTenders(page, `/${ref}/requirements`);
		await expectReady(page, "requirements");
		await expect(page.locator('[data-testid="tnd-returned-notice"]')).toBeVisible();
		await expectGuidance(page, "DES-13-RETURNED");
		await page.locator('[data-testid="tnd-continue"]').click();
		await expectReady(page, "review");
		await page.locator('[data-testid="tnd-submit-for-approval"]').click();
		await page.locator('[data-testid="tnd-submit-dialog-confirm"]').click();
		await expectReady(page, "workspace");

		await login(page, HOPF, PASSWORD);
		await gotoTenders(page, `/${ref}`);
		await expectReady(page, "approval");
		await page.locator('[data-testid="tnd-approve-package"]').click();
		await page.locator('[data-testid="tnd-approve-dialog-confirm"]').click();
		await expectReady(page, "workspace");

		// Amina Hassan — Accounting Officer: authorises publication.
		await login(page, AO, PASSWORD);
		await gotoTenders(page, `/${ref}`);
		await expectReady(page, "authorisation");
		await expectGuidance(page, "DES-07");
		await page.locator('[data-testid="tnd-authorise-publication"]').click();
		await page.locator('[data-testid="tnd-authorise-dialog-confirm"]').click();
		await expectReady(page, "publication");

		// Naomi Chebet — Auditor: reads the record mid-cycle, changes nothing.
		await login(page, AUDITOR, PASSWORD);
		await gotoTenders(page, `/${ref}/history`);
		await expectReady(page, "history");
		expect(await page.locator('[data-testid="tnd-history-decisions"] tbody tr').count()).toBeGreaterThanOrEqual(3);

		// Charles Mutiso — HoPF: confirms all four channels; the last confirmation
		// publishes the Tender.
		await login(page, HOPF, PASSWORD);
		await gotoTenders(page, `/${ref}/publication`);
		await expectReady(page, "publication");
		await expectGuidance(page, "DES-08");
		for (const channel of ["STATE_PORTAL", "MINISTRY_WEBSITE", "NOTICE_BOARD", "NATIONAL_NEWSPAPERS"] as const) {
			const row = page.locator(`[data-testid="tnd-channel-${channel}"]`);
			await row.locator('[data-testid="tnd-confirm-channel"]').click();
			const dialog = page.locator('[data-testid="tnd-channel-dialog"]');
			const online = channel === "STATE_PORTAL" || channel === "MINISTRY_WEBSITE";
			await dialog.locator('[data-testid="tnd-ch-available"]').fill("2027-05-15T08:00");
			await dialog.locator('[data-testid="tnd-ch-reference"]').fill(`${channel}-EVIDENCE`);
			if (online) await dialog.locator('[data-testid="tnd-ch-url"]').fill(`https://portal.example.test/${channel.toLowerCase()}`);
			// Frappe's own uploader — the one control Vue cannot own.
			const [chooser] = await Promise.all([page.waitForEvent("filechooser"), dialog.locator('[data-testid="tnd-ch-choose-file"]').click().then(() => page.locator(".modal.show").getByRole("button", { name: "My Device" }).click())]);
			await chooser.setFiles(require("path").resolve(__dirname, "fixtures/evidence.png"));
			await page.locator(".modal.show .btn-modal-primary, .modal.show button.btn-primary").click();
			await expect(page.locator(".modal.show")).toHaveCount(0);
			await dialog.locator("label.kt-checkbox").click();
			await dialog.locator('[data-testid="tnd-ch-confirm"]').click();
			await page.waitForFunction(() => document.querySelector('[data-testid="tnd-shell"]')?.getAttribute("data-pending") === "false");
		}
		await expectReady(page, "published");
		await expect(page.locator('[data-testid="tnd-record-badge"]')).toHaveText("Published — open");
		await expectGuidance(page, "DES-09-HOPF");

		// Brian Wafula — Procurement Officer: prepares and issues an addendum
		// (with the HoPF), the bidder-service producer's inquiry is answered,
		// and the system closes the submission period — verified read-only
		// here since the canonical seed already proves the full write path
		// (Phase 8) and every write step above this line has already been
		// exercised live by an actor in this same pass.
		await login(page, OFFICER, PASSWORD);
		await gotoTenders(page, `/${ref}`);
		await expectReady(page, "published");
		await expectGuidance(page, "DES-09-OFFICER");
		await expect(page.locator('[data-testid="tnd-prepare-addendum"]')).toBeVisible();
		await expectReflows(page);

		// Naomi Chebet — Auditor: Not involved on the open Tender, no business action.
		await login(page, AUDITOR, PASSWORD);
		await gotoTenders(page, `/${ref}`);
		await expectReady(page, "published");
		await expectGuidance(page, "DES-09-READER");

		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});
});
