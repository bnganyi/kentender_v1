import { expect, test } from "@playwright/test";

import { CHARLES, EVIDENCE, as, awardWorld, closeSession, collectConsoleErrors, expectJourney, expectNextStep, expectScreen, openAwardsFromMenu,
	restoreAwardWorld } from "./awdWorld";

/**
 * AWD-CHG-001 v0.4 slice 3 (boards D01, D02; tracker AWD4-307): the Head of
 * Procurement finds the delivered report as a task from the menu, opens the
 * record, writes and signs the professional opinion; the record reaches the
 * Accounting Officer's decision. Reload and browser back keep the record.
 * One fixture entity: the synthetic tender 033 at "received".
 */

test.describe.configure({ mode: "serial", timeout: 300_000 });

test.describe("Award — professional opinion", () => {
	test.afterAll(async () => {
		await closeSession();
		restoreAwardWorld();
	});

	test("from the menu to a signed opinion", async ({ browser }) => {
		const world = awardWorld("received");
		const page = await as(browser, CHARLES);
		const errors = collectConsoleErrors(page);
		await openAwardsFromMenu(page);
		const root = page.locator('[data-testid="awd-root"]');
		await expect(root).toHaveAttribute("data-screen", "workspace");
		const row = root.locator("tr", { hasText: world.award });
		await expect(row).toContainText("Prepare professional opinion");
		await expect(row).toContainText("Charles Mutiso");
		await page.screenshot({ path: `${EVIDENCE}/D01.png`, fullPage: true });
		await row.getByRole("button", { name: "Open award" }).click();

		await expectScreen(page, "opinion");
		await expect(page).toHaveURL(new RegExp(`/(app|desk)/award/${world.award}$`));
		await expectNextStep(page, "your_turn", "Prepare the professional opinion.");
		await expectJourney(page, ["Current", "Not started", "Not started", "Not started", "Not started"]);
		await expect(root.locator('[data-testid="awd-fact-committee-signatures"]')).toHaveText("3 of 3");
		await expect(root.locator('[data-testid="awd-fact-submitted-tender-sum"]')).toHaveText("KES 46,400,000");
		await expect(root.locator('[data-testid="awd-test-environment"]')).toHaveText("Test environment — no live award notices are sent.");

		await root.locator("label.radio", { hasText: "Recommend award" }).click();
		await root.locator('[data-testid="awd-field-reason"]').fill("The signed report identifies Afya Digital Supplies Limited as the lowest evaluated responsive tenderer. No unresolved issue prevents the proposed award.");
		await root.locator('[data-testid="awd-action-save-draft"]').click();
		await expectScreen(page, "opinion");
		await page.reload({ waitUntil: "domcontentloaded" });
		await expectScreen(page, "opinion");
		await expect(root.locator('[data-testid="awd-field-reason"]')).toHaveValue(/lowest evaluated responsive tenderer/);
		await page.screenshot({ path: `${EVIDENCE}/D02.png`, fullPage: true });

		await root.locator('[data-testid="awd-action-sign-opinion"]').click();
		await expectScreen(page, "decision-read");
		await expectNextStep(page, "waiting", "The Accounting Officer is deciding the award.");
		await expectJourney(page, ["Done", "Current", "Not started", "Not started", "Not started"]);

		// back returns to the workspace, forward to the same record
		await page.goBack();
		await expectScreen(page, "workspace-empty");
		await page.goForward();
		await expectScreen(page, "decision-read");
		expect(errors, errors.join(" | ")).toEqual([]);
	});
});
