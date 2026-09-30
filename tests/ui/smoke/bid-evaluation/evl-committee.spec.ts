import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { PASSWORD, action, collectConsoleErrors, evaluationWorld, expectNextStep, expectScreen, gotoEvaluation, restoreEvlWorld } from "./evlWorld";

/** EVL-CHG-001 v0.4 §9.2, §9.3 — workspace and committee (boards D01-APPOINT, D02-A, D01-APPOINT-HOP, D02-S, D02-D, D02-CONFLICT,
 *  D02-REPLACE, D02-INELIGIBLE, S-OPENING-AWAITED), slices 11.1–11.2. One fixture entity: the Playwright Tender's evaluation. */

test.describe.configure({ mode: "serial", timeout: 600_000 });

test.describe("EVL committee and declaration", () => {
	test.afterAll(() => restoreEvlWorld());

	test("AO appoints from the workspace task, the Head assigns the secretary, a member declares", async ({ page }) => {
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

		// A missing reference stays beside its field; nothing is appointed in part.
		await page.locator('[data-testid="evl-root"] [data-testid="evl-member-0-user"]').selectOption(p.chair);
		await page.locator('[data-testid="evl-root"] [data-testid="evl-member-0-department"]').fill("Human Resource Management and Development");
		await page.locator('[data-testid="evl-root"] [data-testid="evl-member-1-user"]').selectOption(p.member);
		await page.locator('[data-testid="evl-root"] [data-testid="evl-member-1-department"]').fill("ICT");
		await page.locator('[data-testid="evl-root"] [data-testid="evl-member-2-user"]').selectOption(p.member_2);
		await page.locator('[data-testid="evl-root"] [data-testid="evl-member-2-department"]').fill("Finance");
		await action(page, "Appoint committee").click();
		await expectScreen(page, "appoint");
		await expect(page.locator('[data-testid="evl-root"] [data-testid="evl-error"]')).toBeVisible();
		await page.locator('[data-testid="evl-root"] [data-testid="evl-field-appointment_reference"]').fill("MOH/EVAL/PW/2027");
		await action(page, "Appoint committee").click();
		await expect(page.locator('[data-testid="evl-root"]')).not.toHaveAttribute("data-screen", "appoint", { timeout: 30_000 });
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("the Head assigns the secretary (D02-S)", async ({ page }) => {
		const world = evaluationWorld("appointed");
		const p = world.people;
		const errors = collectConsoleErrors(page);
		await login(page, p.hop, PASSWORD);
		await gotoEvaluation(page, world.tender_reference);
		await expectScreen(page, "secretary");
		await expectNextStep(page, "your_turn", "Assign the person who will organise the evaluation record.");
		await expect(page.locator('[data-testid="evl-root"] [data-testid="evl-block-0"] tbody tr')).toHaveCount(3);
		await page.locator('[data-testid="evl-root"] [data-testid="evl-field-secretary"]').selectOption(p.secretary);
		await page.locator('[data-testid="evl-root"] [data-testid="evl-field-appointment_reference"]').fill("MOH/EVAL/SEC/PW/2027");
		await action(page, "Assign secretary").click();
		await expect(page.locator('[data-testid="evl-root"]')).not.toHaveAttribute("data-screen", "secretary", { timeout: 30_000 });
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
		await page.locator('[data-testid="evl-root"] [data-testid="evl-field-appointment_reference"]').fill("MOH/EVAL/PW/2027-R1");
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
