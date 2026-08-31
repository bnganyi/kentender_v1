import { execSync } from "node:child_process";
import path from "node:path";

import { expect, test, Page } from "@playwright/test";

import { login } from "../../helpers/auth";

/**
 * PLN-CHG-001 v1.2 Phase 9 (Slice G) — PLN-UI-14: the Active Plan and
 * Prepare plan update, in a real browser on the **PE-PWPB** world (its own
 * fixture entity per tracker rule 8; the fixture drives the real
 * §5.1/§5.2/§8.2 chain all the way to Active — PublishAnnualPlan runs
 * automatically inside ApproveAnnualPlan against the sandbox destination,
 * which always acknowledges).
 */

const BENCH_ROOT = path.resolve(__dirname, "../../../../../..");
const SITE = process.env.UI_SITE || "kentender.midas.com";
const FIXTURES = "kentender_procurement.procurement_planning.seeds.playwright_ui_fixtures";

const PASSWORD = "Test@123";
const PLANNER = "pwpb.planner@example.test";

let PLAN_REFERENCE = "";
let ITEM_ID = "";

function bench(command: string): string {
	try {
		return execSync(`cd "${BENCH_ROOT}" && bench --site ${SITE} ${command}`, {
			stdio: "pipe",
			timeout: 300_000,
			encoding: "utf-8",
		});
	} catch (error: any) {
		const stderr = (error?.stderr || "").toString().trim();
		const stdout = (error?.stdout || "").toString().trim();
		throw new Error(`bench ${command} failed\n${stderr || stdout || error?.message}`);
	}
}

async function expectReady(page: Page, screen: string): Promise<void> {
	const shell = page.locator('[data-testid="pln-shell"]');
	await expect(shell).toHaveAttribute("data-screen", screen, { timeout: 30_000 });
	await expect(shell).toHaveAttribute("data-loading", "false", { timeout: 30_000 });
}

function pageErrors(errors: string[]): string[] {
	return errors.filter(
		(text) => !text.includes("socket.io") && !text.includes("Failed to load resource")
	);
}

test.beforeEach(() => {
	const out = bench(`execute ${FIXTURES}.reset_publication_fixture`);
	const parsed = JSON.parse(out.trim().split("\n").pop() || "{}");
	PLAN_REFERENCE = parsed.plan_reference;
	ITEM_ID = parsed.item_id;
	expect(PLAN_REFERENCE).toBeTruthy();
	expect(ITEM_ID).toBeTruthy();
});

test.describe("PLN-UI-14 the Active Plan and Prepare plan update", () => {
	test("the Active Plan shows PLN-DES-14, and Prepare plan update opens a mutable Draft successor", async ({
		page,
	}) => {
		test.setTimeout(120_000); // two logins + the update-preparation round trip
		const errors: string[] = [];
		page.on("console", (m) => {
			if (m.type() === "error") errors.push(m.text());
		});

		await login(page, PLANNER, PASSWORD);
		await page.setViewportSize({ width: 1440, height: 1024 });
		await page.goto(`/app/annual-procurement-plan/${PLAN_REFERENCE}`, {
			waitUntil: "domcontentloaded",
		});
		await expectReady(page, "plan");

		// PLN-DES-14 exact composition
		await expect(page.locator('[data-testid="pln-plan-badge"]')).toHaveText("Active");
		await expect(page.locator('[data-testid="pln-active-summary-strip"]')).toContainText("1");
		await expect(page.locator('[data-testid="pln-active-items"]')).toContainText(
			"Regional laboratory equipment refresh"
		);
		await expect(page.locator('[data-testid="pln-active-items"]')).toContainText("KES 60,000,000");
		await expect(page.locator('[data-testid="pln-active-governance"]')).toContainText("Acknowledged");
		await expect(page.locator(`[data-testid="pln-active-view-${ITEM_ID}"]`)).toBeVisible();

		// no correction is open yet, so the update-preparation control is live
		const beginUpdate = page.locator('[data-testid="pln-begin-update"]');
		await expect(beginUpdate).toBeVisible();
		await beginUpdate.click();
		await expectReady(page, "plan");

		// the same route now renders the Draft workbench for the new
		// successor — has_open_successor flips the read model's branch
		await expect(page.locator('[data-testid="pln-plan-badge"]')).toHaveText("Draft");
		await expect(page.locator('[data-testid="pln-plan-items"]')).toContainText(
			"Regional laboratory equipment refresh"
		);
		await expect(page.locator('[data-testid="pln-active-summary-strip"]')).toHaveCount(0);

		expect(pageErrors(errors), errors.join("\n")).toHaveLength(0);
	});

	test("the carried-over item resolves to its own mutable successor copy, not its frozen Active twin", async ({
		page,
	}) => {
		// this is the direct regression proof for resolve_item_doc_name: the
		// SAME plan_item_id now names two live documents at once (the Active
		// predecessor's and the Draft successor's), and every read must
		// prefer the open, mutable one.
		await login(page, PLANNER, PASSWORD);
		await page.setViewportSize({ width: 1440, height: 1024 });
		await page.goto(`/app/annual-procurement-plan/${PLAN_REFERENCE}`, {
			waitUntil: "domcontentloaded",
		});
		await expectReady(page, "plan");
		await page.locator('[data-testid="pln-begin-update"]').click();
		await expectReady(page, "plan");

		await page.goto(`/app/procurement-plan-item/${ITEM_ID}`, { waitUntil: "domcontentloaded" });
		await expectReady(page, "plan-item");
		await expect(page.locator('[data-testid="ppi-save"]')).toBeVisible();
		await expect(page.locator('[data-testid="ppi-dissolve"]')).toBeVisible();
	});
});
