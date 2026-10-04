import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { collectPortalConsoleErrors, expectNoHorizontalOverflow, loginToPortal, waitForPortal } from "../../helpers/portal";
import { CHAIR, PASSWORD, expectScreen, gotoOpening, openingWorld, restoreBopWorld } from "./bopWorld";

/** BOP-CHG-001 v0.10 §10.5 — the public opening page, boards p0–p6 (Phase 9). */

test.describe.configure({ mode: "serial", timeout: 300_000 });

async function openPublic(page, reference: string) {
	await page.goto(`/tenders/${reference}/opening`, { waitUntil: "domcontentloaded" });
	await waitForPortal(page);
	await expect(page.locator('[data-testid="bop-public"]')).toBeVisible({ timeout: 30_000 });
}

test.describe("BOP public opening page", () => {
	test.afterAll(() => restoreBopWorld());

	test("p0 → p1a: a visitor sees when and how to attend, and no bid facts", async ({ page }) => {
		let world = openingWorld("prepared");
		const errors = collectPortalConsoleErrors(page);
		await page.setViewportSize({ width: 1440, height: 1024 });
		await openPublic(page, world.tender_reference);
		await expect(page.locator('[data-testid="bop-public"]')).toHaveAttribute("data-phase", "details-coming");
		await expect(page.locator('[data-testid="bop-public-arrangements"]')).toContainText("Details on how to attend the opening are coming soon");
		world = openingWorld("published");
		await openPublic(page, world.tender_reference);
		await expect(page.locator('[data-testid="bop-public"]')).toHaveAttribute("data-phase", "before-join");
		await expect(page.locator('[data-testid="bop-public-arrangements"] .kt-label')).toHaveText(["How to attend", "Join opens", "Opening time", "Published"]);
		await expect(page.locator('[data-testid="bop-public-join"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="bop-public-readout"]')).toHaveCount(0);
		await page.setViewportSize({ width: 390, height: 844 });
		await expectNoHorizontalOverflow(page);
		expect(errors, `console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("p1: a signed-in observer joins; the committee sees them as a public observer", async ({ page }) => {
		const world = openingWorld("joined");
		await page.goto(`/tenders/${world.tender_reference}/opening`, { waitUntil: "domcontentloaded" });
		await waitForPortal(page);
		await expect(page.locator('[data-testid="bop-public-sign-in"]')).toBeVisible();  // a guest signs in first
		await loginToPortal(page, world.observer, PASSWORD, `/tenders/${world.tender_reference}/opening`);
		await page.locator('[data-testid="bop-public-join"]').click();
		await expect(page.locator('[data-testid="bop-public-joined"]')).toContainText("Joined");
		await login(page, CHAIR, PASSWORD);
		await gotoOpening(page, world.tender_reference);
		await expectScreen(page, "open-bids");
		await expect(page.locator('[data-testid="bop-attendees"] tbody tr')).toContainText(["Playwright Observer"]);
		await expect(page.locator('[data-testid="bop-attendees"]')).toContainText("No one (public observer)");
	});

	test("p2: during the opening each bid appears once its readout is recorded", async ({ page }) => {
		const world = openingWorld("answered");
		await loginToPortal(page, world.observer, PASSWORD, `/tenders/${world.tender_reference}/opening`);
		await expect(page.locator('[data-testid="bop-public"]')).toHaveAttribute("data-phase", "in-session");
		await expect(page.locator('[data-testid="bop-public-readout"] tbody tr')).toHaveCount(1);
		await expect(page.getByText("a figure was repeated at an attendee’s request. The bid is unchanged.", { exact: false })).toBeVisible();
		await expect(page.locator('[data-testid="bop-public-register"]')).toHaveAttribute("data-state", "after-completion");
	});

	test("p3 → p5, p6: a submitting supplier requests and downloads the register; an observer cannot request it", async ({ page }) => {
		const world = openingWorld("complete");
		await loginToPortal(page, world.observer, PASSWORD, `/tenders/${world.tender_reference}/opening`);
		await expect(page.locator('[data-testid="bop-public-register"]')).toHaveAttribute("data-state", "not-a-submitter");
		await expect(page.locator('[data-testid="bop-public-request"]')).toHaveCount(0);
		await loginToPortal(page, world.supplier, PASSWORD, `/tenders/${world.tender_reference}/opening`);
		await expect(page.locator('[data-testid="bop-public-register"]')).toHaveAttribute("data-state", "can-request");
		await page.locator('[data-testid="bop-public-request"]').click();
		await expect(page.locator('[data-testid="bop-public-register"]')).toHaveAttribute("data-state", "ready", { timeout: 30_000 });
		const href = await page.locator('[data-testid="bop-public-download"]').getAttribute("href");
		const response = await page.request.get(href || "");
		expect(response.status()).toBe(200);
		expect((await response.body()).subarray(0, 4).toString()).toBe("%PDF");
	});
});
