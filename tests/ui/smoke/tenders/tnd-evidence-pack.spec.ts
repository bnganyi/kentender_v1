import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { AO, HOPF, OFFICER, PASSWORD, expectReady, gotoTenders, resetFixture, restoreSite } from "./helpers";

/**
 * TPR-CHG-001 v0.8 Phase 9 — one 1440×1024 PNG per board into
 * evidence/v0_8/, the primary variant each Playwright fixture builds.
 * Not every named artboard variant (segregation, invalid evidence, …) —
 * those are already proven structurally by tenders-fidelity.spec.ts and
 * behaviourally by the twelve slice specs; this pack is the visual record
 * of each board's main state, matching the plan's own PNG requirement.
 */

test.describe.configure({ mode: "serial", timeout: 600_000 });

test.describe("TPR-CHG-001 v0.8 — evidence pack", () => {
	test.afterAll(() => restoreSite());

	async function shot(page: any, name: string) {
		await page.waitForTimeout(150);
		await page.screenshot({ path: `evidence/v0_8/${name}.png` });
	}

	test("captures every board's primary state", async ({ page }) => {
		await page.setViewportSize({ width: 1440, height: 1024 });

		let state = resetFixture<{ handoff: string; tender_reference?: string }>("reset_start_fixture");
		await login(page, OFFICER, PASSWORD);
		await gotoTenders(page);
		await expectReady(page, "workspace");
		await shot(page, "01-TPR-DES-01-workspace");

		await gotoTenders(page, `/new/${state.handoff}`);
		await expectReady(page, "start");
		await shot(page, "02-TPR-DES-02-start-dialog");

		state = resetFixture("reset_draft_fixture");
		await gotoTenders(page, `/${state.tender_reference}/details`);
		await expectReady(page, "details");
		await shot(page, "03-TPR-DES-03-details");

		state = resetFixture("reset_draft_complete_fixture");
		await gotoTenders(page, `/${state.tender_reference}/requirements`);
		await expectReady(page, "requirements");
		await shot(page, "04-TPR-DES-04-requirements");

		await gotoTenders(page, `/${state.tender_reference}/review`);
		await expectReady(page, "review");
		await shot(page, "05-TPR-DES-05-review");

		state = resetFixture("reset_awaiting_hopf_fixture");
		await login(page, HOPF, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}`);
		await expectReady(page, "approval");
		await shot(page, "06-TPR-DES-06-hopf-approval");

		state = resetFixture("reset_awaiting_ao_fixture");
		await login(page, AO, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}`);
		await expectReady(page, "authorisation");
		await shot(page, "07-TPR-DES-07-ao-authorisation");

		state = resetFixture("reset_publication_fixture", { confirmed: 2 });
		await login(page, HOPF, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}/publication`);
		await expectReady(page, "publication");
		await shot(page, "08-TPR-DES-08-publication-confirmation");

		state = resetFixture("reset_published_fixture", { with_inquiry: true });
		await gotoTenders(page, `/${state.tender_reference}`);
		await expectReady(page, "published");
		await shot(page, "09-TPR-DES-09-published");

		state = resetFixture("reset_addendum_draft_fixture");
		await login(page, OFFICER, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}/addenda/${state.addendum}`);
		await expectReady(page, "addendum");
		await shot(page, "10-TPR-DES-10-prepare-addendum");

		state = resetFixture("reset_inquiry_fixture");
		await gotoTenders(page, `/${state.tender_reference}/inquiries/${state.inquiry}`);
		await expectReady(page, "inquiry");
		await shot(page, "11-TPR-DES-11-respond-to-inquiry");

		state = resetFixture("reset_cancel_fixture", { recommended: true });
		await login(page, AO, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}/cancel`);
		await expectReady(page, "cancel");
		await shot(page, "12-TPR-DES-12-cancel-tender");

		state = resetFixture("reset_returned_fixture");
		await login(page, OFFICER, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}/requirements`);
		await expectReady(page, "requirements");
		await shot(page, "13-TPR-DES-13-returned");

		await login(page, AO, PASSWORD);
		await gotoTenders(page, "/nonexistent-tender-000");
		await expectReady(page, "not-found");
		await shot(page, "14-TPR-DES-14-common-states-not-found");

		state = resetFixture("reset_published_fixture", { with_inquiry: true });
		await login(page, HOPF, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}/history`);
		await expectReady(page, "history");
		await shot(page, "15-history-route");

		expect(true).toBe(true);
	});
});
