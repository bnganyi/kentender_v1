import { execSync } from "node:child_process";
import path from "node:path";

import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { collectConsoleErrors, expectNoMessageDialog, expectReady, gotoTenderPreparation } from "./helpers";

/**
 * TPR-CHG-001 v0.6 Phase 7 (TPR-701) — the §16 persona pass on the seeded
 * KENTENDER_MVP_V1 world (FY 2027/28): the exact named actors, logged in
 * for real, reading the walkthrough `upsert_tender_preparation()` built
 * (TND-MOH-2027-… approved as Version 2, publication handoff consumed on
 * 15 May 2027). Nothing here resets fixtures — the world is the seed's, and
 * this pass is release evidence (mirrors Requisitions' own
 * `requisitions-release-evidence.spec.ts`). Smoke rows covered: SMOKE-01
 * (the consumed handoff is no longer offered), 02 (inherited rows
 * read-only), 04 (generated schedule, no officer price), 05 (no PE/FY or
 * template control), 09/10/11 (approved Version, publication handoff,
 * consumption acknowledged), 16 (approver identity and time), 20 (auditor
 * read-only).
 *
 * Prerequisite: the canonical MOH Planning world plus
 * `upsert_requisitions_base()` and `upsert_tender_preparation()` (both
 * idempotent; the latter is run here through the seed itself).
 */

const BENCH_ROOT = path.resolve(__dirname, "../../../../../..");
const SITE = process.env.UI_SITE || "kentender.midas.com";
const SEED = "kentender_procurement.tender_preparation.seeds.kentender_mvp_v1";
const PASSWORD = "Test@123";

const BRIAN = "brian.wafula@moh.example.test";
const CHARLES = "charles.mutiso@moh.example.test";
const NAOMI = "naomi.chebet@moh.example.test";

let TENDER = "";
let REFERENCE = "";

test.describe.configure({ mode: "serial", timeout: 180_000 });

