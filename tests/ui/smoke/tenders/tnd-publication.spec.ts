import path from "node:path";

import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { AO, HOPF, PASSWORD, collectConsoleErrors, expectGuidance, expectReady, expectSettled, gotoTenders, resetFixture, restoreSite } from "./helpers";

/** TPR-CHG-001 v0.12 slice C — TPR-DES-08 Publication confirmation (§10.9, §10.17). */

const EVIDENCE = path.resolve(__dirname, "fixtures/evidence.png");

test.describe.configure({ mode: "serial", timeout: 300_000 });

/** Frappe's own uploader: My Device → file chooser → Upload. */
async function uploadEvidence(page: import("@playwright/test").Page, chooseSelector: string) {
	const [chooser] = await Promise.all([page.waitForEvent("filechooser"), page.locator(chooseSelector).click().then(() => page.locator(".modal.show").getByRole("button", { name: "My Device" }).click())]);
	await chooser.setFiles(EVIDENCE);
	await page.locator(".modal.show .btn-modal-primary, .modal.show button.btn-primary").click();
	await expect(page.locator(".modal.show")).toHaveCount(0);
}

test.describe("TPR-DES-08 Publication confirmation", () => {
	test.afterAll(() => restoreSite());

	test("the HoPF confirms a channel with evidence; dialog checks are inline; View confirmation", async ({ page }) => {
		const state = resetFixture("reset_publication_fixture", { confirmed: 2 });
		const errors = collectConsoleErrors(page);
		await login(page, HOPF, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}/publication`);
		await expectReady(page, "publication");
		// the guidance states the count once; no separate progress notice or bar
		await expectGuidance(page, "DES-08");
		await expect(page.locator('[data-kt="next-step"]')).toContainText("2 of 4 channels are confirmed.");
		await expect(page.locator('[data-testid="tnd-publication-progress"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="tnd-channel-STATE_PORTAL"] .kt-status')).toHaveText("Confirmed");
		await expect(page.locator('[data-testid="tnd-confirm-channel"]')).toHaveCount(2);

		await page.locator('[data-testid="tnd-channel-STATE_PORTAL"] [data-testid="tnd-view-confirmation"]').click();
		await expect(page.locator('[data-testid="tnd-confirmation-view"]')).toContainText("REF-STATE_PORTAL");
		await page.locator('[data-testid="tnd-cv-close"]').click();

		await page.locator('[data-testid="tnd-channel-NOTICE_BOARD"] [data-testid="tnd-confirm-channel"]').click();
		const dialog = page.locator('[data-testid="tnd-channel-dialog"]');
		await expect(dialog.locator(".kt-dialog-title")).toHaveText("Confirm notice-board publication");
		await expect(dialog.locator('[data-testid="tnd-ch-url"]')).toHaveCount(0);
		await dialog.locator('[data-testid="tnd-ch-confirm"]').click();
		await expect(dialog.locator('[data-testid="tnd-ch-error-available_at"]')).toBeVisible();
		await expect(dialog.locator('[data-testid="tnd-ch-error-evidence_file"]')).toHaveText("Attach the publication evidence file.");
		await expect(page.locator(".modal.show")).toHaveCount(0);

		await dialog.locator('[data-testid="tnd-ch-available"]').fill("2027-05-15T08:15");
		await dialog.locator('[data-testid="tnd-ch-reference"]').fill("NB-MOH-2027-033");
		await uploadEvidence(page, '[data-testid="tnd-ch-choose-file"]');
		await expect(dialog.locator('[data-testid="tnd-ch-filename"]')).toHaveText("evidence.png");
		await dialog.locator("label.kt-checkbox").click();
		await dialog.locator('[data-testid="tnd-ch-confirm"]').click();
		await expectSettled(page);
		await expect(dialog).toHaveCount(0);
		await expect(page.locator('[data-kt="next-step"]')).toContainText("3 of 4 channels are confirmed.");
		await expect(page.locator('[data-testid="tnd-channel-NOTICE_BOARD"] .kt-status')).toHaveText("Confirmed");
		await page.reload();
		await expectReady(page, "publication");
		await expect(page.locator('[data-testid="tnd-channel-NOTICE_BOARD"] .kt-status')).toHaveText("Confirmed");
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	// The browser's uploader accepts only PDF and image files, so a rejected
	// file cannot be sent from the page; the refusal is replayed here with the
	// exact detail the server returns (its own shape is pinned by
	// test_publication), and the real conflict path is driven below.
	const INVALID = "The selected file cannot be used as publication evidence. Choose an allowed document or image file.";
	const BLOCKED = {
		kind: "your_turn_blocked", label: "Your turn, blocked", headline: "Two national newspapers evidence could not be accepted.", sentence: "", stage: "PUBLICATION", holder: null, since: null, fixes: [], primary_action: "",
		blockers: [{ reason_code: "TND_PUBLICATION_EVIDENCE_INVALID", headline: "Two national newspapers evidence could not be accepted.", facts: [], fixes: [
			{ label: "Choose evidence file", fix_id: "choose_evidence_file", kind: "focus", target: "evidence_file", primary: true },
			{ label: "Confirm publication", fix_id: "confirm_publication_channel", kind: "command" },
		] }],
	};

	const STAGES = [["PREPARE", "Prepare Tender", "done"], ["HOPF_APPROVAL", "HOPF approval", "done"], ["AO_AUTHORISATION", "AO publication authorisation", "done"], ["PUBLICATION", "Confirm publication", "blocked"], ["OPEN_MANAGEMENT", "Manage open Tender", "not_started"]];
	const JOURNEY_BLOCKED = {
		stages: STAGES.map(([code, label, marker]) => ({ code, label, marker, marker_label: { done: "Done", blocked: "Blocked", not_started: "Not started" }[marker], holder: marker === "blocked" ? "Playwright HOPF" : "" })),
		current: "PUBLICATION", reduced: false, reduced_style: "position", reduced_parts: { prefix: "", label: "Confirm publication (blocked)", suffix: " · 4 of 5 · Playwright HOPF" }, upstream: null, downstream: null,
	};

	test("invalid evidence keeps the dialog, the entered values and the inline error; the guidance offers the fixes", async ({ page }) => {
		const state = resetFixture("reset_publication_fixture", { confirmed: 2 });
		await login(page, HOPF, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}/publication`);
		await expectReady(page, "publication");
		await page.route("**/api/method/kentender_procurement.tenders.api.confirm_publication_channel", async (route) => {
			await route.fulfill({ status: 417, contentType: "application/json", body: JSON.stringify({ exc_type: "TendersError", kt_error_code: "TND_PUBLICATION_EVIDENCE_INVALID", kt_error_message: INVALID, kt_error_detail: { channel: "NATIONAL_NEWSPAPERS", fields: { evidence_file: INVALID }, next_step: BLOCKED, guidance: { next_step: BLOCKED, journey: JOURNEY_BLOCKED } } }) });
			await page.unroute("**/api/method/kentender_procurement.tenders.api.confirm_publication_channel");
		});
		await page.locator('[data-testid="tnd-channel-NATIONAL_NEWSPAPERS"] [data-testid="tnd-confirm-channel"]').click();
		const dialog = page.locator('[data-testid="tnd-channel-dialog"]');
		await expect(dialog.locator(".kt-dialog-title")).toHaveText("Confirm newspaper publication — Two national newspapers");
		await dialog.locator('[data-testid="tnd-ch-available"]').fill("2027-05-15T08:20");
		await dialog.locator('[data-testid="tnd-ch-reference"]').fill("NP-MOH-2027-033");
		await uploadEvidence(page, '[data-testid="tnd-ch-choose-file"]');
		await dialog.locator("label.kt-checkbox").click();
		await dialog.locator('[data-testid="tnd-ch-confirm"]').click();
		await expectSettled(page);
		await expect(dialog.locator('[data-testid="tnd-ch-error-evidence_file"]')).toHaveText(INVALID);
		await expect(dialog.locator('[data-testid="tnd-ch-reference"]')).toHaveValue("NP-MOH-2027-033");
		await expect(page.locator(".modal.show")).toHaveCount(0);
		await dialog.getByRole("button", { name: "Cancel" }).click();
		await expectGuidance(page, "DES-08-INVALID");
		await expect(page.locator('[data-testid="tnd-channel-NATIONAL_NEWSPAPERS"] .kt-status')).toHaveText("Awaiting confirmation");
		// Choose evidence file reopens the same channel with its values kept, on the file control
		await page.locator('[data-kt="next-step"] button', { hasText: "Choose evidence file" }).click();
		await expect(dialog.locator('[data-testid="tnd-ch-reference"]')).toHaveValue("NP-MOH-2027-033");
		await expect(dialog.locator('[data-testid="tnd-ch-choose-file"]')).toBeFocused();
	});

	test("a conflicting confirmation draws the inline already-confirmed row and changes nothing", async ({ page }) => {
		const state = resetFixture("reset_publication_fixture", { confirmed: 2 });
		await login(page, HOPF, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}/publication`);
		await expectReady(page, "publication");
		// the request reaches the server for the already-confirmed State Portal
		// (a stale second session): the server refuses and records nothing
		await page.route("**/api/method/kentender_procurement.tenders.api.confirm_publication_channel", async (route) => {
			const body = route.request().postData() || "";
			await route.continue({ postData: body.replace(/channel=NATIONAL_NEWSPAPERS/, "channel=STATE_PORTAL") });
			await page.unroute("**/api/method/kentender_procurement.tenders.api.confirm_publication_channel");
		});
		await page.locator('[data-testid="tnd-channel-NATIONAL_NEWSPAPERS"] [data-testid="tnd-confirm-channel"]').click();
		const dialog = page.locator('[data-testid="tnd-channel-dialog"]');
		await dialog.locator('[data-testid="tnd-ch-available"]').fill("2027-05-15T09:30");
		await dialog.locator('[data-testid="tnd-ch-reference"]').fill("NP-MOH-2027-033");
		await uploadEvidence(page, '[data-testid="tnd-ch-choose-file"]');
		await dialog.locator("label.kt-checkbox").click();
		await dialog.locator('[data-testid="tnd-ch-confirm"]').click();
		await expectSettled(page);
		await expect(dialog).toHaveCount(0);
		await expectGuidance(page, "DES-08-CONFLICT");
		await expect(page.locator('[data-testid="tnd-already-confirmed"]')).toContainText("This channel is already confirmed.");
		await expect(page.locator('[data-testid="tnd-channel-NATIONAL_NEWSPAPERS"] .kt-status')).toHaveText("Awaiting confirmation");
		await expect(page.locator(".modal.show")).toHaveCount(0);
	});

	test("the AO may withdraw only before any confirmation; the Tender returns to Approved", async ({ page }) => {
		const state = resetFixture("reset_publication_fixture", { confirmed: 0 });
		await login(page, AO, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}/publication`);
		await expectReady(page, "publication");
		await page.locator('[data-testid="tnd-withdraw-authorisation"]').click();
		await page.locator('[data-testid="tnd-withdraw-dialog-reason"]').fill("The notice period was set before the corrected budget figure was confirmed.");
		await page.locator('[data-testid="tnd-withdraw-dialog-confirm"]').click();
		await expectReady(page, "authorisation");
		await expectGuidance(page, "DES-07");
	});
});
