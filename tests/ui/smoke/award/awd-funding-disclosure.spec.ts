import { expect, test } from "@playwright/test";

import { AMINA, CHARLES, DANIEL, MARY, NAOMI, as, closeSession } from "./awdWorld";

const EVIDENCE_V07 = "docs/mvp-1-r1/16_award/evidence/v0_7";

/**
 * AWD-CHG-001 v0.7 section 10.4 (AWD-FUND-AC-006): the read-only Funding sources disclosure on the internal Award record, read on the canonical award (AWD-MOH-2026-002, two reservations,
 * KES 46,400,000) exactly as the seed world holds it. Nothing here writes: no profile is loaded and no award command is run. The Accounting Officer, the Head of Procurement and the Auditor
 * read the same table; a technical reader and the supplier's signatory are given no funding at all.
 */

test.describe.configure({ mode: "serial", timeout: 180_000 });

const AWARD = "AWD-MOH-2026-002";

test.describe("Award — Funding sources disclosure on the canonical award", () => {
	test.afterAll(async () => {
		await closeSession();
	});

	for (const [who, user] of [["the Accounting Officer", AMINA], ["the Head of Procurement", CHARLES], ["the Auditor", NAOMI]] as const) {
		test(`${who} reads each department's quantity and awarded amount with the total, and the source details`, async ({ browser }) => {
			const page = await as(browser, user);
			const errors: string[] = [];
			page.on("pageerror", (e) => errors.push(e.message));
			await page.goto(`/app/award/${AWARD}`, { waitUntil: "domcontentloaded" });
			const root = page.locator('[data-testid="awd-root"]');
			await expect(root).toHaveAttribute("data-loading", "false", { timeout: 30_000 });
			const section = root.locator('[data-testid="awd-funding"]');
			await expect(section).toBeVisible();
			await expect(section.locator("h2")).toContainText("Funding sources");
			await expect(section.locator("thead th")).toHaveText(["Department", "Quantity", "Awarded amount"]);
			const rows = section.locator("tbody tr");
			await expect(rows).toHaveCount(3); // two sources and the total
			await expect(rows.nth(0)).toContainText("KES 18,560,000");
			await expect(rows.nth(1)).toContainText("KES 27,840,000");
			await expect(rows.nth(2)).toContainText("Total");
			await expect(rows.nth(2)).toContainText("KES 46,400,000");
			await section.scrollIntoViewIfNeeded();

			// an interactive re-render: open the expanded details, see the exact requisition, reservation and Budget line, close them again
			const details = root.locator('[data-testid="awd-disclosure-funding-source-details"]');
			await expect(details).toBeVisible();
			await details.locator(".kt-disclosure-head").click();
			await expect(details.locator(".kt-disclosure-body p")).toHaveCount(2);
			if (user === AMINA) await page.screenshot({ path: `${EVIDENCE_V07}/funding-sources-canonical-ao.png`, fullPage: true });
			await expect(details.locator(".kt-disclosure-body")).toContainText("Requisition");
			await expect(details.locator(".kt-disclosure-body")).toContainText("Reservation");
			await expect(details.locator(".kt-disclosure-body")).toContainText("Budget line");
			await details.locator(".kt-disclosure-head").click();
			await expect(details.locator(".kt-disclosure-body")).toHaveCount(0);

			// a refresh keeps it
			await page.reload({ waitUntil: "domcontentloaded" });
			await expect(root.locator('[data-testid="awd-funding"] tbody tr')).toHaveCount(3, { timeout: 30_000 });
			expect(errors).toEqual([]);
		});
	}

	test("a technical reader and the supplier's signatory are given no funding", async ({ browser }) => {
		let page = await as(browser, DANIEL);
		await page.goto(`/app/award/${AWARD}`, { waitUntil: "domcontentloaded" });
		const root = page.locator('[data-testid="awd-root"]');
		await expect(root).toHaveAttribute("data-loading", "false", { timeout: 30_000 });
		await expect(root.locator('[data-testid="awd-funding"]')).toHaveCount(0);
		await expect(root).not.toContainText("46,400,000");
		page = await as(browser, MARY);
		await page.goto(`/app/award/${AWARD}`, { waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="awd-funding"]')).toHaveCount(0);
		await expect(page.locator("body")).not.toContainText("Funding sources");
	});
});
