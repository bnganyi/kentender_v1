import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";

/**
 * OVS-CHG-001 v0.6 Phase 5 / OVS-AC-012 (the Not held case on real data). Needs the isolated Tender B branch:
 *   make seed-ovs-register-branch SITE=kentender-test.local   (before)
 *   make seed-ovs-register-branch-restore SITE=kentender-test.local   (after)
 * With it loaded the register has four rows: the canonical Tender's three held meetings and Tender B's opening,
 * which was recorded Not held and is listed once and not counted.
 */
test.describe.configure({ mode: "serial", timeout: 180_000 });

const PASSWORD = process.env.UI_SEED_PASSWORD || "Test@123";
const AMINA = "amina.hassan@moh.example.test";
const NAOMI = "naomi.chebet@moh.example.test";
const PETER = "peter.kimani@moh.example.test";
const B_UNIT = "Playwright — Digital Health";

async function open(page, user: string) {
	await login(page, user, PASSWORD);
	await page.goto("/desk/procurement-meetings", { waitUntil: "domcontentloaded" });
	await expect(page.locator('[data-testid="pmt-title"]')).toBeVisible({ timeout: 60_000 });
}

test("a Not held opening is listed once and is not counted as held", async ({ page }) => {
	await open(page, AMINA);
	await expect(page.locator('[data-testid="pmt-rows"] tbody tr')).toHaveCount(4);
	await expect(page.locator('[data-testid="pmt-held-total"]')).toHaveText("3");
	const notHeld = page.locator('[data-testid="pmt-rows"] tbody tr').filter({ hasText: "Not held" });
	await expect(notHeld).toHaveCount(1);
	await expect(notHeld).toContainText("Scheduled");
	await expect(notHeld).toContainText(B_UNIT);
	const grouping = page.locator('[data-testid="pmt-by-department"] tbody tr').filter({ hasText: B_UNIT });
	await expect(grouping).toContainText("0"); // grouped under its own lead department, with nothing held
});

test("the auditor sees the same four rows", async ({ page }) => {
	await open(page, NAOMI);
	await expect(page.locator('[data-testid="pmt-rows"] tbody tr')).toHaveCount(4);
	await expect(page.locator('[data-testid="pmt-held-total"]')).toHaveText("3");
});

test("a department head whose scope does not reach Tender B does not see it, nor a count that includes it", async ({ page }) => {
	await open(page, PETER);
	await expect(page.locator('[data-testid="pmt-rows"] tbody tr')).toHaveCount(3);
	await expect(page.locator('[data-testid="pmt-held-total"]')).toHaveText("3");
	await expect(page.locator('[data-testid="pmt-rows"]')).not.toContainText(B_UNIT);
	await expect(page.locator("body")).not.toContainText("Not held");
});

test("filtering by state Not held returns that opening and a held total of zero", async ({ page }) => {
	await open(page, AMINA);
	await page.locator("#pmt-state").selectOption("Not held");
	await expect(page.locator('[data-testid="pmt-rows"] tbody tr')).toHaveCount(1);
	await expect(page.locator('[data-testid="pmt-held-total"]')).toHaveText("0");
});
