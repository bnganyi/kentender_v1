import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { addRecord } from "../../helpers/picker";
import { AO, AUDITOR, CHAIR, INDEPENDENT, MEMBER, PASSWORD, collectConsoleErrors, expectNextStep, expectScreen, gotoOpening, openingWorld, restoreBopWorld } from "./bopWorld";

/** BOP-CHG-001 v0.10 §10.2 — BOP-DES-01 Prepare opening (boards a1–a5), slice 8.1. */

test.describe.configure({ mode: "serial", timeout: 300_000 });

test.describe("BOP-DES-01 Prepare opening", () => {
	test.afterAll(() => restoreBopWorld());

	test("AO: a refused committee (a2), then appoint (a1 → a3), publish how to attend (a4 → a5), and back again", async ({ page }) => {
		const world = openingWorld("prepared");
		const errors = collectConsoleErrors(page);
		await login(page, AO, PASSWORD);
		await gotoOpening(page, world.tender_reference);
		await expectScreen(page, "prepare");
		await expectNextStep(page, "your_turn", "Appoint opening committee");
		await expect(page.locator('[data-testid="bop-title"]')).toHaveText("Supply and delivery of business laptops");
		await expect(page.locator('[data-testid="bop-committee-draft"] thead th')).toHaveText(["Member", "Designation", "Role on committee", "Eligibility"]);
		await expect(page.locator('[data-testid="bop-history"] .tag')).toHaveText("No appointments yet");

		// Add members: one dialog, the list open beside the field. Choosing a person adds them to "To appoint" and leaves the list where it was.
		await page.locator('[data-testid="bop-add-member"]').click();
		await expect(page.locator("#bop-add-member-title")).toHaveText("Add members");
		await expect(page.locator('[data-testid="bop-staged-empty"]')).toHaveText("People you choose appear here.");
		await addRecord(page, "#bop-add-member-person", CHAIR);
		await addRecord(page, "#bop-add-member-person", MEMBER);
		await expect(page.locator('[data-testid="bop-staged-title"]')).toHaveText("To appoint · 2");
		await expect(page.locator('[data-testid="bop-add-member-confirm"]')).toHaveText("Appoint 2 members");
		// the second person is suggested as the independent member, and the officer who prepared this Tender cannot be: it says so beside them
		await expect(page.locator(`[data-testid="bop-staged-role-${MEMBER}"]`)).toHaveValue("Independent member");
		await expect(page.locator(`[data-testid="bop-staged-error-${MEMBER}"]`)).toHaveText("Involved in processing this Tender.");
		await expect(page.locator('[data-testid="bop-add-member-confirm"]')).toBeDisabled();
		await page.locator(`[data-testid="bop-staged-role-${MEMBER}"]`).selectOption("Member");
		await expect(page.locator(`[data-testid="bop-staged-error-${MEMBER}"]`)).toHaveCount(0);
		// a2: two processing officers only — one action appoints them, the server refuses, and its guard is the next step.
		await page.locator('[data-testid="bop-add-member-confirm"]').click();
		await expect(page.locator('[data-testid="bop-add-member-dialog"]')).toHaveCount(0);
		await expectScreen(page, "prepare");
		await expectNextStep(page, "your_turn_blocked", "The opening committee needs an independent third member");
		await expect(page.locator('[data-testid="bop-committee-draft"] tbody tr td:first-child')).toHaveText(["Charles Mutiso", "Playwright Tenders Officer"]);
		await expect(page.locator('[data-testid="bop-add-member"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="bop-appoint"]')).toHaveCount(0);
		// What the refused appointment left in the table is the reader's own work in this browser: a refresh must not lose it,
		// and the screen says it is not appointed yet.
		await page.reload({ waitUntil: "domcontentloaded" });
		await expectScreen(page, "prepare");
		await expect(page.locator('[data-testid="bop-committee-draft"] tbody tr td:first-child')).toHaveText(["Charles Mutiso", "Playwright Tenders Officer"]);
		await expect(page.locator('[data-testid="bop-draft-note"]')).toContainText("kept in this browser");

		// The fix opens Add members again, with the two already on the committee; an officer who processed the Tender cannot be the independent member.
		await page.locator('[data-testid="bop-add-member"]').click();
		await addRecord(page, "#bop-add-member-person", INDEPENDENT);
		await expect(page.locator(`[data-testid="bop-staged-role-${INDEPENDENT}"]`)).toHaveValue("Independent member");
		await expect(page.locator(`[data-testid="bop-staged-error-${INDEPENDENT}"]`)).toHaveCount(0); // not involved in processing this Tender
		await expect(page.locator('[data-testid="bop-add-member-confirm"]')).toHaveText("Appoint 3 members");
		await page.locator('[data-testid="bop-add-member-confirm"]').click();

		// a3: appointed; each member has their task; how to attend is not published.
		await expectScreen(page, "prepare");
		await expectNextStep(page, "your_turn", "Publish how to attend");
		await expect(page.locator('[data-testid="bop-committee"] tbody tr td:last-child')).toHaveText(["Sent", "Sent", "Sent"]);
		await expect(page.locator('[data-testid="bop-history"] .tag')).toContainText("Appointed");

		// a4 → a5
		await page.locator('[data-testid="bop-open-arrangements"]').click();
		await expect(page.locator('[data-testid="bop-attendance-method"]')).toHaveValue("Attend the public bid opening online");
		await page.locator('[data-testid="bop-attendance-instructions"]').fill("Select Join public opening on this Tender’s page. You can listen, ask for a figure to be repeated, or make a procedural comment.");
		await page.locator('[data-testid="bop-publish"]').click();
		await expectScreen(page, "prepare");
		await expectNextStep(page, "done", /^You published how to attend on /);
		await expect(page.locator('[data-testid="bop-arrangements"] .kt-label')).toHaveText(["Attendance method", "Join opens", "Opening time", "Published"]);
		await expect(page.locator('[data-testid="bop-committee-summary"]')).toContainText("(independent member)");

		// Update instructions posts a new version; direct load and back/forward keep the opening.
		await page.locator('[data-testid="bop-update-arrangements"]').click();
		await page.locator('[data-testid="bop-attendance-instructions"]').fill("The online service moved; select Join public opening on this Tender’s page.");
		await page.locator('[data-testid="bop-publish"]').click();
		await expectScreen(page, "prepare");
		await expect(page.locator('[data-testid="bop-update-arrangements"]')).toBeVisible();
		await page.reload({ waitUntil: "domcontentloaded" });
		await expectScreen(page, "prepare");
		await page.goto(`/app/tenders/${world.tender_reference}`, { waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="tnd-shell"]')).not.toHaveAttribute("data-screen", "opening", { timeout: 30_000 });
		await page.goBack();
		await expectScreen(page, "prepare");
		await expect(page.locator('[data-testid="bop-arrangements"]')).toBeVisible();
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("the Tender record links to its bid opening (BOP-CHG-001 v0.10 §9)", async ({ page }) => {
		const world = openingWorld("prepared");
		await login(page, AO, PASSWORD);
		await page.setViewportSize({ width: 1440, height: 1024 });
		await page.goto(`/app/tenders/${world.tender_reference}`, { waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="tnd-shell"]')).toHaveAttribute("data-loading", "false", { timeout: 30_000 });
		await page.locator('[data-testid="tnd-link-bid-opening"]').click();
		await expect(page).toHaveURL(new RegExp(`/(app|desk)/tenders/${world.tender_reference}/opening$`));
		await expectScreen(page, "prepare");
		await expectNextStep(page, "your_turn", "Appoint opening committee");
	});

	test("members and the Auditor see no appointment controls; an outsider gets Not found", async ({ page }) => {
		const world = openingWorld("published");
		await login(page, AUDITOR, PASSWORD);
		await gotoOpening(page, world.tender_reference);
		await expect(page.locator('[data-testid="bop-root"]')).not.toHaveAttribute("data-screen", "prepare", { timeout: 30_000 });
		await expect(page.locator('[data-testid="bop-root"]')).toHaveAttribute("data-loading", "false");
		await expect(page.locator('[data-testid="bop-add-member"], [data-testid="bop-appoint"], [data-testid="bop-publish"]')).toHaveCount(0);

		await login(page, "pw.req.outsider@example.test", PASSWORD);
		await gotoOpening(page, world.tender_reference);
		await expect(page.locator('[data-testid="bop-state-not-found"]')).toBeVisible({ timeout: 30_000 });
	});
});
