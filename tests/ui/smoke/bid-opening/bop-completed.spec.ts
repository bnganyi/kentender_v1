import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { AUDITOR, CHAIR, PASSWORD, expectNextStep, expectScreen, gotoOpening, openingWorld, restoreBopWorld } from "./bopWorld";

/** BOP-CHG-001 v0.10 §10.6 — boards r6, h1–h5 (slice 8.7). */

test.describe.configure({ mode: "serial", timeout: 300_000 });

test.describe("BOP-DES-05 Completed record", () => {
	test.afterAll(() => restoreBopWorld());

	test("recorder: correct the completed record with one of the four kinds (h4 → h5)", async ({ page }) => {
		const world = openingWorld("complete");
		await login(page, CHAIR, PASSWORD);
		await gotoOpening(page, world.tender_reference);
		await expectScreen(page, "completed");
		await expectNextStep(page, "done", /after the last signature\.$/);
		await page.locator('[data-testid="bop-correct-open"]').click();
		await expect(page).toHaveURL(new RegExp(`/(app|desk)/tenders/${world.tender_reference}/opening/correct$`));
		await expectScreen(page, "completed");
		await expectNextStep(page, "your_turn", "Correct opening record");
		await expect(page.locator(".kt-radio")).toHaveText(["Attendance note", "Procedural note", "Typographical error in a note", "Observer name or organisation"]);
		await page.locator('[data-testid="bop-correct-info"]').fill("Jane Wanjiku left at 11:03 EAT");
		await page.locator('[data-testid="bop-correct-reason"]').fill("Add the departure noted during the opening");
		await page.locator('[data-testid="bop-correct-add"]').click();
		await expect(page).toHaveURL(new RegExp(`/(app|desk)/tenders/${world.tender_reference}/opening$`));
		await expectScreen(page, "completed");
		await expectNextStep(page, "done", /^Correction added at /);
		await expect(page.locator('[data-testid="bop-corrections"] tbody tr')).toHaveCount(1);
		await page.goBack();
		await expectScreen(page, "completed");
	});

	test("h1: the Auditor reads it all, with no guidance and no action; h3: the administrator sees technical status only", async ({ page }) => {
		const world = openingWorld("complete");
		await login(page, AUDITOR, PASSWORD);
		await gotoOpening(page, world.tender_reference);
		await expectScreen(page, "completed");
		await expect(page.locator('[data-testid="bop-guidance"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="bop-summary"]')).toContainText("Bids opened");
		await expect(page.locator(".kt-page button.kt-btn-primary")).toHaveCount(0);
		await login(page, process.env.UI_ADMIN_USER || "Administrator", process.env.UI_ADMIN_PASSWORD || "admin");
		await gotoOpening(page, world.tender_reference);
		await expectScreen(page, "completed");
		await expect(page.locator('[data-testid="bop-technical"]')).toContainText("Bids, the register and the opening record are not shown to administrators.");
		await expect(page.locator('[data-testid="bop-register"]')).toHaveCount(0);
	});
});
