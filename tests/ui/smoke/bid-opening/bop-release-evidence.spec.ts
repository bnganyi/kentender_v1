import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { collectPortalConsoleErrors, waitForPortal } from "../../helpers/portal";
import { collectConsoleErrors, expectNextStep, expectScreen, gotoOpening } from "./bopWorld";

/**
 * BOP-CHG-001 v0.10 plan Phase 11 (BOP10-1103, PRC-INT-01 browser part): the
 * canonical opening (`make seed-canonical THROUGH=bid_opening`) read in a
 * browser by each seeded person, read-only. Bid Submission closed the
 * canonical Tender at 11:00; Bid Opening opened it with the appointed
 * members, David Ouma's attendance and the final signed record.
 */

const REFERENCE = process.env.UI_BOP_CANONICAL_TENDER || "TND-MOH-2027-002";
const PASSWORD = process.env.UI_SEED_PASSWORD || "Test@123";
const person = (local: string) => `${local}@moh.example.test`;

test.describe.configure({ mode: "serial", timeout: 240_000 });

test.describe("BOP release evidence — the canonical opening, person by person", () => {
	test("the committee: Charles, Brian and Beatrice see the completed record; only the recorder may correct it", async ({ page }) => {
		const errors = collectConsoleErrors(page);
		for (const local of ["charles.mutiso", "brian.wafula", "beatrice.kamau"]) {
			await login(page, person(local), PASSWORD);
			await gotoOpening(page, REFERENCE);
			await expectScreen(page, "completed");
			await expectNextStep(page, "done", /after the last signature\.$/);
			await expect(page.locator('[data-testid="bop-signatures"] tbody tr')).toHaveCount(3);
			await expect(page.locator('[data-testid="bop-signatures"] .kt-status')).toHaveText(["Signed", "Signed", "Signed"]);
			await expect(page.locator('[data-testid="bop-register"] tbody tr')).toHaveCount(1);
			await expect(page.locator('[data-testid="bop-correct-open"]')).toHaveCount(local === "charles.mutiso" ? 1 : 0);
		}
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("Amina Hassan and Naomi Chebet read it all; nothing to do", async ({ page }) => {
		for (const local of ["amina.hassan", "naomi.chebet"]) {
			await login(page, person(local), PASSWORD);
			await gotoOpening(page, REFERENCE);
			await expectScreen(page, "completed");
			await expect(page.locator('[data-testid="bop-summary"]')).toContainText("Bids opened");
			await expect(page.locator('[data-testid="bop-summary"]')).toContainText("EV-IN-");
			await expect(page.locator('[data-testid="bop-session"]')).toContainText("Started the opening");
			await expect(page.locator('[data-testid="bop-requests"] tbody tr')).toHaveCount(1);
			await expect(page.locator(".kt-page button.kt-btn-primary")).toHaveCount(0);
		}
	});

	test("the administrator sees technical status only", async ({ page }) => {
		await login(page, process.env.UI_ADMIN_USER || "Administrator", process.env.UI_ADMIN_PASSWORD || "admin");
		await gotoOpening(page, REFERENCE);
		await expectScreen(page, "completed");
		await expect(page.locator('[data-testid="bop-technical"]')).toBeVisible();
		await expect(page.locator('[data-testid="bop-register"], [data-testid="bop-signatures"]')).toHaveCount(0);
	});

	test("the public page: a visitor sees what was read aloud and cannot request the register", async ({ page }) => {
		const errors = collectPortalConsoleErrors(page);
		await page.goto(`/tenders/${REFERENCE}/opening`, { waitUntil: "domcontentloaded" });
		await waitForPortal(page);
		await expect(page.locator('[data-testid="bop-public"]')).toHaveAttribute("data-phase", "complete");
		await expect(page.locator('[data-testid="bop-public-readout"] tbody tr')).toHaveCount(1);
		await expect(page.locator('[data-testid="bop-public-readout"]')).toContainText("KES 46,400,000.00");
		await expect(page.locator('[data-testid="bop-public-register"]')).toHaveAttribute("data-state", "not-a-submitter");
		// The canonical supplier accounts have no sign-in password (the seed sets
		// none, and this pass never sets one); a submitting supplier's request and
		// download are proven on the browser world (bop-public.spec.ts).
		expect(errors, `console errors: ${errors.join(" | ")}`).toEqual([]);
	});
});
