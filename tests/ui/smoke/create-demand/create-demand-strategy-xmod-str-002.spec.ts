/**
 * XMOD-STR-002 — Create Demand Step 1 primary Strategy Target (Active Name (CODE)).
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

async function selectMohEntity(page: Page): Promise<void> {
	await page.waitForFunction(
		() => {
			const e = document.querySelector<HTMLSelectElement>("#kt-cd-entity");
			return e != null && Array.from(e.options).some((o) => o.value === "PE-MOH");
		},
		{ timeout: 15_000 },
	);
	await page.selectOption("#kt-cd-entity", "PE-MOH");
}

test.describe.configure({ mode: "serial" });

test.describe("Create Demand strategy target (XMOD-STR-002)", () => {
	test.beforeAll(() => {
		seedStrategyHierarchy();
	});

	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1440, height: 1000 });
		await loginAsAdministrator(page);
	});

	test("Active Name (CODE) options; empty Next blocked; select advances to Step 2", async ({
		page,
	}) => {
		test.setTimeout(120_000);
		await openWizard(page);

		await page.fill("#kt-cd-title", "XMOD-STR-002 Strategy Picker");
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
			"Strategy alignment proof for create-demand primary Performance Target selection.",
		);

		await selectMohEntity(page);

		const strategy = page.getByTestId("kt-cd-strategy-target");
		await expect(strategy).toBeVisible();
		await page.waitForFunction(
			() => {
				const s = document.querySelector<HTMLSelectElement>("#kt-cd-strategy-target");
				return !!s && Array.from(s.options).some((o) => Boolean(o.value));
			},
			{ timeout: 15_000 },
		);

		const optionMeta = await strategy.locator("option").evaluateAll((opts) =>
			opts
				.map((o) => {
					const el = o as HTMLOptionElement;
					return { value: el.value, label: (el.textContent || "").trim() };
				})
				.filter((o) => Boolean(o.value)),
		);
		expect(optionMeta.length).toBeGreaterThan(0);
		expect(optionMeta.some((o) => /MOH-TGT-\d+/i.test(o.label))).toBeTruthy();
		for (const o of optionMeta) {
			expect(o.label).not.toMatch(/^[a-z0-9]{8,12}$/);
			expect(o.label).toMatch(/\(/);
		}

		// Empty Next → stay on Step 1 with field error.
		await page.selectOption("#kt-cd-strategy-target", { value: "" });
		await page.click("#kt-cd-next-1");
		const err = page.getByTestId("kt-cd-strategy-target-error");
		await expect(err).toBeVisible({ timeout: 8_000 });
		await expect(err).toContainText(/Select a primary strategy target/i);
		await expect(page.locator("#kt-cd-items-body")).not.toBeVisible();

		// After error re-render, ensure Active options are still present then advance.
		await page.waitForFunction(
			() => {
				const s = document.querySelector<HTMLSelectElement>("#kt-cd-strategy-target");
				return !!s && Array.from(s.options).some((o) => Boolean(o.value));
			},
			{ timeout: 15_000 },
		);
		const pick =
			optionMeta.find((o) => /MOH-TGT-0001/i.test(o.label)) || optionMeta[0];
		await page.selectOption("#kt-cd-strategy-target", pick.value);
		const [saveResp] = await Promise.all([
			page.waitForResponse(
				(r) => r.url().includes("save_demand_draft") && r.request().method() === "POST",
				{ timeout: 20_000 },
			),
			page.click("#kt-cd-next-1"),
		]);
		expect(saveResp.ok()).toBeTruthy();
		await page.waitForSelector("#kt-cd-items-body", { timeout: 20_000 });
		await expect(page.locator("#kt-cd-items-body")).toBeVisible();
	});
});
