import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { PASSWORD, action, collectConsoleErrors, evaluationWorld, expectNextStep, expectScreen, gotoEvaluation, restoreEvlWorld } from "./evlWorld";

/** EVL-CHG-001 v0.8 §3, §9.2, §9.3 (v0.4 boards; the department is read-only text, no reference is typed and the Head is secretary by office) — workspace and committee (boards D01-APPOINT, D02-A, D02-DELEGATE, D02-D, D02-CONFLICT,
 *  D02-REPLACE, D02-INELIGIBLE, S-OPENING-AWAITED), slices 11.1–11.2. One fixture entity: the Playwright Tender's evaluation. */

test.describe.configure({ mode: "serial", timeout: 600_000 });

test.describe("EVL committee and declaration", () => {
	test.afterAll(() => restoreEvlWorld());

	test("AO appoints from the workspace task and the Head is recorded as secretary, a member declares", async ({ page }) => {
		const world = evaluationWorld("prepared");
		const p = world.people;
		const errors = collectConsoleErrors(page);

		// D01-APPOINT: the workspace task opens D02-A; no bidder facts anywhere.
		await login(page, p.ao, PASSWORD);
		await page.setViewportSize({ width: 1440, height: 1024 });
		await page.goto("/app/bid-evaluation", { waitUntil: "domcontentloaded" });
		const ws = page.locator('[data-testid="evl-workspace"]');
		await expect(ws).toHaveAttribute("data-loading", "false", { timeout: 30_000 });
		await expect(ws.locator(".kt-task-row", { hasText: `Appoint evaluation committee for ${world.tender_reference}` })).toBeVisible();
		await expect(ws.locator('[data-testid="evl-register"]')).toContainText(world.tender_reference);
		await ws.locator(".kt-task-row", { hasText: world.tender_reference }).locator("button", { hasText: "Appoint committee" }).click();
		await expectScreen(page, "appoint");
		await expectNextStep(page, "your_turn", "Appoint the members who will evaluate this tender.");
		await expect(page.locator('[data-testid="evl-root"] [data-testid="evl-title"]')).toHaveText("Appoint evaluation committee");
		await expect(page.locator('[data-testid="evl-root"]')).not.toContainText("Afya");

		// The department is read-only text from the person's home organisation unit (EVL-CHG-001 v0.7 §3); no reference is typed.
		const root = page.locator('[data-testid="evl-root"]');
		await expect(root.locator('[data-testid="evl-field-appointment_reference"]')).toHaveCount(0);
		await expect(root.locator('[data-testid="evl-member-0-department"]')).toHaveCount(0);
		await expect(root).toContainText("The appointment reference is created when you appoint the committee. The Head of Procurement Function is recorded as the evaluation secretary.");
		await root.locator('[data-testid="evl-member-0-user"]').selectOption(p.chair);
		await root.locator('[data-testid="evl-member-1-user"]').selectOption(p.member);
		await root.locator('[data-testid="evl-member-2-user"]').selectOption(p.member_2);
		await expect(root.locator('[data-testid="evl-members"] tbody tr').nth(0)).toContainText("Human Resources Management and Development");
		await expect(root.locator('[data-testid="evl-members"] tbody tr').nth(1)).toContainText("ICT");
		await expect(root.locator('[data-testid="evl-members"] tbody tr').nth(2)).toContainText("Finance");
		await action(page, "Appoint committee").click();
		await expect(page.locator('[data-testid="evl-root"]')).not.toHaveAttribute("data-screen", "appoint", { timeout: 30_000 });
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("the Head is secretary by office and delegates the secretary duties (D02-DELEGATE)", async ({ page, browser }) => {
		const world = evaluationWorld("appointed");
		const p = world.people;
		const errors = collectConsoleErrors(page);
		const root = page.locator('[data-testid="evl-root"]');
		// no secretary task, waiting item or next step exists for the Head: the record offers the action as a secondary
		await login(page, p.hop, PASSWORD);
		await gotoEvaluation(page, world.tender_reference);
		await expectScreen(page, "preparing");
		await expect(root).not.toContainText("Assign the person who will organise the evaluation record.");
		await expect(root.locator('[data-testid="evl-roster"]')).toContainText("Secretary");
		await action(page, "Delegate secretary duties").click();
		await expectScreen(page, "delegate");
		await expect(root.locator('[data-testid="evl-title"]')).toHaveText("Delegate secretary duties");
		await expect(root).toContainText("Head of Procurement Function, by office");
		await expect(root.locator('[data-testid="evl-field-appointment_reference"]')).toHaveCount(0);
		await expect(root.locator('[data-testid="evl-field-department"]')).toHaveCount(0);
		await root.locator('[data-testid="evl-field-secretary"]').selectOption(p.secretary);
		await expect(root).toContainText("This is your written appointment and a new reference is created. They will have no vote, finding or signature.");
		await action(page, "Delegate secretary duties").click();
		await expect(root).not.toHaveAttribute("data-screen", "delegate", { timeout: 30_000 });
		// the committee record names the current secretary and keeps both records
		await gotoEvaluation(page, world.tender_reference, "record");
		await expect(root).toContainText("delegated by");
		await root.locator('[data-testid="evl-disclosure-appointment-and-declaration-history"]').click();
		await expect(root.locator('[data-testid="evl-history"]')).toContainText("Secretary by office");
		await expect(root.locator('[data-testid="evl-history"]')).toContainText("written appointment by");
		// only the authorised Head is offered it: the Accounting Officer has no control and is refused the form
		const ao = await browser.newPage();
		await login(ao, p.ao, PASSWORD);
		await gotoEvaluation(ao, world.tender_reference);
		await expect(ao.locator('[data-testid="evl-root"]').getByRole("button", { name: "Delegate secretary duties" })).toHaveCount(0);
		await gotoEvaluation(ao, world.tender_reference, "delegate");
		await expect(ao.locator('[data-testid="evl-root"]')).not.toHaveAttribute("data-screen", "delegate");
		await ao.close();
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("a member declares (D02-D) and then waits for the opening (S-OPENING-AWAITED)", async ({ page }) => {
		const world = evaluationWorld("assigned");
		const p = world.people;
		const errors = collectConsoleErrors(page);
		await login(page, p.chair, PASSWORD);
		await gotoEvaluation(page, world.tender_reference, "declaration");
		await expectScreen(page, "declaration");
		await expect(page.locator('[data-testid="evl-root"] [data-testid="evl-title"]')).toHaveText("Your evaluation declaration");
		await action(page, "Save declaration").click();
		await expectScreen(page, "declaration");
		await expect(page.locator('[data-testid="evl-root"] [data-testid="evl-error"]')).toBeVisible(); // confidentiality not accepted
		await page.locator('[data-testid="evl-root"] label.kt-checkbox', { hasText: "keep bid information confidential" }).click();
		await expect(page.locator('[data-testid="evl-root"] [data-testid="evl-check-confidentiality_accepted"]')).toBeChecked();
		await action(page, "Save declaration").click();
		await expectScreen(page, "preparing");
		await expectNextStep(page, "timed", /^Opening is scheduled for /);
		await expect(page.locator('[data-testid="evl-root"] [data-testid="evl-roster"] tbody tr')).toHaveCount(4);
		// direct load and back/forward keep the evaluation
		await page.reload({ waitUntil: "domcontentloaded" });
		await expectScreen(page, "preparing");
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("a declared conflict: the AO is refused an ineligible replacement, then replaces (D02-INELIGIBLE → D02-REPLACE)", async ({ page }) => {
		const world = evaluationWorld("conflict");
		const p = world.people;
		const errors = collectConsoleErrors(page);
		await login(page, p.ao, PASSWORD);
		await gotoEvaluation(page, world.tender_reference);
		await expectNextStep(page, "your_turn", /declared conflict\.$/);
		await action(page, "Replace member").click();
		await expectScreen(page, "replace");
		await page.locator('[data-testid="evl-root"] [data-testid="evl-field-incoming"]').selectOption(p.member);
		await expect(page.locator('[data-testid="evl-root"] [data-testid="evl-field-appointment_reference"]')).toHaveCount(0);
		await page.locator('[data-testid="evl-root"] [data-testid="evl-field-reason"]').fill("Replace the member who declared a financial interest.");
		await action(page, "Replace member").click();
		await expectScreen(page, "replace");
		await expect(page.locator('[data-testid="evl-root"] [data-testid="evl-error-incoming"]')).toHaveText("This person cannot serve on this evaluation committee.");
		await expect(page.locator('[data-testid="evl-root"] [data-testid="evl-field-reason"]')).toHaveValue("Replace the member who declared a financial interest.");
		await page.locator('[data-testid="evl-root"] [data-testid="evl-field-incoming"]').selectOption(p.replacement);
		await action(page, "Replace member").click();
		await expect(page.locator('[data-testid="evl-root"]')).not.toHaveAttribute("data-screen", "replace", { timeout: 30_000 });
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});
});
