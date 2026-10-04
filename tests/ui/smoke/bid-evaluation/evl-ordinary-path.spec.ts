import { expect, Page, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { PASSWORD, action, collectConsoleErrors, evaluationWorld, evlFixture, expectNextStep, expectScreen, gotoEvaluation, restoreEvlWorld } from "./evlWorld";

/**
 * EVL-CHG-001 v0.4 §11.1 — the ordinary path in the browser, as each person
 * (boards D03, D05-START, D05-JOIN, D05, D05-CONCLUSION, D05-CHAIR, D06-SEND,
 * D06-OUTCOME, D07-DRAFT, D07-SIGN, D07-WAIT, D07-SENT, D07-HOP), slices
 * 11.3–11.6. One fixture entity: the Playwright Tender's evaluation, from the
 * "concern" world (every evidence check reviewed except the service location).
 * The supplier's reply is sent by the fixture: the supplier portal is Phase 12.
 */

test.describe.configure({ mode: "serial", timeout: 900_000 });

const root = (page: Page) => page.locator('[data-testid="evl-root"]');
const EVIDENCE = "docs/mvp-1-r1/15_bid_evaluation/evidence/v0_4";
const shot = (page: Page, board: string) => page.screenshot({ path: `${EVIDENCE}/${board}.png`, fullPage: true });
const inRoot = (page: Page, testid: string) => page.locator(`[data-testid="evl-root"] [data-testid="${testid}"]`);

test.describe("EVL ordinary path", () => {
	test.afterAll(() => restoreEvlWorld());

	test("discussion, clarification, reply outcome, report, signatures and delivery", async ({ page }) => {
		const world = evaluationWorld("concern");
		const p = world.people;
		const errors = collectConsoleErrors(page);
		const as = async (user: string, sub = "") => {
			await page.context().clearCookies();
			await login(page, user, PASSWORD);
			await gotoEvaluation(page, world.tender_reference, sub);
		};

		// D03: the chair sees the comparison and the open concern, and starts the discussion.
		await as(p.chair);
		await expectScreen(page, "results");
		await expectNextStep(page, "your_turn", "Discuss the service location finding with the committee.");
		await expect(inRoot(page, "evl-comparison")).toContainText("Afya Digital Supplies (Test) Limited");
		await expect(inRoot(page, "evl-comparison")).toContainText("KES 46,400,000.00");
		await shot(page, "D03");
		await action(page, "Start discussion").click();
		await expectScreen(page, "discussion");
		await expectNextStep(page, "waiting", /^Waiting for .+ to join the discussion\.$/);
		await shot(page, "D05-START");

		// D05-JOIN, D05: the members and the secretary join personally.
		for (const user of [p.member, p.member_2, p.secretary]) {
			await as(user);
			await expectScreen(page, "discussion");
			await expectNextStep(page, "your_turn", "Join the committee discussion.");
			await action(page, "Join discussion").click();
			await expectScreen(page, "discussion");
		}
		await expectNextStep(page, "your_turn", "Record the discussion for the chair.");
		await shot(page, "D05");

		// D05-CHAIR: with everyone present, the chair authorises the written clarification.
		await as(p.chair);
		await expectScreen(page, "discussion");
		await inRoot(page, "evl-link-authorise-clarification").click();
		const next = new Date(new Date(world.instant.replace(" ", "T")).getTime() + 30 * 3600_000);
		const deadline = `${next.toISOString().slice(0, 10)}T17:00`;
		await inRoot(page, "evl-field-question").fill("Please identify the page and section of your submitted Kenya service-centre details that gives the Nairobi service address.");
		await inRoot(page, "evl-field-reply_deadline").fill(deadline);
		await inRoot(page, "evl-field-reply_scope").fill("Explain the submitted evidence. Do not change your offer or add a new service arrangement.");
		await shot(page, "D05-CHAIR");
		await action(page, "Authorise clarification").click();
		await expectScreen(page, "discussion");
		await expect(root(page).locator('[data-testid="evl-error"]')).toHaveCount(0);
		await action(page, "End discussion").click();
		await expectScreen(page, "results");

		// D06-SEND: the secretary sends the authorised question, unchanged.
		await as(p.secretary);
		await expectNextStep(page, "your_turn", /^Send the committee's question to /);
		await action(page, "View clarification").click();
		await expectScreen(page, "clarification");
		await expect(inRoot(page, "evl-request")).toContainText("Nairobi service address");
		await shot(page, "D06-SEND");
		await action(page, "Send clarification").click();
		await expectScreen(page, "clarification");
		await expect(action(page, "Send clarification")).toHaveCount(0);

		// The supplier replies (the portal is Phase 12).
		const reply = evlFixture<{ ok: boolean }>("supplier_reply");
		expect(reply.ok).toBeTruthy();

		// D06-OUTCOME: in a new session the committee records how the reply affects the finding.
		await as(p.chair);
		await expectNextStep(page, "your_turn", "Record how the reply affects the finding.");
		await action(page, "Start discussion").click();
		await expectScreen(page, "discussion");
		for (const user of [p.member, p.member_2, p.secretary]) {
			await as(user);
			await action(page, "Join discussion").click();
			await expectScreen(page, "discussion");
		}
		await as(p.chair);
		await expectScreen(page, "discussion");
		await expect(root(page)).toContainText("Supplier reply");
		await page.locator('[data-testid="evl-root"] label.kt-seg-opt', { hasText: /^Meets$/ }).click();
		await expect(inRoot(page, "evl-seg-meets")).toBeChecked();
		await shot(page, "D06-OUTCOME");
		await inRoot(page, "evl-field-reason").fill("The address is present in the original submitted document and is within Kenya.");
		await action(page, "Record reply outcome").click();
		await expectScreen(page, "discussion");
		await expect(root(page).locator('[data-testid="evl-error"]')).toHaveCount(0);
		// §11.1, 09:05:30: the committee records its basis for no additional due diligence.
		await inRoot(page, "evl-link-record-due-diligence-basis").click();
		await inRoot(page, "evl-field-reason").fill("No additional exercise undertaken; no separate exercise required by the published tender and no outstanding verification concern recorded by the committee.");
		await action(page, "Record conclusion").click();
		await expectScreen(page, "discussion");
		await expect(root(page).locator('[data-testid="evl-error"]')).toHaveCount(0);
		await action(page, "End discussion").click();
		await expectScreen(page, "results");

		// D07-DRAFT: the secretary checks the report and sends it for signing.
		await as(p.secretary);
		await expectNextStep(page, "your_turn", "Check the report and send it to members for signing.");
		await action(page, "View report").click();
		await expectScreen(page, "report");
		await expect(inRoot(page, "evl-summary")).toContainText("Afya Digital Supplies (Test) Limited");
		await expect(inRoot(page, "evl-summary")).toContainText("No additional exercise undertaken");
		await shot(page, "D07-DRAFT");
		await inRoot(page, "evl-field-narrative").fill("The only bid received meets the published requirements. The submitted service-location evidence was clarified without changing the offer.");
		await action(page, "Send for signing").click();
		await expectScreen(page, "report");
		await expect(root(page).locator('[data-testid="evl-error"]')).toHaveCount(0);

		// D07-SIGN / D07-WAIT: each member signs personally; the last proof delivers.
		for (const user of [p.chair, p.member, p.member_2]) {
			await as(user, "report");
			await expectScreen(page, "report");
			await expectNextStep(page, "your_turn", "Review and sign the evaluation report.");
			if (user === p.chair) await shot(page, "D07-SIGN");
			await action(page, "Sign report").click();
			await expectScreen(page, "report");
			await expect(action(page, "Sign report")).toHaveCount(0);
		}
		// D07-SENT: the members' done; D07-HOP: the Head's own review.
		await expectNextStep(page, "done", /^The committee report was sent to /);
		await shot(page, "D07-SENT");
		// AWD-CHG-001 v0.4 §3 entry contract: Award receives the delivered report,
		// and the Head's review task becomes Award's "Prepare professional
		// opinion" — one work item, so the evaluation record shows it done.
		await as(p.hop, "report");
		await expectScreen(page, "report");
		await expectNextStep(page, "done", /^The committee report was sent to /);
		await expect(page.getByRole("button", { name: /award/i })).toHaveCount(0);
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});
});
