import { expect, test } from "@playwright/test";

import { loginAsAdministrator } from "../../helpers/auth";
import { DANIEL, EVIDENCE, NAOMI, as, closeSession, collectConsoleErrors, expectScreen } from "./awdWorld";

/**
 * AWD-CHG-001 v0.4 §6 persona pass on the canonical award (tracker AWD4-1203;
 * needs `make seed-canonical THROUGH=award`; read-only): the auditor reads the
 * record with no action; the technical operator and Administrator see the
 * technical view only — no report, supplier, price, opinion or decision.
 */

const AWARD = "AWD-MOH-2027-002";

test.describe.configure({ mode: "serial", timeout: 300_000 });

test.describe("Award — persona pass on the canonical award", () => {
	test.afterAll(async () => closeSession());

	test("the auditor reads without any action", async ({ browser }) => {
		const page = await as(browser, NAOMI);
		const errors = collectConsoleErrors(page);
		await page.goto(`/app/award/${AWARD}`, { waitUntil: "domcontentloaded" });
		await expectScreen(page, "delivered");
		const root = page.locator('[data-testid="awd-root"]');
		await expect(root.locator('[data-testid="awd-fact-next"]')).toHaveText("Prepare contract");
		for (const label of ["Sign opinion", "Award and notify bidders", "Record restriction", "Record outcome", "Send and close"]) {
			await expect(root.getByRole("button", { name: label })).toHaveCount(0);
		}
		await page.goto("/app/award", { waitUntil: "domcontentloaded" });
		await expectScreen(page, "workspace-empty");
		await page.screenshot({ path: `${EVIDENCE}/persona-auditor.png`, fullPage: true });
		expect(errors, errors.join(" | ")).toEqual([]);
	});

	for (const [who, login] of [["technical operator", async (browser) => as(browser, DANIEL)], ["Administrator", async (browser) => {
		const context = await browser.newContext({ baseURL: process.env.UI_BASE_URL || "http://127.0.0.1:8000" });
		const page = await context.newPage();
		await page.setViewportSize({ width: 1440, height: 1024 });
		await loginAsAdministrator(page);
		return page;
	}]] as const) {
		test(`the ${who} sees the technical view only`, async ({ browser }) => {
			const page = await (login as (b: typeof browser) => Promise<import("@playwright/test").Page>)(browser);
			await page.goto(`/app/award/${AWARD}`, { waitUntil: "domcontentloaded" });
			await expectScreen(page, "technical");
			const root = page.locator('[data-testid="awd-root"]');
			for (const word of ["Afya", "KES", "46,400,000", "Professional opinion", "lowest evaluated"]) await expect(root).not.toContainText(word);
		});
	}
});
