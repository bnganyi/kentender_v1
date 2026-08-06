/**
 * XMOD-STR-003 — Create Demand Review Plan Value Commitments treatments.
 */
import { execSync } from "node:child_process";
import path from "node:path";

import { expect, test, type Page } from "@playwright/test";

import { loginAsAdministrator } from "../../helpers/auth";

const BENCH_ROOT = path.resolve(__dirname, "../../../../../..");
const SITE = process.env.UI_SITE || "kentender.midas.com";
const CD_PAGE = "/app/create-demand";

function futureDate(daysAhead: number): string {
	return new Date(Date.now() + daysAhead * 86_400_000).toISOString().split("T")[0];
}

function seedStrategyHierarchy(): void {
	try {
		execSync("redis-cli -p 11000 FLUSHDB", { stdio: "pipe" });
	} catch {
		/* ignore */
	}
	let lastErr: unknown;
	for (let attempt = 1; attempt <= 3; attempt += 1) {
		try {
			execSync(
				`cd "${BENCH_ROOT}" && bench --site ${SITE} execute ` +
					"kentender_strategy.seeds.works_master_strategy_hierarchy.upsert_works_master_strategy_hierarchy",
				{ stdio: "pipe", timeout: 120_000 },
			);
			return;
		} catch (e) {
			lastErr = e;
			execSync("sleep 2");
		}
	}
	throw lastErr;
}

async function openWizard(page: Page): Promise<void> {
	await page.goto(CD_PAGE, { waitUntil: "domcontentloaded" });
	await page.waitForSelector("#kt-cd-title", { timeout: 20_000 });
}

async function fillStep1WithStrategy(page: Page, title: string): Promise<void> {
	await page.fill("#kt-cd-title", title);
	await page.waitForFunction(
		() => {
			const d = document.querySelector<HTMLSelectElement>("#kt-cd-dept");
			return d != null && d.options.length > 1;
		},
		{ timeout: 10_000 },
	);
	await page.selectOption("#kt-cd-dept", { index: 1 });
	await page.selectOption("#kt-cd-category", "Works");
	await page.fill("#kt-cd-required-by", futureDate(30));
	await page.fill(
		"#kt-cd-justify",
		"PVC treatment proof for create-demand Review Plan Value Commitments panel.",
	);

	await page.waitForFunction(
		() => {
			const e = document.querySelector<HTMLSelectElement>("#kt-cd-entity");
			return e != null && Array.from(e.options).some((o) => o.value === "PE-MOH");
		},
		{ timeout: 15_000 },
	);
	await page.selectOption("#kt-cd-entity", "PE-MOH");
	await page.waitForFunction(
		() => {
			const s = document.querySelector<HTMLSelectElement>("#kt-cd-strategy-target");
			return !!s && Array.from(s.options).some((o) => Boolean(o.value));
		},
		{ timeout: 15_000 },
	);
	const firstValue = await page.$eval("#kt-cd-strategy-target", (sel: HTMLSelectElement) => {
		for (let i = 0; i < sel.options.length; i += 1) {
			if (sel.options[i].value) return sel.options[i].value;
		}
		return "";
	});
	expect(firstValue).toBeTruthy();
	await page.selectOption("#kt-cd-strategy-target", firstValue);
}

async function addLineItem(page: Page, desc: string): Promise<void> {
	await page.waitForSelector("#kt-cd-new-desc", { state: "visible", timeout: 8_000 });
	await page.fill("#kt-cd-new-desc", desc);
	await page.fill("#kt-cd-new-qty", "2");
	await page.fill("#kt-cd-new-unit", "15000");
	const countBefore = await page.$$eval(
		"#kt-cd-items-body tr:not(.kt-cd-new-row)",
		(rows) => rows.length,
	);
	await page.click("#kt-cd-save-row");
	await page.waitForFunction(
		(expected) => {
			const rows = document.querySelectorAll("#kt-cd-items-body tr:not(.kt-cd-new-row)");
			return rows.length > expected;
		},
		countBefore,
		{ timeout: 5_000 },
	);
}

