import { execSync } from "node:child_process";
import path from "node:path";

import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { collectConsoleErrors, expectReady, gotoRequisitions } from "./helpers";

/**
 * REQ-CHG-001 v1.6 Phase 5 (REQ-501) — the §16 persona pass on the seeded
 * KENTENDER_MVP_V1 world (FY 2027/28): the exact named actors §16.1 names,
 * logged in for real, reading the base fixture `upsert_requisitions_base()`
 * built. Nothing here resets fixtures — the world is the seed's, and this
 * pass is release evidence, not a fixture-driven spec (mirrors Planning's
 * own `planning-release-evidence.spec.ts`).
 *
 * Prerequisite: `make seed-kentender-mvp-v1` (Planning's own base, then
 * Requisitions' own `upsert_requisitions_base()`, both idempotent).
 */

const BENCH_ROOT = path.resolve(__dirname, "../../../../../..");
const SITE = process.env.UI_SITE || "kentender.midas.com";
const SEED = "kentender_procurement.procurement_requisitions.seeds.kentender_mvp_v1";
const PASSWORD = "Test@123";

const GRACE = "grace.wanjiku@moh.example.test";
const PETER = "peter.kimani@moh.example.test";
const CHARLES = "charles.mutiso@moh.example.test";
const NAOMI = "naomi.chebet@moh.example.test";

let REQUISITION = "";
let HANDOFF = "";

test.describe.configure({ mode: "serial", timeout: 180_000 });

test.beforeAll(() => {
	try {
		execSync(`cd "${BENCH_ROOT}" && bench --site ${SITE} execute ${SEED}.verify_prerequisites`, { stdio: "pipe", timeout: 300_000, encoding: "utf-8" });
	} catch (error: any) {
		const detail = (error?.stderr || error?.stdout || "").toString().split("\n").filter((l: string) => l.includes("Missing:")).pop() || "prerequisites absent";
		test.skip(true, `§16 world unavailable: ${detail.trim().slice(0, 300)}`);
		return;
	}
	const out = execSync(`cd "${BENCH_ROOT}" && bench --site ${SITE} execute ${SEED}.upsert_requisitions_base --kwargs "{'commit': True}"`, {
		stdio: "pipe", timeout: 600_000, encoding: "utf-8",
	}).trim();
	const line = out.split("\n").pop() || "{}";
	const parsed = JSON.parse(line.replace(/'/g, '"').replace(/\bTrue\b/g, "true").replace(/\bFalse\b/g, "false"));
	REQUISITION = parsed.requisition;
	HANDOFF = parsed.handoff;
	expect(REQUISITION).toBeTruthy();
});

test.describe("§16 persona pass on the seeded MOH world", () => {
	test("Grace Wanjiku (Author) sees the Authorised MOH Requisition in her own register", async ({ page }) => {
		const errors = collectConsoleErrors(page);
		await login(page, GRACE, PASSWORD);
		await gotoRequisitions(page);
		await expectReady(page, "workspace");
		const row = page.locator('[data-testid="req-your-requisitions"] tbody tr', { hasText: "Authorised" });
		expect(await row.count()).toBeGreaterThanOrEqual(1);
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("Dr Peter Kimani (HoD) reads the Authorised handoff directly", async ({ page }) => {
		const errors = collectConsoleErrors(page);
		await login(page, PETER, PASSWORD);
		await gotoRequisitions(page, `/${REQUISITION}/authorised`);
		await expectReady(page, "authorised");
		await expect(page.locator(".kt-status", { hasText: "Authorised for Tender Preparation" })).toBeVisible();
		await expect(page.locator('[data-testid="req-reservations-table"] tbody tr')).toHaveCount(2);
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("Charles Mutiso (HoPF) reads the exact §16.4 reservations and can see Revoke offered", async ({ page }) => {
		const errors = collectConsoleErrors(page);
		await login(page, CHARLES, PASSWORD);
		await gotoRequisitions(page, `/${REQUISITION}/authorised`);
		await expectReady(page, "authorised");
		const rows = page.locator('[data-testid="req-reservations-table"] tbody tr');
		await expect(rows).toHaveCount(2);
		await expect(rows).toContainText(["KES 20,000,000.00"]);
		await expect(rows).toContainText(["KES 30,000,000.00"]);
		await expect(page.locator('[data-testid="req-revoke"]')).toBeVisible();
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("Naomi Chebet (Auditor) reads the same handoff but is never offered Revoke", async ({ page }) => {
		const errors = collectConsoleErrors(page);
		await login(page, NAOMI, PASSWORD);
		await gotoRequisitions(page, `/${REQUISITION}/authorised`);
		await expectReady(page, "authorised");
		await expect(page.locator('[data-testid="req-reservations-table"] tbody tr')).toHaveCount(2);
		await expect(page.locator('[data-testid="req-revoke"]')).toHaveCount(0);
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});
});
