import { execSync } from "node:child_process";
import path from "node:path";

import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { collectPortalConsoleErrors, loginToPortal, waitForPortal } from "../../helpers/portal";
import { collectConsoleErrors, expectNextStep, expectScreen, gotoOpening } from "./bopWorld";

/**
 * BOP-CHG-001 v0.10 plan Phase 11 (BOP10-1103, PRC-INT-01 browser part): the
 * canonical opening (`make seed-canonical THROUGH=bid_opening`) read in a
 * browser by each seeded person, read-only. Bid Submission closed the
 * canonical Tender at 11:00; Bid Opening opened it with the appointed
 * members, David Ouma's attendance and the final signed record.
 */

const REFERENCE = process.env.UI_BOP_CANONICAL_TENDER || "TND-MOH-2027-002";
// The canonical world is dated 2027; the pages read it just after the opening
// completed (12 Jun 2027 11:15), as the Bid Submission persona pass does, so
// every person's roles are in force. Cleared afterwards.
const AT = "2027-06-12 11:15:00";
const BENCH_ROOT = path.resolve(__dirname, "../../../../../..");
function setInstant(instant: string | null): void {
	const kwargs = instant ? `{"instant": "${instant}"}` : `{"instant": None}`;
	execSync(`cd "${BENCH_ROOT}" && bench --site ${process.env.UI_SITE || "kentender.midas.com"} execute kentender_core.services.test_clock.set_instant --kwargs '${kwargs}'`, { stdio: "pipe", timeout: 120_000 });
}
const PASSWORD = process.env.UI_SEED_PASSWORD || "Test@123";
const person = (local: string) => `${local}@moh.example.test`;

test.describe.configure({ mode: "serial", timeout: 240_000 });

test.describe("BOP release evidence — the canonical opening, person by person", () => {
	test.beforeAll(() => setInstant(AT));
	test.afterAll(() => setInstant(null));

	test("the committee: Charles, Brian and Beatrice see the completed record; only the recorder may correct it", async ({ page }) => {
		const errors = collectConsoleErrors(page);
		for (const local of ["charles.mutiso", "brian.wafula", "beatrice.kamau"]) {
			await login(page, person(local), PASSWORD);
			await gotoOpening(page, REFERENCE);
			await expectScreen(page, "completed");
			await expectNextStep(page, "done", /after the last signature\.$/);
			await expect(page.locator('[data-testid="bop-signatures"] tbody tr')).toHaveCount(3);
			await expect(page.locator('[data-testid="bop-signatures"] .kt-status')).toHaveText(["Signed", "Signed", "Signed"]);
			// the canonical Tender's four bids (SEED-OPS-001 v1.21), in the order the tender box accepted them
			await expect(page.locator('[data-testid="bop-register"] tbody tr')).toHaveCount(4);
			await expect(page.locator('[data-testid="bop-register"] tbody tr').first()).toContainText("Afya Digital Supplies Limited");
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

	test("the administrator and Daniel Otieno (technical operator) see technical status only", async ({ page }) => {
		for (const [user, password] of [[process.env.UI_ADMIN_USER || "Administrator", process.env.UI_ADMIN_PASSWORD || "admin"], [person("daniel.otieno"), PASSWORD]]) {
			await login(page, user, password);
			await gotoOpening(page, REFERENCE);
			await expectScreen(page, "completed");
			await expect(page.locator('[data-testid="bop-technical"]')).toContainText("Bids, the register and the opening record are not shown to administrators.");
			await expect(page.locator('[data-testid="bop-technical"]')).toContainText("None recorded");
			await expect(page.locator('[data-testid="bop-register"], [data-testid="bop-signatures"], [data-testid="bop-guidance"]')).toHaveCount(0);
		}
	});

	test("Amina's record names both attendees: David Ouma for Afya, Jane Wanjiku as a public observer", async ({ page }) => {
		await login(page, person("amina.hassan"), PASSWORD);
		await gotoOpening(page, REFERENCE);
		await expectScreen(page, "completed");
		await expect(page.locator('[data-testid="bop-session"]')).toContainText("Started the opening");
		const res = await page.request.get(`/api/method/kentender_procurement.bid_opening.api.get_opening?tender_reference=${REFERENCE}`);
		const attendees = (await res.json()).message.attendees.map((a: { person_name: string; capacity: string }) => `${a.person_name} · ${a.capacity}`);
		expect(attendees).toEqual(["David Ouma · Tenderer representative", "Jane Wanjiku · Public observer"]);
	});

	test("the public page: a visitor and Jane Wanjiku see what was read aloud; only David Ouma may request the register", async ({ page }) => {
		const errors = collectPortalConsoleErrors(page);
		await page.goto(`/tenders/${REFERENCE}/opening`, { waitUntil: "domcontentloaded" });
		await waitForPortal(page);
		await expect(page.locator('[data-testid="bop-public"]')).toHaveAttribute("data-phase", "complete");
		// all four bids' read-aloud totals are public (SEED-OPS-001 v1.21)
		await expect(page.locator('[data-testid="bop-public-readout"] tbody tr')).toHaveCount(4);
		for (const total of ["KES 46,400,000.00", "KES 48,720,000.00", "KES 43,500,000.00", "KES 46,980,000.00"]) {
			await expect(page.locator('[data-testid="bop-public-readout"]')).toContainText(total);
		}
		await expect(page.locator('[data-testid="bop-public-register"]')).toHaveAttribute("data-state", "not-a-submitter");
		// Jane Wanjiku, signed in: a member of the public, no request control
		await loginToPortal(page, "jane.wanjiku@observer.example", PASSWORD, `/tenders/${REFERENCE}/opening`);
		await expect(page.locator('[data-testid="bop-public"]')).toHaveAttribute("data-phase", "complete");
		await expect(page.locator('[data-testid="bop-public-register"]')).toHaveAttribute("data-state", "not-a-submitter");
		await expect(page.locator('[data-testid="bop-public-request"]')).toHaveCount(0);
		// David Ouma, the submitting supplier's representative: may request the
		// register (read-only here; requesting and downloading are proven on the
		// browser world, bop-public.spec.ts, so the canonical record stays as seeded)
		await loginToPortal(page, "david.ouma@afyadigital.example", PASSWORD, `/tenders/${REFERENCE}/opening`);
		await expect(page.locator('[data-testid="bop-public-register"]')).toHaveAttribute("data-state", "can-request");
		await expect(page.locator('[data-testid="bop-public-request"]')).toBeVisible();
		await expect(page.locator('[data-testid="bop-public-readout"]')).toContainText("Afya Digital Supplies Limited");
		expect(errors, `console errors: ${errors.join(" | ")}`).toEqual([]);
	});
});
