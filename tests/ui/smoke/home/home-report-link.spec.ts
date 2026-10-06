import { execSync } from "node:child_process";
import * as path from "node:path";

import { expect, test } from "@playwright/test";

import { AMINA, flat, openHomeFromMenu, putWorldClock, rows } from "./helpers";

/**
 * HOME-CHG-001 v0.6 HOME-AC-07 — "View report" on an oversight row opens the delivered Evaluation report, by Evaluation's
 * own route. The canonical world is past the Award's opinion stage, so Amina has no such row in it; this spec loads the
 * Award demo profile AWD-DEMO-OPINION (the opinion is awaited, the Evaluation report delivered 16 June, 14:07) and
 * restores the canonical world afterwards. Run on the test site only.
 */
test.describe.configure({ mode: "serial", timeout: 240_000 });

const REF = "TND-MOH-2026-002";

function awardProfile(fn: string, kwargs: Record<string, unknown> = {}): void {
	const bench = path.resolve(__dirname, "../../../../../..");
	const args = Object.keys(kwargs).length ? ` --kwargs '${JSON.stringify(kwargs)}'` : "";
	execSync(`cd "${bench}" && bench --site ${process.env.UI_SITE || "kentender.midas.com"} execute kentender_procurement.award.seeds.profiles.${fn}${args}`, { stdio: "pipe", timeout: 300_000 });
}

test.beforeAll(() => awardProfile("load_profile", { profile: "AWD-DEMO-OPINION" }));
test.afterAll(() => {
	awardProfile("restore_base");
	putWorldClock();
});

test.describe("Amina, Accounting Officer, with the opinion awaited (slice A: Award)", () => {
	test("an oversight row shows when the Evaluation report was delivered and View report opens that report", async ({ page }) => {
		const errors = await openHomeFromMenu(page, AMINA);
		await page.locator('#oversee [data-testid="kt-home-show-more"]').click();
		const row = rows(page, "oversee").filter({ hasText: "Supply and delivery of business laptops" });
		await expect(row).toHaveCount(1);
		const text = await flat(row);
		expect(text).toContain("Awaiting professional opinion by Charles Mutiso");
		expect(text).toContain("Evaluation report delivered 16 June, 14:07");
		const link = row.locator('[data-testid="kt-home-view"]');
		await expect(link).toHaveText("View report");
		await expect(link).toHaveAttribute("href", `/app/tenders/${REF}/evaluation/report`);
		await link.click();
		await expect(page).toHaveURL(new RegExp(`/desk/tenders/${REF}/evaluation/report$`), { timeout: 60_000 });
		await expect(page.locator("body")).not.toContainText("Not found");
		await expect(page.locator("body")).toContainText("report", { ignoreCase: true });
		expect(errors.filter((e) => !/socket|favicon/i.test(e))).toEqual([]);
	});

});
