import { execSync } from "node:child_process";
import * as path from "node:path";

import { expect, test } from "@playwright/test";

import { DANIEL, NAOMI, flat, openHomeFromMenu, putWorldClock, rows } from "./helpers";

/**
 * HOME-CHG-001 v0.6, FU-HOME-46 (owner decision 5 Oct 2026): a Technical Operator's support issues are on Home, since My
 * Work was retired into it. Opens one real Support Issue (namespace HOME_E2E), walks Daniel from the sidebar, and removes
 * the issue and its notices afterwards. Run on the test site:
 *   scripts/test-site.sh run npx playwright test tests/ui/smoke/home/home-technical-work.spec.ts --workers=1
 */
test.describe.configure({ mode: "serial", timeout: 180_000 });

const NAMESPACE = "HOME_E2E";
const SUBJECT = "Resolve evaluation issue for TND-HOME-E2E";
const SITE = () => process.env.UI_SITE || "kentender.midas.com";
const bench = (method: string, kwargs: Record<string, unknown>) => {
	const root = path.resolve(__dirname, "../../../../../..");
	return execSync(`cd "${root}" && bench --site ${SITE()} execute ${method} --kwargs '${JSON.stringify(kwargs)}'`, { stdio: "pipe", timeout: 120_000, encoding: "utf-8" });
};

let issueId = "";

test.beforeAll(() => {
	putWorldClock();
	const out = bench("kentender_core.services.support_issues.open_issue", {
		module: "Bid Evaluation", operation: "ReceiveOpeningPackage", operation_correlation: "HOME-E2E-1", subject: SUBJECT,
		safe_detail: "The completed opening package could not be loaded.", fixture_namespace: NAMESPACE,
	});
	issueId = /SI-\d{4}-\d{5}/.exec(out)?.[0] || "";
	expect(issueId, out).not.toBe("");
});

test.afterAll(() => {
	bench("frappe.db.delete", { doctype: "Notification Log", filters: { document_type: "Support Issue", document_name: issueId } });
	bench("frappe.db.delete", { doctype: "Support Issue", filters: { fixture_namespace: NAMESPACE } });
});

test("Daniel (Technical Operator) sees the issue as his work, with the search link and no counts, and it opens the Support Issue", async ({ page }) => {
	const errors = await openHomeFromMenu(page, DANIEL);
	await expect(page.locator('[data-testid="kt-home-technical-link"]')).toBeVisible();
	await expect(page.locator('[data-testid="kt-home-summary"]')).toHaveCount(0);
	const row = rows(page, "my-work").filter({ hasText: SUBJECT });
	await expect(row).toHaveCount(1);
	const text = await flat(row);
	expect(text).toContain("Support issues");
	expect(text).toContain(issueId);
	expect(text).toContain("Repair the failed operation");
	expect(text).not.toContain("could not be loaded"); // the detail belongs to the issue's own page
	await row.locator('[data-testid="kt-home-continue"]').click();
	await expect(page).toHaveURL(new RegExp(`/desk/support-issue/${issueId}$`), { timeout: 60_000 });
	await expect(page.locator("body")).not.toContainText("Not Permitted");
	expect(errors.filter((e) => !/socket|favicon/i.test(e))).toEqual([]);
});

test("an ordinary business user never sees it", async ({ page }) => {
	await openHomeFromMenu(page, NAOMI);
	await expect(page.locator('[data-testid="kt-home-root"]')).not.toContainText(SUBJECT);
});
