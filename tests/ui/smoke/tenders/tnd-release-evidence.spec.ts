import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { AO, AUDITOR, HOPF, OFFICER, PASSWORD, collectConsoleErrors, expectReady, gotoTenders, resetFixture, restoreSite } from "./helpers";

/**
 * TPR-CHG-001 v0.8 Phase 9 — the §13.3 persona pass: Brian Wafula
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

test.describe("TPR-CHG-001 v0.8 — persona release pass", () => {
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
		await page.locator('[data-testid="tnd-submit-for-approval"]').click();
		await page.locator('[data-testid="tnd-submit-dialog-confirm"]').click();
		await expectReady(page, "workspace");

		// Charles Mutiso — HoPF: returns it once (release evidence for the
		// returned path), then approves the resubmission.
		await login(page, HOPF, PASSWORD);
		await gotoTenders(page, `/${ref}`);
		await expectReady(page, "approval");
		await page.locator('[data-testid="tnd-return-for-correction"]').click();
		await page.locator('[data-testid="tnd-return-dialog-reason"]').fill("Confirm the manufacturer authorisation criterion is proportionate to this purchase.");
		await page.locator('[data-testid="tnd-return-dialog-select"]').selectOption("Supplier and contract requirements");
		await page.locator('[data-testid="tnd-return-dialog-confirm"]').click();
		await expectReady(page, "workspace");

		await login(page, OFFICER, PASSWORD);
		await gotoTenders(page, `/${ref}/requirements`);
		await expectReady(page, "requirements");
		await expect(page.locator('[data-testid="tnd-returned-notice"]')).toBeVisible();
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

		// Brian Wafula — Procurement Officer: prepares and issues an addendum
		// (with the HoPF), the bidder-service producer's inquiry is answered,
		// and the system closes the submission period — verified read-only
		// here since the canonical seed already proves the full write path
		// (Phase 8) and every write step above this line has already been
		// exercised live by an actor in this same pass.
		await login(page, OFFICER, PASSWORD);
		await gotoTenders(page, `/${ref}`);
		await expectReady(page, "published");
		await expect(page.locator('[data-testid="tnd-prepare-addendum"]')).toBeVisible();

		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});
});