async function advanceToReview(page: Page, title: string): Promise<void> {
	await fillStep1WithStrategy(page, title);
	await page.click("#kt-cd-next-1");
	await page.waitForSelector("#kt-cd-items-body", { timeout: 20_000 });
	await addLineItem(page, "Works renovation line for PVC review");
	await page.click("#kt-cd-next-2");
	await page.waitForSelector("#kt-cd-readiness-panel", { timeout: 20_000 });
	await expect(page.getByTestId("kt-cd-pvc-panel")).toBeVisible({ timeout: 15_000 });
}

async function requiredPvcRows(page: Page) {
	const rows = page.getByTestId("kt-cd-pvc-row");
	const count = await rows.count();
	const required: number[] = [];
	for (let i = 0; i < count; i += 1) {
		const hint = (await rows.nth(i).locator(".kt-cd-input-hint").textContent()) || "";
		if (/Required/i.test(hint)) required.push(i);
	}
	return { rows, required };
}

test.describe.configure({ mode: "serial" });

test.describe("Create Demand PVC treatments (XMOD-STR-003)", () => {
	test.beforeAll(() => {
		seedStrategyHierarchy();
	});

	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1440, height: 1000 });
		await loginAsAdministrator(page);
		await openWizard(page);
	});

	test("Required untreated blocks Submit; Included refreshes readiness", async ({ page }) => {
		test.setTimeout(180_000);
		await advanceToReview(page, "XMOD-STR-003 Included Path");

		const panel = page.getByTestId("kt-cd-pvc-panel");
		await expect(panel).toBeVisible();
		const rowCount = await page.getByTestId("kt-cd-pvc-row").count();
		expect(rowCount).toBeGreaterThan(0);

		const labels = await page.getByTestId("kt-cd-pvc-row").evaluateAll((els) =>
			els.map((el) => (el.querySelector("strong")?.textContent || "").trim()),
		);
		expect(labels.some((l) => /PVO-EFT-01|PVO-/i.test(l))).toBeTruthy();
		for (const label of labels) {
			expect(label).not.toMatch(/^[a-z0-9]{8,12}$/);
		}

		const { rows, required } = await requiredPvcRows(page);
		test.skip(required.length === 0, "No Required PVCs applicable for Works path");

		const submit = page.locator("#kt-cd-submit");
		await expect(submit).toBeDisabled();

		for (const idx of required) {
			await rows.nth(idx).getByTestId("kt-cd-pvc-treatment").selectOption("Included");
			await page.waitForTimeout(700);
		}

		await expect(submit).toBeEnabled({ timeout: 20_000 });
		const readinessText = (await page.textContent("#kt-cd-readiness-panel")) || "";
		expect(readinessText).toMatch(/Ready to submit|check_circle/i);
	});

	test("Not applicable requires rationale before Submit enables", async ({ page }) => {
		test.setTimeout(180_000);
		await advanceToReview(page, "XMOD-STR-003 NA Path");

		const { rows, required } = await requiredPvcRows(page);
		test.skip(required.length === 0, "No Required PVCs applicable for Works path");

		const submit = page.locator("#kt-cd-submit");
		await expect(submit).toBeDisabled();

		const first = rows.nth(required[0]);
		await first.getByTestId("kt-cd-pvc-treatment").selectOption("Not applicable");
		await page.waitForTimeout(700);
		await expect(submit).toBeDisabled();

		await first.getByTestId("kt-cd-pvc-rationale").fill("Not in scope for this Works package.");
		await page.waitForTimeout(900);

		// Remaining Required rows → Included so overall readiness can pass.
		for (const idx of required.slice(1)) {
			await rows.nth(idx).getByTestId("kt-cd-pvc-treatment").selectOption("Included");
			await page.waitForTimeout(700);
		}

		await expect(submit).toBeEnabled({ timeout: 20_000 });
	});
});