test.beforeAll(() => {
	try {
		execSync(`cd "${BENCH_ROOT}" && bench --site ${SITE} execute ${SEED}.verify_prerequisites`, { stdio: "pipe", timeout: 300_000, encoding: "utf-8" });
	} catch (error: any) {
		const detail = (error?.stderr || error?.stdout || "").toString().split("\n").filter((l: string) => /missing|Missing/.test(l)).pop() || "prerequisites absent";
		test.skip(true, `§16 world unavailable: ${detail.trim().slice(0, 300)}`);
		return;
	}
	const out = execSync(`cd "${BENCH_ROOT}" && bench --site ${SITE} execute ${SEED}.upsert_tender_preparation --kwargs "{'commit': True}"`, { stdio: "pipe", timeout: 900_000, encoding: "utf-8" }).trim();
	const line = out.split("\n").pop() || "{}";
	const parsed = JSON.parse(line.replace(/'/g, '"').replace(/\bTrue\b/g, "true").replace(/\bFalse\b/g, "false"));
	TENDER = parsed.tender;
	REFERENCE = parsed.tender_reference;
	expect(TENDER).toBeTruthy();
});

test.describe("§16 persona pass on the seeded MOH world", () => {
	test("Brian Wafula (Procurement Officer) sees the approved MOH Tender, and the consumed handoff is no longer offered", async ({ page }) => {
		const errors = collectConsoleErrors(page);
		await login(page, BRIAN, PASSWORD);
		await gotoTenderPreparation(page);
		await expectReady(page, "workspace");
		const row = page.locator('[data-testid="tpr-tender-row"]', { hasText: REFERENCE });
		await expect(row).toContainText("Approved for publication");
		await expect(row).toContainText("2");
		await expect(page.locator('[data-testid="tpr-ready-row"]', { hasText: "REQ-MOH-2027" })).toHaveCount(0);
		await expect(page.locator("text=/Procuring Entity|Fiscal Year/i")).toHaveCount(0);
		await expect(page.locator("select")).toHaveCount(0);
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("Brian reads the approved Version 2 read-only: inherited rows, generated schedule, no price input", async ({ page }) => {
		const errors = collectConsoleErrors(page);
		await login(page, BRIAN, PASSWORD);
		await gotoTenderPreparation(page, `/${TENDER}`);
		await expectReady(page, "editor");
		await expect(page.locator(".tpr-editor-ref")).toContainText("Version 2");
		await expect(page.locator(".tpr-editor-header .kt-status")).toHaveText("Approved");
		await expect(page.locator("#tpr-tender-title")).toHaveValue("Supply and delivery of business laptops");
		await expect(page.locator("#tpr-tender-title")).toBeDisabled();
		await page.locator('[data-testid="tpr-task-2"]').click();
		await expect(page.locator('[data-testid="tpr-goods"] tbody tr')).toHaveCount(1);
		await expect(page.locator('[data-testid="tpr-goods"] tbody tr').first()).toContainText("250");
		await expect(page.locator('[data-testid="tpr-technical"] tbody tr')).toHaveCount(11);
		await expect(page.locator('[data-testid="tpr-acceptance"] tbody tr')).toHaveCount(5);
		await expect(page.locator(".tpr-task-main input, .tpr-task-main select, .tpr-task-main textarea")).toHaveCount(0);
		await page.locator('[data-testid="tpr-task-3"]').click();
		await expect(page.locator('[data-testid="tpr-price-schedule"] tbody tr')).toHaveCount(1);
		await expect(page.locator(".tpr-task-main")).not.toContainText("50,000,000");
		await expect(page.locator(".tpr-task-main input")).toHaveCount(0);
		await expectNoMessageDialog(page);
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("Charles Mutiso (Head of Procurement Function) reads the approved Tender with its consumed publication handoff", async ({ page }) => {
		const errors = collectConsoleErrors(page);
		await login(page, CHARLES, PASSWORD);
		await gotoTenderPreparation(page, `/${TENDER}/approved`);
		await expectReady(page, "approved");
		await expect(page.locator(".tpr-cap").first()).toContainText(`${REFERENCE} · Version 2`);
		await expect(page.locator(".tpr-ro-val", { hasText: "Charles Mutiso" })).toHaveText("Charles Mutiso, 20 April 2027, 10:00 EAT");
		await expect(page.locator('[data-testid="tpr-consumption-status"]')).toContainText("Consumed");
		await expect(page.locator('[data-testid="tpr-consumption-status"]')).toHaveText("Consumed 15 May 2027, 08:00 EAT");
		await expect(page.locator(".tpr-tag.is-accent")).toHaveCount(3);
		await expect(page.locator('[data-testid="tpr-reopen"]')).toHaveCount(0);
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("Naomi Chebet (Auditor) reads everything and can act on nothing", async ({ page }) => {
		const errors = collectConsoleErrors(page);
		await login(page, NAOMI, PASSWORD);
		await gotoTenderPreparation(page);
		await expectReady(page, "workspace");
		await expect(page.locator('[data-testid="tpr-tender-row"]', { hasText: REFERENCE })).toHaveCount(1);
		await expect(page.getByRole("button", { name: "Prepare Tender" })).toHaveCount(0);
		await gotoTenderPreparation(page, `/${TENDER}/approved`);
		await expectReady(page, "approved");
		await expect(page.locator('[data-testid="tpr-reopen"]')).toHaveCount(0);
		await gotoTenderPreparation(page, `/${TENDER}`);
		await expectReady(page, "editor");
		await expect(page.locator('[data-testid="tpr-save-draft"]')).toBeDisabled();
		await page.locator('[data-testid="tpr-task-review"]').click();
		await expect(page.locator('[data-testid="tpr-submit"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="tpr-readiness-counts"]')).toContainText("0 Blocking");
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});
});
